"""Signal feed API routes — real-time(ish) event intelligence."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from src.stores.sqlite_store import get_store

router = APIRouter(tags=["signals"])


@router.get("/signals")
def list_signals(
    since: Optional[str] = Query(None, description="ISO timestamp — return signals after this time"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, description="Max results"),
):
    """Get recent pipeline signals (event log)."""
    store = get_store()
    signals = store.get_signals(since=since, limit=limit)
    if event_type is not None:
        signals = [s for s in signals if s.get("event_type") == event_type]
    return {
        "count": len(signals),
        "signals": signals,
    }
