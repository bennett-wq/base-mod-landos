#!/usr/bin/env python3
"""
Spark BBO Field Discovery Script — LandOS Step 4.5 Pre-Build
=============================================================

Run this against the Spark RESO Web API with your private-role (BBO) credentials
to discover every field available in the feed. Output tells us exactly what to
build in Step 4.5 before a single line of adapter code is written.

Usage:
    SPARK_API_KEY=your_key python3 scripts/spark_bbo_discovery.py

    Or with explicit args:
    python3 scripts/spark_bbo_discovery.py \
        --api-key YOUR_KEY \
        --base-url https://replication.sparkapi.com/v1 \
        --property-type Land

Output:
    - Full field list with types (printed + saved to landos/data/spark_bbo_fields.json)
    - BBO-candidate fields (private-role only, not in public RESO surface)
    - Sample record showing which fields actually contain data for land listings
    - Suggested additions to field_map.py

Spark RESO Web API docs: https://sparkplatform.com/docs/api_services/reso_web_api
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    pass

# ── Known public RESO fields already in our field_map.py ──────────────────────
# Anything NOT in this set is a candidate BBO / private-role field.
KNOWN_PUBLIC_FIELDS: frozenset[str] = frozenset({
    "ListingKey", "ListPrice", "OriginalListPrice", "PropertyType",
    "LotSizeAcres", "PublicRemarks", "ListAgentMlsId", "ListAgentFullName",
    "ListOfficeMlsId", "ListOfficeName", "Latitude", "Longitude",
    "DaysOnMarket", "CumulativeDaysOnMarket", "ClosePrice", "CloseDate",
    "ListingContractDate", "ExpirationDate", "SubdivisionName", "SellerName",
    "UnparsedAddress", "ParcelNumber", "StandardStatus", "ModificationTimestamp",
    "City", "StateOrProvince", "PostalCode", "CountyOrParish",
    "MlsStatus", "ListAgentKey", "ListOfficeKey",
})

# ── Signal families we're hunting for ─────────────────────────────────────────
SIGNAL_FAMILY_KEYWORDS: dict[str, list[str]] = {
    "Developer Exit": [
        "OffMarket", "Withdrawn", "Cancel", "Expire", "ListingAgreement",
        "TerminationDate", "WithdrawalDate", "BuyerFinancing",
    ],
    "Listing Behavior": [
        "CumulativeDays", "CDOM", "PreviousListPrice", "OriginalList",
        "PriceChangeTimestamp", "BackOnMarket", "Relist", "StatusChangeTimestamp",
    ],
    "Language Intelligence": [
        "PrivateRemarks", "ShowingInstructions", "DirectionFaces",
        "Remarks", "AgentNote", "BrokerNote", "InternalNote",
    ],
    "Agent/Office Clustering": [
        "ListAgentKey", "ListAgentNationalAssocId", "ListAgentStateLicense",
        "ListOfficeKey", "ListOfficeNationalAssocId", "CoListAgentKey",
        "CoListOfficeKey", "BuyerAgentKey", "BuyerOfficeKey",
    ],
    "Subdivision Remnant": [
        "SubdivisionName", "LegalDescription", "PlatBook", "PlatPage",
        "Plat", "PhaseNumber", "LotNumber", "Block", "Section", "Township",
    ],
    "Market Velocity": [
        "ClosedDate", "ContractStatusChangeDate", "PurchaseContractDate",
        "PendingTimestamp", "SoldPrice", "SellingPrice", "SaleType",
    ],
    "Parcel / Geo": [
        "ParcelNumber", "TaxParcelLetter", "TaxLegalDescription", "APNNumber",
        "Zoning", "ZoningDescription", "LotFeatures", "LotSizeSquareFeet",
        "LotSizeAcres", "LotDimensions", "FrontageLength", "DepthFeet",
    ],
    "Municipal / Infrastructure": [
        "Sewer", "Water", "Electric", "Gas", "Utilities", "RoadSurface",
        "RoadFrontage", "ImprovementsValue", "ImprovementStatus",
        "PermitNumber", "PermitDate",
    ],
}


def make_request(url: str, api_key: str) -> dict:
    """Make a RESO Web API GET request with Bearer auth."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code} from {url}:\n{body[:500]}", file=sys.stderr)
        raise


def fetch_metadata(base_url: str, api_key: str) -> dict | None:
    """Fetch RESO $metadata if available."""
    url = f"{base_url}/$metadata?$format=json"
    print(f"\nFetching metadata from: {url}")
    try:
        return make_request(url, api_key)
    except Exception as e:
        print(f"Metadata endpoint unavailable ({e}) — will infer from sample record.")
        return None


def fetch_sample_records(
    base_url: str,
    api_key: str,
    property_type: str,
    count: int = 5,
) -> list[dict]:
    """Fetch a small sample of land listing records to see live field names."""
    params = urllib.parse.urlencode({
        "$filter": f"PropertyType eq '{property_type}' and StandardStatus eq 'Active'",
        "$top": count,
        "$orderby": "ModificationTimestamp desc",
    })
    url = f"{base_url}/Property?{params}"
    print(f"\nFetching {count} sample records from: {url}")
    data = make_request(url, api_key)
    return data.get("value", data.get("D", {}).get("Results", []))


def classify_fields(all_fields: set[str]) -> dict[str, list[str]]:
    """Classify fields into signal families based on keyword matching."""
    classified: dict[str, list[str]] = {k: [] for k in SIGNAL_FAMILY_KEYWORDS}
    classified["BBO Candidates (not in public map)"] = []
    classified["Unclassified"] = []

    for field in sorted(all_fields):
        is_bbo_candidate = field not in KNOWN_PUBLIC_FIELDS
        matched_family = None

        for family, keywords in SIGNAL_FAMILY_KEYWORDS.items():
            if any(kw.lower() in field.lower() for kw in keywords):
                classified[family].append(field)
                matched_family = family
                break

        if is_bbo_candidate and matched_family is None:
            classified["BBO Candidates (not in public map)"].append(field)
        elif matched_family is None:
            classified["Unclassified"].append(field)

    return classified


