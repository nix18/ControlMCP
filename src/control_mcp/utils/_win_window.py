"""Windows-specific window operations using pygetwindow and win32gui."""

from __future__ import annotations

import ctypes
import time
from typing import Any

import pygetwindow as gw

_USER32 = ctypes.windll.user32
_KERNEL32 = ctypes.windll.kernel32
_SW_RESTORE = 9
_SW_SHOW = 5
_HWND_TOPMOST = -1
_HWND_NOTOPMOST = -2
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_SHOWWINDOW = 0x0040
_READY_CHECK_INTERVAL_SECONDS = 0.2
_READY_CHECK_ATTEMPTS = 6


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
    hwnd = w._hWnd
    try:
        if w.isMinimized:
            w.restore()
        w.activate()
        if _is_ready(hwnd):
            return True
    except gw.PyGetWindowException:
        # pygetwindow may throw even on success (error code 0).
        # Fall back to raw Win32 API.
        pass
    return _force_foreground(hwnd)


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


def _force_foreground(hwnd: int) -> bool:
    """Force a window to the foreground using Win32 API directly.

    Handles cases where SetForegroundWindow is restricted (e.g. background
    process trying to steal focus). Uses AttachThreadInput as a workaround.
    """
    _show_window(hwnd)

    if _raise_window(hwnd) and _is_ready(hwnd):
        return True

    current_tid = _KERNEL32.GetCurrentThreadId()
    foreground_hwnd = _USER32.GetForegroundWindow()
    foreground_tid = _USER32.GetWindowThreadProcessId(foreground_hwnd, None)
    target_tid = _USER32.GetWindowThreadProcessId(hwnd, None)
    attached_threads: list[int] = []

    for thread_id in (foreground_tid, target_tid):
        if (
            thread_id
            and thread_id != current_tid
            and _USER32.AttachThreadInput(current_tid, thread_id, True)
        ):
            attached_threads.append(thread_id)

    try:
        if _raise_window(hwnd) and _is_ready(hwnd):
            return True
    finally:
        for thread_id in reversed(attached_threads):
            _USER32.AttachThreadInput(current_tid, thread_id, False)

    return _is_ready(hwnd)


def _show_window(hwnd: int) -> None:
    if _USER32.IsIconic(hwnd):
        _USER32.ShowWindow(hwnd, _SW_RESTORE)
    else:
        _USER32.ShowWindow(hwnd, _SW_SHOW)


def _raise_window(hwnd: int) -> bool:
    flags = _SWP_NOMOVE | _SWP_NOSIZE | _SWP_SHOWWINDOW
    _USER32.BringWindowToTop(hwnd)
    _USER32.SetWindowPos(hwnd, _HWND_TOPMOST, 0, 0, 0, 0, flags)
    _USER32.SetWindowPos(hwnd, _HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    switch_to_this_window = getattr(_USER32, "SwitchToThisWindow", None)
    if switch_to_this_window is not None:
        switch_to_this_window(hwnd, True)
    _USER32.SetForegroundWindow(hwnd)
    _USER32.SetActiveWindow(hwnd)
    _USER32.SetFocus(hwnd)
    return True


def _is_foreground(hwnd: int) -> bool:
    return _USER32.GetForegroundWindow() == hwnd


def _is_window_presented(hwnd: int) -> bool:
    if not _USER32.IsWindowVisible(hwnd) or _USER32.IsIconic(hwnd):
        return False

    rect = ctypes.wintypes.RECT()
    if not _USER32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False

    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        return False

    screen_left = _USER32.GetSystemMetrics(76)
    screen_top = _USER32.GetSystemMetrics(77)
    screen_width = _USER32.GetSystemMetrics(78)
    screen_height = _USER32.GetSystemMetrics(79)
    screen_right = screen_left + screen_width
    screen_bottom = screen_top + screen_height

    return not (
        rect.right <= screen_left
        or rect.left >= screen_right
        or rect.bottom <= screen_top
        or rect.top >= screen_bottom
    )


def _is_ready(hwnd: int) -> bool:
    for attempt in range(_READY_CHECK_ATTEMPTS):
        time.sleep(_READY_CHECK_INTERVAL_SECONDS)
        if not (_is_window_presented(hwnd) and _is_foreground(hwnd)):
            return False
        if attempt == 0:
            _USER32.BringWindowToTop(hwnd)
    return True
