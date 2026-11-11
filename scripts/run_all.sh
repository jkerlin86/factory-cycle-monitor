#!/usr/bin/env bash
# Full pipeline from staged data: analysis, figures, notebooks, reports,
# archive staging, tests, lint. Ingestion is separate (needs API keys):
# run scripts/download_data.py or scripts/refresh.py first.
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/run_analysis.py
python scripts/make_figures.py
python scripts/make_notebooks.py
python scripts/execute_notebooks.py
python scripts/make_reports.py
python scripts/make_archive.py
python -m pytest tests -q
python -m ruff check src scripts tests
