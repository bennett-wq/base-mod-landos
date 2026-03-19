"""InMemoryMunicipalEventStore — keyed on municipal_event_id (UUID).

Rules:
  - Always use `is not None` checks when reading from store, never `or`.
  - No DB code. No side effects beyond in-memory state.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.models.enums import MunicipalEventType
from src.models.municipality import MunicipalEvent


class InMemoryMunicipalEventStore:
    def __init__(self) -> None:
        self._events: dict[UUID, MunicipalEvent] = {}

    def save(self, municipal_event: MunicipalEvent) -> None:
        """Insert or replace a MunicipalEvent by its municipal_event_id."""
        self._events[municipal_event.municipal_event_id] = municipal_event

    def get(self, municipal_event_id: UUID) -> Optional[MunicipalEvent]:
        """Return MunicipalEvent by ID, or None if not present."""
        return self._events.get(municipal_event_id)

    def get_by_municipality(self, municipality_id: UUID) -> list[MunicipalEvent]:
        """Return all MunicipalEvents for a given municipality."""
        return [
            me for me in self._events.values()
            if me.municipality_id == municipality_id
        ]

    def get_by_type(
        self,
        municipality_id: UUID,
        event_type: MunicipalEventType,
    ) -> list[MunicipalEvent]:
        """Return MunicipalEvents of a specific type for a municipality."""
        return [
            me for me in self._events.values()
            if me.municipality_id == municipality_id
            and me.event_type == event_type
        ]

    def all(self) -> list[MunicipalEvent]:
        """Return all stored MunicipalEvents."""
        return list(self._events.values())

    def __len__(self) -> int:
        return len(self._events)
