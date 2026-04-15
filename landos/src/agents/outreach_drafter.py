"""Outreach drafter — draft offer letters to vault _drafts/ (NEVER sends email).

Implemented in M2-7.
"""


def draft_outreach(parcel_id: str, contact_info: dict, opportunity: dict) -> str:
    """Draft an offer letter and write it to vault _drafts/ directory.

    Args:
        parcel_id: e.g., "071020-04-001-000"
        contact_info: {name, email, phone} of property contact
        opportunity: OpportunityUnderwriting model

    Returns:
        str: path to drafted file in _drafts/

    Raises:
        NotImplementedError: outreach_drafter not yet implemented (M2-7)
    """
    raise NotImplementedError("outreach_drafter not yet implemented (M2-7)")
