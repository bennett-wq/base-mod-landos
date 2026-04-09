#!/usr/bin/env python3
"""Fetch Spark market statistics for Washtenaw County land.

Pulls all 6 market statistic time-series from the Spark API and stores
them in the market_statistics SQLite table. This feeds the EconomicsPage
(currently hardcoded charts) with real monthly data.

Spark Market Statistics API:
  Base: https://sparkapi.com/v1/marketstatistics/{type}
  Types: absorption, inventory, price, ratio, dom, volume

  Note: If sparkapi.com/v1 returns 403 (key restricted), we fall back to
  constructing market stats from our own listing_history data.

Usage:
    python3 landos/scripts/spark_market_stats.py
    python3 landos/scripts/spark_market_stats.py --types absorption price dom
    python3 landos/scripts/spark_market_stats.py --county Washtenaw
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from src.stores.sqlite_store import SQLiteStore

# ── Config ───────────────────────────────────────────────────────────────

SPARK_NATIVE_BASE = "https://sparkapi.com/v1"
SPARK_RESO_BASE = os.environ.get(
    "SPARK_BASE_URL", "https://replication.sparkapi.com/Reso/OData"
)

STAT_TYPES = ["absorption", "inventory", "price", "ratio", "dom", "volume"]

REQUEST_DELAY = 0.5


# ── Spark API calls ─────────────────────────────────────────────────────

def fetch_market_stat_native(
    api_key: str,
    stat_type: str,
    county: str,
    property_type: str = "Land",
) -> dict | None:
    """Try Spark native Market Statistics API.

    GET https://sparkapi.com/v1/marketstatistics/{type}
        ?_filter=CountyOrParish Eq '{county}' And PropertyType Eq '{property_type}'
    """
    params = urllib.parse.urlencode({
        "_filter": f"CountyOrParish Eq '{county}' And PropertyType Eq '{property_type}'",
    })
    url = f"{SPARK_NATIVE_BASE}/marketstatistics/{stat_type}?{params}"

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
        if e.code == 403:
            print(f"    Native API 403 for {stat_type} — will use derived stats", file=sys.stderr)
        else:
            print(f"    HTTP {e.code} for {stat_type}: {body[:200]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"    Request failed for {stat_type}: {e}", file=sys.stderr)
        return None


def parse_native_stat_response(
    stat_type: str,
    data: dict,
    county: str,
    property_type: str,
) -> list[dict]:
    """Parse Spark native market statistics response into DB entries."""
    entries = []
    # Spark returns D.Results array with monthly data points
    results = data.get("D", {}).get("Results", [])
    if not results:
        results = data.get("value", [])
    if not results and isinstance(data, list):
        results = data

    for item in results:
        # Each item has a date field and one or more value fields
        date_str = item.get("Date") or item.get("Year") or ""
        if not date_str:
            continue

        # Extract year and month
        try:
            if len(str(date_str)) == 4:
                year = int(date_str)
                month = 1
                period = f"{year:04d}-01"
            else:
                dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                year = dt.year
                month = dt.month
                period = f"{year:04d}-{month:02d}"
        except (ValueError, TypeError):
            continue

        # The value field name varies by stat type
        value = item.get("Value") or item.get(stat_type.capitalize()) or item.get("Average")
        if value is not None:
            try:
                value = float(value)
            except (ValueError, TypeError):
                continue

            entries.append({
                "stat_type": stat_type,
                "county": county,
                "property_type": property_type,
                "period": period,
                "value": value,
                "year": year,
                "month": month,
                "source_data": item,
            })

    return entries


# ── Derived stats from listing_history ───────────────────────────────────

def derive_stats_from_history(
    db: SQLiteStore,
    county: str,
    property_type: str = "Land",
) -> list[dict]:
    """Derive market statistics from our listing_history table.

    When the Spark Market Statistics API is unavailable (403), we compute
    approximations from the listing snapshots we've already ingested.
    """
    print("  Deriving market stats from listing_history...")

    # Get all history records
    rows = db._conn.execute(
        """SELECT listing_key, snapshot_status, list_price, dom, cdom,
                  original_list_price, list_date, close_date, ingested_at,
                  lot_size_acres
           FROM listing_history
           ORDER BY ingested_at"""
    ).fetchall()

    if not rows:
        print("    No listing_history data available.")
        return []

    # Group by month based on ingested_at
    monthly: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        ingested = r["ingested_at"] or ""
        if len(ingested) >= 7:
            period = ingested[:7]  # YYYY-MM
        else:
            continue
        monthly[period].append(dict(r))

    entries = []
    for period in sorted(monthly.keys()):
        records = monthly[period]
        year = int(period[:4])
        month = int(period[5:7])

        # Inventory: count of distinct active listing keys
        # Status values are lowercase (from normalizer) or title case (raw)
        active_keys = {r["listing_key"] for r in records if (r["snapshot_status"] or "").lower() == "active"}
        closed_keys = {r["listing_key"] for r in records if (r["snapshot_status"] or "").lower() == "closed"}
        expired_keys = {r["listing_key"] for r in records if (r["snapshot_status"] or "").lower() == "expired"}
        pending_keys = {r["listing_key"] for r in records if (r["snapshot_status"] or "").lower() in ("pending", "activeundercontract")}

        # Inventory stat
        entries.append({
            "stat_type": "inventory",
            "county": county,
            "property_type": property_type,
            "period": period,
            "value": len(active_keys),
            "year": year,
            "month": month,
            "source_data": {
                "method": "derived_from_listing_history",
                "active": len(active_keys),
                "closed": len(closed_keys),
                "expired": len(expired_keys),
                "pending": len(pending_keys),
            },
        })

        # Price stat: average list price of active listings
        active_prices = [
            r["list_price"] for r in records
            if (r["snapshot_status"] or "").lower() == "active" and r["list_price"]
        ]
        if active_prices:
            avg_price = sum(active_prices) / len(active_prices)
            entries.append({
                "stat_type": "price",
                "county": county,
                "property_type": property_type,
                "period": period,
                "value": round(avg_price, 2),
                "year": year,
                "month": month,
                "source_data": {
                    "method": "derived_from_listing_history",
                    "count": len(active_prices),
                    "avg": round(avg_price, 2),
                    "min": min(active_prices),
                    "max": max(active_prices),
                },
            })

        # DOM stat: average DOM of active listings
        active_doms = [
            r["cdom"] or r["dom"]
            for r in records
            if (r["snapshot_status"] or "").lower() == "active" and (r["cdom"] or r["dom"])
        ]
        if active_doms:
            avg_dom = sum(active_doms) / len(active_doms)
            entries.append({
                "stat_type": "dom",
                "county": county,
                "property_type": property_type,
                "period": period,
                "value": round(avg_dom, 1),
                "year": year,
                "month": month,
                "source_data": {
                    "method": "derived_from_listing_history",
                    "count": len(active_doms),
                    "avg": round(avg_dom, 1),
                },
            })

        # Absorption: closed / (active + closed) if denominator > 0
        total_supply = len(active_keys) + len(closed_keys)
        if total_supply > 0:
            absorption = len(closed_keys) / total_supply
            entries.append({
                "stat_type": "absorption",
                "county": county,
                "property_type": property_type,
                "period": period,
                "value": round(absorption, 4),
                "year": year,
                "month": month,
                "source_data": {
                    "method": "derived_from_listing_history",
                    "closed": len(closed_keys),
                    "total_supply": total_supply,
                },
            })

        # Volume: total list value of closed listings
        closed_prices = [
            r["list_price"] for r in records
            if (r["snapshot_status"] or "").lower() == "closed" and r["list_price"]
        ]
        if closed_prices:
            volume = sum(closed_prices)
            entries.append({
                "stat_type": "volume",
                "county": county,
                "property_type": property_type,
                "period": period,
                "value": volume,
                "year": year,
                "month": month,
                "source_data": {
                    "method": "derived_from_listing_history",
                    "count": len(closed_prices),
                    "total": volume,
                },
            })

        # Ratio: avg(list_price / original_list_price) for closed listings
        ratios = []
        for r in records:
            if (
                (r["snapshot_status"] or "").lower() == "closed"
                and r["list_price"]
                and r["original_list_price"]
                and r["original_list_price"] > 0
            ):
                ratios.append(r["list_price"] / r["original_list_price"])
        if ratios:
            avg_ratio = sum(ratios) / len(ratios)
            entries.append({
                "stat_type": "ratio",
                "county": county,
                "property_type": property_type,
                "period": period,
                "value": round(avg_ratio, 4),
                "year": year,
                "month": month,
                "source_data": {
                    "method": "derived_from_listing_history",
                    "count": len(ratios),
                    "avg": round(avg_ratio, 4),
                },
            })

    print(f"    Derived {len(entries)} stat entries across {len(monthly)} months")
    return entries


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Spark market statistics for land listings"
    )
    parser.add_argument("--types", nargs="+", default=STAT_TYPES,
                        choices=STAT_TYPES,
                        help=f"Stat types to fetch (default: all)")
    parser.add_argument("--county", default="Washtenaw",
                        help="County filter (default: Washtenaw)")
    parser.add_argument("--property-type", default="Land",
                        help="Property type (default: Land)")
    parser.add_argument("--db", default=None,
                        help="SQLite DB path (default: landos/data/landos.db)")
    parser.add_argument("--force-derived", action="store_true",
                        help="Skip native API, derive all stats from listing_history")
    args = parser.parse_args()

    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key:
        print("ERROR: SPARK_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    db_path = args.db or str(_PROJECT_ROOT / "data" / "landos.db")
    db = SQLiteStore(db_path)

    print()
    print("=" * 70)
    print("  LandOS — Spark Market Statistics Fetch")
    print("=" * 70)
    print(f"  County: {args.county}")
    print(f"  Property type: {args.property_type}")
    print(f"  Stat types: {', '.join(args.types)}")
    print()

    all_entries: list[dict] = []
    native_available = not args.force_derived

    if native_available:
        # Try native API first
        print("  Trying Spark native Market Statistics API...")
        for stat_type in args.types:
            print(f"    Fetching {stat_type}...")
            result = fetch_market_stat_native(
                api_key, stat_type, args.county, args.property_type
            )
            if result is not None:
                entries = parse_native_stat_response(
                    stat_type, result, args.county, args.property_type
                )
                all_entries.extend(entries)
                print(f"      → {len(entries)} data points")
            else:
                native_available = False
                print(f"      → Native API unavailable, switching to derived stats")
                break
            time.sleep(REQUEST_DELAY)

    if not native_available:
        # Fall back to deriving stats from listing_history
        all_entries = derive_stats_from_history(db, args.county, args.property_type)

    if all_entries:
        db.save_market_stats_batch(all_entries)
        print()
        print(f"  Saved {len(all_entries)} market statistics entries")

        # Show summary
        by_type: dict[str, int] = defaultdict(int)
        for e in all_entries:
            by_type[e["stat_type"]] += 1
        print()
        print("  Entries by stat type:")
        for st, count in sorted(by_type.items()):
            print(f"    {st}: {count} periods")

        # Show latest values
        summary = db.get_market_stats_summary(args.county)
        if summary:
            print()
            print("  Latest values:")
            for st, info in sorted(summary.items()):
                trend_arrow = {"up": "↑", "down": "↓", "flat": "→"}.get(info["trend"], "?")
                change = f" ({info['change_pct']:+.1f}%)" if info["change_pct"] is not None else ""
                print(f"    {st}: {info['latest']:.2f} [{info['period']}] {trend_arrow}{change}")
    else:
        print("  No market statistics data available.")

    print()
    db.close()


if __name__ == "__main__":
    main()
