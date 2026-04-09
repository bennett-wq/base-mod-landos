#!/usr/bin/env python3
"""Ingest live Spark MLS land listings into the LandOS event mesh.

Pulls active land listings from the Spark RESO Web API, runs each through
SparkIngestionAdapter (normalize → diff → BBO signals → trigger routing),
and prints a signal report.

Usage:
    python3 landos/scripts/ingest_spark_live.py
    python3 landos/scripts/ingest_spark_live.py --top 50
    python3 landos/scripts/ingest_spark_live.py --county Washtenaw
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path so `from src...` imports work.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

# Load .env from the repo root (one level above landos/)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.adapters.spark.ingestion import SparkIngestionAdapter, InMemoryListingStore
from src.adapters.spark.field_map import RESO_TO_LISTING, BBO_TO_LISTING
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES


# ── Spark API helpers ─────────────────────────────────────────────────────

SPARK_BASE_URL = os.environ.get("SPARK_BASE_URL", "https://replication.sparkapi.com/Reso/OData")


HISTORICAL_STATUSES = ["Active", "Pending", "Closed", "Withdrawn", "Expired", "Canceled"]

_CURRENT_STATUS_PRIORITY = {
    "Active": 50,
    "Pending": 40,
    "ActiveUnderContract": 40,
    "Closed": 30,
    "Withdrawn": 20,
    "Canceled": 20,
    "Expired": 20,
}


def fetch_listings(api_key: str, top: int, county: str | None, status: str = "Active") -> list[dict]:
    """Fetch land listings from the Spark RESO Web API for a given status."""
    filters = [
        "PropertyType eq 'Land'",
        f"StandardStatus eq '{status}'",
    ]
    if county:
        filters.append(f"CountyOrParish eq '{county}'")

    params = urllib.parse.urlencode({
        "$filter": " and ".join(filters),
        "$top": top,
        "$orderby": "ModificationTimestamp desc",
    })
    url = f"{SPARK_BASE_URL}/Property?{params}"

    print(f"  Fetching up to {top} {status} listings from Spark API...")
    print(f"  URL: {url}")

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\n  HTTP {e.code} error from Spark API:", file=sys.stderr)
        print(f"  {body[:500]}", file=sys.stderr)
        sys.exit(1)

    records = data.get("value", data.get("D", {}).get("Results", []))
    print(f"  Received {len(records)} {status} records from API.\n")
    return records


def _parse_dt(raw: object) -> datetime | None:
    if raw is None or raw == "":
        return None
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _record_sort_key(record: dict) -> tuple[int, datetime]:
    status = str(record.get("StandardStatus") or "").strip()
    status_priority = _CURRENT_STATUS_PRIORITY.get(status, 0)
    ts = (
        _parse_dt(record.get("StatusChangeTimestamp"))
        or _parse_dt(record.get("MajorChangeTimestamp"))
        or _parse_dt(record.get("ModificationTimestamp"))
        or _parse_dt(record.get("OriginalEntryTimestamp"))
        or _parse_dt(record.get("PendingTimestamp"))
    )
    if ts is None:
        listing_contract_date = record.get("ListingContractDate")
        if listing_contract_date:
            dt = _parse_dt(f"{listing_contract_date}T00:00:00+00:00")
            if dt is not None:
                ts = dt
    if ts is None:
        ts = datetime.min
    return (status_priority, ts)


def select_current_records(records: list[dict]) -> list[dict]:
    """Pick one current-state record per ListingKey for live surfaces."""
    by_key: dict[str, dict] = {}
    for rec in records:
        key = rec.get("ListingKey")
        if not key:
            continue
        current = by_key.get(key)
        if current is None or _record_sort_key(rec) > _record_sort_key(current):
            by_key[key] = rec
    return list(by_key.values())


def fetch_all_statuses(api_key: str, top_per_status: int = 200, county: str | None = None, statuses: list[str] | None = None) -> list[dict]:
    """Fetch listings across multiple statuses and return the current-state surface."""
    if statuses is None:
        statuses = HISTORICAL_STATUSES

    all_records: list[dict] = []

    for status in statuses:
        records = fetch_listings(api_key, top=top_per_status, county=county, status=status)
        all_records.extend(records)

    current_records = select_current_records(all_records)
    print(
        f"  Total records across {len(statuses)} statuses: {len(all_records)} "
        f"({len(current_records)} current-state listing keys)\n"
    )
    return current_records


def fetch_status_surfaces(
    api_key: str,
    top_per_status: int = 200,
    county: str | None = None,
    statuses: list[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Fetch both current-state and full historical Spark surfaces."""
    if statuses is None:
        statuses = HISTORICAL_STATUSES

    all_records: list[dict] = []
    for status in statuses:
        records = fetch_listings(api_key, top=top_per_status, county=county, status=status)
        all_records.extend(records)

    current_records = select_current_records(all_records)
    print(
        f"  Total records across {len(statuses)} statuses: {len(all_records)} "
        f"({len(current_records)} current-state listing keys)\n"
    )
    return current_records, all_records


