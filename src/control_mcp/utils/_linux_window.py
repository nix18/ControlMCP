"""Linux-specific window operations using python-xlib."""

from __future__ import annotations

from contextlib import suppress
from typing import Any


def list_windows() -> list[dict[str, Any]]:
    """List all visible windows on Linux via Xlib."""
    try:
        from Xlib import X, display
    except ImportError:
        return []

    d = display.Display()
    root = d.screen().root

    # Get list of client windows via _NET_CLIENT_LIST
    client_list = root.get_full_property(
        d.intern_atom("_NET_CLIENT_LIST"),
        X.AnyPropertyType,
    )
    if client_list is None:
        return []

    results: list[dict[str, Any]] = []
    for win_id in client_list.value:
        win = d.create_resource_object("window", win_id)
        try:
            geom = win.get_geometry()
            name_prop = win.get_full_property(
                d.intern_atom("_NET_WM_NAME"),
                d.intern_atom("UTF8_STRING"),
            )
            title = name_prop.value.decode("utf-8", errors="replace") if name_prop else ""
            if not title:
                with suppress(Exception):
                    title = win.get_wm_name() or ""
            results.append(
                {
                    "title": title,
                    "x": geom.x,
                    "y": geom.y,
                    "width": geom.width,
                    "height": geom.height,
                    "is_visible": True,
                    "is_minimized": False,
                    "process_name": "",
                }
            )
        except Exception:
            continue

    d.close()
    return results


def focus_window(title: str) -> bool:
    """Activate the first window whose title contains *title*."""
    try:
        from Xlib import X, display
    except ImportError:
        return False

    d = display.Display()
    root = d.screen().root

    client_list = root.get_full_property(
        d.intern_atom("_NET_CLIENT_LIST"),
        X.AnyPropertyType,
    )
    if client_list is None:
        d.close()
        return False

    needle = title.lower()
    for win_id in client_list.value:
        win = d.create_resource_object("window", win_id)
        try:
            name_prop = win.get_full_property(
                d.intern_atom("_NET_WM_NAME"),
                d.intern_atom("UTF8_STRING"),
            )
            wt = name_prop.value.decode("utf-8", errors="replace") if name_prop else ""
            if needle in wt.lower():
                # Use _NET_ACTIVE_WINDOW to activate
                root.send_event(
                    event=property.PropertyNotify(
                        window=win,
                        atom=d.intern_atom("_NET_ACTIVE_WINDOW"),
                        time=0,
                    ),
                )
                # Fallback: use xdotool if available
                import subprocess

                subprocess.run(
                    ["xdotool", "search", "--name", title, "windowactivate"],
                    capture_output=True,
                    timeout=5,
                )
                d.close()
                return True
        except Exception:
            continue

    d.close()
    return False


def find_and_get_geometry(title: str) -> dict[str, Any] | None:
    """Return geometry dict for the first window matching *title*, or None."""
    windows = list_windows()
    needle = title.lower()
    for w in windows:
        if needle in w.get("title", "").lower():
            return {
                "title": w["title"],
                "x": w["x"],
                "y": w["y"],
                "width": w["width"],
                "height": w["height"],
            }
    return None
