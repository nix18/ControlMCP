"""Platform-agnostic screen / window capture utilities."""

from __future__ import annotations

import os
import platform
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any

import mss
from PIL import Image

from control_mcp.schemas.responses import (
    MonitorInfo,
    ScreenshotResult,
    WindowScreenshotResult,
    make_screenshot_filename,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DIR = Path(tempfile.gettempdir()) / "control_mcp_screenshots"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _resize_if_needed(img: Image.Image, max_width: int | None) -> tuple[Image.Image, float]:
    """Resize image if width exceeds max_width. Returns (resized_img, scale_factor)."""
    if max_width is None or img.width <= max_width:
        return img, 1.0
    scale = max_width / img.width
    new_height = int(img.height * scale)
    return img.resize((max_width, new_height), Image.LANCZOS), scale


def _save_image(
    img: Image.Image,
    save_path: Path,
    filename: str,
    quality: int,
) -> tuple[str, int]:
    """Save image as JPEG (if quality < 100) or PNG. Returns (filepath, file_size)."""
    if quality < 100:
        jpeg_name = filename.rsplit(".", 1)[0] + ".jpg"
        filepath = save_path / jpeg_name
        img.save(str(filepath), "JPEG", quality=quality, optimize=True)
    else:
        filepath = save_path / filename
        img.save(str(filepath), "PNG")
    return str(filepath), filepath.stat().st_size


def capture_full_screen(
    save_dir: str | Path | None = None,
    monitor_index: int | None = None,
    quality: int = 80,
    max_width: int | None = None,
) -> ScreenshotResult:
    """Capture the full screen (or a specific monitor).

    Parameters
    ----------
    save_dir:
        Directory to save the screenshot. Defaults to ``/tmp/control_mcp_screenshots``.
    monitor_index:
        1-based monitor index. ``None`` means the "virtual screen" (all monitors).
    quality:
        JPEG quality (1-100). 100 = PNG (lossless). Default 80 for ~5-8x smaller files.
    max_width:
        If set, scale image down to this max width (preserving aspect ratio).
        Useful for reducing token cost when LLM analyzes the screenshot.
    """
    save_path = _ensure_dir(Path(save_dir) if save_dir else _DEFAULT_DIR)

    with mss.mss() as sct:
        if monitor_index is not None:
            mon = sct.monitors[monitor_index]
        else:
            mon = sct.monitors[0]

        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        img, scale = _resize_if_needed(img, max_width)

        filename = make_screenshot_filename(
            prefix="screen",
            region=(mon["left"], mon["top"], mon["width"], mon["height"]),
        )
        filepath, file_size = _save_image(img, save_path, filename, quality)

        return ScreenshotResult(
            file_path=str(filepath),
            timestamp=datetime.now().isoformat(),
            width=img.width,
            height=img.height,
            x=mon["left"],
            y=mon["top"],
            monitor_index=monitor_index,
            file_size=file_size,
            quality=quality,
        )


def capture_region(
    x: int,
    y: int,
    width: int,
    height: int,
    save_dir: str | Path | None = None,
    quality: int = 80,
    max_width: int | None = None,
) -> ScreenshotResult:
    """Capture a rectangular region of the screen.

    Parameters
    ----------
    x, y:
        Top-left corner of the region (screen coordinates).
    width, height:
        Size of the region in pixels.
    save_dir:
        Directory to save the screenshot.
    quality:
        JPEG quality (1-100). 100 = PNG (lossless).
    max_width:
        If set, scale image down to this max width.
    """
    save_path = _ensure_dir(Path(save_dir) if save_dir else _DEFAULT_DIR)

    region = {"left": x, "top": y, "width": width, "height": height}

    with mss.mss() as sct:
        raw = sct.grab(region)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        img, scale = _resize_if_needed(img, max_width)

        filename = make_screenshot_filename(
            prefix="region",
            region=(x, y, width, height),
        )
        filepath, file_size = _save_image(img, save_path, filename, quality)

        return ScreenshotResult(
            file_path=str(filepath),
            timestamp=datetime.now().isoformat(),
            width=width,
            height=height,
            x=x,
            y=y,
            file_size=file_size,
            quality=quality,
        )


def get_monitors() -> list[MonitorInfo]:
    """Return information about all connected monitors."""
    monitors: list[MonitorInfo] = []
    with mss.mss() as sct:
        for idx, mon in enumerate(sct.monitors):
            if idx == 0:
                # monitors[0] is the virtual screen — skip it
                continue
            monitors.append(
                MonitorInfo(
                    index=idx,
                    x=mon["left"],
                    y=mon["top"],
                    width=mon["width"],
                    height=mon["height"],
                    is_primary=(idx == 1),
                )
            )
    return monitors


# ---------------------------------------------------------------------------
# Window capture (platform-specific backend selection)
# ---------------------------------------------------------------------------


def _get_platform_window_backend():
    """Return the platform-specific window operations module."""
    system = platform.system()
    if system == "Windows":
        from control_mcp.utils import _win_window as backend

        return backend
    elif system == "Darwin":
        from control_mcp.utils import _mac_window as backend

        return backend
    elif system == "Linux":
        from control_mcp.utils import _linux_window as backend

        return backend
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def list_windows() -> list[dict[str, Any]]:
    """List all visible windows. Returns list of dicts with title, geometry, etc."""
    backend = _get_platform_window_backend()
    return backend.list_windows()


def find_windows(title_contains: str | None = None) -> list[dict[str, Any]]:
    """Find windows by (partial) title match.

    Parameters
    ----------
    title_contains:
        Substring to search for in window titles (case-insensitive).
        If ``None``, returns all windows.
    """
    windows = list_windows()
    if title_contains is None:
        return windows
    needle = title_contains.lower()
    return [w for w in windows if needle in w.get("title", "").lower()]


def focus_window(title: str) -> bool:
    """Bring the window whose title matches *title* (exact or substring) to front.

    Returns ``True`` if a window was found and focused.
    """
    backend = _get_platform_window_backend()
    return backend.focus_window(title)


def capture_window(
    title: str,
    save_dir: str | Path | None = None,
    quality: int = 80,
    max_width: int | None = None,
) -> WindowScreenshotResult:
    """Capture the first window whose title contains *title* (case-insensitive).

    Also brings the window to front (focus) before capturing.

    Parameters
    ----------
    title:
        Substring to match against window titles.
    save_dir:
        Directory to save the screenshot.
    quality:
        JPEG quality (1-100). 100 = PNG (lossless). Default 80.
    max_width:
        If set, scale image down to this max width.

    Raises
    ------
    ValueError
        If no matching window is found.
    """
    backend = _get_platform_window_backend()
    save_path = _ensure_dir(Path(save_dir) if save_dir else _DEFAULT_DIR)

    win = backend.find_and_get_geometry(title)
    if win is None:
        raise ValueError(f"No window found matching '{title}'")

    # Focus the window first
    backend.focus_window(title)

    # Small delay to allow the window to come to front
    import time

    time.sleep(0.2)

    # Capture the region
    region = {
        "left": win["x"],
        "top": win["y"],
        "width": win["width"],
        "height": win["height"],
    }

    with mss.mss() as sct:
        raw = sct.grab(region)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        img, scale = _resize_if_needed(img, max_width)

        filename = make_screenshot_filename(
            prefix="window",
            region=(win["x"], win["y"], win["width"], win["height"]),
        )
        filepath, file_size = _save_image(img, save_path, filename, quality)

        return WindowScreenshotResult(
            file_path=str(filepath),
            timestamp=datetime.now().isoformat(),
            window_title=win.get("title", title),
            window_x=win["x"],
            window_y=win["y"],
            window_width=win["width"],
            window_height=win["height"],
            screenshot_width=img.width,
            screenshot_height=img.height,
            file_size=file_size,
            quality=quality,
        )
