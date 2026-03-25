"""Verification helpers for control-plane execution."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat

from control_mcp.tools.screen import tool_capture_region, tool_capture_screen
from control_mcp.tools.window import tool_capture_window


def _mean_difference(left_path: str, right_path: str) -> float:
    left = Image.open(left_path).convert("RGB")
    right = Image.open(right_path).convert("RGB")
    diff = ImageChops.difference(left, right)
    return float(ImageStat.Stat(diff).mean[0])


def wait_until_stable(
    *,
    scope: str,
    title: str | None = None,
    region: dict[str, int] | None = None,
    rounds: int = 2,
    interval_seconds: float = 1.0,
    difference_threshold: float = 0.75,
) -> dict[str, Any]:
    """Capture the same scope multiple times and confirm it stopped changing."""
    captures: list[str] = []
    stable_rounds = 0
    last_diff = None

    for _ in range(max(2, rounds + 1)):
        if scope == "window" and title:
            result = json_to_dict(tool_capture_window(title=title, quality=75, max_width=960))
        elif scope == "region" and region:
            result = json_to_dict(
                tool_capture_region(
                    x=region["x"],
                    y=region["y"],
                    width=region["width"],
                    height=region["height"],
                    quality=75,
                    max_width=960,
                )
            )
        else:
            result = json_to_dict(tool_capture_screen(quality=75, max_width=960))

        file_path = result.get("file_path")
        if not file_path or not Path(file_path).exists():
            return {"success": False, "message": "Unable to capture verification image."}

        captures.append(file_path)
        if len(captures) >= 2:
            last_diff = _mean_difference(captures[-2], captures[-1])
            if last_diff <= difference_threshold:
                stable_rounds += 1
            else:
                stable_rounds = 0

        if stable_rounds >= rounds:
            return {
                "success": True,
                "stable": True,
                "captures": captures,
                "difference": last_diff,
            }

        time.sleep(interval_seconds)

    return {
        "success": False,
        "stable": False,
        "captures": captures,
        "difference": last_diff,
        "message": "Content did not stabilize within the requested rounds.",
    }


def json_to_dict(payload: str) -> dict[str, Any]:
    import json

    return json.loads(payload)
