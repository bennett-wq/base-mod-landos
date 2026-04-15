"""Tests for the M2-7 outreach_drafter and its MCP handler.

All filesystem tests use pytest's tmp_path fixture — no mocking.
MCP handler tests patch VAULT_PATH in the agent module to redirect vault reads.
Async handlers are exercised via asyncio.run() to avoid a pytest-asyncio dependency.

Hard invariant (spec §4.5): this agent NEVER sends email. The grep guard in
test_outreach_drafter_has_no_email_send_imports enforces that no smtplib,
sendmail, Gmail API, or boto3 SES imports or call sites appear in the agent source.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.models.opportunity import (
    Comp,
    CompAggregates,
    CompConfidence,
    CostBreakdown,
    ExitPrice,
    Margin,
    MarketStats,
    ModelFit,
    OpportunityUnderwriting,
    Program,
    SensitivityMatrix,
    UseCheckResult,
    Verdict,
)


# ── Full OU fixture builder ──────────────────────────────────────────────
#
# Produces a fully-populated OpportunityUnderwriting with realistic McCartney-
# like values. Individual tests override specific fields via kwargs to exercise
# the gap surfacing, verdict branches, and round-trip behavior.

def _make_full_underwriting(**overrides: Any) -> OpportunityUnderwriting:
    """Build a full OpportunityUnderwriting with McCartney-like defaults.

    Fields you'll typically override:
      - verdict
      - negotiate_target_land_price
      - base_land_price
      - applicable_programs
      - market_stats
      - anchor_comp
    """
    fitting_model_id = uuid4()

    defaults: dict[str, Any] = {
        "opportunity_id": uuid4(),
        "parcel_id": uuid4(),
        "package_parcel_ids": [],
        "fitting_model_id": fitting_model_id,
        "computed_at": datetime(2026, 4, 15, 12, 0, 0),
        "engine_version": "0.1.0",
        "zoning_district": "R-5",
        "zoning_source_url": "https://library.municode.com/mi/ypsilanti_charter_township",
        "zoning_pulled_on": date(2026, 4, 15),
        "site_fit_id": uuid4(),
        "permitted_use_result": UseCheckResult(
            allowed=True,
            path="by-right",
            citation="Sec. 406",
            rationale="one-family",
        ),
        "buildable_width_ft": 40.5,
        "buildable_depth_ft": 57.1,
        "envelope_area_sf": 2311.0,
        "coverage_cap_sf": 2206.0,
        "binding_constraint": "depth",
        "fitting_models": [
            ModelFit(
                model_id=fitting_model_id,
                model_name="The Jaxon",
                fits=True,
                reason="fits buildable envelope + Sec. 1101",
            )
        ],
        "comp_set_1_tight_sfr": [],
        "comp_set_1_aggregates": CompAggregates(median_ppsf=183.0, count=3),
        "comp_set_2_broad_sfr": [],
        "comp_set_2_aggregates": {"all": CompAggregates(median_ppsf=175.0, count=46)},
        "comp_set_3_land": [],
        "comp_set_3_aggregates": {"all": CompAggregates(median_ppsf=0.0, count=100)},
        "anchor_comp": Comp(
            address="1070 Hawthorne Ave, Ypsilanti",
            close_date=date(2026, 2, 9),
            price=230000.0,
            sqft=1256,
            ppsf=183.0,
            year_built=2022,
            distance_mi=2.0,
        ),
        "anchor_rationale": "Closest 2022+ build in target band.",
        "market_stats": MarketStats(
            months_of_inventory=22.0,
            median_cdom_days=180,
            p75_cdom_days=240,
            p90_cdom_days=365,
            failed_listings_on_parcel=3,
            years_listed_total=14.0,
            market_health="deep_buyer",
        ),
        "applicable_programs": [
            Program(
                name="Ypsilanti Township Renaissance Zone",
                authority_type="Renaissance Zone (PA 376 of 1996)",
                scope="Removes $27.8M of taxable value township-wide",
                dates_active="TBD -> TBD",
                stacking_notes="Stackable with brownfield TIF and CDBG.",
                applies_to_parcel=False,
                source_citation="2025-08-25-Township-Board",
                value_to_deal=0.0,
            )
        ],
        "net_incentive_delta": 0.0,
        "home_quote": 81645.0,
        "site_cost": 86767.0,
        "contingency_pct": 0.15,
        "contingency_amount": 25262.0,
        "base_land_price": 32500.0,
        "adjusted_cost_breakdown": CostBreakdown(
            home_quote=81645.0,
            site_cost=86767.0,
            contingency_pct=0.15,
            contingency_amount=25261.8,
            base_land_price=32500.0,
            total=226173.8,
        ),
        "total_cost_per_parcel": 226174.0,
        "exit_price": ExitPrice(
            ppsf=183.0,
            total=234240.0,
            confidence=CompConfidence.MEDIUM,
            sqft=1280,
        ),
        "sell_costs_pct": 0.07,
        "margin_base_case": Margin(net=-12274.0, gross=3826.0, net_margin_pct=-5.4),
        "sensitivity_matrix": SensitivityMatrix(rows=[], columns=[], values=[]),
        "verdict": Verdict.GO,
        "negotiate_target_land_price": None,
        "rationale_bullets": [
            "14 years of failed listings across the package.",
            "22 months of land inventory in 48198 — deep buyer's market.",
            "No comps support the $130K ask.",
        ],
        "suggested_offer_terms": "Cash, 30-day close, no inspection contingency.",
    }

    defaults.update(overrides)
    return OpportunityUnderwriting(**defaults)


def _listing_agent_full() -> dict[str, Any]:
    """Full listing-agent dict with every optional field populated."""
    return {
        "agent_name": "Jane Smith",
        "office_name": "ABC Realty",
        "agent_email": "jane@abcrealty.example",
        "agent_phone": "555-0100",
        "listing_id": "54321",
        "listing_address": "1888 McCartney Rd, Ypsilanti",
    }


def _drafts_dir(vault_path: Path) -> Path:
    return vault_path / "04 - Developments" / "_drafts"


# ── Test 1: happy path GO verdict ────────────────────────────────────────

def test_outreach_drafter_happy_path_go_verdict(tmp_path: Path) -> None:
    """GO verdict with a fully-populated underwriting writes both files."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO, base_land_price=20000.0)
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    assert result["verdict"] == "GO"
    assert result["offer_amount"] == 20000.0
    assert result["gaps_flagged"] == []

    offer_path = Path(result["offer_letter_path"])
    body_path = Path(result["email_body_path"])
    assert offer_path.exists()
    assert body_path.exists()
    assert offer_path.parent == _drafts_dir(tmp_path)


