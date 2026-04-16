"""Land bank hunter — scheduled adapter for non-MLS inventory.

Spec §4.7. Parallel scanner for county land banks, tax-foreclosure auctions,
and municipality surplus property disposals. These don't have MLS listings but
they have parcel numbers, so Regrid + zoning pipeline still works.

Invoked by the orchestrator (M2-10) on a scheduled basis, or triggered when
ingest-municipality surfaces a Class B municipal surplus disposal list. Returns
discovered parcels; the orchestrator emits one ``parcel.discovered`` event per
parcel with ``source="land-bank"``.

──────────────────────────────────────────────────────────────────────
Return shape (STABLE CONTRACT with orchestrator — spec §4.7)
──────────────────────────────────────────────────────────────────────
Every return path emits the SAME top-level keys. The orchestrator routes
on ``status``; only the companion fields change.

Top-level keys (ALWAYS present):
  status            : "ok" | "no_source_configured" | "error"
  discovered_parcels: list[dict]  (empty on non-ok paths)
  state             : str          (echoed from input)
  county            : str          (echoed from input)
  sources_queried   : list[str]    (names of sources that were queried)
  warning           : str | None   (set on ok+empty results, None otherwise)
  reason            : str | None   (set on no_source_configured/error, None on ok)

Each discovered parcel dict keys (ALWAYS present):
  source            : str   (e.g. "Genesee County Land Bank")
  source_type       : str   ("land_bank" | "tax_foreclosure" | "municipal_surplus")
  parcel_number     : str | None
  address           : str | None
  price             : float | None  (side lot fee or auction minimum bid)
  price_type        : str   ("side_lot_fee" | "auction_minimum" | "surplus_list_price")
  auction_date      : str | None  (ISO date if applicable)
  acreage           : float | None
  zoning            : str | None
  municipality      : str | None

M2 scope: stub adapters only. Live web scraping is M3 scope.

EnvironmentError (future: missing auth credentials for live scraping) is NOT
caught here — it bubbles up to ``handle_land_bank_hunter`` in
src/mcp/handlers.py, which wraps it in an _err response (spec Finding #2).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# ── Output-shape contract ─────────────────────────────────────────────────

# Canonical key list. Every return path MUST produce exactly these keys.
# The parametrized test ``test_land_bank_hunter_output_shape_is_stable``
# enforces this invariant against the orchestrator contract.
_OUTPUT_KEYS: frozenset[str] = frozenset(
    {
        "status",
        "discovered_parcels",
        "state",
        "county",
        "sources_queried",
        "warning",
        "reason",
    }
)

# Canonical key list for each parcel dict. Every parcel emitted by any adapter
# MUST include exactly these keys (None where data is unavailable).
_PARCEL_KEYS: frozenset[str] = frozenset(
    {
        "source",
        "source_type",
        "parcel_number",
        "address",
        "price",
        "price_type",
        "auction_date",
        "acreage",
        "zoning",
        "municipality",
    }
)


def _envelope(
    *,
    status: str,
    state: str,
    county: str,
    sources_queried: list[str] | None = None,
    discovered_parcels: list[dict] | None = None,
    warning: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Build the stable-shape return dict.

    Centralising construction here guarantees every call site produces
    exactly ``_OUTPUT_KEYS`` — no accidental drift.
    """
    return {
        "status": status,
        "discovered_parcels": list(discovered_parcels) if discovered_parcels else [],
        "state": state,
        "county": county,
        "sources_queried": list(sources_queried) if sources_queried else [],
        "warning": warning,
        "reason": reason,
    }


def _parcel(
    *,
    source: str,
    source_type: str,
    parcel_number: str | None = None,
    address: str | None = None,
    price: float | None = None,
    price_type: str = "side_lot_fee",
    auction_date: str | None = None,
    acreage: float | None = None,
    zoning: str | None = None,
    municipality: str | None = None,
) -> dict[str, Any]:
    """Build a single parcel dict with the canonical stable shape."""
    return {
        "source": source,
        "source_type": source_type,
        "parcel_number": parcel_number,
        "address": address,
        "price": price,
        "price_type": price_type,
        "auction_date": auction_date,
        "acreage": acreage,
        "zoning": zoning,
        "municipality": municipality,
    }


