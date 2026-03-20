"""Screen capture MCP tools."""

from __future__ import annotations

import json

from control_mcp.utils.capture import (
    capture_full_screen,
    capture_region,
    get_monitors,
)
from control_mcp.schemas.responses import OperationResult


def tool_capture_screen(
    save_dir: str | None = None,
    monitor: int | None = None,
) -> str:
    """Capture the full screen or a specific monitor.

    Parameters
    ----------
    save_dir:
        Directory to save the screenshot. Defaults to system temp directory.
    monitor:
        1-based monitor index. None = virtual screen (all monitors combined).
    """
    result = capture_full_screen(save_dir=save_dir, monitor_index=monitor)
    return result.to_json()


def tool_capture_region(
    x: int,
    y: int,
    width: int,
    height: int,
    save_dir: str | None = None,
) -> str:
    """Capture a rectangular region of the screen.

    Parameters
    ----------
    x:
        Left edge x-coordinate (pixels from left of screen).
    y:
        Top edge y-coordinate (pixels from top of screen).
    width:
        Width of the capture region in pixels.
    height:
        Height of the capture region in pixels.
    save_dir:
        Directory to save the screenshot.
    """
    result = capture_region(x, y, width, height, save_dir=save_dir)
    return result.to_json()


def tool_get_screen_info() -> str:
    """Get information about all connected monitors (resolution, position)."""
    monitors = get_monitors()
    data = {"monitors": [m.to_dict() for m in monitors]}
    return json.dumps(data, ensure_ascii=False)
