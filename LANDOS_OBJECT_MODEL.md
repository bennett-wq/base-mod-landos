# BaseMod LandOS — Object Model

> This file defines the first-class objects in the system.
> It is the canonical reference for what objects exist, what fields they carry,
> how they relate to each other, and which phase they belong to.

---

## Design principles

1. Objects are durable memory; events are change.
2. Objects should be normalized enough to avoid duplication, but pragmatic enough to ship.
3. Every object should support confidence, timestamps, and source provenance where relevant.
4. LLM-derived fields should be labeled as derived/inferred, not confused with authoritative source fields.
5. Every object carries its phase designation. Phase 1 objects are fully defined. Phase 2 objects carry minimum shapes. Phase 3+ objects are named and scoped but not yet fully specified.
6. Relationships between objects are explicit. If object A references object B, both sides document it.
7. Objects that are conceptually important but not yet complex enough to justify standalone status are embedded as structured fields within their parent object, with a note that they may be promoted later.

---

## Field annotation conventions

Every field in this document uses these annotations:

- **[required]** — must be present for the object to be valid
- **[optional]** — may be absent; system functions without it
- **[authoritative]** — sourced directly from a system of record (MLS, county parcel system, recorded documents, permit system, GIS)
- **[derived]** — computed by the system from authoritative inputs (scoring, ratios, flags)
- **[llm-derived]** — produced by LLM classification, extraction, or summarization; must always carry a confidence score
- **[confidence]** — field that expresses the system's certainty about an associated value (float 0.0–1.0)

Example: `vacancy_status — string enum — [required] [derived]` means the field is required, and its value is computed by the system rather than sourced directly.

---

## Object inventory

| # | Object | Domain | Phase | Status |
|---|---|---|---|---|
| 1 | Parcel | Supply | 1 | Fully defined |
| 2 | Listing | Supply | 1 | Fully defined |
| 3 | Municipality | Supply | 1 | Fully defined |
| 4 | MunicipalEvent | Supply | 1 | Fully defined |
| 5 | Owner | Supply | 1 | Fully defined |
| 6 | OwnerCluster | Supply | 1 | Fully defined |
| 7 | Subdivision | Supply | 1 | Fully defined |
| 8 | SiteCondoProject | Supply | 1 | Fully defined |
| 9 | DeveloperEntity | Supply | 1 | Fully defined |
| 10 | Opportunity | Supply | 1 | Fully defined |
| 11 | HomeProduct | Product | 1 | Fully defined |
| 12 | SiteFit | Product | 1 | Fully defined |
| 13 | SiteWorkEstimate | Product | 2 | Minimum shape |
| 14 | PricePackage | Product | 2 | Minimum shape |
| 15 | IncentiveProgram | Supply | 2 | Minimum shape |
| 16 | IncentiveApplication | Execution | 2 | Minimum shape |
| 17 | BrokerNote | Supply | 2 | Minimum shape |
| 18 | BuyerProfile | Demand | 3+ | Named and scoped |
| 19 | BrokerProfile | Demand | 3+ | Named and scoped |
| 20 | SavedSearch | Demand | 3+ | Named and scoped |
| 21 | TransactionPath | Execution | 3+ | Named and scoped |
| 22 | ConstructionPath | Execution | 3+ | Named and scoped |
| 23 | DeliveryTimeline | Product | 3+ | Named and scoped |
| 24 | HomeVariant | Product | 3+ | Named and scoped |
| 25 | AgentRun | System | 1 | Lightweight |
| 26 | Action | System | 1 | Lightweight |

### Naming normalization notes

- **SiteFit** replaces the former "SiteFit / SetbackFit" dual name. SetbackFit is now a component analysis within the SiteFit object, not a separate top-level object.
- **UtilityFit** has been absorbed into SiteFit as structured fields. It may be promoted to a standalone object later if utility analysis complexity warrants it.
- **BudgetBand, GeographyPreference, HomeProductPreference, FinancingProfile** are strategically important demand-side concepts but are embedded as structured fields within BuyerProfile for now. They may be promoted to standalone objects when the demand-side layer is built.
- **HOA, Bond, Plat, Permit, MasterDeed** are important records but are carried as typed payloads within MunicipalEvent rather than standalone first-class objects. If any develops enough independent lifecycle complexity (especially Bond with extensions/releases), it may be promoted later.
- **BrokerNote** is a Phase 2 object treated as strategically important enrichment — it captures non-obvious commercial intelligence that is often invisible to automated data feeds and is critical for accurate opportunity scoring.

---

## Phase 1 objects — full definitions

These 12 objects are required for the first implementation pass: the listing → parcel → municipality → cluster flow, stallout detection, site-condo detection, and first packaging path.

---

### Parcel

**Purpose:** The atomic unit of land. Every supply-side signal ultimately resolves to one or more parcels.
**Domain:** Supply
**Phase:** 1
**Relationships:** belongs to Municipality, may belong to Subdivision or SiteCondoProject, linked to Owner, referenced by Listing, referenced by Opportunity, referenced by SiteFit

