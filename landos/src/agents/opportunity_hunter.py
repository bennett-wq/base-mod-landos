"""Opportunity hunter — consume area_favorable events, re-query Spark, return new parcels.

Spec §4.6. Invoked by the orchestrator (M2-10) when incentive_agent emits an
``area_favorable`` event (found a TIF, Renaissance Zone, new MSHDA allocation,
etc.). Re-queries Spark for active Land listings in the favorable scope and
returns them so the orchestrator can emit one ``parcel_discovered`` event
per listing.

The agent DOES NOT emit events directly — that is the orchestrator's job.
The agent DOES NOT write to Airtable — that is a later task (M2-11 family).

──────────────────────────────────────────────────────────────────────
Return shape (STABLE CONTRACT with orchestrator — Finding #8)
──────────────────────────────────────────────────────────────────────
Every return path — success, error, unsupported, warning — emits the
SAME top-level keys. The orchestrator routes on ``status``; only the
companion fields change.

Top-level keys (ALWAYS present):
  status              : "ok" | "error" | "unsupported_scope_type"
  discovered_parcels  : list[dict]   (empty on non-ok paths)
  scope               : dict          (echoed from input for traceability)
  trigger_reason      : str           (echoed from input)
  program_name        : str           (echoed from input; orchestrator
                                       uses this for event.trigger field)
  warning             : str | None    (set on ok+empty results, None otherwise)
  reason              : str | None    (set on error / unsupported, None on ok)

Three non-happy outcomes (Finding #10 gap surfacing):
  1. Spark broken / API error         → status="error",
                                          reason="spark_api_error: ..."
  2. Scope type not supported (e.g. "tif")
                                       → status="unsupported_scope_type",
                                          reason="..."
  3. Scope valid but zero listings   → status="ok",
                                          discovered_parcels=[],
                                          warning="no_active_listings_in_scope"
  4. Scope valid and listings found  → status="ok",
                                          discovered_parcels=[...N items...]

The orchestrator uses ``status`` + optional ``warning`` to distinguish
"Spark went silent for weeks" from "the area genuinely has no active
listings." Silently returning ok+[] on every failure mode would mask
the first case.

EnvironmentError (SPARK_API_KEY unset) is NOT caught here — it bubbles
up to ``handle_opportunity_hunter`` in src/mcp/handlers.py, which wraps
it in an _err response per Finding #2.
"""
from __future__ import annotations

from typing import Any, Callable

from src.adapters.spark.client import (
    SparkHTTPError,
    fetch_active_land_listings,
)

# Scope types the client can actually filter on.
# "tif" is deliberately omitted: TIF district boundaries are polygons and
# Spark OData cannot filter by polygon. Polygon matching is M3 work.
_SUPPORTED_SCOPE_TYPES: frozenset[str] = frozenset({"county", "township", "zip"})

# Canonical key list for the return dict. Every return path MUST produce
# exactly these keys — the ``test_output_shape_is_stable`` parametrized test
# enforces this invariant against the orchestrator contract.
_OUTPUT_KEYS: frozenset[str] = frozenset(
    {
        "status",
        "discovered_parcels",
        "scope",
        "trigger_reason",
        "program_name",
        "warning",
        "reason",
    }
)


