# Methods

## Design

Three sources, one monthly spine. Census M3 provides seasonally
adjusted levels (shipments VS, new orders NO, unfilled orders UO,
total inventories TI, and the stage inventories MI, WI, FI) by
industry category from 1992. Federal Reserve G.17 provides the two
outcome series for manufacturing: industrial production (index,
2017 = 100) and capacity utilization (percent). ALFRED provides the
vintage record for the four total manufacturing M3 aggregates (new
orders AMTMNO, unfilled orders AMTMUO, shipments AMTMVS, total
inventories AMTMTI), which makes a pseudo-real-time version of the
headline test possible from 2011.

The aggregates used are total manufacturing (MTM), durable goods
(MDM), nondurable goods (MNM), and capital goods (TCG). Category 34G
is excluded from category detail: it carries shipments only and its
history ends in March 2010, so no orders, backlog, or inventory
signal can be built from it. The aggregates themselves are published
Census aggregates and do not depend on 34G.

## Signals

All signals are ratios of nominal levels, so units cancel:

- backlog_months = UO / VS. Not defined for nondurable goods, for
  which Census publishes no unfilled orders.
- book_to_bill = NO / VS. New orders begin in February 1992 for most
  categories, so the ratio begins then. For nondurable goods, new
  orders equal shipments by construction and the ratio is 1.
- inventories_to_shipments = TI / VS.
- Stage mix: early_stage_share = (MI + WI) / TI, finished_share =
  FI / TI. The stages sum to the total exactly in the staged data.
- Materials-to-finished divergence (primary definition):
  materials_finished_gap = (MI - FI) / TI, reported as a level with
  its 12-month change as the dynamic form. The alternative form, the
  12-month change in the early-stage share minus the 12-month change
  in the finished share, is identically twice the change in the
  early-stage share because the three stages sum to total
  inventories; it adds no information beyond the share itself, so it
  is not used.

## Validation gate 1

Four checks, all recorded in reports/results.json. (1) The September
2026 total manufacturing anchor values asserted at ingestion must
match the staged table exactly. (2) The computed inventories to
shipments ratio must track the published IS ratio for MTM, MDM, and
MNM to within the published ratio's two-decimal rounding. (3) The
stage identity TI = MI + WI + FI must hold. (4) The staged G.17
September 2026 values must match a fresh parse of the Board Data
Download file. Signals are computed from levels throughout; the
published ratios are cross-checks only, never inputs.

## Lead-lag evaluation

Total manufacturing signals only. Sign convention: a positive lag k
pairs the signal at month t with the outcome at month t + k, so the
signal leads by k months. Cross-correlations are computed for k in
minus 12 to plus 12 against the capacity utilization level and
against trailing 12-month industrial production growth. The best lag
reported per window is the lag with the largest absolute correlation.

Predictive regressions regress the outcome change over the next h
months (h = 6 and 12; capacity utilization change in percentage
points, industrial production growth in percent) on the current
signal level, by OLS with Newey-West standard errors using maxlags
equal to h, which covers the overlap structure of the overlapping
outcome. Windows, defined on the signal date t: the full common
span; 1992 to 2007; 2008 to 2019; 2020 to present; and the full span
excluding 2020 to 2021 as a sensitivity. Instability is reported
plainly: any window set in which the 12-month coefficient changes
sign, or significance at 5% flips, is flagged in the rendered
documents with the per-window values.

## Pseudo-real-time vintage test

A vintage matrix holds, for each observation month (rows) and each
vintage date (columns), the value whose ALFRED effective interval
contains the vintage date. The builder selects, per cell, the last
interval that has started on or before the column date and verifies
its end is on or after it, so no cell can hold a value first
published after its column date; a unit test proves this against a
brute-force containment check on synthetic intervals.

The first published value of an observation month is its value in
the first vintage containing it. For observation months before mid
2011 that vintage is the opening vintage of the ALFRED record
(2011-06-24), which is a snapshot of history as of that date, not the
original release; the first-versus-final comparison is reported with
that caveat attached. The headline regression comparison uses a
stricter sample: observation months whose first vintage, for both
unfilled orders and shipments, is strictly after 2011-06-24 (so the
first value is a genuine first release of that month) and whose
12-month-ahead utilization outcome is observed. The sample is
identical for the first published and final runs; only the signal
series differs.

## Revision triangle

For AMTMUO, rows are observation months from January 2011. Columns
are the first release, the value in effect 3, 6, and 12 calendar
months after the first release date, and the latest value. A horizon
cell is empty when its date falls after the last vintage in the
record, because the value in effect then is not yet knowable.
Summary statistics are the mean and mean absolute revision from
first release to latest, in percent of the first release.

## Limitations and disclosures

1. M3 is a voluntary, non-probability survey of roughly 4,700
   reporting units, benchmarked to the Economic Census. Conventional
   sampling confidence intervals do not apply to M3 levels or their
   changes, and none are reported. The regression standard errors in
   this project describe uncertainty about the fitted lead-lag
   relationship, nothing about the levels themselves.
2. New orders and unfilled orders exclude semiconductors, so the
   order-book signals omit one of the most cyclical manufacturing
   industries.
3. M3 and G.17 share Census manufacturing source data. Agreement
   between them is not independent confirmation; they are two views
   of substantially the same underlying reports.
4. Values are nominal dollars. Ratios are the object of the
   analysis, so no deflator is applied; dollar levels are reported
   for context and are never interpreted as real quantities.
5. Seasonally adjusted final values are computed with the benefit of
   later data. Any evaluation on final values carries that
   look-ahead; the vintage test addresses it for the backlog signal
   only, and only within the ALFRED record from 2011.
6. ALFRED records value-change intervals, not monthly snapshots.
   The vintage matrix is an exact reconstruction from those
   intervals at the recorded vintage dates, but within-vintage
   timing finer than the recorded dates is not observable.
7. The 2020 to present window contains the pandemic collapse and
   rebound, which dominate any short window's fitted relationships;
   the excluding-2020-to-2021 sensitivity exists for exactly that
   reason, and results are stated with both.