**Required fields:**
- parcel_id — uuid — [required] [authoritative] — system-assigned stable identifier
- source_system_ids — object — [required] [authoritative] — map of external IDs keyed by source system (e.g., regrid_id, county_pin)
- jurisdiction_state — string — [required] [authoritative] — two-letter state code
- county — string — [required] [authoritative] — county name
- municipality_id — uuid — [required] [authoritative] — FK to Municipality
- apn_or_parcel_number — string — [required] [authoritative] — assessor parcel number or county parcel number
- acreage — float — [required] [authoritative] — total parcel acreage
- vacancy_status — string enum (vacant, improved, partially_improved, unknown) — [required] [derived]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- legal_description_raw — string — [optional] [authoritative] — raw legal description from source
- geometry — GeoJSON — [optional] [authoritative] — parcel boundary polygon
- centroid — GeoJSON point — [optional] [derived] — center point of parcel
- current_owner_id — uuid — [optional] [derived] — FK to Owner (null if not yet resolved)
- owner_name_raw — string — [optional] [authoritative] — raw owner name from source, kept even after owner_id is resolved
- land_use_class — string — [optional] [authoritative] — zoning or land use classification from assessor
- zoning_code — string — [optional] [authoritative] — municipal zoning designation
- frontage_feet — float — [optional] [authoritative] — road frontage in feet (critical for split analysis)
- depth_feet — float — [optional] [authoritative] — average lot depth
- flood_zone — string — [optional] [authoritative] — FEMA flood zone designation
- topography_summary — string — [optional] [llm-derived] — terrain characterization from aerial/GIS
- topography_confidence — float — [optional] [confidence]
- subdivision_id — uuid — [optional] [derived] — FK to Subdivision if parcel belongs to one
- site_condo_project_id — uuid — [optional] [derived] — FK to SiteCondoProject if parcel belongs to one
- assessed_value — integer — [optional] [authoritative] — county assessed value in dollars
- tax_status — string — [optional] [authoritative] — current/delinquent/exempt
- opportunity_score — float — [optional] [derived] — composite score reflecting development readiness
- opportunity_score_version — string — [optional] [derived] — scoring model version
- split_candidate_flag — boolean — [optional] [derived] — true if frontage + acreage + municipality posture suggest splittability
- split_candidate_confidence — float — [optional] [confidence]

---

### Listing

**Purpose:** A property offered for sale on the market. The highest-frequency signal entry point into the system. Every new listing should wake parcels, owners, clusters, municipal scans, and packaging work.
**Domain:** Supply
**Phase:** 1
**Relationships:** linked to Parcel (when resolved), linked to Owner (via listing agent or seller), linked to OwnerCluster (when detected), triggers MunicipalEvent scans, feeds Opportunity

**Required fields:**
- listing_id — uuid — [required] [authoritative] — system-assigned stable identifier
- source_system — string — [required] [authoritative] — which MLS or feed (e.g., "spark_rets", "realcomp")
- listing_key — string — [required] [authoritative] — source-system-native listing ID
- standard_status — string enum (active, pending, closed, withdrawn, expired, canceled) — [required] [authoritative]
- list_price — integer — [required] [authoritative] — current asking price in dollars
- property_type — string — [required] [authoritative] — MLS property type (vacant_land, residential, etc.)
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- original_list_price — integer — [optional] [authoritative] — price at first listing
- parcel_id — uuid — [optional] [derived] — FK to Parcel (null until parcel linkage resolves)
- municipality_id — uuid — [optional] [derived] — FK to Municipality (resolved from parcel or address)
- subdivision_name_raw — string — [optional] [authoritative] — raw subdivision name from MLS remarks or fields
- remarks_raw — string — [optional] [authoritative] — full agent remarks / public remarks
- remarks_classified — object — [optional] [llm-derived] — structured extraction from remarks (package language, restriction flags, utility mentions, approval signals, fatigue signals)
- remarks_classified_confidence — float — [optional] [confidence]
- listing_agent_name — string — [optional] [authoritative]
- listing_agent_id — string — [optional] [authoritative] — MLS agent ID
- listing_office_name — string — [optional] [authoritative]
- listing_office_id — string — [optional] [authoritative] — MLS office ID
- seller_name_raw — string — [optional] [authoritative] — if available from feed
- owner_id — uuid — [optional] [derived] — FK to Owner (resolved from seller name or parcel owner)
- lot_size_acres — float — [optional] [authoritative]
- latitude — float — [optional] [authoritative]
- longitude — float — [optional] [authoritative]
- dom — integer — [optional] [authoritative] — days on market (current listing period)
- cdom — integer — [optional] [authoritative] — cumulative days on market (across relists)
- price_per_acre — float — [optional] [derived]
- close_price — integer — [optional] [authoritative] — final sale price if closed
- close_date — date — [optional] [authoritative]
- list_date — date — [optional] [authoritative]
- expiration_date — date — [optional] [authoritative]

---

### Municipality

**Purpose:** A local government jurisdiction that controls land use rules, permitting, infrastructure, and development policy. Municipalities are first-class active objects — not passive metadata. A single municipality rule change can reprice every parcel within its borders.
**Domain:** Supply
**Phase:** 1
**Relationships:** contains Parcels, contains Subdivisions, contains SiteCondoProjects, emits MunicipalEvents, linked to IncentivePrograms

