# BaseMod LandOS — Event Library

> This file defines the typed events the system can emit and respond to.
> It is the canonical reference for what events exist, what data they carry,
> how they are classified, and how they relate to the object model and trigger matrix.

---

## Design principles

1. Events are change; objects are memory. An event records that something meaningful happened. An object records the durable state of a thing.
2. Every event must be classifiable (raw, derived, or compound), routeable (routing_class), and dedupeable (dedupe_key + fingerprint_hash).
3. Raw events come from external reality. Derived events come from system analysis. Compound events come from multiple conditions evaluated together. These three classes have different trust levels, processing rules, and recursion implications.
4. Every event rides inside a canonical envelope. The envelope is the same regardless of event type. The payload varies by event type.
5. Payloads should carry the minimum data needed for the trigger engine to route the event without re-reading the source objects. They should not duplicate entire object states.
6. Events should be named so that their family, subject, and nature are apparent from the name alone.
7. The event library and the trigger matrix are companions: this file defines what events exist and what they carry; the trigger matrix defines what wakes what and under what guardrails.

---

## Relationship between event library events and the MunicipalEvent object

This is an important distinction for both founder and engineer.

**The MunicipalEvent object** (defined in `LANDOS_OBJECT_MODEL.md`) is a durable record stored in the database. It represents a historical municipal action — a plat being recorded, a bond being posted, a road being accepted. It has fields like `event_type`, `occurred_at`, `details`, and it persists forever as part of the municipality's memory.

**Municipal process detection events** in this library (like `plat_recorded_detected`, `bond_posted_detected`) are transient signals that flow through the event mesh. They are emitted *when the system discovers or ingests a MunicipalEvent record*. They trigger downstream wake-ups — parcel rescoring, cluster recomputation, stallout detection.

**The relationship:** Creating or ingesting a MunicipalEvent object causes the system to emit the corresponding `_detected` event into the event mesh. The object is the memory; the event is the signal that the memory changed.

Example flow:
1. A municipal scan agent discovers that a plat was recorded in 2024.
2. The agent creates a MunicipalEvent object with `event_type: plat_recorded`.
3. The system emits a `plat_recorded_detected` event into the mesh.
4. The trigger engine routes that event to parcel rescoring, stallout detection, cluster recomputation, etc.

This is not circular. The MunicipalEvent object is written once and persists. The detection event fires once and triggers downstream work.

---

## Event classification taxonomy

Every event in the system belongs to exactly one of three classes. This classification determines trust level, processing rules, and recursion behavior.

### Raw events
**Definition:** Direct observations of external reality. One external signal produces one raw event. No system computation is required to produce them — only ingestion and normalization.

**Source:** MLS feeds, county parcel records, permit systems, recorded documents, GIS data, manual data entry by operators.

**Trust level:** Confidence comes from the source system, not from system analysis.

**Recursion:** Raw events are always generation_depth = 0. They start causal chains but are never the product of one.

**Examples:** `listing_added`, `listing_status_changed`, `listing_price_reduced`, `plat_recorded_detected`, `permit_pulled_detected`, `incentive_detected`, `human_marked_interesting`.

### Derived events
**Definition:** System conclusions computed from one or more raw events, object states, or other derived events. These are the "intelligence" events — the system looked at data and drew a conclusion.

**Source:** Scoring models, pattern detection, LLM classification, time-based analysis, cross-object comparison.

**Trust level:** Confidence is computed by the system. Must always carry `derived_from_event_ids` linking back to the inputs. Must carry `generation_depth` >= 1.

**Recursion:** Subject to recursion guardrails. A derived event can trigger further derived events, but `generation_depth` must increment and the hard cap must be enforced.

**Examples:** `owner_cluster_detected`, `developer_exit_window_detected`, `historical_plat_stall_detected`, `home_model_fit_detected`, `all_in_price_viable_detected`, `opportunity_created`, `opportunity_score_changed`.

### Compound events
**Definition:** Conditions that require multiple independent signals to be true simultaneously. The trigger matrix references these as combined conditions. A compound event is not a single observation or a single system conclusion — it is an evaluated conjunction.

**Source:** The trigger engine evaluates compound event rules when component events arrive. All component conditions must be satisfied. Component events must share relevant entity_refs (e.g., same parcel, same cluster, same municipality).

**Trust level:** Confidence is the minimum confidence of the component signals.

**Evaluation rules:**
- All component conditions must be met.
- Component events must share at least one entity_ref (parcel_id, cluster_id, municipality_id, or developer_entity_id).
- Component events should have occurred within a configurable time window (default: 90 days unless otherwise specified).
- Compound events always carry `derived_from_event_ids` pointing to all component events.
- `generation_depth` = max(component generation_depths) + 1.

**Examples:** `listing_expired_in_cluster` (listing_expired + owner_cluster membership), `distressed_developer_with_activity` (developer_entity_distress_detected + recent listing activity), `split_ready_parcel` (adequate frontage + adequate acreage + favorable municipality split posture).

---

## Canonical event envelope

Every event in the system is wrapped in this envelope. The envelope is the same for all event types. The `payload` field varies by `event_type`.

### Required fields

- **event_id** — uuid — [required] — system-assigned unique identifier for this event instance. Auto-generated at creation time.
- **event_type** — string — [required] — the specific event name from the catalog below (e.g., `listing_added`, `owner_cluster_detected`). Must exactly match a defined event type.
- **event_family** — string enum — [required] — which family this event belongs to. Allowed values: `listing`, `cluster_owner`, `municipal_process`, `historical_stall`, `developer_exit`, `incentive`, `packaging`, `distribution_demand`, `transaction_execution`, `opportunity_lifecycle`, `parcel_state`, `human_operator`, `system_operational`.
- **event_class** — string enum — [required] — `raw`, `derived`, or `compound`. Determines trust level, recursion rules, and processing behavior.
- **occurred_at** — timestamp (ISO 8601, UTC) — [required] — when the underlying real-world change happened. For historical events, this may be approximate (pair with `occurred_at_precision` in payload if needed).
- **observed_at** — timestamp (ISO 8601, UTC) — [required] — when the system first observed or ingested this signal. Always precise. For real-time feeds, this is close to `occurred_at`. For historical scans, this may be years later.
- **source_system** — string — [required] — which external system or internal process produced this event. Examples: `spark_rets`, `realcomp`, `regrid`, `register_of_deeds`, `permit_system`, `planning_commission_minutes`, `gis`, `manual_entry`, `llm_classifier`, `scoring_engine`, `trigger_engine`, `packaging_agent`.
- **entity_refs** — object — [required] — map of entity type to ID(s) that this event is about. Enables routing and entity-scoped processing. Structure: `{ parcel_id?: uuid, parcel_ids?: uuid[], listing_id?: uuid, municipality_id?: uuid, owner_id?: uuid, cluster_id?: uuid, subdivision_id?: uuid, site_condo_project_id?: uuid, developer_entity_id?: uuid, opportunity_id?: uuid, home_product_id?: uuid }`. At least one reference must be present.
- **payload** — object — [required] — event-type-specific data. Structure varies by `event_type`. Minimum payload shapes are defined per event below.
- **schema_version** — string — [required] — version of the event envelope format. Current: `"1.0"`. Allows future envelope changes without breaking consumers.
- **status** — string enum — [required] — processing state of this event. Allowed values: `pending` (created, not yet processed), `processing` (trigger engine is evaluating), `processed` (all downstream triggers evaluated), `suppressed` (muted by operator or guardrail), `expired` (TTL exceeded before processing), `failed` (processing error).

