# LandOS Architectural Decisions Log

## Decision Format
Each entry: [Date] [Decision ID] — Title → Rationale → Status

---

### 2026-03-09 — Live Data Pipeline Session

**D-010: Parcel-first clustering architecture**
Cluster from the 126K parcel dataset (filtered to vacant), NOT from the ~95 MLS listings.
Parcels are the supply intelligence base. Listings are a cross-reference overlay.
→ Rationale: Owner/subdivision/proximity patterns only emerge at parcel scale.
→ Status: LOCKED

**D-011: Vacancy inference via `usedesc` field**
Washtenaw County Regrid data has empty `improvval` and `improvcode` for all records.
Vacancy determined by `usedesc` field: "RESIDENTIAL VACANT", "COMMERCIAL VACANT", etc.
Priority chain: improvval > improvcode > usedesc > UNKNOWN.
→ Rationale: Data availability — usedesc is the only vacancy signal in this county's export.
→ Status: LOCKED

**D-012: Vacant-only CSV filtering at load time**
Filter to `usedesc` containing "VACANT" at CSV read time (`vacant_only=True`).
10,266 vacant parcels from 126,596 total. Don't process improved parcels.
→ Rationale: Performance + signal quality — improved parcels are noise for land supply intelligence.
→ Status: LOCKED

**D-013: Spark RESO OData endpoint**
Correct base URL: `https://replication.sparkapi.com/Reso/OData`
Property endpoint: `{base}/Property` with OData `$filter`, `$top`, `$orderby`.
Auth: `Bearer {SPARK_API_KEY}` header.
→ Rationale: Discovered by trial — `/v1/Property` returns 404, RESO OData is the correct path.
→ Status: LOCKED

**D-014: Three-family parcel cluster detection**
1. **Owner clusters**: Normalized owner name dedup, min 2 parcels
2. **Subdivision clusters**: Regex extraction from `legal_description_raw`, min 3 parcels
3. **Proximity clusters**: Haversine centroid distance, 200m radius greedy, min 3 parcels
Each cluster cross-references against Spark listings via ParcelListingLinker.
→ Rationale: Captures three distinct signal dimensions — ownership consolidation, platted geography, and spatial proximity.
→ Status: LOCKED

**D-015: 5-tier signal scoring system**
- Tier 1 (score ≥ 6): Multi-signal convergence — fatigue + multi-parcel + remarks
- Tier 2 (score 3–5): Owner cluster with listing, some indicators
- Tier 3: Unclustered listings with BBO signals (no parcel cluster match)
- Tier 4: Dormant supply — large owner clusters (10+ lots) without active listings
- Tier 5: Subdivision hot zones — vacant lot concentrations
→ Rationale: Layered intelligence — Tier 1 is actionable now, Tier 4 is strategic pipeline.
→ Status: LOCKED

**D-016: Python 3.9 datetime compatibility**
`datetime.fromisoformat()` in Python 3.9 doesn't handle trailing `Z` (UTC indicator).
Fix: Replace `Z` with `+00:00` before parsing.
→ Rationale: Runtime is Python 3.9; can't rely on 3.11+ ISO 8601 improvements.
→ Status: LOCKED

---

### Pre-session decisions (Steps 1–5, 4.5)

**D-001: Event mesh, not pipeline** — LOCKED
**D-002: InMemory stores only (no DB persistence)** — LOCKED
**D-003: DERIVED event_class requires source_confidence, derived_from_event_ids, emitted_by_agent_run_id** — LOCKED
**D-004: Phase 1 scoring: acreage(40%) + vacancy(40%) + linkage(20%)** — LOCKED
**D-005: Owner matching = name-normalized string dedup (entity resolution deferred)** — LOCKED
**D-006: Geo-match = haversine 50m threshold (Shapely/PostGIS deferred)** — LOCKED
**D-007: BBO Language Intelligence = regex Phase 1 (LLM remarks deferred)** — LOCKED
**D-008: TriggerEngine requires cooldown_tracker=InMemoryCooldownTracker()** — LOCKED
**D-009: RoutingResult fields: event_type, event_id, evaluated_at, fired_rules, suppressed_rules, wake_instructions** — LOCKED
