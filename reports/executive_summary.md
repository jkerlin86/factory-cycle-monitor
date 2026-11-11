# Executive summary

**Question.** Do the factory sector's own order-book and inventory
signals lead the cycle as measured by capacity utilization and
industrial production, and does the answer change when the signals
are restricted to what was actually published at the time?

**Data.** Census M3 seasonally adjusted levels, 1992-01
to 2026-09, 87 category codes
(146535 staged rows); G.17 manufacturing production and
capacity utilization, 1972-01 to 2026-09;
ALFRED vintages for the four total manufacturing series,
191 vintage dates from
2011-06-24 to 2026-11-03.
Signals are ratios of nominal levels (backlog months, book-to-bill,
inventories to shipments, inventory stage shares, and the
materials-to-finished gap and its 12-month change). Latest month:
2026-09. Total manufacturing backlog
2.43 months, book-to-bill
1.013, inventories to shipments
1.460; capital goods
backlog 10.20 months.

**Lead-lag, stated plainly.** No signal shows a stable predictive
relationship with either outcome. Backlog months correlate most
strongly with both outcomes contemporaneously (lag
0 against utilization, lag
0 against production growth, full
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
16.85
there (t = 3.48)
and 0.15
(t = 0.16)
once 2020 to 2021 is excluded. Full tables follow.

**Vintage test.** First published backlog months differ from final by
0.063 months on
average (maximum 0.27;
44.1% of months
move by more than 0.05 months. Re-running the headline 12-month
regression on the identical vintage-era sample
(2011-05 to
2025-09, n =
173): first published coefficient
0.537 (t =
0.21), final coefficient
2.600 (t = 1.11).
Conclusion: the sign does not change; significance at 5% does not change; the best cross-correlation lead changes. Using final data scales
the point estimate by a factor of
4.8
in this sample, but neither estimate is distinguishable from zero, so
the substantive conclusion is the same under both information sets.

**Revisions.** The AMTMUO triangle covers 189
observation months (2011-01 to 2026-09). Mean
revision from first release to latest is
2.13%
with mean absolute revision
3.83%:
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

### Backlog months (unfilled orders / shipments)

| Window | Capacity util.: best lag (corr) | 6m coef | 12m coef | IP growth: best lag (corr) | 6m coef | 12m coef | n (12m) |
|---|---|---|---|---|---|---|---|
| Full span | 0 (-0.43) | 0.256 (t = 0.49) | 0.695 (t = 0.73) | 0 (-0.51) | -1.864 (t = -2.56) | -3.620 (t = -2.79) | 405 |
| 1992 to 2007 | -12 (0.15) | 0.086 (t = 0.08) | -2.307 (t = -0.57) | 12 (-0.25) | -1.075 (t = -0.64) | -6.194 (t = -1.03) | 192 |
| 2008 to 2019 | -12 (0.56) | 0.380 (t = 0.25) | 1.853 (t = 0.54) | 1 (-0.40) | -0.163 (t = -0.08) | 1.217 (t = 0.26) | 144 |
| 2020 to present | 0 (-0.83) | 11.322 (t = 2.35) | 16.852 (t = 3.48) | 12 (0.80) | 16.996 (t = 2.50) | 23.906 (t = 3.82) | 69 |
| Excluding 2020 to 2021 | 3 (-0.41) | -0.160 (t = -0.35) | 0.150 (t = 0.16) | 0 (-0.53) | -2.449 (t = -3.93) | -4.370 (t = -3.45) | 381 |

### Book-to-bill (new orders / shipments)

| Window | Capacity util.: best lag (corr) | 6m coef | 12m coef | IP growth: best lag (corr) | 6m coef | 12m coef | n (12m) |
|---|---|---|---|---|---|---|---|
| Full span | -12 (-0.20) | -1.286 (t = -0.14) | -24.297 (t = -1.11) | 0 (0.29) | -10.144 (t = -0.78) | -48.881 (t = -1.76) | 404 |
| 1992 to 2007 | -12 (-0.13) | 3.968 (t = 0.41) | -23.033 (t = -0.92) | 12 (-0.23) | -7.107 (t = -0.49) | -54.037 (t = -1.30) | 191 |
| 2008 to 2019 | 2 (0.41) | -1.256 (t = -0.08) | -26.654 (t = -0.77) | -1 (0.60) | 2.332 (t = 0.11) | -29.691 (t = -0.67) | 144 |
| 2020 to present | 1 (0.44) | -39.368 (t = -1.11) | -59.330 (t = -1.22) | 1 (0.50) | -55.896 (t = -1.13) | -79.712 (t = -1.24) | 69 |
| Excluding 2020 to 2021 | -12 (-0.18) | 0.398 (t = 0.04) | -23.210 (t = -0.99) | 0 (0.28) | -6.362 (t = -0.48) | -45.065 (t = -1.52) | 380 |

### Inventories / shipments

| Window | Capacity util.: best lag (corr) | 6m coef | 12m coef | IP growth: best lag (corr) | 6m coef | 12m coef | n (12m) |
|---|---|---|---|---|---|---|---|
| Full span | -12 (0.23) | 1.841 (t = 0.78) | 4.344 (t = 1.00) | 0 (-0.24) | 3.004 (t = 0.93) | 6.832 (t = 1.12) | 405 |
| 1992 to 2007 | -12 (0.66) | -0.539 (t = -0.36) | 1.241 (t = 0.31) | -12 (0.40) | 4.065 (t = 2.42) | 11.455 (t = 2.19) | 192 |
| 2008 to 2019 | -12 (0.49) | -1.056 (t = -0.09) | 10.910 (t = 0.58) | 0 (-0.46) | -2.204 (t = -0.14) | 12.503 (t = 0.48) | 144 |
| 2020 to present | 0 (-0.79) | 23.987 (t = 2.34) | 29.203 (t = 2.72) | 12 (0.75) | 36.982 (t = 2.66) | 43.913 (t = 3.23) | 69 |
| Excluding 2020 to 2021 | -12 (0.29) | -0.557 (t = -0.30) | 1.498 (t = 0.36) | 0 (-0.17) | 0.397 (t = 0.14) | 4.625 (t = 0.71) | 381 |

### Materials-to-finished gap, 12-month change

| Window | Capacity util.: best lag (corr) | 6m coef | 12m coef | IP growth: best lag (corr) | 6m coef | 12m coef | n (12m) |
|---|---|---|---|---|---|---|---|
| Full span | -5 (0.16) | -8.680 (t = -0.34) | -40.383 (t = -1.06) | -7 (0.16) | -21.798 (t = -0.62) | -70.820 (t = -1.34) | 393 |
| 1992 to 2007 | 4 (0.45) | 11.845 (t = 0.37) | -8.743 (t = -0.18) | 1 (0.46) | 34.088 (t = 0.86) | 42.094 (t = 0.64) | 180 |
| 2008 to 2019 | -8 (0.50) | -107.122 (t = -2.29) | -188.938 (t = -3.04) | -12 (0.47) | -133.868 (t = -2.04) | -239.222 (t = -2.74) | 144 |
| 2020 to present | 8 (0.56) | 47.069 (t = 0.98) | 40.520 (t = 0.55) | -6 (0.44) | 55.864 (t = 0.85) | 36.744 (t = 0.39) | 69 |
| Excluding 2020 to 2021 | -5 (0.23) | -38.512 (t = -1.59) | -82.250 (t = -2.27) | -9 (0.27) | -54.136 (t = -1.53) | -108.942 (t = -1.85) | 369 |

### Stability notes

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
