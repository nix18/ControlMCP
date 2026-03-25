"""Guarded execution runtime for desktop task plans."""

from __future__ import annotations

import json
from typing import Any

from control_mcp.control_plane.guards import create_confirmation, validate_confirmation_token
from control_mcp.control_plane.memory import record_experience
from control_mcp.control_plane.recovery import recover_execution_context, suggest_recovery
from control_mcp.control_plane.verifier import wait_until_stable
from control_mcp.domain.models import DesktopTaskPlan, ExecutionRun, StepExecutionResult, new_id
from control_mcp.tools.actions import (
    tool_clipboard_set,
    tool_hotkey,
    tool_launch_app,
    tool_launch_url,
    tool_wait,
)
from control_mcp.tools.combined import tool_mouse_and_keyboard
from control_mcp.tools.keyboard import tool_key_press, tool_key_type
from control_mcp.tools.mouse import tool_mouse_click
from control_mcp.tools.screen import (
    tool_capture_region,
    tool_capture_screen,
    tool_capture_scroll_region,
)
from control_mcp.tools.window import tool_capture_window, tool_focus_window

_RUNS: dict[str, ExecutionRun] = {}


def execute_desktop_plan(
    plan: DesktopTaskPlan,
    *,
    confirmation_token: str | None = None,
) -> ExecutionRun:
    run = ExecutionRun(
        run_id=new_id("run"),
        plan_id=plan.plan_id,
        instruction=plan.instruction,
        status="running",
        total_steps=len(plan.steps),
    )
    _RUNS[run.run_id] = run

    ticket = validate_confirmation_token(confirmation_token)

    for step in plan.steps:
        run.current_step = step.id
        run.updated_at = _now_iso()

        if step.sensitive and ticket is None:
            confirmation = create_confirmation(
                summary=step.goal or f"Sensitive step: {step.action}",
                scope="plan_step",
                reason="This step is marked as sensitive and requires explicit confirmation.",
                risk_level=step.risk_level,
                plan_id=plan.plan_id,
                run_id=run.run_id,
                metadata={"step": step.to_dict()},
            )
            run.status = "blocked"
            run.needs_confirmation = True
            run.confirmation_id = confirmation.confirmation_id
            run.recovery_suggestions = suggest_recovery(plan.target_window)
            return run

        step_result = _execute_step(step, plan.target_window)
        run.results.append(step_result)
        run.completed_steps += 1 if step_result.success else 0
        run.updated_at = _now_iso()

        if not step_result.success:
            run.status = "recovering"
            recovery = recover_execution_context(target_window=plan.target_window)
            run.results.append(
                StepExecutionResult(
                    step_id=f"{step.id}:recovery",
                    action="recover_execution_context",
                    success=recovery.get("success", False),
                    result=recovery,
                    message="Triggered recovery after step failure.",
                )
            )
            run.recovery_suggestions = suggest_recovery(plan.target_window)
            run.status = "failed"
            return run

    run.status = "completed"
    run.current_step = None
    record_experience(
        intent=plan.intent,
        instruction=plan.normalized_instruction,
        app=plan.target_window,
        summary=plan.summary,
        preferred_actions=[step.action for step in plan.steps],
        verification_hints=[hint for step in plan.steps for hint in step.verification],
        success=True,
        metadata={"plan_id": plan.plan_id, "run_id": run.run_id},
    )
    return run


def get_execution_status(run_id: str) -> dict[str, Any]:
    run = _RUNS.get(run_id)
    if run is None:
        return {"success": False, "message": f"Unknown run id: {run_id}"}
    return {"success": True, "run": run.to_dict()}


def _execute_step(step, target_window: str | None) -> StepExecutionResult:
    try:
        if step.action == "focus_window":
            payload = _json(tool_focus_window(step.args["title"]))
        elif step.action == "capture_screen":
            payload = _json(tool_capture_screen(**step.args))
        elif step.action == "capture_window":
            payload = _json(tool_capture_window(**step.args))
        elif step.action == "capture_region":
            payload = _json(tool_capture_region(**step.args))
        elif step.action == "capture_scroll_region":
            payload = _json(tool_capture_scroll_region(**step.args))
        elif step.action == "key_press":
            payload = _json(tool_key_press(**step.args))
        elif step.action == "key_type":
            payload = _json(tool_key_type(**step.args))
        elif step.action == "clipboard_set":
            payload = _json(tool_clipboard_set(**step.args))
        elif step.action == "mouse_click":
            payload = _json(tool_mouse_click(**step.args))
        elif step.action == "wait":
            payload = _json(tool_wait(**step.args))
        elif step.action == "launch_app":
            payload = _json(tool_launch_app(**step.args))
        elif step.action == "launch_url":
            payload = _json(tool_launch_url(**step.args))
        elif step.action == "hotkey":
            payload = _json(tool_hotkey(*step.args.get("keys", [])))
        elif step.action == "mouse_and_keyboard":
            payload = _json(tool_mouse_and_keyboard(**step.args))
        elif step.action == "wait_until_stable":
            region = step.args.get("region")
            payload = wait_until_stable(
                scope=step.args.get("scope", "screen"),
                title=step.args.get("title") or target_window,
                region=region,
                rounds=step.args.get("rounds", 2),
                interval_seconds=step.args.get("interval_seconds", 1.0),
            )
        elif step.action == "request_confirmation":
            payload = {
                "success": False,
                "status": "confirmation_required",
                "message": "This plan contains a sensitive confirmation step.",
            }
        else:
            payload = {"success": False, "message": f"Unsupported step action: {step.action}"}

        success = bool(payload.get("success", True))
        return StepExecutionResult(
            step_id=step.id,
            action=step.action,
            success=success,
            result=payload,
            message=payload.get("message", ""),
        )
    except Exception as exc:
        return StepExecutionResult(
            step_id=step.id,
            action=step.action,
            success=False,
            result={"error": str(exc)},
            message=str(exc),
        )


def _json(payload: str) -> dict[str, Any]:
    return json.loads(payload)


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now().isoformat()
