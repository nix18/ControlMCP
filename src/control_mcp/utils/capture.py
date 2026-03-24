"""Platform-agnostic screen / window capture utilities."""

from __future__ import annotations

import platform
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import mss
import pyautogui
from PIL import Image, ImageChops, ImageStat

from control_mcp.schemas.responses import (
    MonitorInfo,
    ScreenshotResult,
    ScrollScreenshotResult,
    WindowScreenshotResult,
    make_screenshot_filename,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DIR = Path(tempfile.gettempdir()) / "control_mcp_screenshots"
_DEFAULT_SCROLL_CHUNK = 120


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


def _capture_region_image(x: int, y: int, width: int, height: int) -> Image.Image:
    """Capture a screen region and return it as a PIL image."""
    region = {"left": x, "top": y, "width": width, "height": height}
    with mss.mss() as sct:
        raw = sct.grab(region)
    return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def _prepare_match_image(img: Image.Image) -> Image.Image:
    """Reduce image width and side noise to make vertical matching more stable."""
    horizontal_margin = max(0, img.width // 10)
    cropped = img.crop((horizontal_margin, 0, img.width - horizontal_margin, img.height)).convert(
        "L"
    )
    if cropped.width <= 96:
        return cropped
    return cropped.resize((96, cropped.height), Image.BILINEAR)


def _mean_image_difference(left: Image.Image, right: Image.Image) -> float:
    """Return the mean absolute difference between two images."""
    diff = ImageChops.difference(left, right)
    return float(ImageStat.Stat(diff).mean[0])


def _match_strip_offset(
    previous: Image.Image,
    current: Image.Image,
    *,
    scroll_down: bool,
) -> tuple[int, int]:
    """Find where a strip from the previous frame appears in the current frame."""
    previous_match = _prepare_match_image(previous)
    current_match = _prepare_match_image(current)
    sample_height = max(40, min(previous_match.height // 5, 120))

    if previous_match.height <= sample_height or current_match.height <= sample_height:
        return 0, sample_height

    if scroll_down:
        reference = previous_match.crop(
            (0, previous_match.height - sample_height, previous_match.width, previous_match.height)
        )
    else:
        reference = previous_match.crop((0, 0, previous_match.width, sample_height))

    max_offset = max(0, current_match.height - sample_height)
    coarse_step = max(2, sample_height // 12)
    best_offset = 0
    best_score = float("inf")

    for offset in range(0, max_offset + 1, coarse_step):
        candidate = current_match.crop((0, offset, current_match.width, offset + sample_height))
        score = _mean_image_difference(reference, candidate)
        if score < best_score:
            best_score = score
            best_offset = offset

    refine_start = max(0, best_offset - coarse_step)
    refine_end = min(max_offset, best_offset + coarse_step)
    for offset in range(refine_start, refine_end + 1):
        candidate = current_match.crop((0, offset, current_match.width, offset + sample_height))
        score = _mean_image_difference(reference, candidate)
        if score < best_score:
            best_score = score
            best_offset = offset

    return best_offset, sample_height


def _extract_new_scrolled_part(
    previous: Image.Image,
    current: Image.Image,
    *,
    scroll_down: bool,
) -> Image.Image | None:
    """Extract the newly revealed content between two scrolled frames."""
    offset, sample_height = _match_strip_offset(previous, current, scroll_down=scroll_down)

    if scroll_down:
        start_y = min(current.height, offset + sample_height)
        if start_y >= current.height:
            return None
        return current.crop((0, start_y, current.width, current.height))

    end_y = max(0, offset)
    if end_y <= 0:
        return None
    return current.crop((0, 0, current.width, end_y))


def _compose_vertical(parts: list[Image.Image]) -> Image.Image:
    """Join multiple equally wide image parts into a single tall image."""
    if not parts:
        raise ValueError("parts must not be empty")

    total_height = sum(part.height for part in parts)
    width = parts[0].width
    stitched = Image.new("RGB", (width, total_height))

    cursor_y = 0
    for part in parts:
        stitched.paste(part, (0, cursor_y))
        cursor_y += part.height

    return stitched


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
        mon = sct.monitors[monitor_index] if monitor_index is not None else sct.monitors[0]

        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        img, _ = _resize_if_needed(img, max_width)

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

    img = _capture_region_image(x, y, width, height)
    img, _ = _resize_if_needed(img, max_width)

    filename = make_screenshot_filename(
        prefix="region",
        region=(x, y, width, height),
    )
    filepath, file_size = _save_image(img, save_path, filename, quality)

    return ScreenshotResult(
        file_path=str(filepath),
        timestamp=datetime.now().isoformat(),
        width=img.width,
        height=img.height,
        x=x,
        y=y,
        file_size=file_size,
        quality=quality,
    )


def capture_scroll_region(
    x: int,
    y: int,
    width: int,
    height: int,
    scroll_distance: int,
    save_dir: str | Path | None = None,
    quality: int = 80,
    max_width: int | None = None,
    settle_time: float = 0.4,
) -> ScrollScreenshotResult:
    """Capture a fixed screen region while scrolling inside it, then stitch the results."""
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if scroll_distance == 0:
        raise ValueError("scroll_distance must be non-zero")

    save_path = _ensure_dir(Path(save_dir) if save_dir else _DEFAULT_DIR)
    center_x = x + width // 2
    center_y = y + height // 2
    scroll_down = scroll_distance < 0
    remaining = abs(scroll_distance)
    initial = _capture_region_image(x, y, width, height)
    previous = initial
    leading_parts: list[Image.Image] = []
    trailing_parts: list[Image.Image] = []
    capture_count = 1

    while remaining > 0:
        chunk = min(_DEFAULT_SCROLL_CHUNK, remaining)
        signed_chunk = -chunk if scroll_down else chunk

        pyautogui.moveTo(center_x, center_y, duration=0.05)
        pyautogui.scroll(signed_chunk, x=center_x, y=center_y)
        time.sleep(settle_time)

        current = _capture_region_image(x, y, width, height)
        capture_count += 1
        new_part = _extract_new_scrolled_part(previous, current, scroll_down=scroll_down)

        if new_part is None or new_part.height < 8:
            if _mean_image_difference(
                _prepare_match_image(previous), _prepare_match_image(current)
            ) < 0.5:
                break

            fallback_boundary = current.height // 2
            if scroll_down:
                new_part = current.crop((0, fallback_boundary, current.width, current.height))
            else:
                new_part = current.crop((0, 0, current.width, fallback_boundary))

            if new_part.height < 8:
                break

        if scroll_down:
            trailing_parts.append(new_part)
        else:
            leading_parts.insert(0, new_part)

        previous = current
        remaining -= chunk

    stitched = _compose_vertical([*leading_parts, initial, *trailing_parts])
    stitched, _ = _resize_if_needed(stitched, max_width)

    filename = make_screenshot_filename(
        prefix="scroll_region",
        region=(x, y, width, height),
    )
    filepath, file_size = _save_image(stitched, save_path, filename, quality)

    return ScrollScreenshotResult(
        file_path=str(filepath),
        timestamp=datetime.now().isoformat(),
        x=x,
        y=y,
        width=stitched.width,
        height=stitched.height,
        scroll_distance=scroll_distance,
        capture_count=capture_count,
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

        img, _ = _resize_if_needed(img, max_width)

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
