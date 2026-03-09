# SESSION_HANDOFF_CURRENT.md

## Project

BaseMod LandOS — Event Mesh ("Land Swarm")

## Current phase

Phase 0 complete. Phase 1 implementation in progress. Steps 1–6 and 4.5 complete. Step 6.5 (comprehensive review + hardening) complete. **235/235 tests pass.** Ready for Step 7: Municipal Scan.

## Concise summary of what was completed this session

- Conducted a comprehensive repository review covering architecture, implementation quality, test coverage, and readiness assessment.
- **Fixed a bug in `detect_market_velocity`**: referenced nonexistent `l.city` attribute on Listing. Replaced with configurable `geography_field` parameter using `getattr()`. Added 4 new tests.
- **Made SparkIngestionAdapter thresholds configurable**: `cdom_threshold` and `agent_accumulation_threshold` are now constructor params. Eliminated brittle 80-line subclass hack in integration tests — tests now use clean constructor calls.
- **Added ALL_RULES uniqueness guard**: startup assertion in `rules/__init__.py` raises `RuntimeError` on duplicate `rule_id` values at import time.
- **Documented APN normalization strategy**: `_normalize_apn` in `linker.py` now has a docstring explaining Phase 1 limitation (global `lstrip("0")` vs per-segment) and the production fix path for multi-county.
- **Documented `detect_developer_exit` field precedence**: numbered branch order and explicit rationale for why `major_change_type` fires without a CDOM check while `withdrawal_date` requires cdom >= 120.
- Updated `LANDOS_DECISIONS_LOG.md` with 5 new locked decisions.
- Updated `MEMORY.md` with Step 6.5 results and known Phase 1 limitations.

## Files that changed or were materially advanced

- `landos/src/adapters/spark/bbo_signals.py` — `detect_developer_exit` docstring expanded; `detect_market_velocity` fixed (geography_field param)
- `landos/src/adapters/spark/ingestion.py` — `SparkIngestionAdapter.__init__` now accepts `cdom_threshold` and `agent_accumulation_threshold`; `_detect_and_build_bbo_events` uses instance thresholds
- `landos/src/adapters/regrid/linker.py` — `_normalize_apn` docstring documenting Phase 1 limitation
- `landos/src/triggers/rules/__init__.py` — startup uniqueness assertion for ALL_RULES rule_ids
- `landos/tests/test_bbo_signals.py` — 4 new `TestMarketVelocity` tests; integration tests simplified (no more subclassing)
- `LANDOS_DECISIONS_LOG.md` — 5 new decisions logged
- `MEMORY.md` — updated to 235/235 tests, Step 6.5 documented

## Key decisions that were locked

- SparkIngestionAdapter thresholds must be constructor params, not hardcoded in internal methods.
- ALL_RULES must enforce rule_id uniqueness at import time.
- APN normalization is global lstrip in Phase 1; per-segment deferred to multi-county.
- `detect_developer_exit` field precedence (major_change_type > cancellation_date > withdrawal_date > off_market_date) is intentional and reflects MLS field confidence hierarchy.
- `detect_market_velocity` uses configurable `geography_field` until Listing gains a proper `city` attribute.

## Unresolved questions still open

- InMemory stores (Listing, Parcel, Owner, Cluster) all need production replacements (PostgreSQL/Redis) before live feed wiring.
- Fan-out enforcement (`max_fan_out`) not yet implemented; belongs in agent orchestration layer.
- No MLS query layer yet — `process_batch()` is a pure record processor; polling/query integration is future work.
- BBO depth follow-up deferred: PrivateRemarks access, custom Michigan fields, metadata-driven field registry, historical bulk query, media/document ingestion.
- Municipality linkage from Regrid requires a pre-built lookup dict or default UUID — production wiring deferred.
- Geo-match polygon intersection (shapely) deferred until PostGIS is wired.
- Listing model needs a `city` field for proper `detect_market_velocity` geography matching.

## Known Phase 1 limitations (documented, not bugs)

- `_normalize_apn`: global `lstrip("0")` — multi-county needs per-segment normalization
- `detect_market_velocity`: uses `geography_field` workaround — Listing needs a `city` field
- Geo-linker takes first match within threshold, not strictly closest (ordering-dependent)
- ClusterDetector groups by `owner_id` OR `seller_name_raw`, not both (entity resolution deferred)
- Municipality resolution is pass-through (default_municipality_id sentinel)

## Single next highest-priority task

Begin Step 7: Municipal Scan — the first Tier 3 step. Build the municipal scan agent for priority Michigan municipalities. This includes:
- Municipality adapter/ingestion path
- Municipal event builders for the 16 raw municipal_process family events
- `municipality_rule_now_supports_split` derived event
- Connect to the pre-wired PLANNED rule: `PLANNED__municipality_rule_now_supports_split__rescore_parcels`
- Tests for municipal event emission and trigger routing

Per the Build Roadmap (Phase 1, section 1g): connect to Register of Deeds (priority counties), permit systems, planning commission minutes. Emit municipal process detection events. Evaluate rule changes.

## Short warning list of what not to drift into next

- Do not reopen Steps 1–6 or 4.5 unless a concrete defect is found.
- Do not wire database persistence yet.
- Do not jump to stallout detection (Step 8) before municipal scan (Step 7) is done.
- Do not build pricing engine, marketplace UI, buyer demand, incentives, or transaction orchestration.
- Do not build LLM remarks pipeline — Phase 1 uses regex only.
- Do not invent new strategy or broaden the architecture.
- Never use `cd <subdir> &&` in a Bash tool call — use absolute paths for pytest and other commands.

## Whether the current task is complete

Complete. Step 6.5 (comprehensive review + hardening) is done. 235/235 tests pass. All documentation updated. Ready for Step 7.
