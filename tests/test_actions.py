"""Tests for additional action tools (mocked)."""

import json
from unittest.mock import patch, MagicMock

from control_mcp.tools.actions import (
    tool_clipboard_get,
    tool_clipboard_set,
    tool_launch_app,
    tool_launch_url,
    tool_wait,
    tool_get_pixel_color,
    tool_hotkey,
)


class TestClipboard:
    @patch("control_mcp.tools.actions.pyperclip", create=True)
    def test_clipboard_get(self, mock_pyperclip):
        mock_pyperclip.paste.return_value = "clipboard text"
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            result = tool_clipboard_get()
        data = json.loads(result)
        assert data["success"] is True
        assert data["content"] == "clipboard text"

    @patch("control_mcp.tools.actions.pyperclip", create=True)
    def test_clipboard_set(self, mock_pyperclip):
        mock_pyperclip.copy.return_value = None
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            result = tool_clipboard_set("new text")
        data = json.loads(result)
        assert data["success"] is True
        mock_pyperclip.copy.assert_called_once_with("new text")

    def test_clipboard_get_no_pyperclip(self):
        with patch.dict("sys.modules", {"pyperclip": None}):
            result = tool_clipboard_get()
        data = json.loads(result)
        assert data["success"] is False
        assert "pyperclip" in data["message"]


class TestLaunchApp:
    @patch("control_mcp.tools.actions.subprocess")
    @patch("control_mcp.tools.actions.platform")
    def test_windows(self, mock_platform, mock_subprocess):
        mock_platform.system.return_value = "Windows"
        result = tool_launch_app("notepad")
        data = json.loads(result)
        assert data["success"] is True
        mock_subprocess.Popen.assert_called_once_with("notepad", shell=True)

    @patch("control_mcp.tools.actions.subprocess")
    @patch("control_mcp.tools.actions.platform")
    def test_macos(self, mock_platform, mock_subprocess):
        mock_platform.system.return_value = "Darwin"
        result = tool_launch_app("TextEdit")
        data = json.loads(result)
        assert data["success"] is True
        mock_subprocess.Popen.assert_called_once_with(["open", "-a", "TextEdit"])

    @patch("control_mcp.tools.actions.subprocess")
    @patch("control_mcp.tools.actions.platform")
    def test_failure(self, mock_platform, mock_subprocess):
        mock_platform.system.return_value = "Linux"
        mock_subprocess.Popen.side_effect = Exception("launch fail")
        result = tool_launch_app("bad_cmd")
        data = json.loads(result)
        assert data["success"] is False


class TestLaunchUrl:
    @patch("control_mcp.tools.actions.webbrowser")
    def test_success(self, mock_webbrowser):
        result = tool_launch_url("https://example.com")
        data = json.loads(result)
        assert data["success"] is True
        mock_webbrowser.open.assert_called_once_with("https://example.com")

    @patch("control_mcp.tools.actions.webbrowser")
    def test_failure(self, mock_webbrowser):
        mock_webbrowser.open.side_effect = Exception("browser fail")
        result = tool_launch_url("bad://url")
        data = json.loads(result)
        assert data["success"] is False


class TestWait:
    @patch("control_mcp.tools.actions.time")
    def test_wait(self, mock_time):
        result = tool_wait(2.5)
        data = json.loads(result)
        assert data["success"] is True
        mock_time.sleep.assert_called_once_with(2.5)


class TestGetPixelColor:
    @patch("control_mcp.tools.actions.pyautogui")
    def test_success(self, mock_pyauto):
        mock_pyauto.pixel.return_value = (255, 128, 0)
        result = tool_get_pixel_color(x=500, y=300)
        data = json.loads(result)
        assert data["r"] == 255
        assert data["g"] == 128
        assert data["b"] == 0
        assert data["hex"] == "#ff8000"

    @patch("control_mcp.tools.actions.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.pixel.side_effect = Exception("pixel fail")
        result = tool_get_pixel_color(x=-1, y=-1)
        data = json.loads(result)
        assert "error" in data


class TestHotkey:
    @patch("control_mcp.tools.actions.pyautogui")
    def test_success(self, mock_pyauto):
        result = tool_hotkey("ctrl", "c")
        data = json.loads(result)
        assert data["success"] is True
        mock_pyauto.hotkey.assert_called_once_with("ctrl", "c")

    @patch("control_mcp.tools.actions.pyautogui")
    def test_failure(self, mock_pyauto):
        mock_pyauto.hotkey.side_effect = Exception("hotkey fail")
        result = tool_hotkey("bad", "combo")
        data = json.loads(result)
        assert data["success"] is False
