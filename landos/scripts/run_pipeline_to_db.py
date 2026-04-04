#!/usr/bin/env python3
"""Run the full LandOS pipeline and persist results to SQLite.

This is the bridge between the Python event mesh and the FastAPI server.
After running, the API at /api/* serves real intelligence from the DB.

Usage:
    python3 landos/scripts/run_pipeline_to_db.py
    python3 landos/scripts/run_pipeline_to_db.py --top 200 --regrid-limit 5000
    python3 landos/scripts/run_pipeline_to_db.py --skip-spark  # Regrid + clusters only
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.adapters.cluster.detector import ClusterDetector
from src.adapters.cluster.parcel_cluster_detector import ParcelClusterDetector
from src.adapters.cluster.store import InMemoryClusterStore
from src.adapters.municipal.store import InMemoryMunicipalEventStore
from src.adapters.regrid.ingestion import (
    RegridIngestionAdapter,
    InMemoryParcelStore,
    InMemoryOwnerStore,
)
from src.adapters.spark.ingestion import SparkIngestionAdapter, InMemoryListingStore
from src.adapters.stallout.detector import StallAssessment, detect_stall
from src.models.development import Subdivision
from src.models.enums import InfrastructureStatus, MunicipalEventType, VacancyStatus
from src.models.municipality import MunicipalEvent
from src.scoring.listing_history_signals import analyze_cluster_listing_history, ListingHistoryEvidence
from src.scoring.strategic_ranker import rank_from_pipeline, StrategicOpportunity
from src.stores.sqlite_store import SQLiteStore
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES

from scripts.ingest_regrid_csv import (
    DEFAULT_CSV,
    WASHTENAW_MUNICIPALITY_ID,
    load_csv_records,
)
from scripts.ingest_spark_live import fetch_listings, fetch_all_statuses


def _routing_result_to_signal(r) -> dict:
    """Convert a RoutingResult into a signal record for the DB."""
    entity_parts = []
    if hasattr(r, 'event_id'):
        pass  # event_id stored separately
    fired = [fr.rule_id if hasattr(fr, 'rule_id') else str(fr) for fr in r.fired_rules] if r.fired_rules else []

    # Build entity ref summary from the routing result
    entity_summary = r.event_type
    payload_summary = ""
    if hasattr(r, 'wake_instructions') and r.wake_instructions:
        payload_summary = f"{len(r.wake_instructions)} wake instructions"

    return {
        "event_type": r.event_type,
        "event_id": str(r.event_id) if hasattr(r, 'event_id') else "",
        "entity_ref_summary": entity_summary,
        "fired_rules": fired,
        "payload_summary": payload_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LandOS pipeline → SQLite")
    parser.add_argument("--top", type=int, default=200, help="Max Spark listings")
    parser.add_argument("--county", default="Washtenaw", help="County filter")
    parser.add_argument("--regrid-csv", default=str(DEFAULT_CSV), help="Regrid CSV path")
    parser.add_argument("--regrid-limit", type=int, default=None, help="Limit Regrid records")
    parser.add_argument("--skip-spark", action="store_true", help="Skip Spark ingestion")
    parser.add_argument("--historical", action="store_true", default=True,
                        help="Pull all statuses (Active+Closed+Withdrawn+Expired+Canceled+Pending). Default: True")
    parser.add_argument("--active-only", action="store_true",
                        help="Pull only Active listings (override --historical)")
    parser.add_argument("--db", default=None, help="SQLite DB path (default: landos/data/landos.db)")
    args = parser.parse_args()

    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key and not args.skip_spark:
        print("ERROR: SPARK_API_KEY not set. Add it to .env or use --skip-spark.", file=sys.stderr)
        sys.exit(1)

    # Initialize SQLite store
    db = SQLiteStore(db_path=args.db) if args.db else SQLiteStore()
    print(f"\n  Database: {db.db_path}")

    # Shared engine
    engine = TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())
    context = TriggerContext()

    all_results = []
    stage_stats = {}

    print()
    print("=" * 70)
    print("  LandOS — Pipeline to Database")
    print("=" * 70)

    # ── Stage 1: Spark MLS ────────────────────────────────────────────────
    listing_store = InMemoryListingStore()
    if not args.skip_spark:
        print("\n  STAGE 1: Spark MLS Ingestion")
        print("  " + "-" * 40)
        t0 = time.time()

        if args.active_only:
            raw_spark = fetch_listings(api_key, top=args.top, county=args.county)
        else:
            raw_spark = fetch_all_statuses(api_key, top_per_status=args.top, county=args.county)
        spark_adapter = SparkIngestionAdapter(engine=engine, context=context, store=listing_store)
        spark_results = spark_adapter.process_batch(raw_spark)
        all_results.extend(spark_results)

        elapsed = time.time() - t0
        stage_stats["spark"] = {
            "listings": len(listing_store),
            "events": len(spark_results),
            "fired": sum(len(r.fired_rules) for r in spark_results),
            "seconds": round(elapsed, 1),
        }

        # Persist listings to SQLite
        all_ingested_listings = listing_store.all_listings()
        print(f"  Saving {len(listing_store)} listings to DB...")
        db.save_listings_batch(all_ingested_listings)

        # Also persist to history table (every run adds snapshots)
        print(f"  Saving {len(all_ingested_listings)} listing snapshots to history...")
        db.save_listing_history_batch(all_ingested_listings)

        print(f"  Stage 1: {len(listing_store)} listings ({elapsed:.1f}s)")
    else:
        print("\n  STAGE 1: Skipped (--skip-spark)")
        stage_stats["spark"] = {"listings": 0, "events": 0, "fired": 0, "seconds": 0}

    # ── Stage 2: Regrid CSV ───────────────────────────────────────────────
    print(f"\n  STAGE 2: Regrid CSV Ingestion")
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

    batch_size = 5000
    regrid_results = []
    total = len(raw_regrid)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = raw_regrid[start:end]
        results = regrid_adapter.process_batch(batch)
        regrid_results.extend(results)
        print(f"    Processed {end}/{total} records ({len(regrid_results)} events)")

    all_results.extend(regrid_results)
    elapsed = time.time() - t0

    all_parcels = list(parcel_store._parcels.values())
    vacant_count = sum(1 for p in all_parcels if p.vacancy_status == VacancyStatus.VACANT)

    stage_stats["regrid"] = {
        "parcels": len(parcel_store),
        "vacant": vacant_count,
        "owners": len(owner_store),
        "events": len(regrid_results),
        "seconds": round(elapsed, 1),
    }

    # Persist parcels to SQLite
    print(f"  Saving {len(parcel_store)} parcels to DB...")
    db.save_parcels_batch(all_parcels)

    print(f"  Stage 2: {len(parcel_store)} parcels ({vacant_count} vacant) ({elapsed:.1f}s)")

    # ── Stage 3: Parcel Cluster Detection ─────────────────────────────────
    print(f"\n  STAGE 3: Vacant Parcel Cluster Detection")
    print("  " + "-" * 40)
    t0 = time.time()

    parcel_cluster_store = InMemoryClusterStore()
    parcel_detector = ParcelClusterDetector(
        engine=engine,
        context=context,
        cluster_store=parcel_cluster_store,
    )

    all_listings = listing_store.all_listings()
    parcel_cluster_results, parcel_clusters = parcel_detector.scan(all_parcels, all_listings)
    all_results.extend(parcel_cluster_results)

    elapsed = time.time() - t0

    owner_clusters = [c for c in parcel_clusters if c.cluster_type == "owner"]
    sub_clusters = [c for c in parcel_clusters if c.cluster_type == "subdivision"]
    prox_clusters = [c for c in parcel_clusters if c.cluster_type == "proximity"]
    clusters_with_listings = [c for c in parcel_clusters if c.matched_listings]

    stage_stats["parcel_clusters"] = {
        "total": len(parcel_clusters),
        "owner": len(owner_clusters),
        "subdivision": len(sub_clusters),
        "proximity": len(prox_clusters),
        "with_listings": len(clusters_with_listings),
        "seconds": round(elapsed, 1),
    }

    # Persist clusters to SQLite
    print(f"  Saving {len(parcel_cluster_store)} clusters to DB...")
    cluster_batch = []
    for stored_cluster in parcel_cluster_store.all():
        # Find matching ParcelClusterResult for enrichment
        matching_pcr = next(
            (c for c in parcel_clusters
             if c.group_key == stored_cluster.detection_method.split(":")[-1]
             or len([p for p in c.parcels if p.parcel_id in (stored_cluster.parcel_ids or [])]) > 0),
            None,
        )
        pcr_parcel_count = matching_pcr.parcel_count if matching_pcr else stored_cluster.member_count
        pcr_listing_count = len(matching_pcr.matched_listings) if matching_pcr else 0
        pcr_has_listings = pcr_listing_count > 0
        group_key = matching_pcr.group_key if matching_pcr else ""
        cluster_batch.append((stored_cluster, group_key, pcr_parcel_count, pcr_listing_count, pcr_has_listings))
    db.save_clusters_batch(cluster_batch)

    print(f"  Stage 3: {len(parcel_clusters)} clusters "
          f"({len(owner_clusters)} owner, {len(sub_clusters)} subdivision, "
          f"{len(prox_clusters)} proximity) ({elapsed:.1f}s)")

    # ── Stage 3.5: Subdivision Materialization + Stallout Detection ───────
    # Subdivision-type clusters come from legal description parsing (e.g.,
    # "LOT 5 SMITH ACRES SUB"). In Michigan, a recorded subdivision plat
    # requires infrastructure plans and performance bonds, so the existence
    # of a platted subdivision IS evidence of infrastructure investment.
    # We materialize Subdivision objects, create domain-justified ROADS_INSTALLED
    # events, and run the stallout detector to get real stall_confidence scores.
    print(f"\n  STAGE 3.5: Stallout Detection on Subdivision Clusters")
    print("  " + "-" * 40)
    t0 = time.time()

    stall_by_group_key: dict[str, StallAssessment] = {}
    subs_by_group_key: dict[str, Subdivision] = {}
    materialized_subs: list[Subdivision] = []
    stall_count = 0

    for cluster in sub_clusters:
        # Compute vacancy from cluster parcels
        total_lots = cluster.parcel_count
        vacant_lots = sum(
            1 for p in cluster.parcels
            if p.vacancy_status == VacancyStatus.VACANT
        )
        vacancy_ratio = vacant_lots / total_lots if total_lots > 0 else 0.0

        # Materialize a Subdivision object
        sub_id = uuid4()
        sub = Subdivision(
            subdivision_id=sub_id,
            name=cluster.group_key,
            municipality_id=WASHTENAW_MUNICIPALITY_ID,
            county="Washtenaw",
            state="MI",
            total_lots=total_lots,
            vacant_lots=vacant_lots,
            vacancy_ratio=vacancy_ratio,
            # Platted subdivision = infrastructure invested (Michigan law)
            infrastructure_status=InfrastructureStatus.ROADS_INSTALLED,
            parcel_ids=[p.parcel_id for p in cluster.parcels],
            active_listing_count=len(cluster.matched_listings),
        )
        materialized_subs.append(sub)
        subs_by_group_key[cluster.group_key] = sub

        # Create a domain-justified ROADS_INSTALLED municipal event.
        # Rationale: Michigan Plat Act (MCL 560) requires road and utility
        # infrastructure as a condition of plat recording. If a subdivision
        # appears in legal descriptions, it was recorded, therefore
        # infrastructure was invested (built or bonded).
        synthetic_event = MunicipalEvent(
            municipality_id=WASHTENAW_MUNICIPALITY_ID,
            event_type=MunicipalEventType.ROADS_INSTALLED,
            occurred_at=datetime(2010, 1, 1, tzinfo=timezone.utc),
            source_system="plat_inference",
            subdivision_id=sub_id,
        )

        # Run stallout detection with real parcel data + inferred infrastructure
        assessment = detect_stall(
            subdivision=sub,
            municipal_events=[synthetic_event],
            parcels=cluster.parcels,
        )

        stall_by_group_key[cluster.group_key] = assessment

        if assessment.is_stalled:
            stall_count += 1

    # Persist materialized subdivisions to SQLite
    if materialized_subs:
        db.save_subdivisions_batch(materialized_subs)

    elapsed = time.time() - t0
    stage_stats["stallout"] = {
        "subdivisions_materialized": len(materialized_subs),
        "stalled": stall_count,
        "seconds": round(elapsed, 1),
    }
    print(f"  Stage 3.5: {len(materialized_subs)} subdivisions materialized, "
          f"{stall_count} stalled ({elapsed:.1f}s)")

    # ── Stage 4: Listing Clusters ─────────────────────────────────────────
    print(f"\n  STAGE 4: Listing Agent/Office Clusters")
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
    print(f"  Stage 4: {len(listing_cluster_store)} listing clusters ({elapsed:.1f}s)")

    # ── Stage 4.5: Listing History Evidence ─────────────────────────────
    print(f"\n  STAGE 4.5: Listing History Evidence Analysis")
    print("  " + "-" * 40)
    t0 = time.time()

    history_evidence: dict[str, ListingHistoryEvidence] = {}
    all_listings_for_history = listing_store.all_listings()

    # Build a lookup from listing subdivision_name → listings
    listings_by_sub: dict[str, list] = {}
    listings_by_parcel: dict[str, list] = {}
    for l in all_listings_for_history:
        if l.subdivision_name_raw:
            sub_key = l.subdivision_name_raw.lower().strip()
            listings_by_sub.setdefault(sub_key, []).append(l)
        if l.parcel_number_raw:
            listings_by_parcel.setdefault(l.parcel_number_raw, []).append(l)

    # For each parcel cluster, find matching historical listings
    from src.models.enums import StandardStatus
    hist_enriched = 0
    for cluster in parcel_clusters:
        # Collect active and historical listings for this cluster
        active = [l for l in cluster.matched_listings if l.standard_status == StandardStatus.ACTIVE]
        historical = [l for l in cluster.matched_listings if l.standard_status != StandardStatus.ACTIVE]

        # Also look up historical listings by subdivision name or parcel number
        if cluster.cluster_type == "subdivision":
            sub_listings = listings_by_sub.get(cluster.group_key, [])
            # Add any listings not already in matched_listings
            matched_keys = {l.listing_key for l in cluster.matched_listings}
            for l in sub_listings:
                if l.listing_key not in matched_keys:
                    if l.standard_status == StandardStatus.ACTIVE:
                        active.append(l)
                    else:
                        historical.append(l)
                    matched_keys.add(l.listing_key)

        ev = analyze_cluster_listing_history(
            active_listings=active,
            historical_listings=historical,
            total_cluster_lots=cluster.parcel_count,
        )
        history_evidence[cluster.group_key] = ev
        if ev.history_signal_score > 0:
            hist_enriched += 1

    elapsed = time.time() - t0
    stage_stats["history_evidence"] = {
        "clusters_analyzed": len(history_evidence),
        "enriched": hist_enriched,
        "seconds": round(elapsed, 1),
    }
    print(f"  Stage 4.5: {len(history_evidence)} clusters analyzed, {hist_enriched} with history signals ({elapsed:.1f}s)")

    # ── Stage 4.6: Legal Description Multi-Lot Grouping ──────────────────
    print(f"\n  STAGE 4.6: Legal Description Multi-Lot Detection")
    print("  " + "-" * 40)
    from src.adapters.spark.bbo_signals import detect_same_subdivision_listings
    legal_groups = detect_same_subdivision_listings(all_listings_for_history)
    legal_group_count = len(legal_groups)
    total_multi_listings = sum(len(v) for v in legal_groups.values())

    if legal_groups:
        print(f"  Found {legal_group_count} subdivisions with 2+ listings from legal descriptions:")
        for sub_name, entries in sorted(legal_groups.items(), key=lambda x: -len(x[1]))[:10]:
            lots = sorted(set(e['lot_number'] for e in entries))
            statuses = [e['listing']['standard_status'] if isinstance(e['listing'], dict) else e['listing'].standard_status.value for e in entries]
            unit_flag = " [SITE CONDO]" if entries[0]['is_unit'] else ""
            print(f"    {sub_name}: {len(entries)} listings, lots {lots}{unit_flag}")
    else:
        print("  No multi-listing subdivisions detected from legal descriptions")

    stage_stats["legal_groups"] = {
        "subdivision_groups": legal_group_count,
        "total_multi_listings": total_multi_listings,
    }

    # ── Stage 5: Strategic Opportunity Ranking ────────────────────────────
    print(f"\n  STAGE 5: Strategic Opportunity Ranking")
    print("  " + "-" * 40)
    t0 = time.time()

    strategic_opps = rank_from_pipeline(
        parcel_clusters=parcel_clusters,
        stall_assessments={},  # No parcel.subdivision_id-based matching yet
        subdivisions={},
        stall_by_group_key=stall_by_group_key,
        subdivisions_by_group_key=subs_by_group_key,
        min_lots=1,  # Rank everything, filter via API
        listing_history_evidence=history_evidence,
    )

    # Convert to dicts for SQLite
    strategic_dicts = []
    for opp in strategic_opps:
        d = asdict(opp)
        strategic_dicts.append(d)

    db.save_strategic_opportunities_batch(strategic_dicts)

    # Stats for the 5+ lot target
    five_plus = [o for o in strategic_opps if o.lot_count >= 5]
    five_plus_infra = [o for o in five_plus if o.infrastructure_invested]

    elapsed = time.time() - t0
    stage_stats["strategic"] = {
        "total_ranked": len(strategic_opps),
        "five_plus_lots": len(five_plus),
        "five_plus_with_infrastructure": len(five_plus_infra),
        "seconds": round(elapsed, 1),
    }
    print(f"  Stage 5: {len(strategic_opps)} opportunities ranked")
    print(f"  → {len(five_plus)} with 5+ lots")
    print(f"  → {len(five_plus_infra)} with 5+ lots AND infrastructure")
    print(f"  ({elapsed:.1f}s)")

    # ── Save pipeline signals ─────────────────────────────────────────────
    print(f"\n  Saving {len(all_results)} pipeline signals to DB...")
    signal_records = [_routing_result_to_signal(r) for r in all_results]
    db.save_signals_batch(signal_records)

    # ── Save aggregate stats ──────────────────────────────────────────────
    db.save_stats(stage_stats)
    db.commit()

    # ── Final Report ──────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  PIPELINE COMPLETE — Results persisted to SQLite")
    print("=" * 70)
    print(f"\n  Database: {db.db_path}")
    print(f"  Listings:     {stage_stats.get('spark', {}).get('listings', 0)}")
    print(f"  Parcels:      {stage_stats['regrid']['parcels']} ({stage_stats['regrid']['vacant']} vacant)")
    print(f"  Clusters:     {stage_stats['parcel_clusters']['total']}")
    print(f"  With listings:{stage_stats['parcel_clusters']['with_listings']}")
    print(f"  Strategic 5+: {stage_stats['strategic']['five_plus_lots']}")
    print(f"  Total events: {len(all_results)}")

    # Top strategic opportunities
    if five_plus:
        print()
        print("  TOP 5+ LOT OPPORTUNITIES:")
        print("  " + "-" * 50)
        for opp in five_plus[:15]:
            infra_flag = " [INFRA]" if opp.infrastructure_invested else ""
            listing_flag = f" ({opp.listing_count} listings)" if opp.has_active_listings else ""
            print(f"    {opp.name}: {opp.lot_count} lots, "
                  f"{opp.total_acreage:.1f}ac, "
                  f"score={opp.composite_score:.3f}{infra_flag}{listing_flag}")

    print()
    print("  Start the API server:")
    print("    cd landos && python3 -m uvicorn api.main:app --reload --port 8000")
    print()
    print("  Key queries:")
    print("    GET http://localhost:8000/api/strategic?min_lots=5")
    print("    GET http://localhost:8000/api/strategic?min_lots=5&infrastructure=true")
    print("    GET http://localhost:8000/api/clusters?has_listings=true")
    print("    GET http://localhost:8000/api/stats")
    print()

    db.close()


if __name__ == "__main__":
    main()
