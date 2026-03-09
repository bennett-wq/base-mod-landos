# BaseMod LandOS — Handoff Master

## Official naming
- **Program name:** BaseMod LandOS — Event Mesh
- **Nickname:** Land Swarm

## Canonical mission
Turn fragmented land supply into structured, transactable, attainable homeownership inventory.

## Canonical vision
Build the operating system that continuously maps land liquidity, development readiness, policy unlocks, seller intent, buyer affordability, and installable home options—then turns those signals into transactable housing outcomes.

## The breakthrough insight
The system's power comes from **authentic signals triggering the next right agents, which create new authentic signals, which trigger the next right agents**, in a compounding cascade that organizes the market into housing outcomes.

This is not "agents for the sake of agents."
This is a **signal architecture** where:
- objects hold durable market memory,
- events express meaningful market change,
- agents perform bounded work,
- outcomes become increasingly packageable and transactable.

## What LandOS is not
LandOS is not:
- just an MLS scraper,
- just a vacant-lot database,
- just a CRM,
- just a modular home configurator,
- just a lead gen funnel.

It is a **market-state engine + packaging engine + distribution engine + transaction engine**.

## Core thesis
Every meaningful land signal should be allowed to wake the market graph. Every major object should be able to receive events, emit events, and trigger next-best actions. The system should keep routing, enriching, packaging, and distributing opportunity until a credible housing outcome exists.

## Why this exists
Housing is constrained not only by cost, but by fragmentation:
- buildable land is hidden or misunderstood,
- municipal process data is scattered,
- incentives are obscure,
- sellers do not know what their land can support,
- buyer brokers do not have a clean land+home product to show,
- buyers cannot easily compare vacant land opportunities to resale homes,
- builders do not have a machine to surface all the low-friction, ready-ish opportunities.

LandOS exists to connect all of that.

## End-state platform concept
For every viable parcel, lot, cluster, subdivision, site condo, or administratively splittable tract:
1. identify the opportunity,
2. understand the policy/municipal context,
3. fit the right BaseMod home product,
4. estimate site work and all-in price,
5. expose it to the market through buyers, brokers, and sellers,
6. convert it into a delivered housing outcome.

The end-state experience is that buyers and brokers can browse **land+home opportunities** the way they browse existing homes today.

## BaseMod's role in the ecosystem
BaseMod may play one or several of these roles depending on the opportunity:
- direct buyer/controller of land,
- conduit between seller and end buyer,
- merchandiser/packager of land+home outcomes,
- dealer of the home product,
- construction management coordinator,
- lead source and transaction organizer,
- data and signal infrastructure layer.

The system should be designed so BaseMod does not need to own every parcel to capture value.

## Major object families
### Supply-side objects
- Parcel
- Listing
- Owner
- OwnerCluster
- Subdivision
- SiteCondoProject
- Municipality
- MunicipalEvent
- DeveloperEntity
- IncentiveProgram
- Opportunity

### Demand-side objects
- BuyerProfile
- BrokerProfile
- SavedSearch
- BudgetBand
- GeographyPreference
- HomeProductPreference
- FinancingProfile

### Product/packaging objects
- HomeProduct
- HomeVariant
- SetbackFit
- UtilityFit
- SiteWorkEstimate
- PricePackage
- DeliveryTimeline

### Execution objects
- Action
- AgentRun
- OutreachTask
- IncentiveApplication
- TransactionPath
- ConstructionPath

## Core trigger families
### Listings
Listings are high-frequency entry points. They should wake:
- parcels,
- owner linkage,
- clusters,
- municipal scans,
- broker notes,
- packaging,
- incentives,
- buyer matching.

### Clusters
Clusters are multiplicative expanders. They should wake:
- broker deep notes,
- owner/entity research,
- adjacent parcel scans,
- municipal scans,
- listing rescans,
- opportunity generation.

### Municipalities
Municipalities are first-class active objects. They should wake:
- parcel rescoring,
- large-acreage scans,
- listing rescans,
- cluster recomputation,
- incentive rematching,
- geography-wide opportunity refreshes.

