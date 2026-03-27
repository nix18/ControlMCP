"""Tests for window management tools (mocked)."""

import json
from unittest.mock import MagicMock, patch

import pygetwindow as gw
import pytest

from control_mcp.tools.window import (
    tool_capture_window,
    tool_find_windows,
    tool_focus_window,
    tool_list_windows,
)
from control_mcp.utils import _win_window

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


class TestWindowsFocusFallback:
    @patch("control_mcp.utils._win_window._force_foreground")
    def test_falls_back_when_activate_does_not_reach_foreground(self, mock_force):
        window = MagicMock()
        window.title = "Notepad"
        window._hWnd = 100
        window.isMinimized = False
        mock_force.return_value = True

        with (
            patch("control_mcp.utils._win_window.gw.getAllWindows", return_value=[window]),
            patch("control_mcp.utils._win_window._is_foreground", return_value=False),
        ):
            assert _win_window.focus_window("Notepad") is True

        mock_force.assert_called_once_with(100)

    @patch("control_mcp.utils._win_window._force_foreground")
    def test_falls_back_when_activate_raises(self, mock_force):
        window = MagicMock()
        window.title = "Notepad"
        window._hWnd = 200
        window.isMinimized = True
        window.activate.side_effect = gw.PyGetWindowException("boom")
        mock_force.return_value = True

        with patch("control_mcp.utils._win_window.gw.getAllWindows", return_value=[window]):
            assert _win_window.focus_window("Notepad") is True

        window.restore.assert_called_once()
        mock_force.assert_called_once_with(200)


class TestWindowsFocusSemantics:
    @patch("control_mcp.utils._win_window.time.sleep")
    def test_ready_requires_consistently_visible_foreground(self, _mock_sleep):
        with (
            patch(
                "control_mcp.utils._win_window._is_window_presented",
                side_effect=[True, True, False],
            ),
            patch("control_mcp.utils._win_window._is_foreground", side_effect=[True, True, True]),
        ):
            assert _win_window._is_ready(123) is False

    @patch("control_mcp.utils._win_window.time.sleep")
    def test_ready_passes_only_after_all_checks(self, _mock_sleep):
        attempts = _win_window._READY_CHECK_ATTEMPTS
        with (
            patch(
                "control_mcp.utils._win_window._is_window_presented",
                side_effect=[True] * attempts,
            ),
            patch(
                "control_mcp.utils._win_window._is_foreground",
                side_effect=[True] * attempts,
            ),
            patch("control_mcp.utils._win_window._USER32.BringWindowToTop") as mock_bring_to_top,
        ):
            assert _win_window._is_ready(456) is True

        mock_bring_to_top.assert_called_once_with(456)


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
        mock_capture.assert_called_once_with(
            "Notepad",
            save_dir=None,
            quality=80,
            max_width=None,
            grid_rows=None,
            grid_cols=None,
        )
        data = json.loads(result)
        assert "Notepad" in data["window_title"]

    @patch("control_mcp.tools.window.capture_window")
    def test_with_save_dir(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_window(
            "Chrome",
            save_dir="/screenshots",
            quality=75,
            max_width=900,
            grid_rows=3,
            grid_cols=3,
        )
        mock_capture.assert_called_once_with(
            "Chrome",
            save_dir="/screenshots",
            quality=75,
            max_width=900,
            grid_rows=3,
            grid_cols=3,
        )

    @patch("control_mcp.tools.window.capture_window")
    def test_not_found_raises(self, mock_capture):
        mock_capture.side_effect = ValueError("No window found")
        with pytest.raises(ValueError, match="No window found"):
            tool_capture_window("missing_window")
