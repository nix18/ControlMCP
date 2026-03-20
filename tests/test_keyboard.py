"""Tests for keyboard control tools (mocked)."""

import json
from unittest.mock import patch, MagicMock, call

from control_mcp.tools.keyboard import (
    tool_key_press,
    tool_key_hold,
    tool_key_type,
    tool_key_sequence,
)


class TestToolKeyPress:
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_single_key(self, mock_pyauto):
        result = tool_key_press(keys=["enter"])
        data = json.loads(result)
        assert data["success"] is True
        assert data["keys"] == ["enter"]
        mock_pyauto.press.assert_called_once_with("enter", presses=1, interval=0)

    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_combo_keys(self, mock_pyauto):
        result = tool_key_press(keys=["ctrl", "c"])
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.hotkey.assert_called_once_with("ctrl", "c")

    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_multiple_presses(self, mock_pyauto):
        result = tool_key_press(keys=["tab"], presses=3, interval=0.1)
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.press.assert_called_once_with("tab", presses=3, interval=0.1)

    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_combo_multiple_times(self, mock_pyauto):
        result = tool_key_press(keys=["alt", "tab"], presses=2, interval=0.5)
        data = json.loads(result)
        assert data["success"] is True
        assert mock_pyauto.hotkey.call_count == 2

    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.press.side_effect = Exception("key fail")
        result = tool_key_press(keys=["enter"])
        data = json.loads(result)
        assert data["success"] is False


class TestToolKeyHold:
    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_hold_single(self, mock_pyauto, mock_time):
        result = tool_key_hold(keys=["shift"], hold_seconds=2.0)
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.keyDown.assert_called_once_with("shift")
        mock_pyauto.keyUp.assert_called_once_with("shift")
        mock_time.sleep.assert_called_once_with(2.0)

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_hold_multiple(self, mock_pyauto, mock_time):
        result = tool_key_hold(keys=["ctrl", "shift"], hold_seconds=1.0)
        data = json.loads(result)
        assert data["success"] is True
        assert mock_pyauto.keyDown.call_count == 2
        assert mock_pyauto.keyUp.call_count == 2

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_failure_releases_keys(self, mock_pyauto, mock_time):
        mock_time.sleep.side_effect = Exception("interrupted")
        result = tool_key_hold(keys=["shift"], hold_seconds=5.0)
        data = json.loads(result)
        assert data["success"] is False
        # keyUp should still be called for cleanup
        mock_pyauto.keyUp.assert_called()


class TestToolKeyType:
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_ascii_text(self, mock_pyauto):
        result = tool_key_type(text="Hello World", interval=0.05)
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.typewrite.assert_called_once_with("Hello World", interval=0.05)

    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_non_ascii_fallback(self, mock_pyauto):
        mock_pyauto.typewrite.side_effect = Exception("not ascii")
        result = tool_key_type(text="你好")
        data = json.loads(result)
        assert data["success"] is True

    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.typewrite.side_effect = Exception("type fail")
        mock_pyauto.press.side_effect = Exception("press fail")
        result = tool_key_type(text="fail")
        data = json.loads(result)
        assert data["success"] is False


class TestToolKeySequence:
    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_press_sequence(self, mock_pyauto, mock_time):
        result = tool_key_sequence(
            sequence=[
                {"action": "press", "keys": ["ctrl", "a"]},
                {"action": "press", "keys": ["enter"]},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        assert len(data["steps"]) == 2
        assert mock_pyauto.hotkey.call_count == 1
        assert mock_pyauto.press.call_count == 1

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_with_delays(self, mock_pyauto, mock_time):
        result = tool_key_sequence(
            sequence=[
                {"action": "press", "keys": ["enter"], "delay": 0.5},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        mock_time.sleep.assert_called_once_with(0.5)

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_type_sequence(self, mock_pyauto, mock_time):
        result = tool_key_sequence(
            sequence=[
                {"action": "type", "text": "hello", "interval": 0.02},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.typewrite.assert_called_once_with("hello", interval=0.02)

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_hold_sequence(self, mock_pyauto, mock_time):
        result = tool_key_sequence(
            sequence=[
                {"action": "hold", "keys": ["shift"], "hold_seconds": 1.0},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.keyDown.assert_called_once_with("shift")
        mock_pyauto.keyUp.assert_called_once_with("shift")

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_unknown_action(self, mock_pyauto, mock_time):
        result = tool_key_sequence(
            sequence=[
                {"action": "invalid_action"},
            ]
        )
        data = json.loads(result)
        assert data["steps"][0]["success"] is False

    @patch("control_mcp.tools.keyboard.time")
    @patch("control_mcp.tools.keyboard.pyautogui")
    def test_mixed_sequence(self, mock_pyauto, mock_time):
        result = tool_key_sequence(
            sequence=[
                {"action": "press", "keys": ["ctrl", "a"], "delay": 0.2},
                {"action": "type", "text": "replaced", "delay": 0.1},
                {"action": "press", "keys": ["enter"], "delay": 0},
            ]
        )
        data = json.loads(result)
        assert data["success"] is True
        assert len(data["steps"]) == 3
