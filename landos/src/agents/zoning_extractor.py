"""Zoning extractor — read Tier 1 municipality vault note and return setback JSON.

Reads the vault note directly from the filesystem (Milestone 2 approach).
The obsidian/reader.py abstraction is deferred to Milestone 3.

If the vault note is missing or the requested district is not found in the note,
returns a ``zoning_blocked`` signal rather than raising an exception. This is
expected pipeline behavior — the caller emits the signal so the laptop /loop
worker can trigger ingest-municipality via Codex.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


# Default vault path: env var or repo default.
_ENV_VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "/Users/bennett2026/Documents/Brain/stranded-lots")
VAULT_PATH = Path(_ENV_VAULT_PATH)


# ── Regex helpers ─────────────────────────────────────────────────────

_BOLD_NUMBER = re.compile(r"\*\*([^*]+)\*\*")


def _extract_number(cell: str) -> str:
    """Return the first bold value from a table cell, stripped of formatting."""
    m = _BOLD_NUMBER.search(cell)
    if not m:
        return cell.strip()
    return m.group(1).strip()


def _parse_float(raw: str) -> float:
    """Strip commas, units, percent signs and return a float."""
    cleaned = re.sub(r"[,%a-zA-Z\s]", "", raw)
    return float(cleaned)


def _parse_int(raw: str) -> int:
    cleaned = re.sub(r"[,%a-zA-Z\s]", "", raw)
    return int(cleaned)


def _parse_height(raw: str) -> tuple[float, int]:
    """Parse '2 stories / 25 ft' → (25.0, 2).  Falls back to (raw_ft, 0)."""
    stories_match = re.search(r"(\d+)\s*stories?", raw, re.IGNORECASE)
    ft_match = re.search(r"([\d,]+(?:\.\d+)?)\s*ft", raw, re.IGNORECASE)
    stories = int(stories_match.group(1)) if stories_match else 0
    height_ft = float(ft_match.group(1).replace(",", "")) if ft_match else 0.0
    return height_ft, stories


# ── Vault note parser ─────────────────────────────────────────────────

_ROW_PATTERN = re.compile(r"^\|(.+)\|(.+)\|(.+)\|")


def _parse_district_table(section_text: str, district_code: str) -> dict[str, Any] | None:
    """Parse the dimensional-standards table from a district section.

    Returns a dict of SetbackRules fields (minus source_url / pulled_on) or
    None if the expected rows are not found.

    The table format:
        | Standard | {district_code} Value | Confidence |
        |---|---|---|
        | Minimum lot area | **5,400 sq ft** | ✅ confirmed |
        ...
    """
    # Collect table rows (skip header and separator lines)
    rows: dict[str, str] = {}
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        label = parts[0].strip()
        value_cell = parts[1].strip()
        # Skip header / separator rows
        if re.match(r"^[-:]+$", value_cell) or label.lower().startswith("standard"):
            continue
        bold_val = _extract_number(value_cell)
        rows[label.lower()] = bold_val

    if not rows:
        return None

    # Map row labels → SetbackRules fields
    def _find(keywords: list[str]) -> str | None:
        for key in rows:
            if all(kw in key for kw in keywords):
                return rows[key]
        return None

    lot_area_raw = _find(["lot", "area"])
    lot_width_raw = _find(["lot", "width"])
    coverage_raw = _find(["coverage"])
    front_raw = _find(["front"])
    side_least_raw = _find(["side", "least"]) or _find(["side setback (least"])
    side_total_raw = _find(["side", "total"]) or _find(["side setback (total"])
    rear_raw = _find(["rear"])
    height_raw = _find(["height"])
    ground_floor_raw = _find(["ground floor"]) or _find(["ground", "floor"])

    required = [lot_area_raw, lot_width_raw, coverage_raw, front_raw,
                side_least_raw, side_total_raw, rear_raw, height_raw, ground_floor_raw]
    if any(v is None for v in required):
        return None

    height_ft, max_stories = _parse_height(height_raw)

    return {
        "district_code": district_code,
        "min_lot_sf": _parse_int(lot_area_raw),
        "min_width_ft": _parse_float(lot_width_raw),
        "max_coverage_pct": _parse_float(coverage_raw),
        "max_height_ft": height_ft,
        "max_stories": max_stories,
        "front_setback_ft": _parse_float(front_raw),
        "side_least_ft": _parse_float(side_least_raw),
        "side_total_ft": _parse_float(side_total_raw),
        "rear_setback_ft": _parse_float(rear_raw),
        "min_ground_floor_sf": _parse_int(ground_floor_raw),
    }


def _extract_frontmatter_value(content: str, key: str) -> str | None:
    """Return the scalar value for a YAML frontmatter key, or None."""
    # Frontmatter is between the first two `---` lines
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None
    fm = fm_match.group(1)
    for line in fm.splitlines():
        m = re.match(rf"^{re.escape(key)}\s*:\s*['\"]?(.*?)['\"]?\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def _find_district_section(content: str, district_code: str) -> str | None:
    """Return the text of the district's ### section, or None if not found."""
    # Match `### R-5` (or `### R-5 — ...` etc.) case-insensitively on district code
    pattern = re.compile(
        rf"^###\s+{re.escape(district_code)}(?:\b.*)?$",
        re.MULTILINE | re.IGNORECASE,
    )
    m = pattern.search(content)
    if not m:
        return None

    section_start = m.end()
    # The section ends at the next heading of equal or higher level (## or ###)
    next_heading = re.search(r"^#{1,3}\s", content[section_start:], re.MULTILINE)
    if next_heading:
        section_text = content[section_start: section_start + next_heading.start()]
    else:
        section_text = content[section_start:]
    return section_text


