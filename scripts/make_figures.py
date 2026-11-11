"""Figures for the B3 report, drawn from the processed panel, the
processed vintage matrices, the revision triangle, and
reports/results.json. All values come from pipeline outputs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from factory_cycle import vintages  # noqa: E402
from factory_cycle.loaders import load_g17  # noqa: E402

BLUE = "#30506e"
RUST = "#b0562f"


def main() -> None:
    results = json.loads((ROOT / "reports/results.json").read_text())
    panel = pd.read_parquet(ROOT / "data/processed/signals_panel.parquet")
    panel["month"] = pd.to_datetime(panel["month"])
    g17 = load_g17(str(ROOT / "data/staged/g17.parquet"))
    figdir = ROOT / "figures"
    figdir.mkdir(exist_ok=True)

    # 1. Backlog months and book-to-bill.
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.4), sharex=True)
    for agg, color in [("MTM", BLUE), ("MDM", RUST), ("TCG", "#6a8a5f")]:
        sub = panel[panel["aggregate"] == agg]
        axes[0].plot(sub["month"], sub["backlog_months"], label=agg, color=color)
    axes[0].set_ylabel("Unfilled orders / shipments")
    axes[0].set_title("Backlog in months of shipments")
    axes[0].legend()
    mtm = panel[panel["aggregate"] == "MTM"]
    axes[1].plot(mtm["month"], mtm["book_to_bill"], color=BLUE)
    axes[1].axhline(1.0, color="k", lw=0.8)
    axes[1].set_ylabel("New orders / shipments")
    axes[1].set_title("Book-to-bill, total manufacturing")
    fig.tight_layout()
    fig.savefig(figdir / "fig_backlog_and_book_to_bill.png", dpi=150)
    plt.close(fig)

    # 2. Inventory stages, total manufacturing.
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.4), sharex=True)
    axes[0].plot(
        mtm["month"], 100 * mtm["early_stage_share"], color=BLUE,
        label="Early stage (materials + work in process)",
    )
    axes[0].plot(
        mtm["month"], 100 * mtm["finished_share"], color=RUST, label="Finished goods"
    )
    axes[0].set_ylabel("Share of total inventories, %")
    axes[0].set_title("Inventory stage mix, total manufacturing")
    axes[0].legend()
    axes[1].plot(mtm["month"], 100 * mtm["materials_finished_gap"], color=BLUE)
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].set_ylabel("(Materials - finished) / total, %")
    axes[1].set_title("Materials-to-finished gap, total manufacturing")
    fig.tight_layout()
    fig.savefig(figdir / "fig_inventory_stages.png", dpi=150)
    plt.close(fig)

    # 3. Outcomes: capacity utilization and industrial production growth.
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.4), sharex=True)
    axes[0].plot(g17["month"], g17["mcumfn"], color=BLUE)
    axes[0].set_ylabel("Percent of capacity")
    axes[0].set_title("Capacity utilization, manufacturing (G.17)")
    growth = 100 * (g17["ipman"] / g17["ipman"].shift(12) - 1)
    axes[1].plot(g17["month"], growth, color=RUST)
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].set_ylabel("Percent, 12-month")
    axes[1].set_title("Industrial production growth, manufacturing (G.17)")
    fig.tight_layout()
    fig.savefig(figdir / "fig_outcomes.png", dpi=150)
    plt.close(fig)

    # 4. Cross-correlations, full window: backlog against both outcomes.
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6))
    for ax, outcome, title in [
        (axes[0], "mcumfn", "Backlog vs capacity utilization level"),
        (axes[1], "ipman", "Backlog vs IP 12-month growth"),
    ]:
        by_lag = results["leadlag"]["backlog_months"][outcome]["full"]["xcorr"]["by_lag"]
        lags = sorted(int(k) for k in by_lag)
        vals = [by_lag[str(k)] for k in lags]
        ax.bar(lags, vals, color=BLUE)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xlabel("Lag k (signal at t, outcome at t + k)")
        ax.set_title(title)
    axes[0].set_ylabel("Correlation")
    fig.tight_layout()
    fig.savefig(figdir / "fig_xcorr_backlog.png", dpi=150)
    plt.close(fig)

    # 5. First published versus final backlog months.
    uo = pd.read_parquet(ROOT / "data/processed/amtmuo_vintage_matrix.parquet")
    vs = pd.read_parquet(ROOT / "data/processed/amtmvs_vintage_matrix.parquet")
    uo_first = vintages.first_release(uo)["first_value"]
    vs_first = vintages.first_release(vs)["first_value"]
    first_backlog = uo_first / vs_first
    final_backlog = vintages.final_values(uo) / vintages.final_values(vs)
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.plot(first_backlog.index, first_backlog, color=RUST, label="First published")
    ax.plot(final_backlog.index, final_backlog, color=BLUE, label="Final (latest vintage)")
    ax.set_ylabel("Unfilled orders / shipments, months")
    ax.set_title("Backlog months: first published versus final, total manufacturing")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figdir / "fig_vintage_backlog.png", dpi=150)
    plt.close(fig)

    # 6. Revision triangle heatmap (percent revision from first release).
    tri = pd.read_csv(ROOT / "reports/revision_triangle_amtmuo.csv")
    cols = ["first_release", "plus_3m", "plus_6m", "plus_12m", "latest"]
    pct = 100 * (tri[cols].div(tri["first_release"], axis=0) - 1.0)
    fig, ax = plt.subplots(figsize=(7.5, 9.0))
    image = ax.imshow(
        pct.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-8, vmax=8
    )
    ax.set_xticks(range(len(cols)), ["First", "+3m", "+6m", "+12m", "Latest"])
    years = pd.to_datetime(tri["obs_month"]).dt.year
    ticks = [i for i in range(len(tri)) if i == 0 or years.iloc[i] != years.iloc[i - 1]]
    ax.set_yticks(ticks, [str(years.iloc[i]) for i in ticks])
    ax.set_title("AMTMUO revision triangle: % change from first release")
    fig.colorbar(image, ax=ax, label="% revision")
    fig.tight_layout()
    fig.savefig(figdir / "fig_revision_triangle.png", dpi=150)
    plt.close(fig)

    print("figures written to", figdir)


if __name__ == "__main__":
    main()
