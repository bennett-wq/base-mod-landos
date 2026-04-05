"""High-precision party name normalization and matching.

Used for seller_name_raw ↔ owner_name_raw linkage in the stranded-lot engine.
The first implementation intentionally optimizes for trust over recall.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_ENTITY_TOKEN_MAP = {
    "limited": "ltd",
    "ltd": "ltd",
    "company": "co",
    "co": "co",
    "corporation": "corp",
    "corp": "corp",
    "incorporated": "inc",
    "inc": "inc",
    "llc": "llc",
    "l.l.c": "llc",
    "lp": "lp",
    "l.p": "lp",
    "llp": "llp",
    "l.l.p": "llp",
    "trust": "trust",
    "estate": "estate",
}

_ENTITY_MARKERS = frozenset({
    "llc",
    "inc",
    "corp",
    "co",
    "ltd",
    "lp",
    "llp",
    "trust",
    "estate",
    "company",
    "corporation",
    "incorporated",
    "limited",
})


@dataclass(frozen=True)
class PartyMatch:
    matched: bool
    method: str = ""
    confidence: float = 0.0


def _base_normalize(raw: str | None) -> str:
    if not raw:
        return ""
    s = unicodedata.normalize("NFKC", raw).casefold()
    s = s.replace("&", " and ")
    # Normalize quirky possessives like "co.'s", "co's", and "owners'"
    # before punctuation stripping so entity names collapse predictably.
    s = re.sub(r"\b(\w+)\.'s\b", r"\1", s)
    s = re.sub(r"\b(\w+)'s\b", r"\1", s)
    s = re.sub(r"\b(\w+)s'\b", r"\1s", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = " ".join(s.split())
    return s


def strict_party_key(raw: str | None) -> str:
    """Conservative exact-match key."""
    return _base_normalize(raw)


def entity_party_key(raw: str | None) -> str:
    """Exact-match key with common entity suffix normalization."""
    base = _base_normalize(raw)
    if not base:
        return ""
    tokens = []
    for token in base.split():
        mapped = _ENTITY_TOKEN_MAP.get(token, token)
        tokens.append(mapped)
    return " ".join(tokens)


def _looks_like_entity(raw: str | None) -> bool:
    base = _base_normalize(raw)
    if not base:
        return False
    tokens = set(base.split())
    return bool(tokens & _ENTITY_MARKERS)


def _looks_like_person(raw: str | None) -> bool:
    base = _base_normalize(raw)
    if not base or _looks_like_entity(raw):
        return False
    tokens = base.split()
    if not 2 <= len(tokens) <= 3:
        return False
    return all(token.isalpha() and len(token) > 1 for token in tokens)


def person_party_key(raw: str | None) -> str:
    """Exact unordered token key for simple personal names only."""
    if not _looks_like_person(raw):
        return ""
    tokens = sorted(_base_normalize(raw).split())
    return " ".join(tokens)


def match_party_names(left: str | None, right: str | None) -> PartyMatch:
    """High-precision party matcher.

    Order:
      1. strict exact
      2. entity-normalized exact
      3. constrained person-name reorder exact
    """
    left_strict = strict_party_key(left)
    right_strict = strict_party_key(right)
    if left_strict and left_strict == right_strict:
        return PartyMatch(True, "strict_exact", 1.0)

    left_entity = entity_party_key(left)
    right_entity = entity_party_key(right)
    if left_entity and left_entity == right_entity:
        return PartyMatch(True, "entity_exact", 0.98)

    left_person = person_party_key(left)
    right_person = person_party_key(right)
    if left_person and left_person == right_person:
        return PartyMatch(True, "person_reordered_exact", 0.95)

    return PartyMatch(False)
