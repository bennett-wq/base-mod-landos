"""MCP tool definitions for the LandOS event mesh.

Each tool has a name, description, and inputSchema following the MCP spec.
Tool descriptions are deliberately detailed — they drive autonomous agent
behavior more effectively than elaborate system prompts (SRE cookbook insight).

Tools are organized into 5 families:
    STORE_TOOLS       — read current state (listings, parcels, clusters)
    SPARK_TOOLS       — Spark MLS ingestion and BBO signal detection
    REGRID_TOOLS      — Regrid parcel ingestion, linkage, scoring
    CLUSTER_TOOLS     — cluster detection and scanning
    TRIGGER_TOOLS     — trigger engine evaluation and rule introspection

Investigation tools (read-only) are safe for autonomous use.
Mutation tools (ingestion, cluster detection) require HITL gating.
"""

from __future__ import annotations

# ── Store query tools (read-only, investigation-safe) ─────────────────

STORE_TOOLS: list[dict] = [
    {
        "name": "get_listing",
        "description": (
            "Get a single listing by its listing_key (Spark MLS identifier). "
            "Returns the full Listing object including BBO fields: cdom, "
            "private_remarks, list_agent_key, off_market_date, subdivision. "
            "Use this to inspect a specific listing during investigation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "listing_key": {
                    "type": "string",
                    "description": "Spark MLS listing_key identifier",
                },
            },
            "required": ["listing_key"],
        },
    },
    {
        "name": "list_all_listings",
        "description": (
            "List all listings currently in the in-memory store. "
            "Returns listing_key, status, list_price, acreage, cdom, and "
            "subdivision for each. Use for broad inventory overview. "
            "Warning: may return thousands of results in production."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": (
                        "Optional filter by StandardStatus value: "
                        "active, pending, closed, withdrawn, expired, canceled"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of listings to return (default 100)",
                    "default": 100,
                },
            },
        },
    },
    {
        "name": "get_parcel",
        "description": (
            "Get a single parcel by its regrid_id (Regrid identifier). "
            "Returns the full Parcel object: acreage, vacancy_status, "
            "centroid, owner, zoning, apn, opportunity_score, linked listing. "
            "Use this to inspect a specific parcel during investigation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "regrid_id": {
                    "type": "string",
                    "description": "Regrid parcel identifier",
                },
            },
            "required": ["regrid_id"],
        },
    },
    {
        "name": "list_all_parcels",
        "description": (
            "List all parcels in the in-memory store with summary fields: "
            "regrid_id, acreage, vacancy_status, county, opportunity_score, "
            "owner_name. Use for broad parcel inventory overview."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vacancy_filter": {
                    "type": "string",
                    "description": (
                        "Optional filter by VacancyStatus: "
                        "vacant, improved, partially_improved, unknown"
                    ),
                },
                "min_acreage": {
                    "type": "number",
                    "description": "Minimum acreage filter",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of parcels to return (default 100)",
                    "default": 100,
                },
            },
        },
    },
    {
        "name": "get_cluster",
        "description": (
            "Get a single OwnerCluster by cluster_id (UUID string). "
            "Returns cluster_type, member_count, total_acreage, detection_method, "
            "parcel_ids, listing_ids, agent/office program flags."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cluster_id": {
                    "type": "string",
                    "description": "Cluster UUID as string",
                },
            },
            "required": ["cluster_id"],
        },
    },
    {
        "name": "list_all_clusters",
        "description": (
            "List all OwnerCluster objects in the store. "
            "Returns cluster_id, cluster_type, member_count, total_acreage, "
            "detection_method for each. Use to find high-value cluster patterns."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cluster_type_filter": {
                    "type": "string",
                    "description": (
                        "Optional filter by ClusterType: "
                        "same_owner, same_agent, same_office, "
                        "same_subdivision, geographic_proximity, mixed"
                    ),
                },
                "min_member_count": {
                    "type": "integer",
                    "description": "Minimum member count filter",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of clusters to return (default 50)",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_mesh_health",
        "description": (
            "Get a comprehensive health summary of the LandOS event mesh. "
            "Returns: listing count by status, parcel count by vacancy, "
            "cluster count by type, active trigger rule count, "
            "total events processed, and store sizes. "
            "Use this as a starting point for any investigation."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]

# ── Spark MLS tools (investigation + mutation) ────────────────────────

SPARK_TOOLS: list[dict] = [
    {
        "name": "analyze_bbo_signals",
        "description": (
            "Run BBO signal analysis on a single listing by listing_key. "
            "Detects all 6 signal families WITHOUT emitting events: "
            "(1) Developer exit, (2) CDOM threshold, (3) PrivateRemarks language, "
            "(4) Agent accumulation, (5) Subdivision remnant, (6) Office land program. "
            "Read-only — safe for investigation. Returns signal detection results."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "listing_key": {
                    "type": "string",
                    "description": "Spark MLS listing_key to analyze",
                },
                "cdom_threshold": {
                    "type": "integer",
                    "description": "CDOM threshold for signal detection (default 90)",
                    "default": 90,
                },
            },
            "required": ["listing_key"],
        },
    },
    {
        "name": "ingest_spark_batch",
        "description": (
            "MUTATION: Ingest a batch of raw Spark MLS records through the "
            "SparkIngestionAdapter. Normalizes records, diffs against existing "
            "store, emits listing-family events, runs BBO signal detection, "
            "and routes all events through the trigger engine. "
            "Returns RoutingResults with fired/suppressed rules and wake instructions. "
            "REQUIRES human approval — this writes to listing store and fires triggers."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of raw Spark RESO/RETS record dicts",
                },
            },
            "required": ["raw_records"],
        },
    },
]