### Optional fields

- **source_record_id** — string — [optional] — the native ID of the record in the source system (e.g., MLS listing key, county parcel number, permit number). Enables traceability back to external sources.
- **source_confidence** — float (0.0–1.0) — [optional] — how much the system trusts the source. Calibration: 0.9+ = authoritative system of record (MLS, county records); 0.7–0.89 = reliable but may have gaps (GIS, permit feeds); 0.5–0.69 = useful but requires verification (LLM extraction, broker remarks); below 0.5 = speculative. Required for derived and compound events. Optional for raw events from authoritative sources.
- **derived_from_event_ids** — array of uuid — [optional] — the event(s) that this event was computed from. Required for derived and compound events. Empty or absent for raw events.
- **causal_chain_id** — uuid — [optional] — identifier for the chain of events this belongs to. The first raw event in a chain generates a new causal_chain_id. All downstream events in that chain inherit it. Enables full chain tracing for debugging and audit.
- **generation_depth** — integer — [optional] — how deep in the causal chain this event is. Raw events = 0. Each derived layer increments by 1. Hard cap: **5** (configurable). If a derived event would exceed the cap, the system emits a `recursion_limit_reached` event instead of the intended event. Default: 0.
- **wake_priority** — integer (1–10) — [optional] — processing priority. 1 = highest (process immediately), 10 = lowest (batch/background). Maps to the trigger matrix priority hierarchy. Default: 5.
- **routing_class** — string enum — [optional] — controls processing urgency and queue assignment. Allowed values: `immediate` (process within seconds, for high-priority market signals), `standard` (process within minutes, normal operational cadence), `batch` (process in next scheduled batch, for bulk rescoring and recomputation), `background` (process when resources allow, for speculative analysis). Default: `standard`.
- **dedupe_key** — string — [optional] — prevents the same external observation from creating duplicate events. Construction: `{source_system}:{source_record_id}:{event_type}:{occurred_at_date}`. Two events with the same dedupe_key are considered duplicates; the second is dropped.
- **fingerprint_hash** — string — [optional] — content hash of the payload. Prevents two different observations of the same underlying market change from being treated as separate signals. Construction: SHA-256 of the canonicalized (sorted-keys, whitespace-stripped) payload JSON. Two events with different dedupe_keys but the same fingerprint_hash should be evaluated for merge.
- **emitted_by_agent_run_id** — uuid — [optional] — FK to AgentRun. Links this event to the specific agent execution that produced it. Required for derived events. Absent for raw events ingested directly from feeds.
- **ttl** — integer (seconds) — [optional] — time-to-live. If the event has not been processed within this many seconds of `observed_at`, its status transitions to `expired` and it is not processed. Default: 86400 (24 hours). Set shorter for time-sensitive signals (e.g., listing price changes). Set longer or omit for historical scans.
- **created_at** — timestamp (ISO 8601, UTC) — [optional] — when this event record was created in the system. Distinct from `observed_at` (when the signal was noticed) and `occurred_at` (when the real-world change happened). Defaults to now.

---

## Event families and catalog

Events are organized into 13 families. Each event entry includes:
- **Name** — the canonical event_type string
- **Class** — raw, derived, or compound
- **Phase** — when this event is needed (1, 2, or 3+)
- **Description** — one sentence explaining what happened
- **Emitter** — what produces this event
- **Minimum payload** — the fields that must be present in the payload

---

### Family 1: Listing events
**event_family:** `listing`

These events originate from MLS feed ingestion and listing analysis. Listings are the highest-frequency entry point into the system. Every listing event should carry at least `listing_id` in entity_refs.

#### listing_added
- **Class:** raw | **Phase:** 1
- **Description:** A new listing appeared in the MLS feed.
- **Emitter:** MLS ingestion pipeline
- **Minimum payload:**
```
{
  listing_key: string,       // MLS-native listing ID
  list_price: integer,       // asking price in dollars
  property_type: string,     // MLS property type
  acreage: float,            // lot size
  address_raw: string,       // raw address string
  listing_agent_id: string,  // MLS agent ID
  listing_office_id: string  // MLS office ID
}
```

#### listing_status_changed
- **Class:** raw | **Phase:** 1
- **Description:** A listing's status changed (active, pending, closed, withdrawn, expired, canceled).
- **Emitter:** MLS ingestion pipeline
- **Minimum payload:**
```
{
  old_status: string,
  new_status: string,
  close_price: integer | null,  // if closed
  close_date: date | null       // if closed
}
```

#### listing_expired
- **Class:** raw | **Phase:** 1
- **Description:** A listing's status changed to expired. Elevated to its own event because expirations inside clusters are a priority-6 trigger in the wake hierarchy.
- **Emitter:** MLS ingestion pipeline (or derived from `listing_status_changed` where `new_status = expired`)
- **Minimum payload:**
```
{
  original_list_price: integer,
  final_list_price: integer,
  dom: integer,
  cdom: integer,
  cluster_id: uuid | null  // if listing was part of a known cluster
}
```

#### listing_price_reduced
- **Class:** raw | **Phase:** 1
- **Description:** A listing's asking price was lowered.
- **Emitter:** MLS ingestion pipeline
- **Minimum payload:**
```
{
  old_price: integer,
  new_price: integer,
  percent_change: float,
  reduction_count: integer  // how many reductions so far
}
```

#### listing_relisted
- **Class:** raw | **Phase:** 1
- **Description:** A previously expired, withdrawn, or canceled listing reappeared as active.
- **Emitter:** MLS ingestion pipeline
- **Minimum payload:**
```
{
  previous_listing_key: string | null,
  previous_status: string,
  gap_days: integer,  // days between removal and relist
  price_change: integer | null
}
```

#### listing_cdom_threshold_crossed
- **Class:** derived | **Phase:** 1
- **Description:** A listing's cumulative days on market crossed a significant threshold (e.g., 180, 365, 540 days).
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  cdom: integer,
  threshold_crossed: integer,
  list_price: integer,
  price_per_acre: float | null
}
```

#### listing_large_acreage_detected
- **Class:** derived | **Phase:** 1
- **Description:** A listing's acreage exceeds the threshold for land-division analysis (default: 5 acres).
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  acreage: float,
  threshold_acres: float,
  municipality_id: uuid | null,
  split_candidate_flag: boolean | null
}
```

#### listing_package_language_detected
- **Class:** derived | **Phase:** 1
- **Description:** Listing remarks contain language suggesting package/bulk sale opportunity (e.g., "all lots," "remaining inventory," "package deal," "bulk discount").
- **Emitter:** LLM classifier on listing remarks
- **Minimum payload:**
```
{
  matched_phrases: string[],
  remarks_excerpt: string,
  classification_confidence: float
}
```
- **Note:** Formerly named `package_language_detected`. Renamed for naming consistency.

#### listing_fatigue_language_detected
- **Class:** derived | **Phase:** 1
- **Description:** Listing remarks contain language suggesting developer or seller fatigue (e.g., "motivated seller," "bring all offers," "price reduced multiple times").
- **Emitter:** LLM classifier on listing remarks
- **Minimum payload:**
```
{
  matched_phrases: string[],
  remarks_excerpt: string,
  classification_confidence: float
}
```
- **Note:** Formerly named `developer_fatigue_language_detected`. Renamed for naming consistency.

