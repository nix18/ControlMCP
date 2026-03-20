# Module Design

## 1. `schemas/responses.py`

### Purpose
Define all structured response types returned by tool functions.

### Types

| Class | Fields | Used By |
|-------|--------|---------|
| `OperationResult` | success, message, details | Generic operations |
| `ScreenshotResult` | file_path, timestamp, width, height, x, y, monitor_index | capture_screen, capture_region |
| `WindowScreenshotResult` | file_path, timestamp, window_title, window_x/y/width/height, screenshot_width/height | capture_window |
| `WindowInfo` | title, x, y, width, height, is_visible, is_minimized, process_name | list_windows |
| `WindowListResult` | windows: list[WindowInfo] | list_windows |
| `ClickResult` | success, x, y, clicks, button, message | mouse_click |
| `DragResult` | success, start_x/y, end_x/y, button, message | mouse_drag |
| `KeyResult` | success, keys, action, message | key_press, key_hold, key_type |
| `MousePosition` | x, y | mouse_position, mouse_move |
| `MonitorInfo` | index, x, y, width, height, is_primary | get_screen_info |
| `ScreenInfoResult` | monitors: list[MonitorInfo] | get_screen_info |
| `ClipboardResult` | success, content, action, message | clipboard_get, clipboard_set |
| `CompositeActionResult` | success, steps_completed, total_steps, results, message | mouse_and_keyboard, key_sequence |

### Helpers
- `make_screenshot_filename(prefix, region, extension)` → generates descriptive filename

## 2. `utils/capture.py`

### Purpose
Platform-agnostic screen and window capture.

### Functions

| Function | Signature | Returns |
|----------|-----------|---------|
| `capture_full_screen` | `(save_dir, monitor_index) → ScreenshotResult` | Full screen screenshot |
| `capture_region` | `(x, y, width, height, save_dir) → ScreenshotResult` | Region screenshot |
| `get_monitors` | `() → list[MonitorInfo]` | Monitor info list |
| `list_windows` | `() → list[dict]` | Window list (delegates to platform backend) |
| `find_windows` | `(title_contains) → list[dict]` | Filtered window list |
| `focus_window` | `(title) → bool` | Focus success |
| `capture_window` | `(title, save_dir) → WindowScreenshotResult` | Window screenshot |

### Dependencies
- `mss` for screen capture
- `Pillow` for image saving
- Platform backends for window operations

## 3. `utils/_win_window.py`

### Purpose
Windows-specific window operations.

### Functions
- `list_windows()` → list[dict] (via pygetwindow)
- `focus_window(title)` → bool
- `find_and_get_geometry(title)` → dict | None

## 4. `utils/_mac_window.py`

### Purpose
macOS-specific window operations.

### Functions
- `list_windows()` → list[dict] (via Quartz)
- `focus_window(title)` → bool (via AppleScript)
- `find_and_get_geometry(title)` → dict | None

## 5. `utils/_linux_window.py`

### Purpose
Linux-specific window operations.

### Functions
- `list_windows()` → list[dict] (via Xlib)
- `focus_window(title)` → bool (via xdotool fallback)
- `find_and_get_geometry(title)` → dict | None

## 6. `tools/screen.py`

### Tools
| Tool | Parameters | Implementation |
|------|-----------|----------------|
| `tool_capture_screen` | save_dir, monitor | → `capture_full_screen()` |
| `tool_capture_region` | x, y, width, height, save_dir | → `capture_region()` |
| `tool_get_screen_info` | — | → `get_monitors()` |

## 7. `tools/window.py`

### Tools
| Tool | Parameters | Implementation |
|------|-----------|----------------|
| `tool_list_windows` | — | → `list_windows()` |
| `tool_find_windows` | title_contains | → `find_windows()` |
| `tool_focus_window` | title | → `focus_window()` |
| `tool_capture_window` | title, save_dir | → `capture_window()` |

## 8. `tools/mouse.py`

### Tools
| Tool | Parameters | Implementation |
|------|-----------|----------------|
| `tool_mouse_click` | x, y, button, clicks, interval, hold_seconds | → `pyautogui.click()` / `mouseDown/Up` |
| `tool_mouse_drag` | start_x/y, end_x/y, button, duration | → `pyautogui.moveTo` + `mouseDown` + `moveTo` + `mouseUp` |
| `tool_mouse_move` | x, y, duration | → `pyautogui.moveTo()` |
| `tool_mouse_position` | — | → `pyautogui.position()` |
| `tool_mouse_scroll` | clicks, x, y | → `pyautogui.scroll()` |

## 9. `tools/keyboard.py`

### Tools
| Tool | Parameters | Implementation |
|------|-----------|----------------|
| `tool_key_press` | keys, presses, interval | → `pyautogui.press()` / `hotkey()` |
| `tool_key_hold` | keys, hold_seconds | → `pyautogui.keyDown()` + sleep + `keyUp()` |
| `tool_key_type` | text, interval | → `pyautogui.typewrite()` |
| `tool_key_sequence` | sequence: list[dict] | → loop of press/hold/type with delays |

## 10. `tools/combined.py`

### Tools
| Tool | Parameters | Implementation |
|------|-----------|----------------|
| `tool_mouse_and_keyboard` | actions: list[dict] | → dispatcher loop over pyautogui operations |

### Supported Action Types
- `move`, `click`, `drag`, `scroll`, `mouse_down`, `mouse_up`
- `key_press`, `key_hold`, `key_type`
- `wait`, `screenshot`

## 11. `tools/actions.py`

### Tools
| Tool | Parameters | Implementation |
|------|-----------|----------------|
| `tool_clipboard_get` | — | → `pyperclip.paste()` |
| `tool_clipboard_set` | text | → `pyperclip.copy()` |
| `tool_launch_app` | command | → `subprocess.Popen()` / `open -a` |
| `tool_launch_url` | url | → `webbrowser.open()` |
| `tool_wait` | seconds | → `time.sleep()` |
| `tool_get_pixel_color` | x, y | → `pyautogui.pixel()` |
| `tool_hotkey` | *keys | → `pyautogui.hotkey()` |
| `tool_screenshot` | save_dir | → `tool_capture_screen()` |

## 12. `server.py`

### Structure
- `Server("control-mcp")` instance
- `TOOLS` list: all 24 `Tool` definitions
- `handle_list_tools()`: returns `TOOLS`
- `handle_call_tool(name, arguments)`: dispatcher to tool functions
- `main()`: runs stdio server (with Windows event loop policy fix)
