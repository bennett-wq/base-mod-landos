# BaseMod LandOS — Data Sources

> This file defines where the system gets its information, how trustworthy each source is,
> what objects it feeds, and how it should be used.
> It is the source-layer companion to the object model and event library:
> the object model defines what exists, the event library defines what changes,
> and this file defines where the raw inputs come from.

---

## Purpose

LandOS is an event mesh that runs on signals. The quality, freshness, and trustworthiness of those signals depends entirely on the data sources feeding them. This document catalogs the major source categories, explains what each is used for, establishes a confidence framework, and defines the sequencing logic for which sources to build first.

This is not yet a field-level schema mapping. It is the source architecture — enough for a technical partner to build ingestion priorities, confidence assignments, and source-combination logic.

---

## Source categories

Sources are grouped by what they contribute to the system. A single external system may span multiple categories (e.g., county records provide both parcel data and recorded documents).

---

### Category 1: Live market sources

**What this covers:** MLS feed data — the primary high-frequency signal stream for listings, pricing, agent/office patterns, and status changes.

#### Spark MLS (via RETS/RESO feed)

- **What it is used for:** Listing ingestion, price tracking, status changes, agent/office identification, listing remarks text, property type classification, acreage, DOM/CDOM tracking.
- **Primary objects fed:** Listing, Parcel (via address resolution), Owner (via seller fields), OwnerCluster (via agent/office patterns)
- **Representative event families supported:** `listing` (all events), `cluster_owner` (via agent/office/owner pattern detection)
- **Confidence tier:** Authoritative for listing facts (price, status, dates, agent). Medium for property descriptions and remarks (human-written, may be inaccurate or promotional).
- **Typical refresh cadence:** Near real-time for active listings (15-minute feed polling in Phase 1). Historical closed data available via bulk query.
- **Key limitations:**
  - MLS data describes what is *listed*, not what *exists*. Unlisted land is invisible to this source.
  - Acreage and property type are entered by listing agents and may be inaccurate.
  - Remarks are free-text and require LLM classification — the raw text is authoritative, but any conclusion drawn from it is derived.
  - Spark covers a specific MLS geography. Other MLSs (e.g., RealComp for metro Detroit) may be needed for full Michigan coverage.

#### RealComp MLS (future)

- **What it is used for:** Same as Spark, for the metro Detroit / southeast Michigan geography.
- **Confidence tier:** Same as Spark.
- **Typical refresh cadence:** Same as Spark when connected.
- **Key limitations:** Separate feed, separate credentials, separate field mappings. Not yet connected.
- **Phase:** Phase 1 stretch or Phase 2.

---

### Category 2: Parcel / ownership sources

**What this covers:** The parcel universe — who owns what land, where it is, how big it is, and what its assessed/zoned status is.

#### Regrid (parcel data platform)

- **What it is used for:** Parcel geometry, parcel boundaries, acreage, APN/parcel numbers, owner names, zoning codes, land use codes, assessed values, legal descriptions.
- **Primary objects fed:** Parcel (core fields), Owner (name resolution), Municipality (parcel counts, geography), Subdivision (lot-level linkage)
- **Representative event families supported:** `parcel_state` (via vacancy/ownership resolution), `cluster_owner` (via owner matching)
- **Confidence tier:** Authoritative for geometry, APN, and assessed values (sourced from county assessor records). Medium for owner names (may be stale, may use LLC names that require entity resolution).
- **Typical refresh cadence:** Quarterly bulk refresh for the parcel universe. Individual parcel lookups can be more current.
- **Key limitations:**
  - Owner names may be LLCs, trusts, or land contracts — entity resolution is needed to link owners to clusters.
  - Zoning codes are county-specific and require normalization.
  - Legal descriptions vary in format and require parsing for site-condo detection (UNIT, CONDOMINIUM patterns).
  - Vacancy status is not directly provided — it must be inferred from improvement data, aerial imagery, or permit records.

#### County assessor / tax records (via Regrid or direct)

- **What it is used for:** Tax-assessed values, improvement status (improved vs. vacant per assessor), property class, tax delinquency signals.
- **Primary objects fed:** Parcel (vacancy_status, assessed values)
- **Confidence tier:** Authoritative for assessed values and improvement flags. May lag real-world changes by 1–2 years.
- **Typical refresh cadence:** Annual (follows assessment cycle). May be accessed more frequently via Regrid.

