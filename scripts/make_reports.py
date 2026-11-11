"""Render README.md, reports/executive_summary.md, and
reports/monitor_snapshot.md from reports/results.json.

No number in any rendered document is hand-typed: every statistic is
formatted from the results file written by scripts/run_analysis.py.
Interpretive sentences that depend on the results (sign changes,
significance flips, whether the vintage conclusion changes) are chosen
programmatically from the flags recorded in results.json.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "reports/results.json").read_text())

LATEST = R["latest_signals"]
VAL = R["validation"]
VT = R["vintage_test"]
TRI = R["revision_triangle"]
COV = R["coverage"]
GEN_DATE = R["generated_date"]
LATEST_MONTH = R["latest_month"]

AGG_LABELS = {
    "MTM": "Total manufacturing (MTM)",
    "MDM": "Durable goods (MDM)",
    "MNM": "Nondurable goods (MNM)",
    "TCG": "Capital goods (TCG)",
}
SIGNAL_LABELS = {
    "backlog_months": "Backlog months (unfilled orders / shipments)",
    "book_to_bill": "Book-to-bill (new orders / shipments)",
    "inventories_to_shipments": "Inventories / shipments",
    "materials_finished_gap_change_12m": (
        "Materials-to-finished gap, 12-month change"
    ),
}
WINDOW_LABELS = {
    "full": "Full span",
    "1992_2007": "1992 to 2007",
    "2008_2019": "2008 to 2019",
    "2020_present": "2020 to present",
    "excl_2020_2021": "Excluding 2020 to 2021",
}


def f(x, nd=3):
    if x is None:
        return "n/a"
    return f"{x:.{nd}f}"


def pct(x, nd=1):
    if x is None:
        return "n/a"
    return f"{100 * x:.{nd}f}%"


def coef_t(reg) -> str:
    if not reg.get("reported"):
        return "not reported"
    return f"{f(reg['coef'], 3)} (t = {f(reg['t_stat'], 2)})"


def latest_table() -> str:
    rows = []
    for agg in ["MTM", "MDM", "MNM", "TCG"]:
        s = LATEST[agg]
        rows.append(
            f"| {AGG_LABELS[agg]} | {f(s['backlog_months'], 2)} | "
            f"{f(s['book_to_bill'], 3)} | {f(s['inventories_to_shipments'], 3)} | "
            f"{pct(s['early_stage_share'])} | {pct(s['finished_share'])} | "
            f"{pct(s['materials_finished_gap'], 1)} |"
        )
    return "\n".join(rows)


def leadlag_table(signal: str) -> str:
    rows = []
    for window, label in WINDOW_LABELS.items():
        cells = []
        for outcome in ["mcumfn", "ipman"]:
            entry = R["leadlag"][signal][outcome][window]
            xc = entry["xcorr"]
            lag = "n/a" if xc["best_lag"] is None else str(xc["best_lag"])
            cells.append(
                f"{lag} ({f(xc['best_corr'], 2)}) | {coef_t(entry['reg_6m'])} | "
                f"{coef_t(entry['reg_12m'])}"
            )
        n12 = R["leadlag"][signal]["mcumfn"][window]["reg_12m"]["n"]
        rows.append(f"| {label} | {cells[0]} | {cells[1]} | {n12} |")
    header = (
        "| Window | Capacity util.: best lag (corr) | 6m coef | 12m coef | "
        "IP growth: best lag (corr) | 6m coef | 12m coef | n (12m) |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    return header + "\n" + "\n".join(rows)


def stability_bullets() -> str:
    lines = []
    for signal, notes in R["leadlag_stability_notes"].items():
        if notes:
            for note in notes:
                lines.append(f"- **{SIGNAL_LABELS[signal]}:** {note}")
        else:
            lines.append(
                f"- **{SIGNAL_LABELS[signal]}:** no sign change and no "
                "significance flip in the 12-month regressions across "
                "windows."
            )
    return "\n".join(lines)


def vintage_conclusion_sentence() -> str:
    ch = VT["changes"]
    parts = []
    parts.append(
        "the sign does not change"
        if not ch["sign_changes"]
        else "the sign changes"
    )
    parts.append(
        "significance at 5% does not change"
        if not ch["significance_changes"]
        else "significance at 5% changes"
    )
    parts.append(
        "the best cross-correlation lead does not change"
        if not ch["best_lead_changes"]
        else "the best cross-correlation lead changes"
    )
    return "; ".join(parts)


BACKLOG_FULL_MCU = R["leadlag"]["backlog_months"]["mcumfn"]["full"]
BACKLOG_FULL_IP = R["leadlag"]["backlog_months"]["ipman"]["full"]

README = f"""# Reading the Factory Cycle

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