**Required fields:**
- municipality_id — uuid — [required] [authoritative] — system-assigned stable identifier
- name — string — [required] [authoritative] — official municipality name
- municipality_type — string enum (city, township, village, charter_township) — [required] [authoritative]
- state — string — [required] [authoritative] — two-letter state code
- county — string — [required] [authoritative] — primary county (some municipalities span counties)
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- fips_code — string — [optional] [authoritative] — federal FIPS code
- geometry — GeoJSON — [optional] [authoritative] — municipal boundary polygon
- population — integer — [optional] [authoritative]
- approval_authority_type — string enum (planning_commission, zoning_board, board_of_trustees, city_council, other) — [optional] [authoritative]
- land_division_posture — string enum (permissive, moderate, restrictive, unknown) — [optional] [llm-derived] — overall stance on land splits
- land_division_posture_confidence — float — [optional] [confidence]
- sb_23_posture — string enum (adopted, partial, not_adopted, unknown) — [optional] [derived] — stance relative to Michigan SB 23 / 2025 PA 58
- section_108_6_posture — string enum (authorized, considering, not_authorized, unknown) — [optional] [derived] — whether municipality has authorized more aggressive local land division under Section 108(6)
- minimum_lot_size_sf — integer — [optional] [authoritative] — minimum lot size in square feet from zoning ordinance
- minimum_frontage_feet — float — [optional] [authoritative] — minimum road frontage requirement
- sewer_service_type — string enum (municipal_sewer, septic_allowed, mixed, unknown) — [optional] [authoritative]
- water_service_type — string enum (municipal_water, well_allowed, mixed, unknown) — [optional] [authoritative]
- zoning_ordinance_url — string — [optional] [authoritative]
- master_plan_url — string — [optional] [authoritative]
- incentive_density_score — float — [optional] [derived] — how many applicable incentive programs exist
- market_wake_score — float — [optional] [derived] — composite score of recent signal activity
- market_wake_score_version — string — [optional] [derived]
- last_municipal_event_at — timestamp — [optional] [derived] — when the most recent MunicipalEvent was recorded
- notes — string — [optional] [llm-derived] — summarized municipal posture and context
- notes_confidence — float — [optional] [confidence]

---

### MunicipalEvent

**Purpose:** A durable record of a specific municipal action — site plan approvals, plat recordings, permits, bonds, master deeds, infrastructure extensions, rule changes. The event envelope is how the system learns about these; the MunicipalEvent object is the lasting memory. This distinction is critical for stallout forensics, where the system compares municipal actions from 10+ years ago to current parcel state.
**Domain:** Supply
**Phase:** 1
**Relationships:** belongs to Municipality, may link to Parcel(s), may link to Subdivision, may link to SiteCondoProject, may link to DeveloperEntity

**Note on sub-records:** HOA, Bond, Plat, Permit, and MasterDeed information is carried as structured data within the `details` payload of a MunicipalEvent, keyed by event_type. These are not standalone first-class objects. If any develops sufficient independent lifecycle complexity (especially Bond with its extensions, releases, and delay tracking), it may be promoted to standalone status later.

**Required fields:**
- municipal_event_id — uuid — [required] — system-assigned stable identifier
- municipality_id — uuid — [required] — FK to Municipality
- event_type — string enum — [required] [authoritative] — the type of municipal action (see list below)
- occurred_at — date or timestamp — [required] [authoritative] — when the action happened (may be approximate for historical records)
- source_system — string — [required] [authoritative] — where this was discovered (e.g., "planning_commission_minutes", "register_of_deeds", "permit_system", "gis")
- created_at — timestamp — [required]

**Optional fields:**
- source_document_ref — string — [optional] [authoritative] — document number, liber/page, URL, or file reference
- occurred_at_precision — string enum (exact, month, quarter, year, estimated) — [optional] — how precise the occurred_at date is
- parcel_ids — array of uuid — [optional] — FK(s) to affected Parcel(s)
- subdivision_id — uuid — [optional] — FK to Subdivision
- site_condo_project_id — uuid — [optional] — FK to SiteCondoProject
- developer_entity_id — uuid — [optional] — FK to DeveloperEntity
- details — object — [optional] [authoritative] — structured payload specific to the event_type (see below)
- notes — string — [optional] [llm-derived] — extracted or summarized context
- notes_confidence — float — [optional] [confidence]
- detection_method — string — [optional] — how the system found this (manual, automated_scan, llm_extraction)
- updated_at — timestamp — [optional]

**Event types and their detail payloads:**
- `plat_recorded` — details: { plat_name, plat_number, total_lots, recording_date, liber_page }
- `site_plan_approved` — details: { project_name, approval_body, conditions, lot_count }
- `engineering_approved` — details: { project_name, scope }
- `permit_pulled` — details: { permit_number, permit_type, address, valuation }
- `bond_posted` — details: { bond_amount, bond_type, issuer, expiration_date }
- `bond_extended` — details: { original_expiration, new_expiration, extension_count }
- `bond_released` — details: { release_date, conditions_met }
- `roads_installed` — details: { road_names, linear_feet, surface_type }
- `roads_accepted` — details: { acceptance_date, accepting_body }
- `sewer_extended` — details: { extension_area, capacity }
- `water_extended` — details: { extension_area, capacity }
- `master_deed_recorded` — details: { project_name, total_units, recording_date, liber_page }
- `hoa_created` — details: { hoa_name, creation_date, developer_control_flag }
- `rule_change` — details: { rule_type, old_value, new_value, effective_date }
- `incentive_created` — details: { program_name, program_type, eligibility_summary }

---

### Owner

**Purpose:** A person, LLC, trust, estate, or other entity that owns one or more parcels. Owner resolution enables cluster detection, developer identification, and seller outreach.
**Domain:** Supply
**Phase:** 1
**Relationships:** owns Parcel(s), may belong to OwnerCluster, may be linked to DeveloperEntity, may be linked to Listing (as seller)

**Required fields:**
- owner_id — uuid — [required] — system-assigned stable identifier
- owner_name_normalized — string — [required] [derived] — cleaned/standardized name
- entity_type — string enum (individual, married_couple, llc, trust, estate, corporation, land_contract, government, unknown) — [required] [derived]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- owner_name_raw — string — [optional] [authoritative] — original name string from source
- source_system — string — [optional] [authoritative] — where the owner record was first discovered
- mailing_address — string — [optional] [authoritative]
- parcel_count — integer — [optional] [derived] — number of parcels owned
- total_acreage_owned — float — [optional] [derived] — sum of acreage across owned parcels
- linked_entity_names — array of string — [optional] [derived] — other names this owner is known by or associated with
- developer_entity_id — uuid — [optional] [derived] — FK to DeveloperEntity if identified as a developer
- entity_type_confidence — float — [optional] [confidence]

