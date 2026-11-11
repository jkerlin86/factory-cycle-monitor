"""Run the full B3 analysis and write reports/results.json.

Outputs:
- reports/results.json: every number rendered into the README, the
  executive summary, and the monitor snapshot.
- data/processed/signals_panel.csv and .parquet: the tidy monthly
  signals panel for the four aggregates.
- data/processed/amtmuo_vintage_matrix.parquet and
  amtmvs_vintage_matrix.parquet: the ALFRED vintage matrices used.
- reports/revision_triangle_amtmuo.csv: the AMTMUO revision triangle.

Validation gate 1 runs inside this script and is recorded in
results.json: the September 2026 MTM anchors asserted in Stage A, the
computed inventories to shipments ratio against the published IS
values, the stage identity TI = MI + WI + FI, and the staged G.17
September 2026 values against a fresh parse of the Board file in
data/raw/G17.zip (skipped, and recorded as skipped, if the raw file is
absent).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from factory_cycle import leadlag, signals as sig, vintages  # noqa: E402
from factory_cycle.loaders import load_alfred_vintages, load_g17, load_m3_levels  # noqa: E402

ANCHORS_2026_09_MTM = {
    "VS": 668454.0,
    "NO": 677247.0,
    "UO": 1623818.0,
    "TI": 976044.0,
    "MI": 367250.0,
    "WI": 278709.0,
    "FI": 330085.0,
}
LEADLAG_SIGNALS = [
    "backlog_months",
    "book_to_bill",
    "inventories_to_shipments",
    "materials_finished_gap_change_12m",
]
FIRST_VINTAGE_OF_RECORD = "2011-06-24"


def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.strftime("%Y-%m-%d")
    if obj is None or (isinstance(obj, float) and np.isnan(obj)):
        return None
    return obj


def _board_g17_values() -> dict | None:
    """Re-parse the Board G.17 file from data/raw for the staged check."""
    zip_path = ROOT / "data/raw/G17.zip"
    if not zip_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "download_data", ROOT / "scripts/download_data.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with zipfile.ZipFile(zip_path) as z:
        xml_text = z.read("G17_data.xml").decode("utf-8", errors="replace")
    out = {}
    for key, series_name in module.G17_SERIES.items():
        series = module._parse_g17_series(xml_text, series_name)
        out[key] = float(series.loc[pd.Timestamp("2026-09-01")])
    return out


def _latest_signals(panel: pd.DataFrame) -> dict:
    latest = {}
    for agg, group in panel.groupby("aggregate"):
        row = group.sort_values("month").iloc[-1]
        entry = {"month": row["month"].strftime("%Y-%m")}
        for col in sig.LEVEL_CODES + sig.SIGNAL_COLUMNS:
            value = row[col]
            entry[col] = None if pd.isna(value) else float(value)
        latest[agg] = entry
    return latest


def _vintage_test(alfred: pd.DataFrame, g17: pd.DataFrame) -> dict:
    uo_matrix = vintages.build_vintage_matrix(alfred, "AMTMUO")
    vs_matrix = vintages.build_vintage_matrix(alfred, "AMTMVS")
    processed = ROOT / "data/processed"
    for name, matrix in [("amtmuo", uo_matrix), ("amtmvs", vs_matrix)]:
        out = matrix.copy()
        out.index.name = "obs_month"
        out.to_parquet(processed / f"{name}_vintage_matrix.parquet")

    uo_first = vintages.first_release(uo_matrix)
    vs_first = vintages.first_release(vs_matrix)
    uo_final = vintages.final_values(uo_matrix)
    vs_final = vintages.final_values(vs_matrix)
    first_backlog = (uo_first["first_value"] / vs_first["first_value"]).rename(
        "first_backlog"
    )
    final_backlog = (uo_final / vs_final).rename("final_backlog")
    both = pd.DataFrame([first_backlog, final_backlog]).T.dropna()
    diff = (both["first_backlog"] - both["final_backlog"]).abs()
    comparison = {
        "n_months": int(len(both)),
        "first_obs_month": both.index.min().strftime("%Y-%m"),
        "last_obs_month": both.index.max().strftime("%Y-%m"),
        "mean_abs_diff_months": float(diff.mean()),
        "max_abs_diff_months": float(diff.max()),
        "share_gt_0_05_months": float((diff > 0.05).mean()),
        "note": (
            "For observation months before mid 2011, first published means "
            "the value in the earliest ALFRED vintage (2011-06-24), which "
            "is the opening snapshot of the vintage record, not the "
            "original release."
        ),
    }

    # Regression sample: identical rows for the first and final runs.
    # An observation month enters only if the first vintage containing
    # it is strictly after the opening vintage of the record (so the
    # first value is a genuine first release of that month, for both
    # unfilled orders and shipments) and its 12-month-ahead capacity
    # utilization outcome is observed in the staged G.17 table.
    outcomes = leadlag.forward_outcomes(g17)
    frame = pd.DataFrame(
        {
            "first_backlog": first_backlog,
            "final_backlog": final_backlog,
            "first_vintage_uo": uo_first["first_vintage"],
            "first_vintage_vs": vs_first["first_vintage"],
            "mcumfn_change_12m": outcomes["mcumfn_change_12m"],
            "mcumfn_level": outcomes["mcumfn_level"],
        }
    )
    genuine = (frame["first_vintage_uo"] > FIRST_VINTAGE_OF_RECORD) & (
        frame["first_vintage_vs"] > FIRST_VINTAGE_OF_RECORD
    )
    sample = frame[genuine].dropna(
        subset=["first_backlog", "final_backlog", "mcumfn_change_12m"]
    )
    reg_first = leadlag.predictive_regression(
        sample.rename(columns={"first_backlog": "signal"}),
        "signal",
        "mcumfn_change_12m",
        12,
    )
    reg_final = leadlag.predictive_regression(
        sample.rename(columns={"final_backlog": "signal"}),
        "signal",
        "mcumfn_change_12m",
        12,
    )
    xcorr_first = leadlag.cross_correlations(
        sample["first_backlog"], outcomes["mcumfn_level"]
    )
    xcorr_final = leadlag.cross_correlations(
        sample["final_backlog"], outcomes["mcumfn_level"]
    )

    def _conclusion(reg: dict, xcorr: dict) -> dict:
        return {
            "coef": reg["coef"],
            "t_stat": reg["t_stat"],
            "p_value": reg["p_value"],
            "r2": reg["r2"],
            "n": reg["n"],
            "significant_5pct": bool(reg["p_value"] is not None and reg["p_value"] < 0.05),
            "best_lead_months": xcorr["best_lag"],
            "best_lead_corr": xcorr["best_corr"],
        }

    conc_first = _conclusion(reg_first, xcorr_first)
    conc_final = _conclusion(reg_final, xcorr_final)
    changes = {
        "sign_changes": bool(
            (conc_first["coef"] or 0) * (conc_final["coef"] or 0) < 0
        ),
        "significance_changes": bool(
            conc_first["significant_5pct"] != conc_final["significant_5pct"]
        ),
        "best_lead_changes": bool(
            conc_first["best_lead_months"] != conc_final["best_lead_months"]
        ),
    }
    changes["conclusion_changes"] = any(changes.values())
    return {
        "first_vs_final_backlog": comparison,
        "regression_sample": {
            "definition": (
                "Observation months whose first vintage for both AMTMUO "
                "and AMTMVS is strictly after 2011-06-24 (the opening "
                "vintage of the ALFRED record) and whose 12-month-ahead "
                "mcumfn change is observed; identical rows for both runs."
            ),
            "start_month": sample.index.min().strftime("%Y-%m"),
            "end_month": sample.index.max().strftime("%Y-%m"),
            "n": int(len(sample)),
        },
        "first_published_run": conc_first,
        "final_run": conc_final,
        "changes": changes,
    }


def main() -> None:
    processed = ROOT / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)

    m3 = load_m3_levels(str(ROOT / "data/staged/m3_levels.parquet"))
    g17 = load_g17(str(ROOT / "data/staged/g17.parquet"))
    alfred = load_alfred_vintages(str(ROOT / "data/staged/alfred_vintages_long.parquet"))

    panel = sig.build_signals_panel(m3)
    panel_out = panel.copy()
    panel_out["month"] = panel_out["month"].dt.strftime("%Y-%m-%d")
    panel_out.to_csv(processed / "signals_panel.csv", index=False)
    panel.to_parquet(processed / "signals_panel.parquet", index=False)

    # Validation gate 1.
    anchor_rows = m3[
        (m3["month"] == pd.Timestamp("2026-09-01")) & (m3["category_code"] == "MTM")
    ].set_index("data_type_code")["value"]
    anchors = {
        code: {
            "staged": float(anchor_rows.loc[code]),
            "expected": expected,
            "match": bool(float(anchor_rows.loc[code]) == expected),
        }
        for code, expected in ANCHORS_2026_09_MTM.items()
    }
    g17_sep = g17[g17["month"] == pd.Timestamp("2026-09-01")].iloc[0]
    board = _board_g17_values()
    if board is None:
        g17_check = {
            "month": "2026-09",
            "staged_ipman": float(g17_sep["ipman"]),
            "staged_mcumfn": float(g17_sep["mcumfn"]),
            "board_ipman": None,
            "board_mcumfn": None,
            "match": None,
            "note": "data/raw/G17.zip absent at analysis time; check skipped.",
        }
    else:
        g17_check = {
            "month": "2026-09",
            "staged_ipman": float(g17_sep["ipman"]),
            "staged_mcumfn": float(g17_sep["mcumfn"]),
            "board_ipman": board["ipman"],
            "board_mcumfn": board["mcumfn"],
            "match": bool(
                float(g17_sep["ipman"]) == board["ipman"]
                and float(g17_sep["mcumfn"]) == board["mcumfn"]
            ),
        }
    validation = {
        "anchors_2026_09_mtm": anchors,
        "anchors_all_match": all(a["match"] for a in anchors.values()),
        "is_crosscheck": sig.is_crosscheck(m3, ["MTM", "MDM", "MNM"]),
        "stage_identity_ti_equals_mi_wi_fi": sig.stage_identity_check(
            m3, ["MTM", "MDM", "MNM"]
        ),
        "g17_sep2026_board_check": g17_check,
    }

    # Lead-lag evaluation, total manufacturing signals only.
    mtm = panel[panel["aggregate"] == "MTM"].set_index("month")
    outcomes = leadlag.forward_outcomes(g17)
    leadlag_results = {}
    stability = {}
    for signal_col in LEADLAG_SIGNALS:
        evaluation = leadlag.evaluate_signal(mtm, outcomes, signal_col)
        leadlag_results[signal_col] = evaluation
        stability[signal_col] = leadlag.stability_note(evaluation)

    vintage_results = _vintage_test(alfred, g17)

    triangle = vintages.revision_triangle(alfred, "AMTMUO", obs_start="2011-01-01")
    triangle_out = triangle.copy()
    triangle_out["obs_month"] = triangle_out["obs_month"].dt.strftime("%Y-%m-%d")
    triangle_out.to_csv(ROOT / "reports/revision_triangle_amtmuo.csv", index=False)
    horizon_cols = ["first_release", "plus_3m", "plus_6m", "plus_12m", "latest"]
    triangle_info = {
        "series": "AMTMUO",
        "series_label": "Unfilled orders, total manufacturing (ALFRED AMTMUO)",
        "obs_start": triangle["obs_month"].min().strftime("%Y-%m"),
        "obs_end": triangle["obs_month"].max().strftime("%Y-%m"),
        "n_obs_months": int(len(triangle)),
        "horizon_coverage": {
            col: int(triangle[col].notna().sum()) for col in horizon_cols
        },
        "horizon_definition": (
            "plus_3m, plus_6m, plus_12m hold the value in effect that "
            "many calendar months after the observation month's first "
            "release date; NaN when that date falls after the last "
            "vintage in the record (2026-11-03)."
        ),
        "revision_stats_first_to_latest_pct": vintages.triangle_revision_stats(triangle),
    }

    cat34g = m3[m3["category_code"] == "34G"]
    results = {
        "generated_date": date.today().isoformat(),
        "latest_month": panel["month"].max().strftime("%Y-%m"),
        "coverage": {
            "m3_rows": int(len(m3)),
            "m3_months": [
                m3["month"].min().strftime("%Y-%m"),
                m3["month"].max().strftime("%Y-%m"),
            ],
            "m3_categories": int(m3["category_code"].nunique()),
            "g17_months": [
                g17["month"].min().strftime("%Y-%m"),
                g17["month"].max().strftime("%Y-%m"),
            ],
            "alfred_vintage_dates_per_series": int(
                alfred.groupby("series_id")["realtime_start"].nunique().iloc[0]
            ),
            "alfred_vintage_span": [
                str(alfred["realtime_start"].min()),
                str(alfred["realtime_start"].max()),
            ],
            "excluded_category_note": (
                "Category 34G is not used in any aggregate detail in this "
                "project: it carries shipments (VS) only and its history "
                "ends "
                + cat34g["month"].max().strftime("%Y-%m")
                + ", so no orders, backlog, or inventory signal can be "
                "built from it. The published aggregates (MTM, MDM, MNM, "
                "TCG) are Census aggregates and are unaffected."
            ),
        },
        "validation": validation,
        "latest_signals": _latest_signals(panel),
        "leadlag": leadlag_results,
        "leadlag_stability_notes": stability,
        "vintage_test": vintage_results,
        "revision_triangle": triangle_info,
    }
    out = ROOT / "reports/results.json"
    out.write_text(json.dumps(_clean(results), indent=2))
    print(f"wrote {out}")
    print("anchors all match:", validation["anchors_all_match"])
    print("g17 board check match:", g17_check["match"])
    print("triangle rows:", len(triangle))


if __name__ == "__main__":
    main()