def _envelope(
    *,
    status: str,
    scope: Any,
    trigger_reason: str,
    program_name: str,
    discovered_parcels: list[dict] | None = None,
    warning: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Build the stable-shape return dict.

    Centralising construction here guarantees every call site produces
    exactly ``_OUTPUT_KEYS`` — no accidental drift.
    """
    return {
        "status": status,
        "discovered_parcels": list(discovered_parcels) if discovered_parcels else [],
        "scope": scope,
        "trigger_reason": trigger_reason,
        "program_name": program_name,
        "warning": warning,
        "reason": reason,
    }


def _parcel_from_record(record: dict) -> dict:
    """Extract the minimum parcel fields the orchestrator needs.

    The orchestrator turns each returned parcel into a
    ``parcel_discovered`` event with ``source="opportunity_hunter"`` and
    ``trigger=<program_name>``. It needs enough identifying info to
    dedupe + route the event through the normal pipeline.
    """
    return {
        "listing_key": record.get("ListingKey"),
        "list_price": record.get("ListPrice"),
        "county": record.get("CountyOrParish"),
        "city": record.get("City"),
        "postal_code": record.get("PostalCode"),
        "unparsed_address": record.get("UnparsedAddress"),
        "latitude": record.get("Latitude"),
        "longitude": record.get("Longitude"),
        "modification_timestamp": record.get("ModificationTimestamp"),
    }


def hunt_opportunities(
    *,
    scope: Any,
    trigger_reason: str,
    program_name: str,
    api_key: str | None = None,
    base_url: str | None = None,
    top: int = 100,
    _fetch: Callable[..., list[dict]] = fetch_active_land_listings,
) -> dict[str, Any]:
    """Find active Land listings in the given scope.

    Args:
        scope: Dict with keys ``type`` (one of "county", "township", "zip",
            "tif") and ``value`` (string — e.g. "Washtenaw", "Ypsilanti",
            "48197"). "tif" is parsed but returns unsupported_scope_type.
        trigger_reason: Why incentive_agent emitted area_favorable (echoed
            to the caller for downstream logging).
        program_name: Incentive program whose discovery triggered this
            hunt — the orchestrator puts this in each emitted event's
            ``trigger`` field.
        api_key: Overrides SPARK_API_KEY. Same semantics as the client.
        base_url: Overrides SPARK_BASE_URL.
        top: Max listings to fetch from Spark per scope.
        _fetch: Dependency-injected client for tests; defaults to the real
            ``fetch_active_land_listings``.

    Returns:
        The envelope dict described in the module docstring. Every return
        path emits the same top-level keys.

    Raises:
        EnvironmentError: Propagated from the client when SPARK_API_KEY is
            unset and no explicit api_key= kwarg is supplied. Caught by the
            MCP handler, NOT here (Finding #2).
    """
    # ── Validate scope shape at the boundary ──────────────────────────
    if not isinstance(scope, dict):
        return _envelope(
            status="error",
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            reason=(
                f"invalid_scope_shape: expected dict, got {type(scope).__name__}"
            ),
        )

    scope_type = scope.get("type")
    scope_value = scope.get("value")
    if scope_type is None or scope_value is None:
        return _envelope(
            status="error",
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            reason="invalid_scope_shape: scope must have both 'type' and 'value' keys",
        )

    # ── Unsupported scope types (tif and anything else) ───────────────
    if scope_type == "tif":
        return _envelope(
            status="unsupported_scope_type",
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            reason=(
                "TIF boundary matching deferred to M3; Spark OData cannot "
                "filter by polygon. Orchestrator should defer this trigger."
            ),
        )
    if scope_type not in _SUPPORTED_SCOPE_TYPES:
        return _envelope(
            status="unsupported_scope_type",
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            reason=(
                f"Unsupported scope_type {scope_type!r}. "
                f"Supported: {sorted(_SUPPORTED_SCOPE_TYPES)}"
            ),
        )

    # ── Fetch from Spark ─────────────────────────────────────────────
    try:
        records = _fetch(
            scope_type=scope_type,
            scope_value=scope_value,
            top=top,
            api_key=api_key,
            base_url=base_url,
        )
    except SparkHTTPError as exc:
        return _envelope(
            status="error",
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            reason=f"spark_api_error: {exc}",
        )
    # EnvironmentError from missing SPARK_API_KEY is intentionally NOT
    # caught here — it bubbles to the MCP handler per Finding #2. The
    # client also raises ValueError for unknown scope_type, but we
    # already gated on _SUPPORTED_SCOPE_TYPES above so that shouldn't
    # be reachable; if it ever is, letting it crash is correct because
    # it indicates a drift between the agent's and client's scope lists.

    # ── Build parcels ────────────────────────────────────────────────
    discovered = [_parcel_from_record(rec) for rec in records]

    # ── Zero-result gap surfacing (Finding #10) ──────────────────────
    if not discovered:
        return _envelope(
            status="ok",
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            discovered_parcels=[],
            warning="no_active_listings_in_scope",
        )

    return _envelope(
        status="ok",
        scope=scope,
        trigger_reason=trigger_reason,
        program_name=program_name,
        discovered_parcels=discovered,
    )
