# SESSION_LOG.md

## 2026-03-08 — Architecture Core Checkpoint

### What was completed
- Confirmed the BaseMod LandOS project folder structure is clean and usable as the canonical project root.
- Split the original handoff packet into individual canonical project files.
- Rewrote `LANDOS_OBJECT_MODEL.md` into an implementation-grade architecture document.
- Rewrote `LANDOS_EVENT_LIBRARY.md` into an implementation-grade event-schema document.
- Rewrote `LANDOS_TRIGGER_MATRIX.md` into an implementation-grade, rule-centric trigger-routing document.
- Audited the object model, event library, and trigger matrix for consistency, implementation readiness, and remaining gaps.
- Reached a clean architecture checkpoint suitable for session handoff.

### Files materially advanced
- `LANDOS_OBJECT_MODEL.md`
- `LANDOS_EVENT_LIBRARY.md`
- `LANDOS_TRIGGER_MATRIX.md`
- `README_SETUP.md`
- `NEXT_STEPS.md`

### Key decisions locked
- LandOS remains an event mesh, not a pipeline.
- The moat remains the wake-up logic.
- Listings, clusters, and municipalities remain co-equal trigger families.
- `SiteFit` is the canonical fit object; `SetbackFit` is a component within it.
- Buyer preference substructures remain embedded in `BuyerProfile` for now.
- `listing_expired` is raw and emitted directly from MLS ingestion.
- `bond_released_detected` should exist.
- Site-condo events form a staged detection-to-stall pipeline.
- `unfinished_site_condo_detected` should belong to the historical stall family.
- Score-change anti-loop logic uses three guardrails:
  - materiality gate
  - one-direction causality per chain
  - cooldown window
- `municipality_rule_change_detected` should be raw.
- `municipality_rule_now_supports_split` should be derived.

### Open items at checkpoint
- Apply the already-decided sync changes back into `LANDOS_EVENT_LIBRARY.md` so it matches the finalized trigger-matrix logic:
  - add `municipality_rule_change_detected`
  - change `municipality_rule_now_supports_split` from raw to derived
  - add `bond_released_detected`
  - move `unfinished_site_condo_detected` from municipal_process to historical_stall
- Confirm whether any additional small naming or routing alignments are needed between the event library and trigger matrix after the sync pass.
- Deepen the next downstream architecture docs after sync:
  - `LANDOS_AGENT_TEAMS.md`
  - `LANDOS_DATA_SOURCES.md`
  - `LANDOS_BUILD_ROADMAP.md`

### Next exact task
Apply the event-library sync changes so `LANDOS_EVENT_LIBRARY.md` fully matches the finalized decisions reflected in `LANDOS_TRIGGER_MATRIX.md`.

### Do not drift into
- source-specific field mapping
- runtime implementation
- new strategy invention
- duplicate master docs
- moving beyond synchronization and downstream architecture deepening before the event library is fully aligned

---

## 2026-03-08 — Downstream Doc Deepening (Agent Teams + Data Sources)

### What was completed
- Deepened `LANDOS_AGENT_TEAMS.md` from 26-line stubs to 410-line implementation-grade doc with all 8 teams fully specified (8 subsections each: purpose, responsibilities, objects, events subscribed, outputs, wake-up responsibilities, HITL points, boundaries).
- Fixed Team 3 misattribution: changed "(Team 5 family)" to "(developer/exit-window events, Family 5 in the trigger matrix)."
- Deepened `LANDOS_DATA_SOURCES.md` from thin source list to 327-line source architecture doc with 8 source categories, 3-tier confidence framework, source-combination logic, Michigan-specific notes, guardrails, and phased implementation sequencing.
- All references verified against canonical event library, trigger matrix, and object model. No new strategy or architecture expansion.

### Files materially advanced
- `LANDOS_AGENT_TEAMS.md` (deepened — full rewrite)
- `LANDOS_DATA_SOURCES.md` (deepened — full rewrite)

### Key decisions locked
- Agent teams are replaceable execution units; the moat is the wake-up architecture (reinforces existing decision).
- Confidence framework formalized: Tier 1 (authoritative), Tier 2 (partial), Tier 3 (inferential/LLM-derived).
- Source-combination logic: convergence strengthens, conflict triggers caution, corroboration required for high-stakes signals.

### Open items at checkpoint
- Deepen final downstream doc: `LANDOS_BUILD_ROADMAP.md`
- Trigger matrix implementation note #8 wording is stale (one-line fix, not blocking)

