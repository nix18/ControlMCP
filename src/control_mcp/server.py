"""ControlMCP — MCP server for LLM-controlled computer operations.

This module creates and runs the MCP server that exposes computer-control
tools to LLM clients via the Model Context Protocol.
"""

from __future__ import annotations

import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from control_mcp.tools.screen import (
    tool_capture_screen,
    tool_capture_region,
    tool_get_screen_info,
)
from control_mcp.tools.window import (
    tool_list_windows,
    tool_find_windows,
    tool_focus_window,
    tool_capture_window,
)
from control_mcp.tools.mouse import (
    tool_mouse_click,
    tool_mouse_drag,
    tool_mouse_move,
    tool_mouse_position,
    tool_mouse_scroll,
)
from control_mcp.tools.keyboard import (
    tool_key_press,
    tool_key_hold,
    tool_key_type,
    tool_key_sequence,
)
from control_mcp.tools.combined import tool_mouse_and_keyboard
from control_mcp.tools.actions import (
    tool_clipboard_get,
    tool_clipboard_set,
    tool_launch_app,
    tool_launch_url,
    tool_wait,
    tool_get_pixel_color,
    tool_hotkey,
    tool_screenshot,
)

# ---------------------------------------------------------------------------
# Server definition
# ---------------------------------------------------------------------------

