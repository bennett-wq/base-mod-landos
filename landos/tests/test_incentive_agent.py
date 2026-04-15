"""Tests for the M2-6 incentive_agent and its MCP handler.

All filesystem tests use pytest's tmp_path fixture — no mocking.
MCP handler tests patch VAULT_PATH in the agent module to redirect reads.
Async handlers are exercised via asyncio.run() to avoid a pytest-asyncio dependency.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.incentive_agent import research_incentives
from src.models.opportunity import Program


# ── Vault note fixture helpers ────────────────────────────────────────

# Separator used in vault note filenames: space + em-dash (U+2014) + space
_EM = "\u2014"


def _write_note(vault_root: Path, municipality: str, content: str) -> None:
    """Create the 04 - Municipalities directory and write the Programs & Incentives note."""
    muni_dir = vault_root / "04 - Municipalities"
    muni_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{municipality} {_EM} Programs & Incentives.md"
    (muni_dir / filename).write_text(content, encoding="utf-8")


# ── Canonical note content fragments ─────────────────────────────────

_RENAISSANCE_ROW = (
    "| **Ypsilanti Township Renaissance Zone** "
    "| Renaissance Zone (PA 376 of 1996) \u2014 eliminates most state and local taxes "
    "| Removes **$27,803,144** of taxable value township-wide "
    "| TBD \u2014 pre-dates 12-month scan window "
    "| TBD \u2014 Renaissance Zones typically run 15 years with possible extensions "
    "| **Highest-tier MI tax incentive.** Designated boundary needed before pitching. "
    "Stackable with brownfield TIF and CDBG. "
    "| [[2025-08-25-Township-Board]] (TV impact figure), [[2025-12-02-Township-Board]] |"
)

_CDBG_ROW = (
    "| **Washtenaw County CDBG (Community Development Block Grant) pass-through** "
    "| Variable. Confirmed allocations: $23,400 ... "
    "| CDBG eligibility \u2014 typically LMI (low-to-moderate-income) census tracts. "
    "Ypsi Twp has multiple LMI tracts. "
    "| Township applies to Washtenaw County for project-based reimbursement. ... "
    "| HUD CDBG \u2192 Washtenaw County \u2192 Ypsilanti Township (pass-through) "
    "| [[2025-06-17-Township-Board]], [[2025-08-19-Township-Board]], ... |"
)

ACTIVE_TABLE_HEADER = """\
## Active Incentive Programs

| Program | Authority type | Scope | Authorized | Expires | Stacking notes | Source |
|---|---|---|---|---|---|---|
"""

CONSUMER_TABLE_HEADER = """\
## Consumer Subsidies (D2C-relevant)

| Program | Amount / benefit | Eligibility gates | Application path | Funding source | Source |
|---|---|---|---|---|---|
"""

NOTE_ACTIVE_ONLY = ACTIVE_TABLE_HEADER + _RENAISSANCE_ROW + "\n"

NOTE_BOTH_TABLES = (
    ACTIVE_TABLE_HEADER
    + _RENAISSANCE_ROW
    + "\n\n"
    + CONSUMER_TABLE_HEADER
    + _CDBG_ROW
    + "\n"
)

NOTE_NO_TABLES = """\
# Ypsilanti Charter Township \u2014 Programs & Incentives

Some content with no programs tables.

## Scan summary

Nothing here either.
"""


# ── Test 1: parse Active Incentive Programs table ─────────────────────

def test_research_incentives_parses_active_programs_table(tmp_path: Path) -> None:
    """Minimal note with one Active Incentive Programs row is parsed correctly."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_ACTIVE_ONLY)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    programs = result["applicable_programs"]
    assert len(programs) == 1

    p = programs[0]
    assert "Renaissance Zone" in p["name"]
    assert p["authority_type"].startswith("Renaissance Zone")
    assert "2025-08-25-Township-Board" in p["source_citation"]


# ── Test 2: parse both tables ─────────────────────────────────────────

def test_research_incentives_parses_both_tables(tmp_path: Path) -> None:
    """Note with both Active Incentive Programs and Consumer Subsidies tables yields 2 programs."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_BOTH_TABLES)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    programs = result["applicable_programs"]
    assert len(programs) == 2

    # Both must round-trip into valid Program Pydantic instances
    for raw in programs:
        p = Program(**raw)
        assert isinstance(p, Program)

    names = [p["name"] for p in programs]
    assert any("Renaissance Zone" in n for n in names)
    assert any("CDBG" in n for n in names)


# ── Test 3: applies_to_parcel always False in M2 ─────────────────────

def test_research_incentives_applies_to_parcel_always_false_in_m2(tmp_path: Path) -> None:
    """Every returned program has applies_to_parcel=False, value_to_deal=0.0, net_incentive_delta=0.0."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_BOTH_TABLES)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    assert result["net_incentive_delta"] == 0.0
    for p in result["applicable_programs"]:
        assert p["applies_to_parcel"] is False
        assert p["value_to_deal"] == 0.0


