"""One-command monitor refresh: ingestion, analysis, figures, reports.

Re-downloads from the official sources (scripts/download_data.py,
which needs CENSUS_API_KEY and FRED_API_KEY in the environment or the
project's local .env), then re-runs the analysis, the figures, and
the report rendering, which rewrites reports/monitor_snapshot.md with
the new latest month. There is no scheduling: the monitor updates
only when this script is run by hand.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    "scripts/download_data.py",
    "scripts/run_analysis.py",
    "scripts/make_figures.py",
    "scripts/make_reports.py",
]


def main() -> None:
    for step in STEPS:
        print(f"== {step} ==", flush=True)
        subprocess.run(
            [sys.executable, step], cwd=ROOT, check=True
        )
    print("refresh complete")


if __name__ == "__main__":
    main()
