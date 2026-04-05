"""Owner-linked seller-intent evidence for vacant parcel clusters."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import re

from src.models.enums import StandardStatus
from src.models.listing import Listing
from src.utils.party_name_match import PartyMatch, match_party_names


@dataclass
class OwnerLinkEvidence:
    owner_linked_active_count: int = 0
    owner_linked_historical_count: int = 0
    owner_linked_failed_exit_count: int = 0
    owner_linked_expired_count: int = 0
    owner_linked_withdrawn_count: int = 0
    owner_linked_canceled_count: int = 0
    owner_linked_listing_keys: list[str] = field(default_factory=list)
    owner_linked_agents: list[str] = field(default_factory=list)
    owner_linked_offices: list[str] = field(default_factory=list)
    repeat_agent_on_owner_inventory: bool = False
    partial_release_test_water: bool = False
    owner_link_match_methods: list[str] = field(default_factory=list)
    owner_link_confidence: float = 0.0
    historical_notes_present: bool = False
    historical_documents_present: bool = False
    historical_notes_count: int = 0
    historical_document_count: int = 0


def _normalize_parcel_number(raw: str | None) -> str:
    if not raw:
        return ""
    value = re.sub(r"[-\s]", "", raw.strip())
    value = value.lstrip("0") or "0"
    return value.lower()


def analyze_owner_cluster_evidence(
    owner_names: list[str],
    listings: list[Listing],
    total_cluster_lots: int,
    parcel_numbers: list[str] | None = None,
) -> OwnerLinkEvidence:
    """Link MLS seller history to a same-owner vacant parcel cluster."""
    evidence = OwnerLinkEvidence()
    if not owner_names:
        return evidence

    owner_names = [name for name in owner_names if name and name.strip()]
    if not owner_names:
        return evidence

    normalized_parcels = {
        _normalize_parcel_number(parcel_number)
        for parcel_number in (parcel_numbers or [])
        if _normalize_parcel_number(parcel_number)
    }

    matched_by_key: dict[str, dict] = {}

    for listing in listings:
        best_match = None

        listing_parcel = _normalize_parcel_number(getattr(listing, "parcel_number_raw", None))
        if listing_parcel and listing_parcel in normalized_parcels:
            best_match = PartyMatch(True, "parcel_exact", 1.0)
        else:
            listing_party_name = getattr(listing, "owner_name_raw", None) or listing.seller_name_raw
            if not listing_party_name:
                continue

            for owner_name in owner_names:
                match = match_party_names(owner_name, listing_party_name)
                if match.matched and (best_match is None or match.confidence > best_match.confidence):
                    best_match = match

        if best_match is None:
            continue

        bucket = matched_by_key.setdefault(
            listing.listing_key,
            {
                "statuses": set(),
                "agents": set(),
                "offices": set(),
                "methods": set(),
                "confidence": 0.0,
                "notes_present": False,
                "documents_present": False,
            },
        )
        if listing.standard_status:
            bucket["statuses"].add(listing.standard_status)
        if listing.listing_agent_name:
            bucket["agents"].add(listing.listing_agent_name)
        if listing.listing_office_name:
            bucket["offices"].add(listing.listing_office_name)
        bucket["methods"].add(best_match.method)
        bucket["confidence"] = max(bucket["confidence"], best_match.confidence)
        bucket["notes_present"] = bucket["notes_present"] or any(
            bool(text)
            for text in [
                listing.remarks_raw,
                listing.private_remarks,
                listing.showing_instructions,
                getattr(listing, "agent_only_remarks", None),
            ]
        )
        bucket["documents_present"] = bucket["documents_present"] or bool(getattr(listing, "documents_count", 0))

    if not matched_by_key:
        return evidence

    agent_counter: Counter[str] = Counter()
    office_counter: Counter[str] = Counter()

    for listing_key, bucket in matched_by_key.items():
        statuses = bucket["statuses"]
        evidence.owner_linked_listing_keys.append(listing_key)
        evidence.owner_link_confidence = max(evidence.owner_link_confidence, bucket["confidence"])
        evidence.owner_link_match_methods.extend(sorted(bucket["methods"]))
        evidence.historical_notes_present = evidence.historical_notes_present or bucket["notes_present"]
        evidence.historical_documents_present = evidence.historical_documents_present or bucket["documents_present"]
        if bucket["notes_present"]:
            evidence.historical_notes_count += 1
        if bucket["documents_present"]:
            evidence.historical_document_count += 1

        if StandardStatus.ACTIVE in statuses:
            evidence.owner_linked_active_count += 1
        if any(status != StandardStatus.ACTIVE for status in statuses):
            evidence.owner_linked_historical_count += 1
        if StandardStatus.EXPIRED in statuses:
            evidence.owner_linked_expired_count += 1
        if StandardStatus.WITHDRAWN in statuses:
            evidence.owner_linked_withdrawn_count += 1
        if StandardStatus.CANCELED in statuses:
            evidence.owner_linked_canceled_count += 1

        failed_exit = any(
            status in {StandardStatus.EXPIRED, StandardStatus.WITHDRAWN, StandardStatus.CANCELED}
            for status in statuses
        )
        if failed_exit:
            evidence.owner_linked_failed_exit_count += 1

        for agent in bucket["agents"]:
            agent_counter[agent] += 1
        for office in bucket["offices"]:
            office_counter[office] += 1

    evidence.owner_link_match_methods = sorted(set(evidence.owner_link_match_methods))
    evidence.owner_linked_agents = sorted(agent_counter.keys())
    evidence.owner_linked_offices = sorted(office_counter.keys())
    evidence.repeat_agent_on_owner_inventory = any(count >= 2 for count in agent_counter.values())

    unique_listing_keys = len(matched_by_key)
    if total_cluster_lots >= 5 and 1 <= unique_listing_keys <= 3:
        ratio = unique_listing_keys / total_cluster_lots
        if ratio <= 0.3:
            evidence.partial_release_test_water = True

    return evidence
