"""StrategicOpportunityRanker — the product feature.

Cross-references stallout detector results with cluster detector results
to surface the highest-value stranded lot opportunities: subdivisions and
clusters with 5+ vacant lots, infrastructure invested, and acquisition signals.

This IS the query that makes BaseMod different.

Composite score formula (v0.4):
  - lot_count_score   (0.14): 5+ lots = 0.5, 10+ = 0.75, 20+ = 1.0
  - stall_confidence  (0.14): direct from stallout detector (0.0-1.0)
  - seller_intent     (0.16): distress + fatigue + relist cycles + partial release
  - infrastructure    (0.12): roads/sewer/water invested OR confirmed in remarks
  - vacancy_ratio     (0.10): from subdivision or cluster parcels
  - bbo_signals       (0.08): any BBO behavioral signals on cluster listings
  - municipal_posture (0.04): PERMISSIVE = 1.0, MODERATE = 0.5, else 0.0
  - listing_activity  (0.08): has active listings = 1.0, else 0.0
  - history_signals   (0.08): listing history composite (test-the-water, failed exits)
  - broker_notes      (0.06): package/bulk language + high CDOM from remarks
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from src.adapters.spark.bbo_signals import (
    BROKER_NOTE_PATTERNS,
    REMARKS_PATTERNS,
    detect_broker_note_signals,
    extract_infrastructure_profile,
)
from src.models.enums import VacancyStatus
from src.scoring.listing_history_signals import ListingHistoryEvidence

# Deterministic namespace for opportunity IDs — stable across reruns
_OPP_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


# ── Weights ──────────────────────────────────────────────────────────────────

WEIGHTS = {
    "lot_count": 0.14,
    "stall_confidence": 0.14,
    "seller_intent": 0.16,
    "infrastructure": 0.12,
    "vacancy_ratio": 0.10,
    "bbo_signals": 0.08,
    "municipal_posture": 0.04,
    "listing_activity": 0.08,
    "history_signals": 0.08,
    "broker_notes": 0.06,
}


@dataclass
class StrategicOpportunity:
    """A ranked, cross-referenced stranded lot opportunity."""
    opportunity_id: str
    name: str
    opportunity_type: str  # "stalled_subdivision", "owner_cluster", "subdivision_cluster"
    municipality_id: Optional[str] = None

    # Core metrics
    lot_count: int = 0
    total_acreage: float = 0.0
    infrastructure_invested: bool = False
    stall_confidence: float = 0.0
    vacancy_ratio: float = 0.0

    # Signal presence
    has_active_listings: bool = False
    listing_count: int = 0
    bbo_signal_count: int = 0
    municipal_posture: str = "UNKNOWN"

    # Identification
    owner_name: str = ""
    subdivision_name: str = ""
    cluster_id: Optional[str] = None
    subdivision_id: Optional[str] = None

    # Listings detail
    listing_keys: list[str] = field(default_factory=list)
    listing_agents: list[str] = field(default_factory=list)

    # Parcel IDs for drill-down
    parcel_ids: list[str] = field(default_factory=list)

    # Centroid for map
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None

    # Stall evidence — what signals fired and why
    stall_signals: list[str] = field(default_factory=list)

    # Historical listing evidence
    historical_listing_count: int = 0
    expired_listing_count: int = 0
    withdrawn_listing_count: int = 0
    has_relist_cycle: bool = False
    partial_release_detected: bool = False
    max_cdom: int = 0
    avg_cdom: float = 0.0

    # BBO note evidence
    package_language_detected: bool = False
    fatigue_language_detected: bool = False
    distress_language_detected: bool = False
    infrastructure_ready_detected: bool = False
    development_ready_detected: bool = False
    remarks_excerpts: list[str] = field(default_factory=list)

    # Structured infrastructure profile (from BBO utility/sewer/water/road fields)
    structured_infra_score: float = 0.0  # 0.0-1.0 from actual utility/sewer/water data
    infra_flags: list[str] = field(default_factory=list)
    has_public_sewer: bool = False
    has_public_water: bool = False
    has_natural_gas: bool = False
    has_paved_road: bool = False
    is_buildable: bool = False
    is_site_condo: bool = False
    has_wetland: bool = False

    # Broker-note intelligence (private remarks signals)
    broker_signals: list[str] = field(default_factory=list)
    splits_available: bool = False
    all_offers_considered: bool = False
    seller_is_agent: bool = False
    site_tested: bool = False
    has_documents: bool = False
    document_count: int = 0

    # Legal description multi-lot evidence
    legal_lot_numbers: list[int] = field(default_factory=list)
    same_sub_listing_count: int = 0

    # Composite history score
    history_signal_score: float = 0.0

    # Computed
    composite_score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)


def _lot_count_score(lot_count: int) -> float:
    if lot_count >= 20:
        return 1.0
    if lot_count >= 10:
        return 0.75
    if lot_count >= 5:
        return 0.5
    if lot_count >= 3:
        return 0.25
    return 0.1


def _municipal_posture_score(posture: str) -> float:
    posture_upper = posture.upper() if posture else ""
    if posture_upper == "PERMISSIVE":
        return 1.0
    if posture_upper == "MODERATE":
        return 0.5
    return 0.0


def score_opportunity(opp: StrategicOpportunity) -> StrategicOpportunity:
    """Compute composite score for a strategic opportunity (v0.4).

    Key change from v0.3: adds explicit seller_intent dimension that
    combines distress language, failed exits, partial release, and relist
    cycles into a single strong signal.
    """
    # Seller intent: the core question — is the owner trying to get out?
    intent_score = 0.0
    if opp.distress_language_detected:
        intent_score += 0.30  # as-is, estate sale, foreclosure
    if opp.fatigue_language_detected:
        intent_score += 0.15  # motivated, bring offer, must sell
    if opp.all_offers_considered:
        intent_score += 0.15  # "all offers considered" = ready to deal
    if opp.has_relist_cycle:
        intent_score += 0.15  # tried, failed, trying again
    if opp.partial_release_detected:
        intent_score += 0.12  # testing the water with few lots
    if opp.splits_available:
        intent_score += 0.10  # actively offering splits = exit strategy
    if opp.expired_listing_count > 0 or opp.withdrawn_listing_count > 0:
        intent_score += 0.08  # any failed exit attempt
    intent_score = min(intent_score, 1.0)

    # Infrastructure: from platted subdivision, structured BBO fields, OR remarks
    infra_score = 0.0
    if opp.infrastructure_invested:
        infra_score = 1.0
    elif opp.structured_infra_score > 0:
        infra_score = max(opp.structured_infra_score, 0.5)  # structured data is reliable
    elif opp.infrastructure_ready_detected or opp.development_ready_detected:
        infra_score = 0.4  # mentioned in remarks only

    breakdown = {
        "lot_count": _lot_count_score(opp.lot_count),
        "stall_confidence": min(opp.stall_confidence, 1.0),
        "seller_intent": intent_score,
        "infrastructure": infra_score,
        "vacancy_ratio": min(opp.vacancy_ratio, 1.0),
        "bbo_signals": min(opp.bbo_signal_count / 3.0, 1.0) if opp.bbo_signal_count > 0 else 0.0,
        "municipal_posture": _municipal_posture_score(opp.municipal_posture),
        "listing_activity": 1.0 if opp.has_active_listings else 0.0,
        "history_signals": min(opp.history_signal_score, 1.0),
        "broker_notes": (
            (1.0 if opp.package_language_detected else 0.0) * 0.25
            + (1.0 if opp.site_tested else 0.0) * 0.25
            + (1.0 if opp.has_documents else 0.0) * 0.15
            + (1.0 if opp.seller_is_agent else 0.0) * 0.15
            + (min(opp.max_cdom / 365.0, 1.0)) * 0.20
        ),
    }

    composite = sum(WEIGHTS[k] * breakdown[k] for k in WEIGHTS)
    opp.composite_score = round(composite, 4)
    opp.score_breakdown = {k: round(v, 4) for k, v in breakdown.items()}
    return opp


def rank_from_pipeline(
    parcel_clusters: list,  # ParcelClusterResult objects
    stall_assessments: dict,  # subdivision_id (str) -> StallAssessment
    subdivisions: dict,  # subdivision_id (str) -> Subdivision
    stall_by_group_key: dict | None = None,  # group_key -> StallAssessment
    subdivisions_by_group_key: dict | None = None,  # group_key -> Subdivision
    min_lots: int = 1,
    listing_history_evidence: dict | None = None,  # group_key -> ListingHistoryEvidence
) -> list[StrategicOpportunity]:
    """Build and rank strategic opportunities from pipeline output.

    Args:
        parcel_clusters: list of ParcelClusterResult from ParcelClusterDetector.scan()
        stall_assessments: dict mapping subdivision_id -> StallAssessment
        subdivisions: dict mapping subdivision_id -> Subdivision
        stall_by_group_key: dict mapping cluster group_key -> StallAssessment
            (for subdivision clusters materialized from parcel legal descriptions)
        subdivisions_by_group_key: dict mapping group_key -> Subdivision
        min_lots: minimum lot count filter (default 1, use 5 for the primary query)
        listing_history_evidence: dict mapping cluster group_key -> ListingHistoryEvidence
            (optional, enriches opportunities with historical listing signals)

    Returns:
        list of StrategicOpportunity, sorted by composite_score descending
    """
    _stall_by_gk = stall_by_group_key or {}
    _subs_by_gk = subdivisions_by_group_key or {}
    _hist_ev_by_gk = listing_history_evidence or {}
    opportunities: list[StrategicOpportunity] = []

    for cluster in parcel_clusters:
        if cluster.parcel_count < min_lots:
            continue

        # Determine if this cluster maps to a stalled subdivision
        # First try parcel.subdivision_id matching (when parcels have IDs set)
        sub_ids = {
            str(p.subdivision_id)
            for p in cluster.parcels
            if p.subdivision_id is not None
        }

        best_stall = None
        best_sub = None
        for sid in sub_ids:
            if sid in stall_assessments:
                assess = stall_assessments[sid]
                if best_stall is None or assess.stall_confidence > best_stall.stall_confidence:
                    best_stall = assess
                    best_sub = subdivisions.get(sid)

        # Fall back to group_key matching (for subdivision clusters from legal descriptions)
        if best_stall is None and cluster.group_key in _stall_by_gk:
            best_stall = _stall_by_gk[cluster.group_key]
            best_sub = _subs_by_gk.get(cluster.group_key)

        # Look up listing history evidence for this cluster
        hist_ev = _hist_ev_by_gk.get(cluster.group_key)

        # BBO signals from matched listings — more granular
        bbo_count = 0
        listing_keys = []
        listing_agents = []
        remarks_excerpts = []
        package_lang = False
        fatigue_lang = False
        distress_lang = False
        infra_ready = False
        dev_ready = False
        # Structured infrastructure + broker note signals
        best_infra_profile: dict = {}
        best_infra_score = 0.0
        all_broker_signals: set[str] = set()
        splits_avail = False
        all_offers = False

        seller_agent = False
        site_tested = False
        has_docs = False
        total_docs = 0
        from src.adapters.spark.bbo_signals import extract_legal_lot_info

        for l in cluster.matched_listings:
            listing_keys.append(l.listing_key)
            if l.listing_agent_name:
                listing_agents.append(l.listing_agent_name)
            if l.cdom and l.cdom >= 90:
                bbo_count += 1

            # Document count
            doc_count = getattr(l, 'documents_count', None) or 0
            if doc_count > 0:
                has_docs = True
                total_docs += doc_count

            # Extract structured infrastructure profile from BBO fields
            profile = extract_infrastructure_profile(l)
            if profile['infra_score'] > best_infra_score:
                best_infra_score = profile['infra_score']
                best_infra_profile = profile

            # Extract broker note signals from private/agent remarks
            broker_sigs = detect_broker_note_signals(l)
            all_broker_signals.update(broker_sigs)
            if 'splits_available' in broker_sigs:
                splits_avail = True
            if 'all_offers' in broker_sigs:
                all_offers = True
            if 'seller_is_agent' in broker_sigs:
                seller_agent = True
            if 'site_tested' in broker_sigs:
                site_tested = True

            # Scan ALL text fields: public remarks, private remarks, showing, agent-only
            for text in [l.remarks_raw, l.private_remarks, l.showing_instructions, getattr(l, 'agent_only_remarks', None)]:
                if not text:
                    continue
                bbo_count += 1
                for cat, pat in REMARKS_PATTERNS.items():
                    if re.search(pat, text, re.IGNORECASE):
                        if cat == "package_language":
                            package_lang = True
                        elif cat == "fatigue_language":
                            fatigue_lang = True
                        elif cat == "distress_language":
                            distress_lang = True
                        elif cat == "infrastructure_ready":
                            infra_ready = True
                        elif cat == "development_ready":
                            dev_ready = True
                excerpt = text.strip()[:100]
                if excerpt and excerpt not in remarks_excerpts:
                    remarks_excerpts.append(excerpt)

        # Centroid from first parcel with coordinates
        centroid_lat = None
        centroid_lon = None
        for p in cluster.parcels:
            if p.centroid and "coordinates" in p.centroid:
                coords = p.centroid["coordinates"]
                if len(coords) >= 2:
                    centroid_lon, centroid_lat = coords[0], coords[1]
                    break

        # Build the opportunity
        opp_type = "stalled_subdivision" if best_stall and best_stall.is_stalled else (
            "subdivision_cluster" if cluster.cluster_type == "subdivision" else "owner_cluster"
        )

        # Deterministic ID: same cluster type + group_key always produces same opportunity_id
        det_id = str(uuid.uuid5(_OPP_NAMESPACE, f"{cluster.cluster_type}:{cluster.group_key}"))

        opp = StrategicOpportunity(
            opportunity_id=det_id,
            name=best_sub.name if best_sub else cluster.group_key,
            opportunity_type=opp_type,
            lot_count=cluster.parcel_count,
            total_acreage=cluster.total_acreage,
            infrastructure_invested=best_stall.infrastructure_invested if best_stall else False,
            stall_confidence=best_stall.stall_confidence if best_stall else 0.0,
            vacancy_ratio=best_stall.vacancy_ratio if best_stall else (
                sum(1 for p in cluster.parcels if p.vacancy_status == VacancyStatus.VACANT) / max(cluster.parcel_count, 1)
            ),
            has_active_listings=len(cluster.matched_listings) > 0,
            listing_count=len(cluster.matched_listings),
            bbo_signal_count=bbo_count,
            owner_name=cluster.group_key if cluster.cluster_type == "owner" else "",
            subdivision_name=best_sub.name if best_sub else (
                cluster.group_key if cluster.cluster_type == "subdivision" else ""
            ),
            cluster_id=None,  # Will be set by pipeline if cluster stored
            subdivision_id=str(best_sub.subdivision_id) if best_sub else None,
            listing_keys=listing_keys,
            listing_agents=listing_agents,
            parcel_ids=[str(p.parcel_id) for p in cluster.parcels],
            centroid_lat=centroid_lat,
            centroid_lon=centroid_lon,
            stall_signals=best_stall.stall_signals if best_stall else [],
            package_language_detected=package_lang or (hist_ev.package_language_detected if hist_ev else False),
            fatigue_language_detected=fatigue_lang or (hist_ev.fatigue_language_detected if hist_ev else False),
            distress_language_detected=distress_lang or (hist_ev.distress_language_detected if hist_ev else False),
            infrastructure_ready_detected=infra_ready or (hist_ev.infrastructure_ready_detected if hist_ev else False),
            development_ready_detected=dev_ready or (hist_ev.development_ready_detected if hist_ev else False),
            remarks_excerpts=remarks_excerpts[:5],
            # Structured infrastructure from BBO fields
            structured_infra_score=best_infra_score,
            infra_flags=best_infra_profile.get('infra_flags', []),
            has_public_sewer=best_infra_profile.get('public_sewer', False),
            has_public_water=best_infra_profile.get('public_water', False),
            has_natural_gas=best_infra_profile.get('natural_gas', False),
            has_paved_road=best_infra_profile.get('paved_road', False),
            is_buildable=best_infra_profile.get('buildable', False),
            is_site_condo=best_infra_profile.get('site_condo', False),
            has_wetland=best_infra_profile.get('wetland', False),
            # Broker note intelligence
            broker_signals=sorted(all_broker_signals),
            splits_available=splits_avail,
            all_offers_considered=all_offers,
            seller_is_agent=seller_agent,
            site_tested=site_tested,
            has_documents=has_docs,
            document_count=total_docs,
            historical_listing_count=hist_ev.total_historical_listings if hist_ev else 0,
            expired_listing_count=hist_ev.expired_listings if hist_ev else 0,
            withdrawn_listing_count=hist_ev.withdrawn_listings if hist_ev else 0,
            has_relist_cycle=hist_ev.has_relist_cycle if hist_ev else False,
            partial_release_detected=hist_ev.partial_release_detected if hist_ev else False,
            max_cdom=hist_ev.max_cdom if hist_ev else (max((l.cdom or 0) for l in cluster.matched_listings) if cluster.matched_listings else 0),
            avg_cdom=hist_ev.avg_cdom if hist_ev else 0.0,
            history_signal_score=hist_ev.history_signal_score if hist_ev else 0.0,
        )

        score_opportunity(opp)
        opportunities.append(opp)

    # Sort by composite score descending
    opportunities.sort(key=lambda o: -o.composite_score)
    return opportunities
