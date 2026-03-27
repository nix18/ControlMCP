"""Tests for screen capture tools (mocked)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from control_mcp.tools.screen import (
    tool_capture_region,
    tool_capture_screen,
    tool_capture_scroll_region,
    tool_get_screen_info,
    tool_read_screenshot_base64,
)


class TestToolCaptureScreen:
    @patch("control_mcp.tools.screen.capture_full_screen")
    def test_default(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = '{"file_path": "/tmp/test.png"}'
        mock_capture.return_value = mock_result

        result = tool_capture_screen()
        mock_capture.assert_called_once_with(
            save_dir=None,
            monitor_index=None,
            quality=80,
            max_width=None,
            grid_rows=None,
            grid_cols=None,
            sharpen=False,
        )
        assert "test.png" in result

    @patch("control_mcp.tools.screen.capture_full_screen")
    def test_with_params(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_screen(
            save_dir="/custom",
            monitor=2,
            quality=70,
            max_width=960,
            grid_rows=3,
            grid_cols=4,
            sharpen=False,
        )
        mock_capture.assert_called_once_with(
            save_dir="/custom",
            monitor_index=2,
            quality=70,
            max_width=960,
            grid_rows=3,
            grid_cols=4,
            sharpen=False,
        )


class TestToolCaptureRegion:
    @patch("control_mcp.tools.screen.capture_region")
    def test_basic(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = '{"width": 800}'
        mock_capture.return_value = mock_result

        result = tool_capture_region(x=100, y=200, width=800, height=600)
        mock_capture.assert_called_once_with(
            100,
            200,
            800,
            600,
            save_dir=None,
            quality=80,
            max_width=None,
            grid_rows=None,
            grid_cols=None,
            sharpen=False,
        )
        assert "800" in result

    @patch("control_mcp.tools.screen.capture_region")
    def test_with_save_dir(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_region(
            x=0,
            y=0,
            width=100,
            height=100,
            save_dir="/screenshots",
            quality=90,
            max_width=640,
            grid_rows=2,
            grid_cols=5,
            sharpen=False,
        )
        mock_capture.assert_called_once_with(
            0,
            0,
            100,
            100,
            save_dir="/screenshots",
            quality=90,
            max_width=640,
            grid_rows=2,
            grid_cols=5,
            sharpen=False,
        )

    @patch("control_mcp.tools.screen.capture_region")
    def test_with_sharpen(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_region(x=1, y=2, width=3, height=4, sharpen=True)

        mock_capture.assert_called_once_with(
            1,
            2,
            3,
            4,
            save_dir=None,
            quality=80,
            max_width=None,
            grid_rows=None,
            grid_cols=None,
            sharpen=True,
        )


class TestToolCaptureScrollRegion:
    @patch("control_mcp.tools.screen.capture_scroll_region")
    def test_basic(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = '{"capture_count": 3}'
        mock_capture.return_value = mock_result

        result = tool_capture_scroll_region(
            x=10,
            y=20,
            width=300,
            height=400,
            scroll_distance=-480,
        )

        mock_capture.assert_called_once_with(
            x=10,
            y=20,
            width=300,
            height=400,
            scroll_distance=-480,
            save_dir=None,
            quality=80,
            max_width=None,
            sharpen=False,
        )
        assert '"capture_count": 3' in result

    @patch("control_mcp.tools.screen.capture_scroll_region")
    def test_with_optional_params(self, mock_capture):
        mock_result = MagicMock()
        mock_result.to_json.return_value = "{}"
        mock_capture.return_value = mock_result

        tool_capture_scroll_region(
            x=10,
            y=20,
            width=300,
            height=400,
            scroll_distance=360,
            save_dir="/shots",
            quality=75,
            max_width=800,
            sharpen=False,
        )

        mock_capture.assert_called_once_with(
            x=10,
            y=20,
            width=300,
            height=400,
            scroll_distance=360,
            save_dir="/shots",
            quality=75,
            max_width=800,
            sharpen=False,
        )


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


class TestToolReadScreenshotBase64:
    def test_reads_file_as_base64(self, tmp_path):
        image_path = tmp_path / "shot.png"
        image_path.write_bytes(b"fake-image-bytes")

        payload = json.loads(tool_read_screenshot_base64(str(image_path)))

        assert payload["success"] is True
        assert payload["file_path"] == str(image_path)
        assert payload["mime_type"] == "image/png"
        assert payload["base64"] == "ZmFrZS1pbWFnZS1ieXRlcw=="

    def test_can_return_data_url(self, tmp_path):
        image_path = tmp_path / "shot.jpg"
        image_path.write_bytes(b"jpg-bytes")

        payload = json.loads(tool_read_screenshot_base64(str(image_path), as_data_url=True))

        assert payload["data_url"].startswith("data:image/jpeg;base64,")

    def test_rejects_missing_file(self, tmp_path):
        missing_path = tmp_path / "missing.png"

        with pytest.raises(ValueError, match="does not exist"):
            tool_read_screenshot_base64(str(missing_path))
