"""ParcelClusterDetector — Vacant-land parcel clustering with listing cross-reference.

Phase 1 approach:
  1. Filter parcels to VACANT only (skip improved/unknown).
  2. Cluster vacant parcels by normalized owner name.
  3. Cluster vacant parcels by subdivision (legal description keywords).
  4. Cluster vacant parcels by geographic proximity.
  5. For every cluster, cross-reference against Spark listings:
     - Current active listing? Pull BBO signals.
     - Historical/closed listing? Note it as prior market exposure.
  6. Emit cluster events and route through TriggerEngine.

This is the parcel-side companion to the listing-side ClusterDetector.
The listing-side detector groups MLS listings by agent/office/seller.
This detector groups county parcels by owner/subdivision/geography
and then enriches with listing data when available.

Thresholds:
  OWNER_MIN_PARCELS     = 2   → vacant_owner_cluster_detected
  SUBDIVISION_MIN       = 3   → vacant_subdivision_cluster_detected
  PROXIMITY_RADIUS_M    = 200 → geographic cluster (nearby vacant parcels)
  PROXIMITY_MIN         = 3   → vacant_proximity_cluster_detected
"""

from __future__ import annotations

import math
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.adapters.cluster.store import InMemoryClusterStore
from src.adapters.regrid.linker import ParcelListingLinker
from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.enums import ClusterType, VacancyStatus
from src.models.listing import Listing
from src.models.owner import OwnerCluster
from src.models.parcel import Parcel
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.result import RoutingResult
from src.utils.subdivision_canon import canonicalize_subdivision

# ── Thresholds ────────────────────────────────────────────────────────────

OWNER_MIN_PARCELS: int = 2
SUBDIVISION_MIN_PARCELS: int = 3
PROXIMITY_RADIUS_METERS: float = 200.0
PROXIMITY_MIN_PARCELS: int = 3

_CLUSTER_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _deterministic_id(cluster_type: str, group_key: str) -> uuid.UUID:
    return uuid.uuid5(_CLUSTER_NAMESPACE, f"parcel_{cluster_type}:{group_key}")


def _normalize_owner(name: str) -> str:
    """Normalize owner name for dedup: lowercase, collapse whitespace."""
    return " ".join(name.lower().strip().split())


# ── Subdivision extraction ────────────────────────────────────────────────

_SUBDIVISION_PATTERNS = [
    # "LOT 5 SMITH ACRES SUB" → "smith acres"
    re.compile(r"(?:LOT\s+\d+[A-Z]?\s+)(.+?)\s+(?:SUB|SUBDIVISION|SUBD|S/D)", re.IGNORECASE),
    # "SMITH ACRES SUB LOT 5" → "smith acres"
    re.compile(r"^(.+?)\s+(?:SUB|SUBDIVISION|SUBD|S/D)", re.IGNORECASE),
    # "PLAT OF SMITH ACRES" → "smith acres"
    re.compile(r"PLAT\s+OF\s+(.+?)(?:\s+LOT|\s+PART|\s*$)", re.IGNORECASE),
]


def _extract_subdivision(legal_desc: str) -> str | None:
    """Try to extract a subdivision name from a legal description string.

    Uses the shared canonicalization path so that the same legal description
    produces the same canonical key everywhere in the pipeline.
    """
    if not legal_desc:
        return None
    for pattern in _SUBDIVISION_PATTERNS:
        m = pattern.search(legal_desc)
        if m:
            name = m.group(1).strip()
            # Clean up: remove lot/block refs that leaked in
            name = re.sub(r"\s+LOT\s+.*", "", name, flags=re.IGNORECASE).strip()
            name = re.sub(r"\s+BLK\s+.*", "", name, flags=re.IGNORECASE).strip()
            # Run through shared canonicalization (handles variants + false positives)
            return canonicalize_subdivision(name)
    return None


# ── Geographic helpers ────────────────────────────────────────────────────

def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_centroid(parcel: Parcel) -> tuple[float, float] | None:
    if not parcel.centroid:
        return None
    try:
        lon, lat = parcel.centroid["coordinates"]
        return (lat, lon)
    except (KeyError, TypeError, ValueError):
        return None


