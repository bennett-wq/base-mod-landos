"""Verify src/engine/ package structure. Tests in M1-5 onward replace these with real assertions."""

import pytest


def test_engine_package_importable():
    """AC M1-2.1: src.engine can be imported as a package."""
    import src.engine  # noqa: F401


def test_all_engine_modules_importable():
    """AC M1-2.2: all eight engine modules can be imported without error."""
    from src.engine import (  # noqa: F401
        envelope,
        models,
        cost,
        pricing,
        margin,
        sensitivity,
        recommendation,
        market_stats,
    )
