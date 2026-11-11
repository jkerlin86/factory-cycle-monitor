# Reading the Factory Cycle

## Unfilled orders, inventory stages, and capacity utilization, 1992 to present

This project (B3, roadmap Project 8) reads the U.S. factory cycle from
three federal statistical sources: the Census Bureau Manufacturers
Shipments, Inventories, and Orders survey (M3), the Federal Reserve
G.17 release on industrial production and capacity utilization, and
ALFRED vintages for the total manufacturing aggregates.

Stage A (this scaffold) covers data ingestion only: the download script
pulls seasonally adjusted M3 levels for every industry category from
1992 to the latest available month, the Board G.17 file for
manufacturing production and capacity utilization, and the full ALFRED
vintage record for new orders, unfilled orders, shipments, and total
inventories. Analysis is a later stage and is not part of this commit.

## Data and methods facts stated up front

- M3 is a voluntary, non-probability survey of roughly 4,700 reporting
  units, benchmarked to the Economic Census. Values are nominal dollars.
- New orders and unfilled orders exclude semiconductors.
- G.17 and M3 share Census manufacturing source data. They are
  complementary views of the cycle, not independent confirmations.
- The analysis basis is seasonally adjusted data. Not seasonally
  adjusted values are not staged.

## Reproduce the ingestion

```bash
pip install -e ".[dev,notebooks]"
python scripts/download_data.py
```

The script needs `CENSUS_API_KEY` and `FRED_API_KEY` in the
environment or in the project's local `.env` file (never committed).
Raw files land in `data/raw/` and staged parquet tables in
`data/staged/`; both are gitignored and reproduced from the official
sources. See `data/README.md` for the staged schemas and the data gate
note for the full source record.

## Layout

- `src/factory_cycle/` package code
- `scripts/download_data.py` all three ingestion routes (M3, G.17, ALFRED)
- `configs/default.json` series and route configuration
- `data/README.md` staged table schemas and source notes
- `docs/` methods and coding decisions (analysis stage)
