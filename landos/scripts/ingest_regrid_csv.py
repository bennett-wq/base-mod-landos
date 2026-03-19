#!/usr/bin/env python3
"""Ingest Regrid Washtenaw County CSV into the LandOS event mesh.

Loads the bulk CSV export, runs each record through RegridIngestionAdapter
(normalize → link → score → emit → route), and prints a signal report.

Can be used standalone or called from run_full_pipeline.py with pre-loaded
listings for parcel-to-listing linkage.

Usage:
    python3 landos/scripts/ingest_regrid_csv.py
    python3 landos/scripts/ingest_regrid_csv.py --csv landos/data/regrid/Washtenaw\ County/mi_washtenaw.csv
    python3 landos/scripts/ingest_regrid_csv.py --limit 1000
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

# Ensure project root is on sys.path so `from src...` imports work.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.adapters.regrid.ingestion import (
    RegridIngestionAdapter,
    InMemoryParcelStore,
    InMemoryOwnerStore,
)
from src.models.listing import Listing
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES

# Default CSV path
DEFAULT_CSV = _PROJECT_ROOT / "data" / "regrid" / "Washtenaw County" / "mi_washtenaw.csv"

# Washtenaw County sentinel municipality UUID (Phase 1 default)
WASHTENAW_MUNICIPALITY_ID = UUID("00000000-0000-0000-0000-000000000001")


def load_csv_records(
    csv_path: Path,
    limit: int | None = None,
    vacant_only: bool = False,
) -> list[dict]:
    """Load raw records from a Regrid CSV export.

    Args:
        csv_path:    Path to the CSV file.
        limit:       Max records to load (None = all).
        vacant_only: If True, only load records where usedesc contains "VACANT".
    """
    print(f"  Loading CSV: {csv_path}")
    if vacant_only:
        print("  Filter: VACANT parcels only (usedesc contains 'VACANT')")
    if not csv_path.exists():
        print(f"  ERROR: CSV not found at {csv_path}", file=sys.stderr)
        sys.exit(1)

    records: list[dict] = []
    skipped = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if vacant_only:
                usedesc = (row.get("usedesc") or "").strip().upper()
                if "VACANT" not in usedesc:
                    skipped += 1
                    continue
            records.append(row)
            if limit is not None and len(records) >= limit:
                break

    if vacant_only:
        print(f"  Loaded {len(records)} vacant records (skipped {skipped} improved).\n")
    else:
        print(f"  Loaded {len(records)} records from CSV.\n")
    return records


def run_regrid_ingestion(
    raw_records: list[dict],
    listings: list[Listing] | None = None,
    engine: TriggerEngine | None = None,
    context: TriggerContext | None = None,
) -> tuple[RegridIngestionAdapter, list]:
    """Run Regrid ingestion and return (adapter, results).

    Args:
        raw_records: Raw CSV dicts.
        listings:    Optional pre-loaded listings for parcel-to-listing linkage.
        engine:      Optional pre-built TriggerEngine (shared with Spark pipeline).
        context:     Optional TriggerContext.
    """
    if engine is None:
        engine = TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())
    if context is None:
        context = TriggerContext()

    parcel_store = InMemoryParcelStore()
    owner_store = InMemoryOwnerStore()

    adapter = RegridIngestionAdapter(
        engine=engine,
        listings=listings or [],
        context=context,
        parcel_store=parcel_store,
        owner_store=owner_store,
        default_municipality_id=WASHTENAW_MUNICIPALITY_ID,
    )

    print("  Processing through RegridIngestionAdapter...")
    # Process in batches to show progress
    batch_size = 5000
    all_results = []
    total = len(raw_records)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = raw_records[start:end]
        results = adapter.process_batch(batch)
        all_results.extend(results)
        print(f"    Processed {end}/{total} records ({len(all_results)} events so far)")

    print()
    return adapter, all_results


def print_report(
    adapter: RegridIngestionAdapter,
    results: list,
    listings: list[Listing] | None = None,
) -> None:
    """Print a summary of Regrid ingestion results."""
    parcel_count = len(adapter.parcel_store)
    owner_count = len(adapter.owner_store)
    total_events = len(results)
    total_fired = sum(len(r.fired_rules) for r in results)

    print("=" * 70)
    print("  REGRID CSV INGESTION REPORT")
    print("=" * 70)
    print(f"  Parcels ingested:      {parcel_count}")
    print(f"  Unique owners:         {owner_count}")
    if listings:
        print(f"  Listings available:    {len(listings)} (for linkage)")
    print(f"  Events emitted:        {total_events}")
    print(f"  Rules fired:           {total_fired}")
    print()

    # Count events by type
    event_counts: dict[str, int] = {}
    for r in results:
        event_counts[r.event_type] = event_counts.get(r.event_type, 0) + 1
    print("  Events by type:")
    for etype, count in sorted(event_counts.items()):
        print(f"    {etype}: {count}")
    print()

    # Count rules fired
    rule_counts: dict[str, int] = {}
    for r in results:
        for rid in r.fired_rules:
            rule_counts[rid] = rule_counts.get(rid, 0) + 1
    if rule_counts:
        print("  Rules fired:")
        for rid, count in sorted(rule_counts.items(), key=lambda x: -x[1]):
            print(f"    {rid}: {count}")
    print()

    # Linkage stats
    linked_count = event_counts.get("parcel_linked_to_listing", 0)
    owner_resolved_count = event_counts.get("parcel_owner_resolved", 0)
    score_updated_count = event_counts.get("parcel_score_updated", 0)
    print(f"  Parcels linked to listings:  {linked_count}")
    print(f"  Owners resolved:             {owner_resolved_count}")
    print(f"  Scores emitted:              {score_updated_count}")
    print()
    print("=" * 70)


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Regrid CSV into LandOS")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to Regrid CSV")
    parser.add_argument("--limit", type=int, default=None, help="Limit records to process")
    args = parser.parse_args()

    csv_path = Path(args.csv)

    print()
    print("=" * 70)
    print("  LandOS — Regrid CSV Ingestion")
    print("=" * 70)

    raw_records = load_csv_records(csv_path, limit=args.limit)
    if not raw_records:
        print("  No records loaded.")
        return

    adapter, results = run_regrid_ingestion(raw_records)
    print_report(adapter, results)


if __name__ == "__main__":
    main()
