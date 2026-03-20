# 模块设计

## 1. `schemas/responses.py`

### 用途

定义所有工具函数返回的结构化响应类型。

### 类型

| 类 | 字段 | 使用者 |
|---|---|---|
| `OperationResult` | success, message, details | 通用操作 |
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

### 辅助函数

- `make_screenshot_filename(prefix, region, extension)` → 生成描述性文件名

---

## 2. `utils/capture.py`

### 用途

跨平台的屏幕和窗口捕获。

### 函数

| 函数 | 签名 | 返回值 |
|---|---|---|
| `capture_full_screen` | `(save_dir, monitor_index) → ScreenshotResult` | 全屏截图 |
| `capture_region` | `(x, y, width, height, save_dir) → ScreenshotResult` | 区域截图 |
| `get_monitors` | `() → list[MonitorInfo]` | 显示器信息列表 |
| `list_windows` | `() → list[dict]` | 窗口列表（委托给平台后端） |
| `find_windows` | `(title_contains) → list[dict]` | 过滤后的窗口列表 |
| `focus_window` | `(title) → bool` | 聚焦是否成功 |
| `capture_window` | `(title, save_dir) → WindowScreenshotResult` | 窗口截图 |

### 依赖

- `mss` 用于屏幕捕获
- `Pillow` 用于图像保存
- 平台后端用于窗口操作

---

## 3. `utils/_win_window.py`

### 用途

Windows 平台特定的窗口操作。

### 函数

- `list_windows()` → list[dict]（通过 pygetwindow）
- `focus_window(title)` → bool
- `find_and_get_geometry(title)` → dict | None

---

## 4. `utils/_mac_window.py`

### 用途

macOS 平台特定的窗口操作。

### 函数

- `list_windows()` → list[dict]（通过 Quartz）
- `focus_window(title)` → bool（通过 AppleScript）
- `find_and_get_geometry(title)` → dict | None

---

## 5. `utils/_linux_window.py`

### 用途

Linux 平台特定的窗口操作。

### 函数

- `list_windows()` → list[dict]（通过 Xlib）
- `focus_window(title)` → bool（通过 xdotool 回退）
- `find_and_get_geometry(title)` → dict | None

---

## 6. `tools/screen.py`

### 工具

| 工具 | 参数 | 实现 |
|---|---|---|
| `tool_capture_screen` | save_dir, monitor | → `capture_full_screen()` |
| `tool_capture_region` | x, y, width, height, save_dir | → `capture_region()` |
| `tool_get_screen_info` | — | → `get_monitors()` |

---

## 7. `tools/window.py`

### 工具

| 工具 | 参数 | 实现 |
|---|---|---|
| `tool_list_windows` | — | → `list_windows()` |
| `tool_find_windows` | title_contains | → `find_windows()` |
| `tool_focus_window` | title | → `focus_window()` |
| `tool_capture_window` | title, save_dir | → `capture_window()` |

---

## 8. `tools/mouse.py`

### 工具

| 工具 | 参数 | 实现 |
|---|---|---|
| `tool_mouse_click` | x, y, button, clicks, interval, hold_seconds | → `pyautogui.click()` / `mouseDown/Up` |
| `tool_mouse_drag` | start_x/y, end_x/y, button, duration | → `pyautogui.moveTo` + `mouseDown` + `moveTo` + `mouseUp` |
| `tool_mouse_move` | x, y, duration | → `pyautogui.moveTo()` |
| `tool_mouse_position` | — | → `pyautogui.position()` |
| `tool_mouse_scroll` | clicks, x, y | → `pyautogui.scroll()` |

---

## 9. `tools/keyboard.py`

### 工具

| 工具 | 参数 | 实现 |
|---|---|---|
| `tool_key_press` | keys, presses, interval | → `pyautogui.press()` / `hotkey()` |
| `tool_key_hold` | keys, hold_seconds | → `pyautogui.keyDown()` + sleep + `keyUp()` |
| `tool_key_type` | text, interval | → `pyautogui.typewrite()` |
| `tool_key_sequence` | sequence: list[dict] | → 带延迟的 press/hold/type 循环 |

---

## 10. `tools/combined.py`

### 工具

| 工具 | 参数 | 实现 |
|---|---|---|
| `tool_mouse_and_keyboard` | actions: list[dict] | → pyautogui 操作分发循环 |

### 支持的操作类型

- `move`（移动）、`click`（点击）、`drag`（拖拽）、`scroll`（滚动）、`mouse_down`（鼠标按下）、`mouse_up`（鼠标释放）
- `key_press`（按键）、`key_hold`（按住）、`key_type`（输入文本）
- `wait`（等待）、`screenshot`（截图）

---

## 11. `tools/actions.py`

### 工具

| 工具 | 参数 | 实现 |
|---|---|---|
| `tool_clipboard_get` | — | → `pyperclip.paste()` |
| `tool_clipboard_set` | text | → `pyperclip.copy()` |
| `tool_launch_app` | command | → `subprocess.Popen()` / `open -a` |
| `tool_launch_url` | url | → `webbrowser.open()` |
| `tool_wait` | seconds | → `time.sleep()` |
| `tool_get_pixel_color` | x, y | → `pyautogui.pixel()` |
| `tool_hotkey` | *keys | → `pyautogui.hotkey()` |
| `tool_screenshot` | save_dir | → `tool_capture_screen()` |

---

## 12. `server.py`

### 结构

- `Server("control-mcp")` 实例
- `TOOLS` 列表：所有 24 个 `Tool` 定义
- `handle_list_tools()`：返回 `TOOLS`
- `handle_call_tool(name, arguments)`：分发到工具函数
- `main()`：运行 stdio 服务器（附带 Windows 事件循环策略修复）
