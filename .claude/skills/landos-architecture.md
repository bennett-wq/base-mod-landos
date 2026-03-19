# LandOS Architecture — Skill for all agents

Non-negotiable truths:
1. LandOS is an event mesh. Not a pipeline.
2. The moat is the wake-up logic.
3. Listings, clusters, municipalities are co-equal trigger families.
4. Municipalities are first-class active objects.
5. Historical stallouts and site condos are strategic supply wedges.
6. Packaging is a first-class system layer.
7. File-based memory is the source of truth.
8. Bidirectional routing is the product. Signals must compound.

Technical contracts:
- TriggerEngine requires cooldown_tracker=InMemoryCooldownTracker()
- RoutingResult: event_type, event_id, evaluated_at, fired_rules,
  suppressed_rules, wake_instructions. No .event sub-object.
- InMemory stores: always `is not None`, never `or`.
- Adapters: EventClass.RAW. Downstream agents: EventClass.DERIVED.

Step sequence:
1✅ 2✅ 3✅ 4✅ 5✅ 4.5→ 6→ 7→ 8→ 9→ 10

Tests:
cd landos && python3 -m pytest tests/ -v