#### listing_restriction_language_detected
- **Class:** derived | **Phase:** 1
- **Description:** Listing remarks contain language about restrictions, covenants, easements, or encumbrances that may affect development feasibility.
- **Emitter:** LLM classifier on listing remarks
- **Minimum payload:**
```
{
  restriction_types: string[],
  remarks_excerpt: string,
  classification_confidence: float
}
```
- **Note:** Formerly named `restriction_language_detected`. Renamed for naming consistency.

#### listing_approval_language_detected
- **Class:** derived | **Phase:** 1
- **Description:** Listing remarks mention approvals, entitlements, or permits already obtained.
- **Emitter:** LLM classifier on listing remarks
- **Minimum payload:**
```
{
  approval_types: string[],
  remarks_excerpt: string,
  classification_confidence: float
}
```
- **Note:** Formerly named `approval_language_detected`. Renamed for naming consistency.

#### listing_utility_language_detected
- **Class:** derived | **Phase:** 1
- **Description:** Listing remarks contain information about utility availability, connections, or requirements.
- **Emitter:** LLM classifier on listing remarks
- **Minimum payload:**
```
{
  utility_mentions: string[],
  remarks_excerpt: string,
  classification_confidence: float
}
```
- **Note:** Formerly named `utility_language_detected`. Renamed for naming consistency.

#### listing_broker_note_required
- **Class:** derived | **Phase:** 2
- **Description:** A listing has characteristics that warrant deeper broker intelligence extraction — the automated signals are insufficient and a BrokerNote should be created.
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  reason: string,
  priority: string  // high, medium, low
}
```

#### listing_cluster_expansion_required
- **Class:** derived | **Phase:** 1
- **Description:** A listing's owner, agent, or office pattern suggests it may belong to an undiscovered or under-explored cluster.
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  expansion_reason: string,  // same_owner, same_agent, same_office, geographic_proximity
  candidate_entity_id: string
}
```

#### listing_municipal_scan_required
- **Class:** derived | **Phase:** 1
- **Description:** A listing is in a municipality that has not been recently scanned, or the listing signals suggest municipal context is needed.
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  reason: string,
  municipality_id: uuid,
  last_scan_at: timestamp | null
}
```

#### listing_incentive_scan_required
- **Class:** derived | **Phase:** 2
- **Description:** A listing is in a geography or category where incentive programs may apply but have not been checked.
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  reason: string,
  municipality_id: uuid
}
```

#### listing_market_shock_candidate_detected
- **Class:** derived | **Phase:** 1
- **Description:** A listing exhibits characteristics that suggest a significant market event — extreme price drop, sudden bulk availability, or unusual listing pattern.
- **Emitter:** Listing analysis agent
- **Minimum payload:**
```
{
  shock_type: string,
  severity: string,  // high, medium
  details: string
}
```

---

### Family 2: Cluster / owner events
**event_family:** `cluster_owner`

These events relate to the detection and analysis of ownership patterns, agent programs, and multi-parcel relationships. Clusters are multiplicative pattern expanders — detecting one can unlock many parcels.

#### same_owner_listing_detected
- **Class:** derived | **Phase:** 1
- **Description:** Two or more active listings share the same owner (by name match, entity resolution, or parcel owner records).
- **Emitter:** Owner resolution agent
- **Minimum payload:**
```
{
  owner_id: uuid,
  listing_ids: uuid[],
  parcel_ids: uuid[],
  match_method: string  // name_exact, name_fuzzy, entity_resolution, parcel_owner
}
```

#### owner_cluster_detected
- **Class:** derived | **Phase:** 1
- **Description:** A new OwnerCluster has been identified — a group of related parcels/listings sharing ownership, agent, or office patterns.
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  cluster_id: uuid,
  cluster_type: string,  // same_owner, same_agent, same_office, geographic
  member_count: integer,
  parcel_ids: uuid[],
  listing_ids: uuid[]
}
```

#### owner_cluster_size_threshold_crossed
- **Class:** derived | **Phase:** 1
- **Description:** An existing cluster grew past a significance threshold (e.g., 3+ lots, 5+ lots, 10+ lots).
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  cluster_id: uuid,
  old_size: integer,
  new_size: integer,
  threshold_crossed: integer
}
```

#### agent_subdivision_program_detected
- **Class:** derived | **Phase:** 1
- **Description:** A single listing agent is systematically marketing multiple lots within the same subdivision or geographic cluster — suggesting a coordinated sell-off program.
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  agent_id: string,
  listing_ids: uuid[],
  subdivision_id: uuid | null,
  lot_count: integer
}
```

#### office_inventory_program_detected
- **Class:** derived | **Phase:** 1
- **Description:** A single listing office is running a coordinated multi-lot inventory program.
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  office_id: string,
  listing_ids: uuid[],
  lot_count: integer
}
```

#### cluster_municipal_scan_required
- **Class:** derived | **Phase:** 1
- **Description:** A cluster has been detected or expanded in a municipality that needs scanning.
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  cluster_id: uuid,
  municipality_id: uuid,
  reason: string
}
```

#### cluster_broker_note_required
- **Class:** derived | **Phase:** 2
- **Description:** A cluster has characteristics that warrant broker intelligence — automated signals are insufficient.
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  cluster_id: uuid,
  reason: string,
  priority: string
}
```

---

### Family 3: Municipal process events
**event_family:** `municipal_process`

These events are emitted when the system discovers or ingests a durable MunicipalEvent record. See the "Relationship between event library events and the MunicipalEvent object" section above for how these relate to the MunicipalEvent object in the object model. Each event below corresponds to one or more `event_type` values on the MunicipalEvent object.

All municipal process detection events are **raw** when discovered from authoritative records (register of deeds, planning commission minutes, permit systems) or **derived** when inferred from indirect signals (LLM extraction from meeting minutes, aerial analysis, pattern detection). The `source_system` field on the envelope distinguishes the two.

#### site_plan_approved_detected
- **Class:** raw | **Phase:** 1
- **Description:** A site plan approval was discovered in municipal records.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  project_name: string | null,
  approval_body: string | null,
  lot_count: integer | null
}
```

#### plat_recorded_detected
- **Class:** raw | **Phase:** 1
- **Description:** A recorded plat was discovered in county/municipal records.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  plat_name: string | null,
  total_lots: integer | null,
  recording_date: date | null
}
```

#### engineering_approved_detected
- **Class:** raw | **Phase:** 1
- **Description:** Engineering plan approval was discovered.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  project_name: string | null
}
```

#### permit_pulled_detected
- **Class:** raw | **Phase:** 1
- **Description:** A building permit was pulled.
- **Emitter:** Permit system ingestion or municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  permit_number: string | null,
  permit_type: string | null,
  valuation: integer | null
}
```

#### permits_pulled_majority_vacant_detected
- **Class:** derived | **Phase:** 1
- **Description:** Permits were pulled in a subdivision/project but the majority of lots remain vacant — suggesting a stall after initial activity.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  subdivision_id: uuid | null,
  site_condo_project_id: uuid | null,
  total_lots: integer,
  permitted_lots: integer,
  vacant_lots: integer,
  vacancy_ratio: float
}
```

#### approved_no_vertical_progress_detected
- **Class:** derived | **Phase:** 1
- **Description:** A project received approvals (site plan, engineering, plat) but no vertical construction followed within a significant time window.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  approval_type: string,
  approval_date: date,
  years_since_approval: float,
  vertical_progress_detected: boolean
}
```

