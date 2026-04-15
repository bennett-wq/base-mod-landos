"""Stranded-lots underwriting engine — pure-math, no LLM, no I/O.

Every function here takes Pydantic domain models from src.models as input
and returns Pydantic domain models as output. See spec §6 for the function
signatures and §6.1.5 for the OpportunityUnderwriting data model.

Populates existing SiteFit (src/models/product.py lines 30-50) — does NOT
invent parallel envelope/setback types.

Modules:
  - envelope: compute_envelope() — parcel polygon + setbacks → buildable envelope
  - models: filter_models() — catalog + envelope → fitting models
  - cost: cost_stack() + incentive_adjust() — Bennett-specified cost formula
  - pricing: exit_price() — anchor $/sf × sqft with confidence band
  - margin: margin_matrix() — net margin from cost + exit + sell costs
  - sensitivity: sensitivity() — 2D margin grid over exit × land
  - recommendation: recommendation() — GO / NO-GO / NEGOTIATE verdict
  - market_stats: months_of_inventory, CDOM distribution, failed-listing history
"""
