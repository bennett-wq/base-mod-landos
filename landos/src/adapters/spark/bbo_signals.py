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
    "fatigue_language":     r"\b(bring (all |any )?offer|motivated|price (reduced|negotiable)|must sell|priced to sell|make (an )?offer|submit (all )?offers|all (reasonable )?offers)\b",
    "restriction_language": r"\b(no split|no subdivision|deed restrict|covenant|hoa approval)\b",
    "utility_language":     r"\b(utilities? (at|to) (street|site|lot)|sewer (available|stubbed|at)|water (available|at)|natural gas|city (water|sewer)|municipal (water|sewer)|public (water|sewer))\b",
    "bulk_language":        r"\b(lot \d+ of \d+|phase \d+|\d+ lots? available|remaining lots?|subdivision remnant)\b",
    "distress_language":    r"\b(as[- ]is|below (market|appraised)|estate sale|foreclosure|bank[- ]owned|reo\b|tax sale|short sale|must close|seller relocat|price just reduced|reduced below)",
    "infrastructure_ready": r"\b(paved road|curb and gutter|electric available|gas available|hookup|tap fee|city (water|sewer|services)|public (water|sewer|utilities)|storm sewer|sanitary sewer|municipal (water|sewer|services))\b",
    "development_ready":    r"\b(site plan|perc test|perk test|soil eval|survey (available|complete|done|attached)|ready to build|shovel[- ]?ready|ready for (construction|development)|splits? (available|approved|pending)|approved for \d|zoned for \d|master deed)\b",
}


def detect_cdom_threshold(listing: Listing, threshold: int = CDOM_THRESHOLD_DEFAULT) -> bool:
    """True if CDOM >= threshold. Returns False if cdom is None."""
    if listing.cdom is None:
        return False
    return listing.cdom >= threshold


def detect_developer_exit(listing: Listing) -> tuple[bool, str]:
    """
    Returns (detected, reason). Fires on first matching signal (short-circuit):
    1. major_change_type containing "Expired" or "Withdrawn"
    2. cancellation_date set AND cdom >= 60
    3. withdrawal_date set AND cdom >= 120
    4. off_market_date set on active/pending listing

    Field precedence note: a listing with major_change_type="Withdrawn" fires
    via branch 1 regardless of cdom, while a listing with only withdrawal_date
    set requires cdom >= 120 via branch 3. This is intentional —
    major_change_type is a stronger MLS-confirmed signal than withdrawal_date
    alone. The two fields can describe the same physical state but
    major_change_type carries higher confidence.
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


def detect_all_remarks_signals(listing: Listing) -> list[str]:
    """Scan ALL text fields for signal categories: public remarks, private
    remarks, showing instructions, and agent-only remarks.

    Returns deduplicated list of matched category keys.
    """
    text_fields = [
        listing.remarks_raw,
        listing.private_remarks,
        listing.showing_instructions,
        getattr(listing, 'agent_only_remarks', None),
    ]
    matched: set[str] = set()
    for text in text_fields:
        if not text:
            continue
        for category, pattern in REMARKS_PATTERNS.items():
            if category not in matched and re.search(pattern, text, re.IGNORECASE):
                matched.add(category)
    return sorted(matched)


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


# ── Broker-note patterns (private remarks only — agent-to-agent intel) ────────

BROKER_NOTE_PATTERNS: dict[str, str] = {
    # Seller exit intent
    "splits_available":    r"\b(splits? (are |is )?(available|allowed|possible)|splittable|additional split available)\b",
    "seller_is_agent":     r"\b(seller (is |/owner is )(a |an? )?licensed|agent[- ]owned|broker[- ]owned|seller.*licensed (realtor|agent|broker|salesperson))\b",
    "hoa_inactive":        r"\b(hoa (not |in)active|no (active )?hoa|hoa (is )?dissolved)\b",
    "all_offers":          r"\b(all (reasonable )?offers|present all offers|entertain all offers|submit (all )?offers to)\b",
    "owner_plans":         r"\b(owner has plans|willing to share|share with buyer|plans available)\b",
    "lot_being_split":     r"\b(split (is )?(pending|being|in process)|currently (being )?split|contingent (upon|on) split|seller (to |will )?(pay|provide).*(split|survey))\b",
    "former_listing":      r"\b(former(ly)? listed|previous(ly)? listed|was listed|re-?list|back on (the )?market)\b",
    # Multi-parcel / ownership structure
    "multi_parcel":        r"\b(\d+ (separate )?lots?\b.*tax id|tax id.*\d+.*tax id|two (separate )?parcels|parcel.*parcel|listing is for (two|three|\d+) parcels?|sold.*together)\b",
    "adjacent_available":  r"\b(adjacent (lot|parcel|property) (also )?(available|for sale)|combine|can be (purchased|bought|sold) (separately|together))\b",
    # Site testing evidence
    "site_tested":         r"\b(soil eval|perc (test|results)|perk (test|results)|survey (attached|on file|available|completed|stakes)|staked|stake and boundary)\b",
    # Seller concession signals
    "seller_pays":         r"\b(seller (to |will )?(pay|cover|provide).*(cost|survey|split|closing)|seller (financing|financ|concession))\b",
    "highest_best":        r"\b(highest and best|offers?\s+due|offer deadline)\b",
}


def detect_broker_note_signals(listing: Listing) -> list[str]:
    """Scan private/agent-only remarks for broker-specific intelligence.

    These patterns target agent-to-agent communications that contain
    seller intent and property status information not found in public remarks.
    """
    text_fields = [
        listing.private_remarks,
        getattr(listing, 'agent_only_remarks', None),
        listing.showing_instructions,
    ]
    matched: set[str] = set()
    for text in text_fields:
        if not text:
            continue
        for category, pattern in BROKER_NOTE_PATTERNS.items():
            if category not in matched and re.search(pattern, text, re.IGNORECASE):
                matched.add(category)
    return sorted(matched)


# ── Structured infrastructure profile from BBO fields ────────────────────────

def _parse_list_field(val) -> list[str]:
    """Parse a structured BBO field that might be a string repr of a list."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if v and str(v).strip()]
    s = str(val).strip()
    if s.startswith('[') and s.endswith(']'):
        # Parse Python list repr: "['Natural Gas Available', 'Electricity Connected']"
        items = re.findall(r"'([^']+)'", s)
        return [i.strip() for i in items if i.strip()]
    return [s] if s and s != 'None' else []


