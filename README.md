# Reading the Factory Cycle

## Unfilled orders, inventory stages, and capacity utilization, 1992 to present

This project (B3, roadmap Project 8) reads the U.S. factory cycle from
three federal statistical sources: the Census Bureau Manufacturers
Shipments, Inventories, and Orders survey (M3), the Federal Reserve
G.17 release on industrial production and capacity utilization, and
ALFRED vintages for the total manufacturing aggregates. It builds
ratio signals from the M3 levels, evaluates honestly whether those
signals lead the G.17 outcomes, and checks whether the answer survives
being restricted to what was actually published at the time.

## Headline findings

- **The latest readings (2026-09).** Total manufacturing backlog
  stands at 2.43 months of shipments,
  with book-to-bill at 1.013 and
  inventories at 1.46 months
  of shipments. Capital goods backlog is far longer, at
  10.20 months, which is normal for
  that aggregate. The full table is below.
- **Backlog is a coincident stock, not a leading signal, in levels.**
  Over the full span the strongest cross-correlation of total
  manufacturing backlog months with the capacity utilization level is
  at lag 0 (correlation
  -0.43), and with industrial
  production 12-month growth at lag 0
  (correlation -0.51). A lag of
  zero means the two move together; the backlog does not move first.
- **The predictive regressions are unstable, stated plainly.** The
  12-month backlog coefficient for capacity utilization is
  0.69 over the full span
  (t = 0.73, not significant),
  and it changes sign across subperiods. The one window where several
  relationships look strong, 2020 to present, is dominated by the
  pandemic collapse and rebound and does not survive excluding 2020 to
  2021. The stability notes under the lead-lag tables record every sign
  change and significance flip; none of the four signals shows a
  stable, significant predictive relationship across windows.
- **First published backlog is close to final, and the vintage test
  does not rescue a leading relationship.** First published and final
  backlog months differ by 0.063
  months on average (maximum
  0.27), and
  44.1% of months
  are revised by more than 0.05 months. On the vintage-restricted
  sample, the sign does not change; significance at 5% does not change; the best cross-correlation lead changes. Neither run is significant:
  revisions move the point estimate but do not change what the data
  support.
- **Unfilled orders are revised upward on average.** From first
  release to latest, AMTMUO revisions average
  2.13%
  (mean absolute 3.83%)
  over 189 observation
  months. First prints of the backlog level should be read as
  systematically a little low.

## Latest signal readings (2026-09)

| Aggregate | Backlog, months | Book-to-bill | Inventories / shipments | Early-stage share | Finished share | Materials-finished gap |
|---|---|---|---|---|---|---|
| Total manufacturing (MTM) | 2.43 | 1.013 | 1.460 | 66.2% | 33.8% | 3.8% |
| Durable goods (MDM) | 4.82 | 1.026 | 1.812 | 72.3% | 27.7% | 10.6% |
| Nondurable goods (MNM) | n/a | 1.000 | 1.103 | 56.0% | 44.0% | -7.6% |
| Capital goods (TCG) | 10.20 | 1.096 | 2.429 | n/a | n/a | n/a |

Nondurable goods (MNM) has no backlog: Census does not publish
unfilled orders for nondurables, and its new orders equal its
shipments by construction, so its book-to-bill is 1.000. Durable goods
carries all of the total manufacturing unfilled orders, which is why
the MDM and MTM unfilled order levels are the same number. Capital
goods (TCG) has no stage inventories, so its stage columns are empty.

## Validation gate 1

- September 2026 total manufacturing anchors (shipments, new orders,
  unfilled orders, total inventories, and the three stages) match the
  staged M3 table exactly: true.
- Computed inventories to shipments against the published IS ratio:
  maximum absolute difference 0.0050
  (MTM), 0.0050 (MDM),
  0.0050 (MNM), each over
  417 months and each inside the rounding
  of the published two-decimal ratio.
- Stage identity: total inventories equal materials plus work in
  process plus finished goods exactly (maximum absolute difference
  0.0
  million dollars) in every aggregate with stages.
- G.17 published-value check: the staged September 2026 values
  (IPMAN 99.4361,
  MCUMFN 75.9245) match
  a fresh parse of the Board file exactly:
  true.

## Lead-lag evaluation

