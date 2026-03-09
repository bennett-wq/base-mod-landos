# BaseMod LandOS — Setup & Orientation Guide

## What is this folder?

This is the project brain for **BaseMod LandOS**. It contains every major decision, architecture definition, and system blueprint created so far — organized into standalone files so that anyone (founder, engineer, or AI tool) can pick up exactly where work left off.

Nothing here is code yet. These are the canonical reference documents that all future code, agents, and tooling should be built from.

---

## What each file is for

### Start here
| File | Purpose |
|---|---|
| `00_START_HERE.md` | The front door. Explains what LandOS is, why it exists, what has been decided so far, and what order to read everything in. |
| `LANDOS_HANDOFF_MASTER.md` | The full system vision — mission, thesis, object families, trigger families, the Michigan wedge, packaging, marketplace, business model, and design principles. This is the single most important document. |

### Decisions and history
| File | Purpose |
|---|---|
| `LANDOS_DECISIONS_LOG.md` | Every major architectural and strategic decision, with the reasoning behind it. If you ever wonder "why did we do it this way?" — the answer is here. |

### System architecture
| File | Purpose |
|---|---|
| `LANDOS_OBJECT_MODEL.md` | Defines the core data objects (Parcel, Listing, Municipality, Owner, etc.) and their minimum field shapes. This is what the database and data layer will be built from. |
| `LANDOS_EVENT_LIBRARY.md` | The full catalog of typed events the system can emit and respond to — listing events, municipal events, stall detection, packaging, demand signals, and more. |
| `LANDOS_TRIGGER_MATRIX.md` | The rules for what wakes what: priority hierarchy, core routing logic, and guardrails to prevent runaway cascades. |
| `LANDOS_AGENT_TEAMS.md` | The eight agent teams and their purposes — from supply intelligence to transaction resolution. |

### Data and roadmap
| File | Purpose |
|---|---|
| `LANDOS_DATA_SOURCES.md` | Where the system gets its information (MLS, parcel data, municipal records, permits, GIS, etc.) and how confident each source type is. |
| `LANDOS_BUILD_ROADMAP.md` | The six build phases in order: documentation, signals, municipal intelligence, packaging, market activation, transaction resolution, flywheel. |

### Tool configuration
| File | Purpose |
|---|---|
| `CLAUDE.md` | Instructions that Claude Code reads automatically at the start of every session. Contains the non-negotiable architectural truths so the AI never drifts from the core design. |
| `CODEX_TASKING.md` | Implementation guide for any coding tool — what to read before starting work, recommended repo structure, and priority build targets. |

### Reference
| File | Purpose |
|---|---|
| `README_PACKET_OVERVIEW.txt` | A plain-text summary listing all the files and suggesting what to do with them. |
| `backups/base_mod_land_os_handoff_packet.md` | The original single-file packet everything was split from. Kept as a backup — do not edit. |

---

## Reading order

### For the founder
1. `00_START_HERE.md` — orient yourself
2. `LANDOS_HANDOFF_MASTER.md` — the full vision and thesis
3. `LANDOS_DECISIONS_LOG.md` — why things are the way they are
4. `LANDOS_BUILD_ROADMAP.md` — what gets built and in what order
5. Everything else as needed

### For the technical partner
1. `00_START_HERE.md` — orient yourself
2. `LANDOS_HANDOFF_MASTER.md` — understand the full system concept
3. `LANDOS_DECISIONS_LOG.md` — understand constraints and commitments
4. `LANDOS_OBJECT_MODEL.md` — the data layer you will build
5. `LANDOS_EVENT_LIBRARY.md` — the event types you will implement
6. `LANDOS_TRIGGER_MATRIX.md` — the routing and guardrail rules
7. `CODEX_TASKING.md` — repo structure and near-term build targets
8. `LANDOS_AGENT_TEAMS.md` and `LANDOS_DATA_SOURCES.md` as needed

---

## What the technical partner should care about first

These four files define the buildable system:

1. **`LANDOS_OBJECT_MODEL.md`** — what objects exist and what fields they carry
2. **`LANDOS_EVENT_LIBRARY.md`** — what events the system speaks
3. **`LANDOS_TRIGGER_MATRIX.md`** — what wakes what, and what prevents runaway loops
4. **`CODEX_TASKING.md`** — recommended repo layout and the first seven build targets

Everything else is context and rationale that informs those four.

---

## What Claude Code should always read first

Before doing any work in this project, Claude Code should read these files in this order:

1. `CLAUDE.md` (loaded automatically if present)
2. `00_START_HERE.md`
3. `LANDOS_HANDOFF_MASTER.md`
4. `LANDOS_DECISIONS_LOG.md`
5. The domain-specific file relevant to the current task

This ensures the AI never contradicts established decisions or misunderstands the system architecture.

---

## One rule above all others

**The files in this folder are the source of truth.** Not chat history, not memory from a previous session, not assumptions. If something isn't written down here, it hasn't been decided yet. If something is written down here, it should be respected unless explicitly updated with a new entry in the decisions log.
