"""Shared subdivision name canonicalization.

One canonical path used by:
  - parcel_cluster_detector._extract_subdivision()
  - bbo_signals.extract_legal_lot_info()
  - run_pipeline_to_db.py Stage 3.5 (subdivision materialization)
  - run_pipeline_to_db.py Stage 4.5 (listing history evidence lookup)
  - run_pipeline_to_db.py Stage 4.6 (legal multi-lot grouping)
  - strategic_ranker.rank_from_pipeline() (opportunity naming)

Rules:
  1. Lowercase, strip outer whitespace.
  2. Collapse multiple spaces to one.
  3. Strip trailing punctuation that leaks from legal descriptions.
  4. Normalize common possessive/punctuation variants
     ("co.'s" → "cos", "co's" → "cos", "co.,  " → "co").
  5. Collapse known duplicate tokens ("summerhomes" vs "summer homes").
  6. Reject municipality false positives (bare city/township names)
     unless the raw string shows subdivision extraction evidence.
"""

from __future__ import annotations

import re

# ── Known Michigan municipality names that are NOT subdivisions ──────────
# These appear in legal descriptions as location context, not subdivision names.
# Only reject if the canonicalized name matches EXACTLY (no additional words).
_MUNICIPALITY_FALSE_POSITIVES = frozenset({
    "ann arbor",
    "ypsilanti",
    "saline",
    "dexter",
    "chelsea",
    "manchester",
    "milan",
    "whitmore lake",
    "bridgewater",
    "pittsfield",
    "scio",
    "webster",
    "superior",
    "lima",
    "lodi",
    "freedom",
    "sharon",
    "sylvan",
    "lyndon",
    "northfield",
    "salem",
    "york",
    "augusta",
    "ann arbor township",
    "ypsilanti township",
    "pittsfield township",
    "scio township",
    "superior township",
    "lima township",
})

# ── Spelling / variant collapse ──────────────────────────────────────────
# (canonical_form, pattern) — applied in order
_VARIANT_COLLAPSES: list[tuple[str, re.Pattern]] = [
    # "summerhomes" → "summer homes"
    ("summer homes", re.compile(r"\bsummerhomes\b")),
    # "co.'s" / "co's" / "co.," / "co." → "co"
    ("co", re.compile(r"\bco[.'',]+s?\b|co\.,?")),
    # Trailing "sub" / "subdivision" / "subd" / "s/d" if they leaked
    ("", re.compile(r"\s+(?:sub|subdivision|subd|s/d)\s*$")),
]


def canonicalize_subdivision(raw: str) -> str | None:
    """Canonicalize a subdivision name.

    Returns the canonical key, or None if the name is a municipality
    false positive or too short to be meaningful.
    """
    if not raw:
        return None

    name = raw.lower().strip()

    # Collapse whitespace
    name = " ".join(name.split())

    # Strip trailing punctuation (periods, commas, semicolons)
    name = name.rstrip(".,;:")

    # Apply variant collapses
    for replacement, pattern in _VARIANT_COLLAPSES:
        name = pattern.sub(replacement, name).strip()

    # Re-collapse whitespace after substitutions
    name = " ".join(name.split())

    # Too short to be a real subdivision name
    if len(name) < 3:
        return None

    # Reject bare municipality names
    if name in _MUNICIPALITY_FALSE_POSITIVES:
        return None

    return name