# ── Source registry types ─────────────────────────────────────────────────

# Adapter callable type: () -> list[dict[str, Any]]
# Each adapter returns a list of parcel dicts (built with _parcel()).
AdapterFn = Callable[[], list[dict[str, Any]]]


@dataclass
class LandBankSource:
    """Registry entry for a single land bank / tax-foreclosure / surplus source."""

    name: str
    source_type: str  # "land_bank" | "tax_foreclosure" | "municipal_surplus"
    county: str
    state: str
    adapter: AdapterFn


# ── Stub adapters (M2 scope) ──────────────────────────────────────────────
# Each stub returns 2–3 realistic sample parcels from publicly known
# Michigan land bank inventories. Live web scraping is M3 scope.


def _genesee_county_land_bank_stub() -> list[dict[str, Any]]:
    """Genesee County Land Bank — side lot program ($500–$1,000 per lot).

    Largest Michigan land bank; thousands of parcels, many vacant.
    Side lot program allows adjacent owners to purchase vacant side lots.
    Source (M3): https://www.thelandbank.org/inventory.asp
    """
    return [
        _parcel(
            source="Genesee County Land Bank",
            source_type="land_bank",
            parcel_number="10-35-576-028",
            address="802 Welch Blvd, Flint, MI 48504",
            price=500.0,
            price_type="side_lot_fee",
            auction_date=None,
            acreage=0.11,
            zoning="R-1",
            municipality="Flint",
        ),
        _parcel(
            source="Genesee County Land Bank",
            source_type="land_bank",
            parcel_number="10-30-405-012",
            address="1414 Missouri Ave, Flint, MI 48505",
            price=1000.0,
            price_type="side_lot_fee",
            auction_date=None,
            acreage=0.14,
            zoning="R-2",
            municipality="Flint",
        ),
    ]


def _wayne_county_land_bank_stub() -> list[dict[str, Any]]:
    """Wayne County Land Bank — Detroit-area auction lots ($1,000–$5,000).

    Annual auction of tax-foreclosed vacant lots; bidding starts at minimum.
    Source (M3): https://www.waynecounty.com/elected/treasurer/tax-foreclosure.aspx
    """
    return [
        _parcel(
            source="Wayne County Land Bank",
            source_type="land_bank",
            parcel_number="44001050632000",
            address="15230 Schoolcraft, Detroit, MI 48227",
            price=1000.0,
            price_type="auction_minimum",
            auction_date="2026-06-15",
            acreage=0.09,
            zoning="R-1",
            municipality="Detroit",
        ),
        _parcel(
            source="Wayne County Land Bank",
            source_type="land_bank",
            parcel_number="44001050633000",
            address="15234 Schoolcraft, Detroit, MI 48227",
            price=1500.0,
            price_type="auction_minimum",
            auction_date="2026-06-15",
            acreage=0.09,
            zoning="R-1",
            municipality="Detroit",
        ),
    ]


def _washtenaw_county_tax_foreclosure_stub() -> list[dict[str, Any]]:
    """Washtenaw County tax-foreclosure auction — annual ($2,000–$5,000).

    County Treasurer conducts annual auction of tax-reverted parcels.
    Source (M3): https://www.washtenaw.org/1095/Delinquent-Tax-Foreclosure
    """
    return [
        _parcel(
            source="Washtenaw County Tax Foreclosure",
            source_type="tax_foreclosure",
            parcel_number="J-11-09-300-021",
            address="1500 Holmes Rd, Ypsilanti, MI 48198",
            price=3500.0,
            price_type="auction_minimum",
            auction_date="2026-09-01",
            acreage=0.25,
            zoning="R-5",
            municipality="Ypsilanti Township",
        ),
        _parcel(
            source="Washtenaw County Tax Foreclosure",
            source_type="tax_foreclosure",
            parcel_number="J-11-09-300-022",
            address="1504 Holmes Rd, Ypsilanti, MI 48198",
            price=2500.0,
            price_type="auction_minimum",
            auction_date="2026-09-01",
            acreage=0.20,
            zoning="R-5",
            municipality="Ypsilanti Township",
        ),
    ]