# ── Test 2: NEGOTIATE uses negotiate_target_land_price ──────────────────

def test_outreach_drafter_negotiate_verdict_uses_target_land_price(tmp_path: Path) -> None:
    """NEGOTIATE with a target price uses the target, not the asking price."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(
        verdict=Verdict.NEGOTIATE,
        negotiate_target_land_price=20000.0,
        base_land_price=130000.0,
    )
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    assert result["verdict"] == "NEGOTIATE"
    assert result["offer_amount"] == 20000.0


# ── Test 3: NO-GO verdict is skipped, no files written ─────────────────

def test_outreach_drafter_skipped_on_no_go_verdict(tmp_path: Path) -> None:
    """NO-GO verdict is skipped defensively; no files written."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.NO_GO)
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "verdict_not_actionable"
    assert result["verdict"] == "NO-GO"

    drafts_dir = _drafts_dir(tmp_path)
    if drafts_dir.exists():
        assert list(drafts_dir.iterdir()) == []


# ── Test 4: NEGOTIATE with None target falls back to skipped ─────────────

def test_outreach_drafter_negotiate_without_target_price_falls_back(tmp_path: Path) -> None:
    """NEGOTIATE without a target price is skipped defensively."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(
        verdict=Verdict.NEGOTIATE,
        negotiate_target_land_price=None,
    )
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "skipped"
    assert "negotiate_target" in result["reason"].lower()

    drafts_dir = _drafts_dir(tmp_path)
    if drafts_dir.exists():
        assert list(drafts_dir.iterdir()) == []


# ── Test 5: missing OBSIDIAN_VAULT_PATH raises EnvironmentError ──────────

def test_outreach_drafter_missing_vault_env_raises_environment_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no vault_path kwarg and no env var, drafter raises EnvironmentError.

    This is Finding #2 at the agent layer — the handler test covers the
    handler-level catch.
    """
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    import src.agents.outreach_drafter as _agent_mod
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting()
    with patch.object(_agent_mod, "VAULT_PATH", None):
        with pytest.raises(EnvironmentError, match="OBSIDIAN_VAULT_PATH"):
            draft_outreach(
                underwriting=uw,
                listing_agent=_listing_agent_full(),
                vault_path=None,
            )


