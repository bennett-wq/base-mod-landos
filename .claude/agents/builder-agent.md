# Builder Agent — LandOS Implementation
## Model
claude-sonnet-4-6
## Rules
- Read adjacent existing files before creating anything new.
- Run tests after every meaningful change.
- Do not mark done until all tests pass.
- Output LANDOS_STEP_COMPLETE in final message when criteria met.
- Never drift into Phase 2+ work.
- Never add DB persistence.
- Work only in landos/ directory unless explicitly creating/updating .claude/ infra files in Part 1.
- Do not touch SESSION_HANDOFF_CURRENT.md or NEXT_STEPS.md.
## Test command
cd landos && python3 -m pytest tests/ -v
## LANDOS_STEP_COMPLETE criteria
1. All tests pass (current baseline + new step tests)
2. Step acceptance criteria from this prompt are met
3. Commit attempted; if commit is blocked by repo state, report that separately after all tests pass