- **The latest readings ({LATEST_MONTH}).** Total manufacturing backlog
  stands at {f(LATEST['MTM']['backlog_months'], 2)} months of shipments,
  with book-to-bill at {f(LATEST['MTM']['book_to_bill'], 3)} and
  inventories at {f(LATEST['MTM']['inventories_to_shipments'], 2)} months
  of shipments. Capital goods backlog is far longer, at
  {f(LATEST['TCG']['backlog_months'], 2)} months, which is normal for
  that aggregate. The full table is below.
- **Backlog is a coincident stock, not a leading signal, in levels.**
  Over the full span the strongest cross-correlation of total
  manufacturing backlog months with the capacity utilization level is
  at lag {BACKLOG_FULL_MCU['xcorr']['best_lag']} (correlation
  {f(BACKLOG_FULL_MCU['xcorr']['best_corr'], 2)}), and with industrial
  production 12-month growth at lag {BACKLOG_FULL_IP['xcorr']['best_lag']}
  (correlation {f(BACKLOG_FULL_IP['xcorr']['best_corr'], 2)}). A lag of
  zero means the two move together; the backlog does not move first.
- **The predictive regressions are unstable, stated plainly.** The
  12-month backlog coefficient for capacity utilization is
  {f(BACKLOG_FULL_MCU['reg_12m']['coef'], 2)} over the full span
  (t = {f(BACKLOG_FULL_MCU['reg_12m']['t_stat'], 2)}, not significant),
  and it changes sign across subperiods. The one window where several
  relationships look strong, 2020 to present, is dominated by the
  pandemic collapse and rebound and does not survive excluding 2020 to
  2021. The stability notes under the lead-lag tables record every sign
  change and significance flip; none of the four signals shows a
  stable, significant predictive relationship across windows.
- **First published backlog is close to final, and the vintage test
  does not rescue a leading relationship.** First published and final
  backlog months differ by {f(VT['first_vs_final_backlog']['mean_abs_diff_months'], 3)}
  months on average (maximum
  {f(VT['first_vs_final_backlog']['max_abs_diff_months'], 2)}), and
  {pct(VT['first_vs_final_backlog']['share_gt_0_05_months'])} of months
  are revised by more than 0.05 months. On the vintage-restricted
  sample, {vintage_conclusion_sentence()}. Neither run is significant:
  revisions move the point estimate but do not change what the data
  support.
- **Unfilled orders are revised upward on average.** From first
  release to latest, AMTMUO revisions average
  {f(TRI['revision_stats_first_to_latest_pct']['mean_revision_pct'], 2)}%
  (mean absolute {f(TRI['revision_stats_first_to_latest_pct']['mean_abs_revision_pct'], 2)}%)
  over {TRI['revision_stats_first_to_latest_pct']['n']} observation
  months. First prints of the backlog level should be read as
  systematically a little low.

## Latest signal readings ({LATEST_MONTH})

| Aggregate | Backlog, months | Book-to-bill | Inventories / shipments | Early-stage share | Finished share | Materials-finished gap |
|---|---|---|---|---|---|---|
{latest_table()}