# ── Regrid parcel tools (investigation + mutation) ────────────────────

REGRID_TOOLS: list[dict] = [
    {
        "name": "analyze_parcel_linkage",
        "description": (
            "Read-only analysis: check if a parcel (by regrid_id) can be linked "
            "to any listing in the store. Tests all 3 linkage methods: "
            "address_match, parcel_number_match, geo_match (haversine 50m). "
            "Returns match result and method without modifying any state."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "regrid_id": {
                    "type": "string",
                    "description": "Regrid parcel identifier to check linkage for",
                },
            },
            "required": ["regrid_id"],
        },
    },
    {
        "name": "compute_parcel_score",
        "description": (
            "Read-only: compute the Phase 1 opportunity score for a parcel. "
            "Scoring model v0.1_phase1_basic: acreage(40%%) + vacancy(40%%) + "
            "linkage(20%%). Returns score without writing to store."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "regrid_id": {
                    "type": "string",
                    "description": "Regrid parcel identifier to score",
                },
            },
            "required": ["regrid_id"],
        },
    },
    {
        "name": "ingest_regrid_batch",
        "description": (
            "MUTATION: Ingest a batch of raw Regrid parcel records. "
            "Normalizes, links to listings, resolves owners, scores, emits "
            "parcel-state events, and routes through the trigger engine. "
            "REQUIRES human approval — writes to parcel and owner stores."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of raw Regrid CSV record dicts",
                },
            },
            "required": ["raw_records"],
        },
    },
]

# ── Cluster detection tools (investigation + mutation) ────────────────