def extract_infrastructure_profile(listing: Listing) -> dict:
    """Extract a structured infrastructure profile from BBO fields.

    Returns a dict with:
      - public_sewer: bool
      - public_water: bool
      - natural_gas: bool (connected or available)
      - electric: bool (connected or available)
      - paved_road: bool
      - storm_sewer: bool
      - buildable: bool (from lot_features)
      - site_condo: bool (from lot_features — master deed development)
      - wetland: bool (from lot_features — constraint)
      - infra_score: float 0.0-1.0 (composite readiness)
      - infra_flags: list[str] (human-readable summary)
    """
    utilities = _parse_list_field(listing.utilities)
    sewer = _parse_list_field(listing.sewer)
    water = _parse_list_field(listing.water_source)
    road = _parse_list_field(listing.road_surface_type)
    lot_feat = _parse_list_field(listing.lot_features)

    util_lower = [u.lower() for u in utilities]
    sewer_lower = [s.lower() for s in sewer]
    water_lower = [w.lower() for w in water]
    road_lower = [r.lower() for r in road]
    feat_lower = [f.lower() for f in lot_feat]

    public_sewer = any('public' in s for s in sewer_lower)
    public_water = any('public' in w for w in water_lower)
    has_gas = any('natural gas' in u for u in util_lower)
    gas_connected = any('natural gas connected' in u for u in util_lower)
    has_electric = any('electric' in u for u in util_lower)
    electric_connected = any('connected' in u and 'electric' in u for u in util_lower)
    paved = any('paved' in r for r in road_lower)
    storm_sewer = any('storm' in u for u in util_lower)
    buildable = any('buildable' in f for f in feat_lower)
    site_condo = any('site condo' in f for f in feat_lower)
    wetland = any('wetland' in f for f in feat_lower)

    # Composite infrastructure readiness score
    score = 0.0
    flags = []
    if public_sewer:
        score += 0.20
        flags.append('Public Sewer')
    if public_water:
        score += 0.15
        flags.append('Public Water')
    if gas_connected:
        score += 0.15
        flags.append('Gas Connected')
    elif has_gas:
        score += 0.10
        flags.append('Gas Available')
    if electric_connected:
        score += 0.15
        flags.append('Electric Connected')
    elif has_electric:
        score += 0.10
        flags.append('Electric Available')
    if paved:
        score += 0.10
        flags.append('Paved Road')
    if storm_sewer:
        score += 0.10
        flags.append('Storm Sewer')
    if buildable:
        score += 0.10
        flags.append('Buildable')
    if site_condo:
        score += 0.05
        flags.append('Site Condo')
    if wetland:
        score -= 0.10
        flags.append('Wetland (constraint)')

    return {
        'public_sewer': public_sewer,
        'public_water': public_water,
        'natural_gas': has_gas,
        'gas_connected': gas_connected,
        'electric': has_electric,
        'electric_connected': electric_connected,
        'paved_road': paved,
        'storm_sewer': storm_sewer,
        'buildable': buildable,
        'site_condo': site_condo,
        'wetland': wetland,
        'infra_score': min(max(score, 0.0), 1.0),
        'infra_flags': flags,
    }


