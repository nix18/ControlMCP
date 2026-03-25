"""Workflow experience persistence for the control plane."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from control_mcp.control_plane.strategies import match_builtin_strategies
from control_mcp.domain.models import WorkflowExperience, new_id

_STORE_DIR = Path(tempfile.gettempdir()) / "control_mcp_memory"
_STORE_PATH = _STORE_DIR / "workflow_experience.jsonl"


def _ensure_store() -> Path:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    if not _STORE_PATH.exists():
        _STORE_PATH.write_text("", encoding="utf-8")
    return _STORE_PATH


def record_experience(
    *,
    intent: str,
    instruction: str,
    app: str | None = None,
    summary: str = "",
    preferred_actions: list[str] | None = None,
    anti_patterns: list[str] | None = None,
    verification_hints: list[str] | None = None,
    success: bool = True,
    metadata: dict[str, Any] | None = None,
) -> WorkflowExperience:
    experience = WorkflowExperience(
        experience_id=new_id("exp"),
        intent=intent,
        instruction=instruction,
        app=app,
        summary=summary,
        preferred_actions=preferred_actions or [],
        anti_patterns=anti_patterns or [],
        verification_hints=verification_hints or [],
        success=success,
        metadata=metadata or {},
    )
    store_path = _ensure_store()
    with store_path.open("a", encoding="utf-8") as fh:
        fh.write(experience.to_json() + "\n")
    return experience


def list_experiences(limit: int = 20, intent: str | None = None) -> list[dict[str, Any]]:
    store_path = _ensure_store()
    rows: list[dict[str, Any]] = []
    for line in store_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if intent and row.get("intent") != intent:
            continue
        rows.append(row)
    return rows[-limit:]


def collect_strategy_hints(instruction: str, app: str | None = None) -> list[dict[str, Any]]:
    """Return dual-layer strategy hints from built-in rules and stored experience."""
    hints = list(match_builtin_strategies(instruction, app=app))
    seen_ids = {hint.get("id") for hint in hints}
    lower = instruction.lower()
    for row in reversed(list_experiences(limit=50)):
        haystack = " ".join(
            [
                str(row.get("instruction", "")),
                str(row.get("summary", "")),
                str(row.get("app", "")),
            ]
        ).lower()
        if (
            lower
            and lower not in haystack
            and not any(token in haystack for token in lower.split())
        ):
            continue
        memory_hint = {"id": row.get("experience_id"), "layer": "memory", **row}
        if memory_hint["id"] in seen_ids:
            continue
        seen_ids.add(memory_hint["id"])
        hints.append(memory_hint)
    return hints