# ── Source registry ───────────────────────────────────────────────────────
# Keyed by (state, county) — lowercase, stripped.
# Multiple sources per county are supported (Washtenaw has both
# tax-foreclosure and potentially municipal surplus in future iterations).

_LAND_BANK_SOURCES: dict[tuple[str, str], list[LandBankSource]] = {
    ("mi", "genesee"): [
        LandBankSource(
            name="Genesee County Land Bank",
            source_type="land_bank",
            county="Genesee",
            state="MI",
            adapter=_genesee_county_land_bank_stub,
        ),
    ],
    ("mi", "wayne"): [
        LandBankSource(
            name="Wayne County Land Bank",
            source_type="land_bank",
            county="Wayne",
            state="MI",
            adapter=_wayne_county_land_bank_stub,
        ),
    ],
    ("mi", "washtenaw"): [
        LandBankSource(
            name="Washtenaw County Tax Foreclosure",
            source_type="tax_foreclosure",
            county="Washtenaw",
            state="MI",
            adapter=_washtenaw_county_tax_foreclosure_stub,
        ),
    ],
}


def _registry_key(state: str, county: str) -> tuple[str, str]:
    """Normalize (state, county) to the registry lookup key."""
    return (state.strip().lower(), county.strip().lower())


def _lookup_sources(state: str, county: str) -> list[LandBankSource]:
    """Return all configured sources for the given (state, county) pair."""
    return _LAND_BANK_SOURCES.get(_registry_key(state, county), [])


# ── Main entry point ──────────────────────────────────────────────────────


def hunt_land_banks(*, state: str, county: str) -> dict[str, Any]:
    """Query all configured land bank sources for a state/county pair.

    Args:
        state: Two-letter state abbreviation (e.g. "MI"). Case-insensitive.
        county: County name (e.g. "Washtenaw"). Case-insensitive.

    Returns:
        The envelope dict described in the module docstring. Every return
        path emits the same top-level keys (``_OUTPUT_KEYS``).

    Raises:
        EnvironmentError: Propagated from adapters when live credentials are
            unset (M3 scope). Caught by the MCP handler, NOT here (Finding #2).
    """
    sources = _lookup_sources(state, county)

    # ── No source configured ──────────────────────────────────────────────
    if not sources:
        return _envelope(
            status="no_source_configured",
            state=state,
            county=county,
            sources_queried=[],
            reason=(
                f"No land bank source configured for {county} County, {state}. "
                "Add a LandBankSource entry to _LAND_BANK_SOURCES to enable scanning."
            ),
        )

    # ── Query all sources ─────────────────────────────────────────────────
    all_parcels: list[dict] = []
    queried_names: list[str] = []

    for source in sources:
        queried_names.append(source.name)
        # EnvironmentError from live adapters (M3) bubbles up to the handler
        parcels = source.adapter()
        all_parcels.extend(parcels)

    # ── Zero-result gap surfacing ─────────────────────────────────────────
    # Unlikely with stubs but required for spec completeness and future
    # live adapters that may return empty inventories.
    if not all_parcels:
        return _envelope(
            status="ok",
            state=state,
            county=county,
            sources_queried=queried_names,
            discovered_parcels=[],
            warning="no_parcels_in_inventory",
        )

    return _envelope(
        status="ok",
        state=state,
        county=county,
        sources_queried=queried_names,
        discovered_parcels=all_parcels,
    )
