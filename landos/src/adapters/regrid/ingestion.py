"""Regrid parcel ingestion adapter — orchestrates normalize → link → score → emit → route.

RegridIngestionAdapter:
  Receives a batch of raw Regrid bulk-export record dicts, normalizes each
  into a Parcel object, attempts parcel-to-listing linkage, resolves the
  owner, scores the parcel, emits the appropriate parcel-state EventEnvelopes,
  and routes each through the TriggerEngine.

InMemoryParcelStore:
  In-memory store used for Step 5. Holds the last-seen Parcel per regrid_id
  and the current opportunity score per parcel_id.
  Production replacement (PostgreSQL + PostGIS) belongs to a future step.

InMemoryOwnerStore:
  In-memory owner name → Owner UUID registry used for Phase 1 name-based
  owner resolution. Normalized owner name → owner_id mapping.
  Entity resolution (LLC graphs, trust beneficiaries) is deferred.

Event emission logic per record:
  1. Normalize raw record → Parcel (SkipRecord on failure)
  2. Attempt linkage via ParcelListingLinker → emit parcel_linked_to_listing if matched
  3. If owner_name_raw is non-null → resolve/create Owner → emit parcel_owner_resolved
  4. Compute opportunity score → if abs(new - old) >= SCORE_MATERIALITY_THRESHOLD:
       emit parcel_score_updated
  5. Route each event through TriggerEngine independently.

Score materiality gate (per trigger matrix):
  parcel_score_updated is only emitted when abs(score_delta) >= 0.05.
  First-time score (old_score = None) always clears the gate.

Phase 1 scoring model (v0.1_phase1_basic):
  Simple composite of three binary signals:
    acreage_signal    = min(parcel.acreage / 5.0, 1.0) * 0.4
    vacancy_signal    = 0.4 if vacancy_status == VACANT else 0.0
    linkage_signal    = 0.2 if parcel was linked to a listing else 0.0
  Score range: 0.0 – 1.0. Version string: "v0.1_phase1_basic".
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.adapters.regrid.event_factory import (
    build_parcel_linked_to_listing,
    build_parcel_owner_resolved,
    build_parcel_score_updated,
)
from src.adapters.regrid.linker import ParcelListingLinker
from src.adapters.regrid.normalizer import SkipRecord, normalize
from src.events.envelope import EventEnvelope
from src.models.enums import VacancyStatus
from src.models.listing import Listing
from src.models.parcel import Parcel
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.result import RoutingResult

logger = logging.getLogger(__name__)

SCORE_MATERIALITY_THRESHOLD: float = 0.05
SCORE_VERSION: str = "v0.1_phase1_basic"


class InMemoryParcelStore:
    """Ephemeral parcel state store for Step 5.

    Keyed on regrid_id (Regrid's stable UUID string).
    Tracks last-seen Parcel and current opportunity score per parcel_id.
    """

    def __init__(self) -> None:
        self._parcels: dict[str, Parcel] = {}       # regrid_id → Parcel
        self._scores: dict[UUID, float] = {}         # parcel_id → current score

    def get_by_regrid_id(self, regrid_id: str) -> Parcel | None:
        return self._parcels.get(regrid_id)

    def put(self, parcel: Parcel) -> None:
        regrid_id = parcel.source_system_ids.get("regrid_id")
        if regrid_id:
            self._parcels[regrid_id] = parcel

    def get_score(self, parcel_id: UUID) -> float | None:
        return self._scores.get(parcel_id)

    def put_score(self, parcel_id: UUID, score: float) -> None:
        self._scores[parcel_id] = score

    def __len__(self) -> int:
        return len(self._parcels)


class InMemoryOwnerStore:
    """Ephemeral owner name → UUID store for Phase 1 name-based resolution.

    Normalized owner name is the key. First time a name is seen, a new UUID
    is assigned. Subsequent records with the same name get the same UUID.
    Entity resolution (LLC graphs, trust beneficiaries) is deferred.
    """

    def __init__(self) -> None:
        self._owners: dict[str, UUID] = {}  # normalized_name → owner_id

    def resolve(self, owner_name_raw: str) -> UUID:
        """Return existing owner_id for this name, or create a new one."""
        key = _normalize_owner_name(owner_name_raw)
        if key not in self._owners:
            self._owners[key] = uuid4()
        return self._owners[key]

    def __len__(self) -> int:
        return len(self._owners)


class RegridIngestionAdapter:
    """Processes batches of raw Regrid records into Parcel objects and routes events.

    Usage:
        parcel_store = InMemoryParcelStore()
        owner_store = InMemoryOwnerStore()
        adapter = RegridIngestionAdapter(
            engine=engine,
            listings=listings,
            context=ctx,
            parcel_store=parcel_store,
            owner_store=owner_store,
        )
        results = adapter.process_batch(raw_records)
    """

    def __init__(
        self,
        engine: TriggerEngine,
        listings: list[Listing] | None = None,
        context: TriggerContext | None = None,
        parcel_store: InMemoryParcelStore | None = None,
        owner_store: InMemoryOwnerStore | None = None,
        default_municipality_id: UUID | None = None,
        municipality_lookup: dict[str, UUID] | None = None,
    ) -> None:
        self._engine = engine
        self._listings = listings or []
        self._context = context if context is not None else TriggerContext()
        self._parcel_store = parcel_store if parcel_store is not None else InMemoryParcelStore()
        self._owner_store = owner_store if owner_store is not None else InMemoryOwnerStore()
        self._default_municipality_id = default_municipality_id
        self._municipality_lookup = municipality_lookup

    @property
    def parcel_store(self) -> InMemoryParcelStore:
        return self._parcel_store

    @property
    def owner_store(self) -> InMemoryOwnerStore:
        return self._owner_store

    def process_batch(
        self,
        raw_records: list[dict],
        now: datetime | None = None,
    ) -> list[RoutingResult]:
        """Normalize, link, score, emit, and route a batch of raw Regrid records.

        Args:
            raw_records: List of raw Regrid bulk-export field dicts.
            now:         Timestamp for all events in this batch.
                         Defaults to UTC now. Pass a fixed value for deterministic tests.

        Returns:
            List of RoutingResult objects — one per emitted event, in emission order.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        linker = ParcelListingLinker(self._listings)
        results: list[RoutingResult] = []

        for record in raw_records:
            try:
                parcel = normalize(
                    record,
                    default_municipality_id=self._default_municipality_id,
                    municipality_lookup=self._municipality_lookup,
                    now=now,
                )
            except SkipRecord as exc:
                logger.debug("SkipRecord: %s", exc)
                continue

            regrid_id = parcel.source_system_ids.get("regrid_id", "")
            existing = self._parcel_store.get_by_regrid_id(regrid_id)
            if existing is not None:
                # Already ingested — skip to avoid duplicate events
                logger.debug("Parcel already in store, skipping: %s", regrid_id)
                continue

            events = self._build_events(parcel, linker, now)

            # Store AFTER building events so old state is available if needed
            self._parcel_store.put(parcel)

            for event in events:
                result = self._engine.evaluate(event, self._context)
                results.append(result)

        return results

    # ── Private helpers ────────────────────────────────────────────────

    def _build_events(
        self,
        parcel: Parcel,
        linker: ParcelListingLinker,
        now: datetime,
    ) -> list[EventEnvelope]:
        events: list[EventEnvelope] = []
        linked = False

        # ── Linkage ────────────────────────────────────────────────────
        match = linker.find_match(parcel)
        if match:
            linked = True
            events.append(
                build_parcel_linked_to_listing(
                    parcel=parcel,
                    listing_id=match.listing.listing_id,
                    linkage_method=match.method,
                    now=now,
                )
            )

        # ── Owner resolution ───────────────────────────────────────────
        if parcel.owner_name_raw:
            owner_id = self._owner_store.resolve(parcel.owner_name_raw)
            events.append(
                build_parcel_owner_resolved(
                    parcel=parcel,
                    owner_id=owner_id,
                    resolution_method="county_records",
                    now=now,
                )
            )

        # ── Scoring ────────────────────────────────────────────────────
        new_score = _compute_score(parcel, linked=linked)
        old_score = self._parcel_store.get_score(parcel.parcel_id)
        score_delta = abs(new_score - (old_score or 0.0))

        if old_score is None or score_delta >= SCORE_MATERIALITY_THRESHOLD:
            self._parcel_store.put_score(parcel.parcel_id, new_score)
            events.append(
                build_parcel_score_updated(
                    parcel=parcel,
                    old_score=old_score,
                    new_score=new_score,
                    trigger_reason=SCORE_VERSION,
                    now=now,
                )
            )

        return events


# ── Scoring model ──────────────────────────────────────────────────────────

def _compute_score(parcel: Parcel, linked: bool) -> float:
    """Phase 1 basic composite score (v0.1_phase1_basic).

    Components:
      acreage_signal  = min(acreage / 5.0, 1.0) * 0.4   (capped at 5 acres = full)
      vacancy_signal  = 0.4 if VACANT else 0.0
      linkage_signal  = 0.2 if linked to a listing else 0.0

    Range: 0.0 – 1.0.
    """
    acreage_signal = min(parcel.acreage / 5.0, 1.0) * 0.4
    vacancy_signal = 0.4 if parcel.vacancy_status == VacancyStatus.VACANT else 0.0
    linkage_signal = 0.2 if linked else 0.0
    return round(acreage_signal + vacancy_signal + linkage_signal, 6)


# ── Owner name normalizer ──────────────────────────────────────────────────

def _normalize_owner_name(raw: str) -> str:
    """Lowercase, strip extra whitespace for owner dedup key."""
    return " ".join(raw.lower().split())
