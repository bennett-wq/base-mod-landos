"""InMemory stores for Subdivision and Opportunity objects.

Rules:
  - Always use `is not None` checks when reading from store, never `or`.
  - No DB code. No side effects beyond in-memory state.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.models.development import Subdivision
from src.models.opportunity import Opportunity


class InMemorySubdivisionStore:
    def __init__(self) -> None:
        self._subdivisions: dict[UUID, Subdivision] = {}

    def save(self, subdivision: Subdivision) -> None:
        """Insert or replace a Subdivision by its subdivision_id."""
        self._subdivisions[subdivision.subdivision_id] = subdivision

    def get(self, subdivision_id: UUID) -> Optional[Subdivision]:
        """Return Subdivision by ID, or None if not present."""
        return self._subdivisions.get(subdivision_id)

    def get_by_municipality(self, municipality_id: UUID) -> list[Subdivision]:
        """Return all Subdivisions for a given municipality."""
        return [
            s for s in self._subdivisions.values()
            if s.municipality_id == municipality_id
        ]

    def all(self) -> list[Subdivision]:
        """Return all stored Subdivisions."""
        return list(self._subdivisions.values())

    def __len__(self) -> int:
        return len(self._subdivisions)


class InMemoryOpportunityStore:
    def __init__(self) -> None:
        self._opportunities: dict[UUID, Opportunity] = {}

    def save(self, opportunity: Opportunity) -> None:
        """Insert or replace an Opportunity by its opportunity_id."""
        self._opportunities[opportunity.opportunity_id] = opportunity

    def get(self, opportunity_id: UUID) -> Optional[Opportunity]:
        """Return Opportunity by ID, or None if not present."""
        return self._opportunities.get(opportunity_id)

    def get_by_subdivision(self, subdivision_id: UUID) -> list[Opportunity]:
        """Return all Opportunities for a given subdivision."""
        return [
            o for o in self._opportunities.values()
            if o.subdivision_id is not None and o.subdivision_id == subdivision_id
        ]

    def get_by_municipality(self, municipality_id: UUID) -> list[Opportunity]:
        """Return all Opportunities for a given municipality."""
        return [
            o for o in self._opportunities.values()
            if o.municipality_id == municipality_id
        ]

    def all(self) -> list[Opportunity]:
        """Return all stored Opportunities."""
        return list(self._opportunities.values())

    def __len__(self) -> int:
        return len(self._opportunities)
