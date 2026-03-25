"""Typed models for the ControlMCP control plane."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class PlanStep:
    """One executable step in a desktop task plan."""

    id: str
    kind: str
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    goal: str = ""
    verification: list[str] = field(default_factory=list)
    fallback: list[str] = field(default_factory=list)
    risk_level: str = "low"
    sensitive: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DesktopTaskPlan:
    """Structured plan produced from a desktop instruction."""

    plan_id: str
    instruction: str
    normalized_instruction: str
    intent: str
    confidence: float
    summary: str
    needs_confirmation: bool = False
    needs_observation: bool = False
    status: str = "ready"
    target_window: str | None = None
    risk_reasons: list[str] = field(default_factory=list)
    steps: list[PlanStep] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [step.to_dict() for step in self.steps]
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


@dataclass
class ConfirmationTicket:
    """A pending confirmation for a sensitive action."""

    confirmation_id: str
    risk_level: str
    reason: str
    summary: str
    scope: str
    status: str = "pending"
    plan_id: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    expires_in_seconds: int = 300
    confirmation_token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


@dataclass
class StepExecutionResult:
    """Execution result of a single plan step."""

    step_id: str
    action: str
    success: bool
    result: dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionRun:
    """State of an executing or completed desktop plan."""

    run_id: str
    plan_id: str
    instruction: str
    status: str
    current_step: str | None = None
    completed_steps: int = 0
    total_steps: int = 0
    needs_confirmation: bool = False
    confirmation_id: str | None = None
    results: list[StepExecutionResult] = field(default_factory=list)
    recovery_suggestions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["results"] = [result.to_dict() for result in self.results]
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


@dataclass
class WorkflowExperience:
    """A persisted workflow experience that can be reused later."""

    experience_id: str
    intent: str
    instruction: str
    app: str | None = None
    summary: str = ""
    preferred_actions: list[str] = field(default_factory=list)
    anti_patterns: list[str] = field(default_factory=list)
    verification_hints: list[str] = field(default_factory=list)
    success: bool = True
    created_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
