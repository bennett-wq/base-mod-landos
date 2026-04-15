"""AC M1-8: exit_price() reproduces McCartney Phase D pricing for the Jaxon model."""

import pytest

from src.engine.pricing import exit_price
from src.models.opportunity import CompConfidence, ExitPrice


def test_exit_price_mccartney_jaxon_medium():
    """AC M1-8: anchor_ppsf=183.0, model_sqft=1280, confidence=MEDIUM
    → total=234240.0, ppsf=183.0, sqft=1280.
    Source: McCartney Phase D, Jaxon 1280 sf @ $183/sf median.
    """
    result = exit_price(
        anchor_ppsf=183.0,
        model_sqft=1280,
        confidence=CompConfidence.MEDIUM,
    )
    assert isinstance(result, ExitPrice)
    assert result.ppsf == pytest.approx(183.0)
    assert result.total == pytest.approx(234240.0)
    assert result.sqft == 1280
    assert result.confidence == CompConfidence.MEDIUM
