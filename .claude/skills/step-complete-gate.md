# LANDOS_STEP_COMPLETE Gate

No agent declares done without ALL:
1. cd landos && python3 -m pytest tests/ -v exits 0
2. All tests pass (existing baseline + new step tests)
3. validator-agent confirms: VALIDATION RESULT: PASS
4. Final message contains exact string: LANDOS_STEP_COMPLETE

On failure: report to PM Agent. Do not retry blindly.
On success: PM Agent updates SESSION_HANDOFF_CURRENT.md,
NEXT_STEPS.md, SESSION_LOG.md.