---

### OwnerCluster

**Purpose:** A group of related owners, listings, or parcels that share a detectable pattern — same owner across multiple lots, same agent listing a block of parcels, same office running an inventory program. Clusters are multiplicative pattern expanders. Detecting a cluster should wake broker deep notes, entity research, adjacent parcel scans, municipal scans, and opportunity generation.
**Domain:** Supply
**Phase:** 1
**Relationships:** contains Owner(s), contains Parcel(s), contains Listing(s), may link to DeveloperEntity, may link to Subdivision or SiteCondoProject

**Required fields:**
- cluster_id — uuid — [required] — system-assigned stable identifier
- cluster_type — string enum (same_owner, same_agent, same_office, same_subdivision, geographic_proximity, mixed) — [required] [derived]
- detection_method — string — [required] [derived] — how the cluster was identified (owner_name_match, agent_id_match, geographic_analysis, llm_pattern)
- member_count — integer — [required] [derived] — number of parcels/listings in the cluster
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- owner_ids — array of uuid — [optional] [derived] — FK(s) to Owner(s)
- parcel_ids — array of uuid — [optional] [derived] — FK(s) to Parcel(s) in the cluster
- listing_ids — array of uuid — [optional] [derived] — FK(s) to active Listing(s) in the cluster
- municipality_id — uuid — [optional] [derived] — FK to Municipality if cluster is geographically concentrated
- subdivision_id — uuid — [optional] [derived] — FK to Subdivision if cluster maps to one
- site_condo_project_id — uuid — [optional] [derived] — FK to SiteCondoProject if cluster maps to one
- developer_entity_id — uuid — [optional] [derived] — FK to DeveloperEntity if cluster is developer-linked
- geographic_centroid — GeoJSON point — [optional] [derived]
- geographic_radius_miles — float — [optional] [derived]
- total_acreage — float — [optional] [derived]
- total_list_value — integer — [optional] [derived] — sum of list prices for active listings
- agent_program_flag — boolean — [optional] [derived] — true if same agent is listing multiple parcels in a pattern
- office_program_flag — boolean — [optional] [derived] — true if same office is running an inventory program
- fatigue_score — float — [optional] [derived] — composite signal of seller/developer fatigue across the cluster
- fatigue_score_confidence — float — [optional] [confidence]

---

### Subdivision

**Purpose:** A legally platted subdivision — a tract of land divided into lots with recorded plat maps, often with roads and infrastructure. Subdivisions are critical for stallout detection: a recorded plat with installed roads but high vacancy years later is a strong stranded-development signal.
**Domain:** Supply
**Phase:** 1
**Relationships:** belongs to Municipality, contains Parcel(s), may link to DeveloperEntity, may link to MunicipalEvent(s), may produce OwnerCluster(s), feeds Opportunity

**Required fields:**
- subdivision_id — uuid — [required] — system-assigned stable identifier
- name — string — [required] [authoritative] — subdivision name from plat or MLS
- municipality_id — uuid — [required] — FK to Municipality
- county — string — [required] [authoritative]
- state — string — [required] [authoritative]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- plat_date — date — [optional] [authoritative] — when the plat was recorded
- plat_municipal_event_id — uuid — [optional] — FK to the MunicipalEvent that recorded the plat
- total_lots — integer — [optional] [derived] — total platted lots
- vacant_lots — integer — [optional] [derived] — lots currently vacant
- improved_lots — integer — [optional] [derived] — lots with vertical construction
- vacancy_ratio — float — [optional] [derived] — vacant_lots / total_lots
- infrastructure_status — string enum (roads_installed, roads_accepted, roads_partial, no_roads, unknown) — [optional] [derived]
- sewer_status — string enum (municipal_connected, septic, planned, unknown) — [optional] [derived]
- water_status — string enum (municipal_connected, well, planned, unknown) — [optional] [derived]
- hoa_exists — boolean — [optional] [derived]
- developer_entity_id — uuid — [optional] [derived] — FK to DeveloperEntity
- developer_control_active — boolean — [optional] [derived] — true if developer still controls HOA
- stall_flag — boolean — [optional] [derived] — true if subdivision meets stallout criteria
- stall_score — float — [optional] [derived] — composite stallout severity score
- stall_score_version — string — [optional] [derived]
- stall_detected_at — timestamp — [optional] [derived]
- years_since_plat — float — [optional] [derived]
- bond_status — string enum (active, extended, released, defaulted, unknown) — [optional] [derived]
- parcel_ids — array of uuid — [optional] [derived] — FK(s) to Parcel(s) within this subdivision
- active_listing_count — integer — [optional] [derived]
- geometry — GeoJSON — [optional] [authoritative] — subdivision boundary

---

### SiteCondoProject

**Purpose:** A site condominium project — land divided under a master deed and condominium regime rather than a traditional plat. Site condos are a major hidden category because they are often under-detected by ordinary subdivision screens. They are discovered via master deed signals, legal-description patterns (UNIT, CONDOMINIUM, SITE CONDO), vacancy ratios, age, and infrastructure evidence.
**Domain:** Supply
**Phase:** 1
**Relationships:** belongs to Municipality, contains Parcel(s)/units, may link to DeveloperEntity, may link to MunicipalEvent(s), feeds Opportunity

