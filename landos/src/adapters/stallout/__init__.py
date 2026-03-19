"""Stallout detection adapter — Step 8.

Detects stalled subdivisions by comparing historical MunicipalEvent
records against current parcel/subdivision vacancy data.
"""

from src.adapters.stallout.detector import StallAssessment, detect_stall
from src.adapters.stallout.event_factory import build_stallout_events
from src.adapters.stallout.ingestion import scan_subdivisions_for_stalls
from src.adapters.stallout.opportunity_factory import create_stall_opportunity
from src.adapters.stallout.store import (
    InMemoryOpportunityStore,
    InMemorySubdivisionStore,
)

__all__ = [
    "StallAssessment",
    "detect_stall",
    "build_stallout_events",
    "create_stall_opportunity",
    "scan_subdivisions_for_stalls",
    "InMemorySubdivisionStore",
    "InMemoryOpportunityStore",
]