### Next exact task
Deepen `LANDOS_BUILD_ROADMAP.md` to include milestones, acceptance criteria, dependencies, and build-sequence logic.

### Do not drift into
- Source-specific field mapping
- Runtime implementation
- New strategy invention
- Duplicate master docs

### Task status
Partially complete — 2 of 3 downstream docs done. `LANDOS_BUILD_ROADMAP.md` remains.

## 2026-03-09 — Continuity Recovery After Shutdown

### What was completed
- Re-read the canonical docs and local repo state after the machine shutdown to re-establish the true implementation checkpoint.
- Confirmed the event-library sync items are already reflected in the current architecture docs.
- Confirmed Step 1 exists under `landos/src/events/` and Step 2 object-model work exists locally under `landos/src/models/` with accompanying Step 2 tests.
- Updated the live continuity baton so it matches the actual local repo state: Steps 1-2 complete locally, Step 3 next.

### Files materially advanced
- `SESSION_HANDOFF_CURRENT.md`
- `NEXT_STEPS.md`
- `SESSION_LOG.md`

### Key decisions locked
- No architecture or strategy changes were introduced.
- Operationally, the next build task is Step 3 trigger engine scaffold.
- Continuity should reflect local repo state, even when that state is ahead of committed history.

### Open items at checkpoint
- Step 2 object-model work is present locally but is not yet reflected in committed git history.
- Working tree still contains macOS `Icon` file noise alongside the actual Step 2 files.

### Next exact task
Begin Step 3: implement the trigger engine scaffold in `landos/src/triggers/` with tests for rule firing, non-match behavior, cooldowns, generation-depth cap, and phase-gating.

### Do not drift into
- database wiring
- ingestion adapters
- municipal scan implementation
- packaging, pricing, UI, or other Phase 2+ work
- continuity-file rewrites beyond keeping the baton aligned to actual repo state

### Task status
Complete

## 2026-03-09 — Step 3 Complete: Trigger Engine Scaffold

### What was completed
- Implemented the full Step 3 trigger engine scaffold in `landos/src/triggers/`.
- All 6 Step 3 acceptance criteria proven by tests:
  1. Matching rule fires (RA, RB, RC each produce a WakeInstruction when conditions met)
  2. Non-matching rule does not fire (wrong event type, condition not met)
  3. Cooldown blocks a duplicate (same entity within window; expires correctly after window)
  4. Generation-depth hard cap stops recursion (depth == cap → all rules DEPTH_CAP_REACHED)
  5. Phase gating prevents Phase 2+ rules from firing in Phase 1 context (RD suppressed)
  6. Cross-family routing confirmed (cluster_owner event → municipal team wake)
- Applied a critical deterministic time-handling fix: `context.current_timestamp` is threaded through all engine operations (RoutingResult.evaluated_at, WakeInstruction.created_at, cooldown reads and writes). No wall-clock calls remain inside the engine, cooldown tracker, wake, or result modules.
- All Step 1 + Step 2 + Step 3 tests pass together: 107/107.

### Files created
- `landos/src/triggers/__init__.py` — public API exports
- `landos/src/triggers/enums.py` — WakeType, PhaseGate, TriggerOutcome, phase_allows()
- `landos/src/triggers/rule.py` — TriggerRule dataclass (frozen)
- `landos/src/triggers/wake.py` — WakeInstruction dataclass
- `landos/src/triggers/result.py` — RoutingResult, SuppressedRule dataclasses
- `landos/src/triggers/context.py` — TriggerContext (frozen)
- `landos/src/triggers/cooldown.py` — CooldownTracker Protocol + InMemoryCooldownTracker
- `landos/src/triggers/engine.py` — TriggerEngine.evaluate()
- `landos/src/triggers/rules/__init__.py` — ALL_RULES (executable) + PLANNED_RULES (catalog)
- `landos/src/triggers/rules/listing_rules.py` — RA, RB
- `landos/src/triggers/rules/cluster_rules.py` — RC
- `landos/src/triggers/rules/phase2_placeholders.py` — RD
- `landos/tests/test_trigger_engine.py` — 30 Step 3 test cases