server = Server("control-mcp")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    # --- Screen capture ---
    Tool(
        name="capture_screen",
        description=(
            "Capture the full screen or a specific monitor. "
            "Returns a JSON object with file_path, timestamp, width, height, x, y, file_size, quality. "
            "TIP: Use quality=70-80 (default) for 5-8x smaller JPEG files. Use max_width=960 to halve "
            "token cost when LLM analyzes the image. Coordinates in response are SCREEN coordinates."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "save_dir": {
                    "type": "string",
                    "description": "Directory to save the screenshot (default: system temp).",
                },
                "monitor": {
                    "type": "integer",
                    "description": "1-based monitor index. Omit for all monitors combined.",
                },
                "quality": {
                    "type": "integer",
                    "description": "JPEG quality 1-100. Default 80. 100=PNG lossless. 70=small file, still clear.",
                    "default": 80,
                },
                "max_width": {
                    "type": "integer",
                    "description": "Scale image to max width (preserves aspect). E.g. 960 halves a 1920px screen.",
                },
            },
        },
    ),
    Tool(
        name="capture_region",
        description=(
            "Capture a rectangular region of the screen defined by (x, y, width, height). "
            "Returns a JSON object with file_path, timestamp, width, height, x, y, file_size, quality. "
            "TIP: Use quality=70-80 and max_width to reduce file size and token cost."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Left edge x-coordinate (pixels)."},
                "y": {"type": "integer", "description": "Top edge y-coordinate (pixels)."},
                "width": {"type": "integer", "description": "Width of capture region (pixels)."},
                "height": {"type": "integer", "description": "Height of capture region (pixels)."},
                "save_dir": {
                    "type": "string",
                    "description": "Directory to save the screenshot.",
                },
                "quality": {
                    "type": "integer",
                    "description": "JPEG quality 1-100. Default 80. 100=PNG lossless.",
                    "default": 80,
                },
                "max_width": {
                    "type": "integer",
                    "description": "Scale image to max width.",
                },
            },
            "required": ["x", "y", "width", "height"],
        },
    ),
    Tool(
        name="get_screen_info",
        description=(
            "Get information about all connected monitors (resolution, position). "
            "Useful for understanding the coordinate space. Primary monitor starts at (0,0)."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # --- Window management ---
    Tool(
        name="list_windows",
        description="List all visible windows on the desktop with their title and geometry.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="find_windows",
        description="Find windows by partial title match (case-insensitive).",
        inputSchema={
            "type": "object",
            "properties": {
                "title_contains": {
                    "type": "string",
                    "description": "Substring to search for in window titles.",
                },
            },
            "required": ["title_contains"],
        },
    ),
    Tool(
        name="focus_window",
        description="Bring a window to the foreground by title (partial, case-insensitive match).",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Substring of the window title to focus.",
                },
            },
            "required": ["title"],
        },
    ),
    Tool(
        name="capture_window",
        description=(
            "Focus a window and capture a screenshot of it. "
            "Returns file_path, window geometry, screenshot dimensions, file_size, quality. "
            "COORDINATES: The returned (window_x, window_y) is the window's SCREEN position. "
            "Elements inside the screenshot are at LOCAL coordinates (0,0 = top-left of window). "
            "To click an element at screenshot (sx, sy), use screen_x = window_x + sx, screen_y = window_y + sy. "
            "TIP: Use max_width=960 and quality=75 for token-efficient captures."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Substring of the window title to capture.",
                },
                "save_dir": {
                    "type": "string",
                    "description": "Directory to save the screenshot.",
                },
                "quality": {
                    "type": "integer",
                    "description": "JPEG quality 1-100. Default 80.",
                    "default": 80,
                },
                "max_width": {
                    "type": "integer",
                    "description": "Scale image to max width.",
                },
            },
            "required": ["title"],
        },
    ),
    # --- Mouse control ---
    Tool(
        name="mouse_click",
        description=(
            "Click the mouse at given SCREEN coordinates. "
            "Supports single/double/multi-click, long-hold, and left/right/middle buttons. "
            "COORDINATE SYSTEM: All coordinates are SCREEN-ABSOLUTE (pixels from top-left of primary monitor). "
            "When clicking inside a captured window: screen_x = window_x + local_x, screen_y = window_y + local_y. "
            "TIP: Prefer keyboard shortcuts over mouse clicks for precision (e.g. Ctrl+F5 instead of clicking a small button)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate to click."},
                "y": {"type": "integer", "description": "Y coordinate to click."},
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "default": "left",
                },
                "clicks": {"type": "integer", "default": 1, "description": "Number of clicks."},
                "interval": {
                    "type": "number",
                    "default": 0,
                    "description": "Seconds between consecutive clicks.",
                },
                "hold_seconds": {
                    "type": "number",
                    "default": 0,
                    "description": "If > 0, press and hold instead of clicking.",
                },
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="mouse_drag",
        description=(
            "Drag the mouse from one position to another while holding a button. "
            "Useful for drag-and-drop, slider control, text selection, etc."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "start_x": {"type": "integer"},
                "start_y": {"type": "integer"},
                "end_x": {"type": "integer"},
                "end_y": {"type": "integer"},
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "default": "left",
                },
                "duration": {
                    "type": "number",
                    "default": 0.5,
                    "description": "Duration of the drag in seconds.",
                },
            },
            "required": ["start_x", "start_y", "end_x", "end_y"],
        },
    ),
    Tool(
        name="mouse_move",
        description="Move the mouse cursor to a position without clicking.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "duration": {"type": "number", "default": 0.25},
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="mouse_position",
        description="Get the current mouse cursor position.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="mouse_scroll",
        description="Scroll the mouse wheel. Positive = up, negative = down.",
        inputSchema={
            "type": "object",
            "properties": {
                "clicks": {
                    "type": "integer",
                    "description": "Number of scroll steps. Positive = up, negative = down.",
                },
                "x": {"type": "integer", "description": "Optional x position to scroll at."},
                "y": {"type": "integer", "description": "Optional y position to scroll at."},
            },
            "required": ["clicks"],
        },
    ),
    # --- Keyboard control ---
    Tool(
        name="key_press",
        description=(
            "Press a key or combination of keys. For combos like Ctrl+C, pass keys=['ctrl','c']."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key names (pyautogui convention).",
                },
                "presses": {"type": "integer", "default": 1},
                "interval": {"type": "number", "default": 0},
            },
            "required": ["keys"],
        },
    ),
    Tool(
        name="key_hold",
        description="Hold down one or more keys for a specified duration.",
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key names to hold.",
                },
                "hold_seconds": {
                    "type": "number",
                    "description": "Duration to hold in seconds.",
                },
            },
            "required": ["keys", "hold_seconds"],
        },
    ),
    Tool(
        name="key_type",
        description="Type a string of text character by character.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type."},
                "interval": {
                    "type": "number",
                    "default": 0,
                    "description": "Seconds between characters.",
                },
            },
            "required": ["text"],
        },
    ),
    Tool(
        name="key_sequence",
        description=(
            "Execute a sequence of keyboard actions with optional delays. "
            "Each step: {action: 'press'|'hold'|'type'|'wait', keys: [...], text: '...', hold_seconds: N, seconds: N, delay: N}. "
            "'delay' waits AFTER the step; 'wait' is a dedicated pause action with 'seconds' param."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of keyboard action descriptors.",
                },
            },
            "required": ["sequence"],
        },
    ),
    # --- Combined operations ---
    Tool(
        name="mouse_and_keyboard",
        description=(
            "Execute a sequence of combined mouse and keyboard actions in one call. "
            "Supported actions: move, click, drag, scroll, mouse_down, mouse_up, "
            "key_press, key_hold, key_type, wait, screenshot. "
            "Each step supports an optional 'delay' field (seconds to wait AFTER the step). "
            "ALL mouse coordinates are SCREEN-ABSOLUTE. "
            "PREFER KEYBOARD SHORTCUTS: IDE actions like run (Ctrl+F5), build (Ctrl+F9), "
            "save (Ctrl+S) are more reliable than clicking small buttons."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Ordered list of action descriptors.",
                },
            },
            "required": ["actions"],
        },
    ),
    # --- Additional actions ---
    Tool(
        name="clipboard_get",
        description="Get the current clipboard text content.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="clipboard_set",
        description="Set the clipboard text content.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to copy to clipboard."},
            },
            "required": ["text"],
        },
    ),
    Tool(
        name="launch_app",
        description=(
            "Launch an application by command or path. "
            "On Windows uses 'start' command for reliable GUI app launching."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "App name (e.g. 'notepad', 'chrome'), "
                        "full path, or protocol (e.g. 'ms-settings:')."
                    ),
                },
                "args": {
                    "type": "string",
                    "default": "",
                    "description": "Optional arguments to pass to the application.",
                },
            },
            "required": ["command"],
        },
    ),
    Tool(
        name="launch_url",
        description="Open a URL in the default browser.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open."},
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="wait",
        description="Pause execution for a specified number of seconds.",
        inputSchema={
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Duration to wait."},
            },
            "required": ["seconds"],
        },
    ),
    Tool(
        name="get_pixel_color",
        description="Get the RGB color of a pixel at given screen coordinates.",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    ),
    Tool(
        name="hotkey",
        description="Press a keyboard shortcut combination (e.g., ctrl+c, alt+tab).",
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key names forming the hotkey.",
                },
            },
            "required": ["keys"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    args = arguments or {}
    try:
        if name == "capture_screen":
            result = tool_capture_screen(
                save_dir=args.get("save_dir"),
                monitor=args.get("monitor"),
                quality=args.get("quality", 80),
                max_width=args.get("max_width"),
            )
        elif name == "capture_region":
            result = tool_capture_region(
                x=args["x"],
                y=args["y"],
                width=args["width"],
                height=args["height"],
                save_dir=args.get("save_dir"),
                quality=args.get("quality", 80),
                max_width=args.get("max_width"),
            )
        elif name == "get_screen_info":
            result = tool_get_screen_info()
        elif name == "list_windows":
            result = tool_list_windows()
        elif name == "find_windows":
            result = tool_find_windows(args["title_contains"])
        elif name == "focus_window":
            result = tool_focus_window(args["title"])
        elif name == "capture_window":
            result = tool_capture_window(
                args["title"],
                save_dir=args.get("save_dir"),
                quality=args.get("quality", 80),
                max_width=args.get("max_width"),
            )
        elif name == "mouse_click":
            result = tool_mouse_click(
                x=args["x"],
                y=args["y"],
                button=args.get("button", "left"),
                clicks=args.get("clicks", 1),
                interval=args.get("interval", 0),
                hold_seconds=args.get("hold_seconds", 0),
            )
        elif name == "mouse_drag":
            result = tool_mouse_drag(
                start_x=args["start_x"],
                start_y=args["start_y"],
                end_x=args["end_x"],
                end_y=args["end_y"],
                button=args.get("button", "left"),
                duration=args.get("duration", 0.5),
            )
        elif name == "mouse_move":
            result = tool_mouse_move(x=args["x"], y=args["y"], duration=args.get("duration", 0.25))
        elif name == "mouse_position":
            result = tool_mouse_position()
        elif name == "mouse_scroll":
            result = tool_mouse_scroll(clicks=args["clicks"], x=args.get("x"), y=args.get("y"))
        elif name == "key_press":
            result = tool_key_press(
                keys=args["keys"],
                presses=args.get("presses", 1),
                interval=args.get("interval", 0),
            )
        elif name == "key_hold":
            result = tool_key_hold(keys=args["keys"], hold_seconds=args["hold_seconds"])
        elif name == "key_type":
            result = tool_key_type(text=args["text"], interval=args.get("interval", 0))
        elif name == "key_sequence":
            result = tool_key_sequence(sequence=args["sequence"])
        elif name == "mouse_and_keyboard":
            result = tool_mouse_and_keyboard(actions=args["actions"])
        elif name == "clipboard_get":
            result = tool_clipboard_get()
        elif name == "clipboard_set":
            result = tool_clipboard_set(args["text"])
        elif name == "launch_app":
            result = tool_launch_app(args["command"], args.get("args", ""))
        elif name == "launch_url":
            result = tool_launch_url(args["url"])
        elif name == "wait":
            result = tool_wait(args["seconds"])
        elif name == "get_pixel_color":
            result = tool_get_pixel_color(args["x"], args["y"])
        elif name == "hotkey":
            result = tool_hotkey(*args["keys"])
        else:
            result = f'{{"error": "Unknown tool: {name}"}}'

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f'{{"error": "{type(e).__name__}: {e}"}}')]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(_run())


if __name__ == "__main__":
    main()
