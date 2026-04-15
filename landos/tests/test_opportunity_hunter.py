"""Tests for the M2-8 opportunity_hunter agent, its Spark client, and MCP handler.

All tests use dependency injection (``_urlopen`` for the client,
``_fetch`` for the agent) so no test touches the real Spark API.

Coverage areas:
  - Client URL construction for each supported scope type
  - Client OData escaping for quoted literals
  - Client EnvironmentError when SPARK_API_KEY is missing
  - Client SparkHTTPError wrapping of urllib errors
  - Agent output-shape stability across all return paths (Finding #8)
  - Agent unsupported_scope_type for "tif" and unknown types
  - Agent zero-results surfacing via warning (Finding #10)
  - Agent success path produces the expected parcel dict shape
  - Agent SparkHTTPError → status="error"
  - Agent invalid scope shape → status="error"
  - Agent EnvironmentError propagation (caught by handler, not agent)
  - Handler EnvironmentError catch (Finding #2)
  - Handler non-dict scope rejection at the boundary
  - Handler registration in HANDLER_MAP
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
from typing import Any
from unittest.mock import patch

import pytest


# ─────────────────────────────────────────────────────────────────────────
# Shared fakes
# ─────────────────────────────────────────────────────────────────────────


class _FakeResp:
    """Minimal context-manager stand-in for http.client.HTTPResponse."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _fake_urlopen_factory(
    captured: dict[str, Any],
    value_payload: list[dict] | None = None,
):
    """Build a _urlopen replacement that records the request and returns a fake body."""

    def _fake_urlopen(req: Any, timeout: int = 60) -> _FakeResp:
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["timeout"] = timeout
        body = json.dumps({"value": value_payload or []}).encode()
        return _FakeResp(body)

    return _fake_urlopen


def _raising_urlopen(exc: Exception):
    """Return a _urlopen substitute that raises ``exc`` on first call."""

    def _raise(req: Any, timeout: int = 60):
        raise exc

    return _raise


# ─────────────────────────────────────────────────────────────────────────
# Client tests
# ─────────────────────────────────────────────────────────────────────────


def test_client_builds_correct_odata_url_for_county() -> None:
    """County scope maps to CountyOrParish and ANDs the Land + Active filters."""
    from src.adapters.spark.client import fetch_active_land_listings

    captured: dict[str, Any] = {}
    fetch_active_land_listings(
        scope_type="county",
        scope_value="Washtenaw",
        api_key="fake-token",
        _urlopen=_fake_urlopen_factory(captured),
    )

    url = captured["url"]
    assert "PropertyType+eq+%27Land%27" in url
    assert "StandardStatus+eq+%27Active%27" in url
    assert "CountyOrParish+eq+%27Washtenaw%27" in url
    assert "%24top=100" in url
    assert "%24orderby=ModificationTimestamp+desc" in url
    # Auth header uses Bearer and the provided token verbatim.
    assert captured["headers"]["Authorization"] == "Bearer fake-token"
    assert captured["headers"]["Accept"] == "application/json"


@pytest.mark.parametrize(
    "scope_type,scope_value,expected_fragment",
    [
        ("township", "Ypsilanti", "City+eq+%27Ypsilanti%27"),
        ("zip", "48197", "PostalCode+eq+%2748197%27"),
    ],
)
def test_client_builds_correct_odata_url_for_township_and_zip(
    scope_type: str, scope_value: str, expected_fragment: str
) -> None:
    """Township → City and zip → PostalCode field mappings."""
    from src.adapters.spark.client import fetch_active_land_listings

    captured: dict[str, Any] = {}
    fetch_active_land_listings(
        scope_type=scope_type,
        scope_value=scope_value,
        api_key="k",
        _urlopen=_fake_urlopen_factory(captured),
    )

    assert expected_fragment in captured["url"]


def test_client_escapes_single_quote_in_scope_value() -> None:
    """Single quotes in the scope value must be doubled per OData spec."""
    from src.adapters.spark.client import fetch_active_land_listings

    captured: dict[str, Any] = {}
    fetch_active_land_listings(
        scope_type="township",  # township maps to the City OData field
        scope_value="O'Brien",
        api_key="k",
        _urlopen=_fake_urlopen_factory(captured),
    )

    # urlencode quotes single quote as %27 and the escaped apostrophe shows
    # as a pair of %27 characters bracketing the letter B.
    assert "City+eq+%27O%27%27Brien%27" in captured["url"]


