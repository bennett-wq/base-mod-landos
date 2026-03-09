from __future__ import annotations
import re
from typing import Optional
from src.models.listing import Listing

CDOM_THRESHOLD_DEFAULT = 90
CDOM_EXIT_THRESHOLD = 120
AGENT_ACCUMULATION_THRESHOLD = 3
PARCEL_HIGH_SCORE_THRESHOLD = 0.70

REMARKS_PATTERNS: dict[str, str] = {
    "package_language":     r"\b(package|bulk|portfolio|all remaining|take all|remaining lots?)\b",
    "fatigue_language":     r"\b(bring (all |any )?offer|motivated|price (reduced|negotiable)|must sell)\b",
    "restriction_language": r"\b(no split|no subdivision|deed restrict|covenant|hoa approval)\b",
    "utility_language":     r"\b(utilities? (at|to) (street|site|lot)|sewer (available|stubbed)|water (available|at))\b",
    "bulk_language":        r"\b(lot \d+ of \d+|phase \d+|\d+ lots? available|remaining lots?|subdivision remnant)\b",
}


def detect_cdom_threshold(listing: Listing, threshold: int = CDOM_THRESHOLD_DEFAULT) -> bool:
    """True if CDOM >= threshold. Returns False if cdom is None."""
    if listing.cdom is None:
        return False
    return listing.cdom >= threshold


def detect_developer_exit(listing: Listing) -> tuple[bool, str]:
    """
    Returns (detected, reason). Fires on:
    - off_market_date set on active listing
    - cancellation with cdom >= 60
    - withdrawal with cdom >= 120
    - major_change_type containing "Expired" or "Withdrawn"
    reason = most specific signal found.
    """
    if listing.major_change_type and any(
        kw in listing.major_change_type for kw in ("Expired", "Withdrawn")
    ):
        return True, f"major_change_type={listing.major_change_type}"
    if listing.cancellation_date and listing.cdom is not None and listing.cdom >= 60:
        return True, f"cancellation with cdom={listing.cdom}"
    if listing.withdrawal_date and listing.cdom is not None and listing.cdom >= 120:
        return True, f"withdrawal with cdom={listing.cdom}"
    if listing.off_market_date and listing.standard_status.value in ("active", "pending"):
        return True, f"off_market_date set on status={listing.standard_status}"
    return False, ""


def detect_private_remarks_signals(listing: Listing) -> list[str]:
    """
    Regex scan of private_remarks for signal categories.
    Returns list of matched category keys. Returns [] if None or empty.
    """
    if not listing.private_remarks:
        return []
    matched = []
    for category, pattern in REMARKS_PATTERNS.items():
        if re.search(pattern, listing.private_remarks, re.IGNORECASE):
            matched.append(category)
    return matched


def detect_agent_land_accumulation(
    listing: Listing,
    all_listings: list[Listing],
    threshold: int = AGENT_ACCUMULATION_THRESHOLD,
) -> tuple[bool, int]:
    """
    True if listing.list_agent_key matches >= threshold listings in all_listings.
    Returns (detected, count). Returns (False, 0) if list_agent_key is None.
    """
    if listing.list_agent_key is None:
        return False, 0
    count = sum(
        1 for l in all_listings
        if l.list_agent_key is not None and l.list_agent_key == listing.list_agent_key
    )
    return count >= threshold, count


def detect_office_land_program(
    listing: Listing,
    all_listings: list[Listing],
    threshold: int = 5,
) -> tuple[bool, int]:
    """
    True if listing.listing_office_id matches >= threshold listings.
    Returns (detected, count). Returns (False, 0) if listing_office_id is None.
    """
    if listing.listing_office_id is None:
        return False, 0
    count = sum(
        1 for l in all_listings
        if l.listing_office_id is not None and l.listing_office_id == listing.listing_office_id
    )
    return count >= threshold, count


def detect_subdivision_remnant(listing: Listing) -> tuple[bool, str]:
    """
    True if:
    - number_of_lots > 1, OR
    - legal_description contains Lot/Block/Plat pattern, OR
    - subdivision_name_raw is set AND cdom >= 180
    Returns (detected, reason).
    """
    if listing.number_of_lots is not None and listing.number_of_lots > 1:
        return True, f"number_of_lots={listing.number_of_lots}"
    if listing.legal_description and re.search(
        r"\b(lot\s+\d+|block\s+\d+|plat)\b", listing.legal_description, re.IGNORECASE
    ):
        return True, "legal_description contains Lot/Block/Plat"
    if (
        listing.subdivision_name_raw
        and listing.cdom is not None
        and listing.cdom >= 180
    ):
        return True, f"subdivision_name_raw set with cdom={listing.cdom}"
    return False, ""


def detect_market_velocity(
    listing: Listing,
    sold_listings: list[Listing],
    geography_key: str,
) -> Optional[float]:
    """
    Returns avg days-to-close for comparable sold listings in same geography.
    Returns None if fewer than 3 comps available.
    geography_key = listing city or county for grouping.
    Utility-only in Step 4.5 — no events emitted here.
    """
    comps = [
        l for l in sold_listings
        if l.city == geography_key and l.close_date is not None and l.cdom is not None
    ]
    if len(comps) < 3:
        return None
    return sum(l.cdom for l in comps) / len(comps)
