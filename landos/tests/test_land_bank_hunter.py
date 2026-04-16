"""Tests for the M2-9 land_bank_hunter agent and MCP handler.

Coverage areas:
  - Agent output-shape stability across all return paths (Finding #3)
  - Each stub adapter returns expected parcels for its county
  - Querying a state/county with no configured source returns no_source_configured
  - County name appears in the no_source_configured reason
  - Multiple sources for the same county are all queried (Washtenaw)
  - Parcel dict shape is consistent (every parcel has all expected keys)
  - Handler catches EnvironmentError → _err (Finding #2)
  - Handler registered in HANDLER_MAP
  - Handler happy path returns _ok envelope
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import patch

import pytest

from src.agents.land_bank_hunter import _OUTPUT_KEYS, _PARCEL_KEYS


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _run(coro):
    """Run a coroutine synchronously in tests."""
    return asyncio.run(coro)


# ─────────────────────────────────────────────────────────────────────────────
# Output-shape stability — parametrized across ALL return paths (Finding #3)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "state,county,expected_status",
    [
        # ok — Genesee stub returns parcels
        ("MI", "Genesee", "ok"),
        # ok — Wayne stub returns parcels
        ("MI", "Wayne", "ok"),
        # ok — Washtenaw stub returns parcels
        ("MI", "Washtenaw", "ok"),
        # no_source_configured — unknown county
        ("MI", "Kalamazoo", "no_source_configured"),
        # no_source_configured — unknown state
        ("TX", "Travis", "no_source_configured"),
    ],
)
def test_land_bank_hunter_output_shape_is_stable(
    state: str, county: str, expected_status: str
) -> None:
    """Finding #3: every return path emits exactly _OUTPUT_KEYS.

    This is the contract with the M2-10 orchestrator. Changing any key here
    is a coordinated change with that task.
    """
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state=state, county=county)

    assert set(result.keys()) == _OUTPUT_KEYS, (
        f"Key mismatch for ({state}, {county}): "
        f"got {set(result.keys())}, expected {_OUTPUT_KEYS}"
    )
    assert result["status"] == expected_status
    # State and county are always echoed back.
    assert result["state"] == state
    assert result["county"] == county
    # discovered_parcels is always a list (never None).
    assert isinstance(result["discovered_parcels"], list)
    # sources_queried is always a list (never None).
    assert isinstance(result["sources_queried"], list)


def test_land_bank_hunter_output_shape_error_path() -> None:
    """Error path (EnvironmentError from adapter) also emits _OUTPUT_KEYS.

    We inject an adapter that raises EnvironmentError — the handler catches
    it, but if the agent itself were to catch it and return a dict (future
    pattern), the shape must stay stable. This test verifies the agent
    PROPAGATES the error (i.e. does NOT silently swallow it), which is
    the correct behavior per Finding #2.
    """
    import src.agents.land_bank_hunter as agent_mod
    from src.agents.land_bank_hunter import LandBankSource

    original_sources = agent_mod._LAND_BANK_SOURCES.copy()
    try:
        def _raising_adapter():
            raise EnvironmentError("LAND_BANK_CREDENTIAL unset")

        agent_mod._LAND_BANK_SOURCES[("test", "raising")] = [
            LandBankSource(
                name="Raising Test Source",
                source_type="land_bank",
                county="Raising",
                state="TEST",
                adapter=_raising_adapter,
            )
        ]

        with pytest.raises(EnvironmentError, match="LAND_BANK_CREDENTIAL"):
            agent_mod.hunt_land_banks(state="TEST", county="Raising")
    finally:
        agent_mod._LAND_BANK_SOURCES.clear()
        agent_mod._LAND_BANK_SOURCES.update(original_sources)


# ─────────────────────────────────────────────────────────────────────────────
# Stub adapter correctness
# ─────────────────────────────────────────────────────────────────────────────


def test_genesee_stub_returns_expected_parcels() -> None:
    """Genesee County Land Bank stub returns 2 side-lot-fee parcels in Flint."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Genesee")

    assert result["status"] == "ok"
    parcels = result["discovered_parcels"]
    assert len(parcels) == 2

    apns = {p["parcel_number"] for p in parcels}
    assert "10-35-576-028" in apns
    assert "10-30-405-012" in apns

    for p in parcels:
        assert p["source"] == "Genesee County Land Bank"
        assert p["source_type"] == "land_bank"
        assert p["price_type"] == "side_lot_fee"
        assert p["auction_date"] is None
        assert p["municipality"] == "Flint"

    prices = {p["parcel_number"]: p["price"] for p in parcels}
    assert prices["10-35-576-028"] == 500.0
    assert prices["10-30-405-012"] == 1000.0


