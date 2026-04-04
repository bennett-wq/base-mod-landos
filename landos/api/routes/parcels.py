"""Parcel API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from src.stores.sqlite_store import get_store

router = APIRouter(tags=["parcels"])


@router.get("/parcels")
def list_parcels(
    cluster_id: Optional[str] = Query(None, description="Get parcels for a specific cluster"),
    limit: int = Query(200, description="Max results"),
):
    """Get parcels, optionally filtered by cluster."""
    store = get_store()
    if cluster_id:
        all_clusters = store.get_all_clusters()
        cluster = next(
            (c for c in all_clusters if c.get("cluster_id") == cluster_id),
            None,
        )
        if cluster is None:
            return {"count": 0, "parcels": []}
        parcel_ids = cluster.get("parcel_ids", [])
        parcels = store.get_parcels_by_cluster([str(pid) for pid in parcel_ids[:limit]])
    else:
        return {
            "total": store.get_total_parcel_count(),
            "vacant": store.get_vacant_parcel_count(),
            "message": "Use ?cluster_id=<id> to get parcels for a specific cluster",
        }
    return {
        "count": len(parcels),
        "parcels": parcels,
    }