### Key design decisions locked
- Per-rule cooldown scoping: each TriggerRule defines its own `cooldown_key_builder`; no global entity-key derivation.
- Per-rule raw-event cooldown bypass: `raw_event_bypasses_cooldown: bool` on TriggerRule; engine only bypasses when the event is RAW AND the rule explicitly opts in.
- Phase ordering via `phase_allows(rule_phase, active_phase)` only — no direct PhaseGate comparisons in engine or rule code.
- Static `routing_class` on TriggerRule for Step 3; dynamic routing-class resolution (e.g., 5+ member cluster upgrade to IMMEDIATE) deferred to Step 6.
- PLANNED_RULES are non-active catalog entries (`condition=lambda e, ctx: False`) not loaded into any TriggerEngine instance.

### Open items at checkpoint
- PLANNED_RULES entries are pre-scaffolded for Steps 4–8; activate each by wiring a real condition and moving to ALL_RULES in the relevant step.
- InMemoryCooldownTracker is not production-safe; replace with Redis- or PostgreSQL-backed implementation in Step 4+.
- Fan-out enforcement (max_fan_out field) is documented on TriggerRule but not enforced; belongs in agent orchestration layer (Step 4+).
- Step 3 trigger engine files are present locally but not yet in committed git history.

### Next exact task
Begin Step 4: Spark MLS listing ingestion path — map Spark RETS/RESO fields to Listing object fields, build the ingestion adapter, and emit listing-family events through the trigger engine.

### Do not drift into
- Database wiring or persistent storage
- Regrid parcel linkage (Step 5)
- Cluster detection (Step 6)
- Municipal scan implementation (Step 7)
- Packaging, pricing, UI, or Phase 2+ work

---

## 2026-03-09 — Step 4 Complete: Spark MLS Listing Ingestion Path

### What was completed
- Built the Spark MLS ingestion adapter under `landos/src/adapters/spark/`.
- Implemented RESO→Listing field mapping, property-type filter (Michigan land/lot only), and full type coercion in the normalizer.
- Emitted all 5 listing-family raw events: `listing_added`, `listing_status_changed`, `listing_expired`, `listing_price_reduced`, `listing_relisted`.
- Applied 5 founder-reviewed plan corrections:
  1. **Source identity**: `entity_refs.listing_id` = internal UUID; `source_record_id` = Spark listing key string; all payloads include `listing_key`.
  2. **Relist dual-emit**: both `listing_status_changed` AND `listing_relisted` emitted for expired/withdrawn/canceled → active transitions.
  3. **gap_days nullability**: emitted as `None` when not computable; no sentinel zero.
  4. **reduction_count semantics**: cumulative tally; never resets on price increase; only resets on new listing_key appearance.
  5. **RE rule activated**: `PLANNED__listing_expired__cluster_reassessment` promoted to `RE__listing_expired__wake_supply_intelligence` in ALL_RULES. Full cluster-reassessment condition deferred to Step 6.
- Fixed subtle bug: `InMemoryListingStore.__len__` caused `store or InMemoryListingStore()` to create a shadow store when the passed store was empty. Changed to `store if store is not None else InMemoryListingStore()`.
- Fixed RB condition to handle `acreage=None` in payload: `float(e.payload.get("acreage", 0) or 0) >= 5.0`.
- 21 new tests added in `tests/test_spark_adapter.py`. All 128 tests pass (107 prior + 21 new).

### Files created
- `landos/src/adapters/spark/__init__.py`
- `landos/src/adapters/spark/field_map.py` — RESO→Listing constants; LAND_PROPERTY_TYPES; STATUS_MAP
- `landos/src/adapters/spark/normalizer.py` — normalize(); SkipRecord exception
- `landos/src/adapters/spark/event_factory.py` — build_* functions for all 5 listing-family events
- `landos/src/adapters/spark/ingestion.py` — SparkIngestionAdapter; InMemoryListingStore
- `landos/tests/test_spark_adapter.py` — 21 Step 4 test cases

### Files materially modified
- `landos/src/triggers/rules/listing_rules.py` — added RE; fixed RB acreage=None guard
- `landos/src/triggers/rules/__init__.py` — RE added to ALL_RULES; PLANNED__listing_expired__cluster_reassessment removed from PLANNED_RULES; RE exported

### Key design decisions locked
- Source identity is preserved via `source_record_id` (Spark listing key) + `entity_refs.listing_id` (internal UUID) + `source_system` field — no changes to EntityRefs model required.
- Relist transitions always emit two events (status_changed + relisted) so generic status listeners never miss a transition.
- `gap_days` is Optional[int] in relist payload; None means unknown, not zero.
- `reduction_count` is a cumulative lifetime tally for the current listing instance, not a current-markdown-streak counter.
- Step 4 adapter uses RESO standard fields only. BBO/private-role depth (PrivateRemarks, custom Michigan fields, metadata-driven mapping, historical bulk query) is explicitly deferred — see BBO Depth Follow-Up notes.

