# Builder Prompt — Step 6: Cluster Detection Agent
# Generated: 2026-03-09
# Paste this into a fresh Claude Code chat opened at the repo root.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are the Builder Agent for BaseMod LandOS — an autonomous real estate
operating system built on an event mesh architecture.

This session implements Step 6: Cluster Detection — formalizing the
ParcelClusterDetector into a full agent-ready module with events, rules,
and bidirectional signal routing.

════════════════════════════════════════════════════════════════════════
CONTEXT — READ BEFORE TOUCHING ANYTHING
════════════════════════════════════════════════════════════════════════

Project root: /Users/bennett2026/Desktop/Kingdom LandOS/BaseMod LandOS/
Python workspace: landos/
Run all tests:
  python3 -m pytest "/Users/bennett2026/Desktop/Kingdom LandOS/BaseMod LandOS/landos/tests/" -v

**NEVER use `cd landos &&` — it corrupts the shell cwd and breaks hooks.**

Current state:
  Steps 1–5 + 4.5 complete. 237/237 tests pass. Zero regressions allowed.
  ParcelClusterDetector EXISTS and is operational with live data.
  Live pipeline produces 2,229 clusters from 10,266 vacant parcels.
  47 clusters already matched to active Spark listings.
  23 Tier 1 high-convergence opportunities identified.

Architecture rules — never violate:
  - LandOS is an event mesh. Every signal can wake any agent. No pipelines.
  - The moat is the wake-up logic. Signals must compound, not terminate.
  - InMemory stores only. No database persistence.
  - TriggerEngine requires cooldown_tracker=InMemoryCooldownTracker()
  - RoutingResult fields: event_type, event_id, evaluated_at, fired_rules,
    suppressed_rules, wake_instructions. No .event sub-object.
  - InMemory stores: always use `is not None` checks, never `or`.
  - DERIVED event_class requires: source_confidence, derived_from_event_ids,
    emitted_by_agent_run_id. Ingestion adapters use RAW.
  - Before creating any file, read the adjacent existing files for patterns.

════════════════════════════════════════════════════════════════════════
PRE-WORK — DO THIS FIRST (~20 min)
════════════════════════════════════════════════════════════════════════

Before starting Step 6, add these test gaps:

1. Add `TestOfficeDetection` class to `landos/tests/test_bbo_signals.py`:
   - Test positive: 5 listings same `listing_office_id` → detected (count=5)
   - Test negative: 2 listings same `listing_office_id` → not detected
   - Test None: `listing_office_id` is None → not detected (False, 0)

2. Add explicit RP + RR assertions to `TestReverseRulesWired` in same file:
   - Assert RP rule (same_owner_listing_detected) exists in ALL_RULES
     with target=spark_signal_agent
   - Assert RR rule (parcel_owner_resolved) exists in ALL_RULES
     with target=spark_signal_agent

3. Run tests. Confirm 239+ pass. Then proceed to Step 6.

════════════════════════════════════════════════════════════════════════
STEP 6 — CLUSTER DETECTION
════════════════════════════════════════════════════════════════════════

