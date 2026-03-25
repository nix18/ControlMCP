"""Window management MCP tools."""

from __future__ import annotations

import json

from control_mcp.utils.capture import (
    capture_window,
    find_windows,
    focus_window,
    list_windows,
)


def tool_list_windows() -> str:
    """List all visible windows on the desktop.

    Returns a JSON array of window objects with title, position, and size.
    """
    windows = list_windows()
    return json.dumps({"windows": windows}, ensure_ascii=False, default=str)


def tool_find_windows(title_contains: str) -> str:
    """Find windows by partial title match (case-insensitive).

    Parameters
    ----------
    title_contains:
        Substring to search for in window titles.
    """
    windows = find_windows(title_contains)
    return json.dumps({"windows": windows, "count": len(windows)}, ensure_ascii=False, default=str)


def tool_focus_window(title: str) -> str:
    """Bring a window to the foreground by title (partial, case-insensitive match).

    Parameters
    ----------
    title:
        Substring of the window title to focus.
    """
    ok = focus_window(title)
    return json.dumps({"success": ok, "title": title}, ensure_ascii=False)


def tool_capture_window(
    title: str,
    save_dir: str | None = None,
    quality: int = 80,
    max_width: int | None = None,
    grid_rows: int | None = None,
    grid_cols: int | None = None,
) -> str:
    """Focus a window and capture a screenshot of it.

    The window is brought to the front before the screenshot is taken.

    Parameters
    ----------
    title:
        Substring of the window title to capture.
    save_dir:
        Directory to save the screenshot.
    quality:
        JPEG quality 1-100. Default 80. 100 = PNG lossless.
    max_width:
        Scale image to this max width (preserving aspect ratio).
    """
    result = capture_window(
        title,
        save_dir=save_dir,
        quality=quality,
        max_width=max_width,
        grid_rows=grid_rows,
        grid_cols=grid_cols,
    )
    return result.to_json()
