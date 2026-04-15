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
    """When applicable_programs is empty, surface 'incentive_list_empty' gap.

    Reports what we observed (empty list), not what we inferred. The OU
    model does not distinguish "incentive_agent ran and found zero" from
    "incentive_agent was never invoked" — that provenance layer is M3
    backlog. Softer wording keeps the factual claim honest.
    """
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
    # New key reports an observed state, not an inferred claim.
    assert "incentive_list_empty" in result["gaps_flagged"]
    # Old key must be gone entirely — it asserted a claim we cannot prove.
    assert "no_incentives_checked" not in result["gaps_flagged"]

    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    assert "> [!warning]" in offer_text
    assert "REVIEW BEFORE SENDING" in offer_text
    assert "incentive_list_empty" in offer_text
    # Softer wording that names the two possibilities instead of asserting
    # one of them.
    assert "empty list" in offer_text
    assert "no_incentives_checked" not in offer_text


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


# ── Test 14: cover-email filename matches spec §4.5 line 313 ───────────

def test_outreach_drafter_cover_email_filename_matches_spec(tmp_path: Path) -> None:
    """The cover email file on disk must end with ``-email-to-agent.md``.

    Spec §4.5 line 313 pins the filename to
    ``04 - Developments/_drafts/<parcel>-email-to-agent.md``. This test is
    cheap insurance against future drift (the implementer previously renamed
    this to ``-cover-note.md`` as a defensive measure against the CI grep
    guard, which was unnecessary — the literal ``email-to-agent.md`` does not
    trip any of the seven forbidden patterns enforced by test 10).
    """
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO, base_land_price=20000.0)
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    body_path = Path(result["email_body_path"])
    assert body_path.name.endswith("-email-to-agent.md"), (
        f"Cover email filename {body_path.name!r} does not match spec §4.5 "
        "line 313 — expected `<parcel>-email-to-agent.md`."
    )
    assert body_path.exists()
    assert body_path.parent == _drafts_dir(tmp_path)


# ── Test 15: cover email never emits "a The <model>" article collision ──

def test_outreach_drafter_cover_email_no_article_collision(tmp_path: Path) -> None:
    """Fitting-model names beginning with "The " must not render as "a The ...".

    Regression test for the code-review finding: fitting_models[0].model_name
    of "The Jaxon" previously produced the ungrammatical
    `"for a The Jaxon build on this parcel"` in the cover email. The fix
    strips a leading "The " before the name is interpolated after the
    indefinite article.
    """
    from src.agents.outreach_drafter import draft_outreach

    jaxon_model_id = uuid4()
    uw = _make_full_underwriting(
        verdict=Verdict.GO,
        base_land_price=20000.0,
        fitting_model_id=jaxon_model_id,
        fitting_models=[
            ModelFit(
                model_id=jaxon_model_id,
                model_name="The Jaxon",
                fits=True,
                reason="fits buildable envelope",
            )
        ],
    )
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    body_text = Path(result["email_body_path"]).read_text(encoding="utf-8")

    # Hard-check that none of the article-collision permutations slipped
    # through. "a The " is the literal bug; the lowercase and capitalized
    # variants guard against future formatting drift.
    assert "a The " not in body_text, (
        "Cover email rendered 'a The <model>' article collision — "
        "_strip_leading_article helper is not wired up."
    )
    assert "a the " not in body_text
    assert "A The " not in body_text

    # Positive assertion: the stripped form should be present.
    assert "a Jaxon build" in body_text


# ── Test 16: offer letter wraps rationale bullets in an H2 heading ─────

def test_outreach_drafter_offer_letter_has_rationale_heading(tmp_path: Path) -> None:
    """Non-empty rationale_bullets must be preceded by `## Underwriting rationale`.

    Regression test: the market-justification bullets and the rationale
    bullets previously rendered as two unlabeled lists running together.
    The reader needs an H2 separator so the two bullet blocks don't collide
    in Obsidian's rendered view.
    """
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(
        verdict=Verdict.GO,
        rationale_bullets=[
            "14 years of failed listings across the package.",
            "22 months of land inventory in 48198 — deep buyer's market.",
        ],
    )
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    assert "## Underwriting rationale" in offer_text


# ── Test 17: empty rationale_bullets omits the rationale heading ───────

def test_outreach_drafter_offer_letter_omits_rationale_heading_when_empty(
    tmp_path: Path,
) -> None:
    """Empty rationale_bullets must NOT produce an empty `## Underwriting rationale`
    stub in the offer letter.
    """
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO, rationale_bullets=[])
    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )

    assert result["status"] == "drafted"
    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    assert "## Underwriting rationale" not in offer_text


