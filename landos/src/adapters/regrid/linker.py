"""Parcel-to-listing linkage logic for the Regrid adapter.

ParcelListingLinker tries three ordered methods. First match wins.

Method 1 — address_match
  Normalize both sides (lowercase, strip punctuation, expand abbreviations).
  Compare full normalized address string. Requires Listing.address_raw and
  Regrid address fields.

Method 2 — parcel_number_match
  Strip hyphens, spaces, and leading zeros from both sides.
  Compare normalized APN string. Requires Listing.parcel_number_raw and
  Parcel.apn_or_parcel_number.

Method 3 — geo_match
  Only attempted when Listing has lat/lon and Parcel has centroid.
  Haversine distance: if centroid is within GEO_MATCH_THRESHOLD_METERS of
  the listing coordinate, the parcel is considered a match.
  Shapely polygon intersection is not used here — centroid proximity is
  sufficient for Phase 1 and avoids the shapely dependency until PostGIS
  is wired in Step 5+.

LinkResult namedtuple:
  parcel       — the matched Parcel
  listing      — the matched Listing
  method       — string: "address_match" | "parcel_number_match" | "geo_match"
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import NamedTuple

from src.models.listing import Listing
from src.models.parcel import Parcel

# ── Constants ──────────────────────────────────────────────────────────────

GEO_MATCH_THRESHOLD_METERS: float = 50.0

_STREET_ABBREVIATIONS: dict[str, str] = {
    r"\bST\b": "STREET",
    r"\bAVE\b": "AVENUE",
    r"\bAV\b": "AVENUE",
    r"\bDR\b": "DRIVE",
    r"\bBLVD\b": "BOULEVARD",
    r"\bRD\b": "ROAD",
    r"\bLN\b": "LANE",
    r"\bCT\b": "COURT",
    r"\bPL\b": "PLACE",
    r"\bCIR\b": "CIRCLE",
    r"\bTRL\b": "TRAIL",
    r"\bWAY\b": "WAY",
    r"\bHWY\b": "HIGHWAY",
    r"\bPKWY\b": "PARKWAY",
    r"\bN\b": "NORTH",
    r"\bS\b": "SOUTH",
    r"\bE\b": "EAST",
    r"\bW\b": "WEST",
}


class LinkResult(NamedTuple):
    parcel: Parcel
    listing: Listing
    method: str  # address_match | parcel_number_match | geo_match


class ParcelListingLinker:
    """Links a single Parcel to the best-matching Listing from a candidate pool.

    Usage:
        linker = ParcelListingLinker(listings)
        result = linker.find_match(parcel)
        if result:
            # result.parcel, result.listing, result.method
    """

    def __init__(self, listings: list[Listing]) -> None:
        self._listings = listings
        # Pre-build normalized address index keyed on normalized address string
        self._address_index: dict[str, Listing] = {}
        self._parcel_num_index: dict[str, Listing] = {}
        for listing in listings:
            if listing.address_raw:
                key = _normalize_address(listing.address_raw)
                if key:
                    self._address_index[key] = listing
            if listing.parcel_number_raw:
                key = _normalize_apn(listing.parcel_number_raw)
                if key:
                    self._parcel_num_index[key] = listing

    def find_match(self, parcel: Parcel) -> LinkResult | None:
        """Try all three linkage methods in priority order. Return first match."""
        result = self._try_address_match(parcel)
        if result:
            return result
        result = self._try_parcel_number_match(parcel)
        if result:
            return result
        return self._try_geo_match(parcel)

    # ── Method 1: address match ────────────────────────────────────────

    def _try_address_match(self, parcel: Parcel) -> LinkResult | None:
        parcel_addr = parcel.address_raw
        if not parcel_addr:
            return None
        key = _normalize_address(parcel_addr)
        if not key:
            return None
        listing = self._address_index.get(key)
        if listing:
            return LinkResult(parcel=parcel, listing=listing, method="address_match")
        return None

    # ── Method 2: parcel number match ─────────────────────────────────

    def _try_parcel_number_match(self, parcel: Parcel) -> LinkResult | None:
        key = _normalize_apn(parcel.apn_or_parcel_number)
        if not key:
            return None
        listing = self._parcel_num_index.get(key)
        if listing:
            return LinkResult(parcel=parcel, listing=listing, method="parcel_number_match")
        return None

    # ── Method 3: geo match ────────────────────────────────────────────

    def _try_geo_match(self, parcel: Parcel) -> LinkResult | None:
        if not parcel.centroid:
            return None
        try:
            parcel_lon, parcel_lat = parcel.centroid["coordinates"]
        except (KeyError, TypeError, ValueError):
            return None

        best_listing: Listing | None = None
        best_dist: float = GEO_MATCH_THRESHOLD_METERS

        for listing in self._listings:
            if listing.latitude is None or listing.longitude is None:
                continue
            dist = _haversine_meters(
                parcel_lat, parcel_lon,
                listing.latitude, listing.longitude,
            )
            if dist <= best_dist:
                best_dist = dist
                best_listing = listing

        if best_listing:
            return LinkResult(parcel=parcel, listing=best_listing, method="geo_match")
        return None


# ── Normalisation helpers ──────────────────────────────────────────────────

def _normalize_address(raw: str) -> str:
    """Lowercase, strip punctuation, expand common abbreviations."""
    s = raw.upper().strip()
    # Remove punctuation except spaces
    s = re.sub(r"[^\w\s]", " ", s)
    # Expand abbreviations
    for pattern, replacement in _STREET_ABBREVIATIONS.items():
        s = re.sub(pattern, replacement, s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # Normalize unicode
    s = unicodedata.normalize("NFKC", s)
    return s.lower()


def _normalize_apn(raw: str) -> str:
    """Strip hyphens, spaces, and leading zeros for APN comparison.

    Phase 1 limitation: strips ALL leading zeros from the concatenated string,
    not per-segment. This is sufficient for Washtenaw County single-county use
    but may cause false positives/negatives for multi-segment APN formats
    where interior segments have meaningful leading zeros (e.g., Michigan PINs
    like "12-003-045" where "003" is distinct from "3").

    Production fix (multi-county): split on separator, lstrip("0") per segment,
    rejoin. Deferred until multi-county ingestion is wired.
    """
    s = re.sub(r"[-\s]", "", raw.strip())
    s = s.lstrip("0") or "0"
    return s.lower()


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in meters between two lat/lon points."""
    r = 6_371_000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
