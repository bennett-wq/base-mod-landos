"""Event factory for cluster-family events (Step 6).

All events:
  - event_class = RAW
  - event_family = CLUSTER_OWNER
  - source_system = "cluster_detector"

Payload key contracts are driven by existing rule cooldown_key_builders:
  same_owner_listing_detected: owner_key required (RP uses owner_key)
  owner_cluster_detected:      cluster_id, cluster_size, owner_key required
                                (RO uses owner_key|cluster_id; RC checks cluster_size)
  owner_cluster_size_threshold_crossed: cluster_id, cluster_size, threshold
  agent_subdivision_program_detected:   list_agent_key, listing_count, cluster_id
  office_inventory_program_detected:    listing_office_id, listing_count, cluster_id
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.listing import Listing
from src.models.owner import OwnerCluster


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_same_owner_listing_detected(
    listing: Listing,
    cluster: OwnerCluster,
    owner_key: str,
    listing_count: int,
    now: Optional[datetime] = None,
) -> EventEnvelope:
    """Build a same_owner_listing_detected event (Rule RP)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="same_owner_listing_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="cluster_detector",
        source_record_id=listing.listing_key,
        entity_refs=EntityRefs(
            listing_id=listing.listing_id,
            cluster_id=cluster.cluster_id,
        ),
        payload={
            "owner_key": owner_key,
            "listing_count": listing_count,
            "cluster_id": str(cluster.cluster_id),
            "triggering_listing_key": listing.listing_key,
        },
    )


def build_owner_cluster_detected(
    cluster: OwnerCluster,
    owner_key: str,
    now: Optional[datetime] = None,
) -> EventEnvelope:
    """Build an owner_cluster_detected event (Rules RC, RO)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="owner_cluster_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "cluster_id": str(cluster.cluster_id),
            "cluster_type": cluster.cluster_type.value,
            "cluster_size": cluster.member_count,
            "owner_key": owner_key,
            "detection_method": cluster.detection_method,
        },
    )


def build_owner_cluster_size_threshold_crossed(
    cluster: OwnerCluster,
    threshold: int,
    now: Optional[datetime] = None,
) -> EventEnvelope:
    """Build an owner_cluster_size_threshold_crossed event (Rules RU1, RU2)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="owner_cluster_size_threshold_crossed",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "cluster_id": str(cluster.cluster_id),
            "cluster_type": cluster.cluster_type.value,
            "cluster_size": cluster.member_count,
            "threshold": threshold,
            "detection_method": cluster.detection_method,
        },
    )


def build_agent_subdivision_program_detected(
    cluster: OwnerCluster,
    list_agent_key: str,
    listing_count: int,
    now: Optional[datetime] = None,
) -> EventEnvelope:
    """Build an agent_subdivision_program_detected event (Step 6 cluster detection)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="agent_subdivision_program_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "list_agent_key": list_agent_key,
            "listing_count": listing_count,
            "cluster_id": str(cluster.cluster_id),
            "detection_method": cluster.detection_method,
        },
    )


def build_office_inventory_program_detected(
    cluster: OwnerCluster,
    listing_office_id: str,
    listing_count: int,
    now: Optional[datetime] = None,
) -> EventEnvelope:
    """Build an office_inventory_program_detected event (Step 6 cluster detection)."""
    if now is None:
        now = _now_utc()

    return EventEnvelope(
        event_type="office_inventory_program_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "listing_office_id": listing_office_id,
            "listing_count": listing_count,
            "cluster_id": str(cluster.cluster_id),
            "detection_method": cluster.detection_method,
        },
    )
