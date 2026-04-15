"""Tests for the M2-3 zoning_extractor agent and its MCP handler.

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

from src.agents.zoning_extractor import extract_zoning
from src.models.opportunity import SetbackRules


# ── Fixture: minimal R-5 vault note ──────────────────────────────────

R5_NOTE_CONTENT = """\
---
tags:
  - municipality
municipality: "Ypsilanti Township"
county: "Washtenaw"
state: "MI"
---

# Ypsilanti Charter Township

## Residential Zoning Districts (Article 4, Sec. 406)

### R-5 — One-Family Residential (smallest lot district)

| Standard | R-5 Value | Confidence |
|---|---|---|
| Minimum lot area | **5,400 sq ft** | ✅ confirmed |
| Minimum lot width | **50 ft** | ✅ confirmed |
| Maximum lot coverage (all bldgs) | **35%** | ✅ confirmed |
| Minimum front setback | **20 ft** | ✅ confirmed |
| Minimum side setback (least) | **5 ft** | ✅ confirmed |
| Minimum side setback (total both sides) | **16 ft** | ✅ confirmed |
| Minimum rear setback | **35 ft** | ✅ confirmed |
| Maximum height | **2 stories / 25 ft** | ✅ confirmed |
| Minimum ground floor area | **720 sq ft** | ✅ confirmed |

> Pulled from https://library.municode.com/mi/ypsilanti_charter_township/test on 2026-04-15.
"""


def _write_note(vault_root: Path, municipality: str, content: str) -> None:
    """Create the note directory and write the vault note file."""
    muni_dir = vault_root / "04 - Municipalities"
    muni_dir.mkdir(parents=True, exist_ok=True)
    (muni_dir / f"{municipality}.md").write_text(content, encoding="utf-8")


# ── Test 1: success path ──────────────────────────────────────────────

def test_extract_zoning_ypsi_r5(tmp_path: Path) -> None:
    """Parsing the canonical R-5 table returns all 9 setback fields correctly."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = extract_zoning(
        state="MI",
        municipality="Ypsilanti Township",
        district_code="R-5",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    sb = result["setbacks"]

    assert sb["district_code"] == "R-5"
    assert sb["min_lot_sf"] == 5400
    assert sb["min_width_ft"] == 50.0
    assert sb["max_coverage_pct"] == 35.0
    assert sb["max_height_ft"] == 25.0
    assert sb["max_stories"] == 2
    assert sb["front_setback_ft"] == 20.0
    assert sb["side_least_ft"] == 5.0
    assert sb["side_total_ft"] == 16.0
    assert sb["rear_setback_ft"] == 35.0
    assert sb["min_ground_floor_sf"] == 720


# ── Test 2: missing vault note ────────────────────────────────────────

def test_extract_zoning_missing_note(tmp_path: Path) -> None:
    """Missing vault note returns zoning_blocked with vault_note_not_found."""
    result = extract_zoning(
        state="MI",
        municipality="Nonexistent Township",
        district_code="R-5",
        vault_path=tmp_path,
    )

    assert result["status"] == "zoning_blocked"
    assert result["reason"] == "vault_note_not_found"
    assert result["municipality"] == "Nonexistent Township"
    assert result["district_code"] == "R-5"


# ── Test 3: district not in note ──────────────────────────────────────

def test_extract_zoning_district_not_in_note(tmp_path: Path) -> None:
    """Note exists but has no R-5 section → zoning_blocked with district_not_in_note."""
    content = """\
---
municipality: "Blank Township"
---

# Blank Township

## Some other section

No zoning districts here.
"""
    _write_note(tmp_path, "Blank Township", content)

    result = extract_zoning(
        state="MI",
        municipality="Blank Township",
        district_code="R-5",
        vault_path=tmp_path,
    )

    assert result["status"] == "zoning_blocked"
    assert result["reason"] == "district_not_in_note"


# ── Test 4: SetbackRules round-trip ──────────────────────────────────

def test_extract_zoning_returns_setback_rules_shape(tmp_path: Path) -> None:
    """The setbacks dict can be deserialized into SetbackRules without error."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = extract_zoning(
        state="MI",
        municipality="Ypsilanti Township",
        district_code="R-5",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    # This will raise ValidationError if the shape is wrong
    rules = SetbackRules(**result["setbacks"])
    assert rules.district_code == "R-5"
    assert rules.min_lot_sf == 5400


# ── Test 5: MCP handler — ok path ────────────────────────────────────

def test_handle_zoning_extractor_ok(tmp_path: Path) -> None:
    """handle_zoning_extractor returns isError=False and 'ok' in response text."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    from src.mcp.handlers import MeshState, handle_zoning_extractor
    import src.agents.zoning_extractor as _agent_mod

    mesh = MeshState()
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_zoning_extractor(
                mesh,
                state="MI",
                municipality="Ypsilanti Township",
                district_code="R-5",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "ok"


# ── Test 6: MCP handler — blocked path ───────────────────────────────

def test_handle_zoning_extractor_blocked(tmp_path: Path) -> None:
    """handle_zoning_extractor returns isError=False and 'zoning_blocked' for missing note.

    A blocked result is NOT an error — it is a pipeline signal telling the
    /loop worker to trigger ingest-municipality.
    """
    from src.mcp.handlers import MeshState, handle_zoning_extractor
    import src.agents.zoning_extractor as _agent_mod

    mesh = MeshState()
    # tmp_path has no vault note — 04 - Municipalities/ dir doesn't even exist
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_zoning_extractor(
                mesh,
                state="MI",
                municipality="Nonexistent Township",
                district_code="R-5",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "zoning_blocked"
    assert "zoning_blocked" in response["content"][0]["text"]