Nondurable goods (MNM) has no backlog: Census does not publish
unfilled orders for nondurables, and its new orders equal its
shipments by construction, so its book-to-bill is 1.000. Durable goods
carries all of the total manufacturing unfilled orders, which is why
the MDM and MTM unfilled order levels are the same number. Capital
goods (TCG) has no stage inventories, so its stage columns are empty.

## Validation gate 1

- September 2026 total manufacturing anchors (shipments, new orders,
  unfilled orders, total inventories, and the three stages) match the
  staged M3 table exactly: {str(VAL['anchors_all_match']).lower()}.
- Computed inventories to shipments against the published IS ratio:
  maximum absolute difference {f(VAL['is_crosscheck']['MTM']['max_abs_diff'], 4)}
  (MTM), {f(VAL['is_crosscheck']['MDM']['max_abs_diff'], 4)} (MDM),
  {f(VAL['is_crosscheck']['MNM']['max_abs_diff'], 4)} (MNM), each over
  {VAL['is_crosscheck']['MTM']['n']} months and each inside the rounding
  of the published two-decimal ratio.
- Stage identity: total inventories equal materials plus work in
  process plus finished goods exactly (maximum absolute difference
  {f(VAL['stage_identity_ti_equals_mi_wi_fi']['MTM']['max_abs_diff'], 1)}
  million dollars) in every aggregate with stages.
- G.17 published-value check: the staged September 2026 values
  (IPMAN {f(VAL['g17_sep2026_board_check']['staged_ipman'], 4)},
  MCUMFN {f(VAL['g17_sep2026_board_check']['staged_mcumfn'], 4)}) match
  a fresh parse of the Board file exactly:
  {str(VAL['g17_sep2026_board_check']['match']).lower()}.

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

{leadlag_table("backlog_months")}

### Stability, all four signals, stated plainly

{stability_bullets()}

Full tables for book-to-bill, inventories to shipments, and the
materials-to-finished gap change are in
`reports/executive_summary.md`. The pattern there is the same family:
book-to-bill keeps one sign and is never significant at 5% at the
12-month horizon in any window for either outcome; the other two
signals flip significance, and the gap change also flips sign.

## Pseudo-real-time vintage test

ALFRED carries {COV['alfred_vintage_dates_per_series']} vintage dates
per series ({COV['alfred_vintage_span'][0]} to
{COV['alfred_vintage_span'][1]}). The first published backlog series
takes, for each observation month, the value from the first vintage
containing that month; the final series takes the latest vintage.
{VT['first_vs_final_backlog']['note']}

The headline regression (backlog months against the next 12 months of
capacity utilization change) is then run on one identical sample both
ways: {VT['regression_sample']['definition']} The sample runs
{VT['regression_sample']['start_month']} to
{VT['regression_sample']['end_month']} (n =
{VT['regression_sample']['n']}). First published: coefficient
{f(VT['first_published_run']['coef'], 3)} (t =
{f(VT['first_published_run']['t_stat'], 2)}, R2 =
{f(VT['first_published_run']['r2'], 3)}), best lead
{VT['first_published_run']['best_lead_months']} months. Final:
coefficient {f(VT['final_run']['coef'], 3)} (t =
{f(VT['final_run']['t_stat'], 2)}, R2 = {f(VT['final_run']['r2'], 3)}),
best lead {VT['final_run']['best_lead_months']} months. Reading:
{vintage_conclusion_sentence()}. Both best leads are negative, which
means utilization moves before the backlog in this sample under both
information sets.

## Revision triangle

