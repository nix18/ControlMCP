"""Structured response schemas for ControlMCP tools."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Generic response helpers
# ---------------------------------------------------------------------------


@dataclass
class OperationResult:
    """Result of any atomic or composite operation."""

    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Screenshot responses
# ---------------------------------------------------------------------------


@dataclass
class ScreenshotResult:
    """Structured result of a screenshot operation."""

    file_path: str
    timestamp: str  # ISO-8601
    width: int
    height: int
    x: int = 0  # top-left x of captured region
    y: int = 0  # top-left y of captured region
    monitor_index: int | None = None
    file_size: int = 0  # bytes
    quality: int = 80  # JPEG quality (100 = PNG lossless)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WindowScreenshotResult:
    """Screenshot result that also carries window geometry."""

    file_path: str
    timestamp: str
    window_title: str
    window_x: int
    window_y: int
    window_width: int
    window_height: int
    screenshot_width: int
    screenshot_height: int
    file_size: int = 0
    quality: int = 80

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Window listing responses
# ---------------------------------------------------------------------------


@dataclass
class WindowInfo:
    """Information about a single window."""

    title: str
    x: int
    y: int
    width: int
    height: int
    is_visible: bool = True
    is_minimized: bool = False
    process_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WindowListResult:
    """Result of listing windows."""

    windows: list[WindowInfo] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Mouse / Keyboard action responses
# ---------------------------------------------------------------------------


@dataclass
class ClickResult:
    """Result of a mouse click operation."""

    success: bool
    x: int
    y: int
    clicks: int
    button: str
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DragResult:
    """Result of a mouse drag operation."""

    success: bool
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    button: str
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KeyResult:
    """Result of a keyboard operation."""

    success: bool
    keys: list[str]
    action: str  # "press", "hold", "type"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Mouse position
# ---------------------------------------------------------------------------


@dataclass
class MousePosition:
    """Current mouse position."""

    x: int
    y: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Screen info
# ---------------------------------------------------------------------------


@dataclass
class MonitorInfo:
    """Information about a monitor."""

    index: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScreenInfoResult:
    """Result of getting screen information."""

    monitors: list[MonitorInfo] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------


@dataclass
class ClipboardResult:
    """Result of a clipboard operation."""

    success: bool
    content: str = ""
    action: str = ""  # "get" or "set"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Composite action result
# ---------------------------------------------------------------------------


@dataclass
class CompositeActionResult:
    """Result of a composite action (multiple steps)."""

    success: bool
    steps_completed: int
    total_steps: int
    results: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helper: generate filename
# ---------------------------------------------------------------------------


def make_screenshot_filename(
    prefix: str = "screenshot",
    region: tuple[int, int, int, int] | None = None,
    extension: str = "png",
) -> str:
    """Generate a descriptive screenshot filename.

    Format: ``{prefix}_{timestamp}_{WxH}_{x}_{y}.{ext}``
    When *region* is None, coordinates default to ``0_0``.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if region:
        x, y, w, h = region
        return f"{prefix}_{ts}_{w}x{h}_{x}_{y}.{extension}"
    return f"{prefix}_{ts}.{extension}"