### BBO depth follow-up items logged (deferred)
- `PrivateRemarks` (confidential remarks) — not yet ingested; requires BBO credential mapping
- Michigan-specific custom fields (WaterFrontage, FrontageLength, MunicipalUtilityAvailable, ZoningDescription) — not in current field_map
- Metadata-driven field registry — `field_map.py` is a static dict; should be replaced with schema-registry approach in a future pass
- Historical bulk MLS query path — needed for cluster-triggered full reconciliation (Step 6+)
- Media/document resource — listing documents not yet ingested

### Open items at checkpoint
- InMemoryCooldownTracker and InMemoryListingStore both need production replacements (PostgreSQL/Redis) before any live feed wiring.
- No MLS query layer exists yet — process_batch() accepts records passed by the caller; polling/query integration is out of scope for Step 4.
- BBO depth pass is deferred; do not address before Step 6 cluster detection is functional.

### Next exact task
Begin Step 5: Regrid parcel linkage path — map Regrid fields to Parcel object fields, ingest Washtenaw County bulk parcel data, implement parcel-to-listing linkage (address match, parcel number match, geo-match fallback), emit parcel-state events.

### Do not drift into
- MLS query layer or live feed wiring
- BBO depth expansion
- Cluster detection (Step 6)
- Municipal scan (Step 7)
- Database or persistence wiring
- Packaging, pricing, UI, or Phase 2+ work

---

## 2026-03-09 — Step 4.5 Complete: Spark BBO Signal Intelligence + PM Gate Review

### What was completed
- PM Agent conducted full gate review of Step 4.5 (Spark BBO Signal Intelligence).
- Step 4.5 APPROVED. 202/202 tests pass. Zero regressions against Steps 1–5 baseline.
- 37 new BBO tests added in `landos/tests/test_bbo_signals.py`.
- 6 BBO signal detection families implemented as pure functions in `landos/src/adapters/spark/bbo_signals.py`.
- 6 new BBO event builders added to `landos/src/adapters/spark/event_factory.py`.
- `landos/src/models/listing.py` extended additively with all BBO field categories (developer exit, listing behavior, language intelligence, agent/office clustering, subdivision remnant, land detail, purchase contract).
- `landos/src/adapters/spark/field_map.py`: `BBO_TO_LISTING` dict added; `CumulativeDaysOnMarket` migrated from RESO to BBO map.
- `landos/src/adapters/spark/ingestion.py`: `_detect_and_build_bbo_events` helper added; BBO detection runs after store update and routes through TriggerEngine.
- `landos/src/triggers/rules/__init__.py`: 23 new rules added (RI–RU, with fan-out rules expressed as separate entries). ALL_RULES grew from 8 to 31 active rules.
- Bidirectional event mesh fully closed: forward rules RI–RN (BBO → cluster/supply agents), reverse rules RO–RR (cluster/parcel agents → spark_signal_agent), opportunity routing RS–RU (signals → opportunity/municipal agents).
- `.claude/` agent-team infrastructure built: 6 agent specs, 3 skill files, 5 hook scripts, settings.json.
- Infrastructure defect found and fixed: hook scripts used relative paths that broke when shell cwd changed to `landos/` subdirectory. All 5 hook commands updated to absolute paths in `.claude/settings.json`.

### Files that changed or were materially advanced
- `landos/src/models/listing.py` (BBO fields added)
- `landos/src/adapters/spark/field_map.py` (BBO_TO_LISTING added)
- `landos/src/adapters/spark/normalizer.py` (BBO field mapping added)
- `landos/src/adapters/spark/bbo_signals.py` (new — 6 detection functions)
- `landos/src/adapters/spark/event_factory.py` (6 BBO event builders added)
- `landos/src/adapters/spark/ingestion.py` (_detect_and_build_bbo_events added)
- `landos/src/triggers/rules/__init__.py` (RI–RU added; ALL_RULES = 31)
- `landos/tests/test_bbo_signals.py` (new — 37 BBO test cases)
- `.claude/settings.json` (hook paths fixed to absolute)
- `.claude/agents/` (6 agent spec files)
- `.claude/skills/` (3 skill files)
- `.claude/hooks/` (5 hook scripts)

