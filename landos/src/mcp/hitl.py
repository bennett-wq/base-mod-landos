"""Human-in-the-loop orchestrator for LandOS agent workflows.

Separates INVESTIGATION (read-only diagnosis) from REMEDIATION (write actions)
as distinct phases with human review in between — the key safety pattern from
the SRE cookbook adapted for the LandOS event mesh.

Architecture:
    Phase 1: INVESTIGATION  — agent uses read-only tools to analyze mesh state
    ─── human reviews findings ───
    Phase 2: REMEDIATION    — agent uses mutation tools to ingest/detect/create

The orchestrator:
  1. Enforces tool access by phase (investigation vs remediation)
  2. Validates mutation tool calls against safety hooks
  3. Produces structured investigation reports for human review
  4. Logs all actions to an audit trail

Usage with Claude Agent SDK:
    from src.mcp.hitl import LandOSOrchestrator, WorkflowPhase

    orch = LandOSOrchestrator()

    # Phase 1: Investigation
    options = orch.build_agent_options(WorkflowPhase.INVESTIGATION)
    async for msg in query(prompt=investigate_prompt, options=options):
        ...

    # Human reviews investigation report
    report = orch.get_investigation_report()

    # Phase 2: Remediation (after human approval)
    orch.approve_remediation(approved_actions=["ingest_spark_batch"])
    options = orch.build_agent_options(WorkflowPhase.REMEDIATION)
    async for msg in query(prompt=remediate_prompt, options=options):
        ...
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.mcp.handlers import MeshState
from src.mcp.tools import (
    INVESTIGATION_TOOLS,
    MUTATION_TOOL_NAMES,
    MUTATION_TOOLS,
)


class WorkflowPhase(str, Enum):
    """Agent workflow phases with distinct tool access."""
    INVESTIGATION = "investigation"
    REMEDIATION = "remediation"


@dataclass
class AuditEntry:
    """Single entry in the agent action audit trail."""
    timestamp: datetime
    phase: WorkflowPhase
    tool_name: str
    arguments: dict[str, Any]
    was_allowed: bool
    result_summary: str | None = None
    blocked_reason: str | None = None


@dataclass
class InvestigationFinding:
    """A structured finding from the investigation phase."""
    category: str  # "signal", "cluster", "anomaly", "health", "linkage"
    severity: str  # "high", "medium", "low", "info"
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    recommended_action: str | None = None


# ── System prompts for each phase ─────────────────────────────────────

INVESTIGATION_SYSTEM_PROMPT = """You are a LandOS mesh investigation agent. Your job is to analyze
the current state of the event mesh and identify actionable findings.

Investigation approach:
1. Start with get_mesh_health for a system overview
2. Check listing inventory — look for BBO signal concentrations
3. Analyze high-value parcels (score >= 0.70) for linkage gaps
4. Preview clusters to identify ownership concentration patterns
5. Run BBO signal analysis on listings with high CDOM or subdivision presence
6. Check trigger rules for any unexpected suppression patterns
7. Dry-run key event types to verify trigger routing

You have READ-ONLY tools. You cannot modify any state.
Report your findings but do NOT suggest running mutation tools yet.
Be thorough and specific — cite listing_keys, regrid_ids, and cluster_ids."""

REMEDIATION_SYSTEM_PROMPT = """You are a LandOS mesh remediation agent. Based on the investigation
findings, you will execute approved mutation operations.

You have access to mutation tools that modify mesh state:
- ingest_spark_batch: Ingest new MLS listings through the Spark adapter
- ingest_regrid_batch: Ingest new parcel records through the Regrid adapter
- run_cluster_detection: Detect clusters from current parcel/listing state

