"""Pipeline stats API routes — aggregate metrics for the NEXUS MetricsStrip."""

from __future__ import annotations

from fastapi import APIRouter

from src.stores.sqlite_store import get_store

router = APIRouter(tags=["stats"])


@router.get("/stats")
def pipeline_stats():
    """Get aggregate pipeline statistics for the dashboard."""
    store = get_store()
    stored_stats = store.get_all_stats()

    return {
        "active_listings": store.get_listing_count(),
        "total_parcels": store.get_total_parcel_count(),
        "vacant_parcels": store.get_vacant_parcel_count(),
        "clusters": store.get_cluster_count(),
        "clusters_with_listings": store.get_clusters_with_listings_count(),
        "opportunities": store.get_opportunity_count(),
        "pipeline_run": stored_stats,
    }