def detect_site_condo_from_legal(listing: Listing) -> tuple[bool, str]:
    """Detect site condo / master deed references from legal_remarks.

    Returns (detected, detail) where detail contains the matched evidence.
    """
    legal = getattr(listing, 'legal_remarks', None) or listing.legal_description or ''
    if not legal:
        return False, ''

    # Master Deed reference: "M.D. L 4188 P 480 UNIT 28 AUGUSTA COMMONS"
    md_match = re.search(r'M\.?D\.?\s+L\s*\d+\s+P\s*\d+\s+UNIT\s+(\d+)\s+(.+?)(?:\s+SPLIT|\s*$)', legal, re.IGNORECASE)
    if md_match:
        return True, f"Master Deed Unit {md_match.group(1)}: {md_match.group(2).strip()}"

    # UNIT reference without M.D.
    unit_match = re.search(r'\bUNIT\s+(\d+)\s+(.{3,40}?)(?:\s+SPLIT|\s+PCL|\s*$)', legal, re.IGNORECASE)
    if unit_match:
        return True, f"Unit {unit_match.group(1)}: {unit_match.group(2).strip()}"

    return False, ''


def extract_legal_lot_info(listing: Listing) -> dict | None:
    """Extract subdivision name and lot number from legal description fields.

    Parses patterns like:
      - "Lot 7 York Crest subdivision"
      - "M.D. L3716 P931 UNIT 16 MANCHESTER SITE CONDOMINIUM"
      - "UNIT 28 AUGUSTA COMMONS"
      - "LOT 5 SMITH ACRES SUB"

    Returns dict with 'subdivision', 'lot_number', 'is_unit' or None.
    """
    for text in [getattr(listing, 'legal_remarks', None),
                 listing.legal_description,
                 getattr(listing, 'tax_legal_description', None)]:
        if not text:
            continue

        # UNIT N SUBDIVISION_NAME (site condo)
        m = re.search(r'\bUNIT\s+(\d+)\s+([A-Z][A-Z\s\'.]+?)(?:\s+SPLIT|\s+PCL|\s*$)', text, re.IGNORECASE)
        if m:
            return {
                'subdivision': m.group(2).strip().lower(),
                'lot_number': int(m.group(1)),
                'is_unit': True,
            }

        # LOT N SUBDIVISION SUB/SUBDIVISION
        m = re.search(r'\bLOT\s+(\d+[A-Z]?)\s+(.+?)\s+(?:SUB|SUBDIVISION|SUBD|S/D)', text, re.IGNORECASE)
        if m:
            name = re.sub(r'\s+BLK\s+.*', '', m.group(2), flags=re.IGNORECASE).strip()
            try:
                lot_num = int(re.sub(r'[A-Z]', '', m.group(1)))
            except ValueError:
                lot_num = 0
            if len(name) >= 3:
                return {
                    'subdivision': name.lower(),
                    'lot_number': lot_num,
                    'is_unit': False,
                }

        # Lot N SUBDIVISION_NAME (without explicit SUB suffix)
        m = re.search(r'\bLot\s+(\d+)\s+([A-Z][a-zA-Z\s]+?)(?:\s+subdivision|\s*$)', text, re.IGNORECASE)
        if m and len(m.group(2).strip()) >= 3:
            return {
                'subdivision': m.group(2).strip().lower(),
                'lot_number': int(m.group(1)),
                'is_unit': False,
            }

    return None


def detect_same_subdivision_listings(listings: list[Listing]) -> dict[str, list[dict]]:
    """Group listings by subdivision name from legal descriptions.

    Returns dict of subdivision_name → list of {listing, lot_number, is_unit}.
    Only includes subdivisions with 2+ listings (the multi-lot signal).
    """
    from collections import defaultdict
    by_sub: dict[str, list[dict]] = defaultdict(list)

    for l in listings:
        info = extract_legal_lot_info(l)
        if info:
            by_sub[info['subdivision']].append({
                'listing': l,
                'lot_number': info['lot_number'],
                'is_unit': info['is_unit'],
            })

    # Only return subdivisions with 2+ listings
    return {k: v for k, v in by_sub.items() if len(v) >= 2}


def detect_market_velocity(
    listing: Listing,
    sold_listings: list[Listing],
    geography_key: str,
    geography_field: str = "address_raw",
) -> Optional[float]:
    """
    Returns avg days-to-close for comparable sold listings in same geography.
    Returns None if fewer than 3 comps available.

    geography_key:   value to match against (e.g. "Ann Arbor").
    geography_field: Listing attribute to compare against geography_key.
                     Defaults to address_raw. When a city/county field is
                     added to Listing, switch to that.

    Utility-only in Step 4.5 — no events emitted here.
    """
    comps = [
        l for l in sold_listings
        if getattr(l, geography_field, None) == geography_key
        and l.close_date is not None
        and l.cdom is not None
    ]
    if len(comps) < 3:
        return None
    return sum(l.cdom for l in comps) / len(comps)
