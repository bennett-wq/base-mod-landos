# NEXT_STEPS.md — BaseMod LandOS

## Purpose
This file is the practical action list for the immediate next steps of the BaseMod LandOS project.
It should stay short, current, and operational.

---

## Current phase
Phase 0 (documentation spine) complete. Implementation planning complete. Founder decisions resolved. Steps 1-4 complete (128/128 tests pass). Ready for Step 5.

---

## First implementation pass — scope definition

The first coding session builds the Phase 1 signal engine foundation. It covers 10 ordered steps grouped into three tiers: infrastructure, ingestion, and detection. Each step produces observable, testable output before the next step begins.

### Tier 1: Core infrastructure (steps 1–3)
These must be built first. Everything else depends on them.

**Step 1. Canonical event envelope**
- Status: complete. Implemented in the `landos/` Python workspace with local tests passing.
- Implement the canonical event envelope exactly as defined in `LANDOS_EVENT_LIBRARY.md` (envelope section).
- Required fields: `event_id`, `event_type`, `event_family`, `event_class`, `occurred_at`, `observed_at`, `source_system`, `entity_refs`, `payload`, `schema_version`, `status`.
- Optional fields: `source_record_id`, `source_confidence`, `derived_from_event_ids`, `causal_chain_id`, `generation_depth`, `wake_priority`, `routing_class`, `dedupe_key`, `fingerprint_hash`, `emitted_by_agent_run_id`, `ttl`, `created_at`.
- This is a data structure and serialization contract, not a runtime yet.
- Acceptance: an event envelope can be instantiated, serialized, and validated against the schema.

**Step 2. Phase 1 object scaffold**
- Status: complete locally. Object-model files and Step 2 tests exist in the current repo state.
- Implement storage schemas for all 12 Phase 1 objects: Parcel, Listing, Municipality, MunicipalEvent, Owner, OwnerCluster, Subdivision, SiteCondoProject, DeveloperEntity, Opportunity, HomeProduct, SiteFit.
- Implement the 2 lightweight system objects: AgentRun, Action.
- Fields per `LANDOS_OBJECT_MODEL.md`. Required and optional annotations respected. Confidence fields included where specified.
- Acceptance: all 14 objects can be created, persisted, and retrieved with their required fields.

**Step 3. Trigger engine scaffold**
- Status: complete locally. Trigger engine files and Step 3 tests exist in the current repo state.
- Implement the routing engine: receive an event envelope → evaluate trigger rules → dispatch wake instructions.
- The trigger engine must support multi-directional cross-family routing when warranted: listings may wake municipalities and clusters, municipalities may wake parcels and opportunities, clusters may wake municipal scans and listing review, and historical stall signals may wake supply rediscovery — always through explicit trigger rules and guardrails, never through uncontrolled recursion.
- Implement cooldown enforcement, materiality gates, generation-depth hard cap (default: 5), and phase-gating (Phase 2+ rules exist but do not fire).
- Does not need all trigger rules wired — just the engine that evaluates them.
- Acceptance: a test event can be routed through the engine, a matching rule fires, a non-matching rule does not fire, cooldown blocks a duplicate, generation cap stops recursion.

### Tier 2: Ingestion and linkage (steps 4–6)
These connect the system to real-world data and produce the first events.

**Step 4. Spark MLS listing ingestion path**
- Status: complete. Implemented in `landos/src/adapters/spark/`. 128/128 tests pass.
- RESO→Listing field mapping, property-type filter (Michigan land/lot only), and type coercion in normalizer.
- All 5 listing-family raw events emitted with correct identity, payload contracts, and relist dual-emit.
- RE rule (listing_expired → RESCORE) activated from PLANNED_RULES.
- BBO depth follow-up items logged; deferred to post-Step-6 pass.
- Acceptance criteria met: Spark feed data produces Listing objects and listing events flowing through the trigger engine.

**Step 5. Regrid parcel linkage path**
- Map Regrid fields to Parcel object fields.
- Ingest Regrid parcel data for priority Michigan counties.
- Implement parcel-to-listing linkage: address match, parcel number match, geo-match fallback.
- Emit parcel-state events: `parcel_linked_to_listing`, `parcel_owner_resolved`, `parcel_score_updated`.
- Acceptance: listings are matched to parcels; parcel objects are created with geometry, ownership, and zoning fields populated.

**Step 6. Cluster detection path**
- Implement owner/agent/office cluster detection from linked listings and parcels.
- Emit cluster events: `same_owner_listing_detected`, `owner_cluster_detected`, `owner_cluster_size_threshold_crossed`, `agent_subdivision_program_detected`, `office_inventory_program_detected`.
- Acceptance: when multiple listings share an owner, agent, or office, cluster events fire and OwnerCluster objects are created.

### Tier 3: Detection and first fit (steps 7–10)
These produce the first scored opportunities and the first packaging signal.

