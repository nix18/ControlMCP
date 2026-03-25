"""Keyboard control MCP tools."""

from __future__ import annotations

import json
import time
from contextlib import suppress

import pyautogui

from control_mcp.schemas.responses import KeyResult

pyautogui.PAUSE = 0.01


def tool_key_press(keys: list[str], presses: int = 1, interval: float = 0.0) -> str:
    """Press a key or combination of keys.

    For a single key like ``Enter``, pass ``["enter"]``.
    For a combo like Ctrl+Shift+S, pass ``["ctrl", "shift", "s"]``.

    Parameters
    ----------
    keys:
        List of key names (pyautogui convention). E.g. ``["ctrl", "c"]`` for Ctrl+C.
    presses:
        Number of times to press the key/combination.
    interval:
        Seconds between consecutive presses.
    """
    try:
        if len(keys) == 1:
            pyautogui.press(keys[0], presses=presses, interval=interval)
        else:
            # hotkey handles combos
            for _ in range(presses):
                pyautogui.hotkey(*keys)
                if interval > 0:
                    time.sleep(interval)
        return KeyResult(success=True, keys=keys, action="press").to_json()
    except Exception as e:
        return KeyResult(success=False, keys=keys, action="press", message=str(e)).to_json()


def tool_key_hold(keys: list[str], hold_seconds: float) -> str:
    """Hold down one or more keys for a specified duration.

    Useful for actions like holding Shift while clicking.

    Parameters
    ----------
    keys:
        List of key names to hold.
    hold_seconds:
        Duration to hold the keys in seconds.
    """
    try:
        for k in keys:
            pyautogui.keyDown(k)
        time.sleep(hold_seconds)
        for k in reversed(keys):
            pyautogui.keyUp(k)
        return KeyResult(
            success=True,
            keys=keys,
            action="hold",
            message=f"Held {keys} for {hold_seconds}s",
        ).to_json()
    except Exception as e:
        # Best-effort release
        for k in reversed(keys):
            with suppress(Exception):
                pyautogui.keyUp(k)
        return KeyResult(
            success=False,
            keys=keys,
            action="hold",
            message=str(e),
        ).to_json()


def tool_key_type(text: str, interval: float = 0.0) -> str:
    """Type a string of text character by character.

    Parameters
    ----------
    text:
        The text to type.
    interval:
        Seconds between each character.
    """
    try:
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)
        return KeyResult(success=True, keys=[text], action="type").to_json()
    except Exception:
        # Fallback: type char by char via press
        try:
            for ch in text:
                pyautogui.press(ch)
                if interval > 0:
                    time.sleep(interval)
            return KeyResult(success=True, keys=[text], action="type").to_json()
        except Exception as e:
            return KeyResult(success=False, keys=[text], action="type", message=str(e)).to_json()


def tool_key_sequence(
    sequence: list[dict],
) -> str:
    """Execute a sequence of keyboard actions with optional delays between them.

    Each element of *sequence* is a dict with:
    - ``action``: "press" | "hold" | "type" | "wait"
    - ``keys``: list of key names (for press/hold)
    - ``text``: string (for type)
    - ``hold_seconds``: float (for hold)
    - ``seconds``: float (for wait)
    - ``delay``: seconds to wait AFTER this step

    Example::

        [
            {"action": "press", "keys": ["ctrl", "a"], "delay": 0.2},
            {"action": "wait", "seconds": 0.3},
            {"action": "type", "text": "hello", "delay": 0.1},
            {"action": "press", "keys": ["enter"], "delay": 0}
        ]

    Parameters
    ----------
    sequence:
        List of keyboard action descriptors.
    """
    results = []
    try:
        for i, step in enumerate(sequence):
            action = step.get("action", "press")
            if action == "press":
                keys = step.get("keys", [])
                pyautogui.hotkey(*keys) if len(keys) > 1 else pyautogui.press(keys[0])
                results.append({"step": i, "action": "press", "keys": keys, "success": True})
            elif action == "hold":
                keys = step.get("keys", [])
                hold_sec = step.get("hold_seconds", 1.0)
                for k in keys:
                    pyautogui.keyDown(k)
                time.sleep(hold_sec)
                for k in reversed(keys):
                    pyautogui.keyUp(k)
                results.append({"step": i, "action": "hold", "keys": keys, "success": True})
            elif action == "type":
                text = step.get("text", "")
                interval = step.get("interval", 0.0)
                if text.isascii():
                    pyautogui.typewrite(text, interval=interval)
                else:
                    for ch in text:
                        pyautogui.press(ch)
                        if interval > 0:
                            time.sleep(interval)
                results.append({"step": i, "action": "type", "text": text, "success": True})
            elif action == "wait":
                wait_sec = step.get("seconds", 1.0)
                time.sleep(wait_sec)
                results.append({"step": i, "action": "wait", "seconds": wait_sec, "success": True})
            else:
                results.append(
                    {"step": i, "action": action, "success": False, "error": "unknown action"}
                )

            delay = step.get("delay", 0)
            if delay > 0:
                time.sleep(delay)

        return json.dumps({"success": True, "steps": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "steps": results, "error": str(e)}, ensure_ascii=False)