---

### Category 3: Municipal / recorded-document sources

**What this covers:** The public record systems that document what municipalities, developers, and property owners have done — plats, permits, bonds, master deeds, site plans, zoning changes.

#### Register of Deeds / county recorder

- **What it is used for:** Recorded plats, master deeds, deed transfers, bond recordings, easements, legal-description-based site-condo detection.
- **Primary objects fed:** MunicipalEvent (type: `plat_recorded`, `master_deed_recorded`, `bond_posted`, `bond_released`), Subdivision, SiteCondoProject, Owner (via deed transfers)
- **Representative event families supported:** `municipal_process`, `historical_stall` (via historical plat analysis)
- **Confidence tier:** Authoritative. Recorded documents are legal facts.
- **Typical refresh cadence:** Varies by county. Some counties have online portals with near-real-time recording. Others require periodic manual or batch access. Historical records (10–15 year lookback for stallout detection) are accessed once and ingested.
- **Key limitations:**
  - Access mechanisms vary widely by county — some have APIs, some have search portals, some require in-person requests.
  - Document text is often scanned images requiring OCR or manual reading.
  - Statewide coverage is not uniform. Michigan has 83 counties with different systems.

#### Planning commission agendas and minutes

- **What it is used for:** Site plan approvals, zoning amendments, variance requests, infrastructure discussions, developer presentations, rule changes.
- **Primary objects fed:** MunicipalEvent (type: `site_plan_approved`, `engineering_approved`, rule changes), Municipality (land_division_posture, zoning context)
- **Representative event families supported:** `municipal_process` (especially `municipality_rule_change_detected`, `municipality_rule_now_supports_split`)
- **Confidence tier:** Authoritative when directly quoting official minutes. Medium when LLM-extracted from meeting minutes or agenda PDFs (the source is authoritative, but the extraction is derived).
- **Typical refresh cadence:** Meeting-driven — typically monthly or bi-monthly per municipality. Phase 1 may focus on the highest-priority municipalities.
- **Key limitations:**
  - No standard format across municipalities. Some publish PDFs, some HTML, some only physical copies.
  - Extracting structured data from minutes requires LLM processing — classify the extraction as `[llm-derived]`.
  - Historical minutes (for stallout detection) may only be available in paper archives for older projects.

#### Permit systems

- **What it is used for:** Building permits pulled, permit types, permit valuations, certificate of occupancy, demolition permits.
- **Primary objects fed:** MunicipalEvent (type: `permit_pulled`), Parcel (permit activity signals), Subdivision (buildout progress tracking)
- **Representative event families supported:** `municipal_process` (`permit_pulled_detected`, `permits_pulled_majority_vacant_detected`, `municipality_permit_activity_increased`)
- **Confidence tier:** Authoritative for permit facts (number, type, date, valuation).
- **Typical refresh cadence:** Varies. Some municipalities have online permit portals with real-time data. Others require periodic batch access.
- **Key limitations:**
  - Permit data granularity varies — some systems track per-parcel, others per-project.
  - Not all municipalities have digital permit systems. Smaller townships may use paper records.
  - Permit-to-parcel linkage may require address matching or manual resolution.

---

### Category 4: Infrastructure / GIS sources

**What this covers:** Physical infrastructure data — roads, water, sewer, gas, electric service areas, and geographic/spatial analysis.

#### Municipal GIS / utility service layers

- **What it is used for:** Utility availability (water, sewer, gas, electric), road status (public/private, paved/unpaved, accepted/not accepted), service area boundaries, flood zones, wetland boundaries.
- **Primary objects fed:** Parcel (utility fields on SiteFit), Municipality (infrastructure context), Subdivision (road status)
- **Representative event families supported:** `municipal_process` (`roads_installed_detected`, `roads_accepted_detected`, `public_sewer_extension_detected`, `water_extension_detected`, `municipality_infrastructure_extension_detected`)
- **Confidence tier:** Authoritative where GIS layers are maintained by the municipality or utility. Medium where layers are stale or incomplete.
- **Typical refresh cadence:** GIS layers are updated irregularly — some municipalities update quarterly, others annually, others rarely. Treat freshness date as a confidence factor.
- **Key limitations:**
  - Not all municipalities publish GIS data. Smaller townships often lack digital GIS.
  - GIS data quality varies dramatically. Some layers are survey-grade; others are approximations.
  - Utility availability at the parcel level often requires confirmation beyond what GIS shows (e.g., a sewer main exists on the street, but is the lateral in place?).

