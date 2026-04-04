"""Opportunity API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from src.stores.sqlite_store import get_store

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
def list_opportunities(
    opp_type: Optional[str] = Query(None, description="Filter by type (STALLED_SUBDIVISION, etc.)"),
    limit: int = Query(100, description="Max results"),
):
    """List all detected opportunities."""
    store = get_store()
    opps = store.get_all_opportunities(opp_type=opp_type)
    return {
        "count": len(opps[:limit]),
        "total": len(opps),
        "opportunities": opps[:limit],
    }


@router.get("/opportunities/stalled")
def stalled_subdivisions():
    """Get all stalled subdivision opportunities specifically."""
    store = get_store()
    subs = store.get_stalled_subdivisions()
    return {
        "count": len(subs),
        "stalled_subdivisions": subs,
    }
