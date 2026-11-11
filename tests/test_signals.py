"""Signal construction: hand-computed synthetic frame and identity
checks against the staged parquet.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from factory_cycle import signals as sig

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "data/staged/m3_levels.parquet"


def _synthetic_levels() -> pd.DataFrame:
    months = pd.date_range("2020-01-01", periods=18, freq="MS")
    frame = pd.DataFrame(
        {
            "VS": 100.0,
            "NO": 110.0,
            "UO": 250.0,
            "TI": 200.0,
            "MI": [80.0] * 12 + [100.0] * 6,
            "WI": 40.0,
            "FI": 80.0,
        },
        index=months,
    )
    frame.index.name = "month"
    return frame


def test_signals_hand_computed():
    out = sig.compute_signals(_synthetic_levels())
    assert np.allclose(out["backlog_months"], 2.5)
    assert np.allclose(out["book_to_bill"], 1.1)
    assert np.allclose(out["inventories_to_shipments"], 2.0)
    assert np.allclose(out["early_stage_share"].iloc[:12], 0.6)
    assert np.allclose(out["early_stage_share"].iloc[12:], 0.7)
    assert np.allclose(out["finished_share"], 0.4)
    # Gap: (80 - 80) / 200 = 0 for the first year, then (100 - 80) / 200.
    assert np.allclose(out["materials_finished_gap"].iloc[:12], 0.0)
    assert np.allclose(out["materials_finished_gap"].iloc[12:], 0.1)
    assert np.isnan(out["materials_finished_gap_change_12m"].iloc[11])
    assert np.isclose(out["materials_finished_gap_change_12m"].iloc[12], 0.1)


def test_signals_missing_codes_become_nan():
    levels = _synthetic_levels().drop(columns=["UO", "MI", "WI", "FI"])
    out = sig.compute_signals(levels)
    assert out["backlog_months"].isna().all()
    assert out["early_stage_share"].isna().all()
    assert np.allclose(out["book_to_bill"], 1.1)


@pytest.mark.skipif(not STAGED.exists(), reason="staged M3 table not present")
def test_identity_against_staged_parquet():
    """Recompute backlog and book-to-bill straight from the staged rows
    and compare with the pipeline panel to 1e-9."""
    m3 = pd.read_parquet(STAGED)
    m3["month"] = pd.to_datetime(m3["month"])
    panel = sig.build_signals_panel(m3, aggregates=["MTM"])
    mtm = m3[m3["category_code"] == "MTM"]
    wide = mtm.pivot_table(
        index="month", columns="data_type_code", values="value", aggfunc="first"
    )
    expected_backlog = (wide["UO"] / wide["VS"]).rename("backlog_months")
    expected_btb = (wide["NO"] / wide["VS"]).rename("book_to_bill")
    got = panel.set_index("month")
    joined = pd.DataFrame(
        {
            "got_backlog": got["backlog_months"],
            "exp_backlog": expected_backlog,
            "got_btb": got["book_to_bill"],
            "exp_btb": expected_btb,
        }
    ).dropna()
    assert len(joined) > 400
    assert (joined["got_backlog"] - joined["exp_backlog"]).abs().max() < 1e-9
    assert (joined["got_btb"] - joined["exp_btb"]).abs().max() < 1e-9


@pytest.mark.skipif(not STAGED.exists(), reason="staged M3 table not present")
def test_is_crosscheck_within_rounding():
    m3 = pd.read_parquet(STAGED)
    m3["month"] = pd.to_datetime(m3["month"])
    check = sig.is_crosscheck(m3, ["MTM", "MDM", "MNM"])
    for cat in ["MTM", "MDM", "MNM"]:
        assert check[cat]["n"] == 417
        assert check[cat]["max_abs_diff"] < 0.0051
