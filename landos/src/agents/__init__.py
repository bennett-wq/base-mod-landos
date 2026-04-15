"""Stranded-lots agentic orchestration — LLM agents + event emission.

Seven independent agents plus one orchestrator fan-out across the stranded-lots
discovery and underwriting pipeline. Each agent reads Tier 1/2/3 municipal
intelligence, performs domain-specific LLM reasoning or retrieval, and emits
events / writes artifacts to the vault.

Modules (7 agents + 1 orchestrator):
  - zoning_extractor: read Municode + setback note → emit setback JSON per district
  - permitted_use_checker: read §406 permitted uses → emit {allowed, path, citation}
  - comp_narrator: read Spark listing data → emit {anchor, exit_$/sf, confidence}
  - incentive_agent: read Programs & Incentives note → emit {programs, net_estimate}
  - outreach_drafter: draft offer letters → write _drafts/ (no email send)
  - opportunity_hunter: consume area_favorable → re-query Spark → emit parcel_discovered
  - land_bank_hunter: scheduled adapter for land banks → emit parcel_discovered
  - underwriter_agent: orchestrator — fan out to all, run engine, emit parcel_underwritten
"""
