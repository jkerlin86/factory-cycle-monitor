"""Cycle signals constructed from the staged M3 levels.

Signals are ratios of seasonally adjusted nominal levels, so the dollar
units cancel. Definitions (per aggregate, per month):

- backlog_months = UO / VS (unfilled orders in months of shipments).
  Not available for nondurable goods (MNM), which Census does not
  publish unfilled orders for.
- book_to_bill = NO / VS (new orders over shipments). New orders start
  1992-02 for most categories, so this ratio starts 1992-02.
- inventories_to_shipments = TI / VS.
- early_stage_share = (MI + WI) / TI and finished_share = FI / TI,
  where the three stages sum to total inventories by construction.
- materials_finished_gap = (MI - FI) / TI, the primary
  materials-to-finished divergence measure, with
  materials_finished_gap_change_12m its 12-month change.

The divergence choice needs one sentence of justification. The
alternative form, the 12-month change in the early-stage share minus
the 12-month change in the finished share, is identically twice the
change in the early-stage share because MI + WI + FI = TI, so it adds
no information beyond the share itself. The (MI - FI) / TI gap is not
degenerate in that way: it compares the two ends of the production
pipeline directly. It is the primary definition used everywhere in
this project.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

AGGREGATES = ["MTM", "MDM", "MNM", "TCG"]
LEVEL_CODES = ["VS", "NO", "UO", "TI", "MI", "WI", "FI"]
SIGNAL_COLUMNS = [
    "backlog_months",
    "book_to_bill",
    "inventories_to_shipments",
    "early_stage_share",
    "finished_share",
    "materials_finished_gap",
    "materials_finished_gap_change_12m",
]


def pivot_category(m3: pd.DataFrame, category: str) -> pd.DataFrame:
    """Wide monthly levels for one category code, indexed by month."""
    sub = m3[m3["category_code"] == category]
    wide = sub.pivot_table(
        index="month", columns="data_type_code", values="value", aggfunc="first"
    )
    wide = wide.sort_index()
    wide.index.name = "month"
    return wide


def compute_signals(levels: pd.DataFrame) -> pd.DataFrame:
    """Signals from one category's wide levels frame.

    Missing source codes produce NaN signal columns rather than errors,
    so aggregates without a code (MNM has no UO; TCG has no MI/WI/FI)
    still return a full frame.
    """
    out = pd.DataFrame(index=levels.index)

    def col(code: str) -> pd.Series:
        if code in levels.columns:
            return levels[code].astype(float)
        return pd.Series(np.nan, index=levels.index)

    vs, no, uo = col("VS"), col("NO"), col("UO")
    ti, mi, wi, fi = col("TI"), col("MI"), col("WI"), col("FI")
    for code, series in [
        ("VS", vs),
        ("NO", no),
        ("UO", uo),
        ("TI", ti),
        ("MI", mi),
        ("WI", wi),
        ("FI", fi),
    ]:
        out[code] = series
    out["backlog_months"] = uo / vs
    out["book_to_bill"] = no / vs
    out["inventories_to_shipments"] = ti / vs
    out["early_stage_share"] = (mi + wi) / ti
    out["finished_share"] = fi / ti
    out["materials_finished_gap"] = (mi - fi) / ti
    out["materials_finished_gap_change_12m"] = out["materials_finished_gap"].diff(12)
    return out


def build_signals_panel(
    m3: pd.DataFrame, aggregates: list[str] | None = None
) -> pd.DataFrame:
    """Tidy monthly signals panel: one row per month per aggregate."""
    aggregates = aggregates or AGGREGATES
    frames = []
    for agg in aggregates:
        signals = compute_signals(pivot_category(m3, agg))
        signals = signals.reset_index().rename(columns={"index": "month"})
        signals.insert(1, "aggregate", agg)
        frames.append(signals)
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["aggregate", "month"]).reset_index(drop=True)
    return panel


def published_ratio(m3: pd.DataFrame, category: str, code: str) -> pd.Series:
    """One staged published ratio series (IS or US) for a category."""
    sub = m3[(m3["category_code"] == category) & (m3["data_type_code"] == code)]
    series = sub.set_index("month")["value"].sort_index()
    series.index.name = "month"
    return series


def is_crosscheck(m3: pd.DataFrame, categories: list[str]) -> dict:
    """Compare computed TI / VS with the published IS ratio per category.

    The published IS is rounded to two decimals, so agreement is
    expected only to within rounding (about 0.005).
    """
    out = {}
    for cat in categories:
        signals = compute_signals(pivot_category(m3, cat))
        published = published_ratio(m3, cat, "IS")
        joined = pd.DataFrame(
            {"computed": signals["inventories_to_shipments"], "published": published}
        ).dropna()
        diff = (joined["computed"] - joined["published"]).abs()
        out[cat] = {
            "n": int(len(joined)),
            "max_abs_diff": float(diff.max()) if len(diff) else None,
            "mean_abs_diff": float(diff.mean()) if len(diff) else None,
        }
    return out


def stage_identity_check(m3: pd.DataFrame, aggregates: list[str]) -> dict:
    """Max |TI - (MI + WI + FI)| per aggregate with stage inventories."""
    out = {}
    for agg in aggregates:
        levels = pivot_category(m3, agg)
        if not {"TI", "MI", "WI", "FI"}.issubset(levels.columns):
            continue
        resid = (levels["TI"] - (levels["MI"] + levels["WI"] + levels["FI"])).abs()
        out[agg] = {"n": int(resid.notna().sum()), "max_abs_diff": float(resid.max())}
    return out