**Required fields:**
- site_condo_project_id — uuid — [required] — system-assigned stable identifier
- name — string — [required] [authoritative] — project name from master deed or MLS
- municipality_id — uuid — [required] — FK to Municipality
- county — string — [required] [authoritative]
- state — string — [required] [authoritative]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- master_deed_date — date — [optional] [authoritative] — when the master deed was recorded
- master_deed_municipal_event_id — uuid — [optional] — FK to MunicipalEvent
- total_units — integer — [optional] [derived] — total units defined in master deed
- vacant_units — integer — [optional] [derived] — units with no vertical construction
- improved_units — integer — [optional] [derived] — units with completed structures
- vacancy_ratio — float — [optional] [derived] — vacant_units / total_units
- infrastructure_status — string enum (roads_installed, roads_accepted, roads_partial, no_roads, unknown) — [optional] [derived]
- sewer_status — string enum (municipal_connected, septic, planned, unknown) — [optional] [derived]
- water_status — string enum (municipal_connected, well, planned, unknown) — [optional] [derived]
- hoa_exists — boolean — [optional] [derived]
- developer_entity_id — uuid — [optional] [derived] — FK to DeveloperEntity
- developer_control_active — boolean — [optional] [derived] — true if developer still controls association
- stall_flag — boolean — [optional] [derived] — true if project meets stallout criteria
- stall_score — float — [optional] [derived]
- stall_score_version — string — [optional] [derived]
- years_since_master_deed — float — [optional] [derived]
- detection_method — string — [optional] [derived] — how the system identified this as a site condo (legal_description_pattern, master_deed_scan, mls_field, manual)
- detection_confidence — float — [optional] [confidence]
- parcel_ids — array of uuid — [optional] [derived] — FK(s) to unit Parcel(s)
- active_listing_count — integer — [optional] [derived]
- geometry — GeoJSON — [optional] [authoritative] — project boundary

---

### DeveloperEntity

**Purpose:** A developer, builder, or land company that controls one or more subdivisions, site-condo projects, or land holdings. The system detects developer fatigue and exit-window readiness through behavioral signals — same-agent inventory programs, package language, long CDOM, roads installed with high vacancy, repeated relists, and broker-note fatigue signals.
**Domain:** Supply
**Phase:** 1
**Relationships:** controls Subdivision(s), controls SiteCondoProject(s), linked to Owner(s), linked to OwnerCluster(s), linked to Listing(s), may link to MunicipalEvent(s)

**Required fields:**
- developer_entity_id — uuid — [required] — system-assigned stable identifier
- name — string — [required] [derived] — primary name (may be normalized from multiple sources)
- entity_type — string enum (builder, developer, land_company, investment_group, individual, unknown) — [required] [derived]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- alternate_names — array of string — [optional] [derived] — other names, DBAs, related LLCs
- owner_ids — array of uuid — [optional] [derived] — FK(s) to Owner(s) associated with this entity
- subdivision_ids — array of uuid — [optional] [derived] — FK(s) to Subdivision(s)
- site_condo_project_ids — array of uuid — [optional] [derived] — FK(s) to SiteCondoProject(s)
- active_listing_count — integer — [optional] [derived]
- total_parcel_count — integer — [optional] [derived]
- total_vacant_parcel_count — integer — [optional] [derived]
- geographic_focus — string — [optional] [derived] — primary operating geography
- fatigue_score — float — [optional] [derived] — composite developer exit-readiness score
- fatigue_score_version — string — [optional] [derived]
- fatigue_signals — object — [optional] [derived] — structured breakdown: { same_agent_program, package_language, long_cdom, high_vacancy, relists, price_drift, broker_fatigue_notes }
- fatigue_score_confidence — float — [optional] [confidence]
- exit_window_flag — boolean — [optional] [derived] — true if fatigue score exceeds threshold
- last_activity_at — timestamp — [optional] [derived]
- detection_method — string — [optional] [derived] — how the entity was identified

---

### Opportunity

**Purpose:** The convergence object — where supply signals, municipal context, owner readiness, and development potential combine into an actionable prospect. Without Opportunity, there is no packaging target. An Opportunity is not just a parcel; it is a parcel (or group of parcels) with enough context to evaluate whether a BaseMod home outcome is feasible.
**Domain:** Supply
**Phase:** 1
**Relationships:** references Parcel(s), references Municipality, may reference Subdivision or SiteCondoProject, may reference DeveloperEntity, may reference OwnerCluster, feeds SiteFit, feeds PricePackage

**Required fields:**
- opportunity_id — uuid — [required] — system-assigned stable identifier
- opportunity_type — string enum (stranded_lot, stalled_subdivision, stalled_site_condo, land_division_candidate, developer_exit, infill, other) — [required] [derived]
- parcel_ids — array of uuid — [required] [derived] — FK(s) to the Parcel(s) comprising this opportunity
- municipality_id — uuid — [required] [derived] — FK to Municipality
- status — string enum (detected, scored, fit_checked, packaged, distributed, engaged, converted, rejected, stale) — [required] [derived]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- subdivision_id — uuid — [optional] [derived] — FK to Subdivision if applicable
- site_condo_project_id — uuid — [optional] [derived] — FK to SiteCondoProject if applicable
- developer_entity_id — uuid — [optional] [derived] — FK to DeveloperEntity if applicable
- owner_cluster_id — uuid — [optional] [derived] — FK to OwnerCluster if applicable
- listing_ids — array of uuid — [optional] [derived] — FK(s) to active Listing(s)
- source_event_ids — array of uuid — [optional] [derived] — event(s) that triggered this opportunity's creation
- opportunity_score — float — [optional] [derived] — composite viability score
- opportunity_score_version — string — [optional] [derived]
- opportunity_score_confidence — float — [optional] [confidence]
- score_factors — object — [optional] [derived] — breakdown of scoring components: { land_readiness, municipal_favorability, infrastructure_completeness, owner_motivation, pricing_viability, incentive_availability }
- packaging_readiness — string enum (not_started, fit_in_progress, fit_complete, estimate_in_progress, packaged, needs_review) — [optional] [derived]
- rejection_reason — string — [optional] [derived] — if rejected, why
- notes — string — [optional] [llm-derived]
- notes_confidence — float — [optional] [confidence]

