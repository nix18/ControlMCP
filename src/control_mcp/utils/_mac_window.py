"""macOS-specific window operations using Quartz."""

from __future__ import annotations

from typing import Any

import Quartz


def list_windows() -> list[dict[str, Any]]:
    """List all on-screen windows on macOS via Quartz."""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    results: list[dict[str, Any]] = []
    for w in windows:
        bounds = w.get(Quartz.kCGWindowBounds, {})
        name = w.get(Quartz.kCGWindowName, "")
        owner = w.get(Quartz.kCGWindowOwnerName, "")
        layer = w.get(Quartz.kCGWindowLayer, 0)
        if not name and not owner:
            continue
        results.append(
            {
                "title": f"{owner} — {name}" if name else owner,
                "x": int(bounds.get("X", 0)),
                "y": int(bounds.get("Y", 0)),
                "width": int(bounds.get("Width", 0)),
                "height": int(bounds.get("Height", 0)),
                "is_visible": True,
                "is_minimized": False,
                "process_name": owner,
            }
        )
    return results


def focus_window(title: str) -> bool:
    """Raise and focus the first window matching *title*."""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
    )
    needle = title.lower()
    for w in windows:
        name = w.get(Quartz.kCGWindowName, "")
        owner = w.get(Quartz.kCGWindowOwnerName, "")
        combined = f"{owner} {name}".lower()
        if needle in combined:
            win_id = w.get(Quartz.kCGWindowNumber)
            # Use AppleScript as fallback for raising windows on macOS
            import subprocess

            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "{owner}" to activate',
                ],
                capture_output=True,
                timeout=5,
            )
            return True
    return False


def find_and_get_geometry(title: str) -> dict[str, Any] | None:
    """Return geometry dict for the first window matching *title*, or None."""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
    )
    needle = title.lower()
    for w in windows:
        name = w.get(Quartz.kCGWindowName, "")
        owner = w.get(Quartz.kCGWindowOwnerName, "")
        combined = f"{owner} {name}".lower()
        if needle in combined:
            bounds = w.get(Quartz.kCGWindowBounds, {})
            return {
                "title": f"{owner} — {name}" if name else owner,
                "x": int(bounds.get("X", 0)),
                "y": int(bounds.get("Y", 0)),
                "width": int(bounds.get("Width", 0)),
                "height": int(bounds.get("Height", 0)),
            }
    return None
