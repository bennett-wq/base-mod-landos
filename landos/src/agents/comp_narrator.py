"""Comp narrator — the three-comp-set agent, return anchor comp + exit $/sf + confidence.

Implemented in M2-5.
"""


def narrate_comps(parcel_id: str, municipality: str) -> dict:
    """Retrieve and narrate three comparable sales from Spark data.

    Args:
        parcel_id: e.g., "071020-04-001-000" (APN)
        municipality: e.g., "Washtenaw County"

    Returns:
        dict: {anchor_comp: CompData, exit_per_sqft: float, confidence: float, rationale: str}

    Raises:
        NotImplementedError: comp_narrator not yet implemented (M2-5)
    """
    raise NotImplementedError("comp_narrator not yet implemented (M2-5)")
