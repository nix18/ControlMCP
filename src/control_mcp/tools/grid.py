"""Grid-based screenshot targeting helpers."""

from __future__ import annotations

import json

from control_mcp.tools.mouse import tool_mouse_click, tool_mouse_move

_LAST_GRID_CAPTURE: dict | None = None

_ANCHOR_MAP: dict[str, tuple[float, float]] = {
    "center": (0.5, 0.5),
    "top_left": (0.2, 0.2),
    "top": (0.5, 0.2),
    "top_right": (0.8, 0.2),
    "right": (0.8, 0.5),
    "bottom_right": (0.8, 0.8),
    "bottom": (0.5, 0.8),
    "bottom_left": (0.2, 0.8),
    "left": (0.2, 0.5),
}


def _resolve_grid_target(
    *,
    base_x: int,
    base_y: int,
    image_width: int,
    image_height: int,
    grid_rows: int,
    grid_cols: int,
    cell: int,
    anchor: str,
) -> dict[str, float | int | str | bool]:
    if grid_rows <= 0 or grid_cols <= 0:
        raise ValueError("grid_rows and grid_cols must be positive")
    if cell <= 0 or cell > grid_rows * grid_cols:
        raise ValueError("cell must be within the grid range")
    if anchor not in _ANCHOR_MAP:
        raise ValueError(f"Unsupported anchor: {anchor}")

    row_index = (cell - 1) // grid_cols
    col_index = (cell - 1) % grid_cols
    cell_width = image_width / grid_cols
    cell_height = image_height / grid_rows
    ratio_x, ratio_y = _ANCHOR_MAP[anchor]

    local_x = round(col_index * cell_width + cell_width * ratio_x)
    local_y = round(row_index * cell_height + cell_height * ratio_y)
    screen_x = base_x + local_x
    screen_y = base_y + local_y
    return {
        "success": True,
        "cell": cell,
        "anchor": anchor,
        "row": row_index + 1,
        "col": col_index + 1,
        "local_x": local_x,
        "local_y": local_y,
        "screen_x": screen_x,
        "screen_y": screen_y,
        "cell_width": cell_width,
        "cell_height": cell_height,
    }


def _extract_capture_grid_metadata(capture: dict) -> dict[str, int]:
    if "window_x" in capture:
        base_x = capture["window_x"]
        base_y = capture["window_y"]
        image_width = capture["screenshot_width"]
        image_height = capture["screenshot_height"]
    else:
        base_x = capture["x"]
        base_y = capture["y"]
        image_width = capture["width"]
        image_height = capture["height"]

    grid_rows = capture.get("grid_rows")
    grid_cols = capture.get("grid_cols")
    if not grid_rows or not grid_cols:
        raise ValueError("capture payload must include grid_rows and grid_cols")

    return {
        "base_x": base_x,
        "base_y": base_y,
        "image_width": image_width,
        "image_height": image_height,
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
    }


def remember_grid_capture(capture: dict) -> None:
    """Persist the most recent capture metadata that includes a grid."""
    global _LAST_GRID_CAPTURE
    _LAST_GRID_CAPTURE = dict(capture)


def clear_remembered_grid_capture() -> None:
    """Clear the remembered grid capture metadata."""
    global _LAST_GRID_CAPTURE
    _LAST_GRID_CAPTURE = None


def _get_capture_or_remembered(capture: dict | None) -> tuple[dict, str]:
    if capture is not None:
        return capture, "explicit"
    if _LAST_GRID_CAPTURE is not None:
        return dict(_LAST_GRID_CAPTURE), "remembered"
    raise ValueError(
        "click_grid_target requires capture metadata or a previously remembered grid capture"
    )


def tool_resolve_grid_target(
    base_x: int | None = None,
    base_y: int | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
    grid_rows: int | None = None,
    grid_cols: int | None = None,
    cell: int = 1,
    anchor: str = "center",
    capture: dict | None = None,
) -> str:
    """Resolve a grid cell + anchor into a screen-absolute target coordinate."""
    capture_source = "explicit"
    if capture is not None:
        metadata = _extract_capture_grid_metadata(capture)
        capture_source = "explicit"
    elif None not in (base_x, base_y, image_width, image_height, grid_rows, grid_cols):
        metadata = {
            "base_x": base_x,
            "base_y": base_y,
            "image_width": image_width,
            "image_height": image_height,
            "grid_rows": grid_rows,
            "grid_cols": grid_cols,
        }
    else:
        remembered_capture, capture_source = _get_capture_or_remembered(None)
        metadata = _extract_capture_grid_metadata(remembered_capture)

    resolved = _resolve_grid_target(
        base_x=metadata["base_x"],
        base_y=metadata["base_y"],
        image_width=metadata["image_width"],
        image_height=metadata["image_height"],
        grid_rows=metadata["grid_rows"],
        grid_cols=metadata["grid_cols"],
        cell=cell,
        anchor=anchor,
    )
    resolved["capture_source"] = capture_source
    return json.dumps(resolved, ensure_ascii=False)


def tool_click_grid_target(
    capture: dict | None,
    cell: int,
    anchor: str = "center",
    button: str = "left",
    clicks: int = 1,
    move_only: bool = False,
    duration: float = 0.25,
) -> str:
    """Resolve grid metadata from a screenshot payload and click or move directly."""
    capture_payload, capture_source = _get_capture_or_remembered(capture)
    metadata = _extract_capture_grid_metadata(capture_payload)
    resolved = _resolve_grid_target(cell=cell, anchor=anchor, **metadata)
    if move_only:
        action_payload = json.loads(
            tool_mouse_move(
                x=resolved["screen_x"],
                y=resolved["screen_y"],
                duration=duration,
            )
        )
    else:
        action_payload = json.loads(
            tool_mouse_click(
                x=resolved["screen_x"],
                y=resolved["screen_y"],
                button=button,
                clicks=clicks,
            )
        )
    return json.dumps(
        {
            "success": action_payload.get("success", True),
            "capture_source": capture_source,
            "resolved_target": resolved,
            "action": action_payload,
        },
        ensure_ascii=False,
    )
