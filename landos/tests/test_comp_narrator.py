"""Tests for comp_narrator agent (M2-5).

Uses synthetic McCartney reference data to verify anchor selection,
exit_ppsf, aggregates, confidence, and the MCP handler round-trip.
"""

from __future__ import annotations

import pytest

from src.agents.comp_narrator import narrate_comps
from src.models.opportunity import Comp, CompAggregates

# ---------------------------------------------------------------------------
# McCartney reference data (inline, no fixtures needed)
# ---------------------------------------------------------------------------

SET1_ROWS = [
    {
        "address": "1070 Hawthorne Ave, Ypsilanti",
        "close_date": "2026-02-09",
        "price": 230000,
        "sqft": 1256,
        "ppsf": 183.0,
        "year_built": 2022,
        "distance_mi": 2.0,
    },
    {
        "address": "1866 Wexford Dr, Ypsilanti",
        "close_date": "2025-11-25",
        "price": 325000,
        "sqft": 1331,
        "ppsf": 244.0,
        "year_built": 2023,
        "distance_mi": 3.9,
    },
    {
        "address": "1433 Weeping Willow Ct, Ypsilanti",
        "close_date": "2026-01-13",
        "price": 374308,
        "sqft": 1570,
        "ppsf": 238.0,
        "year_built": 2025,
        "distance_mi": 3.5,
    },
]

SET3_ROWS = [
    {"address": "1784 Emerson Ave", "close_date": "2025-04-28", "price": 62500, "distance_mi": 0.2, "acres": 0.44},
    {"address": "2149 McGregor Ave", "close_date": "2025-06-06", "price": 22500, "distance_mi": 0.6, "acres": 0.29},
    {"address": "1736 S Pasadena",   "close_date": "2025-07-23", "price": 3500,  "distance_mi": 0.2, "acres": 0.20},
    {"address": "341 Orchard",       "close_date": "2025-09-02", "price": 13000, "distance_mi": 3.3, "acres": 0.14},
    {"address": "319 Orchard",       "close_date": "2025-09-02", "price": 5666,  "distance_mi": 3.4, "acres": 0.14},
]


def _build_set2_rows() -> list[dict]:
    """Build 46 Set 2 rows: 16 in Jaxon band (1000-1500 sqft) at $183/sf median,
    30 outside band at various prices giving ~$175/sf overall median.

    Band rows (16): all at sqft=1280, price=183*1280=234240 → ppsf exactly 183.
    Outside-band rows (30): sqft=800, prices that push overall median to ~$175/sf.
      800 * 175 = 140000. Mixing high and low.
    """
    rows = []
    # 16 in-band rows at exactly $183/sf
    for i in range(16):
        rows.append({
            "address": f"Band House {i}, Ypsilanti",
            "close_date": "2025-10-01",
            "price": 183.0 * 1280,
            "sqft": 1280,
            "ppsf": 183.0,
            "distance_mi": float(3 + i * 0.1),
        })
    # 30 outside-band rows: sqft=800, ppsf=140000/800=175
    # To produce a cross-all median of ~$175/sf we need 30 rows below $183/sf.
    # Use ppsf=165 for lower half and ppsf=185 for upper half → median lands near 175.
    # Actually: we want all-46 median_ppsf ~ 175.
    # Sorted 46 ppsf values: 30 out-of-band + 16 in-band (183.0).
    # Median of 46 = average of 23rd and 24th values when sorted.
    # With 15 at 165, 15 at 185, 16 at 183 → sorted: [165x15, 183x16, 185x15]
    # 23rd value = 183, 24th = 183 → median = 183.  Too high.
    # We need the median of all 46 to be 175 per spec.
    # Use: 30 outside-band all at ppsf=167 → sorted: [167x30, 183x16]
    # 23rd value = 167, 24th = 167 → median = 167. Too low.
    # Use: 23 at ppsf=167, 7 at ppsf=183+, 16 in-band at 183
    # Best approach: spec says "all median $175/sf overall".
    # 46 rows, median = avg(23rd, 24th). We need both ~175.
    # Mix: 20 at 165, 10 at 175, 16 at 183 → sorted: [165x20, 175x10, 183x16]
    # 23rd value = 175, 24th = 175 → median = 175. ✓
    for i in range(20):
        rows.append({
            "address": f"Low House {i}, Ypsilanti",
            "close_date": "2025-08-01",
            "price": 165.0 * 800,
            "sqft": 800,
            "ppsf": 165.0,
            "distance_mi": float(5 + i * 0.1),
        })
    for i in range(10):
        rows.append({
            "address": f"Mid House {i}, Ypsilanti",
            "close_date": "2025-09-01",
            "price": 175.0 * 900,
            "sqft": 900,
            "ppsf": 175.0,
            "distance_mi": float(7 + i * 0.1),
        })
    assert len(rows) == 46
    return rows