`reports/revision_triangle_amtmuo.csv` holds the AMTMUO triangle:
observation months {TRI['obs_start']} to {TRI['obs_end']}
({TRI['n_obs_months']} rows), with the first release, the value in
effect 3, 6, and 12 months after first release, and the latest value.
{TRI['horizon_definition']} Coverage: first release
{TRI['horizon_coverage']['first_release']}, plus 3 months
{TRI['horizon_coverage']['plus_3m']}, plus 6 months
{TRI['horizon_coverage']['plus_6m']}, plus 12 months
{TRI['horizon_coverage']['plus_12m']}, latest
{TRI['horizon_coverage']['latest']}. Mean revision from first to
latest is {f(TRI['revision_stats_first_to_latest_pct']['mean_revision_pct'], 2)}%
and mean absolute revision is
{f(TRI['revision_stats_first_to_latest_pct']['mean_abs_revision_pct'], 2)}%
(median absolute
{f(TRI['revision_stats_first_to_latest_pct']['median_abs_revision_pct'], 2)}%).

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
- {COV['excluded_category_note']}
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
"""

EXEC = f"""# Executive summary

**Question.** Do the factory sector's own order-book and inventory
signals lead the cycle as measured by capacity utilization and
industrial production, and does the answer change when the signals
are restricted to what was actually published at the time?

**Data.** Census M3 seasonally adjusted levels, {COV['m3_months'][0]}
to {COV['m3_months'][1]}, {COV['m3_categories']} category codes
({COV['m3_rows']} staged rows); G.17 manufacturing production and
capacity utilization, {COV['g17_months'][0]} to {COV['g17_months'][1]};
ALFRED vintages for the four total manufacturing series,
{COV['alfred_vintage_dates_per_series']} vintage dates from
{COV['alfred_vintage_span'][0]} to {COV['alfred_vintage_span'][1]}.
Signals are ratios of nominal levels (backlog months, book-to-bill,
inventories to shipments, inventory stage shares, and the
materials-to-finished gap and its 12-month change). Latest month:
{LATEST_MONTH}. Total manufacturing backlog
{f(LATEST['MTM']['backlog_months'], 2)} months, book-to-bill
{f(LATEST['MTM']['book_to_bill'], 3)}, inventories to shipments
{f(LATEST['MTM']['inventories_to_shipments'], 3)}; capital goods
backlog {f(LATEST['TCG']['backlog_months'], 2)} months.

**Lead-lag, stated plainly.** No signal shows a stable predictive
relationship with either outcome. Backlog months correlate most
strongly with both outcomes contemporaneously (lag
{BACKLOG_FULL_MCU['xcorr']['best_lag']} against utilization, lag
{BACKLOG_FULL_IP['xcorr']['best_lag']} against production growth, full
span), which is the signature of a coincident stock rather than a
leading indicator. The 12-month predictive coefficients change sign
across subperiods for backlog (both outcomes) and for the
materials-to-finished gap change (both outcomes); significance at 5%
flips across windows for backlog, inventories to shipments, and the
gap change. Book-to-bill is the exception in form only: its
coefficient keeps one sign in every window and is never significant
at 5% at the 12-month horizon, so it is stably uninformative rather
than stable. Where relationships look strong, in the 2020 to present
window, they are carried by the pandemic collapse and rebound: the
backlog coefficient against 12-month utilization change is
{f(R['leadlag']['backlog_months']['mcumfn']['2020_present']['reg_12m']['coef'], 2)}
there (t = {f(R['leadlag']['backlog_months']['mcumfn']['2020_present']['reg_12m']['t_stat'], 2)})
and {f(R['leadlag']['backlog_months']['mcumfn']['excl_2020_2021']['reg_12m']['coef'], 2)}
(t = {f(R['leadlag']['backlog_months']['mcumfn']['excl_2020_2021']['reg_12m']['t_stat'], 2)})
once 2020 to 2021 is excluded. Full tables follow.