#### roads_installed_detected
- **Class:** raw | **Phase:** 1
- **Description:** Road infrastructure installation was detected in a subdivision or project area.
- **Emitter:** Municipal scan agent or GIS analysis
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  road_names: string[] | null,
  linear_feet: float | null
}
```

#### roads_accepted_detected
- **Class:** raw | **Phase:** 1
- **Description:** Roads were formally accepted by the municipality (transferred from developer to public maintenance).
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  acceptance_date: date | null
}
```

#### roads_installed_majority_vacant_detected
- **Class:** derived | **Phase:** 1
- **Description:** Roads are installed but the majority of lots they serve remain vacant — a strong stallout signal and priority-2 in the wake hierarchy.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  subdivision_id: uuid | null,
  site_condo_project_id: uuid | null,
  total_lots: integer,
  vacant_lots: integer,
  vacancy_ratio: float,
  road_installation_date: date | null
}
```

#### public_sewer_extension_detected
- **Class:** raw | **Phase:** 1
- **Description:** Public sewer infrastructure was extended into an area, potentially unlocking parcels for development.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  extension_area: string | null
}
```

#### water_extension_detected
- **Class:** raw | **Phase:** 1
- **Description:** Public water infrastructure was extended into an area.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  extension_area: string | null
}
```

#### bond_posted_detected
- **Class:** raw | **Phase:** 1
- **Description:** A performance or completion bond was posted for a development project.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  bond_amount: integer | null,
  bond_type: string | null,
  expiration_date: date | null
}
```

#### bond_extension_detected
- **Class:** raw | **Phase:** 1
- **Description:** A development bond's expiration was extended — often signals ongoing stall.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  original_expiration: date | null,
  new_expiration: date | null,
  extension_count: integer | null
}
```

#### bond_released_detected
- **Class:** raw | **Phase:** 1
- **Description:** A development bond was released — signals either that conditions were met or that the bond lapsed. Corresponds to MunicipalEvent type `bond_released`.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  release_date: date | null,
  conditions_met: string | null
}
```

#### bond_release_delay_detected
- **Class:** derived | **Phase:** 1
- **Description:** A bond that should have been released (conditions met) has not been — may indicate administrative delay or unresolved issues.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  expected_release_date: date | null,
  delay_days: integer
}
```

#### bond_posted_no_progress_detected
- **Class:** derived | **Phase:** 1
- **Description:** A bond was posted but no meaningful development progress followed — priority-5 in the wake hierarchy.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  bond_amount: integer | null,
  bond_date: date | null,
  years_since_bond: float,
  progress_indicators: string[]
}
```

#### hoa_created_detected
- **Class:** raw | **Phase:** 1
- **Description:** An HOA or property owners association was created for a project.
- **Emitter:** Municipal scan agent or deed analysis
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  hoa_name: string | null,
  developer_control_flag: boolean | null
}
```

#### master_deed_recorded_detected
- **Class:** raw | **Phase:** 1
- **Description:** A master deed (condominium or site condo) was recorded — signals a site-condo regime.
- **Emitter:** Register of deeds scan or municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  project_name: string | null,
  total_units: integer | null,
  recording_date: date | null
}
```

#### site_condo_regime_detected
- **Class:** derived | **Phase:** 1
- **Description:** A site-condo regime was identified through legal description analysis, master deed discovery, or MLS field patterns.
- **Emitter:** Site-condo detection agent
- **Minimum payload:**
```
{
  site_condo_project_id: uuid,
  detection_method: string,
  total_units: integer | null,
  vacant_units: integer | null
}
```

#### developer_control_active_detected
- **Class:** derived | **Phase:** 1
- **Description:** A developer still holds control of an HOA or condo association — the project has not been turned over to owners.
- **Emitter:** Municipal scan agent or deed analysis
- **Minimum payload:**
```
{
  developer_entity_id: uuid | null,
  hoa_name: string | null,
  years_under_developer_control: float | null
}
```

#### hoa_exists_majority_vacant_detected
- **Class:** derived | **Phase:** 1
- **Description:** An HOA exists but the majority of lots/units remain vacant — priority-9 in the wake hierarchy. Suggests incomplete buildout with organizational structure already in place.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  hoa_name: string | null,
  total_units: integer,
  vacant_units: integer,
  vacancy_ratio: float
}
```

#### municipality_rule_change_detected
- **Class:** raw | **Phase:** 1
- **Description:** A municipal rule change was discovered from authoritative records (ordinance text, planning commission minutes, zoning amendments). This is the raw factual discovery — the system has not yet evaluated whether it favors land division.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  municipal_event_id: uuid,
  rule_type: string,
  old_value: string | null,
  new_value: string | null,
  effective_date: date | null
}
```

#### municipality_rule_now_supports_split
- **Class:** derived | **Phase:** 1
- **Description:** The system concluded that a discovered rule change now supports land division — derived from evaluating `municipality_rule_change_detected`. Priority-4 in the wake hierarchy. This is a policy shockwave that can reprice every qualifying parcel in the jurisdiction.
- **Emitter:** Municipal intelligence agent
- **Minimum payload:**
```
{
  rule_type: string,  // zoning_amendment, ordinance_change, section_108_6_authorization
  old_posture: string | null,
  new_posture: string,
  effective_date: date | null,
  affected_parcel_estimate: integer | null
}
```

#### municipality_split_capacity_increased
- **Class:** derived | **Phase:** 1
- **Description:** A municipality's effective capacity for new land divisions increased — through rule changes, infrastructure extensions, or policy shifts.
- **Emitter:** Municipal intelligence agent
- **Minimum payload:**
```
{
  capacity_driver: string,
  details: string
}
```

#### municipality_frontage_rules_favorable_detected
- **Class:** derived | **Phase:** 1
- **Description:** A municipality's minimum frontage requirements are favorable enough to support practical land division of existing large parcels.
- **Emitter:** Municipal intelligence agent
- **Minimum payload:**
```
{
  minimum_frontage_feet: float,
  comparison_to_region: string  // below_average, average, above_average
}
```

#### municipality_permit_activity_increased
- **Class:** derived | **Phase:** 1
- **Description:** Building permit activity in a municipality increased significantly — signals growing development momentum.
- **Emitter:** Municipal intelligence agent
- **Minimum payload:**
```
{
  period: string,
  permit_count: integer,
  percent_change: float,
  comparison_period: string
}
```

#### municipality_infrastructure_extension_detected
- **Class:** raw | **Phase:** 1
- **Description:** Municipal infrastructure (sewer, water, roads) was extended into a previously unserved or underserved area.
- **Emitter:** Municipal scan agent
- **Minimum payload:**
```
{
  infrastructure_type: string,  // sewer, water, road
  extension_area: string | null,
  affected_parcel_estimate: integer | null
}
```

#### municipality_incentive_program_detected
- **Class:** raw | **Phase:** 2
- **Description:** A municipality created or announced an incentive program relevant to housing development.
- **Emitter:** Municipal intelligence agent or manual entry
- **Minimum payload:**
```
{
  program_name: string,
  program_type: string,
  eligibility_summary: string | null
}
```

#### municipality_subdivision_stagnation_pattern_detected
- **Class:** derived | **Phase:** 1
- **Description:** A municipality-wide pattern of subdivision stagnation was identified — multiple projects stalled, high aggregate vacancy across platted lots.
- **Emitter:** Municipal intelligence agent
- **Minimum payload:**
```
{
  stalled_subdivision_count: integer,
  total_vacant_lots: integer,
  aggregate_vacancy_ratio: float
}
```

---

### Family 4: Historical stall / site-condo events
**event_family:** `historical_stall`

