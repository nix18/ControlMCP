"""Windows-specific window operations using pygetwindow and win32gui."""

from __future__ import annotations

from typing import Any

import pygetwindow as gw


def list_windows() -> list[dict[str, Any]]:
    """List all visible, titled windows on Windows."""
    results: list[dict[str, Any]] = []
    for w in gw.getAllWindows():
        if not w.title:
            continue
        results.append(
            {
                "title": w.title,
                "x": w.left,
                "y": w.top,
                "width": w.width,
                "height": w.height,
                "is_visible": w.visible,
                "is_minimized": w.isMinimized,
                "process_name": "",
            }
        )
    return results


def focus_window(title: str) -> bool:
    """Activate the first window whose title contains *title*."""
    matches = _find(title)
    if not matches:
        return False
    w = matches[0]
    if w.isMinimized:
        w.restore()
    w.activate()
    return True


def find_and_get_geometry(title: str) -> dict[str, Any] | None:
    """Return geometry dict for the first window matching *title*, or None."""
    matches = _find(title)
    if not matches:
        return None
    w = matches[0]
    return {
        "title": w.title,
        "x": w.left,
        "y": w.top,
        "width": w.width,
        "height": w.height,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find(title: str) -> list[gw.Win32Window]:
    needle = title.lower()
    return [w for w in gw.getAllWindows() if w.title and needle in w.title.lower()]
