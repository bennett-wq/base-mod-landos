"""Opportunity factory for stallout detection — Step 8A.4.

Creates Opportunity objects from stall detections.
Only creates when stall_confidence >= 0.45.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.adapters.stallout.detector import StallAssessment
from src.models.development import Subdivision
from src.models.enums import OpportunityStatus, OpportunityType
from src.models.opportunity import Opportunity

_STALL_CONFIDENCE_THRESHOLD = 0.45
_OPPORTUNITY_SCORE_SCALE = 0.8


def create_stall_opportunity(
    assessment: StallAssessment,
    subdivision: Subdivision,
    source_event_ids: list[UUID],
) -> Optional[Opportunity]:
    """Create an Opportunity from a stall detection.

    Returns None if stall_confidence < 0.45.

    Args:
        assessment: The StallAssessment from detect_stall().
        subdivision: The stalled Subdivision.
        source_event_ids: Event IDs that triggered the detection.

    Returns:
        Opportunity with type STALLED_SUBDIVISION, or None.
    """
    if assessment.stall_confidence < _STALL_CONFIDENCE_THRESHOLD:
        return None

    # Use subdivision's parcel_ids if available, otherwise empty list
    parcel_ids = subdivision.parcel_ids if subdivision.parcel_ids is not None else []

    return Opportunity(
        opportunity_type=OpportunityType.STALLED_SUBDIVISION,
        parcel_ids=parcel_ids,
        municipality_id=subdivision.municipality_id,
        subdivision_id=subdivision.subdivision_id,
        status=OpportunityStatus.DETECTED,
        source_event_ids=source_event_ids,
        opportunity_score=assessment.stall_confidence * _OPPORTUNITY_SCORE_SCALE,
    )
