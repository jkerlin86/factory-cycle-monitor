"""Build the two analysis notebooks (unexecuted). Execute with
scripts/execute_notebooks.py. Notebooks read the package and the
staged data files directly, so every number they show is recomputed,
not copied.
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"

SETUP = """import sys
sys.path.insert(0, "../src")
import pandas as pd
from factory_cycle.loaders import load_m3_levels, load_g17, load_alfred_vintages
from factory_cycle import signals as sig
pd.set_option("display.width", 140)
m3 = load_m3_levels("../data/staged/m3_levels.parquet")
g17 = load_g17("../data/staged/g17.parquet")
panel = sig.build_signals_panel(m3)
"""


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def nb1():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "name": "python3"}
    nb.cells = [
        md(
            "# Signals and the factory cycle\n\n"
            "The signals are ratios of Census M3 seasonally adjusted levels: "
            "backlog months (unfilled orders over shipments), book-to-bill "
            "(new orders over shipments), inventories to shipments, the "
            "inventory stage shares, and the materials-to-finished gap, "
            "(materials minus finished goods) over total inventories. The "
            "gap is the project's primary divergence measure: the alternative "
            "difference of share changes is identically twice the change in "
            "the early-stage share, because the three stages sum to total "
            "inventories."
        ),
        code(SETUP),
        md("## The panel: one row per month per aggregate"),
        code("panel.head(8)"),
        md(
            "## Latest readings\n\n"
            "Nondurable goods has no backlog (Census publishes no unfilled "
            "orders for nondurables) and its book-to-bill is 1 by "
            "construction. Capital goods has no stage inventories."
        ),
        code(
            "latest = panel.sort_values('month').groupby('aggregate').tail(1)\n"
            "latest[['aggregate', 'month', 'backlog_months', 'book_to_bill', "
            "'inventories_to_shipments', 'early_stage_share', "
            "'finished_share', 'materials_finished_gap']]"
        ),
        md(
            "## Validation: computed inventories to shipments against the "
            "published IS ratio\n\n"
            "The published ratio is rounded to two decimals, so agreement "
            "to within about 0.005 is exact agreement."
        ),
        code("sig.is_crosscheck(m3, ['MTM', 'MDM', 'MNM'])"),
        md("## Backlog months over the full span"),
        code(
            "import matplotlib.pyplot as plt\n"
            "fig, ax = plt.subplots(figsize=(9, 3.4))\n"
            "for agg in ['MTM', 'MDM', 'TCG']:\n"
            "    sub = panel[panel['aggregate'] == agg]\n"
            "    ax.plot(sub['month'], sub['backlog_months'], label=agg)\n"
            "ax.set_ylabel('Unfilled orders / shipments')\n"
            "ax.legend()\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
        md(
            "## Inventory stage mix, total manufacturing\n\n"
            "The early-stage share and the finished share sum to 1. The "
            "materials-to-finished gap compares the two ends of the "
            "pipeline directly."
        ),
        code(
            "mtm = panel[panel['aggregate'] == 'MTM']\n"
            "fig, ax = plt.subplots(figsize=(9, 3.4))\n"
            "ax.plot(mtm['month'], 100 * mtm['early_stage_share'], label='Early stage')\n"
            "ax.plot(mtm['month'], 100 * mtm['finished_share'], label='Finished')\n"
            "ax.set_ylabel('Share of total inventories, %')\n"
            "ax.legend()\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
    ]
    nbf.write(nb, NB / "01_signals_and_the_cycle.ipynb")


def nb2():
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "name": "python3"}
    nb.cells = [
        md(
            "# Lead-lag and the vintage test\n\n"
            "Sign convention: a positive lag k pairs the signal at month t "
            "with the outcome at month t + k, so the signal leads by k. "
            "Predictive regressions use OLS with Newey-West standard errors "
            "(maxlags equal to the horizon). The inference describes the "
            "fitted relationship; M3 is a voluntary non-probability panel, "
            "and no sampling interval attaches to its levels."
        ),
        code(
            SETUP
            + "from factory_cycle import leadlag, vintages\n"
            + "outcomes = leadlag.forward_outcomes(g17)\n"
            + "mtm = panel[panel['aggregate'] == 'MTM'].set_index('month')\n"
        ),
        md("## Backlog months: cross-correlations and regressions by window"),
        code(
            "ev = leadlag.evaluate_signal(mtm, outcomes, 'backlog_months')\n"
            "rows = []\n"
            "for outcome in ['mcumfn', 'ipman']:\n"
            "    for window, entry in ev[outcome].items():\n"
            "        reg = entry['reg_12m']\n"
            "        rows.append({'outcome': outcome, 'window': window,\n"
            "                     'best_lag': entry['xcorr']['best_lag'],\n"
            "                     'best_corr': entry['xcorr']['best_corr'],\n"
            "                     'coef_12m': reg['coef'], 't_12m': reg['t_stat'],\n"
            "                     'r2': reg['r2'], 'n': reg['n']})\n"
            "pd.DataFrame(rows)"
        ),
        md(
            "## Stability, stated plainly\n\n"
            "The helper flags every sign change and every significance flip "
            "in the 12-month regressions across windows."
        ),
        code("leadlag.stability_note(ev)"),
        md(
            "## Vintage matrices from the ALFRED intervals\n\n"
            "Each cell is the value whose effective interval contains the "
            "column's vintage date. The builder can only select an interval "
            "that had already started at that date."
        ),
        code(
            "alfred = load_alfred_vintages("
            "'../data/staged/alfred_vintages_long.parquet')\n"
            "uo = vintages.build_vintage_matrix(alfred, 'AMTMUO')\n"
            "vs = vintages.build_vintage_matrix(alfred, 'AMTMVS')\n"
            "print('matrix shape (obs months x vintages):', uo.shape)\n"
            "uo.iloc[-3:, -3:]"
        ),
        md("## First published versus final backlog months"),
        code(
            "first_bl = (vintages.first_release(uo)['first_value'] /\n"
            "            vintages.first_release(vs)['first_value'])\n"
            "final_bl = vintages.final_values(uo) / vintages.final_values(vs)\n"
            "diff = (first_bl - final_bl).abs().dropna()\n"
            "{'n_months': int(len(diff)),\n"
            " 'mean_abs_diff_months': float(diff.mean()),\n"
            " 'max_abs_diff_months': float(diff.max()),\n"
            " 'share_gt_0_05': float((diff > 0.05).mean())}"
        ),
        md(
            "## The AMTMUO revision triangle (first rows)\n\n"
            "Horizon columns hold the value in effect 3, 6, and 12 months "
            "after the first release date; they are empty when that date "
            "falls after the last vintage in the record."
        ),
        code(
            "tri = vintages.revision_triangle(alfred, 'AMTMUO', "
            "obs_start='2011-01-01')\n"
            "tri.head(6)"
        ),
        code("vintages.triangle_revision_stats(tri)"),
    ]
    nbf.write(nb, NB / "02_leadlag_and_vintages.ipynb")


if __name__ == "__main__":
    NB.mkdir(exist_ok=True)
    nb1()
    nb2()
    print("notebooks built")
