# CODEX_TASKING.md — BaseMod LandOS Implementation Guide

## Before starting any task
Read:
1. 00_START_HERE.md
2. LANDOS_HANDOFF_MASTER.md
3. LANDOS_DECISIONS_LOG.md
4. the file for the relevant domain
5. this file

## Repo structure recommendation
```text
/docs
  /architecture
  /data
  /decisions
  /municipal
  /product
  /ops

/src
  /objects
  /events
  /triggers
  /agents
  /adapters
  /municipal
  /packaging
  /matching
  /transactions
  /shared
```

## Priority near-term build targets
1. canonical event envelope
2. object models
3. trigger engine scaffold
4. listing->parcel->municipality->cluster flow
5. historical plat stall detector
6. site condo detector
7. first packaging path