def test_wayne_stub_returns_expected_parcels() -> None:
    """Wayne County Land Bank stub returns 2 auction-minimum parcels in Detroit."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Wayne")

    assert result["status"] == "ok"
    parcels = result["discovered_parcels"]
    assert len(parcels) == 2

    apns = {p["parcel_number"] for p in parcels}
    assert "44001050632000" in apns
    assert "44001050633000" in apns

    for p in parcels:
        assert p["source"] == "Wayne County Land Bank"
        assert p["source_type"] == "land_bank"
        assert p["price_type"] == "auction_minimum"
        assert p["auction_date"] == "2026-06-15"
        assert p["municipality"] == "Detroit"

    prices = {p["parcel_number"]: p["price"] for p in parcels}
    assert prices["44001050632000"] == 1000.0
    assert prices["44001050633000"] == 1500.0


def test_washtenaw_stub_returns_expected_parcels() -> None:
    """Washtenaw County tax-foreclosure stub returns 2 auction parcels in Ypsilanti Twp."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Washtenaw")

    assert result["status"] == "ok"
    parcels = result["discovered_parcels"]
    assert len(parcels) == 2

    apns = {p["parcel_number"] for p in parcels}
    assert "J-11-09-300-021" in apns
    assert "J-11-09-300-022" in apns

    for p in parcels:
        assert p["source"] == "Washtenaw County Tax Foreclosure"
        assert p["source_type"] == "tax_foreclosure"
        assert p["price_type"] == "auction_minimum"
        assert p["auction_date"] == "2026-09-01"
        assert p["municipality"] == "Ypsilanti Township"

    prices = {p["parcel_number"]: p["price"] for p in parcels}
    assert prices["J-11-09-300-021"] == 3500.0
    assert prices["J-11-09-300-022"] == 2500.0


# ─────────────────────────────────────────────────────────────────────────────
# No-source path
# ─────────────────────────────────────────────────────────────────────────────


def test_no_source_configured_returns_correct_status() -> None:
    """Querying a county with no source returns status=no_source_configured."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Kalamazoo")

    assert result["status"] == "no_source_configured"
    assert result["discovered_parcels"] == []
    assert result["sources_queried"] == []


def test_no_source_configured_includes_county_name_in_reason() -> None:
    """The county name must appear in the reason so the caller knows what's missing."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Kalamazoo")

    assert result["reason"] is not None
    assert "Kalamazoo" in result["reason"]