---

### HomeProduct

**Purpose:** A BaseMod home model that can be placed on land — the product that makes land into a housing outcome. The system matches HomeProducts to parcels based on physical fit, zoning compatibility, and pricing feasibility.
**Domain:** Product
**Phase:** 1
**Relationships:** matched to Parcel via SiteFit, referenced by PricePackage

**Required fields:**
- home_product_id — uuid — [required] — system-assigned stable identifier
- model_name — string — [required] [authoritative] — BaseMod model designation
- footprint_width_feet — float — [required] [authoritative] — width of the home footprint
- footprint_depth_feet — float — [required] [authoritative] — depth of the home footprint
- stories — integer — [required] [authoritative]
- square_footage — integer — [required] [authoritative] — total living area
- base_price — integer — [required] [authoritative] — base home price before site work, in dollars
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Optional fields:**
- bedrooms — integer — [optional] [authoritative]
- bathrooms — float — [optional] [authoritative]
- garage_type — string enum (attached, detached, none) — [optional] [authoritative]
- foundation_type — string enum (slab, crawl, basement, flexible) — [optional] [authoritative]
- min_lot_width_feet — float — [optional] [authoritative] — minimum lot width this model requires
- min_lot_depth_feet — float — [optional] [authoritative] — minimum lot depth this model requires
- min_lot_acres — float — [optional] [derived] — minimum lot size
- utility_requirements — object — [optional] [authoritative] — { sewer_type, water_type, electric_service, gas_required }
- product_line — string — [optional] [authoritative] — product family or series
- active — boolean — [optional] [authoritative] — whether this model is currently offered
- image_url — string — [optional] [authoritative]
- spec_sheet_url — string — [optional] [authoritative]

---

### SiteFit

**Purpose:** The analysis of whether a specific HomeProduct can physically, legally, and practically be placed on a specific Parcel. SiteFit encompasses setback analysis (does the footprint fit within required setback distances), utility analysis (are the required utilities available or feasibly connectable), and basic site feasibility. This replaces the former "SiteFit / SetbackFit" dual name and absorbs what was previously called "UtilityFit."
**Domain:** Product
**Phase:** 1
**Relationships:** references Parcel, references HomeProduct, references Municipality (for setback/zoning rules), feeds Opportunity scoring, feeds SiteWorkEstimate, feeds PricePackage

**Note on absorbed concepts:** SetbackFit is modeled as the setback analysis fields within this object. UtilityFit is modeled as the utility analysis fields within this object. Either may be promoted to standalone objects later if their complexity warrants independent lifecycle management.

**Required fields:**
- site_fit_id — uuid — [required] — system-assigned stable identifier
- parcel_id — uuid — [required] — FK to Parcel
- home_product_id — uuid — [required] — FK to HomeProduct
- fit_result — string enum (fits, marginal, does_not_fit, insufficient_data) — [required] [derived]
- fit_confidence — float — [required] [confidence]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

**Setback analysis fields (formerly SetbackFit):**
- front_setback_required_feet — float — [optional] [authoritative] — from municipal zoning
- side_setback_required_feet — float — [optional] [authoritative]
- rear_setback_required_feet — float — [optional] [authoritative]
- front_setback_available_feet — float — [optional] [derived] — calculated from parcel geometry
- side_setback_available_feet — float — [optional] [derived]
- rear_setback_available_feet — float — [optional] [derived]
- setback_fit_result — string enum (clear, tight, violation, unknown) — [optional] [derived]
- setback_source — string — [optional] — where setback rules came from (zoning_ordinance, llm_extraction, manual)

**Utility analysis fields (formerly UtilityFit):**
- sewer_available — string enum (municipal_at_lot, municipal_nearby, septic_required, unknown) — [optional] [derived]
- sewer_connection_cost_estimate — integer — [optional] [derived] — estimated cost in dollars
- water_available — string enum (municipal_at_lot, municipal_nearby, well_required, unknown) — [optional] [derived]
- water_connection_cost_estimate — integer — [optional] [derived]
- electric_available — boolean — [optional] [derived]
- gas_available — boolean — [optional] [derived]
- utility_overall_status — string enum (all_available, partial, major_work_needed, unknown) — [optional] [derived]
- utility_confidence — float — [optional] [confidence]

**General site feasibility fields:**
- access_type — string enum (paved_road, gravel_road, private_road, no_access, unknown) — [optional] [derived]
- slope_concern — boolean — [optional] [derived]
- flood_concern — boolean — [optional] [derived]
- wetland_concern — boolean — [optional] [derived]
- environmental_flag — boolean — [optional] [derived] — true if any environmental issue detected
- notes — string — [optional] [llm-derived]
- notes_confidence — float — [optional] [confidence]
- requires_human_review — boolean — [optional] [derived] — true if automated fit assessment is uncertain

---

## Phase 2 objects — minimum shapes

These objects are needed for packaging, incentive matching, and market intelligence enrichment. They are defined at minimum shape — enough to begin implementation but not yet fully specified.

---

### SiteWorkEstimate

**Purpose:** An estimate of the site preparation and infrastructure costs required to make a parcel ready for a specific home installation — grading, foundation, driveway, utility connections, septic/well if needed, permits.
**Domain:** Product
**Phase:** 2
**Relationships:** references Parcel, references HomeProduct, references SiteFit, feeds PricePackage

