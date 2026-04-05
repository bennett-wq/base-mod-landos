#!/usr/bin/env python3
"""Generate a detailed signal breakdown from the full pipeline run.

Categorizes every positive signal into actionable tiers:
  Tier 1: Multi-signal convergence (owner cluster + active listing + fatigue indicators)
  Tier 2: Owner clusters with active listings (but fewer converging signals)
  Tier 3: Active listings with BBO signals but no parcel cluster match
  Tier 4: Large owner clusters without current listings (dormant supply)
  Tier 5: Subdivision/proximity clusters (market geography signals)

Usage:
    python3 landos/scripts/signal_report.py
    python3 landos/scripts/signal_report.py --top 100
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.adapters.cluster.parcel_cluster_detector import ParcelClusterDetector, ParcelClusterResult
from src.adapters.cluster.store import InMemoryClusterStore
from src.adapters.regrid.ingestion import (
    RegridIngestionAdapter, InMemoryParcelStore, InMemoryOwnerStore,
)
from src.adapters.spark.ingestion import SparkIngestionAdapter, InMemoryListingStore
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES

from scripts.ingest_regrid_csv import DEFAULT_CSV, WASHTENAW_MUNICIPALITY_ID, load_csv_records
from scripts.ingest_spark_live import fetch_listings


def classify_signal_strength(cluster: ParcelClusterResult, all_bbo_events: dict) -> dict:
    """Score the signal strength of a cluster with listings."""
    signals = []
    score = 0

    # Multi-parcel owner
    if cluster.parcel_count >= 5:
        signals.append(f"LARGE_OWNER ({cluster.parcel_count} parcels)")
        score += 3
    elif cluster.parcel_count >= 2:
        signals.append(f"MULTI_PARCEL ({cluster.parcel_count} parcels)")
        score += 1

    # Total acreage
    if cluster.total_acreage >= 20:
        signals.append(f"SIGNIFICANT_ACREAGE ({cluster.total_acreage:.1f}ac)")
        score += 2
    elif cluster.total_acreage >= 5:
        signals.append(f"MODERATE_ACREAGE ({cluster.total_acreage:.1f}ac)")
        score += 1

    for listing in cluster.matched_listings:
        lk = listing.listing_key

        # High CDOM = fatigue
        if listing.cdom and listing.cdom >= 180:
            signals.append(f"HIGH_FATIGUE (CDOM={listing.cdom})")
            score += 3
        elif listing.cdom and listing.cdom >= 90:
            signals.append(f"MODERATE_FATIGUE (CDOM={listing.cdom})")
            score += 2

        # Private remarks intelligence
        if listing.private_remarks:
            pr = listing.private_remarks.upper()
            if any(w in pr for w in ["PACKAGE", "TOGETHER", "BUNDLE", "ALL PARCELS"]):
                signals.append("PACKAGE_LANGUAGE")
                score += 3
            if any(w in pr for w in ["MOTIVATED", "MUST SELL", "BRING ALL OFFERS", "MAKE AN OFFER"]):
                signals.append("MOTIVATION_LANGUAGE")
                score += 3
            if any(w in pr for w in ["RECENTLY SPLIT", "NEWLY SPLIT", "JUST SPLIT"]):
                signals.append("RECENT_SPLIT")
                score += 2
            if any(w in pr for w in ["PLANS", "DRAWINGS", "APPROVED", "PERMIT"]):
                signals.append("PRE_DEVELOPMENT")
                score += 2
            if any(w in pr for w in ["PREFERRED BUILDER", "BUILDER INFO"]):
                signals.append("BUILDER_PROGRAM")
                score += 2

        # Multiple listings from same owner
        if len(cluster.matched_listings) >= 2:
            if "MULTI_LISTING" not in [s.split(" ")[0] for s in signals]:
                signals.append(f"MULTI_LISTING ({len(cluster.matched_listings)} active)")
                score += 2

        # BBO signals from engine
        bbo_events = all_bbo_events.get(lk, [])
        for evt_type in bbo_events:
            if evt_type == "listing_bbo_cdom_threshold_crossed" and "FATIGUE" not in str(signals):
                signals.append("BBO_CDOM_THRESHOLD")
                score += 1
            if evt_type == "listing_private_remarks_signal_detected":
                signals.append("BBO_REMARKS_SIGNAL")
                score += 1
            if evt_type == "subdivision_remnant_detected":
                signals.append("SUBDIVISION_REMNANT")
                score += 2

    return {"signals": signals, "score": score}


def main() -> None:
    parser = argparse.ArgumentParser(description="Detailed signal breakdown")
    parser.add_argument("--top", type=int, default=95, help="Spark listings to fetch")
    args = parser.parse_args()

    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key:
        print("ERROR: SPARK_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    engine = TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())
    context = TriggerContext()

    # Stage 1: Spark
    print("\n  Loading Spark listings...")
    listing_store = InMemoryListingStore()
    raw_spark = fetch_listings(api_key, top=args.top, county="Washtenaw")
    spark_adapter = SparkIngestionAdapter(engine=engine, context=context, store=listing_store)
    spark_results = spark_adapter.process_batch(raw_spark)

    # Build BBO event index: listing_key → [event_types]
    bbo_index: dict[str, list[str]] = {}
    for r in spark_results:
        if r.event_type.startswith("listing_bbo") or r.event_type in (
            "listing_private_remarks_signal_detected",
            "subdivision_remnant_detected",
            "agent_land_accumulation_detected",
            "office_land_program_detected",
            "developer_exit_signal_detected",
        ):
            # Extract listing_key from the event — use source record from payload
            bbo_index.setdefault("_global", []).append(r.event_type)

    # Also index by listing key from the engine results
    all_listings = listing_store.all_listings()
    listing_by_key = {l.listing_key: l for l in all_listings}

    # Stage 2: Regrid (vacant only)
    print("  Loading vacant parcels...")
    csv_path = DEFAULT_CSV
    raw_regrid = load_csv_records(csv_path, vacant_only=True)
    parcel_store = InMemoryParcelStore()
    owner_store = InMemoryOwnerStore()
    regrid_adapter = RegridIngestionAdapter(
        engine=engine, listings=all_listings, context=context,
        parcel_store=parcel_store, owner_store=owner_store,
        default_municipality_id=WASHTENAW_MUNICIPALITY_ID,
    )
    batch_size = 5000
    total = len(raw_regrid)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        regrid_adapter.process_batch(raw_regrid[start:end])

    all_parcels = list(parcel_store._parcels.values())

    # Stage 3: Parcel clusters
    print("  Detecting parcel clusters...")
    cluster_store = InMemoryClusterStore()
    detector = ParcelClusterDetector(engine=engine, context=context, cluster_store=cluster_store)
    _, parcel_clusters = detector.scan(all_parcels, all_listings)

    # ── Classify signals ──────────────────────────────────────────────────
    clusters_with_listings = [c for c in parcel_clusters if c.matched_listings]
    clusters_without = [c for c in parcel_clusters if not c.matched_listings]

    scored = []
    for c in clusters_with_listings:
        info = classify_signal_strength(c, bbo_index)
        scored.append((c, info))
    scored.sort(key=lambda x: -x[1]["score"])

    # ── BBO signals on listings without parcel cluster match ──────────────
    clustered_listing_ids = set()
    for c in clusters_with_listings:
        for l in c.matched_listings:
            clustered_listing_ids.add(l.listing_id)

    unclustered_listings_with_signals = []
    for l in all_listings:
        if l.listing_id in clustered_listing_ids:
            continue
        signals = []
        score = 0
        if l.cdom and l.cdom >= 180:
            signals.append(f"HIGH_FATIGUE (CDOM={l.cdom})")
            score += 3
        elif l.cdom and l.cdom >= 90:
            signals.append(f"MODERATE_FATIGUE (CDOM={l.cdom})")
            score += 2
        if l.private_remarks:
            pr = l.private_remarks.upper()
            if any(w in pr for w in ["PACKAGE", "TOGETHER", "BUNDLE"]):
                signals.append("PACKAGE_LANGUAGE")
                score += 3
            if any(w in pr for w in ["MOTIVATED", "MUST SELL", "BRING ALL OFFERS"]):
                signals.append("MOTIVATION_LANGUAGE")
                score += 3
            if any(w in pr for w in ["RECENTLY SPLIT", "NEWLY SPLIT"]):
                signals.append("RECENT_SPLIT")
                score += 2
            if any(w in pr for w in ["PREFERRED BUILDER", "BUILDER INFO"]):
                signals.append("BUILDER_PROGRAM")
                score += 2
        if l.lot_size_acres and l.lot_size_acres >= 5:
            signals.append(f"LARGE_LOT ({l.lot_size_acres:.1f}ac)")
            score += 1
        if signals:
            unclustered_listings_with_signals.append((l, signals, score))
    unclustered_listings_with_signals.sort(key=lambda x: -x[2])

    # ── Print report ──────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print("  LANDOS SIGNAL INTELLIGENCE REPORT — WASHTENAW COUNTY")
    print("=" * 80)
    print(f"\n  Data: {len(all_listings)} active listings, "
          f"{len(all_parcels)} vacant parcels, "
          f"{len(parcel_clusters)} clusters")
    print(f"  Clusters with active listings: {len(clusters_with_listings)}")

    # ── TIER 1: Multi-signal convergence ──────────────────────────────────
    tier1 = [(c, i) for c, i in scored if i["score"] >= 6]
    print(f"\n{'='*80}")
    print(f"  TIER 1 — HIGHEST SIGNAL CONVERGENCE ({len(tier1)} opportunities)")
    print("  Multiple signals reinforcing: fatigue + multi-parcel + remarks intelligence")
    print(f"{'='*80}")
    for c, info in tier1:
        print(f"\n  [{c.cluster_type.upper()}] {c.group_key}")
        print(f"  Score: {info['score']} | {c.parcel_count} parcels | {c.total_acreage:.1f} acres")
        print(f"  Signals: {', '.join(info['signals'])}")
        for l in c.matched_listings:
            cdom = f"CDOM={l.cdom}" if l.cdom else ""
            print(f"    ${l.list_price:,.0f} | {l.address_raw or '?'} | {cdom}")
            print(f"    Agent: {l.listing_agent_name or '?'} | Office: {l.listing_office_name or '?'}")
            if l.private_remarks:
                print(f"    Pvt: {l.private_remarks[:150]}...")
            if l.subdivision_name_raw:
                print(f"    Subdivision: {l.subdivision_name_raw}")

    # ── TIER 2: Owner clusters with listings ──────────────────────────────
    tier2 = [(c, i) for c, i in scored if 3 <= i["score"] < 6]
    print(f"\n{'='*80}")
    print(f"  TIER 2 — MODERATE SIGNAL ({len(tier2)} opportunities)")
    print("  Owner cluster + listing, some fatigue or remarks indicators")
    print(f"{'='*80}")
    for c, info in tier2:
        print(f"\n  [{c.cluster_type.upper()}] {c.group_key}")
        print(f"  Score: {info['score']} | {c.parcel_count} parcels | {c.total_acreage:.1f} acres")
        print(f"  Signals: {', '.join(info['signals'])}")
        for l in c.matched_listings:
            cdom = f"CDOM={l.cdom}" if l.cdom else ""
            print(f"    ${l.list_price:,.0f} | {l.address_raw or '?'} | {cdom}")
            if l.private_remarks:
                print(f"    Pvt: {l.private_remarks[:120]}...")

    # ── TIER 3: Listings with BBO signals but no cluster match ────────────
    print(f"\n{'='*80}")
    print(f"  TIER 3 — UNCLUSTERED LISTINGS WITH SIGNALS ({len(unclustered_listings_with_signals)})")
    print("  Active listing with fatigue/remarks signals, not linked to a parcel cluster")
    print(f"{'='*80}")
    for l, signals, score in unclustered_listings_with_signals[:20]:
        cdom = f"CDOM={l.cdom}" if l.cdom else ""
        print(f"\n  ${l.list_price:,.0f} | {l.address_raw or '?'} | {cdom}")
        print(f"  Signals: {', '.join(signals)}")
        print(f"  Agent: {l.listing_agent_name or '?'} | Office: {l.listing_office_name or '?'}")
        if l.private_remarks:
            print(f"  Pvt: {l.private_remarks[:120]}...")

    # ── TIER 4: Dormant supply — large clusters without listings ──────────
    dormant = [c for c in clusters_without if c.cluster_type == "owner" and c.parcel_count >= 10]
    dormant.sort(key=lambda x: -x.parcel_count)
    print(f"\n{'='*80}")
    print(f"  TIER 4 — DORMANT SUPPLY ({len(dormant)} large owner clusters, no active listing)")
    print("  Owners holding significant vacant inventory not currently on market")
    print(f"{'='*80}")
    for c in dormant[:25]:
        print(f"  {c.group_key}: {c.parcel_count} parcels, {c.total_acreage:.1f} acres")

    # ── TIER 5: Subdivision hot zones ─────────────────────────────────────
    sub_clusters = [c for c in parcel_clusters if c.cluster_type == "subdivision"]
    sub_clusters.sort(key=lambda x: -x.parcel_count)
    print(f"\n{'='*80}")
    print(f"  TIER 5 — SUBDIVISION HOT ZONES ({len(sub_clusters)} subdivisions with vacant lots)")
    print(f"{'='*80}")
    for c in sub_clusters[:20]:
        owners = len({p.owner_name_raw for p in c.parcels if p.owner_name_raw})
        listing_flag = f" ** {len(c.matched_listings)} LISTING(S)" if c.matched_listings else ""
        print(f"  {c.group_key}: {c.parcel_count} lots, {owners} owners, "
              f"{c.total_acreage:.1f} acres{listing_flag}")

    # ── Summary stats ─────────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  SUMMARY")
    print(f"{'='*80}")
    print(f"  Tier 1 (highest convergence):     {len(tier1)}")
    print(f"  Tier 2 (moderate signal):          {len(tier2)}")
    print(f"  Tier 3 (unclustered w/ signals):   {len(unclustered_listings_with_signals)}")
    print(f"  Tier 4 (dormant supply 10+ lots):  {len(dormant)}")
    print(f"  Tier 5 (subdivision hot zones):    {len(sub_clusters)}")
    total_tier1_acres = sum(c.total_acreage for c, _ in tier1)
    total_dormant_acres = sum(c.total_acreage for c in dormant)
    print(f"\n  Tier 1 total acreage:  {total_tier1_acres:.1f}")
    print(f"  Dormant total acreage: {total_dormant_acres:.1f}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