# ── Result containers ─────────────────────────────────────────────────────

@dataclass
class ParcelClusterResult:
    """One detected parcel cluster with optional listing cross-references."""
    cluster_type: str  # "owner" | "subdivision" | "proximity"
    group_key: str
    parcels: list[Parcel]
    matched_listings: list[Listing] = field(default_factory=list)
    total_acreage: float = 0.0

    @property
    def parcel_count(self) -> int:
        return len(self.parcels)


# ── Event builders (parcel-based cluster events) ──────────────────────────

def _build_vacant_owner_cluster_event(
    cluster: OwnerCluster,
    owner_key: str,
    parcel_count: int,
    total_acreage: float,
    matched_listing_count: int,
    now: datetime,
) -> EventEnvelope:
    return EventEnvelope(
        event_type="vacant_owner_cluster_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="parcel_cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "cluster_id": str(cluster.cluster_id),
            "cluster_type": "same_owner_vacant",
            "owner_key": owner_key,
            "parcel_count": parcel_count,
            "total_acreage": round(total_acreage, 2),
            "matched_listing_count": matched_listing_count,
            "detection_method": "parcel_owner_name_match",
        },
    )


def _build_vacant_subdivision_cluster_event(
    cluster: OwnerCluster,
    subdivision_key: str,
    parcel_count: int,
    unique_owners: int,
    total_acreage: float,
    matched_listing_count: int,
    now: datetime,
) -> EventEnvelope:
    return EventEnvelope(
        event_type="vacant_subdivision_cluster_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="parcel_cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "cluster_id": str(cluster.cluster_id),
            "cluster_type": "same_subdivision_vacant",
            "subdivision_key": subdivision_key,
            "parcel_count": parcel_count,
            "unique_owners": unique_owners,
            "total_acreage": round(total_acreage, 2),
            "matched_listing_count": matched_listing_count,
            "detection_method": "legal_description_subdivision_match",
        },
    )


def _build_vacant_proximity_cluster_event(
    cluster: OwnerCluster,
    centroid_lat: float,
    centroid_lon: float,
    parcel_count: int,
    unique_owners: int,
    total_acreage: float,
    matched_listing_count: int,
    now: datetime,
) -> EventEnvelope:
    return EventEnvelope(
        event_type="vacant_proximity_cluster_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.RAW,
        occurred_at=now,
        observed_at=now,
        source_system="parcel_cluster_detector",
        entity_refs=EntityRefs(cluster_id=cluster.cluster_id),
        payload={
            "cluster_id": str(cluster.cluster_id),
            "cluster_type": "geographic_proximity_vacant",
            "centroid_lat": centroid_lat,
            "centroid_lon": centroid_lon,
            "parcel_count": parcel_count,
            "unique_owners": unique_owners,
            "total_acreage": round(total_acreage, 2),
            "matched_listing_count": matched_listing_count,
            "detection_method": "geographic_proximity",
        },
    )


# ── ParcelClusterDetector ────────────────────────────────────────────────