# ── Field Discovery ──────────────────────────────────────────────────────

# Fields to probe that we suspect exist but aren't in our current field_map
PROBE_FIELDS = [
    "PrivateOfficeRemarks",
    "DaysOffMarket",
    "CustomFields",
    "OffMarketDays",
    "CumulativeDaysOffMarket",
    "ListingAgreement",
    "SellerType",
    "OwnerName",
    "Tax_sp_Info_co_Owner_sp_Name2",
]


def discover_fields(api_key: str, county: str | None = None) -> None:
    """Fetch sample records and report all fields not in our field_map.

    Compares every key returned by the API against RESO_TO_LISTING and
    BBO_TO_LISTING to find fields we're leaving on the table.
    """
    print()
    print("=" * 70)
    print("  LandOS — Spark Field Discovery")
    print("=" * 70)

    # Known mapped fields (API-side names)
    mapped_fields = set(RESO_TO_LISTING.keys()) | set(BBO_TO_LISTING.keys())

    # Fetch a small sample across Active + Closed to see the full field surface
    all_fields: dict[str, list] = {}  # field_name → list of sample values
    field_population: dict[str, int] = {}  # field_name → count of non-null values
    total_records = 0

    for status in ["Active", "Closed", "Expired"]:
        records = fetch_listings(api_key, top=5, county=county, status=status)
        for rec in records:
            total_records += 1
            for key, val in rec.items():
                if key not in all_fields:
                    all_fields[key] = []
                    field_population[key] = 0
                if val is not None and val != "" and val != []:
                    field_population[key] = field_population.get(key, 0) + 1
                    if len(all_fields[key]) < 3:
                        all_fields[key].append(val)

    all_field_names = set(all_fields.keys())
    unmapped = all_field_names - mapped_fields
    mapped_present = all_field_names & mapped_fields
    mapped_missing = mapped_fields - all_field_names

    print(f"\n  Total records sampled: {total_records}")
    print(f"  Total fields returned by API: {len(all_field_names)}")
    print(f"  Already mapped in field_map.py: {len(mapped_present)}")
    print(f"  UNMAPPED (new/unknown): {len(unmapped)}")
    print(f"  Mapped but not returned: {len(mapped_missing)}")

    # Report unmapped fields with sample values and population
    if unmapped:
        print()
        print("=" * 70)
        print("  UNMAPPED FIELDS (not in RESO_TO_LISTING or BBO_TO_LISTING)")
        print("=" * 70)
        for field in sorted(unmapped):
            pop = field_population.get(field, 0)
            pct = (pop / total_records * 100) if total_records else 0
            samples = all_fields.get(field, [])
            sample_str = repr(samples[0])[:80] if samples else "(empty)"
            print(f"  {field}")
            print(f"    Population: {pop}/{total_records} ({pct:.0f}%)")
            print(f"    Sample: {sample_str}")
            print()

    # Report probe fields specifically
    print("=" * 70)
    print("  PROBE FIELD RESULTS (targeted fields)")
    print("=" * 70)
    for field in PROBE_FIELDS:
        if field in all_field_names:
            pop = field_population.get(field, 0)
            pct = (pop / total_records * 100) if total_records else 0
            samples = all_fields.get(field, [])
            sample_str = repr(samples[0])[:100] if samples else "(empty)"
            status = "★ FOUND" if field not in mapped_fields else "✓ ALREADY MAPPED"
            print(f"  {status}: {field}")
            print(f"    Population: {pop}/{total_records} ({pct:.0f}%)")
            print(f"    Sample: {sample_str}")
        else:
            print(f"  ✗ NOT RETURNED: {field}")
        print()

    # Report mapped fields that the API doesn't return
    if mapped_missing:
        print("=" * 70)
        print("  MAPPED BUT NOT RETURNED (dead fields in our field_map)")
        print("=" * 70)
        for field in sorted(mapped_missing):
            print(f"  {field}")
        print()

    # Save discovery results
    output_dir = Path(__file__).resolve().parent.parent / "data" / "discovery"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "field_discovery.json"
    output = {
        "discovered_at": datetime.utcnow().isoformat(),
        "total_records_sampled": total_records,
        "total_fields": len(all_field_names),
        "unmapped_fields": sorted(unmapped),
        "mapped_present": sorted(mapped_present),
        "mapped_missing": sorted(mapped_missing),
        "field_population": {
            k: {"count": v, "pct": round(v / total_records * 100, 1) if total_records else 0}
            for k, v in sorted(field_population.items())
        },
        "sample_values": {
            k: [repr(s)[:200] for s in v]
            for k, v in sorted(all_fields.items())
            if k in unmapped
        },
    }
    output_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"  Full discovery results saved to: {output_path}")
    print()


