"""Windows-specific window operations using pygetwindow and win32gui."""

from __future__ import annotations

import ctypes
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
    try:
        if w.isMinimized:
            w.restore()
        w.activate()
    except gw.PyGetWindowException:
        # pygetwindow may throw even on success (error code 0).
        # Fall back to raw Win32 API.
        _force_foreground(w._hWnd)
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


def _force_foreground(hwnd: int) -> None:
    """Force a window to the foreground using Win32 API directly.

    Handles cases where SetForegroundWindow is restricted (e.g. background
    process trying to steal focus). Uses AttachThreadInput as a workaround.
    """
    user32 = ctypes.windll.user32

    # If minimized, restore first
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE

    # Try direct SetForegroundWindow first
    if user32.SetForegroundWindow(hwnd):
        return

    # Fallback: attach our thread to the foreground thread
    current_tid = user32.GetCurrentThreadId()
    foreground_hwnd = user32.GetForegroundWindow()
    foreground_tid = user32.GetWindowThreadProcessId(foreground_hwnd, None)

    if current_tid != foreground_tid:
        user32.AttachThreadInput(current_tid, foreground_tid, True)
        try:
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
        finally:
            user32.AttachThreadInput(current_tid, foreground_tid, False)
    else:
        user32.BringWindowToTop(hwnd)
