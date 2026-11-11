"""Vintage matrices and revision objects from the ALFRED long table.

The staged ALFRED table holds one row per (series, observation month,
value-effective interval): the value was in effect from realtime_start
to realtime_end. Dates are ISO strings; realtime_end can be the
sentinel "9999-12-31", which is out of range for pandas Timestamps, so
all interval comparisons here are string comparisons (ISO dates order
lexicographically) or integer day counts derived from them.

A vintage matrix has observation months as rows and vintage dates as
columns. The cell at (t, V) is the value whose interval contains V:
realtime_start <= V <= realtime_end. By construction the builder only
ever selects an interval that has already started at V, so no cell can
contain a value first published after its column date. The test suite
proves this against a brute-force containment check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def vintage_dates(long_df: pd.DataFrame, series_id: str) -> list[str]:
    """Sorted distinct vintage dates (realtime_start values) for a series."""
    sub = long_df[long_df["series_id"] == series_id]
    return sorted(sub["realtime_start"].astype(str).unique())


def build_vintage_matrix(long_df: pd.DataFrame, series_id: str) -> pd.DataFrame:
    """Vintage matrix for one ALFRED series (rows obs months, cols vintages).

    Index and columns are strings (YYYY-MM-DD) so the sentinel end date
    never has to be parsed as a timestamp.
    """
    sub = long_df[long_df["series_id"] == series_id].copy()
    sub["realtime_start"] = sub["realtime_start"].astype(str)
    sub["realtime_end"] = sub["realtime_end"].astype(str)
    vintages = sorted(sub["realtime_start"].unique())
    obs_months = sorted(sub["obs_month"].unique())
    matrix = pd.DataFrame(np.nan, index=obs_months, columns=vintages, dtype=float)
    matrix.index = [pd.Timestamp(m).strftime("%Y-%m-%d") for m in obs_months]
    for obs, group in sub.groupby("obs_month"):
        group = group.sort_values("realtime_start")
        starts = group["realtime_start"].to_numpy()
        ends = group["realtime_end"].to_numpy()
        values = group["value"].to_numpy(dtype=float)
        # For each vintage V, the candidate interval is the last one whose
        # start is on or before V. It is the value in effect at V only if
        # its end is also on or after V; otherwise the cell stays NaN.
        pos = np.searchsorted(starts, vintages, side="right") - 1
        row = np.full(len(vintages), np.nan)
        valid = pos >= 0
        idx = np.where(valid)[0]
        chosen = pos[idx]
        in_effect = ends[chosen] >= np.array(vintages, dtype=object)[idx]
        hit = idx[in_effect]
        row[hit] = values[pos[hit]]
        matrix.loc[pd.Timestamp(obs).strftime("%Y-%m-%d")] = row
    matrix.index.name = "obs_month"
    matrix.columns.name = "vintage_date"
    return matrix


def first_release(matrix: pd.DataFrame) -> pd.DataFrame:
    """First published value and vintage date per observation month."""
    values = matrix.to_numpy(dtype=float)
    cols = np.array(matrix.columns)
    has = ~np.isnan(values)
    first_idx = np.where(has.any(axis=1), has.argmax(axis=1), -1)
    rows = []
    for i, obs in enumerate(matrix.index):
        j = first_idx[i]
        if j < 0:
            rows.append((obs, np.nan, None))
        else:
            rows.append((obs, float(values[i, j]), str(cols[j])))
    out = pd.DataFrame(rows, columns=["obs_month", "first_value", "first_vintage"])
    out["obs_month"] = pd.to_datetime(out["obs_month"])
    return out.set_index("obs_month")


def final_values(matrix: pd.DataFrame) -> pd.Series:
    """Value in the latest vintage per observation month."""
    series = matrix.iloc[:, -1].copy()
    series.index = pd.to_datetime(series.index)
    series.index.name = "obs_month"
    return series


def value_at_horizon(
    long_df: pd.DataFrame,
    series_id: str,
    obs_month: pd.Timestamp,
    first_vintage: str,
    horizon_months: int,
) -> float:
    """Value in effect horizon_months after a given first vintage date.

    The cap is the last vintage date of the whole series record, not
    the observation month's own last interval start: ALFRED records
    only value-change intervals, so an observation whose value stopped
    changing has a final interval that starts early and runs to the
    9999 sentinel, and it is still the value in effect at any later
    date inside the record.
    """
    target = (
        pd.Timestamp(first_vintage) + pd.DateOffset(months=horizon_months)
    ).strftime("%Y-%m-%d")
    series_rows = long_df[long_df["series_id"] == series_id]
    last_vintage = str(series_rows["realtime_start"].astype(str).max())
    if target > last_vintage:
        return float("nan")
    sub = series_rows[series_rows["obs_month"] == obs_month]
    hit = sub[
        (sub["realtime_start"].astype(str) <= target)
        & (sub["realtime_end"].astype(str) >= target)
    ]
    if len(hit) == 0:
        return float("nan")
    return float(hit.sort_values("realtime_start")["value"].iloc[-1])


def revision_triangle(
    long_df: pd.DataFrame,
    series_id: str,
    obs_start: str = "2011-01-01",
    horizons_months: tuple[int, ...] = (3, 6, 12),
) -> pd.DataFrame:
    """Revision triangle: first release, horizon values, and latest.

    Rows are observation months from obs_start. The horizon columns hold
    the value in effect that many calendar months after the observation
    month's first release date; they are NaN when that date falls after
    the last vintage in the record.
    """
    matrix = build_vintage_matrix(long_df, series_id)
    first = first_release(matrix)
    final = final_values(matrix)
    rows = []
    for obs, row in first.iterrows():
        if obs < pd.Timestamp(obs_start) or pd.isna(row["first_value"]):
            continue
        record = {
            "obs_month": obs,
            "first_release": float(row["first_value"]),
            "first_vintage": row["first_vintage"],
        }
        for h in horizons_months:
            record[f"plus_{h}m"] = value_at_horizon(
                long_df, series_id, obs, str(row["first_vintage"]), h
            )
        record["latest"] = float(final.loc[obs])
        rows.append(record)
    out = pd.DataFrame(rows).sort_values("obs_month").reset_index(drop=True)
    return out


def triangle_revision_stats(triangle: pd.DataFrame) -> dict:
    """Revision size from first release to latest, in percent."""
    both = triangle.dropna(subset=["first_release", "latest"]).copy()
    pct = 100.0 * (both["latest"] - both["first_release"]) / both["first_release"]
    return {
        "n": int(len(both)),
        "mean_revision_pct": float(pct.mean()),
        "mean_abs_revision_pct": float(pct.abs().mean()),
        "median_abs_revision_pct": float(pct.abs().median()),
    }
