"""InMemoryClusterStore — keyed on cluster_id (UUID).

Rules:
  - Always use `is not None` checks when reading from store, never `or`.
  - Upsert is a true logical upsert: same cluster_id replaces prior entry.
  - No DB code. No side effects beyond in-memory state.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.models.owner import OwnerCluster


class InMemoryClusterStore:
    def __init__(self) -> None:
        self._clusters: dict[UUID, OwnerCluster] = {}

    def upsert(self, cluster: OwnerCluster) -> None:
        """Insert or replace a cluster by its cluster_id."""
        self._clusters[cluster.cluster_id] = cluster

    def get(self, cluster_id: UUID) -> Optional[OwnerCluster]:
        """Return cluster by ID, or None if not present."""
        return self._clusters.get(cluster_id)

    def all(self) -> list[OwnerCluster]:
        """Return all stored clusters."""
        return list(self._clusters.values())

    def __len__(self) -> int:
        return len(self._clusters)
