# SESSION_RITUAL.md

## Purpose

This file defines the standard handoff and restart ritual for BaseMod LandOS so the project does not lose continuity between chat sessions, Claude Code sessions, or other agent/context resets.

This ritual does not replace the project docs. It tells humans and agents how to use them correctly.

---

## Core rule

Project truth lives in files, not in chat memory.

Every session must:
1. read into the project from the canonical docs
2. do scoped work
3. write back out through the handoff and logs

---

## Canonical continuity stack

When deciding what to trust, use this order:

1. `00_START_HERE.md`
2. `LANDOS_HANDOFF_MASTER.md`
3. `LANDOS_DECISIONS_LOG.md`
4. `SESSION_HANDOFF_CURRENT.md`
5. `NEXT_STEPS.md`
6. topic-specific architecture docs

---

## End-of-session ritual

### Step 1: Generate the handoff

Before ending any session, ask the model:

```text
Before we end this session, I want you to help me write a clean session handoff.

Please produce:
1. a concise summary of what was completed
2. the files that changed or were materially advanced
3. the key decisions that were locked
4. the unresolved questions still open
5. the single next highest-priority task
6. a short warning list of what not to drift into next
7. whether the current task is complete, partially complete, or blocked

Write it in a format I can paste directly into SESSION_HANDOFF_CURRENT.md. Do not rewrite project strategy. Just create the handoff.
```

### Step 2: Write the live baton

Either paste it manually into `SESSION_HANDOFF_CURRENT.md` or ask Claude Code to do it:

```text
Create or overwrite `SESSION_HANDOFF_CURRENT.md` in the project root.

Write the following content exactly as provided. Do not summarize it. Do not rewrite it. Do not change formatting. Do not add commentary.

[PASTE HANDOFF HERE]

Then confirm the file was saved.
```

### Step 3: Update the archive

Ask Claude Code:

```text
Create or update `SESSION_LOG.md` in the project root.

Rules:
- If it does not exist, create it.
- If it exists, append a new entry to the end.
- Do not rewrite earlier entries.
- Preserve markdown formatting exactly.

Add a new session entry using the current `SESSION_HANDOFF_CURRENT.md` as source material. Use this structure:

## [TODAY'S DATE] — [SHORT SESSION NAME]

### What was completed
[summary bullets]

### Files materially advanced
[file bullets]

### Key decisions locked
[decision bullets]

### Open items at checkpoint
[open item bullets]

### Next exact task
[one task]

### Do not drift into
[warning bullets]

### Task status
[complete / partially complete / blocked]

After saving, confirm the file was updated successfully.
```

### Step 4: Update canonical docs if needed

Only do this if something materially changed:

* update `LANDOS_DECISIONS_LOG.md` if a decision was locked or changed
* update `LANDOS_HANDOFF_MASTER.md` if the canonical architecture framing changed
* update `NEXT_STEPS.md` if priorities changed

### Step 5: Run the closeout confirmation check

```text
Before we end this session, please do this closeout check:

1. Confirm that `SESSION_RITUAL.md` exists in the project root and was written successfully.
2. Confirm that `SESSION_HANDOFF_CURRENT.md` is the current live handoff file and reflects the latest project state. If it does not, update it now without changing the architecture.
3. Confirm that `SESSION_LOG.md` exists and has the latest checkpoint appended. If it does not, append it now.
4. Tell me whether any canonical docs should also be updated before I leave:
   - `LANDOS_DECISIONS_LOG.md`
   - `LANDOS_HANDOFF_MASTER.md`
   - `NEXT_STEPS.md`

After that, give me a short confirmation of the status of all of the above.
```

---

## Start-of-session ritual for ChatGPT

Use this prompt when starting a new ChatGPT session:

```text
We are continuing work on BaseMod LandOS — Event Mesh ("Land Swarm").

This project has canonical file-based memory. Treat the files as source of truth, not prior chat memory.

Here is the current session handoff:

[PASTE SESSION_HANDOFF_CURRENT.md]

Important rules:
- preserve the architecture
- do not invent new strategy unless asked
- continue from the current critical path
- use the handoff and canonical docs as the authoritative context

My immediate task for this session is:
[insert exact next task]
```

---

## Start-of-session ritual for Claude Code

Use this prompt when starting a new Claude Code session:

```text
We are continuing work on BaseMod LandOS — Event Mesh ("Land Swarm").

This repo has canonical project memory in markdown files. Read from files, not assumed chat memory.

Before doing anything substantive, read in this order:
1. `00_START_HERE.md`
2. `LANDOS_HANDOFF_MASTER.md`
3. `LANDOS_DECISIONS_LOG.md`
4. `SESSION_HANDOFF_CURRENT.md`
5. `NEXT_STEPS.md`
6. the topic-specific file relevant to the current task

Current task:
[insert exact next task]

Important:
- do not invent new strategy unless asked
- do not drift into implementation unless explicitly directed
- preserve the architecture
- update `SESSION_HANDOFF_CURRENT.md` before ending the session if material progress is made
```

---

## Main rule

Never start a new session with vague prompts like:

* "continue where we left off"
* "pick up from before"
* "you know the project"

Always start with:

* current handoff
* current critical path
* exact next task

---

## End-of-session checklist

Before closing any session, ask:

* Did we change architecture?
* Did we lock any decisions?
* Did we change priorities?
* Did we finish the current task?
* What is the exact next task?
* What should the next agent absolutely not mess up?

If those are captured, continuity is safe.

---

## Minimum viable continuity system

If time is tight, the minimum good system is:

**Before ending:**

* save what got done
* save what changed
* save what's next
* save what not to mess up
* record whether the task is complete, partial, or blocked

**Before starting:**

* paste `SESSION_HANDOFF_CURRENT.md`
* state the exact next task
* tell the model to use file-based memory as truth

---

## Notes

`SESSION_HANDOFF_CURRENT.md` is the live baton.
`SESSION_LOG.md` is the historical archive.
This file (`SESSION_RITUAL.md`) is the operating manual for continuity.