These events come from forensic analysis of historical records — comparing what was platted or approved years ago against what actually got built. This is a strategic supply wedge that finds opportunity invisible to live-market-only views.

#### historical_plat_stall_detected
- **Class:** derived | **Phase:** 1
- **Description:** A recorded plat from 5+ years ago has lots that remain vacant — the subdivision was started but never completed.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  subdivision_id: uuid | null,
  plat_name: string,
  plat_recording_date: date,
  total_lots: integer,
  vacant_lots: integer,
  vacancy_ratio: float,
  years_since_plat: float
}
```

#### historical_subdivision_stall_detected
- **Class:** derived | **Phase:** 1
- **Description:** A subdivision shows multiple stall signals — plat recorded, infrastructure invested, but persistent vacancy across lots.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  subdivision_id: uuid,
  stall_signals: string[],  // plat_recorded, roads_installed, bonds_posted, permits_pulled, etc.
  vacancy_ratio: float,
  years_since_activity: float,
  stall_confidence: float
}
```

#### site_condo_project_detected
- **Class:** derived | **Phase:** 1
- **Description:** A site-condo project was identified through master deed analysis, legal description patterns, or MLS field detection.
- **Emitter:** Site-condo detection agent
- **Minimum payload:**
```
{
  site_condo_project_id: uuid,
  detection_method: string,  // master_deed_scan, legal_description_pattern, mls_field, manual
  total_units: integer | null,
  project_name: string | null
}
```

#### site_condo_high_vacancy_detected
- **Class:** derived | **Phase:** 1
- **Description:** A known site-condo project has a high vacancy ratio — significant remaining inventory.
- **Emitter:** Site-condo detection agent
- **Minimum payload:**
```
{
  site_condo_project_id: uuid,
  total_units: integer,
  vacant_units: integer,
  vacancy_ratio: float,
  age_years: float
}
```

#### partial_buildout_stagnation_detected
- **Class:** derived | **Phase:** 1
- **Description:** A subdivision or project has some completed homes but remaining lots are stagnant — partial buildout with no recent progress.
- **Emitter:** Stallout detection agent
- **Minimum payload:**
```
{
  subdivision_id: uuid | null,
  site_condo_project_id: uuid | null,
  total_lots: integer,
  built_lots: integer,
  vacant_lots: integer,
  years_since_last_build: float
}
```
- **Note:** Formerly named `improved_subdivision_stagnation_detected`. Renamed for clarity.

#### unfinished_site_condo_detected
- **Class:** derived | **Phase:** 1
- **Description:** A site-condo project was identified as unfinished — master deed recorded, units platted, but significant vacancy persists.
- **Emitter:** Site-condo detection agent
- **Minimum payload:**
```
{
  site_condo_project_id: uuid,
  total_units: integer,
  vacant_units: integer,
  vacancy_ratio: float,
  age_years: float
}
```

---

### Family 5: Developer / exit-window events
**event_family:** `developer_exit`

These events detect when a developer has shifted from value-maximizing buildout to inventory monetization. Developer intent is inferred behaviorally, not from financial distress data.

#### developer_entity_distress_detected
- **Class:** derived | **Phase:** 1
- **Description:** A developer entity shows multiple behavioral distress signals — long hold times, price drift, repeated relists, reduced investment.
- **Emitter:** Developer analysis agent
- **Minimum payload:**
```
{
  developer_entity_id: uuid,
  distress_signals: string[],
  distress_confidence: float
}
```

#### remaining_inventory_program_detected
- **Class:** derived | **Phase:** 1
- **Description:** A developer appears to be running a remaining-inventory liquidation program — marketing remaining lots as a group.
- **Emitter:** Cluster detection agent or LLM classifier
- **Minimum payload:**
```
{
  developer_entity_id: uuid | null,
  cluster_id: uuid | null,
  remaining_lot_count: integer,
  program_indicators: string[]
}
```

#### coordinated_broker_liquidation_detected
- **Class:** derived | **Phase:** 1
- **Description:** A broker or office is running a coordinated liquidation of a developer's remaining inventory.
- **Emitter:** Cluster detection agent
- **Minimum payload:**
```
{
  agent_id: string | null,
  office_id: string | null,
  developer_entity_id: uuid | null,
  listing_ids: uuid[],
  lot_count: integer
}
```

#### subdivision_sellout_strategy_detected
- **Class:** derived | **Phase:** 1
- **Description:** A subdivision's remaining lots are being marketed with sellout-strategy signals — package pricing, bulk discounts, accelerated timeline language.
- **Emitter:** LLM classifier or cluster detection agent
- **Minimum payload:**
```
{
  subdivision_id: uuid,
  strategy_signals: string[],
  remaining_lot_count: integer,
  confidence: float
}
```

#### developer_exit_window_detected
- **Class:** derived | **Phase:** 1
- **Description:** The convergence of multiple signals suggests a developer is in an exit window — ready to sell remaining inventory at a discount or in bulk.
- **Emitter:** Developer analysis agent
- **Minimum payload:**
```
{
  developer_entity_id: uuid,
  exit_signals: string[],
  cluster_id: uuid | null,
  subdivision_id: uuid | null,
  remaining_lot_count: integer,
  exit_confidence: float
}
```

#### broker_signaled_bulk_flexibility_detected
- **Class:** derived | **Phase:** 2
- **Description:** A broker's remarks or behavior indicate willingness to negotiate bulk or package deals.
- **Emitter:** LLM classifier on broker remarks or BrokerNote extraction
- **Minimum payload:**
```
{
  listing_id: uuid | null,
  cluster_id: uuid | null,
  flexibility_signals: string[],
  confidence: float
}
```

---

### Family 6: Incentive events
**event_family:** `incentive`

These events track the discovery, matching, and application lifecycle of government or institutional incentive programs.

#### incentive_detected
- **Class:** raw | **Phase:** 2
- **Description:** A new incentive program was discovered (tax abatement, grant, density bonus, infrastructure subsidy, etc.).
- **Emitter:** Incentives agent or manual entry
- **Minimum payload:**
```
{
  incentive_program_id: uuid,
  program_name: string,
  program_type: string,
  jurisdiction: string
}
```

#### incentive_potential_match_detected
- **Class:** derived | **Phase:** 2
- **Description:** An incentive program was identified as potentially applicable to a specific opportunity.
- **Emitter:** Incentives matching agent
- **Minimum payload:**
```
{
  incentive_program_id: uuid,
  opportunity_id: uuid,
  match_confidence: float,
  estimated_value: integer | null
}
```

#### incentive_application_required
- **Class:** derived | **Phase:** 2
- **Description:** An incentive match is strong enough to warrant preparing and submitting an application.
- **Emitter:** Incentives matching agent
- **Minimum payload:**
```
{
  incentive_program_id: uuid,
  opportunity_id: uuid,
  deadline: date | null
}
```

#### incentive_deadline_upcoming
- **Class:** derived | **Phase:** 2
- **Description:** An incentive application deadline is approaching.
- **Emitter:** Scheduling system
- **Minimum payload:**
```
{
  incentive_program_id: uuid,
  deadline: date,
  days_remaining: integer
}
```

#### incentive_paperwork_started
- **Class:** raw | **Phase:** 2
- **Description:** Work on an incentive application has begun.
- **Emitter:** Manual entry or task system
- **Minimum payload:**
```
{
  incentive_application_id: uuid,
  started_by: string
}
```

