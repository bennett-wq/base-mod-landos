"""AC M1-5: compute_envelope reproduces McCartney 1888 buildable envelope.

Spec §6 envelope.py and §9 item 2 (canonical Regrid GeoPackage techniques).
"""

import json
from pathlib import Path

import pytest

from src.engine.envelope import compute_envelope
from src.models.opportunity import SetbackRules

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mccartney"


@pytest.fixture
def mccartney_polygon_wkb() -> bytes:
    with open(FIXTURE_DIR / "1888_mccartney_polygon.wkb", "rb") as f:
        return f.read()


@pytest.fixture
def ypsi_r5_setbacks() -> SetbackRules:
    data = json.loads((FIXTURE_DIR / "ypsi_twp_r5_setbacks.json").read_text())
    return SetbackRules(**data)


def test_compute_envelope_mccartney_1888(mccartney_polygon_wkb, ypsi_r5_setbacks):
    """AC M1-5.1: McCartney 1888 → buildable ~40.5 × 57.1 ft, envelope ~2311 sf, cov cap ~2206 sf.

    Source: 04 - Developments/1888 McCartney Package — Underwriting.md Phase B table.
    """
    result = compute_envelope(
        polygon_wkb=mccartney_polygon_wkb,
        setbacks=ypsi_r5_setbacks,
        lat=42.2187,
    )
    assert result.buildable_width_ft == pytest.approx(40.5, abs=1.0)
    assert result.buildable_depth_ft == pytest.approx(57.1, abs=1.0)
    assert result.envelope_area_sf == pytest.approx(2311.0, abs=30.0)
    assert result.coverage_cap_sf == pytest.approx(2206.0, abs=30.0)
    assert result.binding_constraint in ("depth", "width", "coverage")
