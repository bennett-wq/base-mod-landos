"""Listing history and BBO signal intelligence for stranded-lot detection.

Detects patterns like:
- Owner controls many lots but only 1-3 were listed
- Same subdivision has repeated small-batch listings over time
- Expired/withdrawn/relisted cycles on partial lot inventory
- Private remarks containing package/bulk/motivated/remaining lots language
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.adapters.spark.bbo_signals import REMARKS_PATTERNS
from src.models.listing import Listing


@dataclass
class ListingHistoryEvidence:
    """Structured evidence from listing history analysis."""
    # Counts
    total_historical_listings: int = 0
    active_listings: int = 0
    closed_listings: int = 0
    expired_listings: int = 0
    withdrawn_listings: int = 0
    canceled_listings: int = 0

    # Test-the-water signals
    partial_release_detected: bool = False
    partial_release_ratio: float = 0.0  # listed/total_lots
    repeated_listing_cycles: int = 0  # number of relist cycles detected

    # Failed exit signals
    has_expired_history: bool = False
    has_withdrawn_history: bool = False
    has_relist_cycle: bool = False
    avg_cdom: float = 0.0
    max_cdom: int = 0
    price_reduction_detected: bool = False

    # BBO note evidence
    package_language_detected: bool = False
    fatigue_language_detected: bool = False
    bulk_language_detected: bool = False
    utility_language_detected: bool = False
    distress_language_detected: bool = False
    infrastructure_ready_detected: bool = False
    development_ready_detected: bool = False
    remarks_excerpts: list[str] = field(default_factory=list)  # relevant snippets

    # Computed
    history_signal_score: float = 0.0  # 0.0-1.0 composite


def analyze_cluster_listing_history(
    active_listings: list[Listing],
    historical_listings: list[Listing],
    total_cluster_lots: int,
) -> ListingHistoryEvidence:
    """Analyze listing history for a cluster to detect test-the-water patterns.

    Args:
        active_listings: Currently active listings matched to this cluster
        historical_listings: All historical listings (any status) matched to this cluster
        total_cluster_lots: Total lot count in the cluster (from parcels)
    """
    all_listings = active_listings + historical_listings
    evidence = ListingHistoryEvidence()

    evidence.total_historical_listings = len(historical_listings)
    evidence.active_listings = len(active_listings)

    # Count by status
    for l in all_listings:
        status = l.standard_status.value if l.standard_status else ""
        if status == "closed":
            evidence.closed_listings += 1
        elif status == "expired":
            evidence.expired_listings += 1
        elif status == "withdrawn":
            evidence.withdrawn_listings += 1
        elif status == "canceled":
            evidence.canceled_listings += 1

    # Test-the-water: few listings relative to total lots
    total_listed = len(set(l.listing_key for l in all_listings))
    if total_cluster_lots >= 5 and total_listed > 0:
        evidence.partial_release_ratio = total_listed / total_cluster_lots
        if evidence.partial_release_ratio <= 0.3:
            evidence.partial_release_detected = True

    # Relist cycles: same listing_key appearing with different statuses
    keys_seen: dict[str, set[str]] = {}
    for l in all_listings:
        if l.listing_key not in keys_seen:
            keys_seen[l.listing_key] = set()
        keys_seen[l.listing_key].add(l.standard_status.value if l.standard_status else "")
    evidence.repeated_listing_cycles = sum(1 for statuses in keys_seen.values() if len(statuses) > 1)

    # Failed exit detection
    evidence.has_expired_history = evidence.expired_listings > 0
    evidence.has_withdrawn_history = evidence.withdrawn_listings > 0
    evidence.has_relist_cycle = evidence.repeated_listing_cycles > 0

    # CDOM analysis
    cdom_values = [l.cdom for l in all_listings if l.cdom is not None and l.cdom > 0]
    if cdom_values:
        evidence.avg_cdom = sum(cdom_values) / len(cdom_values)
        evidence.max_cdom = max(cdom_values)

    # Price reduction detection
    for l in all_listings:
        if l.previous_list_price is not None and l.list_price and l.previous_list_price > l.list_price:
            evidence.price_reduction_detected = True
            break

    # Remarks analysis across all listings — scan ALL text fields including public remarks
    for l in all_listings:
        for text_field in [l.remarks_raw, l.private_remarks, l.showing_instructions, getattr(l, 'agent_only_remarks', None)]:
            if not text_field:
                continue
            for category, pattern in REMARKS_PATTERNS.items():
                if re.search(pattern, text_field, re.IGNORECASE):
                    if category == "package_language":
                        evidence.package_language_detected = True
                    elif category == "fatigue_language":
                        evidence.fatigue_language_detected = True
                    elif category == "bulk_language":
                        evidence.bulk_language_detected = True
                    elif category == "utility_language":
                        evidence.utility_language_detected = True
                    elif category == "distress_language":
                        evidence.distress_language_detected = True
                    elif category == "infrastructure_ready":
                        evidence.infrastructure_ready_detected = True
                    elif category == "development_ready":
                        evidence.development_ready_detected = True

            # Extract relevant excerpts (first 100 chars of each field)
            excerpt = text_field.strip()[:100]
            if excerpt and excerpt not in evidence.remarks_excerpts:
                evidence.remarks_excerpts.append(excerpt)

    # Compute composite history signal score (weights sum to >1.0, capped at 1.0)
    score = 0.0
    # Seller-intent signals (strongest)
    if evidence.partial_release_detected:
        score += 0.20  # few listed out of many owned = testing the water
    if evidence.has_expired_history or evidence.has_withdrawn_history:
        score += 0.18  # tried and failed to exit
    if evidence.has_relist_cycle:
        score += 0.15  # persistent failed attempts
    if evidence.distress_language_detected:
        score += 0.15  # as-is, estate sale, foreclosure, etc.
    # Market signals
    if evidence.package_language_detected or evidence.bulk_language_detected:
        score += 0.15  # explicitly offering bulk/package
    if evidence.fatigue_language_detected:
        score += 0.10  # motivated, bring offer, must sell
    if evidence.max_cdom >= 180:
        score += 0.08  # sitting on market for 6+ months
    # Positive readiness signals (boost, not penalize)
    if evidence.infrastructure_ready_detected or evidence.development_ready_detected:
        score += 0.08  # infrastructure/development ready = actionable
    if evidence.price_reduction_detected:
        score += 0.05  # price cut = urgency
    evidence.history_signal_score = min(score, 1.0)

    return evidence