def generate_field_map_suggestions(new_fields: set[str]) -> str:
    """Generate suggested additions to spark/field_map.py."""
    bbo_specific = new_fields - KNOWN_PUBLIC_FIELDS
    lines = ["# ── Suggested BBO field additions to RESO_TO_LISTING ─────────────────────────"]
    for field in sorted(bbo_specific):
        snake = ''.join(
            ['_' + c.lower() if c.isupper() else c for c in field]
        ).lstrip('_')
        lines.append(f'    "{field}": "{snake}",  # BBO — needs Listing model field')
    return '\n'.join(lines)


def run_discovery(
    api_key: str,
    base_url: str,
    property_type: str,
    output_dir: Path,
) -> None:
    print("\n" + "=" * 70)
    print("  LandOS — Spark BBO Field Discovery")
    print("=" * 70)
    print(f"  Base URL:      {base_url}")
    print(f"  Property type: {property_type}")
    print(f"  Output:        {output_dir}")
    print("=" * 70)

    # Step 1: Try metadata endpoint
    metadata = fetch_metadata(base_url, api_key)
    metadata_fields: set[str] = set()
    if metadata:
        # Parse RESO OData metadata for field names
        try:
            schema = metadata.get("$schema", "")
            entities = (
                metadata.get("Edmx", {})
                .get("DataServices", {})
                .get("Schema", [{}])
            )
            if isinstance(entities, dict):
                entities = [entities]
            for schema_block in entities:
                for entity_type in schema_block.get("EntityType", []):
                    for prop in entity_type.get("Property", []):
                        name = prop.get("Name") or prop.get("@Name")
                        if name:
                            metadata_fields.add(name)
            print(f"\nMetadata: found {len(metadata_fields)} fields")
        except Exception as e:
            print(f"Could not parse metadata structure: {e}")
            print("Raw metadata keys:", list(metadata.keys())[:10])

    # Step 2: Fetch sample records
    try:
        samples = fetch_sample_records(base_url, api_key, property_type)
    except Exception as e:
        print(f"\nCould not fetch sample records: {e}")
        samples = []

    # Step 3: Collect all field names from samples
    sample_fields: set[str] = set()
    for record in samples:
        sample_fields.update(record.keys())

    all_fields = metadata_fields | sample_fields
    new_fields = all_fields - KNOWN_PUBLIC_FIELDS

    print(f"\nTotal fields discovered:  {len(all_fields)}")
    print(f"Already in field_map.py:  {len(all_fields & KNOWN_PUBLIC_FIELDS)}")
    print(f"New / BBO candidates:     {len(new_fields)}")

    # Step 4: Classify into signal families
    classified = classify_fields(all_fields)

    # Step 5: Print classification
    print("\n" + "=" * 70)
    print("  FIELD CLASSIFICATION BY SIGNAL FAMILY")
    print("=" * 70)
    for family, fields in classified.items():
        if fields:
            is_new = [f for f in fields if f not in KNOWN_PUBLIC_FIELDS]
            print(f"\n[{family}] ({len(fields)} total, {len(is_new)} new)")
            for f in sorted(fields):
                marker = "  ★ BBO" if f not in KNOWN_PUBLIC_FIELDS else "    --"
                print(f"  {marker}  {f}")

    # Step 6: Show sample record (first one, pretty)
    if samples:
        print("\n" + "=" * 70)
        print("  SAMPLE RECORD (first result — live field values)")
        print("=" * 70)
        sample = samples[0]
        for k, v in sorted(sample.items()):
            marker = "  ★" if k not in KNOWN_PUBLIC_FIELDS else "   "
            print(f"{marker} {k}: {repr(v)[:120]}")

    # Step 7: Generate field_map suggestions
    print("\n" + "=" * 70)
    print("  SUGGESTED field_map.py ADDITIONS")
    print("=" * 70)
    print(generate_field_map_suggestions(new_fields))

    # Step 8: Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "spark_bbo_fields.json"
    output = {
        "discovered_at": datetime.utcnow().isoformat(),
        "base_url": base_url,
        "property_type": property_type,
        "total_fields": len(all_fields),
        "new_fields": sorted(new_fields),
        "all_fields": sorted(all_fields),
        "classified": {k: sorted(v) for k, v in classified.items()},
        "sample_record": samples[0] if samples else {},
    }
    output_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nFull results saved to: {output_path}")
    print("\nShare spark_bbo_fields.json with the PM agent to finalize Step 4.5 spec.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover Spark BBO fields available with private-role credentials"
    )
    parser.add_argument("--api-key", default=os.environ.get("SPARK_API_KEY"),
                        help="Spark API key (or set SPARK_API_KEY env var)")
    parser.add_argument("--base-url",
                        default=os.environ.get(
                            "SPARK_BASE_URL",
                            "https://replication.sparkapi.com/v1"
                        ),
                        help="Spark RESO Web API base URL")
    parser.add_argument("--property-type", default="Land",
                        help="RESO PropertyType to filter on (default: Land)")
    parser.add_argument("--output-dir",
                        default=str(
                            Path(__file__).parent.parent / "data" / "discovery"
                        ),
                        help="Directory to save discovery output JSON")

    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: No API key. Set SPARK_API_KEY env var or pass --api-key", file=sys.stderr)
        sys.exit(1)

    run_discovery(
        api_key=args.api_key,
        base_url=args.base_url,
        property_type=args.property_type,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