def test_no_source_unknown_state() -> None:
    """Querying an unknown state also returns no_source_configured."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="TX", county="Travis")

    assert result["status"] == "no_source_configured"
    assert result["reason"] is not None
    assert "Travis" in result["reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Case-insensitive lookup
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "state,county",
    [
        ("mi", "genesee"),
        ("MI", "GENESEE"),
        ("Mi", "Genesee"),
        ("mi", "Genesee"),
    ],
)
def test_registry_lookup_is_case_insensitive(state: str, county: str) -> None:
    """State/county matching must be case-insensitive for caller convenience."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state=state, county=county)
    assert result["status"] == "ok"
    assert len(result["discovered_parcels"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Multiple sources per county
# ─────────────────────────────────────────────────────────────────────────────


def test_all_sources_for_county_are_queried() -> None:
    """When a county has multiple sources configured, ALL are queried.

    This test injects a second source into Washtenaw's registry slot to verify
    the fan-out logic, then restores the original registry.
    """
    import src.agents.land_bank_hunter as agent_mod
    from src.agents.land_bank_hunter import LandBankSource, _parcel

    original_sources = agent_mod._LAND_BANK_SOURCES.copy()
    try:
        second_parcels = [
            _parcel(
                source="Ypsilanti Twp Surplus",
                source_type="municipal_surplus",
                parcel_number="SURPLUS-001",
                address="100 Surplus St, Ypsilanti, MI 48198",
                price=2000.0,
                price_type="surplus_list_price",
                municipality="Ypsilanti Township",
            )
        ]

        agent_mod._LAND_BANK_SOURCES[("mi", "washtenaw")] = [
            *original_sources[("mi", "washtenaw")],
            LandBankSource(
                name="Ypsilanti Twp Surplus",
                source_type="municipal_surplus",
                county="Washtenaw",
                state="MI",
                adapter=lambda: second_parcels,
            ),
        ]

        result = agent_mod.hunt_land_banks(state="MI", county="Washtenaw")

        assert result["status"] == "ok"
        assert len(result["sources_queried"]) == 2
        assert "Washtenaw County Tax Foreclosure" in result["sources_queried"]
        assert "Ypsilanti Twp Surplus" in result["sources_queried"]

        # Parcels from both sources are present.
        sources_in_results = {p["source"] for p in result["discovered_parcels"]}
        assert "Washtenaw County Tax Foreclosure" in sources_in_results
        assert "Ypsilanti Twp Surplus" in sources_in_results
    finally:
        agent_mod._LAND_BANK_SOURCES.clear()
        agent_mod._LAND_BANK_SOURCES.update(original_sources)


# ─────────────────────────────────────────────────────────────────────────────
# Parcel dict shape invariant
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "state,county",
    [
        ("MI", "Genesee"),
        ("MI", "Wayne"),
        ("MI", "Washtenaw"),
    ],
)
def test_parcel_dict_shape_is_consistent(state: str, county: str) -> None:
    """Every parcel from every adapter has exactly _PARCEL_KEYS."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state=state, county=county)
    assert result["status"] == "ok"

    for parcel in result["discovered_parcels"]:
        assert set(parcel.keys()) == _PARCEL_KEYS, (
            f"Parcel key mismatch for {county}: "
            f"got {set(parcel.keys())}, expected {_PARCEL_KEYS}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Sources queried list
# ─────────────────────────────────────────────────────────────────────────────


def test_sources_queried_populated_on_ok() -> None:
    """sources_queried contains the source name(s) on a successful call."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Genesee")
    assert result["sources_queried"] == ["Genesee County Land Bank"]


def test_sources_queried_empty_on_no_source_configured() -> None:
    """sources_queried is empty when no source is configured."""
    from src.agents.land_bank_hunter import hunt_land_banks

    result = hunt_land_banks(state="MI", county="Kalamazoo")
    assert result["sources_queried"] == []


# ─────────────────────────────────────────────────────────────────────────────
# MCP handler tests
# ─────────────────────────────────────────────────────────────────────────────


def test_handler_registered_in_handler_map() -> None:
    """The land_bank_hunter tool is dispatchable via HANDLER_MAP."""
    from src.mcp.handlers import HANDLER_MAP, handle_land_bank_hunter

    assert "land_bank_hunter" in HANDLER_MAP
    assert HANDLER_MAP["land_bank_hunter"] is handle_land_bank_hunter


def test_handler_catches_environmenterror_returns_err() -> None:
    """Finding #2 at the handler layer: missing credential → _err, not raise."""
    import src.agents.land_bank_hunter as agent_mod
    from src.mcp.handlers import MeshState, handle_land_bank_hunter

    def _raising(**kwargs: Any):
        raise EnvironmentError("LAND_BANK_CREDENTIAL is unset.")

    mesh = MeshState()
    with patch.object(agent_mod, "hunt_land_banks", _raising):
        response = _run(
            handle_land_bank_hunter(mesh, state="MI", county="Genesee")
        )

    assert response["isError"] is True
    assert "LAND_BANK_CREDENTIAL" in response["content"][0]["text"]


