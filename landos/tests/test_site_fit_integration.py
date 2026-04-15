"""AC M1-4.1 / M1-4.2: existing SiteFit model has the fields the engine needs.

This is a read-only integration test — SiteFit is NOT modified in M1-4.
If this test fails, stop and escalate: the engine cannot populate SiteFit
without matching field names.

Spec reference: §6 (engine intro) — engine populates SiteFit, does NOT
invent parallel types.

IMPORTANT — actual field names differ from the task-template assumptions:
  • SetbackFitResult enum values are CLEAR / TIGHT / VIOLATION / UNKNOWN
    (NOT FITS / DOES_NOT_FIT / UNKNOWN as the spec §6 intro suggested).
  • SiteFit required fields: parcel_id (UUID), home_product_id (UUID),
    fit_result (FitResult), fit_confidence (float 0–1).
  • All six setback fields and setback_fit_result are Optional on the model,
    so they default to None when omitted.

M1-5 (compute_envelope) and M1-6 (filter_models) should use:
    SetbackFitResult.CLEAR, SetbackFitResult.TIGHT,
    SetbackFitResult.VIOLATION, SetbackFitResult.UNKNOWN
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.enums import FitResult, SetbackFitResult
from src.models.product import SiteFit


# ── AC M1-4.1 ────────────────────────────────────────────────────────

def test_site_fit_has_six_setback_fields():
    """SiteFit must have front/side/rear × required/available + fit result.

    These field names are the engine contract for M1-5 and M1-6. If any
    name is wrong, Pydantic raises ValidationError here — that's the
    signal to escalate before implementing M1-5.

    Note: all six setback fields are Optional on SiteFit. This test
    explicitly sets them to confirm the names are accepted.
    """
    sf = SiteFit(
        parcel_id=uuid4(),
        home_product_id=uuid4(),
        fit_result=FitResult.FITS,
        fit_confidence=0.85,
        front_setback_required_feet=20.0,
        side_setback_required_feet=16.0,
        rear_setback_required_feet=35.0,
        front_setback_available_feet=40.0,
        side_setback_available_feet=28.0,
        rear_setback_available_feet=70.0,
        setback_fit_result=SetbackFitResult.UNKNOWN,
    )

    assert sf.front_setback_required_feet == 20.0
    assert sf.side_setback_required_feet == 16.0
    assert sf.rear_setback_required_feet == 35.0
    assert sf.front_setback_available_feet == 40.0
    assert sf.side_setback_available_feet == 28.0
    assert sf.rear_setback_available_feet == 70.0
    assert sf.setback_fit_result == SetbackFitResult.UNKNOWN


# ── AC M1-4.2 ────────────────────────────────────────────────────────

def test_setback_fit_result_enum_has_four_states():
    """SetbackFitResult has CLEAR, TIGHT, VIOLATION, UNKNOWN.

    The task template anticipated FITS / DOES_NOT_FIT / UNKNOWN (three
    states). The actual enum uses four states matching a clearance-band
    model rather than a binary pass/fail. M1-5 and M1-6 must use these
    names.
    """
    assert SetbackFitResult.CLEAR.value == "clear"
    assert SetbackFitResult.TIGHT.value == "tight"
    assert SetbackFitResult.VIOLATION.value == "violation"
    assert SetbackFitResult.UNKNOWN.value == "unknown"
