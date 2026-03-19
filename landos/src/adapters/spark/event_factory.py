"""Event factory for Spark MLS listing-family events.

Each build_* function takes current/previous Listing state and returns a
fully-formed EventEnvelope ready for TriggerEngine evaluation.

Identity contract (per Step 4 plan corrections):
  - entity_refs.listing_id  = internal UUID (EntityRefs typed model field)
  - source_record_id        = Spark listing_key string (EventEnvelope optional field)
  - source_system           = "spark_rets" (EventEnvelope required field)
  - payload includes listing_key per event library minimum payload contracts

All emitted events:
  - event_class = RAW
  - event_family = LISTING
  - generation_depth = 0
  - source_system = "spark_rets"

Relist contract (Correction 2):
  When status transitions from expired/withdrawn/canceled → active, callers
  emit BOTH listing_status_changed AND listing_relisted (two separate envelopes).
  Both are built here independently.

gap_days contract (Correction 3):
  gap_days is Optional[int] in the listing_relisted payload.
  Emitted as None when not computable — never as a sentinel zero.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.enums import StandardStatus
from src.models.listing import Listing

_RELIST_TRIGGER_STATUSES: frozenset[StandardStatus] = frozenset({
    StandardStatus.EXPIRED,
    StandardStatus.WITHDRAWN,
    StandardStatus.CANCELED,
})


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _entity_refs(listing: Listing) -> EntityRefs:
    return EntityRefs(listing_id=listing.listing_id)


def build_listing_added(listing: Listing, now: datetime | None = None) -> EventEnvelope:
    """Build a listing_added event for a newly observed listing.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      listing_key, list_price, property_type, acreage, address_raw,
      listing_agent_id, listing_office_id
    """
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="listing_added",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "listing_key": listing.listing_key,
            "list_price": listing.list_price,
            "property_type": listing.property_type,
            "acreage": listing.lot_size_acres,
            "address_raw": listing.address_raw,
            "listing_agent_id": listing.listing_agent_id,
            "listing_office_id": listing.listing_office_id,
        },
    )


def build_listing_status_changed(
    old: Listing,
    new: Listing,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a listing_status_changed event.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      old_status, new_status, close_price, close_date
    Also includes listing_key for source traceability.
    """
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="listing_status_changed",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=new.listing_key,
        entity_refs=_entity_refs(new),
        payload={
            "listing_key": new.listing_key,
            "old_status": old.standard_status.value,
            "new_status": new.standard_status.value,
            "close_price": new.close_price,
            "close_date": new.close_date.isoformat() if new.close_date else None,
        },
    )