#### incentive_paperwork_completed
- **Class:** raw | **Phase:** 2
- **Description:** An incentive application has been completed and submitted.
- **Emitter:** Manual entry or task system
- **Minimum payload:**
```
{
  incentive_application_id: uuid,
  submitted_date: date
}
```

#### incentive_award_confirmed
- **Class:** raw | **Phase:** 2
- **Description:** An incentive was awarded — confirmed value is known.
- **Emitter:** Manual entry
- **Minimum payload:**
```
{
  incentive_application_id: uuid,
  awarded_value: integer,
  terms_summary: string | null
}
```

---

### Family 7: Packaging events
**event_family:** `packaging`

These events track the process of turning raw land opportunity into a buyer-legible land+home package. Packaging is a first-class system layer — not an afterthought.

#### parcel_geometry_fit_detected
- **Class:** derived | **Phase:** 1
- **Description:** A parcel's geometry (dimensions, shape, area) can physically accommodate one or more BaseMod home models.
- **Emitter:** Packaging agent (geometry analysis)
- **Minimum payload:**
```
{
  parcel_id: uuid,
  fitting_home_product_ids: uuid[],
  fit_method: string  // geometry_calculation, manual_review
}
```

#### home_model_fit_detected
- **Class:** derived | **Phase:** 1
- **Description:** A specific HomeProduct was confirmed as fitting a specific Parcel — a SiteFit analysis was completed.
- **Emitter:** Packaging agent
- **Minimum payload:**
```
{
  site_fit_id: uuid,
  parcel_id: uuid,
  home_product_id: uuid,
  fit_result: string,  // fits, marginal, does_not_fit, insufficient_data
  fit_confidence: float
}
```

#### utility_assumption_confident_detected
- **Class:** derived | **Phase:** 1
- **Description:** Utility availability for a parcel has been assessed with sufficient confidence to proceed with pricing.
- **Emitter:** Packaging agent (utility analysis)
- **Minimum payload:**
```
{
  parcel_id: uuid,
  utility_overall_status: string,
  utility_confidence: float
}
```

#### site_work_estimate_completed
- **Class:** derived | **Phase:** 2
- **Description:** A site work cost estimate has been completed for a specific parcel+home combination.
- **Emitter:** Packaging agent
- **Minimum payload:**
```
{
  site_work_estimate_id: uuid,
  parcel_id: uuid,
  home_product_id: uuid,
  total_estimate: integer,
  confidence: float
}
```

#### all_in_price_viable_detected
- **Class:** derived | **Phase:** 2
- **Description:** An all-in price (land + home + site work + fees) was calculated and falls within a viable range for the target market.
- **Emitter:** Packaging agent
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  price_package_id: uuid,
  all_in_low: integer,
  all_in_high: integer,
  land_cost: integer,
  home_cost: integer,
  site_work_estimate: integer
}
```

#### package_ready_for_distribution
- **Class:** derived | **Phase:** 2
- **Description:** A complete land+home package is ready to be shown to buyers, brokers, or sellers. All major components (fit, pricing, feasibility) are in place.
- **Emitter:** Packaging agent
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  parcel_ids: uuid[],
  home_product_ids: uuid[],
  price_range_low: integer,
  price_range_high: integer,
  municipality_id: uuid,
  feasibility_confidence: float
}
```

#### fit_requires_human_review
- **Class:** derived | **Phase:** 1
- **Description:** An automated fit assessment (SiteFit, utility analysis, or pricing) could not reach sufficient confidence and requires human review.
- **Emitter:** Packaging agent
- **Minimum payload:**
```
{
  review_subject: string,  // site_fit, utility, pricing, zoning
  parcel_id: uuid,
  home_product_id: uuid | null,
  reason: string,
  current_confidence: float
}
```

---

### Family 8: Distribution / demand events
**event_family:** `distribution_demand`

These events track buyer and broker interest, seller engagement, and opportunity distribution. Phase 3+ for most, but some early signals may appear in Phase 2.

#### buyer_search_profile_created
- **Class:** raw | **Phase:** 3+
- **Description:** A buyer created a search profile expressing their preferences and budget.
- **Emitter:** Marketplace platform
- **Minimum payload:**
```
{
  buyer_profile_id: uuid,
  budget_range: { low: integer, high: integer },
  geography_preferences: string[]
}
```

#### buyer_search_matches_opportunity
- **Class:** derived | **Phase:** 3+
- **Description:** A buyer's search profile matches a packaged opportunity.
- **Emitter:** Matching engine
- **Minimum payload:**
```
{
  buyer_profile_id: uuid,
  opportunity_id: uuid,
  match_score: float
}
```

#### broker_saved_search_created
- **Class:** raw | **Phase:** 3+
- **Description:** A broker created a saved search for land+home opportunities matching client criteria.
- **Emitter:** Marketplace platform
- **Minimum payload:**
```
{
  broker_profile_id: uuid,
  search_criteria: object
}
```

#### broker_interest_detected
- **Class:** derived | **Phase:** 2
- **Description:** A broker expressed interest in a specific opportunity or geography through platform engagement signals.
- **Emitter:** Marketplace platform or manual entry
- **Minimum payload:**
```
{
  broker_profile_id: uuid | null,
  opportunity_id: uuid | null,
  interest_signal: string  // viewed, saved, inquired, requested_info
}
```

#### seller_engagement_started
- **Class:** raw | **Phase:** 2
- **Description:** Contact has been initiated with a seller or their representative.
- **Emitter:** Outreach system or manual entry
- **Minimum payload:**
```
{
  owner_id: uuid,
  contact_method: string,  // email, phone, mail, agent_contact
  opportunity_id: uuid | null
}
```

#### seller_ready_to_transact
- **Class:** derived | **Phase:** 2
- **Description:** A seller has indicated willingness to transact at terms that could work.
- **Emitter:** Manual entry or outreach system
- **Minimum payload:**
```
{
  owner_id: uuid,
  parcel_ids: uuid[],
  asking_range: { low: integer, high: integer } | null,
  terms_flexibility: string | null
}
```

#### opportunity_ready_for_distribution
- **Class:** derived | **Phase:** 2
- **Description:** An opportunity has been fully packaged and is ready to be exposed to the marketplace.
- **Emitter:** Packaging agent
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  distribution_channels: string[]  // marketplace, broker_network, direct_buyer, mls
}
```

---

### Family 9: Transaction / execution events
**event_family:** `transaction_execution`

These events track the progression from packaged opportunity to executed housing outcome. Phase 3+ for all.

#### site_feasibility_confirmed
- **Class:** derived | **Phase:** 3+
- **Description:** Site feasibility has been independently confirmed — beyond the automated SiteFit, this may include site visits, soil tests, survey results.
- **Emitter:** Manual entry or field verification system
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  confirmation_method: string,
  confirmed_by: string
}
```

#### buyer_ready_to_proceed
- **Class:** raw | **Phase:** 3+
- **Description:** A buyer has expressed intent to proceed with a specific opportunity.
- **Emitter:** Marketplace platform or manual entry
- **Minimum payload:**
```
{
  buyer_profile_id: uuid,
  opportunity_id: uuid,
  financing_method: string | null
}
```

#### lender_path_available
- **Class:** derived | **Phase:** 3+
- **Description:** A financing path has been identified for a specific opportunity — lender, product type, and preliminary terms.
- **Emitter:** Financing analysis or manual entry
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  lender: string | null,
  loan_type: string,
  preliminary_terms: object | null
}
```

#### contractor_path_available
- **Class:** derived | **Phase:** 3+
- **Description:** A construction contractor has been identified who can execute the home installation for a specific opportunity.
- **Emitter:** Construction coordination system or manual entry
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  contractor_name: string | null,
  estimated_timeline_weeks: integer | null
}
```

