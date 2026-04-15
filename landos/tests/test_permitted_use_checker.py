"""Tests for the M2-4 permitted_use_checker agent and its MCP handler.

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

from src.agents.permitted_use_checker import check_permitted_use
from src.models.opportunity import UseCheckResult


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

Sec. 406.1 intent: one-family residential use.
Sec. 1101: modular compatibility standards (min 24 ft width, ≤3:1 ratio, perimeter foundation).
"""

NOTE_WITHOUT_R5 = """\
---
municipality: "Ypsilanti Township"
---

# Ypsilanti Charter Township

## Some other section

No R-5 district here.
"""


def _write_note(vault_root: Path, municipality: str, content: str) -> None:
    """Create the note directory and write the vault note file."""
    muni_dir = vault_root / "04 - Municipalities"
    muni_dir.mkdir(parents=True, exist_ok=True)
    (muni_dir / f"{municipality}.md").write_text(content, encoding="utf-8")


# ── Test 1: R-5 one_family_residential — by-right ────────────────────

def test_r5_one_family_by_right(tmp_path: Path) -> None:
    """R-5 + one_family_residential → status=ok, allowed=True, path=by-right, citation has Sec. 1101."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = check_permitted_use(
        model_type="one_family_residential",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    r = result["result"]
    assert r["allowed"] is True
    assert r["path"] == "by-right"
    assert "Sec. 1101" in r["citation"]


# ── Test 2: R-5 two_family_residential — denied ───────────────────────

def test_r5_two_family_denied(tmp_path: Path) -> None:
    """R-5 + two_family_residential → status=ok, allowed=False, path=denied."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = check_permitted_use(
        model_type="two_family_residential",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    r = result["result"]
    assert r["allowed"] is False
    assert r["path"] == "denied"


# ── Test 3: R-5 multi_family — denied ────────────────────────────────

def test_r5_multi_family_denied(tmp_path: Path) -> None:
    """R-5 + multi_family → status=ok, allowed=False, path=denied."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = check_permitted_use(
        model_type="multi_family",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    r = result["result"]
    assert r["allowed"] is False
    assert r["path"] == "denied"


# ── Test 4: R-5 manufactured_home_community — denied ─────────────────

def test_r5_mhc_denied(tmp_path: Path) -> None:
    """R-5 + manufactured_home_community → status=ok, allowed=False, path=denied."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = check_permitted_use(
        model_type="manufactured_home_community",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    r = result["result"]
    assert r["allowed"] is False
    assert r["path"] == "denied"


# ── Test 5: R-5 unknown use type → use_blocked ───────────────────────

def test_r5_unknown_use_blocked(tmp_path: Path) -> None:
    """R-5 + commercial_retail → status=use_blocked, reason=use_not_deterministic."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = check_permitted_use(
        model_type="commercial_retail",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "use_blocked"
    assert result["reason"] == "use_not_deterministic"
    assert result["model_type"] == "commercial_retail"


# ── Test 6: missing vault note ────────────────────────────────────────

def test_missing_vault_note(tmp_path: Path) -> None:
    """Missing vault note → status=use_blocked, reason=vault_note_not_found."""
    result = check_permitted_use(
        model_type="one_family_residential",
        district_code="R-5",
        municipality="Nonexistent Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "use_blocked"
    assert result["reason"] == "vault_note_not_found"
    assert result["municipality"] == "Nonexistent Township"
    assert result["district_code"] == "R-5"


# ── Test 7: district not in note ─────────────────────────────────────

def test_district_not_in_note(tmp_path: Path) -> None:
    """Note exists but has no R-5 section → status=use_blocked, reason=district_not_in_note."""
    _write_note(tmp_path, "Ypsilanti Township", NOTE_WITHOUT_R5)

    result = check_permitted_use(
        model_type="one_family_residential",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "use_blocked"
    assert result["reason"] == "district_not_in_note"


# ── Test 8: UseCheckResult round-trip ────────────────────────────────

def test_use_check_result_shape(tmp_path: Path) -> None:
    """R-5 + one_family_residential result dict can be deserialized into UseCheckResult."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    result = check_permitted_use(
        model_type="one_family_residential",
        district_code="R-5",
        municipality="Ypsilanti Township",
        state="MI",
        vault_path=tmp_path,
    )

    assert result["status"] == "ok"
    # This will raise ValidationError if the shape is wrong
    ucr = UseCheckResult(**result["result"])
    assert ucr.allowed is True
    assert ucr.path == "by-right"


# ── Test 9: MCP handler — ok path ────────────────────────────────────

def test_handle_permitted_use_checker_ok(tmp_path: Path) -> None:
    """handle_permitted_use_checker returns isError=False and 'ok' in payload."""
    _write_note(tmp_path, "Ypsilanti Township", R5_NOTE_CONTENT)

    from src.mcp.handlers import MeshState, handle_permitted_use_checker
    import src.agents.permitted_use_checker as _agent_mod

    mesh = MeshState()
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_permitted_use_checker(
                mesh,
                model_type="one_family_residential",
                district_code="R-5",
                municipality="Ypsilanti Township",
                state="MI",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "ok"


# ── Test 10: MCP handler — blocked path ──────────────────────────────

def test_handle_permitted_use_checker_blocked(tmp_path: Path) -> None:
    """handle_permitted_use_checker returns isError=False (not True) for use_blocked.

    A blocked result is NOT an error — it is a pipeline signal telling the
    /loop worker to trigger ingest-municipality or flag the use case.
    """
    from src.mcp.handlers import MeshState, handle_permitted_use_checker
    import src.agents.permitted_use_checker as _agent_mod

    mesh = MeshState()
    # tmp_path has no vault note
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_permitted_use_checker(
                mesh,
                model_type="one_family_residential",
                district_code="R-5",
                municipality="Nonexistent Township",
                state="MI",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "use_blocked"
    assert "use_blocked" in response["content"][0]["text"]
