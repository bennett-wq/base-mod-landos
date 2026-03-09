"""Regrid bulk parcel export field mapping constants for LandOS parcel ingestion.

This module defines:
  - REGRID_TO_PARCEL: mapping from Regrid standard field names to Parcel model fields.
  - VACANCY_CLASS_MAP: normalization of Regrid improvement indicators to VacancyStatus.
  - REQUIRED_FIELDS: minimum fields that must be present for a record to be ingested.

Regrid field names follow the standard Washtenaw County bulk export schema.
Vacancy status is inferred from improvement value / improvement code because
Regrid does not expose a direct vacancy flag.

Phase 1 scope note:
  This mapping covers the Washtenaw County bulk export surface.
  Ottawa and Livingston counties will extend this map when bulk data is
  purchased. Entity resolution (LLC → person, trust → beneficiary) is
  deferred to the Owner resolution layer built in Steps 5–6.
"""

from __future__ import annotations

# ── Regrid standard field → Parcel model field ────────────────────────────
# Fields listed here are direct scalar mappings handled by the normalizer.
# Composite / derived fields (geometry, centroid, vacancy_status) are
# constructed in the normalizer from multiple source fields.

REGRID_TO_PARCEL: dict[str, str] = {
    "parcelnumb": "apn_or_parcel_number",
    "owner": "owner_name_raw",
    "zoning": "zoning_code",
    "usedesc": "land_use_class",
    "legaldesc": "legal_description_raw",
    "frontage": "frontage_feet",
    "depth": "depth_feet",
    "floodzone": "flood_zone",
}

# ── Improvement code strings that indicate a vacant parcel ───────────────
# When improvval == 0 or improvcode matches one of these, vacancy = VACANT.
VACANT_IMPROV_CODES: frozenset[str] = frozenset({
    "VACANT", "V", "0", "UNIMPROVED", "VAC", "VACANT LAND",
})

# ── Minimum required Regrid fields (SkipRecord if absent) ────────────────
REQUIRED_REGRID_FIELDS: tuple[str, ...] = ("ll_uuid", "parcelnumb", "state2", "county")