**Minimum fields:**
- site_work_estimate_id — uuid — [required]
- parcel_id — uuid — [required] — FK to Parcel
- home_product_id — uuid — [required] — FK to HomeProduct
- site_fit_id — uuid — [optional] — FK to SiteFit
- estimate_range_low — integer — [required] [derived] — low-end estimate in dollars
- estimate_range_high — integer — [required] [derived] — high-end estimate in dollars
- estimate_confidence — float — [required] [confidence]
- assumptions — object — [optional] [derived] — what was assumed (soil_type, access, utility_distances, foundation_type)
- line_items — array of object — [optional] [derived] — breakdown by category (grading, foundation, driveway, utilities, permits, other)
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

---

### PricePackage

**Purpose:** The all-in price object that makes a land+home opportunity buyer-legible. Combines land cost, home cost, and site work into a total that can be compared to resale homes. This is the trust layer — packaging with grounded assumptions and clear explanations.
**Domain:** Product
**Phase:** 2
**Relationships:** references Opportunity, references Parcel, references HomeProduct, references SiteFit, references SiteWorkEstimate, may reference IncentiveProgram

**Minimum fields:**
- price_package_id — uuid — [required]
- opportunity_id — uuid — [required] — FK to Opportunity
- parcel_id — uuid — [required] — FK to Parcel
- home_product_id — uuid — [required] — FK to HomeProduct
- land_cost — integer — [required] [derived] — estimated or listed land price
- home_cost — integer — [required] [authoritative] — base home price
- site_work_estimate_low — integer — [required] [derived]
- site_work_estimate_high — integer — [required] [derived]
- all_in_price_low — integer — [required] [derived] — land + home + site work low
- all_in_price_high — integer — [required] [derived] — land + home + site work high
- incentive_offset — integer — [optional] [derived] — estimated incentive value if applicable
- assumptions_summary — string — [required] [derived] — plain-English summary of what was assumed
- feasibility_rating — string enum (strong, moderate, speculative, not_feasible) — [required] [derived]
- feasibility_confidence — float — [required] [confidence]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

---

### IncentiveProgram

**Purpose:** A government or institutional program that can reduce cost, accelerate permitting, or otherwise improve the economics of a land+home outcome — tax abatements, down payment assistance, infrastructure grants, density bonuses, brownfield credits.
**Domain:** Supply
**Phase:** 2
**Relationships:** belongs to Municipality or geography, matched to Opportunity, referenced by PricePackage, tracked via IncentiveApplication

**Minimum fields:**
- incentive_program_id — uuid — [required]
- name — string — [required] [authoritative]
- program_type — string enum (tax_abatement, dpa, infrastructure_grant, density_bonus, brownfield, land_bank, other) — [required] [authoritative]
- jurisdiction_level — string enum (federal, state, county, municipal, other) — [required] [authoritative]
- municipality_id — uuid — [optional] — FK to Municipality if municipal-level
- eligibility_summary — string — [required] [llm-derived]
- eligibility_summary_confidence — float — [required] [confidence]
- estimated_value_range — string — [optional] [derived] — e.g., "$5,000–$15,000"
- application_deadline — date — [optional] [authoritative]
- active — boolean — [required] [derived]
- source_url — string — [optional] [authoritative]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

---

### IncentiveApplication

**Purpose:** Tracks the pursuit of a specific incentive for a specific opportunity — from identification through paperwork to award or denial.
**Domain:** Execution
**Phase:** 2
**Relationships:** references IncentiveProgram, references Opportunity

**Minimum fields:**
- incentive_application_id — uuid — [required]
- incentive_program_id — uuid — [required] — FK to IncentiveProgram
- opportunity_id — uuid — [required] — FK to Opportunity
- status — string enum (identified, application_started, submitted, under_review, awarded, denied, expired) — [required] [derived]
- estimated_value — integer — [optional] [derived]
- awarded_value — integer — [optional] [authoritative]
- created_at — timestamp — [required]
- updated_at — timestamp — [required]

---

### BrokerNote

**Purpose:** A structured capture of non-obvious commercial intelligence from listing remarks, broker conversations, back-office notes, and market patterns. BrokerNote is strategically important enrichment — it surfaces truths that are invisible to automated data feeds. Developer fatigue, bulk flexibility, off-market willingness, seller motivation, zoning complications, and neighborhood dynamics often live only in broker remarks and conversation. Accurate opportunity scoring depends on this intelligence.
**Domain:** Supply
**Phase:** 2
**Relationships:** may reference Listing, may reference Parcel, may reference OwnerCluster, may reference DeveloperEntity, may reference Subdivision or SiteCondoProject

**Minimum fields:**
- broker_note_id — uuid — [required]
- source_type — string enum (listing_remarks, agent_conversation, office_intel, public_record_note, manual_entry) — [required]
- source_listing_id — uuid — [optional] — FK to Listing
- parcel_id — uuid — [optional] — FK to Parcel
- cluster_id — uuid — [optional] — FK to OwnerCluster
- raw_text — string — [required] [authoritative] — the original remark or note
- extracted_signals — object — [optional] [llm-derived] — structured extraction: { package_language, fatigue_signals, bulk_flexibility, off_market_hints, restriction_flags, approval_mentions, utility_mentions, motivation_signals }
- extracted_signals_confidence — float — [optional] [confidence]
- created_at — timestamp — [required]

---

## Phase 3+ objects — named and scoped

These objects are strategically important but not needed until the demand-side, distribution, and transaction layers are built. They are named and scoped here so future work does not conflict with their eventual definitions.

---

### BuyerProfile

**Purpose:** A prospective buyer's preferences, constraints, and readiness. Contains embedded structured fields for budget, geography, home preferences, and financing — concepts that are strategically important but do not yet need standalone object status.
**Domain:** Demand
**Phase:** 3+