# ── Test 6: optional listing_agent fields default to placeholders ──────

def test_outreach_drafter_optional_listing_agent_fields_default_to_placeholders(
    tmp_path: Path,
) -> None:
    """Missing optional fields (email, phone, listing_id) use placeholder tokens."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO)
    minimal_agent = {
        "agent_name": "Jane Smith",
        "office_name": "ABC Realty",
    }
    result = draft_outreach(
        underwriting=uw,
        listing_agent=minimal_agent,
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"

    body_path = Path(result["email_body_path"])
    body_text = body_path.read_text(encoding="utf-8")
    assert "[pull from Spark]" in body_text


# ── Test 7: empty applicable_programs is flagged as a gap ─────────────

def test_outreach_drafter_flags_empty_applicable_programs_as_gap(tmp_path: Path) -> None:
    """When applicable_programs is empty, surface 'no_incentives_checked' gap."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(
        verdict=Verdict.GO,
        applicable_programs=[],
    )
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    assert "no_incentives_checked" in result["gaps_flagged"]

    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    assert "> [!warning]" in offer_text
    assert "REVIEW BEFORE SENDING" in offer_text
    assert "no_incentives_checked" in offer_text


# ── Test 8: weak market history is flagged as a gap ────────────────────

def test_outreach_drafter_flags_weak_market_history_as_gap(tmp_path: Path) -> None:
    """Zero failed listings AND zero years_listed_total flags 'no_listing_history'."""
    from src.agents.outreach_drafter import draft_outreach

    weak_market = MarketStats(
        months_of_inventory=22.0,
        median_cdom_days=180,
        p75_cdom_days=240,
        p90_cdom_days=365,
        failed_listings_on_parcel=0,
        years_listed_total=0.0,
        market_health="deep_buyer",
    )
    uw = _make_full_underwriting(verdict=Verdict.GO, market_stats=weak_market)
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    assert "no_listing_history" in result["gaps_flagged"]

    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    assert "> [!warning]" in offer_text
    assert "no_listing_history" in offer_text


# ── Test 9: full Pydantic round-trip (Finding #8 inverted) ──────────────

def test_outreach_drafter_full_pydantic_round_trip(tmp_path: Path) -> None:
    """The drafter CONSUMES a full OpportunityUnderwriting without KeyError/AttributeError.

    Finding #8 inverted: if the agent references a field that doesn't exist
    on the OU model, this test catches it immediately.
    """
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(
        verdict=Verdict.NEGOTIATE,
        negotiate_target_land_price=20000.0,
        base_land_price=130000.0,
    )
    # Confirm the fixture really is a valid OpportunityUnderwriting
    assert isinstance(uw, OpportunityUnderwriting)

    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    assert Path(result["offer_letter_path"]).exists()
    assert Path(result["email_body_path"]).exists()


