"""MCP tool handlers for the LandOS event mesh.

Each handler wraps existing LandOS adapters, stores, and engines.
Handlers return MCP-compliant response dicts: {"content": [...], "isError": bool}.

Design principles (from SRE cookbook):
  - Handler-level restrictions enforce safety (store isolation, read-only checks)
  - Clear separation: investigation handlers never write, mutation handlers always write
  - Every handler returns structured data the agent can reason about
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.adapters.cluster.parcel_cluster_detector import (
    OWNER_MIN_PARCELS,
    PROXIMITY_MIN_PARCELS,
    PROXIMITY_RADIUS_METERS,
    SUBDIVISION_MIN_PARCELS,
    ParcelClusterDetector,
)
from src.adapters.cluster.store import InMemoryClusterStore
from src.adapters.regrid.ingestion import (
    InMemoryOwnerStore,
    InMemoryParcelStore,
    RegridIngestionAdapter,
)
from src.adapters.regrid.linker import ParcelListingLinker
from src.adapters.spark.bbo_signals import (
    CDOM_THRESHOLD_DEFAULT,
    detect_agent_land_accumulation,
    detect_cdom_threshold,
    detect_developer_exit,
    detect_office_land_program,
    detect_private_remarks_signals,
    detect_subdivision_remnant,
)
from src.adapters.spark.ingestion import InMemoryListingStore, SparkIngestionAdapter
from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.enums import StandardStatus, VacancyStatus
from src.triggers.context import TriggerContext
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES


# ── Response helpers ──────────────────────────────────────────────────

def _ok(data: Any) -> dict[str, Any]:
    """Build a successful MCP tool response."""
    text = json.dumps(data, default=str, indent=2) if not isinstance(data, str) else data
    return {"content": [{"type": "text", "text": text}], "isError": False}


def _err(message: str) -> dict[str, Any]:
    """Build an error MCP tool response."""
    return {"content": [{"type": "text", "text": f"Error: {message}"}], "isError": True}


def _serialize_listing(listing: Any) -> dict[str, Any]:
    """Serialize a Listing to a summary dict."""
    return {
        "listing_key": listing.listing_key,
        "listing_id": str(listing.listing_id),
        "status": listing.standard_status.value,
        "list_price": listing.list_price,
        "property_type": listing.property_type,
        "acreage": listing.lot_size_acres,
        "address_raw": listing.address_raw,
        "cdom": listing.cdom,
        "dom": listing.dom,
        "subdivision": listing.subdivision_name_raw,
        "list_agent_key": listing.list_agent_key,
        "listing_office_name": listing.listing_office_name,
        "private_remarks_present": listing.private_remarks is not None,
    }


def _serialize_parcel(parcel: Any) -> dict[str, Any]:
    """Serialize a Parcel to a summary dict."""
    return {
        "parcel_id": str(parcel.parcel_id),
        "regrid_id": parcel.source_system_ids.get("regrid_id"),
        "acreage": parcel.acreage,
        "vacancy_status": parcel.vacancy_status.value,
        "county": parcel.county,
        "apn": parcel.apn_or_parcel_number,
        "owner_name": parcel.owner_name_raw,
        "centroid": parcel.centroid,
        "opportunity_score": parcel.opportunity_score,
        "address_raw": parcel.address_raw,
    }


def _serialize_cluster(cluster: Any) -> dict[str, Any]:
    """Serialize an OwnerCluster to a summary dict."""
    return {
        "cluster_id": str(cluster.cluster_id),
        "cluster_type": cluster.cluster_type.value,
        "member_count": cluster.member_count,
        "total_acreage": cluster.total_acreage,
        "detection_method": cluster.detection_method,
        "parcel_ids": [str(p) for p in (cluster.parcel_ids or [])],
        "listing_ids": [str(l) for l in (cluster.listing_ids or [])],
        "agent_program_flag": cluster.agent_program_flag,
        "office_program_flag": cluster.office_program_flag,
    }


def _serialize_routing_result(rr: Any) -> dict[str, Any]:
    """Serialize a RoutingResult to a dict."""
    return {
        "event_id": str(rr.event_id),
        "event_type": rr.event_type,
        "evaluated_at": str(rr.evaluated_at),
        "fired_rules": rr.fired_rules,
        "suppressed_rules": [
            {"rule_id": s.rule_id, "outcome": s.outcome.value, "detail": s.detail}
            for s in rr.suppressed_rules
        ],
        "wake_instructions": [
            {
                "rule_id": w.rule_id,
                "wake_target": w.wake_target,
                "wake_type": w.wake_type.value,
                "priority": w.priority,
            }
            for w in rr.wake_instructions
        ],
    }


# ── Mesh state container ─────────────────────────────────────────────

class MeshState:
    """Holds references to all LandOS in-memory stores and the trigger engine.

    A single MeshState instance is shared across all MCP tool handlers,
    providing the unified state context that the agent operates on.
    """

    def __init__(
        self,
        listing_store: InMemoryListingStore | None = None,
        parcel_store: InMemoryParcelStore | None = None,
        owner_store: InMemoryOwnerStore | None = None,
        cluster_store: InMemoryClusterStore | None = None,
        cooldown_tracker: InMemoryCooldownTracker | None = None,
        engine: TriggerEngine | None = None,
        context: TriggerContext | None = None,
    ):
        self.listing_store = listing_store or InMemoryListingStore()
        self.parcel_store = parcel_store or InMemoryParcelStore()
        self.owner_store = owner_store or InMemoryOwnerStore()
        self.cluster_store = cluster_store or InMemoryClusterStore()
        self.cooldown_tracker = cooldown_tracker or InMemoryCooldownTracker()
        self.engine = engine or TriggerEngine(
            rules=ALL_RULES,
            cooldown_tracker=self.cooldown_tracker,
        )
        self.context = context or TriggerContext()

    @property
    def all_listings(self) -> list:
        return self.listing_store.all_listings()

    @property
    def all_parcels(self) -> list:
        return [
            self.parcel_store.get_by_regrid_id(rid)
            for rid in self.parcel_store._store.keys()
        ]


# ── Store handlers (read-only) ───────────────────────────────────────

async def handle_get_listing(mesh: MeshState, listing_key: str) -> dict[str, Any]:
    listing = mesh.listing_store.get(listing_key)
    if listing is None:
        return _err(f"Listing '{listing_key}' not found in store")
    return _ok(_serialize_listing(listing))


async def handle_list_all_listings(
    mesh: MeshState,
    status_filter: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    listings = mesh.all_listings
    if status_filter:
        try:
            status = StandardStatus(status_filter)
            listings = [l for l in listings if l.standard_status == status]
        except ValueError:
            return _err(f"Invalid status_filter: '{status_filter}'")
    listings = listings[:limit]
    return _ok({
        "count": len(listings),
        "listings": [_serialize_listing(l) for l in listings],
    })


async def handle_get_parcel(mesh: MeshState, regrid_id: str) -> dict[str, Any]:
    parcel = mesh.parcel_store.get_by_regrid_id(regrid_id)
    if parcel is None:
        return _err(f"Parcel '{regrid_id}' not found in store")
    return _ok(_serialize_parcel(parcel))


async def handle_list_all_parcels(
    mesh: MeshState,
    vacancy_filter: str | None = None,
    min_acreage: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    parcels = mesh.all_parcels
    if vacancy_filter:
        try:
            vs = VacancyStatus(vacancy_filter)
            parcels = [p for p in parcels if p.vacancy_status == vs]
        except ValueError:
            return _err(f"Invalid vacancy_filter: '{vacancy_filter}'")
    if min_acreage is not None:
        parcels = [p for p in parcels if p.acreage >= min_acreage]
    parcels = parcels[:limit]
    return _ok({
        "count": len(parcels),
        "parcels": [_serialize_parcel(p) for p in parcels],
    })


async def handle_get_cluster(mesh: MeshState, cluster_id: str) -> dict[str, Any]:
    try:
        cid = UUID(cluster_id)
    except ValueError:
        return _err(f"Invalid cluster_id UUID: '{cluster_id}'")
    cluster = mesh.cluster_store.get(cid)
    if cluster is None:
        return _err(f"Cluster '{cluster_id}' not found in store")
    return _ok(_serialize_cluster(cluster))


async def handle_list_all_clusters(
    mesh: MeshState,
    cluster_type_filter: str | None = None,
    min_member_count: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    clusters = mesh.cluster_store.all()
    if cluster_type_filter:
        clusters = [c for c in clusters if c.cluster_type.value == cluster_type_filter]
    if min_member_count is not None:
        clusters = [c for c in clusters if c.member_count >= min_member_count]
    clusters = clusters[:limit]
    return _ok({
        "count": len(clusters),
        "clusters": [_serialize_cluster(c) for c in clusters],
    })


async def handle_get_mesh_health(mesh: MeshState) -> dict[str, Any]:
    listings = mesh.all_listings
    parcels = mesh.all_parcels
    clusters = mesh.cluster_store.all()

    status_counts = {}
    for l in listings:
        s = l.standard_status.value
        status_counts[s] = status_counts.get(s, 0) + 1

    vacancy_counts = {}
    for p in parcels:
        v = p.vacancy_status.value
        vacancy_counts[v] = vacancy_counts.get(v, 0) + 1

    cluster_type_counts = {}
    for c in clusters:
        ct = c.cluster_type.value
        cluster_type_counts[ct] = cluster_type_counts.get(ct, 0) + 1

    return _ok({
        "mesh_health": {
            "listings": {"total": len(listings), "by_status": status_counts},
            "parcels": {"total": len(parcels), "by_vacancy": vacancy_counts},
            "clusters": {"total": len(clusters), "by_type": cluster_type_counts},
            "owners": {"total": len(mesh.owner_store)},
            "active_trigger_rules": len(ALL_RULES),
        }
    })


# ── Spark handlers ───────────────────────────────────────────────────

async def handle_analyze_bbo_signals(
    mesh: MeshState,
    listing_key: str,
    cdom_threshold: int = CDOM_THRESHOLD_DEFAULT,
) -> dict[str, Any]:
    """Read-only BBO signal analysis on a single listing."""
    listing = mesh.listing_store.get(listing_key)
    if listing is None:
        return _err(f"Listing '{listing_key}' not found in store")

    all_listings = mesh.all_listings
    signals: dict[str, Any] = {}

    # 1. CDOM threshold
    signals["cdom_threshold_crossed"] = detect_cdom_threshold(listing, cdom_threshold)

    # 2. Developer exit
    exit_detected, exit_reason = detect_developer_exit(listing)
    signals["developer_exit"] = {"detected": exit_detected, "reason": exit_reason}

    # 3. PrivateRemarks language intelligence
    signals["private_remarks_signals"] = detect_private_remarks_signals(listing)

    # 4. Agent accumulation
    agent_detected, agent_count = detect_agent_land_accumulation(
        listing, all_listings, threshold=3
    )
    signals["agent_accumulation"] = {"detected": agent_detected, "count": agent_count}

    # 5. Office land program
    office_detected, office_count = detect_office_land_program(
        listing, all_listings, threshold=5
    )
    signals["office_land_program"] = {"detected": office_detected, "count": office_count}

    # 6. Subdivision remnant
    remnant_detected, remnant_reason = detect_subdivision_remnant(listing)
    signals["subdivision_remnant"] = {"detected": remnant_detected, "reason": remnant_reason}

    active_signals = [k for k, v in signals.items()
                      if (isinstance(v, bool) and v)
                      or (isinstance(v, dict) and v.get("detected"))
                      or (isinstance(v, list) and len(v) > 0)]

    return _ok({
        "listing_key": listing_key,
        "signals": signals,
        "active_signal_count": len(active_signals),
        "active_signals": active_signals,
    })


async def handle_ingest_spark_batch(
    mesh: MeshState,
    raw_records: list[dict],
) -> dict[str, Any]:
    """MUTATION: run Spark ingestion adapter on raw records."""
    adapter = SparkIngestionAdapter(
        engine=mesh.engine,
        context=mesh.context,
        store=mesh.listing_store,
    )
    results = adapter.process_batch(raw_records)
    return _ok({
        "records_processed": len(raw_records),
        "routing_results": [_serialize_routing_result(r) for r in results],
        "store_size_after": len(mesh.listing_store),
    })


# ── Regrid handlers ──────────────────────────────────────────────────

async def handle_analyze_parcel_linkage(
    mesh: MeshState,
    regrid_id: str,
) -> dict[str, Any]:
    """Read-only: check parcel-to-listing linkage."""
    parcel = mesh.parcel_store.get_by_regrid_id(regrid_id)
    if parcel is None:
        return _err(f"Parcel '{regrid_id}' not found in store")

    listings = mesh.all_listings
    if not listings:
        return _ok({"regrid_id": regrid_id, "match": None, "reason": "No listings in store"})

    linker = ParcelListingLinker(listings)
    result = linker.find_match(parcel)

    if result is None:
        return _ok({"regrid_id": regrid_id, "match": None, "reason": "No match found"})

    return _ok({
        "regrid_id": regrid_id,
        "match": {
            "listing_key": result.listing.listing_key,
            "method": result.method,
        },
    })


async def handle_compute_parcel_score(
    mesh: MeshState,
    regrid_id: str,
) -> dict[str, Any]:
    """Read-only: compute parcel opportunity score."""
    from src.adapters.regrid.ingestion import _compute_score

    parcel = mesh.parcel_store.get_by_regrid_id(regrid_id)
    if parcel is None:
        return _err(f"Parcel '{regrid_id}' not found in store")

    listings = mesh.all_listings
    linker = ParcelListingLinker(listings) if listings else None
    linked = linker.find_match(parcel) is not None if linker else False

    score = _compute_score(parcel, linked)
    return _ok({
        "regrid_id": regrid_id,
        "score": round(score, 4),
        "scoring_model": "v0.1_phase1_basic",
        "linked_to_listing": linked,
        "factors": {
            "acreage_weight": 0.40,
            "vacancy_weight": 0.40,
            "linkage_weight": 0.20,
        },
    })


async def handle_ingest_regrid_batch(
    mesh: MeshState,
    raw_records: list[dict],
) -> dict[str, Any]:
    """MUTATION: run Regrid ingestion adapter on raw records."""
    adapter = RegridIngestionAdapter(
        engine=mesh.engine,
        listings=mesh.all_listings,
        context=mesh.context,
        parcel_store=mesh.parcel_store,
        owner_store=mesh.owner_store,
    )
    results = adapter.process_batch(raw_records)
    return _ok({
        "records_processed": len(raw_records),
        "routing_results": [_serialize_routing_result(r) for r in results],
        "parcel_store_size_after": len(mesh.parcel_store),
        "owner_store_size_after": len(mesh.owner_store),
    })


# ── Cluster handlers ─────────────────────────────────────────────────

async def handle_preview_clusters(
    mesh: MeshState,
    owner_min_parcels: int = OWNER_MIN_PARCELS,
    subdivision_min_parcels: int = SUBDIVISION_MIN_PARCELS,
    proximity_radius_m: float = PROXIMITY_RADIUS_METERS,
) -> dict[str, Any]:
    """Read-only cluster preview — no events emitted, no state written."""
    parcels = mesh.all_parcels
    listings = mesh.all_listings
    if not parcels:
        return _ok({"clusters": [], "reason": "No parcels in store"})

    # Use a throwaway store and engine to avoid side effects
    throwaway_store = InMemoryClusterStore()
    throwaway_cooldown = InMemoryCooldownTracker()
    throwaway_engine = TriggerEngine(
        rules=ALL_RULES,
        cooldown_tracker=throwaway_cooldown,
    )

    detector = ParcelClusterDetector(
        engine=throwaway_engine,
        context=mesh.context,
        cluster_store=throwaway_store,
        owner_min_parcels=owner_min_parcels,
        subdivision_min_parcels=subdivision_min_parcels,
        proximity_radius_m=proximity_radius_m,
        proximity_min_parcels=PROXIMITY_MIN_PARCELS,
    )
    _results, clusters = detector.scan(parcels, listings)
    return _ok({
        "preview_cluster_count": len(clusters),
        "clusters": [
            {
                "cluster_type": c.cluster_type,
                "group_key": c.group_key,
                "parcel_count": c.parcel_count,
                "total_acreage": round(c.total_acreage, 2),
                "matched_listing_count": len(c.matched_listings),
            }
            for c in clusters
        ],
    })


async def handle_run_cluster_detection(
    mesh: MeshState,
    owner_min_parcels: int = OWNER_MIN_PARCELS,
    subdivision_min_parcels: int = SUBDIVISION_MIN_PARCELS,
    proximity_radius_m: float = PROXIMITY_RADIUS_METERS,
) -> dict[str, Any]:
    """MUTATION: run full cluster detection with event emission."""
    parcels = mesh.all_parcels
    listings = mesh.all_listings
    if not parcels:
        return _ok({"clusters": [], "reason": "No parcels in store"})

    detector = ParcelClusterDetector(
        engine=mesh.engine,
        context=mesh.context,
        cluster_store=mesh.cluster_store,
        owner_min_parcels=owner_min_parcels,
        subdivision_min_parcels=subdivision_min_parcels,
        proximity_radius_m=proximity_radius_m,
        proximity_min_parcels=PROXIMITY_MIN_PARCELS,
    )
    results, clusters = detector.scan(parcels, listings)
    return _ok({
        "clusters_detected": len(clusters),
        "routing_results": [_serialize_routing_result(r) for r in results],
        "cluster_store_size_after": len(mesh.cluster_store),
    })


# ── Trigger handlers ─────────────────────────────────────────────────

async def handle_list_trigger_rules(
    mesh: MeshState,
    event_type_filter: str | None = None,
) -> dict[str, Any]:
    """List all active trigger rules."""
    rules = ALL_RULES
    if event_type_filter:
        rules = [r for r in rules if r.event_type == event_type_filter or r.event_type == "*"]
    return _ok({
        "rule_count": len(rules),
        "rules": [
            {
                "rule_id": r.rule_id,
                "event_type": r.event_type,
                "wake_target": r.wake_target,
                "wake_type": r.wake_type.value,
                "phase": r.phase.value,
                "priority": r.priority,
                "cooldown_seconds": r.cooldown_seconds,
                "description": r.description,
            }
            for r in rules
        ],
    })


async def handle_dry_run_event(
    mesh: MeshState,
    event_type: str,
    event_family: str,
    payload: dict | None = None,
) -> dict[str, Any]:
    """Read-only: evaluate a synthetic event against all rules."""
    try:
        family = EventFamily(event_family)
    except ValueError:
        return _err(f"Invalid event_family: '{event_family}'")

    event = EventEnvelope(
        event_type=event_type,
        event_family=family,
        event_class=EventClass.RAW,
        occurred_at=datetime.now(timezone.utc),
        observed_at=datetime.now(timezone.utc),
        source_system="dry_run",
        entity_refs=EntityRefs(listing_id=uuid4()),
        payload=payload or {},
    )

    # Use a throwaway cooldown tracker so dry runs don't affect real state
    throwaway_cooldown = InMemoryCooldownTracker()
    throwaway_engine = TriggerEngine(
        rules=ALL_RULES,
        cooldown_tracker=throwaway_cooldown,
    )
    result = throwaway_engine.evaluate(event, mesh.context)
    return _ok(_serialize_routing_result(result))


async def handle_get_cooldown_state(
    mesh: MeshState,
    rule_id: str,
    cooldown_key: str,
) -> dict[str, Any]:
    """Check cooldown state for a rule + entity combo."""
    # Find the rule to get its cooldown_seconds
    rule = next((r for r in ALL_RULES if r.rule_id == rule_id), None)
    if rule is None:
        return _err(f"Rule '{rule_id}' not found in ALL_RULES")

    if rule.cooldown_seconds is None:
        return _ok({
            "rule_id": rule_id,
            "has_cooldown": False,
            "message": "This rule has no cooldown configured",
        })

    now = datetime.now(timezone.utc)
    is_cooling = mesh.cooldown_tracker.is_cooling_down(
        cooldown_key, rule_id, rule.cooldown_seconds, now
    )
    return _ok({
        "rule_id": rule_id,
        "cooldown_key": cooldown_key,
        "is_cooling_down": is_cooling,
        "cooldown_seconds": rule.cooldown_seconds,
    })


# ── Agent handlers ───────────────────────────────────────────────────

async def handle_zoning_extractor(
    mesh: MeshState,
    state: str,
    municipality: str,
    district_code: str,
) -> dict[str, Any]:
    """Extract dimensional setbacks for a municipality/district from the Tier 1 vault note.

    Returns zoning_blocked if the vault note is missing or the district is not found.
    This is expected behavior — the pipeline emits a zoning_blocked event so the
    laptop /loop worker can trigger ingest-municipality via Codex.
    """
    from src.agents.zoning_extractor import extract_zoning
    try:
        result = extract_zoning(state=state, municipality=municipality, district_code=district_code)
    except EnvironmentError as exc:
        return _err(str(exc))
    return _ok(result)


async def handle_permitted_use_checker(
    mesh: MeshState,
    model_type: str,
    district_code: str,
    municipality: str,
    state: str,
) -> dict[str, Any]:
    """Check whether a use type is permitted in a zoning district.

    Returns use_blocked if vault note is missing or the case is not deterministic.
    """
    from src.agents.permitted_use_checker import check_permitted_use
    try:
        result = check_permitted_use(
            model_type=model_type,
            district_code=district_code,
            municipality=municipality,
            state=state,
        )
    except EnvironmentError as exc:
        return _err(str(exc))
    return _ok(result)


async def handle_comp_narrator(
    mesh: MeshState,
    set1_rows: list[dict],
    set2_rows: list[dict],
    set3_rows: list[dict],
    sqft_band: tuple[int, int] = (1000, 1500),
) -> dict[str, Any]:
    """Produce three comp sets with aggregates and an anchor comp + exit $/sf.

    The caller (typically underwriter_agent) pre-filters the listing store by
    postal_code, property_type, date_range, etc. and passes the rows here.
    sqft_band is the (low, high) sqft range for the Set 2 Jaxon-band filter.
    """
    from src.agents.comp_narrator import narrate_comps
    result = narrate_comps(
        set1_rows=set1_rows,
        set2_rows=set2_rows,
        set3_rows=set3_rows,
        sqft_band=sqft_band,
    )
    return _ok(result)


async def handle_incentive_agent(
    mesh: MeshState,
    state: str,
    municipality: str,
    parcel_apn: str | None = None,
) -> dict[str, Any]:
    """Read the Programs & Incentives Tier 1 note for a municipality.

    Returns programs_blocked if the vault note is missing or no programs
    table is found. Blocked is NOT an error — it is a signal for the
    laptop /loop worker to trigger ingest-municipality via Codex.
    """
    from src.agents.incentive_agent import research_incentives
    try:
        result = research_incentives(
            state=state,
            municipality=municipality,
            parcel_apn=parcel_apn,
        )
    except EnvironmentError as exc:
        return _err(str(exc))
    return _ok(result)


async def handle_outreach_drafter(
    mesh: MeshState,
    underwriting: dict[str, Any],
    listing_agent: dict[str, Any],
) -> dict[str, Any]:
    """Draft an offer letter + cover email to agent for a GO/NEGOTIATE parcel.

    Hard rule (spec §4.5): NEVER sends. Drafts only. See
    ``src/agents/outreach_drafter.py`` for the CI grep guard that enforces
    this at the source level.

    The MCP layer passes the OpportunityUnderwriting as a plain dict; we
    validate it into the Pydantic model inside the handler so callers can
    send JSON-serialized payloads.

    Returns ``_err`` if OBSIDIAN_VAULT_PATH is unset (Finding #2 guard).
    """
    # Validate listing_agent at the MCP boundary. The drafter calls .get()
    # on this value, so passing a list, None, or a bare string would raise
    # an uncaught AttributeError that escapes the handler and breaks the
    # MCP contract — every tool response must be {"content": [...],
    # "isError": bool}. Catch the bad shape up front and return a clean
    # _err instead.
    if not isinstance(listing_agent, dict):
        return _err(
            f"listing_agent must be a dict, got {type(listing_agent).__name__}"
        )

    from pydantic import ValidationError

    from src.agents.outreach_drafter import draft_outreach
    from src.models.opportunity import OpportunityUnderwriting
    try:
        underwriting_model = OpportunityUnderwriting.model_validate(underwriting)
        result = draft_outreach(
            underwriting=underwriting_model,
            listing_agent=listing_agent,
        )
    except ValidationError as exc:
        return _err(f"Invalid underwriting payload: {exc}")
    except EnvironmentError as exc:
        return _err(str(exc))
    return _ok(result)


async def handle_opportunity_hunter(
    mesh: MeshState,
    scope: dict[str, Any],
    trigger_reason: str,
    program_name: str,
    top: int = 100,
) -> dict[str, Any]:
    """Query Spark for active Land listings in a favorable scope.

    Invoked when incentive_agent finds a new program (TIF, Renaissance
    Zone, MSHDA allocation, etc.) that changes parcel underwriting in an
    area. Returns the parcel list; the orchestrator (M2-10) turns each
    returned parcel into a ``parcel_discovered`` event with the program
    name in the event's ``trigger`` field.

    The handler catches ``EnvironmentError`` (Finding #2) so a missing
    SPARK_API_KEY surfaces as an MCP ``_err`` response instead of leaking
    a raw Python exception to the caller. It also type-checks ``scope``
    at the boundary — passing a list, string, or None would otherwise
    cause the agent's ``scope.get(...)`` calls to raise AttributeError.
    """
    if not isinstance(scope, dict):
        return _err(
            f"scope must be a dict, got {type(scope).__name__}"
        )

    from src.agents.opportunity_hunter import hunt_opportunities

    try:
        result = hunt_opportunities(
            scope=scope,
            trigger_reason=trigger_reason,
            program_name=program_name,
            top=top,
        )
    except EnvironmentError as exc:
        return _err(str(exc))
    return _ok(result)


# ── Tool dispatch ─────────────────────────────────────────────────────

HANDLER_MAP: dict[str, Any] = {
    # Store tools (read-only)
    "get_listing": handle_get_listing,
    "list_all_listings": handle_list_all_listings,
    "get_parcel": handle_get_parcel,
    "list_all_parcels": handle_list_all_parcels,
    "get_cluster": handle_get_cluster,
    "list_all_clusters": handle_list_all_clusters,
    "get_mesh_health": handle_get_mesh_health,
    # Spark tools
    "analyze_bbo_signals": handle_analyze_bbo_signals,
    "ingest_spark_batch": handle_ingest_spark_batch,
    # Regrid tools
    "analyze_parcel_linkage": handle_analyze_parcel_linkage,
    "compute_parcel_score": handle_compute_parcel_score,
    "ingest_regrid_batch": handle_ingest_regrid_batch,
    # Cluster tools
    "preview_clusters": handle_preview_clusters,
    "run_cluster_detection": handle_run_cluster_detection,
    # Trigger tools
    "list_trigger_rules": handle_list_trigger_rules,
    "dry_run_event": handle_dry_run_event,
    "get_cooldown_state": handle_get_cooldown_state,
    # Agent tools
    "zoning_extractor": handle_zoning_extractor,
    "permitted_use_checker": handle_permitted_use_checker,
    "comp_narrator": handle_comp_narrator,
    "incentive_agent": handle_incentive_agent,
    "outreach_drafter": handle_outreach_drafter,
    "opportunity_hunter": handle_opportunity_hunter,
}


async def dispatch_tool(
    mesh: MeshState,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Dispatch an MCP tool call to the appropriate handler.

    The mesh state is injected automatically — callers only provide
    the tool name and its arguments from the MCP request.
    """
    handler = HANDLER_MAP.get(tool_name)
    if handler is None:
        return _err(f"Unknown tool: '{tool_name}'")

    return await handler(mesh, **arguments)