**Step 7. Municipal scan scaffold**
- Build the municipal scan agent for one priority Michigan municipality (proof of concept).
- Connect to available municipal sources: Register of Deeds, permit system, planning commission minutes (whichever are accessible for the chosen municipality).
- Emit municipal process detection events per `LANDOS_EVENT_LIBRARY.md` municipal_process family.
- LLM extraction from planning commission minutes if available.
- Acceptance: at least one municipality scanned end-to-end; MunicipalEvent objects created; detection events emitted.

**Step 8. Historical stallout detection scaffold**
- Compare historical recorded plats against current parcel vacancy data.
- Assess infrastructure-invested-but-vacant patterns (roads installed + high vacancy ratio).
- Emit: `historical_plat_stall_detected`, `historical_subdivision_stall_detected`.
- Create Opportunity objects (type: `stalled_subdivision`) for detected candidates.
- Acceptance: at least one candidate stalled subdivision identified from historical plat + vacancy data.

**Step 9. Site-condo detection scaffold**
- Scan Register of Deeds for master deed signals.
- Parse legal descriptions for UNIT/CONDOMINIUM/SITE CONDO patterns.
- Assess vacancy ratios for detected site-condo projects.
- Emit: `site_condo_project_detected`, `site_condo_high_vacancy_detected`, `unfinished_site_condo_detected`.
- Create SiteCondoProject objects and Opportunity objects (type: `stalled_site_condo`).
- Acceptance: at least one candidate site-condo project identified from master deed + vacancy data.

**Step 10. First geometry-only SiteFit path**
- Implement geometry fit analysis: given a Parcel and a HomeProduct, determine if the home physically fits (dimensions, shape, setback constraints).
- Emit: `parcel_geometry_fit_detected`, `home_model_fit_detected`, `fit_requires_human_review`.
- No site work estimation. No pricing. Geometry only.
- Acceptance: at least one parcel has been checked against at least one HomeProduct; SiteFit object created with fit result.

---

## Listing remarks classification — scoped deferral

Listing remarks classification (LLM pipeline, Team 4) remains a Phase 1 capability per the architecture docs and the trigger matrix. It is not removed from Phase 1 scope — it is deferred from the first implementation pass only because it depends on a working ingestion pipeline and trigger engine (steps 1–4) to produce useful results. It should be built as the immediate next step after the first implementation pass completes, or in parallel with Tier 3 steps if capacity allows. The Phase 1 architecture, event definitions, and trigger rules for remarks classification are unchanged.

---

## Explicitly out of scope for the first implementation pass

These are real system capabilities that exist in the architecture docs but must not be built yet:

- **Pricing engine** — no SiteWorkEstimate, no PricePackage, no all-in pricing (Phase 2)
- **Marketplace UI** — no buyer-facing browse, no broker search interface (Phase 3)
- **Buyer demand system** — no BuyerProfile, no SavedSearch, no demand-side events (Phase 3+)
- **Incentives execution workflow** — no IncentiveProgram matching, no IncentiveApplication tracking (Phase 2)
- **Transaction orchestration** — no TransactionPath, no ConstructionPath, no lender/contractor matching (Phase 4)
- **Broad source expansion** — no RealComp MLS, no aerial imagery, no ATTOM, no GIS utility layers (Phase 2)

---

## Founder decisions — resolved

1. **Spark MLS access** — Confirmed. RETS/RESO credentials and active feed access available. Step 4 uses the real feed.
2. **Regrid access** — Washtenaw County bulk parcel data already purchased and available. Ottawa and Livingston counties will use Regrid API trial or bulk purchase when ready to expand. No blocker for Step 5.
3. **Priority Michigan counties** — Washtenaw County (first, bulk data in hand), Ottawa County (second), Livingston County (third).
4. **Priority municipality** — Ypsilanti Charter Township (primary proof of concept for Step 7). Augusta Township (secondary). Expand to broader Washtenaw County after the municipal scan agent works end-to-end on one township.
5. **Technology stack** — Python + PostgreSQL (with PostGIS for geospatial support).
6. **Repo folder structure** — Tightened from `CODEX_TASKING.md` recommendation:
   ```
   landos/
     docs/
     src/
       models/
       events/
       triggers/
       agents/
       adapters/
       shared/
     tests/
     data/
     config/
   ```
7. **HomeProduct seed data** — Available. At least one BaseMod home model with real dimensions confirmed. Unblocks Step 10.

All blockers resolved. Steps 1-3 are complete in the current local repo state. Coding continues at Step 4 (Spark MLS listing ingestion path).

---

## What not to do
- Do not deviate from the resolved founder decisions above without explicit founder approval.
- Do not skip Tier 1 infrastructure and jump to ingestion or detection.
- Do not invent new strategy or broaden the architecture.
- Do not create duplicate master docs.
- Do not overbuild UI before the signal engine is real.
- Do not drift away from the Michigan wedge before the first proof exists.
- Do not let chat memory replace file memory.

---

## Current north-star
Build the operating system that turns fragmented land supply into attainable homeownership inventory by mapping signals, waking the right agents, packaging homes that fit, and routing the market toward transaction.
