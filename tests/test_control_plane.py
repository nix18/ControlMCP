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


def test_plan_desktop_task_adds_windows_tray_strategy_hints():
    payload = json.loads(
        dispatch_tool(
            "plan_desktop_task",
            {"instruction": "从托盘恢复微信主窗口，不要重新启动微信"},
        )
    )

    assert payload["intent"] == "restore_tray_application"
    assert payload["strategy_hints"]
    assert any(hint["id"] == "wechat-tray-restore" for hint in payload["strategy_hints"])
    assert payload["steps"][0]["action"] == "recover_execution_context"


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


def test_click_grid_target_guarded_by_sensitive_risk_context():
    payload = json.loads(
        dispatch_tool(
            "click_grid_target",
            {
                "capture": {
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 100,
                    "grid_rows": 2,
                    "grid_cols": 2,
                },
                "cell": 1,
                "risk_context": "支付确认按钮",
            },
        )
    )

    assert payload["status"] == "confirmation_required"


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


@patch("control_mcp.control_plane.recovery.tool_wait")
@patch("control_mcp.control_plane.recovery.tool_key_press")
@patch("control_mcp.control_plane.recovery.tool_capture_window")
@patch("control_mcp.control_plane.recovery.tool_focus_window")
@patch("control_mcp.control_plane.recovery.tool_hotkey")
def test_recover_execution_context_supports_wechat_tray_restore(
    mock_hotkey,
    mock_focus_window,
    mock_capture_window,
    mock_key_press,
    mock_wait,
):
    mock_hotkey.return_value = '{"success": true}'
    mock_focus_window.return_value = '{"success": true}'
    mock_capture_window.return_value = '{"success": true, "file_path": "/tmp/wx.png"}'
    mock_key_press.return_value = '{"success": true}'
    mock_wait.return_value = '{"success": true}'

    payload = json.loads(
        dispatch_tool(
            "recover_execution_context",
            {"strategy": "wechat_tray_restore", "target_window": "微信"},
        )
    )

    assert payload["success"] is True
    assert payload["strategy"] == "wechat_tray_restore"
    assert mock_hotkey.call_args_list[0].args == ("win", "b")
    assert mock_wait.call_args_list[0].args == (0.5,)
    assert mock_key_press.call_args_list[0].args == (["enter"],)


@patch("control_mcp.control_plane.recovery.tool_capture_window")
@patch("control_mcp.control_plane.recovery.tool_hotkey")
@patch("control_mcp.control_plane.recovery.tool_focus_window")
def test_recover_execution_context_supports_occlusion_rescue_with_target(
    mock_focus_window,
    mock_hotkey,
    mock_capture_window,
):
    mock_focus_window.return_value = '{"success": true}'
    mock_hotkey.return_value = '{"success": true}'
    mock_capture_window.return_value = '{"success": true, "file_path": "/tmp/win.png"}'

    payload = json.loads(
        dispatch_tool(
            "recover_execution_context",
            {"strategy": "occlusion_rescue", "target_window": "PyCharm"},
        )
    )

    assert payload["strategy"] == "occlusion_rescue"
    mock_focus_window.assert_called_once_with("PyCharm")
    mock_hotkey.assert_called_once_with("win", "up")


def test_plan_desktop_task_generates_occlusion_recovery_step():
    payload = json.loads(
        dispatch_tool(
            "plan_desktop_task",
            {"instruction": "窗口被别的窗口遮挡了，帮我恢复 PyCharm"},
        )
    )

    assert payload["intent"] == "recover_window_visibility"
    assert payload["steps"][0]["action"] == "recover_execution_context"