### Key decisions locked
- BBO language intelligence is regex-only in Phase 1. LLM remarks pipeline deferred.
- Private remarks never appear in full in event payloads. Excerpt capped at 200 chars.
- One private remarks event per listing with all matched categories in `detected_categories` list.
- `detect_agent_land_accumulation` uses `list_agent_key` (stable UUID), not agent name string.
- Fan-out rules (RN, RU) expressed as separate rules (RN1/RN2, RU1/RU2) because engine does not natively support multi-target fan-out. Semantics preserved.
- Hook commands must use absolute paths. Relative path hook configuration is fragile after any `cd` operation in a Bash tool call.

### Minor gaps noted (non-blocking, carry into Step 6 pre-work)
- No dedicated unit test class for `detect_office_land_program` (agent accumulation tested; office not given its own class).
- RP (`same_owner_listing_detected`) and RR (`parcel_owner_resolved`) reverse rules are wired but not individually name-verified in TestReverseRulesWired (only RO and RQ have explicit assertions).

### Open items at checkpoint
- Two small test additions should be done before Step 6 builder session begins (see pre-Step-6 cleanup in NEXT_STEPS).
- InMemory stores (Listing, Parcel, Owner) still need PostgreSQL replacements before live feed wiring.

### Next exact task
Pre-Step 6 cleanup (small): add `TestOfficeDetection` class and explicit RP/RR assertions to `test_bbo_signals.py`. Then begin Step 6: Cluster Detection.

### Do not drift into
- Step 6 cluster implementation before test cleanup is done
- Municipal scan (Step 7) before cluster (Step 6)
- Database persistence
- Phase 2+ work

---

## 2026-03-09 — Step 6.5: Comprehensive Review + Hardening

### What was completed

- Comprehensive repository review covering architecture, implementation quality, test coverage, and readiness assessment across all 7 test files and all source modules.
- Fixed bug: `detect_market_velocity` referenced nonexistent `l.city` on Listing. Replaced with configurable `geography_field` parameter. 4 new tests added.
- Made `SparkIngestionAdapter` thresholds (`cdom_threshold`, `agent_accumulation_threshold`) into constructor params. Eliminated 80-line brittle subclass hack in integration tests.
- Added `ALL_RULES` uniqueness guard — startup assertion raises `RuntimeError` on duplicate `rule_id` values at import time.
- Documented `_normalize_apn` Phase 1 limitation (global `lstrip("0")` vs per-segment) with production fix path.
- Documented `detect_developer_exit` field precedence and MLS confidence hierarchy rationale.

### Files materially advanced

- `landos/src/adapters/spark/bbo_signals.py` (bug fix + docstring)
- `landos/src/adapters/spark/ingestion.py` (constructor params)
- `landos/src/adapters/regrid/linker.py` (docstring)
- `landos/src/triggers/rules/__init__.py` (uniqueness guard)
- `landos/tests/test_bbo_signals.py` (4 new tests, integration tests simplified)
- `LANDOS_DECISIONS_LOG.md` (5 new decisions)
- `MEMORY.md` (updated)
- `SESSION_HANDOFF_CURRENT.md` (updated)

### Key decisions locked

- SparkIngestionAdapter thresholds must be constructor params.
- ALL_RULES must enforce rule_id uniqueness at import time.
- APN normalization is global lstrip in Phase 1; per-segment deferred to multi-county.
- `detect_developer_exit` field precedence is intentional (MLS confidence hierarchy).
- `detect_market_velocity` uses configurable `geography_field` until Listing gains a city attribute.

### Open items at checkpoint

- InMemory stores need production replacements before live feed wiring.
- Listing model needs a `city` field for proper geography matching.
- APN normalization needs per-segment logic for multi-county.

### Next exact task

Begin Step 7: Municipal Scan — municipality adapter, municipal event builders, `municipality_rule_now_supports_split` derived event, activate PLANNED rule.

### Do not drift into

- Reopening Steps 1–6 unless a defect is found
- Database persistence
- Stallout detection before municipal scan
- Pricing, packaging, UI, or Phase 2+ work

### Task status

Complete — 235/235 tests pass. All documentation updated.

---

## 2026-03-09 — Step 5 Complete

