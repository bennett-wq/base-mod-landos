"""Incentive agent — read Programs & Incentives Tier 1 vault note, return Program list.

Reads the vault note directly from the filesystem (Milestone 2 approach).
The obsidian/reader.py abstraction is deferred to Milestone 3.

If the vault note is missing or the programs tables are absent, returns a
``programs_blocked`` signal rather than raising. This is expected pipeline
behavior — the caller emits the signal so the laptop /loop worker can trigger
ingest-municipality via Codex.

Geographic applicability (applies_to_parcel) and value_to_deal are deferred to
Milestone 3 when parcel geometry + boundary matching are available. Every program
returned in M2 carries applies_to_parcel=False and value_to_deal=0.0.
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


# ── Markdown table helpers ────────────────────────────────────────────

def _strip_bold(text: str) -> str:
    """Remove ** bold markers from a string."""
    return re.sub(r"\*\*([^*]*)\*\*", r"\1", text).strip()


def _split_row(line: str) -> list[str]:
    """Split a markdown table row into cells, stripped of leading/trailing |."""
    # Remove leading/trailing whitespace + pipes
    line = line.strip().strip("|")
    return [cell.strip() for cell in line.split("|")]


def _is_separator(line: str) -> bool:
    """True if the line is a table separator row like |---|---|---|."""
    stripped = line.strip().strip("|")
    return bool(re.match(r"^[\s\-|:]+$", stripped))


def _parse_table_rows(section_text: str) -> list[list[str]]:
    """Extract data rows from a markdown table in section_text.

    Skips the header row (first table row) and separator row.
    Returns a list of cell-lists for each data row.
    """
    rows: list[list[str]] = []
    header_seen = False
    separator_seen = False

    for line in section_text.splitlines():
        line_stripped = line.strip()
        if not line_stripped.startswith("|"):
            continue
        if _is_separator(line_stripped):
            if header_seen:
                separator_seen = True
            continue
        if not header_seen:
            header_seen = True
            continue
        # Must have seen the separator before counting data rows
        if not separator_seen:
            continue
        cells = _split_row(line_stripped)
        if cells:
            rows.append(cells)

    return rows


# ── Section finder ────────────────────────────────────────────────────

def _find_section(content: str, heading: str) -> str | None:
    """Return text from a ## heading to the next ## heading (or EOF).

    heading should be the exact ## heading text (not regex) to search for.
    """
    # Escape for regex and allow trailing content on the same heading line
    escaped = re.escape(heading)
    pattern = re.compile(rf"^{escaped}.*?$", re.MULTILINE)
    m = pattern.search(content)
    if not m:
        return None

    section_start = m.end()
    # Next ## heading ends the section
    next_h2 = re.search(r"^##\s", content[section_start:], re.MULTILINE)
    if next_h2:
        return content[section_start: section_start + next_h2.start()]
    return content[section_start:]


# ── Row → Program dict converters ────────────────────────────────────

def _row_to_active_program(cells: list[str]) -> dict[str, Any] | None:
    """Map a row from ## Active Incentive Programs to a Program dict.

    Table columns (7):
      0 Program | 1 Authority type | 2 Scope | 3 Authorized | 4 Expires |
      5 Stacking notes | 6 Source
    """
    if len(cells) < 7:
        return None
    name = _strip_bold(cells[0])
    if not name:
        return None

    return {
        "name": name,
        "authority_type": cells[1].strip(),
        "scope": cells[2].strip(),
        "dates_active": f"{cells[3].strip()} \u2192 {cells[4].strip()}",
        "stacking_notes": _strip_bold(cells[5]),
        "source_citation": cells[6].strip(),
        "applies_to_parcel": False,
        "value_to_deal": 0.0,
    }


def _row_to_consumer_program(cells: list[str]) -> dict[str, Any] | None:
    """Map a row from ## Consumer Subsidies (D2C-relevant) to a Program dict.

    Table columns (6):
      0 Program | 1 Amount / benefit | 2 Eligibility gates | 3 Application path |
      4 Funding source | 5 Source
    """
    if len(cells) < 6:
        return None
    name = _strip_bold(cells[0])
    if not name:
        return None

    return {
        "name": name,
        "authority_type": cells[4].strip(),
        "scope": cells[1].strip(),
        "dates_active": "ongoing",
        "stacking_notes": f"{cells[2].strip()} | {cells[3].strip()}",
        "source_citation": cells[5].strip(),
        "applies_to_parcel": False,
        "value_to_deal": 0.0,
    }


# ── Public API ────────────────────────────────────────────────────────

def research_incentives(
    state: str,
    municipality: str,
    parcel_apn: str | None = None,
    vault_path: Path | None = None,
) -> dict[str, Any]:
    """Read the Programs & Incentives Tier 1 vault note and return a Program list.

    Args:
        state: Two-letter state abbreviation, e.g. "MI". Accepted but unused
            in M2 path resolution (included for API parity with M2-3/M2-4).
        municipality: Municipality name, e.g. "Ypsilanti Township". Used to
            locate the vault note at
            ``{vault_path}/04 - Municipalities/{municipality} — Programs & Incentives.md``.
        parcel_apn: APN string for logging/rationale; unused in M2 geo matching.
        vault_path: Override the vault root. Defaults to the OBSIDIAN_VAULT_PATH
            env var.

    Returns:
        On success::

            {
                "status": "ok",
                "municipality": str,
                "applicable_programs": [<Program dicts>],
                "net_incentive_delta": 0.0,
                "rationale": str,
            }

        On blocked::

            {
                "status": "programs_blocked",
                "municipality": str,
                "parcel_apn": str | None,
                "reason": "vault_note_not_found" | "programs_table_not_found",
            }

    Raises:
        EnvironmentError: if vault_path is not passed and OBSIDIAN_VAULT_PATH
            is not set in the environment.
    """
    root = vault_path if vault_path is not None else VAULT_PATH
    if root is None:
        raise EnvironmentError(
            "OBSIDIAN_VAULT_PATH env var is required when vault_path is not passed"
        )

    # Note filename uses " — " (space + em-dash U+2014 + space)
    note_path = root / "04 - Municipalities" / f"{municipality} \u2014 Programs & Incentives.md"

    if not note_path.exists():
        return {
            "status": "programs_blocked",
            "municipality": municipality,
            "parcel_apn": parcel_apn,
            "reason": "vault_note_not_found",
        }

    content = note_path.read_text(encoding="utf-8")

    programs: list[dict[str, Any]] = []

    # ── Table 1: ## Active Incentive Programs ─────────────────────────
    active_section = _find_section(content, "## Active Incentive Programs")
    if active_section is not None:
        for cells in _parse_table_rows(active_section):
            prog = _row_to_active_program(cells)
            if prog is not None:
                programs.append(prog)

    # ── Table 2: ## Consumer Subsidies (D2C-relevant) ─────────────────
    consumer_section = _find_section(content, "## Consumer Subsidies (D2C-relevant)")
    if consumer_section is not None:
        for cells in _parse_table_rows(consumer_section):
            prog = _row_to_consumer_program(cells)
            if prog is not None:
                programs.append(prog)

    if not programs:
        return {
            "status": "programs_blocked",
            "municipality": municipality,
            "parcel_apn": parcel_apn,
            "reason": "programs_table_not_found",
        }

    # Build human-readable rationale explaining M2 constraints
    program_names = ", ".join(p["name"] for p in programs)
    rationale = (
        f"Found {len(programs)} active incentive program(s) in {municipality}: "
        f"{program_names}. "
        "Geographic boundary matching (Renaissance Zone, LDFA districts) is deferred to "
        "Milestone 3 — applies_to_parcel is False for all programs in M2. "
        "Orchestrator will display the full list but no programs contribute to "
        "net_incentive_delta until Milestone 3 adds parcel geometry and boundary matching."
    )

    return {
        "status": "ok",
        "municipality": municipality,
        "applicable_programs": programs,
        "net_incentive_delta": 0.0,
        "rationale": rationale,
    }
