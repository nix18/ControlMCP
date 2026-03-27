"""Central tool registry for atomic and control-plane tools."""

from __future__ import annotations

from mcp.types import Tool


def _atomic_tools() -> list[Tool]:
    return [
        Tool(
            name="capture_screen",
            description=(
                "Capture the full screen or a specific monitor. "
                "Prefer quality=70-80 and max_width=960 for fast LLM analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "save_dir": {"type": "string"},
                    "monitor": {"type": "integer"},
                    "quality": {"type": "integer", "default": 80},
                    "max_width": {"type": "integer"},
                    "grid_rows": {"type": "integer"},
                    "grid_cols": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="capture_region",
            description="Capture a rectangular region of the screen.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "save_dir": {"type": "string"},
                    "quality": {"type": "integer", "default": 80},
                    "max_width": {"type": "integer"},
                    "grid_rows": {"type": "integer"},
                    "grid_cols": {"type": "integer"},
                },
                "required": ["x", "y", "width", "height"],
            },
        ),
        Tool(
            name="capture_scroll_region",
            description="Capture a fixed region while scrolling inside it, then stitch the frames.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "scroll_distance": {"type": "integer"},
                    "save_dir": {"type": "string"},
                    "quality": {"type": "integer", "default": 80},
                    "max_width": {"type": "integer"},
                },
                "required": ["x", "y", "width", "height", "scroll_distance"],
            },
        ),
        Tool(
            name="get_screen_info",
            description="Get information about all monitors.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="read_screenshot_base64",
            description=(
                "Read a screenshot file and return Base64 text. Useful for models "
                "that cannot directly inspect image attachments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "as_data_url": {"type": "boolean", "default": False},
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="list_windows",
            description="List all visible windows.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="find_windows",
            description="Find windows by partial title match.",
            inputSchema={
                "type": "object",
                "properties": {"title_contains": {"type": "string"}},
                "required": ["title_contains"],
            },
        ),
        Tool(
            name="focus_window",
            description="Bring a window to the foreground by title.",
            inputSchema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
        ),
        Tool(
            name="capture_window",
            description="Focus a window and capture it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "save_dir": {"type": "string"},
                    "quality": {"type": "integer", "default": 80},
                    "max_width": {"type": "integer"},
                    "grid_rows": {"type": "integer"},
                    "grid_cols": {"type": "integer"},
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="resolve_grid_target",
            description=(
                "Resolve a grid cell and anchor from a screenshot into screen-absolute "
                "coordinates for precise clicking."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "base_x": {"type": "integer"},
                    "base_y": {"type": "integer"},
                    "image_width": {"type": "integer"},
                    "image_height": {"type": "integer"},
                    "grid_rows": {"type": "integer"},
                    "grid_cols": {"type": "integer"},
                    "cell": {"type": "integer"},
                    "anchor": {
                        "type": "string",
                        "enum": [
                            "center",
                            "top_left",
                            "top",
                            "top_right",
                            "right",
                            "bottom_right",
                            "bottom",
                            "bottom_left",
                            "left",
                        ],
                        "default": "center",
                    },
                },
                "required": [
                    "base_x",
                    "base_y",
                    "image_width",
                    "image_height",
                    "grid_rows",
                    "grid_cols",
                    "cell",
                ],
            },
        ),
        Tool(
            name="click_grid_target",
            description=(
                "Use grid metadata from a screenshot response to resolve and directly "
                "move or click the target cell anchor. If capture metadata is omitted, "
                "the tool defaults to the most recent screenshot metadata that included a grid."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "capture": {"type": "object"},
                    "cell": {"type": "integer"},
                    "anchor": {
                        "type": "string",
                        "enum": [
                            "center",
                            "top_left",
                            "top",
                            "top_right",
                            "right",
                            "bottom_right",
                            "bottom",
                            "bottom_left",
                            "left",
                        ],
                        "default": "center",
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "default": "left",
                    },
                    "clicks": {"type": "integer", "default": 1},
                    "move_only": {"type": "boolean", "default": False},
                    "duration": {"type": "number", "default": 0.25},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["cell"],
            },
        ),
        Tool(
            name="mouse_click",
            description=(
                "Click at screen coordinates. "
                "Optional risk_context helps guard sensitive operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "default": "left",
                    },
                    "clicks": {"type": "integer", "default": 1},
                    "interval": {"type": "number", "default": 0},
                    "hold_seconds": {"type": "number", "default": 0},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["x", "y"],
            },
        ),
        Tool(
            name="mouse_drag",
            description="Drag the mouse while holding a button.",
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
                    "duration": {"type": "number", "default": 0.5},
                },
                "required": ["start_x", "start_y", "end_x", "end_y"],
            },
        ),
        Tool(
            name="mouse_move",
            description="Move the mouse cursor.",
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
            description="Get the current mouse position.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="mouse_scroll",
            description="Scroll the mouse wheel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["clicks"],
            },
        ),
        Tool(
            name="key_press",
            description=(
                "Press a key or key combination. "
                "Optional risk_context helps guard sensitive operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}},
                    "presses": {"type": "integer", "default": 1},
                    "interval": {"type": "number", "default": 0},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["keys"],
            },
        ),
        Tool(
            name="key_hold",
            description="Hold one or more keys for a duration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}},
                    "hold_seconds": {"type": "number"},
                },
                "required": ["keys", "hold_seconds"],
            },
        ),
        Tool(
            name="key_type",
            description="Type text. Optional risk_context helps guard sensitive operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "interval": {"type": "number", "default": 0},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="key_sequence",
            description="Execute a sequence of keyboard actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequence": {"type": "array", "items": {"type": "object"}},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["sequence"],
            },
        ),
        Tool(
            name="mouse_and_keyboard",
            description="Execute a combined sequence of mouse and keyboard actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actions": {"type": "array", "items": {"type": "object"}},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["actions"],
            },
        ),
        Tool(
            name="clipboard_get",
            description="Get clipboard text.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="clipboard_set",
            description=(
                "Set clipboard text. Optional risk_context helps guard sensitive operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="launch_app",
            description="Launch an application.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "args": {"type": "string", "default": ""},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
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
                    "url": {"type": "string"},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="wait",
            description="Pause execution.",
            inputSchema={
                "type": "object",
                "properties": {"seconds": {"type": "number"}},
                "required": ["seconds"],
            },
        ),
        Tool(
            name="get_pixel_color",
            description="Get the RGB color of a screen pixel.",
            inputSchema={
                "type": "object",
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
                "required": ["x", "y"],
            },
        ),
        Tool(
            name="hotkey",
            description="Press a keyboard shortcut.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}},
                    "risk_context": {"type": "string"},
                    "confirmation_token": {"type": "string"},
                },
                "required": ["keys"],
            },
        ),
    ]


