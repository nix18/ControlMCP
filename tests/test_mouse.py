"""Tests for mouse control tools (mocked)."""

import json
from unittest.mock import MagicMock, patch

from control_mcp.tools.mouse import (
    tool_mouse_click,
    tool_mouse_drag,
    tool_mouse_move,
    tool_mouse_position,
    tool_mouse_scroll,
)


class TestToolMouseClick:
    @patch("control_mcp.tools.mouse.pyautogui")
    def test_single_click(self, mock_pyauto):
        result = tool_mouse_click(x=500, y=300)
        data = json.loads(result)
        assert data["success"] is True
        assert data["x"] == 500
        assert data["y"] == 300
        assert data["clicks"] == 1
        assert data["button"] == "left"
        mock_pyauto.moveTo.assert_called_once()
        mock_pyauto.click.assert_called_once()

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_double_click(self, mock_pyauto):
        result = tool_mouse_click(x=100, y=200, clicks=2)
        data = json.loads(result)
        assert data["clicks"] == 2

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_right_click(self, mock_pyauto):
        result = tool_mouse_click(x=0, y=0, button="right")
        data = json.loads(result)
        assert data["button"] == "right"

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_hold(self, mock_pyauto):
        result = tool_mouse_click(x=100, y=100, hold_seconds=2.0)
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.mouseDown.assert_called_once()
        mock_pyauto.mouseUp.assert_called_once()

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.moveTo.side_effect = Exception("fail")
        result = tool_mouse_click(x=0, y=0)
        data = json.loads(result)
        assert data["success"] is False
        assert "fail" in data["message"]


class TestToolMouseDrag:
    @patch("control_mcp.tools.mouse.pyautogui")
    def test_success(self, mock_pyauto):
        result = tool_mouse_drag(start_x=10, start_y=20, end_x=100, end_y=200, duration=0.5)
        data = json.loads(result)
        assert data["success"] is True
        assert data["start_x"] == 10
        assert data["end_y"] == 200
        mock_pyauto.mouseDown.assert_called_once()
        mock_pyauto.mouseUp.assert_called_once()

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.moveTo.side_effect = Exception("drag fail")
        result = tool_mouse_drag(start_x=0, start_y=0, end_x=100, end_y=100)
        data = json.loads(result)
        assert data["success"] is False


class TestToolMouseMove:
    @patch("control_mcp.tools.mouse.pyautogui")
    def test_success(self, mock_pyauto):
        result = tool_mouse_move(x=960, y=540, duration=0.1)
        data = json.loads(result)
        assert data["x"] == 960
        assert data["y"] == 540
        mock_pyauto.moveTo.assert_called_once()

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.moveTo.side_effect = Exception("move fail")
        result = tool_mouse_move(x=0, y=0)
        data = json.loads(result)
        assert "error" in data


class TestToolMousePosition:
    @patch("control_mcp.tools.mouse.pyautogui")
    def test_returns_position(self, mock_pyauto):
        pos = MagicMock()
        pos.x = 500
        pos.y = 300
        mock_pyauto.position.return_value = pos

        result = tool_mouse_position()
        data = json.loads(result)
        assert data["x"] == 500
        assert data["y"] == 300


class TestToolMouseScroll:
    @patch("control_mcp.tools.mouse.pyautogui")
    def test_scroll_up(self, mock_pyauto):
        result = tool_mouse_scroll(clicks=3)
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.scroll.assert_called_once_with(3)

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_scroll_down(self, mock_pyauto):
        result = tool_mouse_scroll(clicks=-5, x=500, y=300)
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.scroll.assert_called_once_with(-5, x=500, y=300)

    @patch("control_mcp.tools.mouse.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.scroll.side_effect = Exception("scroll fail")
        result = tool_mouse_scroll(clicks=1)
        data = json.loads(result)
        assert data["success"] is False
