"""Exit-price engine — M1-8.

Pure multiplication: anchor_ppsf × model_sqft, wrapped in ExitPrice.
See spec §6 pricing.py.
"""

from src.models.opportunity import CompConfidence, ExitPrice


def exit_price(
    anchor_ppsf: float,
    model_sqft: int,
    confidence: CompConfidence,
) -> ExitPrice:
    """Return an ExitPrice from a $/sf anchor and a model's square footage.

    Args:
        anchor_ppsf: Median $/sf from comp set (e.g. 183.0).
        model_sqft: Living area of the selected model plan.
        confidence: Confidence tier from comp_narrator (HIGH/MEDIUM/LOW).

    Returns:
        ExitPrice with ppsf and total both rounded to 2 decimal places.
    """
    total = anchor_ppsf * model_sqft
    return ExitPrice(
        ppsf=round(anchor_ppsf, 2),
        total=round(total, 2),
        confidence=confidence,
        sqft=model_sqft,
    )