Key files to read first:
  landos/src/adapters/cluster/parcel_cluster_detector.py  (EXISTS — the foundation)
  landos/src/adapters/cluster/detector.py                 (EXISTS — listing-level detector)
  landos/src/adapters/cluster/event_factory.py            (EXISTS — cluster events)
  landos/src/adapters/cluster/store.py                    (EXISTS — InMemoryClusterStore)
  landos/src/models/owner.py                              (EXISTS — OwnerCluster model)
  landos/src/triggers/rules/__init__.py                   (31 rules already wired)
  landos/tests/test_cluster_detection.py                  (EXISTS — check what's covered)

────────────────────────────────────────────────────────────────────────
6A. Understand what already exists
────────────────────────────────────────────────────────────────────────

ParcelClusterDetector (built this session) already does:
  - Owner name clustering (normalized string dedup, min 2 parcels)
  - Subdivision clustering (regex from legal_description_raw, min 3 parcels)
  - Geographic proximity clustering (haversine 200m radius, min 3 parcels)
  - Cross-references clusters against Spark listings
  - Emits events: vacant_owner_cluster_detected, vacant_subdivision_cluster_detected,
    vacant_proximity_cluster_detected

ClusterDetector (from Step 4.5) already does:
  - Listing-level agent/office pattern detection
  - Emits: same_owner_listing_detected, owner_cluster_detected,
    owner_cluster_size_threshold_crossed, agent_subdivision_program_detected,
    office_inventory_program_detected

Event factory (event_factory.py) already builds:
  - build_same_owner_listing_detected
  - build_owner_cluster_detected
  - build_owner_cluster_size_threshold_crossed
  - build_agent_subdivision_program_detected
  - build_office_inventory_program_detected

Trigger rules already wired:
  - RO: owner_cluster_detected → RESCAN spark_signal_agent (reverse)
  - RP: same_owner_listing_detected → RESCAN spark_signal_agent (reverse)
  - RU: owner_cluster_size_threshold_crossed → RESCAN opportunity_creation_agent + municipal_agent

────────────────────────────────────────────────────────────────────────
6B. What Step 6 needs to add/formalize
────────────────────────────────────────────────────────────────────────

1. **Unify ParcelClusterDetector + ClusterDetector** into a coherent module
   - ParcelClusterDetector handles parcel-level clustering (the big data)
   - ClusterDetector handles listing-level pattern detection (agent/office)
   - Both should emit through the same event factory and route through TriggerEngine
   - Consider a ClusterOrchestrator that runs both detectors in sequence

2. **Ensure all 5 cluster event types route through TriggerEngine**
   The events exist but verify they fire rules correctly:
   - same_owner_listing_detected → RP fires → spark_signal_agent wakes
   - owner_cluster_detected → RO fires → spark_signal_agent wakes
   - owner_cluster_size_threshold_crossed → RU fires → opportunity + municipal agents
   - agent_subdivision_program_detected → (add rule if missing)
   - office_inventory_program_detected → (add rule if missing)

3. **Add cluster-to-listing enrichment loop**
   When a parcel cluster is detected that contains matched listings:
   - Emit same_owner_listing_detected for each listing in the cluster
   - This triggers RP → spark_signal_agent → deeper BBO analysis
   - The ping-pong: cluster → BBO → deeper cluster is the product

4. **Cluster persistence in InMemoryClusterStore**
   - Store all detected clusters
   - Support lookup by owner_key, subdivision, proximity group
   - Support cluster growth tracking (count changes between runs)

5. **Tests for Step 6** — add to `test_cluster_detection.py` or create new file:
   - ParcelClusterDetector with mock parcels → correct cluster counts
   - Owner cluster with matched listing → same_owner_listing_detected fires
   - Cluster size threshold → owner_cluster_size_threshold_crossed fires
   - Cluster → BBO reverse routing (RP, RO) fires correctly
   - Integration: full pipeline mock with parcels + listings → correct events

────────────────────────────────────────────────────────────────────────
6C. Signal enrichment opportunities
────────────────────────────────────────────────────────────────────────

The live data revealed these patterns — encode them as detection logic:

- **Dormant supply detection**: Owner clusters with 10+ vacant lots and NO
  active listings → emit `dormant_supply_detected` event. 76 such clusters
  exist (22,057 acres). Toll Brothers alone has 146 lots sitting dormant.

- **Listing fatigue in cluster context**: When a cluster has listings with
  CDOM > 180, the cluster-level fatigue signal is stronger than individual
  listing fatigue. Score multiplier for cluster-level fatigue.

- **Cross-cluster ownership**: Some owners appear in multiple subdivision
  clusters. Detect and emit `cross_cluster_owner_detected`.

────────────────────────────────────────────────────────────────────────
6D. Acceptance criteria
────────────────────────────────────────────────────────────────────────

Step 6 is complete when:
1. All cluster event types emit through TriggerEngine
2. Reverse routing RO + RP confirmed firing in tests
3. ParcelClusterDetector integrated with ClusterDetector
4. InMemoryClusterStore persists all cluster results
5. 250+ tests pass (237 baseline + new cluster tests)
6. Zero regressions on existing tests
7. Output: LANDOS_STEP_COMPLETE

────────────────────────────────────────────────────────────────────────
6E. Commit
────────────────────────────────────────────────────────────────────────

Commit message:
  Step 6: Cluster detection — parcel-first clustering with bidirectional routing

  - Unified ParcelClusterDetector + ClusterDetector into cluster orchestration
  - All 5 cluster event types route through TriggerEngine
  - Reverse routing RP/RO confirmed: cluster → BBO feedback loop active
  - InMemoryClusterStore persistence for all cluster results
  - [N] new tests, [M] total passing

  Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

────────────────────────────────────────────────────────────────────────
DONE — output gate string
────────────────────────────────────────────────────────────────────────

When all tests pass and commit is made, output exactly:

LANDOS_STEP_COMPLETE — Step 6: Cluster Detection
Tests: [N] passed, 0 failed
Cluster event types: same_owner_listing_detected, owner_cluster_detected,
  owner_cluster_size_threshold_crossed, agent_subdivision_program_detected,
  office_inventory_program_detected
Reverse routing: RP + RO confirmed firing
Parcel clusters: owner, subdivision, proximity (3 families)
Step 7 (Municipal Agent) is now unblocked.
