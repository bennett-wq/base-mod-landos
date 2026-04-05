#!/usr/bin/env python3
"""Run the full LandOS ingestion pipeline: Spark → Regrid → Parcel Clusters → Listing Clusters.

Orchestrates four stages in sequence:
  1. Spark MLS: Fetch live land listings → normalize → BBO signals → trigger routing
  2. Regrid CSV: Load Washtenaw County parcels → link to listings → score → trigger routing
  3. Parcel Cluster Detection: Filter to VACANT parcels → cluster by owner/subdivision/proximity
     → cross-reference each cluster against Spark listings for BBO signals
  4. Listing Cluster Detection: Scan listings for agent/office patterns

This produces the complete signal picture for Washtenaw County.

Usage:
    python3 landos/scripts/run_full_pipeline.py
    python3 landos/scripts/run_full_pipeline.py --top 200 --regrid-limit 5000
    python3 landos/scripts/run_full_pipeline.py --county Washtenaw
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so `from src...` imports work.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.adapters.cluster.detector import ClusterDetector
from src.adapters.cluster.parcel_cluster_detector import ParcelClusterDetector
from src.adapters.cluster.store import InMemoryClusterStore
from src.adapters.regrid.ingestion import (
    RegridIngestionAdapter,
    InMemoryParcelStore,
    InMemoryOwnerStore,
)
from src.adapters.spark.ingestion import SparkIngestionAdapter, InMemoryListingStore
from src.models.enums import VacancyStatus
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES

# Re-use CSV loader from the standalone script
from scripts.ingest_regrid_csv import (
    DEFAULT_CSV,
    WASHTENAW_MUNICIPALITY_ID,
    load_csv_records,
)
from scripts.ingest_spark_live import fetch_listings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full LandOS ingestion pipeline")
    parser.add_argument("--top", type=int, default=200, help="Max Spark listings to fetch")
    parser.add_argument("--county", default="Washtenaw", help="County filter for Spark")
    parser.add_argument("--regrid-csv", default=str(DEFAULT_CSV), help="Path to Regrid CSV")
    parser.add_argument("--regrid-limit", type=int, default=None, help="Limit Regrid records")
    parser.add_argument("--skip-spark", action="store_true", help="Skip Spark ingestion (Regrid + clusters only)")
    args = parser.parse_args()

    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key and not args.skip_spark:
        print("ERROR: SPARK_API_KEY not set. Add it to .env or use --skip-spark.", file=sys.stderr)
        sys.exit(1)

    # Shared engine and context across all stages
    engine = TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())
    context = TriggerContext()

    all_results = []
    stage_stats = {}

    print()
    print("=" * 70)
    print("  LandOS — Full Pipeline Run")
    print("=" * 70)

    # ── Stage 1: Spark MLS ────────────────────────────────────────────────
    listing_store = InMemoryListingStore()
    if not args.skip_spark:
        print("\n  STAGE 1: Spark MLS Ingestion")
        print("  " + "-" * 40)
        t0 = time.time()

        raw_spark = fetch_listings(api_key, top=args.top, county=args.county)
        spark_adapter = SparkIngestionAdapter(engine=engine, context=context, store=listing_store)

        print("  Processing through SparkIngestionAdapter...")
        spark_results = spark_adapter.process_batch(raw_spark)
        all_results.extend(spark_results)

        elapsed = time.time() - t0
        stage_stats["spark"] = {
            "listings": len(listing_store),
            "events": len(spark_results),
            "fired": sum(len(r.fired_rules) for r in spark_results),
            "seconds": round(elapsed, 1),
        }
        print(f"  Stage 1 complete: {len(listing_store)} listings, "
              f"{len(spark_results)} events ({elapsed:.1f}s)")
    else:
        print("\n  STAGE 1: Skipped (--skip-spark)")
        stage_stats["spark"] = {"listings": 0, "events": 0, "fired": 0, "seconds": 0}

    # ── Stage 2: Regrid CSV ───────────────────────────────────────────────
    print("\n  STAGE 2: Regrid CSV Ingestion")
    print("  " + "-" * 40)
    t0 = time.time()

    csv_path = Path(args.regrid_csv)
    raw_regrid = load_csv_records(csv_path, limit=args.regrid_limit, vacant_only=True)

    listings_for_linkage = listing_store.all_listings()
    parcel_store = InMemoryParcelStore()
    owner_store = InMemoryOwnerStore()

    regrid_adapter = RegridIngestionAdapter(
        engine=engine,
        listings=listings_for_linkage,
        context=context,
        parcel_store=parcel_store,
        owner_store=owner_store,
        default_municipality_id=WASHTENAW_MUNICIPALITY_ID,
    )

    # Process in batches for progress
    batch_size = 5000
    regrid_results = []
    total = len(raw_regrid)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = raw_regrid[start:end]
        results = regrid_adapter.process_batch(batch)
        regrid_results.extend(results)
        print(f"    Processed {end}/{total} records ({len(regrid_results)} events so far)")

    all_results.extend(regrid_results)
    elapsed = time.time() - t0

    # Count vacant parcels for the report
    all_parcels = list(parcel_store._parcels.values())
    vacant_count = sum(1 for p in all_parcels if p.vacancy_status == VacancyStatus.VACANT)

    stage_stats["regrid"] = {
        "parcels": len(parcel_store),
        "vacant": vacant_count,
        "improved": len(parcel_store) - vacant_count,
        "owners": len(owner_store),
        "events": len(regrid_results),
        "fired": sum(len(r.fired_rules) for r in regrid_results),
        "seconds": round(elapsed, 1),
    }
    print(f"  Stage 2 complete: {len(parcel_store)} parcels "
          f"({vacant_count} vacant, {len(parcel_store) - vacant_count} improved/unknown), "
          f"{len(owner_store)} owners ({elapsed:.1f}s)")

    # ── Stage 3: PARCEL Cluster Detection (the main event) ────────────────
    print("\n  STAGE 3: Vacant Parcel Cluster Detection")
    print("  " + "-" * 40)
    t0 = time.time()

    parcel_cluster_store = InMemoryClusterStore()
    parcel_detector = ParcelClusterDetector(
        engine=engine,
        context=context,
        cluster_store=parcel_cluster_store,
    )

    all_listings = listing_store.all_listings()
    print(f"  Scanning {vacant_count} vacant parcels for clusters...")
    print(f"  Cross-referencing against {len(all_listings)} Spark listings...")

    parcel_cluster_results, parcel_clusters = parcel_detector.scan(
        all_parcels, all_listings
    )
    all_results.extend(parcel_cluster_results)

    elapsed = time.time() - t0

    # Breakdown by cluster type
    owner_clusters = [c for c in parcel_clusters if c.cluster_type == "owner"]
    sub_clusters = [c for c in parcel_clusters if c.cluster_type == "subdivision"]
    prox_clusters = [c for c in parcel_clusters if c.cluster_type == "proximity"]
    clusters_with_listings = [c for c in parcel_clusters if c.matched_listings]

    stage_stats["parcel_clusters"] = {
        "total_clusters": len(parcel_clusters),
        "owner_clusters": len(owner_clusters),
        "subdivision_clusters": len(sub_clusters),
        "proximity_clusters": len(prox_clusters),
        "clusters_with_listings": len(clusters_with_listings),
        "events": len(parcel_cluster_results),
        "seconds": round(elapsed, 1),
    }
    print(f"  Stage 3 complete: {len(parcel_clusters)} clusters "
          f"({len(owner_clusters)} owner, {len(sub_clusters)} subdivision, "
          f"{len(prox_clusters)} proximity)")
    print(f"  Clusters with active listings: {len(clusters_with_listings)}")

    # ── Stage 4: Listing Cluster Detection (agent/office) ─────────────────
    print("\n  STAGE 4: Listing Agent/Office Clusters")
    print("  " + "-" * 40)
    t0 = time.time()

    listing_cluster_store = InMemoryClusterStore()
    listing_detector = ClusterDetector(
        engine=engine, context=context, cluster_store=listing_cluster_store
    )
    listing_cluster_results = listing_detector.scan_listings(all_listings)
    all_results.extend(listing_cluster_results)

    elapsed = time.time() - t0
    stage_stats["listing_clusters"] = {
        "clusters": len(listing_cluster_store),
        "events": len(listing_cluster_results),
        "seconds": round(elapsed, 1),
    }
    print(f"  Stage 4 complete: {len(listing_cluster_store)} listing clusters ({elapsed:.1f}s)")

    # ── Final report ──────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  FULL PIPELINE REPORT")
    print("=" * 70)

    print("\n  Stage summary:")
    for stage, stats in stage_stats.items():
        print(f"    {stage:>18}: {stats}")

    total_events = len(all_results)
    total_fired = sum(len(r.fired_rules) for r in all_results)
    print(f"\n  Total events:  {total_events}")
    print(f"  Total fired:   {total_fired}")

    # ── Parcel cluster detail (the key output) ────────────────────────────
    print()
    print("=" * 70)
    print("  VACANT PARCEL CLUSTERS — TOP FINDINGS")
    print("=" * 70)

    # Owner clusters: sorted by parcel count descending
    if owner_clusters:
        print(f"\n  OWNER CLUSTERS ({len(owner_clusters)} total) — same owner, multiple vacant parcels:")
        for c in sorted(owner_clusters, key=lambda x: -x.parcel_count)[:20]:
            listing_flag = f" ** {len(c.matched_listings)} ACTIVE LISTING(S)" if c.matched_listings else ""
            print(f"    {c.group_key}: {c.parcel_count} parcels, "
                  f"{c.total_acreage:.1f} acres{listing_flag}")
            if c.matched_listings:
                for l in c.matched_listings:
                    cdom = f"CDOM={l.cdom}" if l.cdom else ""
                    remarks = ""
                    if l.private_remarks:
                        remarks = f" | Pvt: {l.private_remarks[:60]}..."
                    print(f"      → ${l.list_price:,.0f} | {l.address_raw or 'no addr'} | {cdom}{remarks}")

    # Subdivision clusters
    if sub_clusters:
        print(f"\n  SUBDIVISION CLUSTERS ({len(sub_clusters)} total) — vacant lots in same subdivision:")
        for c in sorted(sub_clusters, key=lambda x: -x.parcel_count)[:20]:
            listing_flag = f" ** {len(c.matched_listings)} LISTING(S)" if c.matched_listings else ""
            owners = len({p.owner_name_raw for p in c.parcels if p.owner_name_raw})
            print(f"    {c.group_key}: {c.parcel_count} vacant lots, "
                  f"{owners} owners, {c.total_acreage:.1f} acres{listing_flag}")

    # Proximity clusters
    if prox_clusters:
        print(f"\n  PROXIMITY CLUSTERS ({len(prox_clusters)} total) — nearby vacant parcels:")
        for c in sorted(prox_clusters, key=lambda x: -x.parcel_count)[:20]:
            listing_flag = f" ** {len(c.matched_listings)} LISTING(S)" if c.matched_listings else ""
            owners = len({p.owner_name_raw for p in c.parcels if p.owner_name_raw})
            print(f"    @{c.group_key}: {c.parcel_count} parcels, "
                  f"{owners} owners, {c.total_acreage:.1f} acres{listing_flag}")

    # ── Clusters with listings (highest priority) ─────────────────────────
    if clusters_with_listings:
        print()
        print("=" * 70)
        print(f"  HIGH-PRIORITY: {len(clusters_with_listings)} CLUSTERS WITH ACTIVE LISTINGS")
        print("=" * 70)
        for c in sorted(clusters_with_listings, key=lambda x: -len(x.matched_listings)):
            print(f"\n  [{c.cluster_type.upper()}] {c.group_key}: "
                  f"{c.parcel_count} parcels, {c.total_acreage:.1f} acres")
            for l in c.matched_listings:
                cdom = f"CDOM={l.cdom}" if l.cdom else ""
                status = l.standard_status.value if l.standard_status else "?"
                agent = l.listing_agent_name or l.listing_agent_id or "?"
                office = l.listing_office_name or l.listing_office_id or "?"
                print(f"    LISTING: ${l.list_price:,.0f} | {status} | {cdom}")
                print(f"      Address: {l.address_raw or '?'}")
                print(f"      Agent: {agent} | Office: {office}")
                if l.private_remarks:
                    print(f"      Private Remarks: {l.private_remarks[:120]}...")
                if l.subdivision_name_raw:
                    print(f"      Subdivision: {l.subdivision_name_raw}")
                if l.seller_name_raw:
                    print(f"      Seller: {l.seller_name_raw}")

    # Event breakdown
    event_counts: dict[str, int] = {}
    for r in all_results:
        event_counts[r.event_type] = event_counts.get(r.event_type, 0) + 1
    print("\n  All events by type:")
    for etype, count in sorted(event_counts.items(), key=lambda x: -x[1]):
        print(f"    {etype}: {count}")

    print()
    print("=" * 70)
    print("  Pipeline complete.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