Outcomes are G.17 capacity utilization (level for cross-correlations;
change over the next 6 and 12 months, in percentage points, for the
regressions) and industrial production (12-month growth for
cross-correlations; growth over the next 6 and 12 months for the
regressions). Sign convention: a positive lag k pairs the signal at
month t with the outcome at t + k, so the signal leads by k months.
Regressions are OLS with Newey-West standard errors (maxlags equal to
the horizon). That inference describes the fitted relationship; it is
not a sampling statement about M3 levels, which come from a voluntary
non-probability panel (see Data and methods facts).

### Backlog months, total manufacturing

| Window | Capacity util.: best lag (corr) | 6m coef | 12m coef | IP growth: best lag (corr) | 6m coef | 12m coef | n (12m) |
|---|---|---|---|---|---|---|---|
| Full span | 0 (-0.43) | 0.256 (t = 0.49) | 0.695 (t = 0.73) | 0 (-0.51) | -1.864 (t = -2.56) | -3.620 (t = -2.79) | 405 |
| 1992 to 2007 | -12 (0.15) | 0.086 (t = 0.08) | -2.307 (t = -0.57) | 12 (-0.25) | -1.075 (t = -0.64) | -6.194 (t = -1.03) | 192 |
| 2008 to 2019 | -12 (0.56) | 0.380 (t = 0.25) | 1.853 (t = 0.54) | 1 (-0.40) | -0.163 (t = -0.08) | 1.217 (t = 0.26) | 144 |
| 2020 to present | 0 (-0.83) | 11.322 (t = 2.35) | 16.852 (t = 3.48) | 12 (0.80) | 16.996 (t = 2.50) | 23.906 (t = 3.82) | 69 |
| Excluding 2020 to 2021 | 3 (-0.41) | -0.160 (t = -0.35) | 0.150 (t = 0.16) | 0 (-0.53) | -2.449 (t = -3.93) | -4.370 (t = -3.45) | 381 |

### Stability, all four signals, stated plainly

- **Backlog months (unfilled orders / shipments):** capacity utilization: the 12-month coefficient changes sign across windows (full span +0.69, 1992 to 2007 -2.31, 2008 to 2019 +1.85, 2020 to present +16.85, excluding 2020 to 2021 +0.15); the relationship is not stable.
- **Backlog months (unfilled orders / shipments):** capacity utilization: 12-month significance at 5% flips across windows (full span not significant, 1992 to 2007 not significant, 2008 to 2019 not significant, 2020 to present significant, excluding 2020 to 2021 not significant).
- **Backlog months (unfilled orders / shipments):** IP growth: the 12-month coefficient changes sign across windows (full span -3.62, 1992 to 2007 -6.19, 2008 to 2019 +1.22, 2020 to present +23.91, excluding 2020 to 2021 -4.37); the relationship is not stable.
- **Backlog months (unfilled orders / shipments):** IP growth: 12-month significance at 5% flips across windows (full span significant, 1992 to 2007 not significant, 2008 to 2019 not significant, 2020 to present significant, excluding 2020 to 2021 significant).
- **Book-to-bill (new orders / shipments):** no sign change and no significance flip in the 12-month regressions across windows.
- **Inventories / shipments:** capacity utilization: 12-month significance at 5% flips across windows (full span not significant, 1992 to 2007 not significant, 2008 to 2019 not significant, 2020 to present significant, excluding 2020 to 2021 not significant).
- **Inventories / shipments:** IP growth: 12-month significance at 5% flips across windows (full span not significant, 1992 to 2007 significant, 2008 to 2019 not significant, 2020 to present significant, excluding 2020 to 2021 not significant).
- **Materials-to-finished gap, 12-month change:** capacity utilization: the 12-month coefficient changes sign across windows (full span -40.38, 1992 to 2007 -8.74, 2008 to 2019 -188.94, 2020 to present +40.52, excluding 2020 to 2021 -82.25); the relationship is not stable.
- **Materials-to-finished gap, 12-month change:** capacity utilization: 12-month significance at 5% flips across windows (full span not significant, 1992 to 2007 not significant, 2008 to 2019 significant, 2020 to present not significant, excluding 2020 to 2021 significant).
- **Materials-to-finished gap, 12-month change:** IP growth: the 12-month coefficient changes sign across windows (full span -70.82, 1992 to 2007 +42.09, 2008 to 2019 -239.22, 2020 to present +36.74, excluding 2020 to 2021 -108.94); the relationship is not stable.
- **Materials-to-finished gap, 12-month change:** IP growth: 12-month significance at 5% flips across windows (full span not significant, 1992 to 2007 not significant, 2008 to 2019 significant, 2020 to present not significant, excluding 2020 to 2021 not significant).