# ── Signal report ─────────────────────────────────────────────────────────

def print_report(adapter: SparkIngestionAdapter, results: list) -> None:
    """Print a summary of what the engine found."""
    listings = adapter.store_listings
    total_events = len(results)
    fired = [r for r in results if r.fired_rules]
    total_fired = sum(len(r.fired_rules) for r in results)

    print("=" * 70)
    print("  SPARK LIVE INGESTION REPORT")
    print("=" * 70)
    print(f"  Listings ingested:     {len(listings)}")
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

    # Show BBO signals detected
    bbo_types = {
        "listing_bbo_cdom_threshold_crossed",
        "private_remarks_signal",
        "agent_land_accumulation_detected",
        "office_land_program_detected",
        "developer_exit_signal_detected",
        "subdivision_remnant_detected",
    }
    bbo_events = [r for r in results if r.event_type in bbo_types]
    if bbo_events:
        print(f"  BBO signals detected: {len(bbo_events)}")
        for r in bbo_events:
            print(f"    - {r.event_type} (fired: {r.fired_rules})")
    else:
        print("  BBO signals detected: 0")
    print()

    # Sample listings
    print("  Sample listings (first 5):")
    for listing in listings[:5]:
        status = listing.standard_status.value if listing.standard_status else "?"
        acres = f"{listing.lot_size_acres:.2f}ac" if listing.lot_size_acres else "?ac"
        cdom = f"CDOM={listing.cdom}" if listing.cdom else ""
        addr = listing.address_raw or "no address"
        print(f"    {listing.listing_key}: ${listing.list_price:,.0f} | {acres} | {status} | {cdom} | {addr}")
    print()
    print("=" * 70)


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest live Spark MLS land listings")
    parser.add_argument("--top", type=int, default=100, help="Max records to fetch (default: 100)")
    parser.add_argument("--county", default=None, help="Filter by county (e.g., Washtenaw)")
    parser.add_argument("--discover", action="store_true",
                        help="Run field discovery mode: probe for unmapped fields and exit")
    args = parser.parse_args()

    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key:
        print("ERROR: SPARK_API_KEY not set. Add it to .env or set the env var.", file=sys.stderr)
        sys.exit(1)

    if args.discover:
        discover_fields(api_key, county=args.county)
        return

    print()
    print("=" * 70)
    print("  LandOS — Spark Live Ingestion")
    print("=" * 70)

    # Fetch from API
    raw_records = fetch_listings(api_key, top=args.top, county=args.county)
    if not raw_records:
        print("  No records returned. Check your API key and filters.")
        return

    # Wire up the engine
    engine = TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())
    context = TriggerContext()
    store = InMemoryListingStore()
    adapter = SparkIngestionAdapter(engine=engine, context=context, store=store)

    # Run through the adapter
    print("  Processing through SparkIngestionAdapter...")
    results = adapter.process_batch(raw_records)

    print_report(adapter, results)

    return adapter  # Return for use by run_full_pipeline


if __name__ == "__main__":
    main()