# ── Test 18: handler returns _err on a malformed underwriting payload ──

def test_handle_outreach_drafter_mcp_handler_validation_error_returns_err(
    tmp_path: Path,
) -> None:
    """Malformed OpportunityUnderwriting dict produces _err, not a raise.

    Regression test: previously the handler only caught EnvironmentError, so
    any pydantic ValidationError on malformed MCP input propagated out of
    the handler and broke the MCP contract
    (all tool responses must be `{"content": [...], "isError": bool}`).
    """
    from src.mcp.handlers import MeshState, handle_outreach_drafter
    import src.agents.outreach_drafter as _agent_mod

    mesh = MeshState()
    # Deliberately missing nearly every required field so pydantic raises.
    malformed = {"verdict": "GO"}

    with patch.object(_agent_mod, "VAULT_PATH", tmp_path):
        response = asyncio.run(
            handle_outreach_drafter(
                mesh,
                underwriting=malformed,
                listing_agent=_listing_agent_full(),
            )
        )

    assert response["isError"] is True
    error_text = response["content"][0]["text"]
    assert "Invalid underwriting payload" in error_text


# ── Test 19: atomic tmp+rename cleans up both tmps on any write failure ──

def test_outreach_drafter_rolls_back_offer_letter_on_cover_email_write_failure(
    tmp_path: Path,
) -> None:
    """If either tmp write fails, neither final draft file may exist and
    neither tmp file may be left behind.

    Mid-write failures are a real production concern on NFS / iCloud-synced
    vaults. The drafter writes to sibling .tmp files first, then promotes
    them atomically via os.replace. A transient I/O error on the second
    tmp write must leave the drafts dir in a clean state — no final pair,
    no stale tmps.
    """
    import pathlib

    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO, base_land_price=20000.0)

    # Patch Path.write_text at the class level. The offer-letter tmp write
    # (call 1) succeeds; the cover-email tmp write (call 2) raises. We let
    # call 1 land on disk so we can verify the cleanup branch actually
    # unlinks the first tmp rather than leaving it behind.
    original_write_text = pathlib.Path.write_text
    call_count = {"n": 0}

    def fake_write_text(self: pathlib.Path, *args: Any, **kwargs: Any) -> int:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return original_write_text(self, *args, **kwargs)
        raise OSError("test disk full")

    with patch.object(pathlib.Path, "write_text", fake_write_text):
        with pytest.raises(OSError, match="test disk full"):
            draft_outreach(
                underwriting=uw,
                listing_agent=_listing_agent_full(),
                vault_path=tmp_path,
            )

    drafts_dir = _drafts_dir(tmp_path)
    remaining = list(drafts_dir.iterdir()) if drafts_dir.exists() else []

    # Neither final file exists (no os.replace ran), and neither tmp
    # file is left behind (cleanup branch unlinked both).
    parcel_slug = str(uw.parcel_id)
    offer_final = drafts_dir / f"{parcel_slug}-offer-letter.md"
    cover_final = drafts_dir / f"{parcel_slug}-email-to-agent.md"
    offer_tmp = drafts_dir / f"{parcel_slug}-offer-letter.md.tmp"
    cover_tmp = drafts_dir / f"{parcel_slug}-email-to-agent.md.tmp"

    assert not offer_final.exists(), "Final offer letter must not exist after failure"
    assert not cover_final.exists(), "Final cover email must not exist after failure"
    assert not offer_tmp.exists(), "Offer-letter tmp must be cleaned up after failure"
    assert not cover_tmp.exists(), "Cover-email tmp must be cleaned up after failure"
    assert remaining == [], (
        f"drafts dir is not clean after failed write: {remaining!r}"
    )


# ── Test 20: tmp+rename pattern is actually used (concurrency invariant) ──

