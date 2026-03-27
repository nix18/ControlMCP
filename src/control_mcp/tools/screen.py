"""Screen capture MCP tools."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

from control_mcp.tools.grid import remember_grid_capture
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
    grid_rows: int | None = None,
    grid_cols: int | None = None,
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
        save_dir=save_dir,
        monitor_index=monitor,
        quality=quality,
        max_width=max_width,
        grid_rows=grid_rows,
        grid_cols=grid_cols,
    )
    if result.grid_rows and result.grid_cols:
        remember_grid_capture(result.to_dict())
    return result.to_json()


def tool_capture_region(
    x: int,
    y: int,
    width: int,
    height: int,
    save_dir: str | None = None,
    quality: int = 80,
    max_width: int | None = None,
    grid_rows: int | None = None,
    grid_cols: int | None = None,
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
        x,
        y,
        width,
        height,
        save_dir=save_dir,
        quality=quality,
        max_width=max_width,
        grid_rows=grid_rows,
        grid_cols=grid_cols,
    )
    if result.grid_rows and result.grid_cols:
        remember_grid_capture(result.to_dict())
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


def tool_read_screenshot_base64(file_path: str, as_data_url: bool = False) -> str:
    """Read a screenshot file and return its Base64 representation.

    Useful for models that cannot directly consume attached images but can process
    text payloads.
    """
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"Screenshot file does not exist: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    payload = {
        "success": True,
        "file_path": str(path),
        "mime_type": mime_type,
        "base64": encoded,
        "size_bytes": path.stat().st_size,
    }
    if as_data_url:
        payload["data_url"] = f"data:{mime_type};base64,{encoded}"
    return json.dumps(payload, ensure_ascii=False)
