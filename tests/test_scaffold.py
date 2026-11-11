"""Placeholder tests for the Stage A scaffold.

The ingestion verification for Stage A is run by scripts/download_data.py
itself (row counts, spans, key uniqueness, and the September 2026 MTM
anchor check). Analysis tests arrive with the analysis stage.
"""

from factory_cycle import __doc__  # noqa: F401


def test_package_imports():
    assert __doc__ is not None