#### Road and infrastructure field data

- **What it is used for:** Confirming road installation status, road acceptance status, and infrastructure completeness for stallout detection.
- **Primary objects fed:** Subdivision (road status, infrastructure_complete flag), MunicipalEvent
- **Confidence tier:** Authoritative if from municipal road-acceptance records. Medium if inferred from aerial imagery or GIS.
- **Typical refresh cadence:** Event-driven — checked when stallout detection or municipal scan runs.

---

### Category 5: Imagery / physical-state sources

**What this covers:** Aerial and satellite imagery used to confirm physical conditions on the ground — vacancy, construction progress, road presence, lot clearing.

#### Satellite / aerial imagery (Google Earth, Nearmap, county orthophotos)

- **What it is used for:** Vacancy confirmation (is the lot actually empty?), construction progress detection, road installation verification, lot-clearing detection.
- **Primary objects fed:** Parcel (vacancy_status confirmation), Subdivision (buildout progress), SiteCondoProject (unit vacancy)
- **Representative event families supported:** `parcel_state` (`parcel_vacancy_confirmed`), `municipal_process` (corroboration of `roads_installed_detected`)
- **Confidence tier:** Medium. Imagery interpretation is useful but inherently inferential — a lot that *appears* vacant in an image may have underground infrastructure, pending construction, or seasonal conditions. Always pair with structured data.
- **Typical refresh cadence:** Varies by provider. Google Earth imagery can be months to years old. Nearmap provides more frequent coverage but at higher cost. County orthophotos are typically annual.
- **Key limitations:**
  - Image dates vary — a "current" aerial may be 6–18 months old.
  - Interpretation requires either human review or computer vision / LLM analysis — classify as `[derived]` or `[llm-derived]`.
  - Cannot confirm underground infrastructure, legal status, or ownership.
  - Seasonal variation (snow cover, vegetation) affects interpretation accuracy.

---

### Category 6: Historical summary sources

**What this covers:** Pre-aggregated data summaries that provide context but are not primary authoritative sources.

#### Mission Control / ATTOM historical summaries

- **What it is used for:** Historical property data summaries, transaction history, tax and assessment trends, neighborhood-level context.
- **Primary objects fed:** Parcel (historical context, transaction history), Municipality (market context)
- **Confidence tier:** Medium. ATTOM aggregates from authoritative sources (county records, MLS), but the aggregation introduces lag, normalization choices, and potential gaps. Useful for enrichment and context — not a substitute for direct source access.
- **Typical refresh cadence:** Periodic bulk refresh (quarterly or as available).
- **Key limitations:**
  - Coverage gaps — not all properties or all fields are populated.
  - Historical transaction data may not match current county records exactly.
  - Should be treated as supplementary context, not primary signal.

---

### Category 7: Human / operator sources

**What this covers:** Information entered by human operators — founder, team members, brokers, or field partners.

#### Manual entry / operator interface

- **What it is used for:** Broker notes, opportunity verification, entity flagging, event suppression, forced rescans, field observations.
- **Primary objects fed:** BrokerNote (Phase 2), Opportunity (status overrides, verification), any object (via human_marked_interesting, human_requested_rescan)
- **Representative event families supported:** `human_operator` (all events: `human_marked_interesting`, `human_requested_rescan`, `human_verified_opportunity`, `human_suppressed_event`)
- **Confidence tier:** High for factual observations by a knowledgeable operator. Medium for subjective assessments. Human inputs always override cooldowns and always route as `immediate`.
- **Typical refresh cadence:** Event-driven — entered when a human has something to add.
- **Key limitations:**
  - Depends on human availability and attention.
  - Not scalable as the sole source for any category — humans should be used for verification, override, and enrichment, not primary ingestion.
  - Quality depends on the operator's knowledge and care.

---

### Category 8: Demand-side sources

**What this covers:** Buyer and broker interest signals — search activity, saved searches, inquiries, engagement patterns.