# ── Test 4: missing vault note ────────────────────────────────────────

def test_research_incentives_missing_note(tmp_path: Path) -> None:
    """tmp_path with no vault note returns programs_blocked with vault_note_not_found."""
    result = research_incentives(
        state="MI",
        municipality="Nonexistent Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "programs_blocked"
    assert result["reason"] == "vault_note_not_found"
    assert result["municipality"] == "Nonexistent Township"


# ── Test 5: note exists but no programs tables ────────────────────────

def test_research_incentives_note_without_programs_table(tmp_path: Path) -> None:
    """Note exists but has no Active Incentive Programs or Consumer Subsidies sections."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_NO_TABLES)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "programs_blocked"
    assert result["reason"] == "programs_table_not_found"


# ── Test 6: single program model round-trip ───────────────────────────

def test_research_incentives_program_model_round_trip(tmp_path: Path) -> None:
    """The first returned program dict can be deserialized into Program without ValidationError."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_ACTIVE_ONLY)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    assert len(result["applicable_programs"]) >= 1

    p = Program(**result["applicable_programs"][0])
    assert isinstance(p, Program)
    assert p.applies_to_parcel is False
    assert p.value_to_deal == 0.0


# ── Test 7: full Pydantic round-trip (Finding #8 guard) ───────────────

def test_research_incentives_full_pydantic_round_trip(tmp_path: Path) -> None:
    """All programs round-trip into Program instances and net_incentive_delta is a float.

    This is the Finding #8 guard test — catches shape mismatches before M2-10
    depends on this agent. Keys MUST be applicable_programs and net_incentive_delta.
    """
    _write_note(tmp_path, "Ypsilanti Township", NOTE_BOTH_TABLES)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"

    # Finding #8: exact key names required by OpportunityUnderwriting
    programs = [Program(**p) for p in result["applicable_programs"]]
    assert all(isinstance(p, Program) for p in programs)

    delta = float(result["net_incentive_delta"])
    assert isinstance(delta, float)


# ── Test 8: rationale mentions Milestone 3 deferral ──────────────────

def test_research_incentives_rationale_mentions_m3_deferral(tmp_path: Path) -> None:
    """Rationale string explains why applies_to_parcel is False (geographic deferral)."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_ACTIVE_ONLY)

    result = research_incentives(
        state="MI",
        municipality="Ypsilanti Township",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    rationale = result["rationale"]
    assert any(
        keyword in rationale
        for keyword in ("Milestone 3", "boundary", "geographic")
    ), f"Rationale did not mention deferral context: {rationale!r}"


# ── Test 9: MCP handler — ok path ────────────────────────────────────

def test_handle_incentive_agent_ok(tmp_path: Path) -> None:
    """handle_incentive_agent returns isError=False and status='ok' for a populated note."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_ACTIVE_ONLY)

    from src.mcp.handlers import MeshState, handle_incentive_agent
    import src.agents.incentive_agent as _agent_mod

    mesh = MeshState()
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_incentive_agent(
                mesh,
                state="MI",
                municipality="Ypsilanti Township",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "ok"


# ── Test 10: MCP handler — blocked path is NOT an error ───────────────

def test_handle_incentive_agent_blocked(tmp_path: Path) -> None:
    """handle_incentive_agent returns isError=False (NOT True) for programs_blocked.

    A blocked result is NOT an error — it is a pipeline signal telling the
    /loop worker to trigger ingest-municipality via Codex.
    """
    from src.mcp.handlers import MeshState, handle_incentive_agent
    import src.agents.incentive_agent as _agent_mod

    mesh = MeshState()
    # tmp_path has no vault note
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_incentive_agent(
                mesh,
                state="MI",
                municipality="Nonexistent Township",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "programs_blocked"


# ── Test 11: MCP handler — EnvironmentError guard (Finding #2) ────────

def test_handle_incentive_agent_env_error(tmp_path: Path) -> None:
    """handle_incentive_agent returns isError=True when VAULT_PATH is None.

    This is the Finding #2 guard — EnvironmentError must be caught at the
    handler boundary and returned as _err(), not leaked through the MCP layer.
    """
    from src.mcp.handlers import MeshState, handle_incentive_agent
    import src.agents.incentive_agent as _agent_mod

    mesh = MeshState()
    # Patch VAULT_PATH to None to trigger EnvironmentError in research_incentives
    with patch.object(_agent_mod, "VAULT_PATH", None):
        response = asyncio.run(
            handle_incentive_agent(
                mesh,
                state="MI",
                municipality="Ypsilanti Township",
            )
        )

    assert response["isError"] is True
    error_text = response["content"][0]["text"]
    assert "OBSIDIAN_VAULT_PATH" in error_text
