"""Underwriter agent — orchestrator, fan out to all agents, run engine, emit parcel_underwritten.

Implemented in M2-10.
"""


def underwrite(parcel_id: str, municipality: str) -> dict:
    """Orchestrate the full underwriting pipeline for a parcel.

    Fans out to all seven agents, runs the engine, produces OpportunityUnderwriting,
    and emits parcel_underwritten event.

    Args:
        parcel_id: e.g., "071020-04-001-000"
        municipality: e.g., "Washtenaw County"

    Returns:
        dict: OpportunityUnderwriting model with full analysis

    Raises:
        NotImplementedError: underwriter_agent not yet implemented (M2-10)
    """
    raise NotImplementedError("underwriter_agent not yet implemented (M2-10)")
