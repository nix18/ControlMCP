# Tutorial & Examples

This tutorial shows how to use ControlMCP tools — both individually and in combination — to automate computer operations through an LLM.

## Table of Contents

1. [Screen Capture](#1-screen-capture)
2. [Window Management](#2-window-management)
3. [Mouse Control](#3-mouse-control)
4. [Keyboard Control](#4-keyboard-control)
5. [Combined Operations](#5-combined-operations)
6. [Additional Actions](#6-additional-actions)
7. [Real-World Patterns](#7-real-world-patterns)
8. [Control Plane Workflow](#8-control-plane-workflow)

---

## 0. Recommended Start: Plan First

When the user intent is vague, do not immediately chain raw keyboard and mouse tools.
Prefer the new control-plane flow:

```
tool: plan_desktop_task
args: {"instruction": "Switch to PyCharm and run the current config"}
```

Then execute the returned plan:

```
tool: execute_desktop_plan
args: {"plan_id": "plan_abc123"}
```

If a step is sensitive, approve it explicitly:

```
tool: confirm_sensitive_action
args: {"confirmation_id": "confirm_abc123", "approve": true}
```

If the UI drifts or the wrong shortcut was used, recover first:

```
tool: recover_execution_context
args: {"strategy": "show_desktop_then_capture"}
```

---

## 1. Screen Capture

### Take a full-screen screenshot

Captures the entire screen and saves it to a file.

```
tool: capture_screen
args: {}
```

### Compressed screenshot (recommended)

Use `quality=75` for JPEG (~5-8x smaller than PNG) and `max_width=960` to halve resolution.

```
tool: capture_screen
args: {"quality": 75, "max_width": 960}
```

**Response:**
```json
{
  "file_path": "/tmp/control_mcp_screenshots/screen_20260320_143022_123456_1920x1080_0_0.jpg",
  "timestamp": "2026-03-20T14:30:22.123456",
  "width": 960,
  "height": 540,
  "x": 0,
  "y": 0,
  "monitor_index": null,
  "file_size": 85000,
  "quality": 75
}
```

> **Tip:** `quality=100` produces lossless PNG. Lower quality = smaller files.
> `max_width` scales the image down (preserving aspect ratio), reducing token cost when LLMs analyze the screenshot.

### Capture a specific region

Captures a rectangular region at the specified coordinates.

```
tool: capture_region
args: {"x": 100, "y": 200, "width": 800, "height": 600}
```

### Capture second monitor

Captures a specific monitor by index and saves to a custom directory.

```
tool: capture_screen
args: {"monitor": 2, "save_dir": "C:/screenshots"}
```

### Get monitor info

Returns information about all connected monitors.

```
tool: get_screen_info
args: {}
```

---

## 2. Window Management

### List all windows

Returns a list of all visible windows with their titles and positions.

```
tool: list_windows
args: {}
```

### Find Chrome windows

Finds windows whose title contains the specified string (case-insensitive).

```
tool: find_windows
args: {"title_contains": "chrome"}
```

### Focus and screenshot a window

Finds a window, brings it to the foreground, and takes a screenshot of it.

```
tool: capture_window
args: {"title": "Notepad", "save_dir": "C:/screenshots"}
```

This will:
1. Find the window with "Notepad" in its title
2. Bring it to the foreground
3. Take a screenshot of just that window
4. Return the file path, window position, and dimensions

---

## 3. Mouse Control

### Single click

```
tool: mouse_click
args: {"x": 500, "y": 300}
```

### Double-click

```
tool: mouse_click
args: {"x": 500, "y": 300, "clicks": 2}
```

### Right-click

```
tool: mouse_click
args: {"x": 500, "y": 300, "button": "right"}
```

### Long-press (hold for 3 seconds)

Presses and holds the mouse button at the specified coordinates for the given duration.

```
tool: mouse_click
args: {"x": 500, "y": 300, "hold_seconds": 3.0}
```

### Drag from one point to another

```
tool: mouse_drag
args: {"start_x": 100, "start_y": 100, "end_x": 800, "end_y": 600, "duration": 0.5}
```

### Move cursor

Moves the cursor to the specified position without clicking.

```
tool: mouse_move
args: {"x": 960, "y": 540, "duration": 0.25}
```

### Get current position

```
tool: mouse_position
args: {}
```

### Scroll down

```
tool: mouse_scroll
args: {"clicks": -5}
```

### Scroll up at specific position

```
tool: mouse_scroll
args: {"clicks": 3, "x": 500, "y": 300}
```

---

## 4. Keyboard Control

### Press Enter

```
tool: key_press
args: {"keys": ["enter"]}
```

### Press Ctrl+C (copy)

```
tool: key_press
args: {"keys": ["ctrl", "c"]}
```

### Press Alt+Tab 3 times

Presses a key combination multiple times with an interval between presses.

```
tool: key_press
args: {"keys": ["alt", "tab"], "presses": 3, "interval": 0.5}
```

### Hold Shift for 2 seconds

```
tool: key_hold
args: {"keys": ["shift"], "hold_seconds": 2.0}
```

### Type text

Types text character by character with configurable interval.

```
tool: key_type
args: {"text": "Hello, World!", "interval": 0.05}
```

### Execute a key sequence

Executes a sequence of keyboard actions with delays between steps. Supports `press`, `hold`, `type`, and `wait` actions.

```
tool: key_sequence
args: {
  "sequence": [
    {"action": "press", "keys": ["ctrl", "a"], "delay": 0.2},
    {"action": "wait", "seconds": 0.3},
    {"action": "type", "text": "New content here", "delay": 0.1},
    {"action": "press", "keys": ["enter"], "delay": 0}
  ]
}
```

> **Note:** Use `"delay"` (seconds to wait AFTER a step) for simple pauses. Use `"action": "wait"` with `"seconds"` for explicit pauses between non-key actions.

---

## 5. Combined Operations

The `mouse_and_keyboard` tool lets you chain mouse and keyboard actions:

### Open a file in Notepad and type

Opens Notepad via Win key search, waits for it to load, then types text.

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "key_press", "keys": ["win"]},
    {"action": "wait", "seconds": 1.0},
    {"action": "key_type", "text": "notepad"},
    {"action": "key_press", "keys": ["enter"]},
    {"action": "wait", "seconds": 2.0},
    {"action": "key_type", "text": "Hello from ControlMCP!", "interval": 0.02}
  ]
}
```

### Select all text and replace it

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "key_press", "keys": ["ctrl", "a"], "delay": 0.2},
    {"action": "key_type", "text": "Replacement text", "delay": 0.1}
  ]
}
```

### Click a button, wait, then take a screenshot

Clicks at coordinates, waits for the result to load, then captures the screen.

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "click", "x": 500, "y": 300, "delay": 0.5},
    {"action": "screenshot", "save_dir": "/tmp/results"}
  ]
}
```

### Drag a slider

Clicks and holds at the start position, moves to the end position, then releases.

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "move", "x": 200, "y": 500, "delay": 0.2},
    {"action": "mouse_down", "x": 200, "y": 500, "button": "left"},
    {"action": "move", "x": 800, "y": 500, "duration": 0.3},
    {"action": "mouse_up", "x": 800, "y": 500, "button": "left"}
  ]
}
```

### Complex form filling

Clicks a field, types data, tabs to the next field, and repeats. Finally clicks submit and takes a screenshot.

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "click", "x": 400, "y": 250, "delay": 0.3},
    {"action": "key_type", "text": "John Doe", "delay": 0.2},
    {"action": "key_press", "keys": ["tab"], "delay": 0.2},
    {"action": "key_type", "text": "john@example.com", "delay": 0.2},
    {"action": "key_press", "keys": ["tab"], "delay": 0.2},
    {"action": "key_type", "text": "555-1234", "delay": 0.2},
    {"action": "click", "x": 400, "y": 400, "delay": 0.5},
    {"action": "screenshot"}
  ]
}
```

---

## 6. Additional Actions

### Get clipboard content

```
tool: clipboard_get
args: {}
```

### Set clipboard and paste

Sets the clipboard text, then use `key_press` with `["ctrl", "v"]` to paste.

```
tool: clipboard_set
args: {"text": "Hello from clipboard!"}
```

Then use `key_press` with `["ctrl", "v"]` to paste.

### Launch an app

Launches an application by name or path. Commands vary by platform.

```
tool: launch_app
args: {"command": "notepad"}   # Windows
tool: launch_app
args: {"command": "TextEdit"}  # macOS
```

### Open a URL

```
tool: launch_url
args: {"url": "https://example.com"}
```

### Get pixel color

Returns the RGB color of the pixel at the specified coordinates.

```
tool: get_pixel_color
args: {"x": 500, "y": 300}
```

Response: `{"x": 500, "y": 300, "r": 255, "g": 128, "b": 0, "hex": "#ff8000"}`

### Wait

Pauses execution for the specified number of seconds.

```
tool: wait
args: {"seconds": 2.5}
```

### Hotkey shortcut

Convenience wrapper for pressing hotkey combinations.

```
tool: hotkey
args: {"keys": ["ctrl", "shift", "s"]}  # Save As
```

---

## 7. Real-World Patterns

## 8. Control Plane Workflow

### Plan a vague desktop instruction

```
tool: plan_desktop_task
args: {"instruction": "Open the admin page and check the latest error"}
```

### Execute a plan and poll status

```
tool: execute_desktop_plan
args: {"plan_id": "plan_abc123"}
```

```
tool: get_execution_status
args: {"run_id": "run_abc123"}
```

### Save a successful workflow pattern

```
tool: record_workflow_experience
args: {
  "intent": "run_application_flow",
  "instruction": "Switch to PyCharm and run the current config",
  "app": "PyCharm",
  "summary": "Focus window, maximize, run, then wait until output stabilizes",
  "preferred_actions": ["focus_window", "key_press", "wait_until_stable"]
}
```

### Pattern: Screenshot -> Analyze -> Click

1. Take a screenshot
2. LLM analyzes the image
3. Click on the identified element

```
# Step 1
tool: capture_screen → returns file_path

