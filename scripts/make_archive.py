"""Stage the clean-data archive bundle (not uploaded).

Copies the constructed signals panel, the two ALFRED vintage matrices
used by the vintage test, and the AMTMUO revision triangle to the
portfolio clean-data archive with a manifest.json carrying per-file
SHA-256, row and column counts, the source files with their checksums
taken from data/raw/manifest.json, the generation date, and the repo
URL of record. Verifies one headline number (the September 2026 total
manufacturing backlog) recomputed from the archived panel against
reports/results.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (
    Path.home()
    / "workspace/data-science-portfolio/clean-data-archive/B3_factory_cycle_monitor"
)
REPO_URL = "https://github.com/jkerlin86/factory-cycle-monitor"

FILES = [
    (
        ROOT / "data/processed/signals_panel.csv",
        "tidy constructed signals panel: one row per month per aggregate "
        "(MTM, MDM, MNM, TCG) with the M3 levels and the ratio signals",
    ),
    (
        ROOT / "data/processed/amtmuo_vintage_matrix.parquet",
        "vintage matrix for ALFRED AMTMUO (unfilled orders, total "
        "manufacturing): rows are observation months, columns are "
        "vintage dates, cells are the value in effect at that vintage",
    ),
    (
        ROOT / "data/processed/amtmvs_vintage_matrix.parquet",
        "vintage matrix for ALFRED AMTMVS (shipments, total "
        "manufacturing), same layout as the AMTMUO matrix",
    ),
    (
        ROOT / "reports/revision_triangle_amtmuo.csv",
        "AMTMUO revision triangle: first release, values in effect 3, 6, "
        "and 12 months after first release, and the latest value, for "
        "observation months 2011-01 to 2026-09",
    ),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _shape(path: Path) -> tuple[int, int]:
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path)
    return int(frame.shape[0]), int(frame.shape[1])


def main() -> None:
    results = json.loads((ROOT / "reports/results.json").read_text())
    raw_manifest = json.loads((ROOT / "data/raw/manifest.json").read_text())
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    files = []
    for source, content in FILES:
        staged = ARCHIVE / source.name
        shutil.copyfile(source, staged)
        rows, cols = _shape(staged)
        files.append(
            {
                "file": staged.name,
                "sha256": sha256(staged),
                "bytes": staged.stat().st_size,
                "rows": rows,
                "columns": cols,
                "content": content,
            }
        )

    panel = pd.read_csv(ARCHIVE / "signals_panel.csv")
    row = panel[
        (panel["aggregate"] == "MTM") & (panel["month"] == "2026-09-01")
    ].iloc[0]
    expected = results["latest_signals"]["MTM"]["backlog_months"]
    verification = {
        "statistic": "backlog_months, MTM, 2026-09, from the archived panel",
        "archived_panel_value": float(row["backlog_months"]),
        "results_json_value": expected,
        "match": bool(abs(float(row["backlog_months"]) - expected) < 1e-9),
    }
    assert verification["match"]

    sources = []
    for rel, info in sorted(raw_manifest["files"].items()):
        sources.append(
            {
                "source_file": f"data/raw/{rel}",
                "sha256": info["sha256"],
                "bytes": info["bytes"],
                "source_url": info["source_url"],
            }
        )
    for name, info in sorted(raw_manifest.get("staged", {}).items()):
        sources.append(
            {
                "source_file": f"data/staged/{name}",
                "sha256": info["sha256"],
                "bytes": info["bytes"],
                "source_url": "staged by scripts/download_data.py from the raw files above",
            }
        )
    manifest = {
        "project": "B3, Reading the Factory Cycle: Unfilled Orders, "
        "Inventory Stages, and Capacity Utilization, 1992-Present "
        "(roadmap Project 8)",
        "repo_url": REPO_URL,
        "generated_date": date.today().isoformat(),
        "retrieval_date": raw_manifest["retrieval_date"],
        "files": files,
        "sources": sources,
        "notes": [
            "All underlying observations are U.S. federal statistical "
            "agency data (Census Bureau M3, Federal Reserve G.17, and "
            "Census series as archived by ALFRED), public domain at the "
            "originator.",
            "The vintage matrices are reconstructions from ALFRED "
            "value-change intervals at the recorded vintage dates.",
            "No file exceeds the size threshold for chunking; every "
            "file is staged whole.",
        ],
        "verification": verification,
    }
    (ARCHIVE / "manifest.json").write_text(json.dumps(manifest, indent=2))
    total = sum(f["bytes"] for f in files) + (ARCHIVE / "manifest.json").stat().st_size
    print(f"archive staged at {ARCHIVE}: {len(files)} data files, total {total} bytes")


if __name__ == "__main__":
    main()
