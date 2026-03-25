"""Recovery strategies for desktop-control execution."""

from __future__ import annotations

from typing import Any

from control_mcp.tools.actions import tool_hotkey
from control_mcp.tools.screen import tool_capture_screen
from control_mcp.tools.window import tool_capture_window, tool_focus_window, tool_list_windows


def recover_execution_context(
    *,
    strategy: str = "window_rescue",
    target_window: str | None = None,
) -> dict[str, Any]:
    """Attempt a bounded recovery and return the observed result."""
    results: list[dict[str, Any]] = []

    if strategy == "show_desktop_then_capture":
        results.append(_parse(tool_hotkey("win", "d")))
        results.append(_parse(tool_capture_screen(quality=75, max_width=960)))
        return {"success": True, "strategy": strategy, "results": results}

    if target_window:
        results.append(_parse(tool_focus_window(target_window)))
        results.append(_parse(tool_hotkey("win", "up")))
        results.append(_parse(tool_capture_window(target_window, quality=75, max_width=960)))
        return {"success": True, "strategy": strategy, "results": results}

    results.append(_parse(tool_list_windows()))
    results.append(_parse(tool_capture_screen(quality=75, max_width=960)))
    return {"success": True, "strategy": "global_reobserve", "results": results}


def suggest_recovery(target_window: str | None = None) -> list[str]:
    suggestions = [
        "重新截图并从当前真实界面重新规划。",
        "先做窗口救援，再继续操作。",
    ]
    if target_window:
        suggestions.insert(0, f"尝试重新聚焦并最大化窗口: {target_window}")
    else:
        suggestions.insert(0, "如果上下文完全丢失，可先显示桌面再重新观察。")
    return suggestions


def _parse(payload: str) -> dict[str, Any]:
    import json

    return json.loads(payload)