def _control_plane_tools() -> list[Tool]:
    return [
        Tool(
            name="plan_desktop_task",
            description=(
                "Normalize a desktop-operation instruction into a structured plan before execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "Natural-language desktop task.",
                    },
                    "current_context": {
                        "type": "string",
                        "description": "Optional extra context from the caller.",
                    },
                },
                "required": ["instruction"],
            },
        ),
        Tool(
            name="execute_desktop_plan",
            description="Execute a structured desktop plan through the guarded control plane.",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string"},
                    "plan": {"type": "object"},
                    "confirmation_token": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_execution_status",
            description="Get the current status of a control-plane execution run.",
            inputSchema={
                "type": "object",
                "properties": {"run_id": {"type": "string"}},
                "required": ["run_id"],
            },
        ),
        Tool(
            name="confirm_sensitive_action",
            description=(
                "Approve or reject a pending sensitive action and optionally issue "
                "a confirmation token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_id": {"type": "string"},
                    "approve": {"type": "boolean", "default": True},
                    "note": {"type": "string"},
                },
                "required": ["confirmation_id"],
            },
        ),
        Tool(
            name="recover_execution_context",
            description=(
                "Run a bounded recovery flow such as re-focusing a window or "
                "showing the desktop and re-observing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {"type": "string", "default": "window_rescue"},
                    "target_window": {"type": "string"},
                },
            },
        ),
        Tool(
            name="record_workflow_experience",
            description="Persist a reusable workflow experience after a successful or failed run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intent": {"type": "string"},
                    "instruction": {"type": "string"},
                    "app": {"type": "string"},
                    "summary": {"type": "string"},
                    "preferred_actions": {"type": "array", "items": {"type": "string"}},
                    "anti_patterns": {"type": "array", "items": {"type": "string"}},
                    "verification_hints": {"type": "array", "items": {"type": "string"}},
                    "success": {"type": "boolean", "default": True},
                },
                "required": ["intent", "instruction"],
            },
        ),
    ]


TOOLS: list[Tool] = [*_atomic_tools(), *_control_plane_tools()]
