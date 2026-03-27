"""Tests for grid-assisted targeting helpers."""

import json

import pytest

from control_mcp.tools.grid import clear_remembered_grid_capture, tool_resolve_grid_target
from control_mcp.utils.capture import _draw_grid_overlay, _normalize_grid


def setup_function() -> None:
    clear_remembered_grid_capture()


def test_normalize_grid_requires_both_values():
    with pytest.raises(ValueError, match="provided together"):
        _normalize_grid(3, None)


def test_draw_grid_overlay_preserves_size():
    from PIL import Image

    image = Image.new("RGB", (300, 200), color=(255, 255, 255))
    overlay = _draw_grid_overlay(image, 3, 4)
    assert overlay.size == image.size


def test_resolve_grid_target_center_anchor():
    payload = json.loads(
        tool_resolve_grid_target(
            base_x=100,
            base_y=200,
            image_width=400,
            image_height=300,
            grid_rows=3,
            grid_cols=4,
            cell=6,
            anchor="center",
        )
    )
    assert payload["row"] == 2
    assert payload["col"] == 2
    assert payload["screen_x"] == 250
    assert payload["screen_y"] == 350


def test_resolve_grid_target_top_left_anchor():
    payload = json.loads(
        tool_resolve_grid_target(
            base_x=0,
            base_y=0,
            image_width=200,
            image_height=100,
            grid_rows=2,
            grid_cols=2,
            cell=1,
            anchor="top_left",
        )
    )
    assert payload["screen_x"] == 20
    assert payload["screen_y"] == 10


def test_resolve_grid_target_rejects_invalid_cell():
    with pytest.raises(ValueError, match="grid range"):
        tool_resolve_grid_target(
            base_x=0,
            base_y=0,
            image_width=200,
            image_height=100,
            grid_rows=2,
            grid_cols=2,
            cell=5,
        )


def test_click_grid_target_uses_capture_metadata():
    from unittest.mock import patch

    from control_mcp.tools.grid import tool_click_grid_target

    capture = {
        "window_x": 100,
        "window_y": 200,
        "screenshot_width": 400,
        "screenshot_height": 300,
        "grid_rows": 3,
        "grid_cols": 4,
    }
    with patch("control_mcp.tools.grid.tool_mouse_click") as mock_click:
        mock_click.return_value = '{"success": true, "x": 250, "y": 350}'
        payload = json.loads(tool_click_grid_target(capture=capture, cell=6))

    assert payload["resolved_target"]["screen_x"] == 250
    assert payload["resolved_target"]["screen_y"] == 350
    mock_click.assert_called_once()


def test_click_grid_target_move_only_uses_mouse_move():
    from unittest.mock import patch

    from control_mcp.tools.grid import tool_click_grid_target

    capture = {
        "x": 10,
        "y": 20,
        "width": 200,
        "height": 100,
        "grid_rows": 2,
        "grid_cols": 2,
    }
    with patch("control_mcp.tools.grid.tool_mouse_move") as mock_move:
        mock_move.return_value = '{"success": true, "x": 60, "y": 45}'
        payload = json.loads(tool_click_grid_target(capture=capture, cell=1, move_only=True))

    assert payload["action"]["success"] is True
    mock_move.assert_called_once()


def test_click_grid_target_uses_remembered_capture_when_omitted():
    from unittest.mock import patch

    from control_mcp.tools.grid import remember_grid_capture, tool_click_grid_target

    remember_grid_capture(
        {
            "window_x": 100,
            "window_y": 200,
            "screenshot_width": 400,
            "screenshot_height": 300,
            "grid_rows": 3,
            "grid_cols": 4,
        }
    )
    with patch("control_mcp.tools.grid.tool_mouse_click") as mock_click:
        mock_click.return_value = '{"success": true, "x": 250, "y": 250}'
        payload = json.loads(tool_click_grid_target(capture=None, cell=2))

    assert payload["capture_source"] == "remembered"
    assert payload["resolved_target"]["screen_x"] == 250
    mock_click.assert_called_once()


def test_click_grid_target_requires_capture_when_nothing_remembered():
    from control_mcp.tools.grid import tool_click_grid_target

    with pytest.raises(ValueError, match="requires capture metadata"):
        tool_click_grid_target(capture=None, cell=1)


def test_resolve_grid_target_uses_remembered_capture_when_omitted():
    from control_mcp.tools.grid import remember_grid_capture

    remember_grid_capture(
        {"x": 10, "y": 20, "width": 200, "height": 100, "grid_rows": 2, "grid_cols": 2}
    )
    payload = json.loads(tool_resolve_grid_target(cell=1))

    assert payload["capture_source"] == "remembered"
    assert payload["screen_x"] == 60
    assert payload["screen_y"] == 45


def test_click_grid_target_rejects_missing_grid_metadata():
    from control_mcp.tools.grid import tool_click_grid_target

    with pytest.raises(ValueError, match="grid_rows and grid_cols"):
        tool_click_grid_target(capture={"x": 0, "y": 0, "width": 100, "height": 100}, cell=1)
