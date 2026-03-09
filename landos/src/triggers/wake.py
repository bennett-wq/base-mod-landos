"""WakeInstruction — what the trigger engine dispatches to an agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.events.envelope import EntityRefs
from src.events.enums import RoutingClass
from src.triggers.enums import WakeType


@dataclass
class WakeInstruction:
    """Instruction produced when a trigger rule fires.

    The engine constructs one WakeInstruction per fired rule per event.
    generation_depth is always source_event.generation_depth + 1.
    causal_chain_id is inherited from the source event or assigned fresh.
    created_at is supplied by the engine from context.current_timestamp —
    no wall-clock calls inside this class.
    """

    rule_id: str
    source_event_id: UUID
    wake_target: str
    wake_type: WakeType
    priority: int
    routing_class: RoutingClass
    entity_refs: EntityRefs
    generation_depth: int
    causal_chain_id: UUID
    created_at: datetime                         # provided by TriggerEngine from context.current_timestamp
    context: dict[str, Any] = field(default_factory=dict)
    instruction_id: UUID = field(default_factory=uuid4)  # auto-generated, not time-dependent