def test_client_raises_environmenterror_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No api_key= kwarg AND no SPARK_API_KEY env → EnvironmentError."""
    import src.adapters.spark.client as client_mod

    monkeypatch.delenv("SPARK_API_KEY", raising=False)
    with patch.object(client_mod, "_ENV_API_KEY", None):
        with pytest.raises(EnvironmentError, match="SPARK_API_KEY"):
            client_mod.fetch_active_land_listings(
                scope_type="county",
                scope_value="Washtenaw",
                _urlopen=_fake_urlopen_factory({}),
            )


def test_client_rejects_unsupported_scope_type() -> None:
    """ValueError is raised if the scope_type isn't in the mapping."""
    from src.adapters.spark.client import fetch_active_land_listings

    with pytest.raises(ValueError, match="Unsupported scope_type"):
        fetch_active_land_listings(
            scope_type="wardrobe",
            scope_value="x",
            api_key="k",
            _urlopen=_fake_urlopen_factory({}),
        )


def test_client_wraps_http_errors_in_sparkhttperror() -> None:
    """urllib.error.URLError is wrapped in SparkHTTPError, not bubbled raw."""
    from src.adapters.spark.client import SparkHTTPError, fetch_active_land_listings

    with pytest.raises(SparkHTTPError, match="Spark API request failed"):
        fetch_active_land_listings(
            scope_type="county",
            scope_value="Washtenaw",
            api_key="k",
            _urlopen=_raising_urlopen(urllib.error.URLError("econnrefused")),
        )


def test_client_returns_empty_list_when_value_field_missing() -> None:
    """Spark response with neither ``value`` nor the legacy envelope → empty list."""
    from src.adapters.spark.client import fetch_active_land_listings

    captured: dict[str, Any] = {}

    def _fake_urlopen(req: Any, timeout: int = 60) -> _FakeResp:
        captured["url"] = req.full_url
        return _FakeResp(b"{}")

    result = fetch_active_land_listings(
        scope_type="county",
        scope_value="Washtenaw",
        api_key="k",
        _urlopen=_fake_urlopen,
    )
    assert result == []


# ─────────────────────────────────────────────────────────────────────────
# Agent tests
# ─────────────────────────────────────────────────────────────────────────


