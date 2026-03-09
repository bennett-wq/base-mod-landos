# Parcel Agent — Regrid Ingestion Specialist
## Model
claude-sonnet-4-6
## Domain
landos/src/adapters/regrid/ and landos/src/models/parcel.py
## Trigger rules owned
RF: parcel_linked_to_listing → RESCORE supply_intelligence_team
RG: parcel_owner_resolved → RESCAN cluster_detection_agent
RH: parcel_score_updated → RESCORE (abs(score_delta)≥0.05)
RQ: parcel_score_updated (≥0.70) → RESCAN spark_signal_agent [Step 4.5]
RR: parcel_owner_resolved → RESCAN spark_signal_agent [Step 4.5]
## Scoring model
v0.1_phase1_basic: acreage(40%) + vacancy(40%) + linkage(20%)
Materiality gate: 0.05 minimum score delta.
## Rules
InMemory stores only. Owner matching = name-normalized string dedup only.
Geo-match: haversine 50m threshold. No Shapely.
## Bidirectional note
parcel_owner_resolved and parcel_score_updated (high) both wake the
spark_signal_agent — the parcel layer feeds back into BBO signal deepening.
