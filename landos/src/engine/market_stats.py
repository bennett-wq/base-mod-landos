"""Engine market_stats — absorption, CDOM distribution, failed-listing history."""

from __future__ import annotations

from statistics import median as _median

from src.models.opportunity import MarketStats


def months_of_inventory(active_count: int, closed_last_30d: int) -> float:
    """Months to clear active inventory at current sales run-rate.

    Spec §6 market_stats.py. McCartney 48198 land = 22 months (deep buyer's market).
    """
    if closed_last_30d == 0:
        return float("inf")
    monthly_rate = closed_last_30d  # 30 days is one month
    moi = active_count / monthly_rate
    return round(moi, 1)


def cdom_distribution(cdoms: list[int]) -> tuple[int, int, int]:
    """Return (median_cdom, p75_cdom, p90_cdom)."""
    if not cdoms:
        return 0, 0, 0
    sorted_cdoms = sorted(cdoms)
    n = len(sorted_cdoms)
    median = int(_median(sorted_cdoms))
    p75 = sorted_cdoms[int(n * 0.75)] if n > 3 else sorted_cdoms[-1]
    p90 = sorted_cdoms[int(n * 0.90)] if n > 9 else sorted_cdoms[-1]
    return median, p75, p90


def failed_listings_on_parcel(listing_history: list[dict]) -> tuple[int, float]:
    """Return (relist_count, years_listed_total) from raw listing-history rows.

    McCartney = (multiple relists, 14.0 years).
    """
    if not listing_history:
        return 0, 0.0
    relists = len([l for l in listing_history if l.get("status") in ("Expired", "Withdrawn", "Canceled")])
    first = min(l["list_date"] for l in listing_history)
    last = max(l.get("close_date") or l.get("off_market_date") or l["list_date"] for l in listing_history)
    from datetime import date
    if isinstance(first, str):
        first = date.fromisoformat(first)
        last = date.fromisoformat(last)
    years = (last - first).days / 365.25
    return relists, round(years, 1)


def compile_market_stats(
    active_count: int,
    closed_last_30d: int,
    active_cdoms: list[int],
    parcel_listing_history: list[dict],
) -> MarketStats:
    """Wrap the three functions into a single MarketStats object for
    OpportunityUnderwriting.market_stats.
    """
    moi = months_of_inventory(active_count, closed_last_30d)
    median, p75, p90 = cdom_distribution(active_cdoms)
    relists, years = failed_listings_on_parcel(parcel_listing_history)

    if moi >= 18.0:
        health = "deep_buyer"
    elif moi >= 9.0:
        health = "balanced"
    elif moi >= 4.0:
        health = "soft"
    elif moi >= 1.0:
        health = "hot"
    else:
        health = "frozen"

    return MarketStats(
        months_of_inventory=moi,
        median_cdom_days=median,
        p75_cdom_days=p75,
        p90_cdom_days=p90,
        failed_listings_on_parcel=relists,
        years_listed_total=years,
        market_health=health,
    )
