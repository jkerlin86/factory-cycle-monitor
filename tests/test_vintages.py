"""Vintage integrity: the matrix builder must never use an interval
whose realtime_start is after the vintage date of the column.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from factory_cycle import vintages


def _synthetic_long() -> pd.DataFrame:
    rows = [
        # obs 2020-01: value 10 from the 2020-02-01 vintage, revised to
        # 12 from the 2020-03-01 vintage onward.
        ("TEST", "2020-01-01", 10.0, "2020-02-01", "2020-02-29"),
        ("TEST", "2020-01-01", 12.0, "2020-03-01", "9999-12-31"),
        # obs 2020-02: not published until the 2020-03-01 vintage.
        ("TEST", "2020-02-01", 20.0, "2020-03-01", "9999-12-31"),
        # obs 2020-03: published once, never revised; its only interval
        # starts at its own first vintage and runs to the sentinel.
        ("TEST", "2020-03-01", 30.0, "2020-04-01", "9999-12-31"),
    ]
    frame = pd.DataFrame(
        rows,
        columns=["series_id", "obs_month", "value", "realtime_start", "realtime_end"],
    )
    frame["obs_month"] = pd.to_datetime(frame["obs_month"])
    return frame


def _brute_force_value(long_df: pd.DataFrame, obs: str, vintage: str) -> float:
    """Independent containment scan used to check the builder."""
    sub = long_df[long_df["obs_month"] == pd.Timestamp(obs)]
    hit = sub[
        (sub["realtime_start"] <= vintage) & (sub["realtime_end"] >= vintage)
    ]
    if len(hit) == 0:
        return float("nan")
    assert len(hit) == 1
    return float(hit["value"].iloc[0])


def test_matrix_matches_brute_force_containment():
    long_df = _synthetic_long()
    matrix = vintages.build_vintage_matrix(long_df, "TEST")
    for obs in matrix.index:
        for vintage in matrix.columns:
            expected = _brute_force_value(long_df, obs, vintage)
            got = matrix.loc[obs, vintage]
            if np.isnan(expected):
                assert np.isnan(got), (obs, vintage)
            else:
                assert got == expected, (obs, vintage)


def test_matrix_never_uses_a_future_interval():
    long_df = _synthetic_long()
    matrix = vintages.build_vintage_matrix(long_df, "TEST")
    # obs 2020-02 has no interval at the 2020-02-01 vintage; the cell
    # must be empty, not filled with the value published a month later.
    assert np.isnan(matrix.loc["2020-02-01", "2020-02-01"])
    assert matrix.loc["2020-02-01", "2020-03-01"] == 20.0
    # Every filled cell's source interval starts on or before its column.
    for obs in matrix.index:
        for vintage in matrix.columns:
            value = matrix.loc[obs, vintage]
            if np.isnan(value):
                continue
            starts = long_df[
                (long_df["obs_month"] == pd.Timestamp(obs))
                & (long_df["value"] == value)
            ]["realtime_start"]
            assert (starts <= vintage).any()


def test_first_release_and_final():
    matrix = vintages.build_vintage_matrix(_synthetic_long(), "TEST")
    first = vintages.first_release(matrix)
    assert first.loc[pd.Timestamp("2020-01-01"), "first_value"] == 10.0
    assert first.loc[pd.Timestamp("2020-01-01"), "first_vintage"] == "2020-02-01"
    assert first.loc[pd.Timestamp("2020-02-01"), "first_vintage"] == "2020-03-01"
    final = vintages.final_values(matrix)
    assert final.loc[pd.Timestamp("2020-01-01")] == 12.0


def test_horizon_beyond_record_is_nan():
    long_df = _synthetic_long()
    # Series record ends at the 2020-04-01 vintage; +3 months after the
    # 2020-02-01 first release is 2020-05-01, outside the record.
    got = vintages.value_at_horizon(
        long_df, "TEST", pd.Timestamp("2020-01-01"), "2020-02-01", 3
    )
    assert np.isnan(got)
    # +1 month lands on the 2020-03-01 vintage, whose value is 12.
    got = vintages.value_at_horizon(
        long_df, "TEST", pd.Timestamp("2020-01-01"), "2020-02-01", 1
    )
    assert got == 12.0
    # An unrevised observation keeps its value at in-record horizons
    # even though its only interval started earlier (sentinel end).
    got = vintages.value_at_horizon(
        long_df, "TEST", pd.Timestamp("2020-03-01"), "2020-04-01", 0
    )
    assert got == 30.0