#### orderable_package_created
- **Class:** derived | **Phase:** 3+
- **Description:** All components are in place for a buyer to order — land, home, site work, financing, contractor, timeline. This is the final convergence event before transaction execution.
- **Emitter:** Transaction coordination agent
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  buyer_profile_id: uuid | null,
  all_in_price: integer,
  estimated_timeline_weeks: integer
}
```

---

### Family 10: Opportunity lifecycle events
**event_family:** `opportunity_lifecycle`

These events track the lifecycle of the Opportunity object — the system's central convergence point. Every significant status transition should emit an event so the rest of the system can react.

#### opportunity_created
- **Class:** derived | **Phase:** 1
- **Description:** A new Opportunity was created — enough supply signals converged to identify an actionable prospect.
- **Emitter:** Opportunity detection agent
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  opportunity_type: string,  // stranded_lot, stalled_subdivision, stalled_site_condo, land_division_candidate, developer_exit, infill, other
  parcel_ids: uuid[],
  municipality_id: uuid,
  triggering_signals: string[]
}
```

#### opportunity_score_changed
- **Class:** derived | **Phase:** 1
- **Description:** An Opportunity's composite score changed materially — new signals, new municipal context, or new market data altered the assessment.
- **Emitter:** Scoring engine
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  old_score: float | null,
  new_score: float,
  score_delta: float,
  change_drivers: string[]  // what caused the change
}
```

#### opportunity_status_changed
- **Class:** derived | **Phase:** 1
- **Description:** An Opportunity transitioned between lifecycle states (detected, scored, fit_checked, packaged, distributed, engaged, converted, rejected, stale).
- **Emitter:** Various agents depending on the transition
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  old_status: string,
  new_status: string,
  reason: string | null
}
```

#### opportunity_rejected
- **Class:** derived | **Phase:** 1
- **Description:** An Opportunity was rejected — determined not viable after analysis.
- **Emitter:** Packaging agent, human operator, or scoring engine
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  rejection_reason: string,
  rejected_by: string  // agent_type or operator_id
}
```

#### opportunity_stale
- **Class:** derived | **Phase:** 1
- **Description:** An Opportunity has had no meaningful activity or signal updates for a configurable period — it may need rescan or archiving.
- **Emitter:** Scheduling system or staleness detector
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  last_activity_at: timestamp,
  days_inactive: integer
}
```

---

### Family 11: Parcel state-change events
**event_family:** `parcel_state`

These events track meaningful state changes on the Parcel object — the atomic unit of land supply.

#### parcel_linked_to_listing
- **Class:** derived | **Phase:** 1
- **Description:** A Parcel was successfully linked to a Listing — the system resolved the relationship between a market offering and its underlying land.
- **Emitter:** Parcel-listing linkage agent
- **Minimum payload:**
```
{
  parcel_id: uuid,
  listing_id: uuid,
  linkage_method: string  // address_match, parcel_number_match, geo_match, manual
}
```

#### parcel_owner_resolved
- **Class:** derived | **Phase:** 1
- **Description:** A Parcel's owner was identified or updated — the system resolved who owns this land.
- **Emitter:** Owner resolution agent
- **Minimum payload:**
```
{
  parcel_id: uuid,
  owner_id: uuid,
  resolution_method: string  // county_records, mls_seller, entity_resolution, manual
}
```

#### parcel_score_updated
- **Class:** derived | **Phase:** 1
- **Description:** A Parcel's opportunity score was recalculated — triggered by new signals, municipal changes, or model updates.
- **Emitter:** Scoring engine
- **Minimum payload:**
```
{
  parcel_id: uuid,
  old_score: float | null,
  new_score: float,
  score_delta: float,
  trigger_reason: string
}
```

#### parcel_vacancy_confirmed
- **Class:** derived | **Phase:** 1
- **Description:** A Parcel's vacancy status was confirmed or changed through aerial analysis, permit records, or field verification.
- **Emitter:** Vacancy detection agent or manual entry
- **Minimum payload:**
```
{
  parcel_id: uuid,
  vacancy_status: string,  // vacant, improved, partially_improved
  confirmation_method: string,  // aerial, permit_records, field_visit, assessor_data
  confidence: float
}
```

#### parcel_split_candidate_identified
- **Class:** derived | **Phase:** 1
- **Description:** A Parcel was identified as a potential land-division candidate based on frontage, acreage, and municipality posture.
- **Emitter:** Split analysis agent
- **Minimum payload:**
```
{
  parcel_id: uuid,
  acreage: float,
  frontage_feet: float | null,
  municipality_split_posture: string,
  estimated_resultant_lots: integer | null,
  confidence: float
}
```

---

### Family 12: Human / operator events
**event_family:** `human_operator`

These events are initiated by human operators — founder, team members, or external partners. They allow humans to inject signals, override system conclusions, and maintain control at critical inflection points.

#### human_marked_interesting
- **Class:** raw | **Phase:** 1
- **Description:** A human operator flagged an entity as worth investigating further.
- **Emitter:** Operator interface
- **Minimum payload:**
```
{
  entity_type: string,  // parcel, listing, subdivision, site_condo_project, cluster, opportunity
  entity_id: uuid,
  operator_id: string,
  reason: string | null
}
```

#### human_requested_rescan
- **Class:** raw | **Phase:** 1
- **Description:** A human operator requested that an entity or geography be rescanned for new signals.
- **Emitter:** Operator interface
- **Minimum payload:**
```
{
  scan_target_type: string,  // parcel, municipality, subdivision, cluster
  scan_target_id: uuid,
  operator_id: string,
  reason: string | null
}
```

#### human_verified_opportunity
- **Class:** raw | **Phase:** 1
- **Description:** A human operator verified that a system-detected opportunity is real and worth pursuing.
- **Emitter:** Operator interface
- **Minimum payload:**
```
{
  opportunity_id: uuid,
  operator_id: string,
  verification_notes: string | null
}
```

#### human_suppressed_event
- **Class:** raw | **Phase:** 1
- **Description:** A human operator suppressed a specific event — marking it as noise, incorrect, or not worth acting on. The event's status transitions to `suppressed`.
- **Emitter:** Operator interface
- **Minimum payload:**
```
{
  suppressed_event_id: uuid,
  operator_id: string,
  reason: string
}
```

---

### Family 13: System / operational events
**event_family:** `system_operational`

These events monitor the system's own health, enforce guardrails, and provide observability. They do not represent market signals — they represent system behavior. Essential for debugging, monitoring, and ensuring the event mesh does not run away.

#### agent_run_completed
- **Class:** derived | **Phase:** 1
- **Description:** An agent execution completed successfully.
- **Emitter:** Agent runtime
- **Minimum payload:**
```
{
  agent_run_id: uuid,
  agent_type: string,
  duration_ms: integer,
  events_emitted: integer,
  objects_created: integer,
  objects_updated: integer
}
```

#### agent_run_failed
- **Class:** derived | **Phase:** 1
- **Description:** An agent execution failed — error, timeout, or unexpected state.
- **Emitter:** Agent runtime
- **Minimum payload:**
```
{
  agent_run_id: uuid,
  agent_type: string,
  failure_reason: string,
  error_message: string | null,
  duration_ms: integer
}
```

