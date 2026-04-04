"""Strategic opportunity routes — THE product feature.

GET /strategic?min_lots=5&infrastructure=true

This is the query that surfaces 5+ lot, infrastructure-invested stranded
lot opportunities. This is what makes BaseMod different.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from src.stores.sqlite_store import get_store

router = APIRouter(tags=["strategic"])


@router.get("/strategic")
def list_strategic_opportunities(
    min_lots: Optional[int] = Query(None, description="Minimum lot count (use 5 for primary targets)"),
    infrastructure: Optional[bool] = Query(None, description="Only infrastructure-invested opportunities"),
    limit: int = Query(100, description="Max results"),
):
    """Get ranked strategic opportunities — the primary acquisition target list.

    The key query: /strategic?min_lots=5&infrastructure=true
    Returns stalled subdivisions and large clusters with infrastructure invested,
    ranked by composite score.
    """
    store = get_store()
    opps = store.get_strategic_opportunities(
        min_lots=min_lots,
        infrastructure_only=infrastructure or False,
        limit=limit,
    )
    return {
        "count": len(opps),
        "query": {
            "min_lots": min_lots,
            "infrastructure_only": infrastructure,
        },
        "opportunities": opps,
    }
