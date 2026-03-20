"""Mouse control MCP tools."""

from __future__ import annotations

import json
import time

import pyautogui

from control_mcp.schemas.responses import ClickResult, DragResult, MousePosition

# Disable pyautogui pause/fail-safe for headless use (re-enable if needed)
pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = True


def tool_mouse_click(
    x: int,
    y: int,
    button: str = "left",
    clicks: int = 1,
    interval: float = 0.0,
    hold_seconds: float = 0.0,
) -> str:
    """Click the mouse at the specified screen coordinates.

    Supports single, double, and multi-clicks, with optional hold duration.

    Parameters
    ----------
    x:
        X coordinate to click (pixels from left of screen).
    y:
        Y coordinate to click (pixels from top of screen).
    button:
        Mouse button: "left", "right", or "middle".
    clicks:
        Number of clicks (1 = single, 2 = double, etc.).
    interval:
        Seconds between consecutive clicks.
    hold_seconds:
        If > 0, press and hold the button for this many seconds instead of clicking.
    """
    try:
        pyautogui.moveTo(x, y, duration=0.1)
        if hold_seconds > 0:
            pyautogui.mouseDown(x, y, button=button)
            time.sleep(hold_seconds)
            pyautogui.mouseUp(x, y, button=button)
            msg = f"Held {button} button at ({x}, {y}) for {hold_seconds}s"
        else:
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            msg = f"Clicked {button} {clicks}x at ({x}, {y})"

        return ClickResult(
            success=True, x=x, y=y, clicks=clicks, button=button, message=msg
        ).to_json()
    except Exception as e:
        return ClickResult(
            success=False, x=x, y=y, clicks=clicks, button=button, message=str(e)
        ).to_json()


def tool_mouse_drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    button: str = "left",
    duration: float = 0.5,
) -> str:
    """Drag the mouse from one position to another while holding a button.

    Parameters
    ----------
    start_x, start_y:
        Starting coordinates of the drag.
    end_x, end_y:
        Ending coordinates of the drag.
    button:
        Mouse button to hold during the drag: "left", "right", or "middle".
    duration:
        Duration of the drag in seconds (controls smoothness).
    """
    try:
        pyautogui.moveTo(start_x, start_y, duration=0.1)
        pyautogui.mouseDown(button=button)
        pyautogui.moveTo(end_x, end_y, duration=duration)
        pyautogui.mouseUp(button=button)
        msg = f"Dragged {button} from ({start_x},{start_y}) to ({end_x},{end_y}) in {duration}s"
        return DragResult(
            success=True,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            button=button,
            message=msg,
        ).to_json()
    except Exception as e:
        return DragResult(
            success=False,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            button=button,
            message=str(e),
        ).to_json()


def tool_mouse_move(x: int, y: int, duration: float = 0.25) -> str:
    """Move the mouse cursor to the specified position without clicking.

    Parameters
    ----------
    x, y:
        Target coordinates.
    duration:
        Time in seconds for the movement animation.
    """
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return MousePosition(x=x, y=y).to_json()
    except Exception as e:
        return json.dumps({"error": str(e)})


def tool_mouse_position() -> str:
    """Get the current mouse cursor position."""
    pos = pyautogui.position()
    return MousePosition(x=pos.x, y=pos.y).to_json()


def tool_mouse_scroll(
    clicks: int,
    x: int | None = None,
    y: int | None = None,
) -> str:
    """Scroll the mouse wheel.

    Parameters
    ----------
    clicks:
        Number of scroll steps. Positive = up, negative = down.
    x, y:
        Optional position to scroll at. If omitted, scrolls at current position.
    """
    try:
        if x is not None and y is not None:
            pyautogui.scroll(clicks, x=x, y=y)
        else:
            pyautogui.scroll(clicks)
        return json.dumps({"success": True, "clicks": clicks})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
