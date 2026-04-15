"""Land bank hunter — scheduled adapter for Genesee/Wayne/Washtenaw land banks, emit parcel_discovered.

Implemented in M2-9.
"""


def hunt_land_banks(municipality: str) -> list:
    """Query municipal/county land bank and surplus property catalogs.

    Args:
        municipality: e.g., "Washtenaw County"

    Returns:
        list: [parcel_ids] discovered from land bank inventories

    Raises:
        NotImplementedError: land_bank_hunter not yet implemented (M2-9)
    """
    raise NotImplementedError("land_bank_hunter not yet implemented (M2-9)")
