#!/usr/bin/env python3
"""Fetch Spark listing genealogy for top strategic opportunities.

Calls the Spark NATIVE API (not RESO OData) to get the full historical
listing chain for each property — every agent who tried, every price,
every failure. This replaces stallout inference with ground truth.

Endpoints:
  GET https://sparkapi.com/v1/listings/{listing_key}
  (Spark native API returns related/historical listings)

Usage:
    python3 landos/scripts/spark_historical_fetch.py
    python3 landos/scripts/spark_historical_fetch.py --limit 10
    python3 landos/scripts/spark_historical_fetch.py --limit 1 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.stores.sqlite_store import SQLiteStore

# ── Spark Native API ─────────────────────────────────────────────────────

SPARK_NATIVE_BASE = "https://sparkapi.com/v1"
SPARK_RESO_BASE = os.environ.get(
    "SPARK_BASE_URL", "https://replication.sparkapi.com/Reso/OData"
)

# Rate limit: 4,000 req/5min. We use ~2-3 calls per listing_key.
REQUEST_DELAY = 0.5  # seconds between calls (courtesy throttle)


def _spark_native_request(url: str, api_key: str) -> dict | None:
    """Make a Spark native API GET request with Bearer auth."""
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "X-SparkApi-User-Agent": "LandOS/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 404:
            return None
        print(f"  HTTP {e.code} from {url}: {body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Request failed for {url}: {e}", file=sys.stderr)
        return None


def _spark_reso_request(url: str, api_key: str) -> dict | None:
    """Make a RESO OData GET request with Bearer auth."""
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code} from RESO: {body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  RESO request failed: {e}", file=sys.stderr)
        return None


# ── Target listing keys ──────────────────────────────────────────────────


def get_target_listing_keys(db: SQLiteStore, limit: int = 30) -> list[dict]:
    """Extract unique listing_keys for top tier 1+2 strategic opportunities.

    Returns list of dicts: {name, opportunity_id, listing_keys, parcel_numbers, subdivision_name}
    """
    rows = db._conn.execute(
        """SELECT opportunity_id, name, data_json
           FROM strategic_opportunities
           WHERE precedence_tier <= 2
           ORDER BY precedence_tier ASC, composite_score DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    targets = []
    for row in rows:
        data = json.loads(row["data_json"])
        listing_keys = data.get("listing_keys", [])
        # Also get owner-linked listing keys
        owner_linked_keys = data.get("owner_linked_listing_keys", [])
        all_keys = list(set(listing_keys + owner_linked_keys))

        parcel_ids = data.get("parcel_ids", [])
        subdivision_name = data.get("name") or row["name"]

        # If no listing_keys, try to find them from listing_history
        if not all_keys:
            # Try by subdivision name
            if subdivision_name:
                history_rows = db._conn.execute(
                    "SELECT DISTINCT listing_key FROM listing_history WHERE subdivision_name LIKE ?",
                    (f"%{subdivision_name}%",),
                ).fetchall()
                all_keys = [r["listing_key"] for r in history_rows]

        targets.append({
            "name": row["name"] or subdivision_name,
            "opportunity_id": row["opportunity_id"],
            "listing_keys": all_keys,
            "subdivision_name": subdivision_name,
        })

    return targets


# ── Fetch genealogy via RESO OData ───────────────────────────────────────

