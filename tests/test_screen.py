"""Tests for screen capture tools (mocked)."""

import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from control_mcp.tools.screen import tool_capture_screen, tool_capture_region, tool_get_screen_info


class TestToolCaptureScreen:
    @patch("control_mcp.tools.screen.capture_full_screen")
    def test_default(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = '{"file_path": "/tmp/test.png"}'
        mock_capture.return_value = mock_result

        result = tool_capture_screen()
        mock_capture.assert_called_once_with(save_dir=None, monitor_index=None)
        assert "test.png" in result

    @patch("control_mcp.tools.screen.capture_full_screen")
    def test_with_params(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_screen(save_dir="/custom", monitor=2)
        mock_capture.assert_called_once_with(save_dir="/custom", monitor_index=2)


class TestToolCaptureRegion:
    @patch("control_mcp.tools.screen.capture_region")
    def test_basic(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = '{"width": 800}'
        mock_capture.return_value = mock_result

        result = tool_capture_region(x=100, y=200, width=800, height=600)
        mock_capture.assert_called_once_with(100, 200, 800, 600, save_dir=None)
        assert "800" in result

    @patch("control_mcp.tools.screen.capture_region")
    def test_with_save_dir(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_region(x=0, y=0, width=100, height=100, save_dir="/screenshots")
        mock_capture.assert_called_once_with(0, 0, 100, 100, save_dir="/screenshots")


class TestToolGetScreenInfo:
    @patch("control_mcp.tools.screen.get_monitors")
    def test_returns_json(self, mock_monitors):
        mock_monitor = MagicMock()
        mock_monitor.to_dict.return_value = {"index": 1, "width": 1920, "height": 1080}
        mock_monitors.return_value = [mock_monitor]

        result = tool_get_screen_info()
        data = json.loads(result)
        assert len(data["monitors"]) == 1
        assert data["monitors"][0]["width"] == 1920

    @patch("control_mcp.tools.screen.get_monitors")
    def test_empty_monitors(self, mock_monitors):
        mock_monitors.return_value = []
        result = tool_get_screen_info()
        data = json.loads(result)
        assert data["monitors"] == []
