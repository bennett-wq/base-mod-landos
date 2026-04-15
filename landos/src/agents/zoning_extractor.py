"""Zoning extractor — read Tier 1 municipality note + Municode, return setback JSON.

Implemented in M2-3.
"""


def extract_zoning(municipality: str, district: str) -> dict:
    """Extract setback and zoning rules for a given municipality/district.

    Args:
        municipality: e.g., "Washtenaw County"
        district: e.g., "R1" zoning district code

    Returns:
        dict with setback JSON: {setback_front, setback_side, setback_rear, etc.}

    Raises:
        NotImplementedError: zoning_extractor not yet implemented (M2-3)
    """
    raise NotImplementedError("zoning_extractor not yet implemented (M2-3)")