def test_outreach_drafter_uses_atomic_rename_pattern_for_concurrency_safety(
    tmp_path: Path,
) -> None:
    """The drafter must promote tmp files via os.replace so two concurrent
    callers drafting the same parcel can never observe a mismatched pair.

    This test verifies the code actually goes through the tmp+rename path
    rather than writing directly to the final paths. It monkeypatches
    os.replace inside the agent module and asserts exactly two promotion
    calls — one for each draft file.
    """
    import src.agents.outreach_drafter as _agent_mod
    from src.agents.outreach_drafter import draft_outreach

    uw = _make_full_underwriting(verdict=Verdict.GO, base_land_price=20000.0)

    calls: list[tuple[str, str]] = []
    real_replace = _agent_mod.os.replace

    def fake_replace(src: Any, dst: Any) -> None:
        calls.append((str(src), str(dst)))
        real_replace(src, dst)

    with patch.object(_agent_mod.os, "replace", fake_replace):
        result = draft_outreach(
            underwriting=uw,
            listing_agent=_listing_agent_full(),
            vault_path=tmp_path,
        )

    assert result["status"] == "drafted"
    assert len(calls) == 2, (
        f"Expected exactly 2 os.replace calls (tmp -> final for each draft), "
        f"got {len(calls)}: {calls!r}"
    )
    # Each promotion must go from a .tmp file to a non-.tmp file.
    for src_path, dst_path in calls:
        assert src_path.endswith(".tmp"), (
            f"source path is not a .tmp file: {src_path!r}"
        )
        assert not dst_path.endswith(".tmp"), (
            f"destination path is still a .tmp file: {dst_path!r}"
        )

    # Final pair lands on disk; the tmp files are gone.
    offer_path = Path(result["offer_letter_path"])
    cover_path = Path(result["email_body_path"])
    assert offer_path.exists()
    assert cover_path.exists()
    assert not offer_path.with_suffix(offer_path.suffix + ".tmp").exists()
    assert not cover_path.with_suffix(cover_path.suffix + ".tmp").exists()


# ── Test 21: anchor_comp.ppsf=None must not render as "$0/sf" ──────────

def test_outreach_drafter_handles_none_anchor_ppsf_without_false_zero(
    tmp_path: Path,
) -> None:
    """Comp.ppsf is Optional[float]. Rendering a None ppsf as "$0/sf" in
    either the offer letter or the cover email is a false factual claim
    to the seller's agent — the comp did not close at zero dollars per
    square foot, we simply don't know the per-sf price.

    Regression guard: both render sites must handle None explicitly.
    Land comps legitimately lack sqft, so ppsf=None is a valid data
    state we must display honestly.
    """
    from src.agents.outreach_drafter import draft_outreach

    anchor_no_ppsf = Comp(
        address="1070 Hawthorne Ave, Ypsilanti",
        close_date=date(2026, 2, 9),
        price=230000.0,
        sqft=None,
        ppsf=None,
        year_built=2022,
        distance_mi=2.0,
    )
    uw = _make_full_underwriting(
        verdict=Verdict.GO,
        base_land_price=20000.0,
        anchor_comp=anchor_no_ppsf,
    )

    result = draft_outreach(
        underwriting=uw,
        listing_agent=_listing_agent_full(),
        vault_path=tmp_path,
    )
    assert result["status"] == "drafted"

    offer_text = Path(result["offer_letter_path"]).read_text(encoding="utf-8")
    cover_text = Path(result["email_body_path"]).read_text(encoding="utf-8")

    # Hard guard: the false "$0/sf" string must not appear anywhere.
    assert "$0/sf" not in offer_text, (
        "Offer letter rendered a false '$0/sf' claim when ppsf is None"
    )
    assert "$0/sf" not in cover_text, (
        "Cover email rendered a false '$0/sf' claim when ppsf is None"
    )

    # Offer letter still says "unknown" so the reviewer can spot the gap.
    assert "unknown" in offer_text, (
        "Offer letter should surface 'unknown' when anchor ppsf is missing"
    )

    # Cover email drops the $/sf clause entirely but still cites the
    # anchor address and the exit figure.
    assert "1070 Hawthorne Ave" in cover_text
    assert "$234,240" in cover_text or "$234,240." in cover_text or "234,240" in cover_text


# ── Test 22: handler rejects non-dict listing_agent at the MCP boundary ──

@pytest.mark.parametrize(
    "bad_listing_agent",
    [
        [],
        "not a dict",
        None,
        42,
    ],
)
def test_handle_outreach_drafter_rejects_non_dict_listing_agent(
    tmp_path: Path,
    bad_listing_agent: Any,
) -> None:
    """listing_agent must be a dict; anything else returns _err, never raises.

    Regression test: the drafter calls .get() on listing_agent, so passing
    a list, None, a string, or a number would escape as an uncaught
    AttributeError and break the MCP contract (tool responses must be
    `{"content": [...], "isError": bool}`). The handler now type-checks
    at the boundary and returns a clean _err.
    """
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
                listing_agent=bad_listing_agent,
            )
        )

    assert response["isError"] is True
    error_text = response["content"][0]["text"]
    assert "listing_agent" in error_text
    assert "dict" in error_text