def build_listing_expired(
    old: Listing,
    new: Listing,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a listing_expired event (elevated from status_changed where new_status=expired).

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      original_list_price, final_list_price, dom, cdom, cluster_id
    Also includes listing_key for source traceability.
    """
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="listing_expired",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=new.listing_key,
        entity_refs=_entity_refs(new),
        payload={
            "listing_key": new.listing_key,
            "original_list_price": new.original_list_price or old.list_price,
            "final_list_price": new.list_price,
            "dom": new.dom,
            "cdom": new.cdom,
            "cluster_id": None,  # Populated in Step 6 (cluster detection)
        },
    )


def build_listing_price_reduced(
    old: Listing,
    new: Listing,
    reduction_count: int,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a listing_price_reduced event.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      old_price, new_price, percent_change, reduction_count
    Also includes listing_key for source traceability.

    percent_change is negative (price went down).
    """
    if now is None:
        now = _now_utc()

    percent_change = round(
        (new.list_price - old.list_price) / old.list_price * 100, 4
    )

    return EventEnvelope(
        event_type="listing_price_reduced",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=new.listing_key,
        entity_refs=_entity_refs(new),
        payload={
            "listing_key": new.listing_key,
            "old_price": old.list_price,
            "new_price": new.list_price,
            "percent_change": percent_change,
            "reduction_count": reduction_count,
        },
    )


def build_listing_relisted(
    old: Listing,
    new: Listing,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a listing_relisted event.

    Minimum payload per LANDOS_EVENT_LIBRARY.md:
      previous_listing_key, previous_status, gap_days, price_change

    gap_days contract (Correction 3):
      Computed as the number of days between old.expiration_date (or old.list_date
      as fallback) and new.list_date. Emitted as None if not computable.
      Never emitted as 0 when the value is unknown.
    """
    if now is None:
        now = _now_utc()

    gap_days: Optional[int] = _compute_gap_days(old, new)
    price_change: Optional[int] = None
    if new.list_price is not None and old.list_price is not None:
        price_change = new.list_price - old.list_price

    return EventEnvelope(
        event_type="listing_relisted",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=new.listing_key,
        entity_refs=_entity_refs(new),
        payload={
            "listing_key": new.listing_key,
            "previous_listing_key": None,  # Same listing_key; prior key unknown without history
            "previous_status": old.standard_status.value,
            "gap_days": gap_days,
            "price_change": price_change,
        },
    )


# ── BBO signal event builders ─────────────────────────────────────────────

def build_listing_bbo_cdom_threshold_crossed(
    listing: Listing,
    cdom: int,
    threshold: int,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a listing_bbo_cdom_threshold_crossed event (Rule RI)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="listing_bbo_cdom_threshold_crossed",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "listing_key": listing.listing_key,
            "cdom": cdom,
            "threshold": threshold,
            "list_agent_key": listing.list_agent_key,
            "list_office_name": listing.listing_office_name,
            "subdivision_name_raw": listing.subdivision_name_raw,
        },
    )


def build_listing_private_remarks_signal_detected(
    listing: Listing,
    detected_categories: list[str],
    remarks_excerpt: str,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a listing_private_remarks_signal_detected event (Rules RJ/RK)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="listing_private_remarks_signal_detected",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "listing_key": listing.listing_key,
            "detected_categories": detected_categories,
            "remarks_excerpt": remarks_excerpt[:200],  # NEVER full remarks
            "list_agent_key": listing.list_agent_key,
            "list_office_name": listing.listing_office_name,
        },
    )


def build_agent_land_accumulation_detected(
    listing: Listing,
    agent_listing_count: int,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build an agent_land_accumulation_detected event (Rule RL)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="agent_land_accumulation_detected",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "list_agent_key": listing.list_agent_key,
            "listing_agent_name": listing.listing_agent_name,
            "listing_agent_id": listing.listing_agent_id,
            "list_office_name": listing.listing_office_name,
            "agent_listing_count": agent_listing_count,
            "triggering_listing_key": listing.listing_key,
        },
    )


def build_office_land_program_detected(
    listing: Listing,
    office_listing_count: int,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build an office_land_program_detected event (Rule RM)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="office_land_program_detected",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "listing_office_id": listing.listing_office_id,
            "list_office_name": listing.listing_office_name,
            "office_listing_count": office_listing_count,
            "triggering_listing_key": listing.listing_key,
        },
    )


def build_subdivision_remnant_detected(
    listing: Listing,
    reason: str,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a subdivision_remnant_detected event (Rule RT)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="subdivision_remnant_detected",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "listing_key": listing.listing_key,
            "subdivision_name_raw": listing.subdivision_name_raw,
            "legal_description": listing.legal_description,
            "number_of_lots": listing.number_of_lots,
            "cdom": listing.cdom,
            "reason": reason,
        },
    )


def build_developer_exit_signal_detected(
    listing: Listing,
    reason: str,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a developer_exit_signal_detected event (Rules RN/RS)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="developer_exit_signal_detected",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="spark_rets",
        source_record_id=listing.listing_key,
        entity_refs=_entity_refs(listing),
        payload={
            "listing_key": listing.listing_key,
            "list_agent_key": listing.list_agent_key,
            "list_office_name": listing.listing_office_name,
            "cdom": listing.cdom,
            "off_market_date": listing.off_market_date.isoformat() if listing.off_market_date else None,
            "reason": reason,
        },
    )


# ── Private helpers ────────────────────────────────────────────────────────

def _compute_gap_days(old: Listing, new: Listing) -> Optional[int]:
    """Compute days between removal and relist. Returns None if not computable."""
    # Use the new listing's list_date as the relist anchor
    relist_date = new.list_date
    if relist_date is None:
        return None

    # Use old expiration_date first, then old list_date as fallback
    removal_date = old.expiration_date or old.list_date
    if removal_date is None:
        return None

    delta = relist_date - removal_date
    return max(delta.days, 0)  # 0 is valid (same-day relist), only None means unknown