def test_handler_happy_path_returns_ok_envelope() -> None:
    """End-to-end: handler dispatches to the agent and returns an _ok response."""
    import src.agents.land_bank_hunter as agent_mod
    from src.mcp.handlers import MeshState, handle_land_bank_hunter

    fake_result = {
        "status": "ok",
        "discovered_parcels": [
            {
                "source": "Genesee County Land Bank",
                "source_type": "land_bank",
                "parcel_number": "10-35-576-028",
                "address": "802 Welch Blvd, Flint, MI 48504",
                "price": 500.0,
                "price_type": "side_lot_fee",
                "auction_date": None,
                "acreage": 0.11,
                "zoning": "R-1",
                "municipality": "Flint",
            }
        ],
        "state": "MI",
        "county": "Genesee",
        "sources_queried": ["Genesee County Land Bank"],
        "warning": None,
        "reason": None,
    }

    def _fake_hunt(**kwargs: Any) -> dict[str, Any]:
        return fake_result

    mesh = MeshState()
    with patch.object(agent_mod, "hunt_land_banks", _fake_hunt):
        response = _run(
            handle_land_bank_hunter(mesh, state="MI", county="Genesee")
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "ok"
    assert payload["state"] == "MI"
    assert payload["county"] == "Genesee"
    assert len(payload["discovered_parcels"]) == 1
    assert payload["discovered_parcels"][0]["parcel_number"] == "10-35-576-028"


def test_handler_no_source_configured_returns_ok_envelope() -> None:
    """Handler wraps no_source_configured result in _ok (not an error response)."""
    from src.mcp.handlers import MeshState, handle_land_bank_hunter

    mesh = MeshState()
    response = _run(
        handle_land_bank_hunter(mesh, state="MI", county="Kalamazoo")
    )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "no_source_configured"
    assert payload["discovered_parcels"] == []
    assert "Kalamazoo" in payload["reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Handler boundary validation — non-string state/county (Codex fix)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "state,county",
    [
        (None, "Genesee"),
        ("MI", None),
        (None, None),
        (42, "Genesee"),
        ("MI", 42),
        (["MI"], "Genesee"),
        ("MI", ["Genesee"]),
    ],
)
def test_handler_rejects_non_string_state_or_county(state: Any, county: Any) -> None:
    """Handler must return isError=True when state or county is not a string.

    Without this guard, a None/int/list would reach agent's .strip() call and
    raise AttributeError, leaking a raw exception to the caller (Codex fix).
    """
    from src.mcp.handlers import MeshState, handle_land_bank_hunter

    mesh = MeshState()
    response = _run(
        handle_land_bank_hunter(mesh, state=state, county=county)
    )

    assert response["isError"] is True
    assert "must be a string" in response["content"][0]["text"]


# ─────────────────────────────────────────────────────────────────────────────
# Empty-inventory warning branch (Codex fix)
# ─────────────────────────────────────────────────────────────────────────────


def test_hunt_land_banks_empty_inventory_warning() -> None:
    """Adapter configured but returns [] → status=ok, warning=no_parcels_in_inventory.

    This covers the zero-result gap-surfacing branch in hunt_land_banks, which
    is reachable when a live adapter returns an empty list (M3 scope). In M2
    we inject a stub adapter that returns [] to exercise the branch now.
    """
    import src.agents.land_bank_hunter as agent_mod
    from src.agents.land_bank_hunter import LandBankSource, hunt_land_banks

    original_sources = agent_mod._LAND_BANK_SOURCES.copy()
    try:
        agent_mod._LAND_BANK_SOURCES[("mi", "empty")] = [
            LandBankSource(
                name="Empty Test Source",
                source_type="land_bank",
                county="Empty",
                state="MI",
                adapter=lambda: [],
            )
        ]

        result = hunt_land_banks(state="MI", county="Empty")

        assert result["status"] == "ok"
        assert result["warning"] == "no_parcels_in_inventory"
        assert result["discovered_parcels"] == []
        assert result["sources_queried"] == ["Empty Test Source"]
        assert result["reason"] is None
    finally:
        agent_mod._LAND_BANK_SOURCES.clear()
        agent_mod._LAND_BANK_SOURCES.update(original_sources)
