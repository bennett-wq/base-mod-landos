"""Opportunity hunter — consume area_favorable events, re-query Spark, emit parcel_discovered.

Implemented in M2-8.
"""


def hunt_opportunities(municipality: str, zone: str) -> list:
    """Re-query Spark for active land listings in a favorable area.

    Args:
        municipality: e.g., "Washtenaw County"
        zone: zoning district code, e.g., "R1"

    Returns:
        list: [parcel_ids] of newly discovered parcels

    Raises:
        NotImplementedError: opportunity_hunter not yet implemented (M2-8)
    """
    raise NotImplementedError("opportunity_hunter not yet implemented (M2-8)")
