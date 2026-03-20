"""Tests for window management tools (mocked)."""

import json
from unittest.mock import patch, MagicMock

from control_mcp.tools.window import (
    tool_list_windows,
    tool_find_windows,
    tool_focus_window,
    tool_capture_window,
)

SAMPLE_WINDOWS = [
    {"title": "Notepad", "x": 100, "y": 100, "width": 800, "height": 600},
    {"title": "Chrome - Google", "x": 200, "y": 50, "width": 1024, "height": 768},
    {"title": "VS Code", "x": 0, "y": 0, "width": 1920, "height": 1080},
]


class TestToolListWindows:
    @patch("control_mcp.tools.window.list_windows")
    def test_returns_all_windows(self, mock_list):
        mock_list.return_value = SAMPLE_WINDOWS
        result = tool_list_windows()
        data = json.loads(result)
        assert len(data["windows"]) == 3

    @patch("control_mcp.tools.window.list_windows")
    def test_empty(self, mock_list):
        mock_list.return_value = []
        result = tool_list_windows()
        data = json.loads(result)
        assert data["windows"] == []


class TestToolFindWindows:
    @patch("control_mcp.tools.window.find_windows")
    def test_find_chrome(self, mock_find):
        mock_find.return_value = [SAMPLE_WINDOWS[1]]
        result = tool_find_windows("chrome")
        data = json.loads(result)
        assert data["count"] == 1
        assert "Chrome" in data["windows"][0]["title"]

    @patch("control_mcp.tools.window.find_windows")
    def test_case_insensitive(self, mock_find):
        mock_find.return_value = [SAMPLE_WINDOWS[0]]
        result = tool_find_windows("NOTEPAD")
        data = json.loads(result)
        mock_find.assert_called_once_with("NOTEPAD")
        assert data["count"] == 1

    @patch("control_mcp.tools.window.find_windows")
    def test_no_match(self, mock_find):
        mock_find.return_value = []
        result = tool_find_windows("nonexistent")
        data = json.loads(result)
        assert data["count"] == 0


class TestToolFocusWindow:
    @patch("control_mcp.tools.window.focus_window")
    def test_success(self, mock_focus):
        mock_focus.return_value = True
        result = tool_focus_window("Notepad")
        data = json.loads(result)
        assert data["success"] is True

    @patch("control_mcp.tools.window.focus_window")
    def test_not_found(self, mock_focus):
        mock_focus.return_value = False
        result = tool_focus_window("missing")
        data = json.loads(result)
        assert data["success"] is False


class TestToolCaptureWindow:
    @patch("control_mcp.tools.window.capture_window")
    def test_success(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = json.dumps(
            {
                "file_path": "/tmp/window.png",
                "window_title": "Notepad",
                "window_x": 100,
            }
        )
        mock_capture.return_value = mock_result

        result = tool_capture_window("Notepad")
        mock_capture.assert_called_once_with("Notepad", save_dir=None)
        data = json.loads(result)
        assert "Notepad" in data["window_title"]

    @patch("control_mcp.tools.window.capture_window")
    def test_with_save_dir(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_window("Chrome", save_dir="/screenshots")
        mock_capture.assert_called_once_with("Chrome", save_dir="/screenshots")

    @patch("control_mcp.tools.window.capture_window")
    def test_not_found_raises(self, mock_capture):
        mock_capture.side_effect = ValueError("No window found")
        try:
            tool_capture_window("missing_window")
            assert False, "Should have raised"
        except ValueError:
            pass
