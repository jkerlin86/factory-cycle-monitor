"""Staged-table loaders and source keys.

The G.17 series keys below were discovered inside the Board Data
Download file (G17_data.xml, SDMX) during the Stage A ingestion and
are recorded in the project data gate note:

- ipman: SERIES_NAME IP.GMF.S, dataset IP_MAJOR_INDUSTRY_GROUPS,
  SERIES_CODE GMF, monthly (FREQ 129), seasonally adjusted, index
  2017=100. Industrial production, manufacturing (NAICS). FRED mirror
  IPMAN (named for cross-reference only; FRED is not a source here).
- mcumfn: SERIES_NAME CAPUTL.GMF.S, dataset CAPUTL, SERIES_CODE GMF,
  monthly, seasonally adjusted, percent. Capacity utilization,
  manufacturing (NAICS). FRED mirror MCUMFN.
"""

from __future__ import annotations

import pandas as pd

G17_SERIES_KEYS = {
    "ipman": "IP.GMF.S",
    "mcumfn": "CAPUTL.GMF.S",
}

M3_LEVEL_CODES = ["VS", "NO", "UO", "TI", "MI", "WI", "FI"]
ALFRED_SERIES = ["AMTMNO", "AMTMUO", "AMTMVS", "AMTMTI"]


def load_m3_levels(path: str = "data/staged/m3_levels.parquet") -> pd.DataFrame:
    """Load the staged Census M3 seasonally adjusted levels table."""
    frame = pd.read_parquet(path)
    frame["month"] = pd.to_datetime(frame["month"])
    return frame


def load_g17(path: str = "data/staged/g17.parquet") -> pd.DataFrame:
    """Load the staged G.17 manufacturing production and utilization table."""
    frame = pd.read_parquet(path)
    frame["month"] = pd.to_datetime(frame["month"])
    return frame


def load_alfred_vintages(
    path: str = "data/staged/alfred_vintages_long.parquet",
) -> pd.DataFrame:
    """Load the staged ALFRED vintage intervals (long format)."""
    frame = pd.read_parquet(path)
    frame["obs_month"] = pd.to_datetime(frame["obs_month"])
    return frame
