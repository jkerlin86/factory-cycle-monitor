# Data

## What is here

`data/raw/` holds the source files exactly as downloaded (gitignored;
recreate with `scripts/download_data.py`). `data/raw/manifest.json`
records per-file SHA-256, byte sizes, source URLs, and the retrieval
date. `data/staged/` holds the analysis-ready parquet tables written by
the same script (also gitignored).

## Staged tables

- `data/staged/m3_levels.parquet`: Census M3 seasonally adjusted levels.
  Columns: `month` (date, first of month), `category_code`,
  `data_type_code`, `value` (float, millions of dollars for the level
  codes). Level codes: VS shipments, NO new orders, UO unfilled orders,
  TI total inventories, MI materials and supplies inventories, WI
  work-in-process inventories, FI finished goods inventories. The
  published inventories to shipments ratios IS and US are staged in the
  same table for MTM, MDM, and MNM only, as cross-check columns; the
  analysis uses levels.
- `data/staged/g17.parquet`: Federal Reserve G.17, Board Data Download
  file only. Columns: `month`, `ipman` (industrial production index,
  manufacturing), `mcumfn` (capacity utilization, percent,
  manufacturing). Both series are monthly and seasonally adjusted.
- `data/staged/alfred_vintages_long.parquet`: ALFRED vintage intervals
  via the FRED API. Columns: `series_id`, `obs_month`, `value`,
  `realtime_start`, `realtime_end`. One row per observation per
  value-effective interval. Series: AMTMNO (new orders), AMTMUO
  (unfilled orders), AMTMVS (shipments), AMTMTI (total inventories),
  all total manufacturing, U.S. Census Bureau originator.

## Sources

- Census M3 API: https://api.census.gov/data/timeseries/eits/m3
- G.17 Board Data Download:
  https://www.federalreserve.gov/datadownload/Output.aspx?rel=G17&filetype=zip
- ALFRED via the FRED API: https://api.stlouisfed.org

Keys are read from the environment or the project's local `.env` and
are never committed. See the project data gate note for spans,
checksums, and the disclosed methods facts.
