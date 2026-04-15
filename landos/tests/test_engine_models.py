"""AC M1-6: filter_models reproduces McCartney Phase C (2 fitting models)."""

import csv
from pathlib import Path
from uuid import uuid4

import pytest

from src.engine.envelope import EnvelopeResult
from src.engine.models import filter_models, HomeModelSpec
from src.models.opportunity import DwellingRules

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mccartney"


@pytest.fixture
def basemod_catalog() -> list[HomeModelSpec]:
    """Load 24-model BaseMod catalog from CSV fixture.

    Actual CSV columns (differ from plan's assumed headers):
      model, factory, series, bdr, bth, sqft, box_w, box_d,
      footprint_w_with_garage, footprint_d_with_porch, base_price, status

    box_w / box_d may be blank (e.g. The Jaxon) — HomeModelSpec falls
    back to footprint_w / footprint_d for those entries.
    """
    models = []
    with open(FIXTURE_DIR / "basemod_catalog.csv") as f:
        for row in csv.DictReader(f):
            fw = float(row["footprint_w_with_garage"]) if row["footprint_w_with_garage"] else None
            fd = float(row["footprint_d_with_porch"]) if row["footprint_d_with_porch"] else None
            bw = float(row["box_w"]) if row["box_w"] else fw
            bd = float(row["box_d"]) if row["box_d"] else fd

            # Derive dwelling_type from status text; default to SFR
            status = row.get("status", "")
            if "Duplex" in status or "duplex" in status:
                dtype = "duplex"
            elif "Triplex" in status or "triplex" in status:
                dtype = "triplex"
            else:
                dtype = "SFR"

            models.append(HomeModelSpec(
                model_id=uuid4(),
                name=row["model"],
                box_width_ft=bw,
                box_depth_ft=bd,
                total_width_ft=fw,
                total_depth_ft=fd,
                living_sf=int(row["sqft"]) if row["sqft"] else 0,
                bedrooms=int(row["bdr"]) if row["bdr"] else 0,
                bathrooms=float(row["bth"]) if row["bth"] else 0.0,
                base_price=float(row["base_price"]) if row["base_price"] else 0.0,
                dwelling_type=dtype,
            ))
    return models


def test_filter_models_mccartney_1888(basemod_catalog):
    """AC M1-6.1: McCartney envelope → Jaxon + Arlington fit, rest fail.

    Source: McCartney Phase C. Buildable envelope is 40.5 × 57.1 ft,
    coverage cap 2206 sf. Sec. 1101 rules: min 24 ft plan width, max 3:1 ratio.
    """
    envelope = EnvelopeResult(
        buildable_width_ft=40.5,
        buildable_depth_ft=57.1,
        envelope_area_sf=2311.0,
        coverage_cap_sf=2206.0,
        binding_constraint="coverage",
    )
    sec1101 = DwellingRules()

    results = filter_models(envelope, basemod_catalog, sec1101)

    fitting = [r for r in results if r.fits]
    fitting_names = {r.model_name for r in fitting}

    # McCartney Phase C: exactly Jaxon and Arlington fit
    assert "The Jaxon" in fitting_names
    assert "The Arlington" in fitting_names
    # Belmont / Aspen fail: footprint depth 68 > 57.1 ft envelope depth
    assert "The Belmont" not in fitting_names
    assert "The Aspen" not in fitting_names
    # Hawthorne fails on footprint width (64 > 40.5)
    assert "Hawthorne" not in fitting_names
    # Laurel fails on footprint width (44 > 40.5)
    assert "Laurel" not in fitting_names
    # Tolerance: exactly 2 fitting models (plan acceptance criteria: 2–3)
    assert 2 <= len(fitting) <= 3