# ── Test 10: CI grep guard — no email-sending imports or call sites ────

def test_outreach_drafter_has_no_email_send_imports() -> None:
    """Read the agent source and assert no email-sending imports or call sites appear.

    This is the hard CI guard for spec §4.5. NEVER bypass with # noqa.
    """
    agent_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "agents"
        / "outreach_drafter.py"
    )
    assert agent_path.exists(), f"outreach_drafter.py not found at {agent_path}"
    content = agent_path.read_text(encoding="utf-8")
    lower = content.lower()

    assert "send_gmail" not in lower, "Forbidden substring 'send_gmail' found in outreach_drafter.py"
    assert "smtplib" not in lower, "Forbidden substring 'smtplib' found in outreach_drafter.py"
    assert "sendmail" not in lower, "Forbidden substring 'sendmail' found in outreach_drafter.py"
    assert "from email.mime" not in lower, (
        "Forbidden substring 'from email.mime' found in outreach_drafter.py"
    )
    assert "SMTP(" not in content, "Forbidden substring 'SMTP(' found in outreach_drafter.py"

    gmail_post_match = re.search(
        r"requests\.post\s*\(\s*['\"][^'\"]*gmail",
        content,
        re.IGNORECASE,
    )
    assert gmail_post_match is None, (
        f"Forbidden pattern requests.post(...gmail...) found in outreach_drafter.py: "
        f"{gmail_post_match.group(0) if gmail_post_match else ''!r}"
    )

    boto3_ses_match = re.search(r"boto3[^)]*ses", content, re.IGNORECASE)
    assert boto3_ses_match is None, (
        f"Forbidden pattern boto3...ses found in outreach_drafter.py: "
        f"{boto3_ses_match.group(0) if boto3_ses_match else ''!r}"
    )


# ── Test 11: MCP handler happy path ───────────────────────────────────

def test_handle_outreach_drafter_mcp_handler_happy_path(tmp_path: Path) -> None:
    """The MCP handler accepts a dict-serialized OU and returns _ok."""
    from src.mcp.handlers import MeshState, handle_outreach_drafter
    import src.agents.outreach_drafter as _agent_mod

    uw = _make_full_underwriting(verdict=Verdict.GO, base_land_price=20000.0)
    uw_dict = uw.model_dump(mode="json")

    mesh = MeshState()
    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_outreach_drafter(
                mesh,
                underwriting=uw_dict,
                listing_agent=_listing_agent_full(),
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "drafted"
    assert payload["offer_amount"] == 20000.0


# ── Test 12: MCP handler env error (Finding #2) ────────────────────────

def test_handle_outreach_drafter_mcp_handler_env_error_returns_err(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When VAULT_PATH is None, handle_outreach_drafter returns _err, not raises.

    Finding #2 guard: EnvironmentError is caught at the handler boundary and
    surfaced as an MCP error response.
    """
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    from src.mcp.handlers import MeshState, handle_outreach_drafter
    import src.agents.outreach_drafter as _agent_mod

    uw = _make_full_underwriting(verdict=Verdict.GO)
    uw_dict = uw.model_dump(mode="json")

    mesh = MeshState()
    with patch.object(_agent_mod, "VAULT_PATH", None):
        response = asyncio.run(
            handle_outreach_drafter(
                mesh,
                underwriting=uw_dict,
                listing_agent=_listing_agent_full(),
            )
        )

    assert response["isError"] is True
    error_text = response["content"][0]["text"]
    assert "OBSIDIAN_VAULT_PATH" in error_text


# ── Test 13: offer letter contains market facts as digit strings ───────

def test_outreach_drafter_offer_letter_contains_market_facts(tmp_path: Path) -> None:
    """The offer letter interpolates real market stats, not template placeholders."""
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO)
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    assert "22" in offer_text  # months_of_inventory
    assert "180" in offer_text  # median_cdom_days
    assert "14" in offer_text  # years_listed_total