### What was completed
- Completed Step 5: Regrid parcel linkage path. 165/165 tests pass.
- Added `address_raw` and `parcel_number_raw` as Optional fields to the Listing model.
- Added `address_raw` as Optional field to the Parcel model.
- Extended Spark field_map with `UnparsedAddress` → `address_raw` and `ParcelNumber` → `parcel_number_raw`.
- Updated Spark normalizer and event_factory to populate and emit these fields.
- Built `landos/src/adapters/regrid/` (5 files): `field_map.py`, `normalizer.py`, `event_factory.py`, `linker.py`, `ingestion.py`, `__init__.py`.
- Normalizer: Regrid bulk record → Parcel; SkipRecord guards; vacancy inference from improvval/improvcode; centroid construction from lat/lon; municipality linkage via default or lookup.
- Linker (`ParcelListingLinker`): address_match → parcel_number_match → geo_match (haversine 50m threshold) priority chain.
- Event factory: `parcel_linked_to_listing`, `parcel_owner_resolved`, `parcel_score_updated` — all RAW (ingestion adapter is the authoritative origin, matching Step 4 Spark convention).
- Ingestion adapter (`RegridIngestionAdapter`): batch normalize → link → owner resolve → score → emit → route through TriggerEngine; `InMemoryParcelStore` + `InMemoryOwnerStore` for Phase 1.
- Phase 1 scoring model (v0.1_phase1_basic): acreage_signal + vacancy_signal + linkage_signal; materiality gate 0.05.
- Created `landos/src/triggers/rules/parcel_rules.py` with RF, RG, RH.
- Promoted RF from PLANNED_RULES to ALL_RULES. Added RG and RH. ALL_RULES now has 8 active rules.
- 37 new Step 5 tests; 165/165 total pass.

### Files that changed or were materially advanced
- `landos/src/models/listing.py` (address_raw, parcel_number_raw added)
- `landos/src/models/parcel.py` (address_raw added)
- `landos/src/adapters/spark/field_map.py` (UnparsedAddress, ParcelNumber added)
- `landos/src/adapters/spark/normalizer.py` (address_raw, parcel_number_raw mapped)
- `landos/src/adapters/spark/event_factory.py` (listing_added now emits address_raw)
- `landos/src/adapters/regrid/__init__.py` (new)
- `landos/src/adapters/regrid/field_map.py` (new)
- `landos/src/adapters/regrid/normalizer.py` (new)
- `landos/src/adapters/regrid/event_factory.py` (new)
- `landos/src/adapters/regrid/linker.py` (new)
- `landos/src/adapters/regrid/ingestion.py` (new)
- `landos/src/triggers/rules/parcel_rules.py` (new — RF, RG, RH)
- `landos/src/triggers/rules/__init__.py` (RF, RG, RH added to ALL_RULES; PLANNED cleaned)
- `landos/tests/test_regrid_adapter.py` (new — 37 Step 5 test cases)

### Key decisions locked
- Parcel-state events emitted from the ingestion adapter use EventClass.RAW, consistent with Spark adapter convention. DERIVED class applies to downstream agent re-emission only.
- Phase 1 scoring model is v0.1_phase1_basic: acreage (40%) + vacancy (40%) + linkage (20%). No entity resolution in Phase 1 — owner matching is name-normalized string dedup only.
- `address_raw` added to both Listing (from RESO UnparsedAddress) and Parcel (from Regrid address/saddress). This field was always in the architecture; Step 5 is the first point it has data.
- Geo-match uses haversine centroid distance (50m threshold). Shapely polygon intersection deferred to PostGIS wiring.
- InMemoryParcelStore deduplicates on regrid_id. Re-ingesting the same regrid_id produces no events.

### Open items at checkpoint
- InMemoryParcelStore, InMemoryOwnerStore, InMemoryListingStore all need PostgreSQL replacements before live feed wiring.
- Owner entity resolution (LLC graphs, trust beneficiaries) deferred — Phase 1 uses name-normalized string matching only.
- Geo-match polygon intersection (shapely) deferred until PostGIS is wired.
- Municipality linkage from Regrid requires a pre-built lookup dict or default UUID — production wiring deferred.

### Next exact task
Begin Step 6: Cluster detection path — owner/agent/office cluster detection from linked listings and parcels; emit `same_owner_listing_detected`, `owner_cluster_detected`, `owner_cluster_size_threshold_crossed`, `agent_subdivision_program_detected`, `office_inventory_program_detected`; create OwnerCluster objects.

### Do not drift into
- Database or persistence wiring
- Owner entity resolution (LLC graphs) — Step 6 uses name matching only
- Municipal scan (Step 7)
- Stallout detection (Step 8)
- Pricing, packaging, UI, or Phase 2+ work