ONLY execute operations that were explicitly approved by the human operator.
After each mutation, verify the result by checking mesh health and store state.
Report what changed and any new wake instructions that fired."""


# ── Safety hooks ──────────────────────────────────────────────────────

class SafetyHookResult:
    """Result of a safety hook evaluation."""

    def __init__(self, allowed: bool, reason: str | None = None):
        self.allowed = allowed
        self.reason = reason

    def __bool__(self) -> bool:
        return self.allowed


def validate_batch_size(tool_name: str, arguments: dict[str, Any]) -> SafetyHookResult:
    """Prevent excessively large batch ingestions.

    Max batch sizes:
      - Spark: 500 records per call
      - Regrid: 1000 records per call
    """
    if tool_name == "ingest_spark_batch":
        records = arguments.get("raw_records", [])
        if len(records) > 500:
            return SafetyHookResult(
                False,
                f"Spark batch too large: {len(records)} records (max 500)",
            )
    elif tool_name == "ingest_regrid_batch":
        records = arguments.get("raw_records", [])
        if len(records) > 1000:
            return SafetyHookResult(
                False,
                f"Regrid batch too large: {len(records)} records (max 1000)",
            )
    return SafetyHookResult(True)


def validate_cluster_params(tool_name: str, arguments: dict[str, Any]) -> SafetyHookResult:
    """Prevent cluster detection with dangerously loose parameters."""
    if tool_name == "run_cluster_detection":
        radius = arguments.get("proximity_radius_m", 200.0)
        if radius > 1000.0:
            return SafetyHookResult(
                False,
                f"Proximity radius too large: {radius}m (max 1000m). "
                "This would create false-positive clusters.",
            )
        min_parcels = arguments.get("owner_min_parcels", 2)
        if min_parcels < 2:
            return SafetyHookResult(
                False,
                f"owner_min_parcels too low: {min_parcels} (min 2). "
                "Single-parcel 'clusters' are meaningless.",
            )
    return SafetyHookResult(True)


# All safety hooks, evaluated in order before any mutation tool call
SAFETY_HOOKS = [validate_batch_size, validate_cluster_params]


# ── Orchestrator ──────────────────────────────────────────────────────

class LandOSOrchestrator:
    """Orchestrates LandOS agent workflows with human-in-the-loop gating.

    The orchestrator enforces the investigation → review → remediation
    pattern by controlling which tools are available in each phase.
    """

    def __init__(self, mesh: MeshState | None = None):
        self.mesh = mesh or MeshState()
        self.current_phase: WorkflowPhase = WorkflowPhase.INVESTIGATION
        self.audit_trail: list[AuditEntry] = []
        self.investigation_findings: list[InvestigationFinding] = []
        self.approved_mutations: set[str] = set()
        self._remediation_approved: bool = False

    # ── Phase management ──────────────────────────────────────────────

    def get_system_prompt(self, phase: WorkflowPhase | None = None) -> str:
        """Get the system prompt for the current or specified phase."""
        p = phase or self.current_phase
        if p == WorkflowPhase.INVESTIGATION:
            return INVESTIGATION_SYSTEM_PROMPT
        return REMEDIATION_SYSTEM_PROMPT

    def get_allowed_tools(self, phase: WorkflowPhase | None = None) -> list[dict]:
        """Get tool definitions allowed in the current or specified phase."""
        p = phase or self.current_phase
        if p == WorkflowPhase.INVESTIGATION:
            return list(INVESTIGATION_TOOLS)
        # Remediation phase: investigation tools + approved mutations only
        allowed_mutations = [
            t for t in MUTATION_TOOLS if t["name"] in self.approved_mutations
        ]
        return list(INVESTIGATION_TOOLS) + allowed_mutations

    def get_allowed_tool_names(self, phase: WorkflowPhase | None = None) -> list[str]:
        """Get MCP-prefixed tool names for Claude Agent SDK allowed_tools config."""
        tools = self.get_allowed_tools(phase)
        return [f"mcp__landos__{t['name']}" for t in tools]

    def build_agent_options(self, phase: WorkflowPhase | None = None) -> dict[str, Any]:
        """Build a Claude Agent SDK options dict for the given phase.

        Returns a dict suitable for ClaudeAgentOptions construction.
        The caller adds their own model and API key config.
        """
        import sys
        from pathlib import Path

        p = phase or self.current_phase
        server_path = Path(__file__).parent / "server.py"

        options = {
            "system_prompt": self.get_system_prompt(p),
            "mcp_servers": {
                "landos": {
                    "command": sys.executable,
                    "args": [str(server_path)],
                },
            },
            "allowed_tools": self.get_allowed_tool_names(p),
        }

        # Add safety hooks for remediation phase
        if p == WorkflowPhase.REMEDIATION:
            options["hooks"] = self._build_safety_hooks()

        return options

    def _build_safety_hooks(self) -> dict[str, list]:
        """Build PreToolUse hook config for mutation tools."""
        hooks: list[dict] = []
        for tool_name in self.approved_mutations:
            hooks.append({
                "matcher": f"mcp__landos__{tool_name}",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"echo 'HITL: {tool_name} approved for execution'",
                    }
                ],
            })
        return {"PreToolUse": hooks} if hooks else {}

    # ── Tool call gating ──────────────────────────────────────────────

    def check_tool_allowed(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> SafetyHookResult:
        """Check if a tool call is allowed in the current phase.

        Returns SafetyHookResult — True if allowed, False with reason if blocked.
        """
        # Phase gate
        if self.current_phase == WorkflowPhase.INVESTIGATION:
            if tool_name in MUTATION_TOOL_NAMES:
                return SafetyHookResult(
                    False,
                    f"Mutation tool '{tool_name}' not allowed during investigation phase. "
                    "Complete investigation first, then request remediation approval.",
                )

        elif self.current_phase == WorkflowPhase.REMEDIATION:
            if tool_name in MUTATION_TOOL_NAMES and tool_name not in self.approved_mutations:
                return SafetyHookResult(
                    False,
                    f"Mutation tool '{tool_name}' not approved. "
                    f"Approved mutations: {sorted(self.approved_mutations) or 'none'}",
                )

        # Safety hooks (for mutation tools)
        if tool_name in MUTATION_TOOL_NAMES:
            for hook in SAFETY_HOOKS:
                result = hook(tool_name, arguments)
                if not result:
                    return result

        return SafetyHookResult(True)

    async def execute_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a tool call with phase gating and safety hooks.

        This is the primary entry point for the orchestrator.
        It checks permissions, runs safety hooks, dispatches to the handler,
        and records the action in the audit trail.
        """
        from src.mcp.handlers import dispatch_tool

        # Check permissions
        check = self.check_tool_allowed(tool_name, arguments)
        if not check:
            entry = AuditEntry(
                timestamp=datetime.now(timezone.utc),
                phase=self.current_phase,
                tool_name=tool_name,
                arguments=arguments,
                was_allowed=False,
                blocked_reason=check.reason,
            )
            self.audit_trail.append(entry)
            return {
                "content": [{"type": "text", "text": f"BLOCKED: {check.reason}"}],
                "isError": True,
            }

        # Execute
        result = await dispatch_tool(self.mesh, tool_name, arguments)

        # Audit
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            phase=self.current_phase,
            tool_name=tool_name,
            arguments=arguments,
            was_allowed=True,
            result_summary=_summarize_result(result),
        )
        self.audit_trail.append(entry)
        return result

    # ── Investigation → Remediation transition ────────────────────────

    def add_finding(self, finding: InvestigationFinding) -> None:
        """Add a finding during the investigation phase."""
        self.investigation_findings.append(finding)

    def get_investigation_report(self) -> dict[str, Any]:
        """Get the structured investigation report for human review.

        Returns a dict with findings grouped by severity, plus
        recommended mutation actions for the human to approve/deny.
        """
        high = [f for f in self.investigation_findings if f.severity == "high"]
        medium = [f for f in self.investigation_findings if f.severity == "medium"]
        low = [f for f in self.investigation_findings if f.severity in ("low", "info")]

        recommended_actions = set()
        for f in self.investigation_findings:
            if f.recommended_action:
                recommended_actions.add(f.recommended_action)

        return {
            "findings_count": len(self.investigation_findings),
            "by_severity": {
                "high": [_serialize_finding(f) for f in high],
                "medium": [_serialize_finding(f) for f in medium],
                "low_and_info": [_serialize_finding(f) for f in low],
            },
            "recommended_actions": sorted(recommended_actions),
            "audit_trail_size": len(self.audit_trail),
        }

    def approve_remediation(self, approved_actions: list[str] | None = None) -> None:
        """Human approves transition to remediation phase.

        Args:
            approved_actions: list of mutation tool names to approve.
                If None, approves all recommended actions from findings.
        """
        if approved_actions is not None:
            # Validate requested actions are real mutation tools
            for action in approved_actions:
                if action not in MUTATION_TOOL_NAMES:
                    raise ValueError(
                        f"'{action}' is not a mutation tool. "
                        f"Available: {sorted(MUTATION_TOOL_NAMES)}"
                    )
            self.approved_mutations = set(approved_actions)
        else:
            # Auto-approve all recommended actions from findings
            recommended = set()
            for f in self.investigation_findings:
                if f.recommended_action and f.recommended_action in MUTATION_TOOL_NAMES:
                    recommended.add(f.recommended_action)
            self.approved_mutations = recommended

        self._remediation_approved = True
        self.current_phase = WorkflowPhase.REMEDIATION

    def deny_remediation(self) -> None:
        """Human denies remediation — stays in investigation phase."""
        self.approved_mutations = set()
        self._remediation_approved = False

    # ── Audit trail ───────────────────────────────────────────────────

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Get the full audit trail as serializable dicts."""
        return [
            {
                "timestamp": str(e.timestamp),
                "phase": e.phase.value,
                "tool_name": e.tool_name,
                "was_allowed": e.was_allowed,
                "blocked_reason": e.blocked_reason,
                "result_summary": e.result_summary,
            }
            for e in self.audit_trail
        ]

    @property
    def is_remediation_approved(self) -> bool:
        return self._remediation_approved


# ── Helpers ───────────────────────────────────────────────────────────

def _serialize_finding(f: InvestigationFinding) -> dict[str, Any]:
    return {
        "category": f.category,
        "severity": f.severity,
        "summary": f.summary,
        "details": f.details,
        "recommended_action": f.recommended_action,
    }


def _summarize_result(result: dict[str, Any]) -> str:
    """Extract a one-line summary from an MCP tool result."""
    if result.get("isError"):
        text = result.get("content", [{}])[0].get("text", "unknown error")
        return f"ERROR: {text[:100]}"
    text = result.get("content", [{}])[0].get("text", "")
    # Try to parse as JSON and extract a key metric
    try:
        data = json.loads(text)
        if "count" in data:
            return f"OK: {data['count']} items"
        if "clusters_detected" in data:
            return f"OK: {data['clusters_detected']} clusters"
        if "records_processed" in data:
            return f"OK: {data['records_processed']} records"
        return f"OK: {text[:80]}"
    except (json.JSONDecodeError, TypeError):
        return f"OK: {text[:80]}"