#### recursion_limit_reached
- **Class:** derived | **Phase:** 1
- **Description:** A derived event would have exceeded the generation_depth hard cap (default: 5). The intended event was not emitted. This is a guardrail activation, not an error.
- **Emitter:** Trigger engine
- **Minimum payload:**
```
{
  intended_event_type: string,
  causal_chain_id: uuid,
  generation_depth: integer,
  hard_cap: integer
}
```

#### cooldown_triggered
- **Class:** derived | **Phase:** 1
- **Description:** A wake action was suppressed because the target object is within its cooldown window — it was recently processed and no material delta was detected.
- **Emitter:** Trigger engine
- **Minimum payload:**
```
{
  target_entity_type: string,
  target_entity_id: uuid,
  last_processed_at: timestamp,
  cooldown_remaining_seconds: integer,
  suppressed_event_type: string
}
```

#### event_processing_error
- **Class:** derived | **Phase:** 1
- **Description:** An error occurred while processing an event through the trigger engine.
- **Emitter:** Trigger engine
- **Minimum payload:**
```
{
  failed_event_id: uuid,
  failed_event_type: string,
  error_message: string,
  retry_eligible: boolean
}
```

---

## Compound event definitions

These are the compound events referenced in the trigger matrix. Each requires multiple independent conditions to be true simultaneously.

### listing_expired_in_cluster
- **Priority:** 6 (from trigger matrix)
- **Components:** `listing_expired` + the listing's parcel belongs to an active OwnerCluster with 3+ members
- **Entity overlap:** listing's `parcel_id` must be in the cluster's `parcel_ids`
- **Time window:** cluster must be active (detected within last 365 days)
- **Payload:**
```
{
  listing_id: uuid,
  cluster_id: uuid,
  cluster_size: integer,
  listing_cdom: integer,
  cluster_type: string
}
```

### distressed_developer_with_activity
- **Priority:** 7 (from trigger matrix)
- **Components:** `developer_entity_distress_detected` + at least one `listing_added` or `listing_price_reduced` for a parcel owned by the same developer within the last 90 days
- **Entity overlap:** shared `developer_entity_id`
- **Time window:** listing activity within 90 days of distress detection
- **Payload:**
```
{
  developer_entity_id: uuid,
  distress_event_id: uuid,
  recent_listing_ids: uuid[],
  activity_type: string  // new_listing, price_reduction
}
```

### split_ready_parcel
- **Priority:** 10 (from trigger matrix)
- **Components:** Parcel has adequate frontage (>= 2x municipality minimum) + adequate acreage (>= 2x minimum lot size) + municipality `land_division_posture` is `permissive` or `moderate`
- **Entity overlap:** same `parcel_id` and `municipality_id`
- **Time window:** municipality posture must be current (assessed within last 365 days)
- **Payload:**
```
{
  parcel_id: uuid,
  municipality_id: uuid,
  acreage: float,
  frontage_feet: float,
  municipality_posture: string,
  estimated_resultant_lots: integer,
  confidence: float
}
```

---

## Event naming conventions

All event names follow these rules:

1. **Family prefix when ambiguous:** If an event could belong to multiple families, prefix it with the family subject. All listing-remark-derived events carry the `listing_` prefix.
2. **Action suffix pattern:** Events end with what happened — `_detected` (discovery), `_created` (new object), `_changed` (state transition), `_required` (action needed), `_confirmed` (verification complete), `_completed` (process finished).
3. **Snake_case only:** All event names use `snake_case`. No camelCase, no hyphens.
4. **Specificity over brevity:** `roads_installed_majority_vacant_detected` is better than `road_vacancy` because the name alone tells you what happened.
5. **No verb-first names:** Events describe what happened, not what to do. `listing_added` not `add_listing`.

### Naming normalizations applied in this version

| Old name | New name | Reason |
|---|---|---|
| `package_language_detected` | `listing_package_language_detected` | Added `listing_` prefix for family consistency |
| `developer_fatigue_language_detected` | `listing_fatigue_language_detected` | Added `listing_` prefix for family consistency |
| `restriction_language_detected` | `listing_restriction_language_detected` | Added `listing_` prefix for family consistency |
| `approval_language_detected` | `listing_approval_language_detected` | Added `listing_` prefix for family consistency |
| `utility_language_detected` | `listing_utility_language_detected` | Added `listing_` prefix for family consistency |
| `improved_subdivision_stagnation_detected` | `partial_buildout_stagnation_detected` | Clarified meaning — "improved" was ambiguous |

---

## Event inventory summary

| Family | Event count | Raw | Derived | Compound | Phase 1 | Phase 2 | Phase 3+ |
|---|---|---|---|---|---|---|---|
| Listing | 17 | 5 | 12 | — | 14 | 3 | — |
| Cluster / owner | 7 | — | 7 | — | 6 | 1 | — |
| Municipal process | 29 | 16 | 13 | — | 28 | 1 | — |
| Historical stall | 6 | — | 6 | — | 6 | — | — |
| Developer / exit | 6 | — | 6 | — | 5 | 1 | — |
| Incentive | 7 | 3 | 4 | — | — | 7 | — |
| Packaging | 7 | — | 7 | — | 4 | 3 | — |
| Distribution / demand | 7 | 3 | 4 | — | — | 4 | 3 |
| Transaction / execution | 5 | 1 | 4 | — | — | — | 5 |
| Opportunity lifecycle | 5 | — | 5 | — | 5 | — | — |
| Parcel state | 5 | — | 5 | — | 5 | — | — |
| Human / operator | 4 | 4 | — | — | 4 | — | — |
| System / operational | 5 | — | 5 | — | 5 | — | — |
| Compound (cross-family) | 3 | — | — | 3 | 3 | — | — |
| **Total** | **113** | **30** | **77** | **3** | **85** | **20** | **8** |

---

## Implementation notes

1. **Schema version:** The current envelope schema version is `"1.0"`. Any structural change to the envelope (adding required fields, changing types) requires a version bump.
2. **Generation depth hard cap:** Default is **5**. This means a raw event (depth 0) can trigger derived events up to depth 5. If an agent would emit a depth-6 event, the system emits `recursion_limit_reached` instead. This cap is configurable per deployment but should not be changed without understanding the cascade implications.
3. **Cooldown windows:** Not defined in this file — they belong in the trigger matrix. This file defines the events; the trigger matrix defines the routing rules and guardrails.
4. **Compound event evaluation:** The trigger engine is responsible for evaluating compound event conditions. This file defines what the conditions are. The trigger engine implementation determines how efficiently they are checked (eager vs. lazy evaluation, indexing strategy, etc.).
5. **Event storage:** Events should be stored durably (append-only event log) for audit, debugging, and replay. The `status` field tracks processing state. Events are never deleted — only their status changes.
6. **Relationship to MunicipalEvent object:** Reiterated for implementers — creating a MunicipalEvent record causes a corresponding `_detected` event to be emitted. The object is the memory; the event is the signal. Do not confuse the two. The MunicipalEvent persists. The detection event fires once and triggers downstream work.
7. **Payload shapes are minimums:** The payloads defined above are the minimum required fields. Implementations may include additional fields as long as the minimums are present. Additional fields should be documented in implementation-level schemas.
8. **Confidence calibration:** The `source_confidence` scale (0.0–1.0) should be calibrated consistently across the system. The ranges defined in the envelope section (0.9+ authoritative, 0.7–0.89 reliable, 0.5–0.69 needs verification, below 0.5 speculative) are guidelines, not hard cutoffs. Specific agents may refine these ranges for their domain.
