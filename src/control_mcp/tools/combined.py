"""Combined mouse + keyboard operation MCP tools."""

from __future__ import annotations

import json
import time

import pyautogui

from control_mcp.schemas.responses import CompositeActionResult

pyautogui.PAUSE = 0.01


def tool_mouse_and_keyboard(
    actions: list[dict],
) -> str:
    """Execute a sequence of combined mouse and keyboard actions.

    Each action in the list is a dict describing one step. Supported action types:

    **Mouse actions:**
    - ``move``: ``{"action": "move", "x": int, "y": int, "duration": float}``
    - ``click``: ``{"action": "click", "x": int, "y": int, "button": str, "clicks": int, "hold_seconds": float}``
    - ``drag``: ``{"action": "drag", "start_x": int, "start_y": int, "end_x": int, "end_y": int, "button": str, "duration": float}``
    - ``scroll``: ``{"action": "scroll", "clicks": int, "x": int, "y": int}``
    - ``mouse_down``: ``{"action": "mouse_down", "x": int, "y": int, "button": str}``
    - ``mouse_up``: ``{"action": "mouse_up", "x": int, "y": int, "button": str}``

    **Keyboard actions:**
    - ``key_press``: ``{"action": "key_press", "keys": [str], "presses": int}``
    - ``key_hold``: ``{"action": "key_hold", "keys": [str], "hold_seconds": float}``
    - ``key_type``: ``{"action": "key_type", "text": str, "interval": float}``

    **Utility:**
    - ``wait``: ``{"action": "wait", "seconds": float}``
    - ``screenshot``: ``{"action": "screenshot", "save_dir": str, "quality": int, "max_width": int}``

    All actions accept an optional ``"delay"`` field (seconds) to wait AFTER the step.

    Parameters
    ----------
    actions:
        Ordered list of action descriptors to execute.
    """
    results: list[dict] = []
    total = len(actions)

    try:
        for i, step in enumerate(actions):
            action_type = step.get("action", "")
            step_result: dict = {"step": i, "action": action_type}

            try:
                if action_type == "move":
                    pyautogui.moveTo(step["x"], step["y"], duration=step.get("duration", 0.25))
                    step_result["success"] = True

                elif action_type == "click":
                    x, y = step.get("x"), step.get("y")
                    if x is not None and y is not None:
                        pyautogui.moveTo(x, y, duration=0.05)
                    hold = step.get("hold_seconds", 0)
                    if hold > 0:
                        btn = step.get("button", "left")
                        pyautogui.mouseDown(button=btn)
                        time.sleep(hold)
                        pyautogui.mouseUp(button=btn)
                    else:
                        pyautogui.click(
                            x=step.get("x"),
                            y=step.get("y"),
                            clicks=step.get("clicks", 1),
                            button=step.get("button", "left"),
                        )
                    step_result["success"] = True

                elif action_type == "drag":
                    pyautogui.moveTo(step["start_x"], step["start_y"], duration=0.05)
                    pyautogui.mouseDown(button=step.get("button", "left"))
                    pyautogui.moveTo(
                        step["end_x"], step["end_y"], duration=step.get("duration", 0.5)
                    )
                    pyautogui.mouseUp(button=step.get("button", "left"))
                    step_result["success"] = True

                elif action_type == "scroll":
                    pyautogui.scroll(
                        step.get("clicks", 1),
                        x=step.get("x"),
                        y=step.get("y"),
                    )
                    step_result["success"] = True

                elif action_type == "mouse_down":
                    pyautogui.mouseDown(
                        x=step.get("x"),
                        y=step.get("y"),
                        button=step.get("button", "left"),
                    )
                    step_result["success"] = True

                elif action_type == "mouse_up":
                    pyautogui.mouseUp(
                        x=step.get("x"),
                        y=step.get("y"),
                        button=step.get("button", "left"),
                    )
                    step_result["success"] = True

                elif action_type == "key_press":
                    keys = step.get("keys", [])
                    if len(keys) == 1:
                        pyautogui.press(keys[0], presses=step.get("presses", 1))
                    else:
                        pyautogui.hotkey(*keys)
                    step_result["success"] = True

                elif action_type == "key_hold":
                    keys = step.get("keys", [])
                    hold_sec = step.get("hold_seconds", 1.0)
                    for k in keys:
                        pyautogui.keyDown(k)
                    time.sleep(hold_sec)
                    for k in reversed(keys):
                        pyautogui.keyUp(k)
                    step_result["success"] = True

                elif action_type == "key_type":
                    text = step.get("text", "")
                    iv = step.get("interval", 0.0)
                    if text.isascii():
                        pyautogui.typewrite(text, interval=iv)
                    else:
                        for ch in text:
                            pyautogui.press(ch)
                            if iv > 0:
                                time.sleep(iv)
                    step_result["success"] = True

                elif action_type == "wait":
                    time.sleep(step.get("seconds", 1.0))
                    step_result["success"] = True

                elif action_type == "screenshot":
                    from control_mcp.utils.capture import capture_full_screen

                    res = capture_full_screen(
                        save_dir=step.get("save_dir"),
                        quality=step.get("quality", 80),
                        max_width=step.get("max_width"),
                    )
                    step_result["success"] = True
                    step_result["screenshot"] = res.to_dict()

                else:
                    step_result["success"] = False
                    step_result["error"] = f"unknown action: {action_type}"

            except Exception as exc:
                step_result["success"] = False
                step_result["error"] = str(exc)

            results.append(step_result)

            # Post-step delay
            delay = step.get("delay", 0)
            if delay > 0:
                time.sleep(delay)

        all_ok = all(r.get("success", False) for r in results)
        return CompositeActionResult(
            success=all_ok,
            steps_completed=sum(1 for r in results if r.get("success", False)),
            total_steps=total,
            results=results,
        ).to_json()

    except Exception as e:
        return CompositeActionResult(
            success=False,
            steps_completed=sum(1 for r in results if r.get("success", False)),
            total_steps=total,
            results=results,
            message=str(e),
        ).to_json()
