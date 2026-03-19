"""ClusterDetector — Phase 1 owner/agent/office cluster detection.

Detects repeated owner/agent/office patterns across listings,
persists OwnerCluster objects in memory, emits authoritative cluster
events, and activates the pre-wired cluster routing loop.

Detection families in scope (Phase 1):
  SAME_OWNER:  group by listing.owner_id (UUID) if set,
               else normalize(seller_name_raw) if set
  SAME_AGENT:  group by listing.list_agent_key
  SAME_OFFICE: group by listing.listing_office_id

Owner name normalization (Phase 1 — string dedup only, entity resolution deferred):
  _normalize_name(s) = " ".join(s.lower().strip().split())

Thresholds (inclusive):
  OWNER_CLUSTER_MIN       = 2   → same_owner_listing_detected
  OWNER_CLUSTER_EMIT      = 3   → owner_cluster_detected (RC + RO fire)
  CLUSTER_SIZE_THRESHOLD  = 5   → owner_cluster_size_threshold_crossed (RU1/RU2 fire)
  AGENT_THRESHOLD         = 3   → agent_subdivision_program_detected
  OFFICE_THRESHOLD        = 5   → office_inventory_program_detected

Deterministic cluster IDs:
  Cluster IDs are stable across scans for the same logical group.
  Derived via uuid5(NAMESPACE_DNS, "{cluster_type}:{canonical_group_key}").
  Re-running on the same data upserts the same cluster, not duplicates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from src.adapters.cluster.event_factory import (
    build_agent_subdivision_program_detected,
    build_office_inventory_program_detected,
    build_owner_cluster_detected,
    build_owner_cluster_size_threshold_crossed,
    build_same_owner_listing_detected,
)
from src.adapters.cluster.store import InMemoryClusterStore
from src.models.enums import ClusterType
from src.models.listing import Listing
from src.models.owner import OwnerCluster
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.result import RoutingResult

# ── Thresholds ────────────────────────────────────────────────────────────

OWNER_CLUSTER_MIN: int = 2       # same_owner_listing_detected fires
OWNER_CLUSTER_EMIT: int = 3      # owner_cluster_detected fires (RC + RO)
CLUSTER_SIZE_THRESHOLD: int = 5  # owner_cluster_size_threshold_crossed fires (RU1/RU2)
AGENT_THRESHOLD: int = 3         # agent_subdivision_program_detected fires
OFFICE_THRESHOLD: int = 5        # office_inventory_program_detected fires

# ── Deterministic ID namespace ────────────────────────────────────────────

_CLUSTER_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # NAMESPACE_DNS


def _deterministic_cluster_id(cluster_type: ClusterType, group_key: str) -> uuid.UUID:
    """Derive a stable UUID from cluster type and canonical group key.

    Same inputs always produce the same UUID — re-scanning the same logical
    group will upsert the existing cluster rather than create a duplicate.
    """
    composite_key = f"{cluster_type.value}:{group_key}"
    return uuid.uuid5(_CLUSTER_NAMESPACE, composite_key)


# ── Name normalization ────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Phase 1 owner name normalization — whitespace collapse + lowercase."""
    return " ".join(name.lower().strip().split())


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── ClusterDetector ───────────────────────────────────────────────────────

