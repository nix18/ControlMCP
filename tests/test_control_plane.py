"""Tests for the ControlMCP control-plane workflow."""

import json
from unittest.mock import patch

from control_mcp.app.dispatcher import dispatch_tool
from control_mcp.control_plane.guards import approve_confirmation
from control_mcp.control_plane.planner import plan_desktop_task


def test_plan_desktop_task_generates_structured_plan():
    payload = json.loads(
        dispatch_tool(
            "plan_desktop_task",
            {"instruction": "切换到 PyCharm 并运行当前配置"},
        )
    )

    assert payload["plan_id"].startswith("plan_")
    assert payload["intent"] == "run_application_flow"
    assert payload["steps"]
    assert any(step["action"] == "key_press" for step in payload["steps"])


def test_execute_desktop_plan_blocks_sensitive_step_without_confirmation():
    plan = plan_desktop_task("输入支付密码并确认付款")

    payload = json.loads(
        dispatch_tool(
            "execute_desktop_plan",
            {"plan_id": plan.plan_id},
        )
    )

    assert payload["status"] == "blocked"
    assert payload["needs_confirmation"] is True
    assert payload["confirmation_id"]


@patch("control_mcp.control_plane.executor.tool_key_type")
def test_execute_desktop_plan_after_confirmation(mock_key_type):
    mock_key_type.return_value = '{"success": true, "message": "typed"}'
    plan = plan_desktop_task("输入支付密码并确认付款")
    blocked = json.loads(dispatch_tool("execute_desktop_plan", {"plan_id": plan.plan_id}))
    approval = approve_confirmation(blocked["confirmation_id"], approve=True)

    payload = json.loads(
        dispatch_tool(
            "execute_desktop_plan",
            {"plan_id": plan.plan_id, "confirmation_token": approval["confirmation_token"]},
        )
    )

    assert payload["status"] == "completed"
    assert mock_key_type.called


def test_atomic_tool_returns_confirmation_required_when_risk_context_is_sensitive():
    payload = json.loads(
        dispatch_tool(
            "launch_url",
            {"url": "https://example.com/pay", "risk_context": "支付并输入密码"},
        )
    )

    assert payload["status"] == "confirmation_required"
    assert payload["confirmation"]["risk_level"] == "high"


@patch("control_mcp.control_plane.recovery.tool_hotkey")
@patch("control_mcp.control_plane.recovery.tool_capture_screen")
def test_recover_execution_context_supports_show_desktop(mock_capture_screen, mock_hotkey):
    mock_hotkey.return_value = '{"success": true, "message": "desktop shown"}'
    mock_capture_screen.return_value = '{"file_path": "/tmp/screen.jpg", "success": true}'
    payload = json.loads(
        dispatch_tool(
            "recover_execution_context",
            {"strategy": "show_desktop_then_capture"},
        )
    )

    assert payload["success"] is True
    assert payload["strategy"] == "show_desktop_then_capture"
