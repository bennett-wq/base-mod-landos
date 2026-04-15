"""Comp narrator — three-comp-set agent: aggregates, anchor comp, exit $/sf, confidence.

Implemented in M2-5.

Function signature:
    narrate_comps(set1_rows, set2_rows, set3_rows, sqft_target, sqft_band) -> dict
"""

from __future__ import annotations

import statistics
from datetime import date
from typing import Any


def _parse_date(value: str | date | None) -> date | None:
    """Parse an ISO date string or return a date as-is."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _resolve_ppsf(row: dict) -> float | None:
    """Return ppsf from row, computing price/sqft if needed."""
    if row.get("ppsf") is not None:
        return float(row["ppsf"])
    price = row.get("price")
    sqft = row.get("sqft")
    if price and sqft and sqft > 0:
        return float(price) / float(sqft)
    return None


def _row_to_comp_dict(row: dict) -> dict:
    """Normalize a comp row into a Comp-compatible dict."""
    ppsf = _resolve_ppsf(row)
    return {
        "address": row["address"],
        "close_date": str(_parse_date(row.get("close_date"))),
        "price": float(row["price"]),
        "sqft": row.get("sqft"),
        "ppsf": ppsf,
        "year_built": row.get("year_built"),
        "distance_mi": float(row.get("distance_mi", 0.0)),
        "subdivision": row.get("subdivision"),
        "cdom": row.get("cdom"),
    }


def _median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.median(values)


def _set1_aggregates(rows: list[dict]) -> dict:
    """Compute Set 1 aggregates: median_ppsf, count, median_price, date_range_days."""
    ppsf_values = [p for p in (_resolve_ppsf(r) for r in rows) if p is not None]
    prices = [float(r["price"]) for r in rows]
    dates = [_parse_date(r.get("close_date")) for r in rows]
    dates = [d for d in dates if d is not None]

    median_ppsf = statistics.median(ppsf_values) if ppsf_values else 0.0
    median_price = statistics.median(prices) if prices else None

    date_range_days = 0
    if len(dates) >= 2:
        date_range_days = (max(dates) - min(dates)).days

    return {
        "median_ppsf": median_ppsf,
        "count": len(rows),
        "median_price": median_price,
        "date_range_days": date_range_days,
    }


def _set2_aggregates(rows: list[dict], sqft_band: tuple[int, int]) -> tuple[dict, dict]:
    """Compute Set 2 aggregates: all rows + Jaxon-band filtered rows."""
    ppsf_all = [p for p in (_resolve_ppsf(r) for r in rows) if p is not None]
    agg_all = {
        "median_ppsf": statistics.median(ppsf_all) if ppsf_all else 0.0,
        "count": len(rows),
        "median_price": statistics.median([float(r["price"]) for r in rows]) if rows else None,
    }

    band_rows = [
        r for r in rows
        if r.get("sqft") is not None and sqft_band[0] <= int(r["sqft"]) <= sqft_band[1]
    ]
    ppsf_band = [p for p in (_resolve_ppsf(r) for r in band_rows) if p is not None]
    agg_band = {
        "median_ppsf": statistics.median(ppsf_band) if ppsf_band else 0.0,
        "count": len(band_rows),
        "median_price": statistics.median([float(r["price"]) for r in band_rows]) if band_rows else None,
    }

    return agg_all, agg_band


def _set3_aggregates(rows: list[dict]) -> tuple[dict, dict, dict]:
    """Compute Set 3 aggregates: all, sub-half-acre, within-3mi."""
    prices_all = [float(r["price"]) for r in rows]
    agg_all = {
        "median_ppsf": 0.0,
        "count": len(rows),
        "median_price": statistics.median(prices_all) if prices_all else None,
    }

    # sub-half-acre: rows where acres is present and < 0.5
    sub_half = [r for r in rows if r.get("acres") is not None and float(r["acres"]) < 0.5]
    prices_sub = [float(r["price"]) for r in sub_half]
    agg_sub_half = {
        "median_ppsf": 0.0,
        "count": len(sub_half),
        "median_price": statistics.median(prices_sub) if prices_sub else None,
    }

    # within-3mi
    within_3mi = [r for r in rows if float(r.get("distance_mi", 9999.0)) < 3.0]
    prices_3mi = [float(r["price"]) for r in within_3mi]
    agg_3mi = {
        "median_ppsf": 0.0,
        "count": len(within_3mi),
        "median_price": statistics.median(prices_3mi) if prices_3mi else None,
    }

    return agg_all, agg_sub_half, agg_3mi


def _select_anchor(
    set1_rows: list[dict],
    set2_rows: list[dict],
    sqft_band: tuple[int, int],
) -> dict | None:
    """Pick anchor comp: nearest Set 1 comp; tie-break on recency. Falls back to nearest Set 2 in band."""
    if set1_rows:
        candidates = sorted(
            set1_rows,
            key=lambda r: (
                float(r.get("distance_mi", 9999.0)),
                # negate date for recency (most recent first on tie)
                -(_parse_date(r.get("close_date")) or date.min).toordinal(),
            ),
        )
        return candidates[0]

    # Fall back to Set 2 filtered by sqft_band
    band_rows = [
        r for r in set2_rows
        if r.get("sqft") is not None and sqft_band[0] <= int(r["sqft"]) <= sqft_band[1]
    ]
    if band_rows:
        candidates = sorted(
            band_rows,
            key=lambda r: (
                float(r.get("distance_mi", 9999.0)),
                -(_parse_date(r.get("close_date")) or date.min).toordinal(),
            ),
        )
        return candidates[0]

    return None


def _compute_confidence(
    set1_rows: list[dict],
    band_count: int,
    exit_ppsf: float | None,
) -> str:
    """Determine confidence tier."""
    if not set1_rows and band_count == 0:
        return "none"
    if len(set1_rows) >= 2 and band_count >= 5 and exit_ppsf is not None:
        return "high"
    if len(set1_rows) >= 1 or band_count >= 2:
        return "medium"
    return "low"


def _build_rationale(
    anchor: dict,
    set1_rows: list[dict],
    exit_ppsf: float | None,
    sqft_band: tuple[int, int],
) -> str:
    """Build anchor_rationale string per spec template."""
    addr = anchor["address"]
    dist = float(anchor.get("distance_mi", 0.0))
    ppsf = _resolve_ppsf(anchor) or 0.0
    year_built = anchor.get("year_built", "n/a")

    rationale = f"Closest infill comp: {addr} ({dist:.1f} mi, ${ppsf:.0f}/sf, {year_built})."

    # Count outlier comps (ppsf > 20% above anchor ppsf)
    if ppsf > 0:
        outliers = [
            r for r in set1_rows
            if r.get("address") != anchor.get("address")
            and (_resolve_ppsf(r) or 0.0) > ppsf * 1.20
        ]
        if outliers:
            n = len(outliers)
            rationale += f" {n} outlier comp{'s' if n != 1 else ''} excluded from anchor (platted new-construction tracts)."

    if exit_ppsf is not None:
        rationale += f" Exit anchored at ${exit_ppsf:.0f}/sf (Set 1 anchor + Set 2 {sqft_band} median)."

    return rationale


def narrate_comps(
    set1_rows: list[dict],
    set2_rows: list[dict],
    set3_rows: list[dict],
    sqft_target: int = 1280,
    sqft_band: tuple[int, int] = (1000, 1500),
) -> dict[str, Any]:
    """Produce three comp sets with aggregates and an anchor comp + exit $/sf.

    Args:
        set1_rows: Tight SFR comps (new-ish, pre-filtered by caller).
        set2_rows: Broad SFR comps (large set — only aggregates extracted).
        set3_rows: Land comps (Washtenaw).
        sqft_target: Target home sqft (default 1280 for Jaxon).
        sqft_band: (low, high) sqft range for Set 2 Jaxon-band filter.

    Returns:
        dict with comp sets, aggregates, anchor_comp, exit_ppsf, confidence,
        anchor_rationale, and status ("ok" or "no_comps").
    """
    # Empty check
    if not set1_rows and not set2_rows and not set3_rows:
        return {
            "status": "no_comps",
            "comp_set_1": [],
            "comp_set_1_aggregates": {"median_ppsf": 0.0, "count": 0, "median_price": None, "date_range_days": 0},
            "comp_set_2_all": {"median_ppsf": 0.0, "count": 0, "median_price": None},
            "comp_set_2_jaxon_band": {"median_ppsf": 0.0, "count": 0, "median_price": None},
            "comp_set_3": [],
            "comp_set_3_all": {"median_ppsf": 0.0, "count": 0, "median_price": None},
            "comp_set_3_sub_half_acre": {"median_ppsf": 0.0, "count": 0, "median_price": None},
            "comp_set_3_within_3mi": {"median_ppsf": 0.0, "count": 0, "median_price": None},
            "anchor_comp": None,
            "anchor_rationale": "",
            "exit_ppsf": None,
            "confidence": "none",
        }

    # ── Set 1 ─────────────────────────────────────────────────────────
    set1_comp_dicts = [_row_to_comp_dict(r) for r in set1_rows]
    agg1 = _set1_aggregates(set1_rows)

    # ── Set 2 ─────────────────────────────────────────────────────────
    agg2_all, agg2_band = _set2_aggregates(set2_rows, sqft_band)

    # ── Set 3 ─────────────────────────────────────────────────────────
    set3_comp_dicts = [_row_to_comp_dict(r) for r in set3_rows]
    agg3_all, agg3_sub_half, agg3_3mi = _set3_aggregates(set3_rows)

    # ── Anchor comp ───────────────────────────────────────────────────
    anchor_row = _select_anchor(set1_rows, set2_rows, sqft_band)
    anchor_dict = _row_to_comp_dict(anchor_row) if anchor_row is not None else None

    # ── exit_ppsf ─────────────────────────────────────────────────────
    anchor_ppsf = _resolve_ppsf(anchor_row) if anchor_row is not None else None
    band_median = agg2_band["median_ppsf"] if agg2_band["count"] > 0 else None
    # band_median of 0.0 means no data — treat as None
    if band_median == 0.0 and agg2_band["count"] == 0:
        band_median = None

    if anchor_ppsf is not None and band_median is not None:
        exit_ppsf = min(anchor_ppsf, band_median)
    elif anchor_ppsf is not None:
        exit_ppsf = anchor_ppsf
    elif band_median is not None:
        exit_ppsf = band_median
    else:
        exit_ppsf = None

    # ── Confidence ────────────────────────────────────────────────────
    confidence = _compute_confidence(set1_rows, agg2_band["count"], exit_ppsf)

    # ── Rationale ─────────────────────────────────────────────────────
    if anchor_dict is not None:
        rationale = _build_rationale(anchor_row, set1_rows, exit_ppsf, sqft_band)
    else:
        rationale = ""

    return {
        "status": "ok",
        "comp_set_1": set1_comp_dicts,
        "comp_set_1_aggregates": agg1,
        "comp_set_2_all": agg2_all,
        "comp_set_2_jaxon_band": agg2_band,
        "comp_set_3": set3_comp_dicts,
        "comp_set_3_all": agg3_all,
        "comp_set_3_sub_half_acre": agg3_sub_half,
        "comp_set_3_within_3mi": agg3_3mi,
        "anchor_comp": anchor_dict,
        "anchor_rationale": rationale,
        "exit_ppsf": exit_ppsf,
        "confidence": confidence,
    }
