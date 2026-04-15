"""Permitted use checker — read Sec. 406 permitted uses, return {allowed, path, citation}.

Implemented in M2-4.
"""


def check_permitted_use(model_type: str, district: str, municipality: str) -> dict:
    """Check if a model type is permitted in a given zoning district.

    Args:
        model_type: e.g., "modular_home_single_family"
        district: e.g., "R1" zoning district code
        municipality: e.g., "Washtenaw County"

    Returns:
        dict: {allowed: bool, path: str, citation: str, rationale: str}

    Raises:
        NotImplementedError: permitted_use_checker not yet implemented (M2-4)
    """
    raise NotImplementedError("permitted_use_checker not yet implemented (M2-4)")
