"""Screen capture MCP tools."""

from __future__ import annotations

import json

from control_mcp.utils.capture import (
    capture_full_screen,
    capture_region,
    capture_scroll_region,
    get_monitors,
)


def tool_capture_screen(
    save_dir: str | None = None,
    monitor: int | None = None,
    quality: int = 80,
    max_width: int | None = None,
) -> str:
    """Capture the full screen or a specific monitor.

    Parameters
    ----------
    save_dir:
        Directory to save the screenshot. Defaults to system temp directory.
    monitor:
        1-based monitor index. None = virtual screen (all monitors combined).
    quality:
        JPEG quality 1-100. Default 80 (~5-8x smaller than PNG, visually lossless).
        Set to 100 for lossless PNG. Lower values = smaller files.
    max_width:
        Scale image to this max width (preserving aspect ratio).
        E.g. 960 halves a 1920-wide screen. Reduces token cost for LLM analysis.
    """
    result = capture_full_screen(
        save_dir=save_dir, monitor_index=monitor, quality=quality, max_width=max_width
    )
    return result.to_json()


def tool_capture_region(
    x: int,
    y: int,
    width: int,
    height: int,
    save_dir: str | None = None,
    quality: int = 80,
    max_width: int | None = None,
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
    quality:
        JPEG quality 1-100. Default 80. 100 = PNG lossless.
    max_width:
        Scale image to this max width (preserving aspect ratio).
    """
    result = capture_region(
        x, y, width, height, save_dir=save_dir, quality=quality, max_width=max_width
    )
    return result.to_json()


def tool_capture_scroll_region(
    x: int,
    y: int,
    width: int,
    height: int,
    scroll_distance: int,
    save_dir: str | None = None,
    quality: int = 80,
    max_width: int | None = None,
) -> str:
    """Capture a scrollable screen region and stitch it into one long image."""
    result = capture_scroll_region(
        x=x,
        y=y,
        width=width,
        height=height,
        scroll_distance=scroll_distance,
        save_dir=save_dir,
        quality=quality,
        max_width=max_width,
    )
    return result.to_json()


def tool_get_screen_info() -> str:
    """Get information about all connected monitors (resolution, position)."""
    monitors = get_monitors()
    data = {"monitors": [m.to_dict() for m in monitors]}
    return json.dumps(data, ensure_ascii=False)