def _fake_fetch_returning(records: list[dict]):
    """Return a _fetch substitute that yields the given records."""

    def _fetch(
        *,
        scope_type: str,
        scope_value: str,
        top: int = 100,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> list[dict]:
        return records

    return _fetch


def _fake_fetch_raising(exc: Exception):
    """Return a _fetch substitute that raises ``exc``."""

    def _fetch(*args: Any, **kwargs: Any) -> list[dict]:
        raise exc

    return _fetch


def _sample_record(**overrides: Any) -> dict:
    base = {
        "ListingKey": "20220101000000000000000000",
        "ListPrice": 32500.0,
        "CountyOrParish": "Washtenaw",
        "City": "Ypsilanti",
        "PostalCode": "48197",
        "UnparsedAddress": "1888 McCartney Rd, Ypsilanti, MI 48197",
        "Latitude": 42.23,
        "Longitude": -83.61,
        "ModificationTimestamp": "2026-04-14T10:00:00Z",
    }
    base.update(overrides)
    return base


_STABLE_TOP_LEVEL_KEYS = {
    "status",
    "discovered_parcels",
    "scope",
    "trigger_reason",
    "program_name",
    "warning",
    "reason",
}


@pytest.mark.parametrize(
    "scope,fetch,expected_status",
    [
        # ok — non-empty
        (
            {"type": "county", "value": "Washtenaw"},
            _fake_fetch_returning([_sample_record()]),
            "ok",
        ),
        # ok — empty
        (
            {"type": "county", "value": "Washtenaw"},
            _fake_fetch_returning([]),
            "ok",
        ),
        # unsupported — tif
        (
            {"type": "tif", "value": "Ypsi-downtown"},
            _fake_fetch_returning([_sample_record()]),
            "unsupported_scope_type",
        ),
        # unsupported — unknown
        (
            {"type": "wardrobe", "value": "x"},
            _fake_fetch_returning([]),
            "unsupported_scope_type",
        ),
        # error — spark broken
        (
            {"type": "county", "value": "Washtenaw"},
            _fake_fetch_raising(__import__("src.adapters.spark.client", fromlist=["SparkHTTPError"]).SparkHTTPError("boom")),
            "error",
        ),
        # error — invalid scope shape
        (
            "not-a-dict",
            _fake_fetch_returning([]),
            "error",
        ),
        # error — missing type/value keys
        (
            {"value": "Washtenaw"},
            _fake_fetch_returning([]),
            "error",
        ),
    ],
)
def test_opportunity_hunter_output_shape_is_stable(
    scope: Any, fetch: Any, expected_status: str
) -> None:
    """Finding #8: every return path emits exactly the same top-level keys.

    This is the contract with the M2-10 orchestrator. Changing any key here
    is a coordinated change with that task.
    """
    from src.agents.opportunity_hunter import hunt_opportunities

    result = hunt_opportunities(
        scope=scope,
        trigger_reason="area_favorable_ypsi",
        program_name="Ypsilanti Township Renaissance Zone",
        _fetch=fetch,
    )

    assert set(result.keys()) == _STABLE_TOP_LEVEL_KEYS
    assert result["status"] == expected_status
    # Trigger metadata is always echoed back for orchestrator logging.
    assert result["trigger_reason"] == "area_favorable_ypsi"
    assert result["program_name"] == "Ypsilanti Township Renaissance Zone"


def test_hunt_opportunities_unsupported_scope_type_tif() -> None:
    """tif scope is deferred to M3 and returns unsupported_scope_type + reason."""
    from src.agents.opportunity_hunter import hunt_opportunities

    result = hunt_opportunities(
        scope={"type": "tif", "value": "Downtown-Ypsi"},
        trigger_reason="tif_found",
        program_name="Downtown Ypsi TIF",
        _fetch=_fake_fetch_returning([_sample_record()]),
    )

    assert result["status"] == "unsupported_scope_type"
    assert result["discovered_parcels"] == []
    assert "M3" in result["reason"]
    assert result["warning"] is None


def test_hunt_opportunities_unsupported_scope_type_unknown() -> None:
    """Any scope type outside {county, township, zip} → unsupported_scope_type."""
    from src.agents.opportunity_hunter import hunt_opportunities

    result = hunt_opportunities(
        scope={"type": "wardrobe", "value": "anything"},
        trigger_reason="r",
        program_name="p",
        _fetch=_fake_fetch_returning([]),
    )

    assert result["status"] == "unsupported_scope_type"
    assert "wardrobe" in result["reason"]


def test_hunt_opportunities_empty_results_returns_warning() -> None:
    """Finding #10: zero listings for a valid scope surfaces as a warning.

    The orchestrator distinguishes ``status=ok + warning=...`` (valid area
    with no listings, expected on quiet markets) from ``status=error``
    (Spark broke) and routes accordingly.
    """
    from src.agents.opportunity_hunter import hunt_opportunities

    result = hunt_opportunities(
        scope={"type": "county", "value": "Washtenaw"},
        trigger_reason="r",
        program_name="p",
        _fetch=_fake_fetch_returning([]),
    )

    assert result["status"] == "ok"
    assert result["discovered_parcels"] == []
    assert result["warning"] == "no_active_listings_in_scope"
    assert result["reason"] is None


def test_hunt_opportunities_success_builds_parcel_dicts() -> None:
    """Happy path: 3 records → 3 parcels with every expected field populated."""
    from src.agents.opportunity_hunter import hunt_opportunities

    records = [
        _sample_record(ListingKey="a", ListPrice=10000),
        _sample_record(ListingKey="b", ListPrice=20000),
        _sample_record(ListingKey="c", ListPrice=30000),
    ]
    result = hunt_opportunities(
        scope={"type": "county", "value": "Washtenaw"},
        trigger_reason="area_favorable",
        program_name="Washtenaw Brownfield",
        _fetch=_fake_fetch_returning(records),
    )

    assert result["status"] == "ok"
    assert result["warning"] is None
    assert len(result["discovered_parcels"]) == 3

    expected_keys = {
        "listing_key",
        "list_price",
        "county",
        "city",
        "postal_code",
        "unparsed_address",
        "latitude",
        "longitude",
        "modification_timestamp",
    }
    for parcel in result["discovered_parcels"]:
        assert set(parcel.keys()) == expected_keys

    assert [p["listing_key"] for p in result["discovered_parcels"]] == ["a", "b", "c"]
    assert [p["list_price"] for p in result["discovered_parcels"]] == [10000, 20000, 30000]


def test_hunt_opportunities_spark_http_error_returns_error_status() -> None:
    """SparkHTTPError from the client is caught and surfaced in reason."""
    from src.adapters.spark.client import SparkHTTPError
    from src.agents.opportunity_hunter import hunt_opportunities

    result = hunt_opportunities(
        scope={"type": "county", "value": "Washtenaw"},
        trigger_reason="r",
        program_name="p",
        _fetch=_fake_fetch_raising(SparkHTTPError("500 Internal Server Error")),
    )

    assert result["status"] == "error"
    assert "spark_api_error" in result["reason"]
    assert "500" in result["reason"]
    assert result["discovered_parcels"] == []


def test_hunt_opportunities_invalid_scope_shape_returns_error() -> None:
    """Scope dict missing ``type`` or ``value`` → status=error, clear reason."""
    from src.agents.opportunity_hunter import hunt_opportunities

    result = hunt_opportunities(
        scope={},
        trigger_reason="r",
        program_name="p",
        _fetch=_fake_fetch_returning([]),
    )

    assert result["status"] == "error"
    assert "type" in result["reason"] and "value" in result["reason"]


def test_hunt_opportunities_propagates_environmenterror_from_client() -> None:
    """Finding #2: EnvironmentError bubbles up through the agent, NOT caught.

    The MCP handler is the only layer that catches this exception; the agent
    leaves it for the handler so the test proves the bubble.
    """
    from src.agents.opportunity_hunter import hunt_opportunities

    def _raising_fetch(*args: Any, **kwargs: Any):
        raise EnvironmentError("SPARK_API_KEY is unset.")

    with pytest.raises(EnvironmentError, match="SPARK_API_KEY"):
        hunt_opportunities(
            scope={"type": "county", "value": "Washtenaw"},
            trigger_reason="r",
            program_name="p",
            _fetch=_raising_fetch,
        )


# ─────────────────────────────────────────────────────────────────────────
# MCP handler tests
# ─────────────────────────────────────────────────────────────────────────


def test_handler_catches_environmenterror_returns_err() -> None:
    """Finding #2 at the handler layer: SPARK_API_KEY missing → _err, not raise.

    We patch the agent module so the handler's call site raises
    EnvironmentError without the test having to touch the environment.
    """
    import src.agents.opportunity_hunter as agent_mod
    from src.mcp.handlers import MeshState, handle_opportunity_hunter

    def _raising(**kwargs: Any):
        raise EnvironmentError("SPARK_API_KEY is unset.")

    mesh = MeshState()
    with patch.object(agent_mod, "hunt_opportunities", _raising):
        response = asyncio.run(
            handle_opportunity_hunter(
                mesh,
                scope={"type": "county", "value": "Washtenaw"},
                trigger_reason="r",
                program_name="p",
            )
        )

    assert response["isError"] is True
    assert "SPARK_API_KEY" in response["content"][0]["text"]


@pytest.mark.parametrize("bad_scope", [None, "oops", 42, ["not", "a", "dict"]])
def test_handler_rejects_non_dict_scope(bad_scope: Any) -> None:
    """The handler type-checks scope at the boundary, avoiding AttributeError."""
    from src.mcp.handlers import MeshState, handle_opportunity_hunter

    mesh = MeshState()
    response = asyncio.run(
        handle_opportunity_hunter(
            mesh,
            scope=bad_scope,
            trigger_reason="r",
            program_name="p",
        )
    )

    assert response["isError"] is True
    assert "scope must be a dict" in response["content"][0]["text"]


def test_handler_registered_in_handler_map() -> None:
    """The opportunity_hunter tool is dispatchable via HANDLER_MAP."""
    from src.mcp.handlers import HANDLER_MAP, handle_opportunity_hunter

    assert "opportunity_hunter" in HANDLER_MAP
    assert HANDLER_MAP["opportunity_hunter"] is handle_opportunity_hunter


def test_handler_happy_path_returns_ok_envelope() -> None:
    """End-to-end: handler dispatches to the agent and returns an _ok response."""
    import src.agents.opportunity_hunter as agent_mod
    from src.mcp.handlers import MeshState, handle_opportunity_hunter

    records = [_sample_record(ListingKey="only-one")]

    def _fake_hunt(**kwargs: Any) -> dict[str, Any]:
        # Return a realistic envelope shape so the test proves the full round-trip.
        return {
            "status": "ok",
            "discovered_parcels": [
                {
                    "listing_key": "only-one",
                    "list_price": 32500.0,
                    "county": "Washtenaw",
                    "city": "Ypsilanti",
                    "postal_code": "48197",
                    "unparsed_address": "1888 McCartney",
                    "latitude": 42.23,
                    "longitude": -83.61,
                    "modification_timestamp": "2026-04-14T10:00:00Z",
                }
            ],
            "scope": kwargs["scope"],
            "trigger_reason": kwargs["trigger_reason"],
            "program_name": kwargs["program_name"],
            "warning": None,
            "reason": None,
        }

    mesh = MeshState()
    with patch.object(agent_mod, "hunt_opportunities", _fake_hunt):
        response = asyncio.run(
            handle_opportunity_hunter(
                mesh,
                scope={"type": "county", "value": "Washtenaw"},
                trigger_reason="area_favorable_ypsi",
                program_name="Ypsilanti Township Renaissance Zone",
            )
        )

    assert response["isError"] is False
    payload = json.loads(response["content"][0]["text"])
    assert payload["status"] == "ok"
    assert payload["program_name"] == "Ypsilanti Township Renaissance Zone"
    assert len(payload["discovered_parcels"]) == 1
    assert payload["discovered_parcels"][0]["listing_key"] == "only-one"
