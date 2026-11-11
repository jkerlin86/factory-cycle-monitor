"""Results schema: reports/results.json carries the required keys and
the Stage A anchor values.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports/results.json"

pytestmark = pytest.mark.skipif(
    not RESULTS.exists(), reason="results.json not built yet"
)


@pytest.fixture(scope="module")
def results() -> dict:
    return json.loads(RESULTS.read_text())


def test_required_keys(results):
    for key in [
        "generated_date",
        "latest_month",
        "coverage",
        "validation",
        "latest_signals",
        "leadlag",
        "leadlag_stability_notes",
        "vintage_test",
        "revision_triangle",
    ]:
        assert key in results, key
    assert results["latest_month"] == "2026-09"
    for agg in ["MTM", "MDM", "MNM", "TCG"]:
        assert agg in results["latest_signals"]


def test_anchor_values(results):
    anchors = results["validation"]["anchors_2026_09_mtm"]
    expected = {
        "VS": 668454.0,
        "NO": 677247.0,
        "UO": 1623818.0,
        "TI": 976044.0,
        "MI": 367250.0,
        "WI": 278709.0,
        "FI": 330085.0,
    }
    assert results["validation"]["anchors_all_match"] is True
    for code, value in expected.items():
        assert anchors[code]["expected"] == value
        assert anchors[code]["staged"] == value
        assert anchors[code]["match"] is True


def test_g17_check(results):
    check = results["validation"]["g17_sep2026_board_check"]
    assert check["staged_ipman"] == 99.4361
    assert check["staged_mcumfn"] == 75.9245
    if check["board_ipman"] is not None:
        assert check["match"] is True


def test_leadlag_structure(results):
    for signal in [
        "backlog_months",
        "book_to_bill",
        "inventories_to_shipments",
        "materials_finished_gap_change_12m",
    ]:
        assert signal in results["leadlag"]
        for outcome in ["mcumfn", "ipman"]:
            for window in [
                "full",
                "1992_2007",
                "2008_2019",
                "2020_present",
                "excl_2020_2021",
            ]:
                entry = results["leadlag"][signal][outcome][window]
                assert "xcorr" in entry and "reg_6m" in entry and "reg_12m" in entry


def test_vintage_and_triangle_structure(results):
    vt = results["vintage_test"]
    comp = vt["first_vs_final_backlog"]
    assert comp["n_months"] == 417
    assert 0 < comp["mean_abs_diff_months"] < comp["max_abs_diff_months"]
    assert vt["regression_sample"]["n"] > 100
    assert "first_published_run" in vt and "final_run" in vt
    tri = results["revision_triangle"]
    assert tri["series"] == "AMTMUO"
    assert tri["n_obs_months"] == 189
    assert tri["horizon_coverage"]["first_release"] == 189
    assert tri["horizon_coverage"]["latest"] == 189