def fetch_related_listings_reso(
    api_key: str,
    listing_key: str,
    db: SQLiteStore,
) -> list[dict]:
    """Fetch all listings at the same address/parcel using RESO OData.

    Since the Spark native historical endpoint may not be available for all
    credentials, we use RESO OData to find related listings by:
    1. Getting the parcel number and address from the listing
    2. Querying all listings at that parcel/address across all statuses
    """
    # First get the listing's details from our DB
    row = db._conn.execute(
        "SELECT data_json FROM listings WHERE listing_key = ?",
        (listing_key,),
    ).fetchone()

    if not row:
        # Try listing_history
        row = db._conn.execute(
            "SELECT data_json FROM listing_history WHERE listing_key = ? LIMIT 1",
            (listing_key,),
        ).fetchone()

    if not row:
        return []

    data = json.loads(row["data_json"])
    parcel_number = data.get("parcel_number_raw")
    address = data.get("address_raw")

    related: list[dict] = []

    # Search by parcel number (most precise)
    if parcel_number:
        import urllib.parse
        params = urllib.parse.urlencode({
            "$filter": f"ParcelNumber eq '{parcel_number}' and PropertyType eq 'Land'",
            "$top": 50,
            "$orderby": "ModificationTimestamp desc",
        })
        url = f"{SPARK_RESO_BASE}/Property?{params}"
        result = _spark_reso_request(url, api_key)
        if result:
            records = result.get("value", result.get("D", {}).get("Results", []))
            related.extend(records)
            time.sleep(REQUEST_DELAY)

    # Also search by address if we got few results
    if address and len(related) < 3:
        import urllib.parse
        # Clean the address for OData filter
        clean_addr = address.replace("'", "''")
        params = urllib.parse.urlencode({
            "$filter": f"UnparsedAddress eq '{clean_addr}' and PropertyType eq 'Land'",
            "$top": 50,
            "$orderby": "ModificationTimestamp desc",
        })
        url = f"{SPARK_RESO_BASE}/Property?{params}"
        result = _spark_reso_request(url, api_key)
        if result:
            records = result.get("value", result.get("D", {}).get("Results", []))
            # Dedup by ListingKey
            existing_keys = {r.get("ListingKey") for r in related}
            for rec in records:
                if rec.get("ListingKey") not in existing_keys:
                    related.append(rec)
            time.sleep(REQUEST_DELAY)

    return related


def extract_genealogy_entries(
    source_listing_key: str,
    related_records: list[dict],
) -> list[dict]:
    """Convert raw related listing records into genealogy entries."""
    entries = []
    for rec in related_records:
        related_key = rec.get("ListingKey", "")
        status = rec.get("StandardStatus", "")

        # Determine event type from status
        event_type = "listed"
        if status in ("Expired",):
            event_type = "expired"
        elif status in ("Withdrawn",):
            event_type = "withdrawn"
        elif status in ("Canceled", "Cancelled"):
            event_type = "canceled"
        elif status in ("Closed",):
            event_type = "closed"
        elif status in ("Pending", "ActiveUnderContract"):
            event_type = "pending"
        elif status == "Active":
            event_type = "active"

        # Determine relationship
        relationship = "same_property"
        if related_key == source_listing_key:
            relationship = "self"

        # Best date for this record
        event_date = (
            rec.get("CloseDate")
            or rec.get("ExpirationDate")
            or rec.get("StatusChangeTimestamp", "")[:10]
            or rec.get("ListingContractDate")
            or rec.get("OnMarketDate")
        )

        entries.append({
            "listing_key": source_listing_key,
            "related_listing_key": related_key,
            "relationship": relationship,
            "event_type": event_type,
            "event_date": event_date,
            "list_price": int(float(rec.get("ListPrice", 0) or 0)),
            "status": status,
            "agent_name": rec.get("ListAgentFullName"),
            "office_name": rec.get("ListOfficeName"),
            "days_on_market": (
                int(rec["CumulativeDaysOnMarket"])
                if rec.get("CumulativeDaysOnMarket") is not None
                else int(rec["DaysOnMarket"])
                if rec.get("DaysOnMarket") is not None
                else None
            ),
            "source_data": {
                "ListingKey": related_key,
                "StandardStatus": status,
                "ListPrice": rec.get("ListPrice"),
                "OriginalListPrice": rec.get("OriginalListPrice"),
                "ListingContractDate": rec.get("ListingContractDate"),
                "CloseDate": rec.get("CloseDate"),
                "ExpirationDate": rec.get("ExpirationDate"),
                "DaysOnMarket": rec.get("DaysOnMarket"),
                "CumulativeDaysOnMarket": rec.get("CumulativeDaysOnMarket"),
                "ListAgentFullName": rec.get("ListAgentFullName"),
                "ListOfficeName": rec.get("ListOfficeName"),
                "PrivateRemarks": rec.get("PrivateRemarks"),
                "SubdivisionName": rec.get("SubdivisionName"),
                "ParcelNumber": rec.get("ParcelNumber"),
                "SellerName": rec.get("SellerName"),
            },
        })

    return entries


# ── Also try Spark native API ────────────────────────────────────────────

