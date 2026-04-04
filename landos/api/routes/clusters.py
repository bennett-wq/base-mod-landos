"""Cluster API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from src.stores.sqlite_store import get_store

router = APIRouter(tags=["clusters"])


@router.get("/clusters")
def list_clusters(
    min_lots: Optional[int] = Query(None, description="Minimum lot/parcel count"),
    cluster_type: Optional[str] = Query(None, description="Filter by cluster type (owner, subdivision, proximity)"),
    has_listings: Optional[bool] = Query(None, description="Only clusters with active listings"),
    limit: int = Query(500, description="Max results"),
):
    """List all detected parcel clusters with optional filtering."""
    store = get_store()
    clusters = store.get_all_clusters(
        min_lots=min_lots,
        cluster_type=cluster_type,
    )
    if has_listings is not None and has_listings:
        clusters = [c for c in clusters if c.get("_has_active_listings")]
    return {
        "count": len(clusters[:limit]),
        "total": len(clusters),
        "clusters": clusters[:limit],
    }


@router.get("/clusters/{cluster_id}")
def get_cluster(cluster_id: str):
    """Get a single cluster by ID with associated parcels."""
    store = get_store()
    all_clusters = store.get_all_clusters()
    cluster = next(
        (c for c in all_clusters if c.get("cluster_id") == cluster_id),
        None,
    )
    if cluster is None:
        return {"error": "Cluster not found"}

    parcel_ids = cluster.get("parcel_ids", [])
    parcels = store.get_parcels_by_cluster([str(pid) for pid in parcel_ids]) if parcel_ids else []

    return {
        "cluster": cluster,
        "parcels": parcels,
    }