#### Marketplace platform (future)

- **What it is used for:** Buyer search profiles, broker saved searches, opportunity views/saves/inquiries, seller engagement tracking.
- **Primary objects fed:** BuyerProfile (Phase 3+), BrokerProfile (Phase 3+), SavedSearch (Phase 3+), Opportunity (demand signal rescore)
- **Representative event families supported:** `distribution_demand` (all events)
- **Confidence tier:** Authoritative for behavioral facts (a buyer clicked, a broker saved). Medium for intent inference (a save does not mean a purchase).
- **Typical refresh cadence:** Real-time (event-driven from platform interactions).
- **Key limitations:**
  - Does not exist yet — Phase 3+.
  - Demand signals are only meaningful once supply is packaged and distributed.
  - Volume will be low initially; statistical significance requires scale.
- **Phase:** Phase 3+.

---

## Confidence framework

Every data point in the system should carry an implicit or explicit confidence level. The object model uses field annotations (`[authoritative]`, `[derived]`, `[llm-derived]`, `[confidence]`) to express this. The source determines the baseline confidence.

### Tier 1: Authoritative structured records
**Sources:** Recorded documents (Register of Deeds), permit systems, county assessor records, MLS feed facts (price, status, dates), GIS layers maintained by the issuing authority.

**Characteristics:**
- Direct from the system of record
- Structured data (not free text)
- Legally or institutionally reliable
- May still be stale — freshness matters even for authoritative sources

**Treatment:** Fields sourced from Tier 1 are marked `[authoritative]` in the object model. Events based solely on Tier 1 data are classified as `raw`. No additional corroboration is required before emitting events.

### Tier 2: Useful but partial data
**Sources:** Regrid owner names (may need entity resolution), MLS listing remarks (raw text is factual, but content may be inaccurate), aerial imagery (physical observation but interpretation required), ATTOM summaries (aggregated from authoritative sources but with lag and gaps), county GIS layers of uncertain vintage.

**Characteristics:**
- Comes from a credible source but requires interpretation, normalization, or resolution
- May have gaps, lag, or ambiguity
- Useful for enrichment and corroboration

**Treatment:** Fields sourced from Tier 2 are marked `[derived]` in the object model and should carry a `[confidence]` score. Events based on Tier 2 data should note the source_system and may require corroboration from a second source before triggering high-priority downstream actions.

### Tier 3: Inferential / LLM-derived signals
**Sources:** LLM classification of listing remarks or meeting minutes, computer vision analysis of aerial imagery, entity resolution heuristics, inferred owner clusters, municipal posture interpretation from indirect signals.

**Characteristics:**
- Produced by system analysis, not direct observation
- Confidence varies by model quality and input quality
- Valuable for detection and prioritization but not for authoritative facts

**Treatment:** Fields sourced from Tier 3 are marked `[llm-derived]` in the object model and must always carry a `[confidence]` score. Events based on Tier 3 data are classified as `derived`. High-stakes actions (e.g., creating an Opportunity, emitting `municipality_rule_now_supports_split`) should require a minimum confidence threshold before firing (see trigger matrix materiality gates).

---

## Source-combination logic

No single source is the truth for everything. The system is designed so that confidence improves when multiple sources converge and caution increases when sources conflict.

### Convergence strengthens confidence
- A parcel marked as vacant by county assessor records + confirmed vacant by aerial imagery = high confidence in vacancy status.
- A plat recorded in the Register of Deeds + lots still vacant in Regrid parcel data + no permits pulled in the permit system = high confidence in a stalled subdivision.
- Package language detected in listing remarks + multiple same-owner listings in the cluster + long CDOM = high confidence in developer exit readiness.

### Conflict triggers caution
- A parcel marked as "improved" by assessor records but appearing vacant in recent aerial imagery → flag for human review, do not auto-resolve.
- A listing claiming "all utilities available" but GIS showing no sewer main on the street → lower utility confidence score, flag uncertainty.
- An LLM classifying meeting minutes as a "rule change favoring splits" but the actual ordinance text not yet confirmed → emit `municipality_rule_change_detected` as raw, but hold `municipality_rule_now_supports_split` until confidence threshold is met.

