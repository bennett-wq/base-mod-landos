# Cluster Agent — Owner Cluster Detection (Step 6)
## Model
claude-sonnet-4-6
## Status
WAITING — do not implement until PM Agent authorizes Step 6.
Step 4.5 (BBO) must complete first.
## What Step 6 will build
Owner/agent/office cluster detection from linked listings, parcels,
and BBO signals. Emits: same_owner_listing_detected, owner_cluster_detected,
owner_cluster_size_threshold_crossed, agent_subdivision_program_detected,
office_inventory_program_detected.
## BBO enrichment available from Step 4.5
ListAgentKey links listings to agents reliably across the feed.
BuyerOfficeKey reveals corporate buyer patterns.
CDOM thresholds confirm cluster fatigue signals.
PrivateRemarks package language confirms acquisition opportunity.
## Reverse routing note
When cluster_agent emits owner_cluster_detected or same_owner_listing_detected,
rules RO and RP route those events BACK to spark_signal_agent to deepen
BBO analysis on all listings in the cluster. This is the ping-pong.
## Thresholds
3+ listings, same normalized owner = owner_cluster_detected
5+ = owner_cluster_size_threshold_crossed
## Activation
PM Agent authorization only. Not before Step 4.5 LANDOS_STEP_COMPLETE.
