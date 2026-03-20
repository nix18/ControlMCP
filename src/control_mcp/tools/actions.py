"""Additional computer-action MCP tools (clipboard, hotkeys, app launch, etc.)."""

from __future__ import annotations

import json
import platform
import subprocess
import time
import webbrowser

import pyautogui

from control_mcp.schemas.responses import ClipboardResult, OperationResult

pyautogui.PAUSE = 0.01


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------


def tool_clipboard_get() -> str:
    """Get the current clipboard text content.

    Uses platform-specific methods for reliable clipboard access.
    """
    try:
        import pyperclip

        text = pyperclip.paste()
        return ClipboardResult(success=True, content=text, action="get").to_json()
    except ImportError:
        # Fallback: simulate Ctrl+V in a text field
        return ClipboardResult(
            success=False,
            action="get",
            message="pyperclip not installed. Install with: pip install pyperclip",
        ).to_json()


def tool_clipboard_set(text: str) -> str:
    """Set the clipboard to the given text.

    Parameters
    ----------
    text:
        Text to copy to the clipboard.
    """
    try:
        import pyperclip

        pyperclip.copy(text)
        return ClipboardResult(success=True, content=text, action="set").to_json()
    except ImportError:
        return ClipboardResult(
            success=False,
            action="set",
            message="pyperclip not installed. Install with: pip install pyperclip",
        ).to_json()


# ---------------------------------------------------------------------------
# App launch / focus
# ---------------------------------------------------------------------------


def tool_launch_app(command: str, args: str = "") -> str:
    """Launch an application by command/path.

    Parameters
    ----------
    command:
        The command or full path to the application executable.
        On Windows: can be an app name (e.g. "notepad", "chrome"),
        a full path (e.g. "C:\\Program Files\\app.exe"),
        or a URL/protocol (e.g. "ms-settings:").
    args:
        Optional arguments to pass to the application.
    """
    try:
        system = platform.system()
        if system == "Windows":
            # Use 'start' via cmd to reliably launch GUI apps
            # '""' is an empty title required by start
            cmd_parts = ["cmd", "/c", "start", "", command]
            if args:
                cmd_parts.append(args)
            proc = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            # Give it a moment and check for immediate failure
            time.sleep(0.5)
            ret = proc.poll()
            if ret is not None and ret != 0:
                stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
                return OperationResult(
                    success=False,
                    message=f"Process exited with code {ret}: {stderr.strip()}",
                ).to_json()
        elif system == "Darwin":
            cmd_list = ["open", "-a", command]
            if args:
                cmd_list.extend(["--args", *args.split()])
            proc = subprocess.Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            time.sleep(0.5)
            ret = proc.poll()
            if ret is not None and ret != 0:
                stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
                return OperationResult(
                    success=False,
                    message=f"open failed (exit {ret}): {stderr.strip()}",
                ).to_json()
        else:
            cmd_str = f"{command} {args}".strip()
            proc = subprocess.Popen(
                cmd_str,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            time.sleep(0.5)
            ret = proc.poll()
            if ret is not None and ret != 0:
                stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
                return OperationResult(
                    success=False,
                    message=f"Launch failed (exit {ret}): {stderr.strip()}",
                ).to_json()

        return OperationResult(success=True, message=f"Launched: {command}").to_json()
    except Exception as e:
        return OperationResult(success=False, message=f"{type(e).__name__}: {e}").to_json()


def tool_launch_url(url: str) -> str:
    """Open a URL in the default browser.

    Parameters
    ----------
    url:
        The URL to open.
    """
    try:
        webbrowser.open(url)
        return OperationResult(success=True, message=f"Opened URL: {url}").to_json()
    except Exception as e:
        return OperationResult(success=False, message=str(e)).to_json()


# ---------------------------------------------------------------------------
# Screenshot helper (used in combined flow)
# ---------------------------------------------------------------------------


def tool_screenshot(save_dir: str | None = None) -> str:
    """Take a screenshot of the entire screen. Alias for capture_screen.

    Parameters
    ----------
    save_dir:
        Directory to save the screenshot.
    """
    from control_mcp.tools.screen import tool_capture_screen

    return tool_capture_screen(save_dir=save_dir)


# ---------------------------------------------------------------------------
# Wait / pause
# ---------------------------------------------------------------------------


def tool_wait(seconds: float) -> str:
    """Pause execution for a specified number of seconds.

    Parameters
    ----------
    seconds:
        Duration to wait.
    """
    time.sleep(seconds)
    return OperationResult(success=True, message=f"Waited {seconds}s").to_json()


# ---------------------------------------------------------------------------
# Get screen pixel color
# ---------------------------------------------------------------------------


def tool_get_pixel_color(x: int, y: int) -> str:
    """Get the RGB color of a pixel at the given screen coordinates.

    Parameters
    ----------
    x, y:
        Screen coordinates.
    """
    try:
        r, g, b = pyautogui.pixel(x, y)
        return json.dumps(
            {
                "x": x,
                "y": y,
                "r": r,
                "g": g,
                "b": b,
                "hex": f"#{r:02x}{g:02x}{b:02x}",
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Hotkey (convenience wrapper)
# ---------------------------------------------------------------------------


def tool_hotkey(*keys: str) -> str:
    """Press a keyboard shortcut / hotkey combination.

    Examples: ``tool_hotkey("ctrl", "c")`` for Ctrl+C, ``tool_hotkey("alt", "tab")`` for Alt+Tab.

    Parameters
    ----------
    keys:
        Variable number of key names forming the hotkey.
    """
    try:
        pyautogui.hotkey(*keys)
        return OperationResult(success=True, message=f"Pressed hotkey: {'+'.join(keys)}").to_json()
    except Exception as e:
        return OperationResult(success=False, message=str(e)).to_json()