### Corroboration requirements for high-stakes signals
Some signals should only be emitted or acted upon when supported by more than one source:
- **Vacancy confirmation:** Assessor data alone is insufficient for `parcel_vacancy_confirmed` — should be corroborated by aerial imagery, permit absence, or field observation. Minimum confidence threshold: 0.7.
- **Stallout detection:** Historical plat existence alone is insufficient — should be paired with current vacancy data. The trigger matrix already enforces this through vacancy_ratio conditions.
- **Municipal rule-change impact:** The raw discovery event (`municipality_rule_change_detected`) can fire from a single authoritative source. The derived impact conclusion (`municipality_rule_now_supports_split`) requires the municipal intelligence agent to evaluate the rule change — this is an intentional two-step design already built into the event library.

---

## Michigan-specific source notes

Michigan is the launch wedge. These source realities are specific to operating in Michigan and affect ingestion priorities:

- **83 counties, each with its own systems.** Register of Deeds, assessor, and permit systems vary by county. There is no single statewide API for any of these. Phase 1 should prioritize the counties with the highest opportunity density, not attempt statewide coverage.
- **BS&A is common municipal software.** Many Michigan municipalities use BS&A for permits, assessments, and property records. Familiarity with BS&A data formats may accelerate ingestion for multiple municipalities.
- **2025 PA 58 (land division reform)** means land-division posture data is actively changing. Municipal scan agents need to watch for local ordinance changes adopting or responding to the new state framework. This makes planning commission minutes especially valuable in Phase 1.
- **Recorded plats are in county Register of Deeds.** Michigan plats are recorded at the county level. Historical plat lookback (10–15 years for stallout detection) is county-by-county work.
- **Site condos are recorded via master deed.** Michigan site-condo detection depends on finding master deeds in the Register of Deeds and parsing legal descriptions for UNIT/CONDOMINIUM patterns.

---

## What not to do yet

- **No field-by-field schema mapping yet.** This document defines source categories, confidence tiers, and ingestion priorities. Detailed field mapping (e.g., "Spark field `ListPrice` maps to Listing.list_price") is the next step after this doc is confirmed clean — it should happen source-by-source during implementation.
- **No over-expansion into low-value sources before core sources are working.** Get MLS feeds, Regrid parcel data, and Register of Deeds working before adding satellite imagery or demand-side signals.
- **No letting one source dominate the architecture.** The system is designed as a co-equal trigger mesh. MLS is the highest-frequency signal, but it is not more architecturally important than municipal records or parcel data. Ingestion pipelines should be built to the canonical event envelope — source-specific adapters feed generic events.
- **No building demand-side ingestion before supply is packaged.** Demand signals (Phase 3+) are meaningless without packaged opportunities to match against.

---

## Implementation sequencing

### Phase 1 — core sources (build first)

| Priority | Source | Why first |
|---|---|---|
| 1 | Spark MLS feed | Highest-frequency signal. Listings are the primary entry point. Enables all listing-family events. |
| 2 | Regrid parcel data | Parcel universe is required for parcel linking, vacancy inference, and cluster detection. |
| 3 | Register of Deeds (priority counties) | Recorded plats and master deeds are required for stallout and site-condo detection. |
| 4 | Permit systems (priority municipalities) | Permit data feeds stallout detection and municipal process events. |
| 5 | Planning commission minutes (priority municipalities) | Rule-change detection and site-plan approvals. LLM extraction pipeline needed. |
| 6 | County assessor / tax records (via Regrid or direct) | Vacancy inference, improvement status, assessed values. |

### Phase 2 — enrichment sources (build next)

| Source | Why Phase 2 |
|---|---|
| Municipal GIS / utility layers | Needed for SiteFit utility assessment and packaging. |
| Aerial imagery (Nearmap or equivalent) | Needed for vacancy confirmation and physical-state corroboration. |
| ATTOM / Mission Control summaries | Enrichment and historical context. Not blocking for core detection. |
| RealComp MLS (metro Detroit) | Expands geographic coverage. Same architecture as Spark. |
| Manual entry / operator interface | BrokerNote creation and operator overrides. Interface must exist. |

### Phase 3+ — demand and transaction sources

| Source | Why later |
|---|---|
| Marketplace platform (buyer/broker signals) | Requires packaged supply to match against. |
| Lender and contractor databases | Transaction resolution sources. Not needed until transactions are real. |