class ClusterDetector:
    """Detects owner/agent/office clusters from a listing pool.

    Usage:
        detector = ClusterDetector(engine, context, cluster_store)
        results = detector.scan_listings(listings, now=datetime.now(UTC))
    """

    def __init__(
        self,
        engine: TriggerEngine,
        context: TriggerContext,
        cluster_store: InMemoryClusterStore,
    ) -> None:
        self.engine = engine
        self.context = context
        self.store = cluster_store

    def scan_listings(
        self,
        listings: list[Listing],
        now: Optional[datetime] = None,
    ) -> list[RoutingResult]:
        """Scan all listings for owner/agent/office clusters.

        Returns all RoutingResults produced by routing cluster events
        through TriggerEngine.
        """
        if now is None:
            now = _now_utc()

        results: list[RoutingResult] = []
        results.extend(self._detect_owner_clusters(listings, now))
        results.extend(self._detect_agent_clusters(listings, now))
        results.extend(self._detect_office_clusters(listings, now))
        return results

    # ── Owner cluster detection ───────────────────────────────────────

    def _detect_owner_clusters(
        self,
        listings: list[Listing],
        now: datetime,
    ) -> list[RoutingResult]:
        """Group listings by owner_id or normalized seller_name_raw.

        Emits:
          - same_owner_listing_detected     (group_size >= OWNER_CLUSTER_MIN = 2)
          - owner_cluster_detected          (group_size >= OWNER_CLUSTER_EMIT = 3)
          - owner_cluster_size_threshold_crossed (group_size >= CLUSTER_SIZE_THRESHOLD = 5)
        """
        # Build groups: prefer owner_id, else normalized seller_name_raw
        owner_id_groups: dict[str, list[Listing]] = {}
        name_groups: dict[str, list[Listing]] = {}

        for listing in listings:
            if listing.owner_id is not None:
                key = str(listing.owner_id)
                owner_id_groups.setdefault(key, []).append(listing)
            elif listing.seller_name_raw is not None and listing.seller_name_raw.strip():
                norm = _normalize_name(listing.seller_name_raw)
                if norm:
                    name_groups.setdefault(norm, []).append(listing)

        results: list[RoutingResult] = []

        for group_key, group in owner_id_groups.items():
            if len(group) >= OWNER_CLUSTER_MIN:
                results.extend(
                    self._process_owner_group(
                        group, group_key, "owner_id_match", now
                    )
                )

        for group_key, group in name_groups.items():
            if len(group) >= OWNER_CLUSTER_MIN:
                results.extend(
                    self._process_owner_group(
                        group, group_key, "name_normalized_match", now
                    )
                )

        return results

    def _process_owner_group(
        self,
        group: list[Listing],
        owner_key: str,
        detection_method: str,
        now: datetime,
    ) -> list[RoutingResult]:
        cluster_id = _deterministic_cluster_id(ClusterType.SAME_OWNER, owner_key)
        cluster = OwnerCluster(
            cluster_id=cluster_id,
            cluster_type=ClusterType.SAME_OWNER,
            detection_method=detection_method,
            member_count=len(group),
            listing_ids=[l.listing_id for l in group],
        )
        self.store.upsert(cluster)

        results: list[RoutingResult] = []
        triggering_listing = group[0]

        # same_owner_listing_detected — always when group_size >= 2
        event = build_same_owner_listing_detected(
            listing=triggering_listing,
            cluster=cluster,
            owner_key=owner_key,
            listing_count=len(group),
            now=now,
        )
        results.append(self.engine.evaluate(event, self.context))

        # owner_cluster_detected — when group_size >= 3
        if len(group) >= OWNER_CLUSTER_EMIT:
            event = build_owner_cluster_detected(
                cluster=cluster, owner_key=owner_key, now=now
            )
            results.append(self.engine.evaluate(event, self.context))

        # owner_cluster_size_threshold_crossed — when group_size >= 5
        if len(group) >= CLUSTER_SIZE_THRESHOLD:
            event = build_owner_cluster_size_threshold_crossed(
                cluster=cluster, threshold=CLUSTER_SIZE_THRESHOLD, now=now
            )
            results.append(self.engine.evaluate(event, self.context))

        return results

    # ── Agent cluster detection ───────────────────────────────────────

    def _detect_agent_clusters(
        self,
        listings: list[Listing],
        now: datetime,
    ) -> list[RoutingResult]:
        """Group listings by list_agent_key.

        Emits agent_subdivision_program_detected when group_size >= AGENT_THRESHOLD = 3.
        """
        groups: dict[str, list[Listing]] = {}
        for listing in listings:
            if listing.list_agent_key is not None and listing.list_agent_key.strip():
                groups.setdefault(listing.list_agent_key, []).append(listing)

        results: list[RoutingResult] = []
        for agent_key, group in groups.items():
            if len(group) >= AGENT_THRESHOLD:
                cluster_id = _deterministic_cluster_id(ClusterType.SAME_AGENT, agent_key)
                cluster = OwnerCluster(
                    cluster_id=cluster_id,
                    cluster_type=ClusterType.SAME_AGENT,
                    detection_method="agent_key_match",
                    member_count=len(group),
                    listing_ids=[l.listing_id for l in group],
                    agent_program_flag=True,
                )
                self.store.upsert(cluster)

                event = build_agent_subdivision_program_detected(
                    cluster=cluster,
                    list_agent_key=agent_key,
                    listing_count=len(group),
                    now=now,
                )
                results.append(self.engine.evaluate(event, self.context))

        return results

    # ── Office cluster detection ──────────────────────────────────────

    def _detect_office_clusters(
        self,
        listings: list[Listing],
        now: datetime,
    ) -> list[RoutingResult]:
        """Group listings by listing_office_id.

        Emits office_inventory_program_detected when group_size >= OFFICE_THRESHOLD = 5.
        """
        groups: dict[str, list[Listing]] = {}
        for listing in listings:
            if listing.listing_office_id is not None and listing.listing_office_id.strip():
                groups.setdefault(listing.listing_office_id, []).append(listing)

        results: list[RoutingResult] = []
        for office_id, group in groups.items():
            if len(group) >= OFFICE_THRESHOLD:
                cluster_id = _deterministic_cluster_id(ClusterType.SAME_OFFICE, office_id)
                cluster = OwnerCluster(
                    cluster_id=cluster_id,
                    cluster_type=ClusterType.SAME_OFFICE,
                    detection_method="office_id_match",
                    member_count=len(group),
                    listing_ids=[l.listing_id for l in group],
                    office_program_flag=True,
                )
                self.store.upsert(cluster)

                event = build_office_inventory_program_detected(
                    cluster=cluster,
                    listing_office_id=office_id,
                    listing_count=len(group),
                    now=now,
                )
                results.append(self.engine.evaluate(event, self.context))

        return results
