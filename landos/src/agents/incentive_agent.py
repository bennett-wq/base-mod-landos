"""Incentive agent — read Programs & Incentives Tier 1 note, return {programs, net_estimate}.

Emits area_favorable when new programs found. Implemented in M2-6.
"""


def extract_incentives(municipality: str, parcel_id: str) -> dict:
    """Extract applicable incentive programs from municipality Tier 1 note.

    Args:
        municipality: e.g., "Washtenaw County"
        parcel_id: e.g., "071020-04-001-000"

    Returns:
        dict: {programs: [Program], net_incentive_estimate: float}

    Raises:
        NotImplementedError: incentive_agent not yet implemented (M2-6)
    """
    raise NotImplementedError("incentive_agent not yet implemented (M2-6)")