# [LLM analyzes the image at file_path]

# Step 2
tool: mouse_click → {"x": identified_x, "y": identified_y}
```

### Pattern: Window workflow

1. Find and focus a window
2. Take a screenshot of it
3. Perform actions in that window

```
tool: find_windows → {"title_contains": "VS Code"}
tool: capture_window → {"title": "VS Code"}
tool: key_press → {"keys": ["ctrl", "shift", "p"]}
tool: key_type → {"text": "Format Document"}
tool: key_press → {"keys": ["enter"]}
```

### Pattern: Repeat-action loop

Use `mouse_and_keyboard` with a sequence that includes clicking a "next" button:

```
tool: mouse_and_keyboard → {
  "actions": [
    {"action": "click", "x": 500, "y": 300, "delay": 0.5},
    {"action": "key_press", "keys": ["ctrl", "c"], "delay": 0.2},
    {"action": "click", "x": 900, "y": 500, "delay": 0.5}  # next button
  ]
}
```

### Pattern: Wait for element then interact

Wait for a page or element to load, capture the screen, verify it appeared, then interact.

```
tool: wait → {"seconds": 3.0}
tool: capture_screen
# [LLM checks if target element appeared]
tool: mouse_click → {"x": element_x, "y": element_y}
```

---

## Key Names Reference

Common key names (pyautogui convention):

| Key | Name |
|---|---|
| Enter | `enter` / `return` |
| Tab | `tab` |
| Escape | `escape` |
| Backspace | `backspace` |
| Delete | `delete` |
| Space | `space` |
| Arrow keys | `up`, `down`, `left`, `right` |
| Function keys | `f1` through `f15` |
| Modifiers | `ctrl`, `alt`, `shift`, `win` (Windows) / `command` (Mac) |
| Home/End | `home`, `end` |
| Page Up/Down | `pageup`, `pagedown` |
| Print Screen | `printscreen` |

For a full list, see [pyautogui documentation](https://pyautogui.readthedocs.io/en/latest/keyboard.html).
