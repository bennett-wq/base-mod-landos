"""Event factory for Regrid parcel-state events.

Each build_* function takes Parcel state (and linked Listing or Owner where
relevant) and returns a fully-formed EventEnvelope ready for TriggerEngine
evaluation.

Identity contract:
  - entity_refs.parcel_id  = internal UUID (Parcel.parcel_id)
  - entity_refs.listing_id = internal UUID of linked Listing (where applicable)
  - source_system          = "regrid_bulk"
  - event_class            = RAW  (authoritative source — ingestion adapter is the origin)
  - generation_depth       = 0

Note on event_class:
  The event library classifies parcel_linked_to_listing, parcel_owner_resolved,
  and parcel_score_updated as "derived" in their logical description (inferred
  signals, not raw API pushes). However, when emitted directly from the ingestion
  adapter — the authoritative Regrid source — the correct class is RAW, matching
  the Step 4 Spark adapter convention. DERIVED class applies when a downstream
  agent re-emits these events after further processing.

Events emitted here:
  parcel_linked_to_listing — parcel matched to a Listing object
  parcel_owner_resolved    — parcel owner identified from county records
  parcel_score_updated     — parcel opportunity score computed or changed
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.parcel import Parcel


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parcel_entity_refs(parcel: Parcel, listing_id: UUID | None = None) -> EntityRefs:
    return EntityRefs(parcel_id=parcel.parcel_id, listing_id=listing_id)


def build_parcel_linked_to_listing(
    parcel: Parcel,
    listing_id: UUID,
    linkage_method: str,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a parcel_linked_to_listing event.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      parcel_id, listing_id, linkage_method

    linkage_method values: address_match | parcel_number_match | geo_match | manual
    """
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="parcel_linked_to_listing",
        event_family=EventFamily.PARCEL_STATE,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="regrid_bulk",
        source_record_id=parcel.source_system_ids.get("regrid_id"),
        entity_refs=_parcel_entity_refs(parcel, listing_id=listing_id),
        payload={
            "parcel_id": str(parcel.parcel_id),
            "listing_id": str(listing_id),
            "linkage_method": linkage_method,
        },
    )


def build_parcel_owner_resolved(
    parcel: Parcel,
    owner_id: UUID,
    resolution_method: str = "county_records",
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a parcel_owner_resolved event.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      parcel_id, owner_id, resolution_method

    resolution_method values: county_records | mls_seller | entity_resolution | manual
    Phase 1 always uses county_records.
    """
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="parcel_owner_resolved",
        event_family=EventFamily.PARCEL_STATE,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="regrid_bulk",
        source_record_id=parcel.source_system_ids.get("regrid_id"),
        entity_refs=_parcel_entity_refs(parcel),
        payload={
            "parcel_id": str(parcel.parcel_id),
            "owner_id": str(owner_id),
            "resolution_method": resolution_method,
        },
    )


def build_parcel_score_updated(
    parcel: Parcel,
    old_score: float | None,
    new_score: float,
    trigger_reason: str,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a parcel_score_updated event.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      parcel_id, old_score, new_score, score_delta, trigger_reason

    Callers are responsible for the materiality gate (abs(score_delta) >= 0.05).
    This factory emits the event unconditionally when called.
    """
    if now is None:
        now = _now_utc()

    score_delta = round(new_score - (old_score or 0.0), 6)

    return EventEnvelope(
        event_type="parcel_score_updated",
        event_family=EventFamily.PARCEL_STATE,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="regrid_bulk",
        source_record_id=parcel.source_system_ids.get("regrid_id"),
        entity_refs=_parcel_entity_refs(parcel),
        payload={
            "parcel_id": str(parcel.parcel_id),
            "old_score": old_score,
            "new_score": new_score,
            "score_delta": score_delta,
            "trigger_reason": trigger_reason,
        },
    )
