"""Spark MLS ingestion adapter — orchestrates normalize → diff → emit → route.

SparkIngestionAdapter:
  Receives a batch of raw Spark RETS/RESO record dicts, normalizes each into
  a Listing object, diffs against stored state, emits the appropriate
  listing-family EventEnvelopes, and routes each through the TriggerEngine.

InMemoryListingStore:
  In-memory store used for Step 4. Holds the last-seen Listing per listing_key
  and the cumulative reduction_count per listing.
  Production replacement (PostgreSQL) belongs to a future step.

Event emission logic:
  1. listing_key not in store → listing_added
  2. listing_key in store:
     a. list_price decreased → listing_price_reduced (increment reduction_count)
     b. standard_status changed:
        - Always: listing_status_changed
        - If new status == expired: also listing_expired
        - If new status == active AND old status was expired/withdrawn/canceled:
            also listing_relisted
  3. Store is updated AFTER events are built (old state is needed for diffs).

Relist dual-emit contract (Correction 2):
  Both listing_status_changed and listing_relisted are emitted for relist
  transitions. Each is a separate engine.evaluate() call.

reduction_count contract (Correction 4):
  Cumulative tally — increments on price decrease, never resets on price
  increase. Only reset when a new listing_key appears.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.adapters.spark.event_factory import (
    build_listing_added,
    build_listing_expired,
    build_listing_price_reduced,
    build_listing_relisted,
    build_listing_status_changed,
)
from src.adapters.spark.normalizer import SkipRecord, normalize
from src.events.envelope import EventEnvelope
from src.models.enums import StandardStatus
from src.models.listing import Listing
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.result import RoutingResult

logger = logging.getLogger(__name__)

_RELIST_TRIGGER_STATUSES: frozenset[StandardStatus] = frozenset({
    StandardStatus.EXPIRED,
    StandardStatus.WITHDRAWN,
    StandardStatus.CANCELED,
})


class InMemoryListingStore:
    """Ephemeral listing state store for Step 4.

    Holds last-seen Listing and cumulative reduction_count per listing_key.
    Thread-safety is not a concern for the single-process Step 4 proof.
    """

    def __init__(self) -> None:
        self._listings: dict[str, Listing] = {}
        self._reduction_counts: dict[str, int] = {}

    def get(self, listing_key: str) -> Listing | None:
        return self._listings.get(listing_key)

    def put(self, listing: Listing) -> None:
        self._listings[listing.listing_key] = listing

    def get_reduction_count(self, listing_key: str) -> int:
        return self._reduction_counts.get(listing_key, 0)

    def increment_reduction_count(self, listing_key: str) -> int:
        new_count = self._reduction_counts.get(listing_key, 0) + 1
        self._reduction_counts[listing_key] = new_count
        return new_count

    def reset_reduction_count(self, listing_key: str) -> None:
        self._reduction_counts[listing_key] = 0

    def __len__(self) -> int:
        return len(self._listings)


class SparkIngestionAdapter:
    """Processes batches of raw Spark records into Listing objects and routes events.

    Usage:
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=ctx, store=store)
        results = adapter.process_batch(raw_records)
    """

    def __init__(
        self,
        engine: TriggerEngine,
        context: TriggerContext | None = None,
        store: InMemoryListingStore | None = None,
    ) -> None:
        self._engine = engine
        self._context = context if context is not None else TriggerContext()
        self._store = store if store is not None else InMemoryListingStore()

    @property
    def store(self) -> InMemoryListingStore:
        return self._store

    def process_batch(
        self,
        raw_records: list[dict],
        now: datetime | None = None,
    ) -> list[RoutingResult]:
        """Normalize, diff, emit, and route a batch of raw Spark records.

        Args:
            raw_records: List of raw RESO field dicts from the Spark feed.
            now:         Timestamp to use for all events in this batch.
                         Defaults to UTC now. Pass a fixed value for deterministic tests.

        Returns:
            List of RoutingResult objects — one per emitted event, in emission order.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        results: list[RoutingResult] = []

        for record in raw_records:
            try:
                new_listing = normalize(record, now=now)
            except SkipRecord as exc:
                logger.debug("SkipRecord: %s", exc)
                continue

            events = self._diff_and_build_events(new_listing, now)

            # Update store AFTER building events so old state is preserved for diff.
            self._store.put(new_listing)

            for event in events:
                result = self._engine.evaluate(event, self._context)
                results.append(result)

        return results

    # ── Private helpers ────────────────────────────────────────────────

    def _diff_and_build_events(
        self,
        new: Listing,
        now: datetime,
    ) -> list[EventEnvelope]:
        old = self._store.get(new.listing_key)
        events: list[EventEnvelope] = []

        if old is None:
            # New listing — reset (initialize) reduction count
            self._store.reset_reduction_count(new.listing_key)
            events.append(build_listing_added(new, now=now))
            return events

        # ── Price diff ─────────────────────────────────────────────────
        if new.list_price < old.list_price:
            new_count = self._store.increment_reduction_count(new.listing_key)
            events.append(
                build_listing_price_reduced(old, new, new_count, now=now)
            )

        # ── Status diff ────────────────────────────────────────────────
        if new.standard_status != old.standard_status:
            # Generic status event — always emitted on any status change
            events.append(build_listing_status_changed(old, new, now=now))

            # Elevated expiry event
            if new.standard_status == StandardStatus.EXPIRED:
                events.append(build_listing_expired(old, new, now=now))

            # Relist: previous status was a terminal/inactive state
            if (
                new.standard_status == StandardStatus.ACTIVE
                and old.standard_status in _RELIST_TRIGGER_STATUSES
            ):
                events.append(build_listing_relisted(old, new, now=now))

        return events