CLUSTER_TOOLS: list[dict] = [
    {
        "name": "preview_clusters",
        "description": (
            "Read-only: preview what clusters WOULD be detected from current "
            "parcel and listing stores without writing anything. Returns "
            "cluster type, group key, parcel count, total acreage, and "
            "matched listings for each potential cluster. "
            "Safe for investigation — no events emitted, no state changed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner_min_parcels": {
                    "type": "integer",
                    "description": "Min parcels for owner cluster (default 2)",
                    "default": 2,
                },
                "subdivision_min_parcels": {
                    "type": "integer",
                    "description": "Min parcels for subdivision cluster (default 3)",
                    "default": 3,
                },
                "proximity_radius_m": {
                    "type": "number",
                    "description": "Proximity radius in meters (default 200)",
                    "default": 200.0,
                },
            },
        },
    },
    {
        "name": "run_cluster_detection",
        "description": (
            "MUTATION: Run full ParcelClusterDetector scan on current stores. "
            "Detects owner, subdivision, and proximity clusters. Creates "
            "OwnerCluster objects, emits cluster-family events, and routes "
            "through the trigger engine. "
            "REQUIRES human approval — writes to cluster store and fires triggers."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner_min_parcels": {
                    "type": "integer",
                    "description": "Min parcels for owner cluster (default 2)",
                    "default": 2,
                },
                "subdivision_min_parcels": {
                    "type": "integer",
                    "description": "Min parcels for subdivision cluster (default 3)",
                    "default": 3,
                },
                "proximity_radius_m": {
                    "type": "number",
                    "description": "Proximity radius in meters (default 200)",
                    "default": 200.0,
                },
            },
        },
    },
]

# ── Trigger engine tools (read-only investigation) ────────────────────

TRIGGER_TOOLS: list[dict] = [
    {
        "name": "list_trigger_rules",
        "description": (
            "List all active trigger rules in ALL_RULES. Returns rule_id, "
            "event_type, wake_target, wake_type, phase, priority, description "
            "for each. Use to understand what rules exist and what they do."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type_filter": {
                    "type": "string",
                    "description": "Optional: filter rules by event_type match",
                },
            },
        },
    },
    {
        "name": "dry_run_event",
        "description": (
            "Read-only: evaluate a synthetic event against all trigger rules "
            "WITHOUT executing any wake instructions. Returns which rules "
            "would fire, which would be suppressed (and why: cooldown, phase, "
            "materiality, depth cap), and what wake instructions would be produced. "
            "Use this to test trigger behavior without side effects."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Event type to simulate (e.g. 'listing_added')",
                },
                "event_family": {
                    "type": "string",
                    "description": (
                        "Event family: listing, cluster_owner, parcel_state, "
                        "municipal_process, developer_exit, etc."
                    ),
                },
                "payload": {
                    "type": "object",
                    "description": "Event payload dict for condition evaluation",
                },
            },
            "required": ["event_type", "event_family"],
        },
    },
    {
        "name": "get_cooldown_state",
        "description": (
            "Check cooldown state for a specific rule + entity combination. "
            "Returns whether the rule is currently cooling down and when "
            "the cooldown expires. Use to debug why expected rules didn't fire."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "string",
                    "description": "Rule ID to check (e.g. 'RA', 'RI')",
                },
                "cooldown_key": {
                    "type": "string",
                    "description": "Entity key (e.g. listing_key or cluster_id)",
                },
            },
            "required": ["rule_id", "cooldown_key"],
        },
    },
]


# ── Combined registries ───────────────────────────────────────────────

INVESTIGATION_TOOLS: list[dict] = (
    STORE_TOOLS
    + [SPARK_TOOLS[0]]           # analyze_bbo_signals (read-only)
    + [REGRID_TOOLS[0], REGRID_TOOLS[1]]  # analyze_parcel_linkage, compute_parcel_score
    + [CLUSTER_TOOLS[0]]          # preview_clusters (read-only)
    + TRIGGER_TOOLS               # all read-only
)

MUTATION_TOOLS: list[dict] = [
    SPARK_TOOLS[1],   # ingest_spark_batch
    REGRID_TOOLS[2],  # ingest_regrid_batch
    CLUSTER_TOOLS[1], # run_cluster_detection
]

ALL_TOOLS: list[dict] = INVESTIGATION_TOOLS + MUTATION_TOOLS

# Tool name sets for permission checking
INVESTIGATION_TOOL_NAMES: frozenset[str] = frozenset(
    t["name"] for t in INVESTIGATION_TOOLS
)
MUTATION_TOOL_NAMES: frozenset[str] = frozenset(
    t["name"] for t in MUTATION_TOOLS
)
ALL_TOOL_NAMES: frozenset[str] = INVESTIGATION_TOOL_NAMES | MUTATION_TOOL_NAMES
