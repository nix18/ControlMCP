"""Tool dispatching for atomic and control-plane tools."""

from __future__ import annotations

import json
from typing import Any

from control_mcp.control_plane.executor import execute_desktop_plan, get_execution_status
from control_mcp.control_plane.guards import (
    approve_confirmation,
    maybe_require_confirmation,
    validate_confirmation_token,
)
from control_mcp.control_plane.memory import record_experience
from control_mcp.control_plane.planner import get_plan, plan_desktop_task, remember_plan
from control_mcp.control_plane.recovery import recover_execution_context
from control_mcp.domain.models import DesktopTaskPlan, PlanStep
from control_mcp.tools.actions import (
    tool_clipboard_get,
    tool_clipboard_set,
    tool_get_pixel_color,
    tool_hotkey,
    tool_launch_app,
    tool_launch_url,
    tool_wait,
)
from control_mcp.tools.combined import tool_mouse_and_keyboard
from control_mcp.tools.grid import tool_click_grid_target, tool_resolve_grid_target
from control_mcp.tools.keyboard import (
    tool_key_hold,
    tool_key_press,
    tool_key_sequence,
    tool_key_type,
)
from control_mcp.tools.mouse import (
    tool_mouse_click,
    tool_mouse_drag,
    tool_mouse_move,
    tool_mouse_position,
    tool_mouse_scroll,
)
from control_mcp.tools.screen import (
    tool_capture_region,
    tool_capture_screen,
    tool_capture_scroll_region,
    tool_get_screen_info,
    tool_read_screenshot_base64,
)
from control_mcp.tools.window import (
    tool_capture_window,
    tool_find_windows,
    tool_focus_window,
    tool_list_windows,
)

_GUARDED_TOOL_NAMES = {
    "mouse_click",
    "key_press",
    "key_type",
    "key_sequence",
    "mouse_and_keyboard",
    "clipboard_set",
    "launch_app",
    "launch_url",
    "hotkey",
    "click_grid_target",
}