**Embedded concepts (may be promoted to standalone objects later):**
- **BudgetBand** — price range the buyer can afford (min/max all-in price, monthly payment target, down payment available)
- **GeographyPreference** — where the buyer wants to live (municipalities, counties, zip codes, drive-time radius, school districts)
- **HomeProductPreference** — what kind of home the buyer wants (bedrooms, bathrooms, square footage range, stories, garage, foundation type)
- **FinancingProfile** — how the buyer intends to pay (conventional, FHA, VA, USDA, cash, land contract, pre-approval status, lender)

---

### BrokerProfile

**Purpose:** A real estate broker or agent who represents buyers or has market knowledge relevant to land+home opportunities.
**Domain:** Demand
**Phase:** 3+

---

### SavedSearch

**Purpose:** A persistent search query from a buyer or broker that should trigger matching when new opportunities are packaged.
**Domain:** Demand
**Phase:** 3+

---

### TransactionPath

**Purpose:** The sequence of steps required to convert a packaged opportunity into a completed housing outcome — offer, contract, financing, permits, construction, closing.
**Domain:** Execution
**Phase:** 3+

---

### ConstructionPath

**Purpose:** The construction-specific execution plan — contractor selection, permitting, foundation, home delivery, installation, inspection, occupancy.
**Domain:** Execution
**Phase:** 3+

---

### DeliveryTimeline

**Purpose:** The estimated schedule for delivering a completed home on a specific parcel — from contract to occupancy.
**Domain:** Product
**Phase:** 3+

---

### HomeVariant

**Purpose:** A specific configuration of a HomeProduct — floor plan option, finish level, optional features. Adds depth to the product catalog beyond base models.
**Domain:** Product
**Phase:** 3+

---

## System objects — lightweight definitions

These objects support system operations, debugging, and audit trails. They are kept lightweight but should exist from Phase 1.

---

### AgentRun

**Purpose:** A record of a specific agent execution — what agent ran, when, what it consumed, what it produced, and whether it succeeded. Essential for debugging, guardrail enforcement, and understanding system behavior.
**Domain:** System
**Phase:** 1

**Minimum fields:**
- agent_run_id — uuid — [required]
- agent_type — string — [required] — which agent ran
- triggered_by_event_id — uuid — [optional] — the event that triggered this run
- started_at — timestamp — [required]
- completed_at — timestamp — [optional]
- status — string enum (running, completed, failed, timed_out, circuit_broken) — [required]
- input_entity_refs — object — [optional] — what objects/events the agent consumed
- output_event_ids — array of uuid — [optional] — events emitted by this run
- output_object_ids — array of uuid — [optional] — objects created or updated
- error_message — string — [optional]
- generation_depth — integer — [optional] — how deep in the causal chain this run is (for recursion guardrails)

---

### Action

**Purpose:** A generic unit of work tracked by the system — outreach tasks, manual review assignments, follow-ups, human-in-the-loop checkpoints.
**Domain:** System
**Phase:** 1

**Minimum fields:**
- action_id — uuid — [required]
- action_type — string — [required] — what kind of work (outreach, review, follow_up, verification, manual_scan)
- status — string enum (pending, in_progress, completed, canceled, blocked) — [required]
- assigned_to — string — [optional] — person or system responsible
- related_object_type — string — [optional] — what object this action is about
- related_object_id — uuid — [optional] — FK to the related object
- due_at — timestamp — [optional]
- created_at — timestamp — [required]
- completed_at — timestamp — [optional]
- notes — string — [optional]

---

## Relationship map

This section shows how objects connect. Arrows indicate "references" or "belongs to." The system is a graph, not a tree — objects can be reached from multiple paths.

```
Listing ──→ Parcel ──→ Municipality
  │            │            │
  │            ├──→ Owner   ├──→ MunicipalEvent
  │            │      │     │
  │            │      └──→ OwnerCluster
  │            │
  │            ├──→ Subdivision ──→ DeveloperEntity
  │            │
  │            └──→ SiteCondoProject ──→ DeveloperEntity
  │
  └──→ BrokerNote

Parcel ──→ Opportunity ──→ SiteFit ──→ HomeProduct
                │              │
                │              └──→ SiteWorkEstimate
                │
                └──→ PricePackage ──→ IncentiveProgram
                            │
                            └──→ IncentiveApplication

Municipality ──→ IncentiveProgram

OwnerCluster ──→ DeveloperEntity

AgentRun ──→ (any object, any event)
Action ──→ (any object)
```

**Key relationship rules:**
- Every Parcel belongs to exactly one Municipality.
- A Parcel may belong to zero or one Subdivision and zero or one SiteCondoProject.
- A Listing may link to zero or one Parcel (until parcel resolution completes).
- An Opportunity references one or more Parcels (a multi-lot deal is one Opportunity with multiple Parcels).
- A SiteFit is always a specific Parcel + specific HomeProduct combination.
- A PricePackage is always tied to one Opportunity.
- MunicipalEvents belong to one Municipality but may reference multiple Parcels.
- OwnerClusters can span Municipalities (an owner may hold land in multiple jurisdictions).

---

## Implementation notes

- IDs should be stable and portable (UUIDs recommended).
- Favor append-only event history over destructive overwrite where possible.
- Track provenance on critical fields — know where every value came from.
- Separate raw source fields (e.g., `owner_name_raw`) from normalized/derived fields (e.g., `owner_name_normalized`). Keep both.
- Support confidence scores on any field where the system infers rather than observes.
- All [llm-derived] fields must carry an associated confidence score.
- Scoring fields (opportunity_score, stall_score, fatigue_score, etc.) should carry a version identifier so scores can be compared across model updates.
- Timestamps should be UTC.
- Enum values listed here are starting sets and may be extended. Additions should be documented in the decisions log.