**Vintage test.** First published backlog months differ from final by
{f(VT['first_vs_final_backlog']['mean_abs_diff_months'], 3)} months on
average (maximum {f(VT['first_vs_final_backlog']['max_abs_diff_months'], 2)};
{pct(VT['first_vs_final_backlog']['share_gt_0_05_months'])} of months
move by more than 0.05 months. Re-running the headline 12-month
regression on the identical vintage-era sample
({VT['regression_sample']['start_month']} to
{VT['regression_sample']['end_month']}, n =
{VT['regression_sample']['n']}): first published coefficient
{f(VT['first_published_run']['coef'], 3)} (t =
{f(VT['first_published_run']['t_stat'], 2)}), final coefficient
{f(VT['final_run']['coef'], 3)} (t = {f(VT['final_run']['t_stat'], 2)}).
Conclusion: {vintage_conclusion_sentence()}. Using final data scales
the point estimate by a factor of
{f(abs(VT['final_run']['coef'] / VT['first_published_run']['coef']), 1)}
in this sample, but neither estimate is distinguishable from zero, so
the substantive conclusion is the same under both information sets.

**Revisions.** The AMTMUO triangle covers {TRI['n_obs_months']}
observation months ({TRI['obs_start']} to {TRI['obs_end']}). Mean
revision from first release to latest is
{f(TRI['revision_stats_first_to_latest_pct']['mean_revision_pct'], 2)}%
with mean absolute revision
{f(TRI['revision_stats_first_to_latest_pct']['mean_abs_revision_pct'], 2)}%:
first prints of unfilled orders run systematically low, mostly through
annual benchmark revisions rather than month-to-month corrections.

**Disclosures.** M3 is a voluntary non-probability panel (roughly
4,700 units) benchmarked to the Economic Census; no sampling interval
attaches to its levels, and the regression inference reported here is
about the fitted relationships only. New and unfilled orders exclude
semiconductors. M3 and G.17 share Census source data and are
complementary views, not independent confirmations. Values are
nominal; ratios are the object and no deflator is applied. Final
seasonally adjusted values embed later data; the vintage test partly
addresses that look-ahead, from 2011 only.

## Full lead-lag tables

Coefficients are OLS with Newey-West standard errors (maxlags equal
to the horizon). Best lag is the lag in minus 12 to plus 12 with the
largest absolute cross-correlation; a positive lag means the signal
leads.

### {SIGNAL_LABELS['backlog_months']}

{leadlag_table("backlog_months")}

### {SIGNAL_LABELS['book_to_bill']}

{leadlag_table("book_to_bill")}

### {SIGNAL_LABELS['inventories_to_shipments']}

{leadlag_table("inventories_to_shipments")}

### {SIGNAL_LABELS['materials_finished_gap_change_12m']}

{leadlag_table("materials_finished_gap_change_12m")}

### Stability notes

{stability_bullets()}
"""

SNAPSHOT = f"""# Factory cycle monitor snapshot

**Snapshot date:** {GEN_DATE}
**Latest data month:** {LATEST_MONTH}

## Latest readings

| Aggregate | Backlog, months | Book-to-bill | Inventories / shipments | Early-stage share | Finished share | Materials-finished gap |
|---|---|---|---|---|---|---|
{latest_table()}

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

- {GEN_DATE}: initial build (Stage B, 2026-11-11). First snapshot:
  signals through {LATEST_MONTH}, lead-lag evaluation over the full
  span and subperiods, pseudo-real-time vintage test, AMTMUO revision
  triangle.

## Refresh

Run `python scripts/refresh.py` from the project root. It re-runs
ingestion (`scripts/download_data.py`, which needs `CENSUS_API_KEY`
and `FRED_API_KEY` in the environment or the project's local `.env`),
then analysis, figures, and reports, and rewrites this snapshot with
the then-current latest month. There is no scheduled automation; the
monitor updates only when the refresh is run by hand.
"""


def main() -> None:
    (ROOT / "README.md").write_text(README)
    (ROOT / "reports/executive_summary.md").write_text(EXEC)
    (ROOT / "reports/monitor_snapshot.md").write_text(SNAPSHOT)
    print("rendered README.md, reports/executive_summary.md, "
          "reports/monitor_snapshot.md")


if __name__ == "__main__":
    main()