def dispatch_tool(name: str, args: dict[str, Any]) -> str:
    if name in _GUARDED_TOOL_NAMES and not validate_confirmation_token(
        args.get("confirmation_token")
    ):
        confirmation = maybe_require_confirmation(
            name,
            args,
            summary=f"Sensitive guard check for {name}",
            scope="atomic_tool",
        )
        if confirmation is not None:
            return json.dumps(confirmation, ensure_ascii=False)

    if name == "capture_screen":
        return tool_capture_screen(
            save_dir=args.get("save_dir"),
            monitor=args.get("monitor"),
            quality=args.get("quality", 80),
            max_width=args.get("max_width"),
            grid_rows=args.get("grid_rows"),
            grid_cols=args.get("grid_cols"),
        )
    if name == "capture_region":
        return tool_capture_region(
            x=args["x"],
            y=args["y"],
            width=args["width"],
            height=args["height"],
            save_dir=args.get("save_dir"),
            quality=args.get("quality", 80),
            max_width=args.get("max_width"),
            grid_rows=args.get("grid_rows"),
            grid_cols=args.get("grid_cols"),
        )
    if name == "capture_scroll_region":
        return tool_capture_scroll_region(
            x=args["x"],
            y=args["y"],
            width=args["width"],
            height=args["height"],
            scroll_distance=args["scroll_distance"],
            save_dir=args.get("save_dir"),
            quality=args.get("quality", 80),
            max_width=args.get("max_width"),
        )
    if name == "resolve_grid_target":
        return tool_resolve_grid_target(
            base_x=args["base_x"],
            base_y=args["base_y"],
            image_width=args["image_width"],
            image_height=args["image_height"],
            grid_rows=args["grid_rows"],
            grid_cols=args["grid_cols"],
            cell=args["cell"],
            anchor=args.get("anchor", "center"),
        )
    if name == "get_screen_info":
        return tool_get_screen_info()
    if name == "read_screenshot_base64":
        return tool_read_screenshot_base64(
            file_path=args["file_path"],
            as_data_url=args.get("as_data_url", False),
        )
    if name == "list_windows":
        return tool_list_windows()
    if name == "find_windows":
        return tool_find_windows(args["title_contains"])
    if name == "focus_window":
        return tool_focus_window(args["title"])
    if name == "capture_window":
        return tool_capture_window(
            args["title"],
            save_dir=args.get("save_dir"),
            quality=args.get("quality", 80),
            max_width=args.get("max_width"),
            grid_rows=args.get("grid_rows"),
            grid_cols=args.get("grid_cols"),
        )
    if name == "click_grid_target":
        return tool_click_grid_target(
            capture=args.get("capture"),
            cell=args["cell"],
            anchor=args.get("anchor", "center"),
            button=args.get("button", "left"),
            clicks=args.get("clicks", 1),
            move_only=args.get("move_only", False),
            duration=args.get("duration", 0.25),
        )
    if name == "mouse_click":
        return tool_mouse_click(
            x=args["x"],
            y=args["y"],
            button=args.get("button", "left"),
            clicks=args.get("clicks", 1),
            interval=args.get("interval", 0),
            hold_seconds=args.get("hold_seconds", 0),
        )
    if name == "mouse_drag":
        return tool_mouse_drag(
            start_x=args["start_x"],
            start_y=args["start_y"],
            end_x=args["end_x"],
            end_y=args["end_y"],
            button=args.get("button", "left"),
            duration=args.get("duration", 0.5),
        )
    if name == "mouse_move":
        return tool_mouse_move(args["x"], args["y"], duration=args.get("duration", 0.25))
    if name == "mouse_position":
        return tool_mouse_position()
    if name == "mouse_scroll":
        return tool_mouse_scroll(args["clicks"], x=args.get("x"), y=args.get("y"))
    if name == "key_press":
        return tool_key_press(
            args["keys"], presses=args.get("presses", 1), interval=args.get("interval", 0.0)
        )
    if name == "key_hold":
        return tool_key_hold(args["keys"], args["hold_seconds"])
    if name == "key_type":
        return tool_key_type(args["text"], interval=args.get("interval", 0.0))
    if name == "key_sequence":
        return tool_key_sequence(args["sequence"])
    if name == "mouse_and_keyboard":
        return tool_mouse_and_keyboard(args["actions"])
    if name == "clipboard_get":
        return tool_clipboard_get()
    if name == "clipboard_set":
        return tool_clipboard_set(args["text"])
    if name == "launch_app":
        return tool_launch_app(args["command"], args.get("args", ""))
    if name == "launch_url":
        return tool_launch_url(args["url"])
    if name == "wait":
        return tool_wait(args["seconds"])
    if name == "get_pixel_color":
        return tool_get_pixel_color(args["x"], args["y"])
    if name == "hotkey":
        return tool_hotkey(*args["keys"])

    if name == "plan_desktop_task":
        plan = plan_desktop_task(args["instruction"], current_context=args.get("current_context"))
        return plan.to_json()
    if name == "execute_desktop_plan":
        plan = _resolve_plan(args)
        if plan is None:
            return json.dumps(
                {"success": False, "message": "Missing plan_id or plan payload."},
                ensure_ascii=False,
            )
        run = execute_desktop_plan(plan, confirmation_token=args.get("confirmation_token"))
        return run.to_json()
    if name == "get_execution_status":
        return json.dumps(get_execution_status(args["run_id"]), ensure_ascii=False)
    if name == "confirm_sensitive_action":
        return json.dumps(
            approve_confirmation(
                args["confirmation_id"],
                approve=args.get("approve", True),
                note=args.get("note"),
            ),
            ensure_ascii=False,
        )
    if name == "recover_execution_context":
        return json.dumps(
            recover_execution_context(
                strategy=args.get("strategy", "window_rescue"),
                target_window=args.get("target_window"),
            ),
            ensure_ascii=False,
        )
    if name == "record_workflow_experience":
        experience = record_experience(
            intent=args["intent"],
            instruction=args["instruction"],
            app=args.get("app"),
            summary=args.get("summary", ""),
            preferred_actions=args.get("preferred_actions", []),
            anti_patterns=args.get("anti_patterns", []),
            verification_hints=args.get("verification_hints", []),
            success=args.get("success", True),
        )
        return experience.to_json()

    return json.dumps({"success": False, "message": f"Unknown tool: {name}"}, ensure_ascii=False)


def _resolve_plan(args: dict[str, Any]) -> DesktopTaskPlan | None:
    if args.get("plan_id"):
        return get_plan(args["plan_id"])
    payload = args.get("plan")
    if not payload:
        return None
    steps = [PlanStep(**step) for step in payload.get("steps", [])]
    plan = DesktopTaskPlan(
        plan_id=payload.get("plan_id") or "plan_inline",
        instruction=payload["instruction"],
        normalized_instruction=payload.get("normalized_instruction", payload["instruction"]),
        intent=payload.get("intent", "navigate_and_observe"),
        confidence=payload.get("confidence", 0.0),
        summary=payload.get("summary", ""),
        needs_confirmation=payload.get("needs_confirmation", False),
        needs_observation=payload.get("needs_observation", False),
        status=payload.get("status", "ready"),
        target_window=payload.get("target_window"),
        risk_reasons=payload.get("risk_reasons", []),
        strategy_hints=payload.get("strategy_hints", []),
        steps=steps,
        created_at=payload.get("created_at") or __import__("datetime").datetime.now().isoformat(),
    )
    return remember_plan(plan)