class ParcelClusterDetector:
    """Detects clusters of vacant parcels and cross-references with listings.

    Usage:
        detector = ParcelClusterDetector(engine, context, cluster_store)
        results, clusters = detector.scan(parcels, listings)
    """

    def __init__(
        self,
        engine: TriggerEngine,
        context: TriggerContext,
        cluster_store: InMemoryClusterStore,
        owner_min_parcels: int = OWNER_MIN_PARCELS,
        subdivision_min_parcels: int = SUBDIVISION_MIN_PARCELS,
        proximity_radius_m: float = PROXIMITY_RADIUS_METERS,
        proximity_min_parcels: int = PROXIMITY_MIN_PARCELS,
    ) -> None:
        self.engine = engine
        self.context = context
        self.store = cluster_store
        self.owner_min = owner_min_parcels
        self.subdivision_min = subdivision_min_parcels
        self.proximity_radius = proximity_radius_m
        self.proximity_min = proximity_min_parcels

    def scan(
        self,
        parcels: list[Parcel],
        listings: list[Listing],
        now: datetime | None = None,
    ) -> tuple[list[RoutingResult], list[ParcelClusterResult]]:
        """Scan vacant parcels for clusters, cross-reference with listings.

        Returns:
            (routing_results, cluster_details) — routing results for engine,
            plus the raw cluster data for reporting.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Step 1: Filter to vacant parcels only
        vacant = [p for p in parcels if p.vacancy_status == VacancyStatus.VACANT]

        # Build linker for cross-referencing parcels → listings
        linker = ParcelListingLinker(listings) if listings else None

        all_results: list[RoutingResult] = []
        all_clusters: list[ParcelClusterResult] = []

        # Step 2: Owner clusters
        r, c = self._detect_owner_clusters(vacant, linker, now)
        all_results.extend(r)
        all_clusters.extend(c)

        # Step 3: Subdivision clusters
        r, c = self._detect_subdivision_clusters(vacant, linker, now)
        all_results.extend(r)
        all_clusters.extend(c)

        # Step 4: Proximity clusters
        r, c = self._detect_proximity_clusters(vacant, linker, now)
        all_results.extend(r)
        all_clusters.extend(c)

        return all_results, all_clusters

    # ── Owner clustering ──────────────────────────────────────────────

    def _detect_owner_clusters(
        self,
        parcels: list[Parcel],
        linker: ParcelListingLinker | None,
        now: datetime,
    ) -> tuple[list[RoutingResult], list[ParcelClusterResult]]:
        groups: dict[str, list[Parcel]] = defaultdict(list)
        for p in parcels:
            if p.owner_name_raw:
                key = _normalize_owner(p.owner_name_raw)
                if key:
                    groups[key].append(p)

        results: list[RoutingResult] = []
        clusters: list[ParcelClusterResult] = []

        for owner_key, group in groups.items():
            if len(group) < self.owner_min:
                continue

            total_acreage = sum(p.acreage for p in group)
            matched = self._cross_reference_listings(group, linker)

            cluster_id = _deterministic_id("owner", owner_key)
            oc = OwnerCluster(
                cluster_id=cluster_id,
                cluster_type=ClusterType.SAME_OWNER,
                detection_method="parcel_owner_name_match",
                member_count=len(group),
                parcel_ids=[p.parcel_id for p in group],
                listing_ids=[l.listing_id for l in matched],
                total_acreage=total_acreage,
            )
            self.store.upsert(oc)

            event = _build_vacant_owner_cluster_event(
                oc, owner_key, len(group), total_acreage, len(matched), now
            )
            results.append(self.engine.evaluate(event, self.context))

            clusters.append(ParcelClusterResult(
                cluster_type="owner",
                group_key=owner_key,
                parcels=group,
                matched_listings=matched,
                total_acreage=total_acreage,
            ))

        return results, clusters

    # ── Subdivision clustering ────────────────────────────────────────

    def _detect_subdivision_clusters(
        self,
        parcels: list[Parcel],
        linker: ParcelListingLinker | None,
        now: datetime,
    ) -> tuple[list[RoutingResult], list[ParcelClusterResult]]:
        groups: dict[str, list[Parcel]] = defaultdict(list)
        for p in parcels:
            sub = _extract_subdivision(p.legal_description_raw or "")
            if sub:
                groups[sub].append(p)

        results: list[RoutingResult] = []
        clusters: list[ParcelClusterResult] = []

        for sub_key, group in groups.items():
            if len(group) < self.subdivision_min:
                continue

            total_acreage = sum(p.acreage for p in group)
            unique_owners = len({_normalize_owner(p.owner_name_raw) for p in group if p.owner_name_raw})
            matched = self._cross_reference_listings(group, linker)

            cluster_id = _deterministic_id("subdivision", sub_key)
            oc = OwnerCluster(
                cluster_id=cluster_id,
                cluster_type=ClusterType.SAME_SUBDIVISION,
                detection_method="legal_description_subdivision_match",
                member_count=len(group),
                parcel_ids=[p.parcel_id for p in group],
                listing_ids=[l.listing_id for l in matched],
                total_acreage=total_acreage,
            )
            self.store.upsert(oc)

            event = _build_vacant_subdivision_cluster_event(
                oc, sub_key, len(group), unique_owners, total_acreage, len(matched), now
            )
            results.append(self.engine.evaluate(event, self.context))

            clusters.append(ParcelClusterResult(
                cluster_type="subdivision",
                group_key=sub_key,
                parcels=group,
                matched_listings=matched,
                total_acreage=total_acreage,
            ))

        return results, clusters

    # ── Proximity clustering ──────────────────────────────────────────

    def _detect_proximity_clusters(
        self,
        parcels: list[Parcel],
        linker: ParcelListingLinker | None,
        now: datetime,
    ) -> tuple[list[RoutingResult], list[ParcelClusterResult]]:
        """Simple greedy proximity clustering of vacant parcels with centroids.

        For each unvisited parcel, find all other unvisited parcels within
        proximity_radius. If the group meets the minimum, emit a cluster.
        """
        # Only parcels with centroids
        geo_parcels = [(p, _get_centroid(p)) for p in parcels]
        geo_parcels = [(p, c) for p, c in geo_parcels if c is not None]

        visited: set[int] = set()
        results: list[RoutingResult] = []
        clusters: list[ParcelClusterResult] = []

        for i, (seed, seed_coord) in enumerate(geo_parcels):
            if i in visited:
                continue

            group_indices = [i]
            for j, (candidate, cand_coord) in enumerate(geo_parcels):
                if j == i or j in visited:
                    continue
                dist = _haversine_meters(seed_coord[0], seed_coord[1], cand_coord[0], cand_coord[1])
                if dist <= self.proximity_radius:
                    group_indices.append(j)

            if len(group_indices) < self.proximity_min:
                continue

            # Mark all as visited
            for idx in group_indices:
                visited.add(idx)

            group = [geo_parcels[idx][0] for idx in group_indices]
            total_acreage = sum(p.acreage for p in group)
            unique_owners = len({_normalize_owner(p.owner_name_raw) for p in group if p.owner_name_raw})
            matched = self._cross_reference_listings(group, linker)

            # Cluster centroid = average of member centroids
            lats = [geo_parcels[idx][1][0] for idx in group_indices]
            lons = [geo_parcels[idx][1][1] for idx in group_indices]
            avg_lat = sum(lats) / len(lats)
            avg_lon = sum(lons) / len(lons)

            geo_key = f"{avg_lat:.5f},{avg_lon:.5f}"
            cluster_id = _deterministic_id("proximity", geo_key)
            oc = OwnerCluster(
                cluster_id=cluster_id,
                cluster_type=ClusterType.GEOGRAPHIC_PROXIMITY,
                detection_method="geographic_proximity",
                member_count=len(group),
                parcel_ids=[p.parcel_id for p in group],
                listing_ids=[l.listing_id for l in matched],
                total_acreage=total_acreage,
                geographic_centroid={"type": "Point", "coordinates": [avg_lon, avg_lat]},
                geographic_radius_miles=round(self.proximity_radius / 1609.34, 3),
            )
            self.store.upsert(oc)

            event = _build_vacant_proximity_cluster_event(
                oc, avg_lat, avg_lon, len(group), unique_owners, total_acreage, len(matched), now
            )
            results.append(self.engine.evaluate(event, self.context))

            clusters.append(ParcelClusterResult(
                cluster_type="proximity",
                group_key=geo_key,
                parcels=group,
                matched_listings=matched,
                total_acreage=total_acreage,
            ))

        return results, clusters

    # ── Listing cross-reference ───────────────────────────────────────

    def _cross_reference_listings(
        self,
        parcels: list[Parcel],
        linker: ParcelListingLinker | None,
    ) -> list[Listing]:
        """For each parcel in the cluster, check if it matches a Spark listing."""
        if linker is None:
            return []
        matched: list[Listing] = []
        seen_ids: set = set()
        for parcel in parcels:
            result = linker.find_match(parcel)
            if result and result.listing.listing_id not in seen_ids:
                matched.append(result.listing)
                seen_ids.add(result.listing.listing_id)
        return matched
