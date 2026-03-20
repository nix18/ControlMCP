"""Tests for combined mouse+keyboard operations (mocked)."""

import json
from unittest.mock import patch, MagicMock

from control_mcp.tools.combined import tool_mouse_and_keyboard


class TestToolMouseAndKeyboard:
    @patch("control_mcp.tools.combined.time")
    @patch("control_mcp.tools.combined.pyautogui")
    def test_click_sequence(self, mock_pyauto, mock_time):
        result = tool_mouse_and_keyboard(
            actions=[
                {"action": "move", "x": 500, "y": 300},
                {"action": "click", "x": 500, "y": 300, "button": "left"},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        assert data["steps_completed"] == 2
        assert data["total_steps"] == 2
        mock_pyauto.moveTo.assert_called()
        mock_pyauto.click.assert_called_once()

    @patch("control_mcp.tools.combined.time")
    @patch("control_mcp.tools.combined.pyautogui")
    def test_unknown_action(self, mock_pyauto, mock_time):
        result = tool_mouse_and_keyboard(
            actions=[
                {"action": "unknown_action"},
            ]
        )
        data = json.loads(result)
        assert data["success"] is False
        assert data["results"][0]["success"] is False

    @patch("control_mcp.tools.combined.time")
    @patch("control_mcp.tools.combined.pyautogui")
    def test_partial_failure(self, mock_pyauto, mock_time):
        mock_pyauto.click.side_effect = [Exception("fail"), None]
        result = tool_mouse_and_keyboard(
            actions=[
                {"action": "click", "x": 0, "y": 0},
                {"action": "click", "x": 1, "y": 1},
            ]
        )
        data = json.loads(result)
        assert data["success"] is False
        assert data["steps_completed"] == 1

    @patch("control_mcp.tools.combined.time")
    @patch("control_mcp.tools.combined.pyautogui")
    def test_delay_between_steps(self, mock_pyauto, mock_time):
        result = tool_mouse_and_keyboard(
            actions=[
                {"action": "move", "x": 100, "y": 100, "delay": 0.5},
                {"action": "move", "x": 200, "y": 200},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        # delay should cause a time.sleep call
        mock_time.sleep.assert_called()

    @patch("control_mcp.tools.combined.time")
    @patch("control_mcp.tools.combined.pyautogui")
    def test_click_with_hold(self, mock_pyauto, mock_time):
        result = tool_mouse_and_keyboard(
            actions=[
                {"action": "click", "x": 100, "y": 100, "hold_seconds": 2.0},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.mouseDown.assert_called_once()
        mock_pyauto.mouseUp.assert_called_once()
        mock_time.sleep.assert_called_with(2.0)

    @patch("control_mcp.tools.combined.time")
    @patch("control_mcp.tools.combined.pyautogui")
    def test_complex_workflow(self, mock_pyauto, mock_time):
        result = tool_mouse_and_keyboard(
            actions=[
                {"action": "move", "x": 500, "y": 300, "delay": 0.1},
                {"action": "click", "x": 500, "y": 300, "delay": 0.2},
                {"action": "key_press", "keys": ["ctrl", "a"], "delay": 0.1},
                {"action": "key_type", "text": "replaced", "delay": 0.1},
                {"action": "key_press", "keys": ["enter"]},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        assert data["steps_completed"] == 5
