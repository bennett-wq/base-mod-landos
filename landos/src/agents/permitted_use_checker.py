"""Permitted use checker — determine if a use type is permitted in a zoning district.

Answers: "Is a given use type permitted by-right, conditional, or denied in a given
zoning district, and what Sec. 1101 constraints apply?"

For M2, implements deterministic rules for R-5 one-family residential (the McCartney
reference case). Returns use_blocked for any case it cannot determine.

Reads the Tier 1 municipality vault note directly from the filesystem (Milestone 2
approach). The obsidian/reader.py abstraction is deferred to Milestone 3.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


# Default vault path: controlled by OBSIDIAN_VAULT_PATH env var.
# Falls back to None so callers without the env var must pass vault_path= explicitly.
_ENV_VAULT_PATH: str | None = os.environ.get("OBSIDIAN_VAULT_PATH")
VAULT_PATH: Path | None = Path(_ENV_VAULT_PATH) if _ENV_VAULT_PATH else None


# ── Deterministic rules (M2: R-5 only) ───────────────────────────────

# Keyed by (district_code_upper, model_type).
# Each value is (allowed, path, citation, rationale).
_R5_RULES: dict[str, tuple[bool, str, str, str]] = {
    "one_family_residential": (
        True,
        "by-right",
        "Sec. 406.1 + Sec. 1101",
        (
            "One-family dwellings (including modular per PA 230) are by-right in R-5 "
            "subject to Sec. 1101 compatibility standards (min 24 ft width, ≤3:1 ratio, "
            "permanent perimeter foundation, front facade with entry)."
        ),
    ),
    "two_family_residential": (
        False,
        "denied",
        "Sec. 406.1",
        "R-5 is a one-family residential district. Two-family and multi-family uses are not permitted in R-5.",
    ),
    "multi_family": (
        False,
        "denied",
        "Sec. 406.1",
        "R-5 is a one-family residential district. Multi-family uses are not permitted in R-5.",
    ),
    "manufactured_home_community": (
        False,
        "denied",
        "Sec. 410 + Sec. 1162",
        (
            "Manufactured housing communities require the MHP district (Sec. 410). "
            "R-5 does not permit MHP developments."
        ),
    ),
}

# Map from district_code_upper → rules dict.
# Only R-5 is deterministic for M2; all other districts fall through to use_not_deterministic.
_DISTRICT_RULES: dict[str, dict[str, tuple[bool, str, str, str]]] = {
    "R-5": _R5_RULES,
}


# ── Vault note helpers ────────────────────────────────────────────────

def _find_district_section(content: str, district_code: str) -> str | None:
    """Return the text of the district's ### section, or None if not found.

    Copied from zoning_extractor pattern (M2 approach — reader abstraction in M3).
    """
    pattern = re.compile(
        rf"^###\s+{re.escape(district_code)}(?:\b.*)?$",
        re.MULTILINE | re.IGNORECASE,
    )
    m = pattern.search(content)
    if not m:
        return None

    section_start = m.end()
    next_heading = re.search(r"^#+\s", content[section_start:], re.MULTILINE)
    if next_heading:
        return content[section_start: section_start + next_heading.start()]
    return content[section_start:]


# ── Public API ────────────────────────────────────────────────────────

def check_permitted_use(
    model_type: str,
    district_code: str,
    municipality: str,
    state: str,
    vault_path: Path | None = None,
) -> dict[str, Any]:
    """Check whether a use type is permitted in a zoning district.

    Args:
        model_type: Dwelling use type, e.g. "one_family_residential".
        district_code: Zoning district code, e.g. "R-5". Case-normalized to upper.
        municipality: Municipality name, e.g. "Ypsilanti Township".
        state: Two-letter state abbreviation, e.g. "MI".
        vault_path: Override the vault root. Defaults to the OBSIDIAN_VAULT_PATH env var.

    Returns:
        On success (determination made)::

            {
                "status": "ok",
                "result": {
                    "allowed": bool,
                    "path": "by-right" | "conditional" | "denied",
                    "citation": str,
                    "rationale": str,
                }
            }

        On blocked (vault note missing or case not deterministic)::

            {
                "status": "use_blocked",
                "municipality": str,
                "district_code": str,
                "model_type": str,
                "reason": "vault_note_not_found" | "district_not_in_note" | "use_not_deterministic",
            }
    """
    # Normalize district_code upfront so ok and blocked paths return consistent casing.
    district_code = district_code.upper()

    root = vault_path if vault_path is not None else VAULT_PATH
    if root is None:
        raise EnvironmentError(
            "OBSIDIAN_VAULT_PATH env var is required when vault_path is not passed"
        )

    note_path = root / "04 - Municipalities" / f"{municipality}.md"

    if not note_path.exists():
        return {
            "status": "use_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "model_type": model_type,
            "reason": "vault_note_not_found",
        }

    content = note_path.read_text(encoding="utf-8")

    section_text = _find_district_section(content, district_code)
    if section_text is None:
        return {
            "status": "use_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "model_type": model_type,
            "reason": "district_not_in_note",
        }

    # Look up deterministic rules for this district
    district_rules = _DISTRICT_RULES.get(district_code)
    if district_rules is None:
        return {
            "status": "use_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "model_type": model_type,
            "reason": "use_not_deterministic",
        }

    rule = district_rules.get(model_type)
    if rule is None:
        return {
            "status": "use_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "model_type": model_type,
            "reason": "use_not_deterministic",
        }

    allowed, path, citation, rationale = rule
    return {
        "status": "ok",
        "result": {
            "allowed": allowed,
            "path": path,
            "citation": f"{citation} ({municipality})",
            "rationale": rationale,
        },
    }
