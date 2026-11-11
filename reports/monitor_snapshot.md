# Factory cycle monitor snapshot

**Snapshot date:** 2026-11-11
**Latest data month:** 2026-09

## Latest readings

| Aggregate | Backlog, months | Book-to-bill | Inventories / shipments | Early-stage share | Finished share | Materials-finished gap |
|---|---|---|---|---|---|---|
| Total manufacturing (MTM) | 2.43 | 1.013 | 1.460 | 66.2% | 33.8% | 3.8% |
| Durable goods (MDM) | 4.82 | 1.026 | 1.812 | 72.3% | 27.7% | 10.6% |
| Nondurable goods (MNM) | n/a | 1.000 | 1.103 | 56.0% | 44.0% | -7.6% |
| Capital goods (TCG) | 10.20 | 1.096 | 2.429 | n/a | n/a | n/a |

Supporting levels and ratios behind these readings are in
`reports/results.json` (key `latest_signals`), and the full monthly
panel is in `data/processed/signals_panel.csv`.

## What the readings mean, briefly

Backlog months say how long the current order book would take to ship
at the current shipment rate. Book-to-bill above 1 means orders are
arriving faster than shipments. The stage shares and the
materials-to-finished gap describe where inventories sit in the
production pipeline. The project's lead-lag evaluation found these
signals coincident rather than leading, and unstable as predictors
across subperiods; the snapshot reports the readings without a
forecast claim. See the README and `reports/executive_summary.md` for
the evaluation and its stability notes.

## Changelog

- 2026-11-11: initial build (Stage B, 2026-11-11). First snapshot:
  signals through 2026-09, lead-lag evaluation over the full
  span and subperiods, pseudo-real-time vintage test, AMTMUO revision
  triangle.

## Refresh

Run `python scripts/refresh.py` from the project root. It re-runs
ingestion (`scripts/download_data.py`, which needs `CENSUS_API_KEY`
and `FRED_API_KEY` in the environment or the project's local `.env`),
then analysis, figures, and reports, and rewrites this snapshot with
the then-current latest month. There is no scheduled automation; the
monitor updates only when the refresh is run by hand.
