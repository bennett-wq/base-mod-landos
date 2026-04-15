"""Verify src/agents/ package structure. Tests in M2-3 onward replace these with real assertions."""

import pytest


def test_agents_package_importable():
    """AC M2-1.1: src.agents can be imported as a package."""
    import src.agents  # noqa: F401


def test_all_agent_modules_importable():
    """AC M2-1.2: all eight agent modules can be imported without error."""
    from src.agents import (  # noqa: F401
        zoning_extractor,
        permitted_use_checker,
        comp_narrator,
        incentive_agent,
        outreach_drafter,
        opportunity_hunter,
        land_bank_hunter,
        underwriter_agent,
    )


def test_zoning_extractor_importable():
    """AC M2-1.3.1 (updated M2-3): zoning_extractor is importable and extract_zoning is callable."""
    from src.agents.zoning_extractor import extract_zoning

    # M2-3 replaces the NotImplementedError stub; module must import without error.
    assert callable(extract_zoning)


def test_permitted_use_checker_importable():
    """AC M2-1.3.2 (updated M2-4): permitted_use_checker is importable and check_permitted_use is callable."""
    from src.agents.permitted_use_checker import check_permitted_use

    # M2-4 replaces the NotImplementedError stub; module must import without error.
    assert callable(check_permitted_use)


def test_comp_narrator_raises_not_implemented():
    """AC M2-1.3.3: comp_narrator stub raises NotImplementedError."""
    from src.agents.comp_narrator import narrate_comps

    with pytest.raises(NotImplementedError, match="comp_narrator not yet implemented \\(M2-5\\)"):
        narrate_comps("071020-04-001-000", "Washtenaw County")


def test_incentive_agent_raises_not_implemented():
    """AC M2-1.3.4: incentive_agent stub raises NotImplementedError."""
    from src.agents.incentive_agent import extract_incentives

    with pytest.raises(NotImplementedError, match="incentive_agent not yet implemented \\(M2-6\\)"):
        extract_incentives("Washtenaw County", "071020-04-001-000")


def test_outreach_drafter_raises_not_implemented():
    """AC M2-1.3.5: outreach_drafter stub raises NotImplementedError."""
    from src.agents.outreach_drafter import draft_outreach

    with pytest.raises(NotImplementedError, match="outreach_drafter not yet implemented \\(M2-7\\)"):
        draft_outreach("071020-04-001-000", {}, {})


def test_opportunity_hunter_raises_not_implemented():
    """AC M2-1.3.6: opportunity_hunter stub raises NotImplementedError."""
    from src.agents.opportunity_hunter import hunt_opportunities

    with pytest.raises(NotImplementedError, match="opportunity_hunter not yet implemented \\(M2-8\\)"):
        hunt_opportunities("Washtenaw County", "R1")


def test_land_bank_hunter_raises_not_implemented():
    """AC M2-1.3.7: land_bank_hunter stub raises NotImplementedError."""
    from src.agents.land_bank_hunter import hunt_land_banks

    with pytest.raises(NotImplementedError, match="land_bank_hunter not yet implemented \\(M2-9\\)"):
        hunt_land_banks("Washtenaw County")


def test_underwriter_agent_raises_not_implemented():
    """AC M2-1.3.8: underwriter_agent stub raises NotImplementedError."""
    from src.agents.underwriter_agent import underwrite

    with pytest.raises(NotImplementedError, match="underwriter_agent not yet implemented \\(M2-10\\)"):
        underwrite("071020-04-001-000", "Washtenaw County")
