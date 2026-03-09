"""AgentRun and Action system object models.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import ActionStatus, AgentRunStatus


class AgentRun(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    agent_run_id: UUID = Field(default_factory=uuid4)
    agent_type: str
    started_at: datetime
    status: AgentRunStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    triggered_by_event_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    input_entity_refs: Optional[dict[str, Any]] = None
    output_event_ids: Optional[list[UUID]] = None
    output_object_ids: Optional[list[UUID]] = None
    error_message: Optional[str] = None
    generation_depth: Optional[int] = None


class Action(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    action_id: UUID = Field(default_factory=uuid4)
    action_type: str
    status: ActionStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    assigned_to: Optional[str] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[UUID] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