### Historical stallouts
Historical municipal and plat/site-condo forensics seed supply even without live listings.

### Buyer demand
Saved searches, buyer budgets, location preferences, and broker interest should wake packaging and prioritization.

## The Michigan wedge
Michigan is a particularly strong launch market because:
- it has a meaningful amount of stranded lot and vacant land opportunity,
- stalled subdivisions and site condos are common,
- land division law has shifted,
- municipalities may create more aggressive local division possibilities under Section 108(6),
- the gap between land availability and attainable home product is significant.

## Priority strategic wedges inside Michigan
1. **Stranded lots**
2. **Stalled subdivisions**
3. **Stalled site condos**
4. **5+ acre land-division candidates**
5. **Subsection 6 municipality opportunities**
6. **Developer fatigue / exit-window inventory**
7. **Infrastructure-complete, vertically incomplete projects**

## Historical stallout thesis
A large amount of valuable opportunity may come from projects that stalled 10–15 years ago:
- plats recorded,
- master deeds recorded,
- roads installed,
- utilities installed,
- but lots still vacant.

These should be detected by comparing historical municipal/deed/plat signals to current parcel vacancy and, where possible, aerial evidence.

## Site-condo thesis
Site condos are a major hidden category because they are often under-detected by ordinary subdivision screens. They should be discovered via:
- master deed signals,
- legal-description patterns (`UNIT`, `CONDOMINIUM`, `SITE CONDO`),
- vacancy ratios,
- age,
- roads/infrastructure signals.

## Developer fatigue / exit-window thesis
The system should detect when a developer has shifted from value-maximizing buildout to inventory monetization. Key patterns include:
- same-agent inventory program,
- package or remaining-inventory language,
- long CDOM,
- roads installed with high vacancy,
- repeated relists and price drift,
- broker-note fatigue signals.

## Packaging thesis
Land is not enough. The platform must package land into buyer-legible opportunity:
- what home fits,
- what assumptions were used,
- what setbacks and zoning considerations apply,
- what site work range is likely,
- what the all-in price range is,
- what timeline is realistic,
- what incentives may apply.

Packaging is the trust layer.

## Marketplace thesis
The platform should ultimately expose:
- lots and land that can become housing,
- BaseMod home options that fit,
- all-in pricing ranges,
- municipality/site highlights,
- feasibility confidence,
- broker/buyer-friendly browse experiences.

This should create a new kind of market behavior:
buyers compare land+home to resale homes in one mental workflow.

## Business model thesis
BaseMod monetizes where it sits in the value chain:
- home/dealer margin,
- construction management fee,
- transaction coordination,
- data advantage,
- distribution advantage,
- possibly financing/referral and ancillary revenue over time.

## System design principles
1. Use genuine signals only.
2. Let every major object receive and emit events.
3. Use typed events and deterministic state updates where possible.
4. Use LLMs for ambiguity, summarization, classification, and extraction—not as the sole source of truth.
5. Keep confidence and assumptions explicit.
6. Keep humans in the loop on critical inflection points.
7. Build recursion guardrails from day one.
8. Optimize for a real housing outcome, not just signal generation.

## Immediate next build priorities
1. Finalize the documentation spine.
2. Finalize canonical object model.
3. Finalize event schema and event library.
4. Finalize trigger matrix and guardrails.
5. Build municipal history / stallout logic.
6. Build listing + cluster + municipality cross-wake engine.
7. Build packaging prototype (home fit + all-in pricing).
8. Build first broker/buyer browse experience.

## Never forget
- The product is the signal architecture, not a loose collection of agents.
- Packaging matters as much as sourcing.
- The buyer/broker experience is the proof of category creation.
- The first wedge is high-confidence land opportunity, not universal perfection.
- Trust comes from grounded assumptions and clear explanations.
- BaseMod's societal impact comes from making overlooked land legible and attainable as housing.