SET2_ROWS = _build_set2_rows()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_narrate_comps_anchor_selection():
    """Anchor comp is 1070 Hawthorne Ave (min distance_mi=2.0 from Set 1)."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    anchor = result["anchor_comp"]
    assert anchor is not None
    assert "1070 Hawthorne" in anchor["address"]
    assert anchor["distance_mi"] == pytest.approx(2.0)


def test_narrate_comps_exit_ppsf():
    """exit_ppsf = 183.0 — min(anchor ppsf=183, Set2 Jaxon band median=183)."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    assert result["exit_ppsf"] == pytest.approx(183.0, abs=0.5)


def test_narrate_comps_set1_aggregates():
    """Set 1 count=3, median_ppsf in [183, 244] (the three comps are 183, 238, 244)."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    agg = result["comp_set_1_aggregates"]
    assert agg["count"] == 3
    # Sorted: 183, 238, 244 → median = 238
    assert 183.0 <= agg["median_ppsf"] <= 244.0
    assert agg["median_ppsf"] == pytest.approx(238.0, abs=1.0)


def test_narrate_comps_set2_jaxon_band():
    """Set 2 Jaxon band count=16, median_ppsf ≈ 183."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    band = result["comp_set_2_jaxon_band"]
    assert band["count"] == 16
    assert band["median_ppsf"] == pytest.approx(183.0, abs=1.0)


def test_narrate_comps_set3_within_3mi():
    """Set 3 within-3mi count=3 (Emerson 0.2mi + McGregor 0.6mi + S Pasadena 0.2mi)."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    within = result["comp_set_3_within_3mi"]
    assert within["count"] == 3


def test_narrate_comps_confidence_high():
    """With full Set 1 (3 comps) + Set 2 Jaxon band (16 comps) → confidence='high'."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    assert result["confidence"] == "high"


def test_narrate_comps_empty():
    """All empty sets → status='no_comps'."""
    result = narrate_comps([], [], [])
    assert result["status"] == "no_comps"
    assert result["anchor_comp"] is None
    assert result["exit_ppsf"] is None
    assert result["confidence"] == "none"


def test_comp_model_round_trip():
    """Comp(**result['anchor_comp']) and CompAggregates(**result['comp_set_1_aggregates']) succeed."""
    result = narrate_comps(SET1_ROWS, SET2_ROWS, SET3_ROWS)
    # Should not raise
    anchor = Comp(**result["anchor_comp"])
    assert anchor.address is not None

    agg = CompAggregates(**result["comp_set_1_aggregates"])
    assert agg.count == 3


def test_handle_comp_narrator():
    """Handler returns isError=False with 'ok' status in the response content.

    Async handler exercised via asyncio.run() to avoid a pytest-asyncio dependency.
    """
    import asyncio

    from src.mcp.handlers import MeshState, handle_comp_narrator

    mesh = MeshState()
    response = asyncio.run(
        handle_comp_narrator(
            mesh=mesh,
            set1_rows=SET1_ROWS,
            set2_rows=SET2_ROWS,
            set3_rows=SET3_ROWS,
            sqft_target=1280,
        )
    )
    assert response["isError"] is False
    content_text = response["content"][0]["text"]
    assert "ok" in content_text