def fetch_listing_native(api_key: str, listing_key: str) -> dict | None:
    """Try to get a listing via the Spark native API.

    GET https://sparkapi.com/v1/listings/{listing_key}
    """
    url = f"{SPARK_NATIVE_BASE}/listings/{listing_key}"
    return _spark_native_request(url, api_key)


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Spark listing genealogy for top strategic opportunities"
    )
    parser.add_argument("--limit", type=int, default=30,
                        help="Top N opportunities to fetch genealogy for (default: 30)")
    parser.add_argument("--db", default=None,
                        help="SQLite DB path (default: landos/data/landos.db)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be fetched without making API calls")
    parser.add_argument("--clear", action="store_true",
                        help="Clear existing genealogy data before fetching")
    args = parser.parse_args()

    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key:
        print("ERROR: SPARK_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    db_path = args.db or str(_PROJECT_ROOT / "data" / "landos.db")
    db = SQLiteStore(db_path)

    print()
    print("=" * 70)
    print("  LandOS — Spark Listing Genealogy Fetch")
    print("=" * 70)

    if args.clear:
        db.clear_genealogy()
        print("  Cleared existing genealogy data.")

    # Get target opportunities and their listing keys
    targets = get_target_listing_keys(db, limit=args.limit)
    total_keys = sum(len(t["listing_keys"]) for t in targets)

    print(f"  Opportunities found: {len(targets)}")
    print(f"  Total listing keys to research: {total_keys}")
    print(f"  Estimated API calls: ~{total_keys * 2}")
    print()

    if args.dry_run:
        print("  DRY RUN — would fetch genealogy for:")
        for i, t in enumerate(targets, 1):
            keys = t["listing_keys"][:5]
            more = f" (+{len(t['listing_keys']) - 5} more)" if len(t["listing_keys"]) > 5 else ""
            print(f"    {i}. {t['name']}: {len(t['listing_keys'])} keys — {keys}{more}")
        print()
        print("  Run without --dry-run to fetch.")
        db.close()
        return

    # Fetch genealogy for each opportunity
    total_entries = 0
    total_api_calls = 0

    for i, target in enumerate(targets, 1):
        name = target["name"]
        keys = target["listing_keys"]
        if not keys:
            print(f"  [{i}/{len(targets)}] {name}: no listing keys — skipping")
            continue

        print(f"  [{i}/{len(targets)}] {name}: researching {len(keys)} listing(s)...")

        opp_entries = []
        for key in keys:
            # Fetch related listings via RESO OData (parcel/address match)
            related = fetch_related_listings_reso(api_key, key, db)
            total_api_calls += 2  # up to 2 calls per key (parcel + address)

            entries = extract_genealogy_entries(key, related)
            opp_entries.extend(entries)

            # Also try native API for this listing
            native_result = fetch_listing_native(api_key, key)
            total_api_calls += 1
            if native_result:
                # If native API returns data, log it
                d = native_result.get("D", {}).get("Results", [])
                if isinstance(d, list):
                    for rec in d:
                        native_entries = extract_genealogy_entries(key, [rec])
                        # Dedup against what we already have
                        existing_related = {e["related_listing_key"] for e in opp_entries}
                        for ne in native_entries:
                            if ne["related_listing_key"] not in existing_related:
                                opp_entries.append(ne)

            time.sleep(REQUEST_DELAY)

        if opp_entries:
            db.save_genealogy_batch(opp_entries)
            total_entries += len(opp_entries)
            # Count unique related listings (excluding self)
            unique_related = {
                e["related_listing_key"]
                for e in opp_entries
                if e["relationship"] != "self"
            }
            print(f"    → {len(opp_entries)} genealogy entries, {len(unique_related)} related listings")
        else:
            print(f"    → no related listings found")

    # Summary
    print()
    print("=" * 70)
    print("  GENEALOGY FETCH COMPLETE")
    print("=" * 70)
    print(f"  Opportunities researched: {len(targets)}")
    print(f"  API calls made: {total_api_calls}")
    print(f"  Genealogy entries saved: {total_entries}")

    # Show a summary of what we found
    rows = db._conn.execute(
        "SELECT listing_key, COUNT(*) as cnt FROM listing_genealogy GROUP BY listing_key ORDER BY cnt DESC LIMIT 10"
    ).fetchall()
    if rows:
        print()
        print("  Top listings by genealogy depth:")
        for r in rows:
            print(f"    {r['listing_key']}: {r['cnt']} entries")

    print()
    db.close()


if __name__ == "__main__":
    main()