Full tables for book-to-bill, inventories to shipments, and the
materials-to-finished gap change are in
`reports/executive_summary.md`. The pattern there is the same family:
book-to-bill keeps one sign and is never significant at 5% at the
12-month horizon in any window for either outcome; the other two
signals flip significance, and the gap change also flips sign.

## Pseudo-real-time vintage test

ALFRED carries 191 vintage dates
per series (2011-06-24 to
2026-11-03). The first published backlog series
takes, for each observation month, the value from the first vintage
containing that month; the final series takes the latest vintage.
For observation months before mid 2011, first published means the value in the earliest ALFRED vintage (2011-06-24), which is the opening snapshot of the vintage record, not the original release.

The headline regression (backlog months against the next 12 months of
capacity utilization change) is then run on one identical sample both
ways: Observation months whose first vintage for both AMTMUO and AMTMVS is strictly after 2011-06-24 (the opening vintage of the ALFRED record) and whose 12-month-ahead mcumfn change is observed; identical rows for both runs. The sample runs
2011-05 to
2025-09 (n =
173). First published: coefficient
0.537 (t =
0.21, R2 =
0.001), best lead
-8 months. Final:
coefficient 2.600 (t =
1.11, R2 = 0.038),
best lead -12 months. Reading:
the sign does not change; significance at 5% does not change; the best cross-correlation lead changes. Both best leads are negative, which
means utilization moves before the backlog in this sample under both
information sets.

## Revision triangle

`reports/revision_triangle_amtmuo.csv` holds the AMTMUO triangle:
observation months 2011-01 to 2026-09
(189 rows), with the first release, the value in
effect 3, 6, and 12 months after first release, and the latest value.
plus_3m, plus_6m, plus_12m hold the value in effect that many calendar months after the observation month's first release date; NaN when that date falls after the last vintage in the record (2026-11-03). Coverage: first release
189, plus 3 months
185, plus 6 months
182, plus 12 months
175, latest
189. Mean revision from first to
latest is 2.13%
and mean absolute revision is
3.83%
(median absolute
3.47%).

## Data and methods facts, stated plainly

- M3 is a voluntary, non-probability survey of roughly 4,700 reporting
  units, benchmarked to the Economic Census. Conventional sampling
  confidence intervals do not apply to M3 levels or their changes, and
  none are attached anywhere in this project. Regression inference
  here is about the fitted lead-lag relationship only.
- New orders and unfilled orders exclude semiconductors.
- M3 values are nominal dollars. Ratios are the object of this
  project, so no deflator is applied; levels are never interpreted on
  their own.
- M3 and G.17 share Census manufacturing source data. They are
  complementary views of the cycle, not independent confirmations.
- The analysis basis is seasonally adjusted data. Final seasonally
  adjusted values are computed with later data, so a final-value
  signal contains a form of look-ahead; the vintage test partly
  addresses this, and only from 2011, where the ALFRED record begins.
- Category 34G is not used in any aggregate detail in this project: it carries shipments (VS) only and its history ends 2010-03, so no orders, backlog, or inventory signal can be built from it. The published aggregates (MTM, MDM, MNM, TCG) are Census aggregates and are unaffected.
- Full design and limitations: `docs/methods.md`.

## Reproduce

```bash
pip install -e ".[dev,notebooks]"
python scripts/download_data.py   # needs CENSUS_API_KEY and FRED_API_KEY
python scripts/run_analysis.py    # writes reports/results.json
python scripts/make_figures.py
python scripts/make_notebooks.py && python scripts/execute_notebooks.py
python scripts/make_reports.py    # renders README, executive summary, snapshot
pytest
ruff check src scripts tests
```

One-command refresh (ingestion, analysis, figures, reports):

```bash
python scripts/refresh.py
```

The refresh re-downloads from the official sources, so it needs the
same API keys in the environment or the project's local `.env`. There
is no scheduling: the monitor updates only when the refresh is run.

## Layout

- `src/factory_cycle/` loaders (data access), signals, leadlag,
  vintages
- `scripts/` download_data, run_analysis, make_figures, make_reports,
  make_notebooks, execute_notebooks, make_archive, refresh
- `notebooks/` 01 signals and the cycle; 02 lead-lag and vintages
- `reports/results.json` every number in the rendered documents
- `reports/revision_triangle_amtmuo.csv` the AMTMUO revision triangle
- `reports/monitor_snapshot.md` the current monitor snapshot
- `docs/methods.md` design, timing conventions, and limitations
