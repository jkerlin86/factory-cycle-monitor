"""Download and stage the three sources used by this project.

Route 1, Census M3 (keyed by the reader's own Census API key, read from
the CENSUS_API_KEY environment variable or the project's local .env;
never commit a key): the Manufacturers Shipments, Inventories, and
Orders survey API at https://api.census.gov/data/timeseries/eits/m3.
One full-year pull per year returns every category, measure, month, and
seasonal adjustment in that year (17,400 rows for 2024: 86 categories x
measures x 12 months x SA/NSA). The raw JSON responses are stored per
year under data/raw/m3/. Staging keeps seasonally adjusted rows only:
the level codes VS, NO, UO, TI, MI, WI, FI for all 86 categories, plus
the published ratios IS and US for MTM, MDM, and MNM as cross-check
columns. Not seasonally adjusted values are not staged; seasonally
adjusted data are the analysis basis.

Route 2, Federal Reserve G.17 (keyless): the Board Data Download zip at
https://www.federalreserve.gov/datadownload/Output.aspx?rel=G17&filetype=zip
contains G17_data.xml (SDMX). The two monthly seasonally adjusted
manufacturing series are parsed out of that file only:

- IP.GMF.S (dataset IP_MAJOR_INDUSTRY_GROUPS, SERIES_CODE GMF,
  FREQ 129 monthly, SA, index 2017=100): industrial production,
  manufacturing (NAICS). The FRED mirror of this series is IPMAN.
- CAPUTL.GMF.S (dataset CAPUTL, SERIES_CODE GMF, monthly, SA,
  percent): capacity utilization, manufacturing (NAICS). The FRED
  mirror of this series is MCUMFN.

FRED is not used as a source for either series; the mirrors are named
only so the Board keys can be cross-referenced.

Route 3, ALFRED vintages (keyed by the reader's own free FRED API key,
read from the FRED_API_KEY environment variable or the project's local
.env; never commit a key): the FRED API series/observations endpoint
with the realtime span opened to all of history (realtime_start
1776-07-04, realtime_end 9999-12-31), which returns one row per
(observation, value-effective interval) across every vintage,
paginated at 100,000 rows, following the C4 project's route. Series:
AMTMNO (new orders), AMTMUO (unfilled orders), AMTMVS (shipments),
AMTMTI (total inventories), all total manufacturing, U.S. Census
Bureau originator (the M3 aggregates as archived by ALFRED).

Outputs: raw files under data/raw/ (with data/raw/manifest.json
recording per-file SHA-256, byte sizes, source URLs, and the retrieval
date) and staged parquet tables under data/staged/:
m3_levels.parquet, g17.parquet, alfred_vintages_long.parquet.
The script finishes by verifying the staged tables: row counts,
min/max months, key uniqueness, and an exact match of the September
2026 MTM seasonally adjusted anchor values against the staged M3
table. Categories whose seasonally adjusted history starts later than
1992-01 are printed, not hidden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import zipfile
from datetime import date

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

M3_BASE = "https://api.census.gov/data/timeseries/eits/m3"
M3_GET = "cell_value,data_type_code,seasonally_adj,category_code,time_slot_id"
LEVEL_CODES = ["VS", "NO", "UO", "TI", "MI", "WI", "FI"]
RATIO_CODES = ["IS", "US"]
RATIO_CATEGORIES = ["MTM", "MDM", "MNM"]
M3_START_YEAR = 1992

G17_URL = "https://www.federalreserve.gov/datadownload/Output.aspx?rel=G17&filetype=zip"
G17_SERIES = {
    "ipman": "IP.GMF.S",
    "mcumfn": "CAPUTL.GMF.S",
}

ALFRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
ALFRED_SERIES = ["AMTMNO", "AMTMUO", "AMTMVS", "AMTMTI"]

# September 2026, MTM, seasonally adjusted, millions of dollars.
# Reconstruction check: the staged M3 values must match these exactly.
ANCHORS_2026_09_MTM = {
    "VS": 668454.0,
    "NO": 677247.0,
    "UO": 1623818.0,
    "TI": 976044.0,
    "MI": 367250.0,
    "WI": 278709.0,
    "FI": 330085.0,
}


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _session() -> requests.Session:
    s = requests.Session()
    s.headers = {"User-Agent": "Mozilla/5.0"}
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2)))
    return s


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- M3


def download_m3(raw_dir: str, api_key: str) -> list[str]:
    """Pull M3 year by year; store the raw API JSON per year."""
    m3_dir = os.path.join(raw_dir, "m3")
    os.makedirs(m3_dir, exist_ok=True)
    s = _session()
    paths = []
    year = M3_START_YEAR
    while year <= date.today().year + 1:
        path = os.path.join(m3_dir, f"m3_{year}.json")
        if os.path.exists(path):
            print(f"m3 {year}: exists, skipping download")
        else:
            params = {
                "get": M3_GET,
                "for": "us:1",
                "time": str(year),
                "key": api_key,
            }
            r = s.get(M3_BASE, params=params, timeout=300)
            if r.status_code != 200:
                print(f"m3 {year}: HTTP {r.status_code}, stopping year loop")
                break
            payload = r.json()
            if len(payload) <= 1:
                print(f"m3 {year}: no data rows, stopping year loop")
                break
            with open(path, "w") as f:
                json.dump(payload, f)
            print(f"m3 {year}: {len(payload) - 1} raw rows -> {path}")
            time.sleep(0.5)
        paths.append(path)
        year += 1
    return paths


def stage_m3(paths: list[str], staged_path: str) -> pd.DataFrame:
    frames = []
    for path in paths:
        with open(path) as f:
            payload = json.load(f)
        frame = pd.DataFrame(payload[1:], columns=payload[0])
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw["seasonally_adj"] == "yes"]
    raw = raw[raw["time_slot_id"] == "0"]
    keep_levels = raw["data_type_code"].isin(LEVEL_CODES)
    keep_ratios = raw["data_type_code"].isin(RATIO_CODES) & raw[
        "category_code"
    ].isin(RATIO_CATEGORIES)
    staged = raw[keep_levels | keep_ratios].copy()
    staged["value"] = pd.to_numeric(staged["cell_value"], errors="coerce")
    n_bad = int(staged["value"].isna().sum())
    if n_bad:
        print(f"m3 staging: dropping {n_bad} rows with non-numeric cell_value")
        staged = staged[staged["value"].notna()]
    staged["month"] = pd.to_datetime(staged["time"] + "-01")
    staged = staged[["month", "category_code", "data_type_code", "value"]]
    staged = staged.sort_values(["category_code", "data_type_code", "month"])
    staged = staged.reset_index(drop=True)
    staged.to_parquet(staged_path, index=False)
    print(f"m3 staged: {len(staged)} rows -> {staged_path}")
    return staged


# ---------------------------------------------------------------- G.17


def download_g17(raw_dir: str) -> str:
    path = os.path.join(raw_dir, "G17.zip")
    if os.path.exists(path):
        print("g17: zip exists, skipping download")
        return path
    s = _session()
    r = s.get(G17_URL, timeout=600)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"g17: downloaded zip ({len(r.content)} bytes) -> {path}")
    return path


def _parse_g17_series(xml_text: str, series_name: str) -> pd.Series:
    """Extract one monthly series (TIME_PERIOD, OBS_VALUE) from the SDMX text."""
    marker = f'SERIES_NAME="{series_name}"'
    start = xml_text.find(marker)
    if start < 0:
        raise ValueError(f"Series {series_name} not found in G17_data.xml")
    end = xml_text.find("</kf:Series>", start)
    block = xml_text[start:end]
    pairs = re.findall(r'TIME_PERIOD="(\d{4}-\d{2})-\d{2}"[^>]*OBS_VALUE="([^"]+)"', block)
    if not pairs:
        pairs = re.findall(r'OBS_VALUE="([^"]+)" TIME_PERIOD="(\d{4}-\d{2})-\d{2}"', block)
        pairs = [(t, v) for v, t in pairs]
    months = pd.to_datetime([p[0] + "-01" for p in pairs])
    values = pd.Series([float(p[1]) for p in pairs], index=months, dtype=float)
    values = values[~values.index.duplicated(keep="last")].sort_index()
    return values


def stage_g17(zip_path: str, staged_path: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z:
        xml_text = z.read("G17_data.xml").decode("utf-8", errors="replace")
    frame = pd.DataFrame(
        {
            "ipman": _parse_g17_series(xml_text, G17_SERIES["ipman"]),
            "mcumfn": _parse_g17_series(xml_text, G17_SERIES["mcumfn"]),
        }
    )
    frame = frame.dropna(how="any").reset_index().rename(columns={"index": "month"})
    frame = frame[["month", "ipman", "mcumfn"]].sort_values("month")
    frame.to_parquet(staged_path, index=False)
    print(f"g17 staged: {len(frame)} rows -> {staged_path}")
    return frame


# ---------------------------------------------------------------- ALFRED


def download_alfred(raw_dir: str, api_key: str) -> list[str]:
    """Fetch ALFRED vintage intervals per series; write one raw CSV each."""
    import csv

    s = _session()
    paths = []
    for series in ALFRED_SERIES:
        rows = []
        offset = 0
        while True:
            params = {
                "series_id": series,
                "api_key": api_key,
                "file_type": "json",
                "realtime_start": "1776-07-04",
                "realtime_end": "9999-12-31",
                "limit": 100000,
                "offset": offset,
            }
            r = s.get(ALFRED_BASE, params=params, timeout=300)
            r.raise_for_status()
            payload = r.json()
            page = payload.get("observations", [])
            rows.extend(page)
            offset += len(page)
            if len(page) < 100000 or offset >= int(payload.get("count", 0)):
                break
            time.sleep(1)
        seen = set()
        unique = []
        for obs in rows:
            key = (obs["date"], obs["realtime_start"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(obs)
        unique.sort(key=lambda o: (o["date"], o["realtime_start"]))
        path = os.path.join(raw_dir, f"alfred_{series.lower()}_vintages.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "vintage_date", "realtime_end", "value"])
            for obs in unique:
                w.writerow(
                    [obs["date"], obs["realtime_start"], obs["realtime_end"], obs["value"]]
                )
        print(f"alfred {series}: {len(unique)} vintage-interval rows -> {path}")
        paths.append(path)
        time.sleep(1)
    return paths


def stage_alfred(paths: list[str], staged_path: str) -> pd.DataFrame:
    frames = []
    for path in paths:
        series = os.path.basename(path).split("_")[1].upper()
        frame = pd.read_csv(path, dtype=str)
        frame["series_id"] = series
        frame["obs_month"] = pd.to_datetime(frame["date"]).dt.to_period("M").dt.to_timestamp()
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame["realtime_start"] = frame["vintage_date"]
        frames.append(
            frame[["series_id", "obs_month", "value", "realtime_start", "realtime_end"]]
        )
    staged = pd.concat(frames, ignore_index=True)
    staged = staged.sort_values(["series_id", "obs_month", "realtime_start"]).reset_index(
        drop=True
    )
    staged.to_parquet(staged_path, index=False)
    print(f"alfred staged: {len(staged)} rows -> {staged_path}")
    return staged


# ---------------------------------------------------------------- verify


def verify(m3: pd.DataFrame, g17: pd.DataFrame, alfred: pd.DataFrame) -> None:
    print("\n=== verification ===")
    print(
        f"m3_levels: {len(m3)} rows, months {m3['month'].min():%Y-%m} to "
        f"{m3['month'].max():%Y-%m}, categories {m3['category_code'].nunique()}, "
        f"codes {sorted(m3['data_type_code'].unique())}"
    )
    dup = m3.duplicated(subset=["month", "category_code", "data_type_code"]).sum()
    print(f"m3 duplicate (month, category, code) keys: {dup}")
    assert dup == 0
    print(
        f"g17: {len(g17)} rows, months {g17['month'].min():%Y-%m} to "
        f"{g17['month'].max():%Y-%m}, duplicate months: {g17['month'].duplicated().sum()}"
    )
    assert not g17["month"].duplicated().any()
    for series, group in alfred.groupby("series_id"):
        vintages = group["realtime_start"].nunique()
        print(
            f"alfred {series}: {len(group)} interval rows, obs months "
            f"{group['obs_month'].min():%Y-%m} to {group['obs_month'].max():%Y-%m}, "
            f"{vintages} distinct vintage dates "
            f"({group['realtime_start'].min()} to {group['realtime_start'].max()})"
        )
    dup_a = alfred.duplicated(subset=["series_id", "obs_month", "realtime_start"]).sum()
    print(f"alfred duplicate (series, obs_month, realtime_start) keys: {dup_a}")
    assert dup_a == 0

    print("\nanchor check, Sep 2026 MTM seasonally adjusted:")
    anchor_rows = m3[
        (m3["month"] == pd.Timestamp("2026-09-01"))
        & (m3["category_code"] == "MTM")
    ].set_index("data_type_code")["value"]
    for code, expected in ANCHORS_2026_09_MTM.items():
        got = float(anchor_rows.loc[code])
        status = "MATCH" if got == expected else "MISMATCH"
        print(f"  {code}: staged {got:.0f} vs anchor {expected:.0f} -> {status}")
        assert got == expected, f"anchor mismatch for {code}: {got} != {expected}"
    print("anchor check: ALL MATCH")

    print("\ncategories whose SA level history starts later than 1992-01:")
    levels = m3[m3["data_type_code"].isin(LEVEL_CODES)]
    first_month = levels.groupby("category_code")["month"].min().sort_values()
    late = first_month[first_month > pd.Timestamp("1992-01-01")]
    if len(late) == 0:
        print("  none")
    for cat, first in late.items():
        print(f"  {cat}: first month {first:%Y-%m}")
    # Per-code late starts inside categories that do begin in 1992.
    print("category/code pairs whose history starts later than 1992-01:")
    first_pair = (
        levels.groupby(["category_code", "data_type_code"])["month"].min().reset_index()
    )
    late_pairs = first_pair[first_pair["month"] > pd.Timestamp("1992-01-01")]
    for _, row in late_pairs.iterrows():
        print(f"  {row['category_code']}/{row['data_type_code']}: first month {row['month']:%Y-%m}")
    if len(late_pairs) == 0:
        print("  none")


# ---------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--staged-dir", default="data/staged")
    args = ap.parse_args()
    _load_dotenv()
    census_key = os.environ.get("CENSUS_API_KEY", "")
    fred_key = os.environ.get("FRED_API_KEY", "")
    if not census_key:
        raise SystemExit("CENSUS_API_KEY is not set; the M3 route cannot run.")
    if not fred_key:
        raise SystemExit("FRED_API_KEY is not set; the ALFRED route cannot run.")
    os.makedirs(args.raw_dir, exist_ok=True)
    os.makedirs(args.staged_dir, exist_ok=True)
    retrieval_date = date.today().isoformat()

    m3_paths = download_m3(args.raw_dir, census_key)
    m3 = stage_m3(m3_paths, os.path.join(args.staged_dir, "m3_levels.parquet"))

    g17_zip = download_g17(args.raw_dir)
    g17 = stage_g17(g17_zip, os.path.join(args.staged_dir, "g17.parquet"))

    alfred_paths = download_alfred(args.raw_dir, fred_key)
    alfred = stage_alfred(
        alfred_paths, os.path.join(args.staged_dir, "alfred_vintages_long.parquet")
    )

    verify(m3, g17, alfred)

    manifest: dict = {"retrieval_date": retrieval_date, "files": {}}
    sources = {os.path.basename(p): M3_BASE for p in m3_paths}
    sources[os.path.basename(g17_zip)] = G17_URL
    for p in alfred_paths:
        sources[os.path.basename(p)] = ALFRED_BASE
    for path in m3_paths + [g17_zip] + alfred_paths:
        rel = os.path.relpath(path, args.raw_dir)
        manifest["files"][rel] = {
            "bytes": os.path.getsize(path),
            "sha256": _sha256(path),
            "source_url": sources[os.path.basename(path)],
        }
    staged_info = {}
    for name in ["m3_levels.parquet", "g17.parquet", "alfred_vintages_long.parquet"]:
        p = os.path.join(args.staged_dir, name)
        staged_info[name] = {"bytes": os.path.getsize(p), "sha256": _sha256(p)}
    manifest["staged"] = staged_info
    manifest_path = os.path.join(args.raw_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nmanifest -> {manifest_path}")


if __name__ == "__main__":
    main()
