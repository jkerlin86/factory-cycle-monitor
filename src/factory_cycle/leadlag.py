"""Lead-lag evaluation of total manufacturing signals against G.17.

Sign convention: a positive lag k means the signal at month t is
correlated with the outcome at month t + k, so the signal leads the
outcome by k months. A negative lag means the outcome leads.

Predictive regressions are OLS of the outcome change over the next h
months (h = 6 and 12) on the current signal level, with Newey-West
(HAC) standard errors using maxlags = h, which covers the overlap
induced MA(h - 1) structure of the overlapping outcome. The inference
is about the fitted relationship. It is not a sampling statement about
M3 levels: M3 is a voluntary non-probability panel, and no sampling
confidence interval attaches to the levels themselves.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

WINDOWS = {
    "full": (None, None),
    "1992_2007": ("1992-01-01", "2007-12-01"),
    "2008_2019": ("2008-01-01", "2019-12-01"),
    "2020_present": ("2020-01-01", None),
    "excl_2020_2021": ("exclude", "2020-01-01:2021-12-01"),
}


def window_mask(index: pd.DatetimeIndex, window: str) -> pd.Series:
    """Boolean mask over signal dates t for one named window."""
    start, end = WINDOWS[window]
    if start == "exclude":
        lo, hi = end.split(":")
        return pd.Series(
            ~((index >= lo) & (index <= hi)), index=index, dtype=bool
        )
    mask = pd.Series(True, index=index, dtype=bool)
    if start is not None:
        mask &= index >= start
    if end is not None:
        mask &= index <= end
    return mask


def cross_correlations(
    signal: pd.Series, outcome: pd.Series, max_lag: int = 12
) -> dict:
    """Correlations of signal_t with outcome_{t+k} for k in -max_lag..max_lag.

    Pairs are formed on the signal's own index (already windowed by the
    caller): for each lag, signal values are paired with outcome values
    shifted so that outcome_{t+k} aligns with t.
    """
    by_lag = {}
    aligned_outcome = outcome.reindex(
        pd.date_range(outcome.index.min(), outcome.index.max(), freq="MS")
    )
    for k in range(-max_lag, max_lag + 1):
        shifted = aligned_outcome.shift(-k)
        pair = pd.DataFrame({"s": signal, "o": shifted}).dropna()
        if len(pair) >= 24 and pair["s"].std() > 0 and pair["o"].std() > 0:
            by_lag[k] = float(pair["s"].corr(pair["o"]))
        else:
            by_lag[k] = None
    valid = {k: v for k, v in by_lag.items() if v is not None}
    if valid:
        best_lag = max(valid, key=lambda k: abs(valid[k]))
        best = {"best_lag": int(best_lag), "best_corr": float(valid[best_lag])}
    else:
        best = {"best_lag": None, "best_corr": None}
    return {"by_lag": {str(k): v for k, v in by_lag.items()}, **best}


def forward_outcomes(g17: pd.DataFrame) -> pd.DataFrame:
    """Outcome series indexed by signal date t.

    mcumfn_change_h: capacity utilization change over the next h months,
    in percentage points. ipman_growth_h: industrial production growth
    over the next h months, in percent. ipman_growth_12m_trailing: the
    published-style 12-month growth rate dated at its end month, used
    only for cross-correlations.
    """
    g = g17.set_index("month").sort_index()
    out = pd.DataFrame(index=g.index)
    out["mcumfn_level"] = g["mcumfn"]
    out["ipman_growth_12m_trailing"] = 100.0 * (g["ipman"] / g["ipman"].shift(12) - 1.0)
    for h in (6, 12):
        out[f"mcumfn_change_{h}m"] = g["mcumfn"].shift(-h) - g["mcumfn"]
        out[f"ipman_growth_{h}m"] = 100.0 * (g["ipman"].shift(-h) / g["ipman"] - 1.0)
    out.index.name = "month"
    return out


def predictive_regression(
    frame: pd.DataFrame, signal_col: str, outcome_col: str, horizon: int
) -> dict:
    """OLS of outcome on a constant and the signal, Newey-West errors."""
    pair = frame[[signal_col, outcome_col]].dropna()
    n = int(len(pair))
    if n < 24:
        return {
            "n": n,
            "coef": None,
            "se": None,
            "t_stat": None,
            "p_value": None,
            "r2": None,
            "intercept": None,
            "reported": False,
        }
    x = sm.add_constant(pair[signal_col].astype(float))
    y = pair[outcome_col].astype(float)
    fit = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": horizon})
    return {
        "n": n,
        "coef": float(fit.params.iloc[1]),
        "se": float(fit.bse.iloc[1]),
        "t_stat": float(fit.tvalues.iloc[1]),
        "p_value": float(fit.pvalues.iloc[1]),
        "r2": float(fit.rsquared),
        "intercept": float(fit.params.iloc[0]),
        "reported": True,
    }


def evaluate_signal(
    signals_mtm: pd.DataFrame, outcomes: pd.DataFrame, signal_col: str
) -> dict:
    """Full lead-lag evaluation of one signal against both outcomes.

    signals_mtm is the per-aggregate signals frame indexed by month;
    outcomes comes from forward_outcomes. Returns, per outcome and per
    window, the cross-correlations and the 6 and 12 month regressions.
    """
    merged = signals_mtm.join(outcomes, how="inner")
    result: dict = {}
    outcome_specs = {
        "mcumfn": {
            "xcorr_outcome": "mcumfn_level",
            "reg_outcomes": {6: "mcumfn_change_6m", 12: "mcumfn_change_12m"},
        },
        "ipman": {
            "xcorr_outcome": "ipman_growth_12m_trailing",
            "reg_outcomes": {6: "ipman_growth_6m", 12: "ipman_growth_12m"},
        },
    }
    for outcome_name, spec in outcome_specs.items():
        windows = {}
        for window in WINDOWS:
            mask = window_mask(merged.index, window)
            sub = merged[mask]
            entry = {
                "xcorr": cross_correlations(sub[signal_col], merged[spec["xcorr_outcome"]]),
                "xcorr_n_months_in_window": int(mask.sum()),
            }
            for h, col in spec["reg_outcomes"].items():
                entry[f"reg_{h}m"] = predictive_regression(sub, signal_col, col, h)
            windows[window] = entry
        result[outcome_name] = windows
    return result


_WINDOW_SHORT = {
    "full": "full span",
    "1992_2007": "1992 to 2007",
    "2008_2019": "2008 to 2019",
    "2020_present": "2020 to present",
    "excl_2020_2021": "excluding 2020 to 2021",
}
_OUTCOME_SHORT = {"mcumfn": "capacity utilization", "ipman": "IP growth"}


def stability_note(evaluation: dict) -> list[str]:
    """Plain-language instability flags for one signal's evaluation.

    A flag is raised when the headline 12-month regression coefficient
    changes sign, or when significance at 5% flips, across the reported
    windows of an outcome. The note lists the per-window values in
    readable form.
    """
    notes = []
    for outcome_name, windows in evaluation.items():
        coefs = {}
        sig = {}
        for window, entry in windows.items():
            reg = entry["reg_12m"]
            if reg.get("reported"):
                coefs[window] = reg["coef"]
                sig[window] = bool(reg["p_value"] < 0.05)
        label = _OUTCOME_SHORT.get(outcome_name, outcome_name)
        signs = {np.sign(v) for v in coefs.values() if v != 0}
        if len(signs) > 1:
            detail = ", ".join(
                f"{_WINDOW_SHORT[w]} {v:+.2f}" for w, v in coefs.items()
            )
            notes.append(
                f"{label}: the 12-month coefficient changes sign across "
                f"windows ({detail}); the relationship is not stable."
            )
        if len(set(sig.values())) > 1:
            detail = ", ".join(
                f"{_WINDOW_SHORT[w]} {'significant' if v else 'not significant'}"
                for w, v in sig.items()
            )
            notes.append(
                f"{label}: 12-month significance at 5% flips across "
                f"windows ({detail})."
            )
    return notes
