"""Engine envelope — pure-math parcel buildable envelope computation.

Spec §6 pricing.py. Implementation notes from spec §9 item 2 (canonical
Regrid GeoPackage techniques):
  - WKB column is wkb_geometry (not geom)
  - GPKG header is 8 bytes + variable envelope prefix — strip before parsing
  - Project to local meters via 111320 × cos(lat) for longitude scaling
  - Use shapely.minimum_rotated_rectangle, NOT axis-aligned bbox
    (parcels are not cardinally oriented)
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from shapely import wkb
from shapely.geometry import Polygon
from shapely.affinity import rotate

from src.models.opportunity import SetbackRules


@dataclass
class EnvelopeResult:
    buildable_width_ft: float
    buildable_depth_ft: float
    envelope_area_sf: float
    coverage_cap_sf: float
    binding_constraint: str  # "width" | "depth" | "coverage"


def _strip_gpkg_header(gpkg_wkb: bytes) -> bytes:
    """GPKG WKB format: 8-byte magic/flags header + optional envelope + raw WKB.
    Returns the raw WKB portion.
    """
    assert len(gpkg_wkb) >= 8, "Not a valid GPKG WKB blob"
    flags = gpkg_wkb[3]
    envelope_type = (flags >> 1) & 0x07  # bits 1-3
    envelope_sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
    envelope_size = envelope_sizes.get(envelope_type, 0)
    return gpkg_wkb[8 + envelope_size:]


def _meters_per_degree(lat: float) -> tuple[float, float]:
    """Return (meters_per_degree_lat, meters_per_degree_lon) at given latitude."""
    m_per_deg_lat = 111_132.92 - 559.82 * math.cos(2 * math.radians(lat))
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat))
    return m_per_deg_lat, m_per_deg_lon


def compute_envelope(
    polygon_wkb: bytes,
    setbacks: SetbackRules,
    lat: float,
) -> EnvelopeResult:
    """Parcel polygon + zoning rules → (buildable width/depth, envelope area, cov cap).

    Spec §6 envelope.py. Uses shapely.minimum_rotated_rectangle to get
    the true (non-axis-aligned) parcel bounds, subtracts front/rear/side
    setbacks, then caps by max_coverage_pct × total area.
    """
    raw_wkb = _strip_gpkg_header(polygon_wkb)
    geom = wkb.loads(raw_wkb)

    # Project to local meters (longitude compressed by cos(lat))
    m_per_deg_lat, m_per_deg_lon = _meters_per_degree(lat)
    ref_lon, ref_lat = geom.centroid.x, geom.centroid.y

    def project(x: float, y: float) -> tuple[float, float]:
        return ((x - ref_lon) * m_per_deg_lon, (y - ref_lat) * m_per_deg_lat)

    projected = Polygon([project(x, y) for x, y in geom.exterior.coords])

    # Minimum rotated rectangle — the true parcel bounds
    mrr = projected.minimum_rotated_rectangle

    # Extract width and depth from the MRR coordinates
    coords = list(mrr.exterior.coords)[:-1]
    edges = [
        math.hypot(coords[(i + 1) % 4][0] - coords[i][0], coords[(i + 1) % 4][1] - coords[i][1])
        for i in range(4)
    ]
    width_m = min(edges[0], edges[1])
    depth_m = max(edges[0], edges[1])

    # Convert meters → feet
    M_TO_FT = 3.28084
    true_width_ft = width_m * M_TO_FT
    true_depth_ft = depth_m * M_TO_FT
    lot_area_sf = projected.area * M_TO_FT * M_TO_FT

    # Subtract setbacks
    buildable_width = max(0.0, true_width_ft - setbacks.side_total_ft)
    buildable_depth = max(0.0, true_depth_ft - setbacks.front_setback_ft - setbacks.rear_setback_ft)
    envelope_area = buildable_width * buildable_depth
    coverage_cap = lot_area_sf * (setbacks.max_coverage_pct / 100.0)

    # Binding constraint: which limit hits first?
    if coverage_cap < envelope_area:
        binding = "coverage"
        effective_area = coverage_cap
    elif buildable_depth <= 0 or buildable_depth < buildable_width:
        binding = "depth"
        effective_area = envelope_area
    else:
        binding = "width"
        effective_area = envelope_area

    return EnvelopeResult(
        buildable_width_ft=round(buildable_width, 1),
        buildable_depth_ft=round(buildable_depth, 1),
        envelope_area_sf=round(envelope_area, 1),
        coverage_cap_sf=round(coverage_cap, 1),
        binding_constraint=binding,
    )