def _find_pulled_on(section_text: str, frontmatter_content: str) -> date:
    """Return a pulled_on date from the section or fall back to today."""
    # Look for 'pulled_on' in frontmatter
    fm_val = _extract_frontmatter_value(frontmatter_content, "pulled_on")
    if fm_val:
        try:
            return date.fromisoformat(fm_val)
        except ValueError:
            pass
    # Look for an ISO date in the section text
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", section_text)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return date.today()


# ── Public API ────────────────────────────────────────────────────────

def extract_zoning(
    state: str,
    municipality: str,
    district_code: str,
    vault_path: Path | None = None,
) -> dict[str, Any]:
    """Extract dimensional setbacks for a municipality/district from the Tier 1 vault note.

    Args:
        state: Two-letter state abbreviation, e.g. "MI". Currently unused in
            path resolution but included for future multi-state support.
        municipality: Municipality name, e.g. "Ypsilanti Township". Used to
            locate the vault note at ``{vault_path}/04 - Municipalities/{municipality}.md``.
        district_code: Zoning district code, e.g. "R-5". Case-insensitive match
            on the ``### {district_code}`` heading.
        vault_path: Override the vault root. Defaults to the ``OBSIDIAN_VAULT_PATH``
            env var or ``/Users/bennett2026/Documents/Brain/stranded-lots``.

    Returns:
        On success::

            {"status": "ok", "setbacks": {<SetbackRules fields>}}

        On blocked::

            {"status": "zoning_blocked", "municipality": ..., "district_code": ..., "reason": ...}

        Possible ``reason`` values:
        - ``"vault_note_not_found"`` — the ``.md`` file does not exist
        - ``"district_not_in_note"`` — file exists but no ``### {district_code}`` section
        - ``"table_parse_failed"`` — section found but table could not be parsed
    """
    root = vault_path if vault_path is not None else VAULT_PATH
    note_path = root / "04 - Municipalities" / f"{municipality}.md"

    if not note_path.exists():
        return {
            "status": "zoning_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "reason": "vault_note_not_found",
        }

    content = note_path.read_text(encoding="utf-8")
    district_code_upper = district_code.upper()

    section_text = _find_district_section(content, district_code_upper)
    if section_text is None:
        return {
            "status": "zoning_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "reason": "district_not_in_note",
        }

    fields = _parse_district_table(section_text, district_code_upper)
    if fields is None:
        return {
            "status": "zoning_blocked",
            "municipality": municipality,
            "district_code": district_code,
            "reason": "table_parse_failed",
        }

    # Source URL: prefer frontmatter zoning_ordinance_url, else scan section body
    source_url = _extract_frontmatter_value(content, "zoning_ordinance_url") or ""
    if not source_url:
        url_match = re.search(r"https?://[^\s\)\]>\"]+", section_text)
        if url_match:
            source_url = url_match.group(0).rstrip(".")

    pulled_on = _find_pulled_on(section_text, content)

    fields["source_url"] = source_url
    fields["pulled_on"] = pulled_on.isoformat()

    return {"status": "ok", "setbacks": fields}
