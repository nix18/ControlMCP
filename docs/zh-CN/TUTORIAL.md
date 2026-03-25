# 教程与示例

本教程展示如何使用 ControlMCP 工具——单独使用或组合使用——通过 LLM 自动化计算机操作。

## 目录

1. [屏幕截图](#1-屏幕截图)
2. [窗口管理](#2-窗口管理)
3. [鼠标控制](#3-鼠标控制)
4. [键盘控制](#4-键盘控制)
5. [组合操作](#5-组合操作)
6. [附加操作](#6-附加操作)
7. [实际场景模式](#7-实际场景模式)
8. [控制平面工作流](#8-控制平面工作流)

---

## 0. 推荐入口：先规划再执行

如果用户的电脑操作意图比较模糊，不要立刻串联原子鼠标键盘工具。
优先使用新的控制平面工作流：

```
tool: plan_desktop_task
args: {"instruction": "切到 PyCharm 并运行当前配置"}
```

然后执行返回的计划：

```
tool: execute_desktop_plan
args: {"plan_id": "plan_abc123"}
```

如果步骤是敏感操作，先显式确认：

```
tool: confirm_sensitive_action
args: {"confirmation_id": "confirm_abc123", "approve": true}
```

如果界面跑偏或快捷键误用，先恢复上下文：

```
tool: recover_execution_context
args: {"strategy": "show_desktop_then_capture"}
```

---

## 1. 屏幕截图

### 全屏截图

捕获整个屏幕并保存为文件。

```
tool: capture_screen
args: {}
```

**响应:**
```json
{
  "file_path": "/tmp/control_mcp_screenshots/screen_20260320_143022_123456_1920x1080_0_0.png",
  "timestamp": "2026-03-20T14:30:22.123456",
  "width": 1920,
  "height": 1080,
  "x": 0,
  "y": 0,
  "monitor_index": null
}
```

### 截取指定区域

截取指定坐标处的矩形区域。

```
tool: capture_region
args: {"x": 100, "y": 200, "width": 800, "height": 600}
```

### 生成带网格的辅助截图，用于精确点击

```
tool: capture_window
args: {"title": "Chrome", "grid_rows": 3, "grid_cols": 4}
```

这会同时返回原图和 `grid_file_path` 网格图。
当你在网格图里确定了目标格子和锚点后，再这样换算点击坐标：

```
tool: resolve_grid_target
args: {
  "base_x": 286,
  "base_y": 22,
  "image_width": 1404,
  "image_height": 990,
  "grid_rows": 3,
  "grid_cols": 4,
  "cell": 6,
  "anchor": "center"
}
```

支持的锚点：`center`、`top_left`、`top`、`top_right`、`right`、`bottom_right`、`bottom`、`bottom_left`、`left`。

如果你已经拿到了截图响应对象，也可以直接点击：

```
tool: click_grid_target
args: {
  "capture": {"window_x": 286, "window_y": 22, "screenshot_width": 1404, "screenshot_height": 990, "grid_rows": 3, "grid_cols": 4},
  "cell": 6,
  "anchor": "center"
}
```

### 截取第二个显示器

按索引截取指定显示器，并保存到自定义目录。

```
tool: capture_screen
args: {"monitor": 2, "save_dir": "C:/screenshots"}
```

### 获取显示器信息

返回所有已连接显示器的信息。

```
tool: get_screen_info
args: {}
```

---

## 2. 窗口管理

### 列出所有窗口

返回所有可见窗口的列表及其标题和位置。

```
tool: list_windows
args: {}
```

### 查找 Chrome 窗口

查找标题包含指定字符串的窗口（不区分大小写）。

```
tool: find_windows
args: {"title_contains": "chrome"}
```

### 聚焦并截取窗口

查找窗口、将其置为前台，并截取其截图。

```
tool: capture_window
args: {"title": "Notepad", "save_dir": "C:/screenshots"}
```

这将：
1. 查找标题中包含 "Notepad" 的窗口
2. 将其置于前台
3. 仅截取该窗口的截图
4. 返回文件路径、窗口位置和尺寸

---

## 3. 鼠标控制

### 单击

```
tool: mouse_click
args: {"x": 500, "y": 300}
```

### 双击

```
tool: mouse_click
args: {"x": 500, "y": 300, "clicks": 2}
```

### 右键点击

```
tool: mouse_click
args: {"x": 500, "y": 300, "button": "right"}
```

### 长按（按住 3 秒）

在指定坐标处按下并按住鼠标按钮指定时长。

```
tool: mouse_click
args: {"x": 500, "y": 300, "hold_seconds": 3.0}
```

### 从一点拖拽到另一点

```
tool: mouse_drag
args: {"start_x": 100, "start_y": 100, "end_x": 800, "end_y": 600, "duration": 0.5}
```

### 移动光标

将光标移动到指定位置，不点击。

```
tool: mouse_move
args: {"x": 960, "y": 540, "duration": 0.25}
```

### 获取当前位置

```
tool: mouse_position
args: {}
```

### 向下滚动

```
tool: mouse_scroll
args: {"clicks": -5}
```

### 在指定位置向上滚动

```
tool: mouse_scroll
args: {"clicks": 3, "x": 500, "y": 300}
```

---

## 4. 键盘控制

### 按下 Enter 键

```
tool: key_press
args: {"keys": ["enter"]}
```

### 按下 Ctrl+C（复制）

```
tool: key_press
args: {"keys": ["ctrl", "c"]}
```

### 按下 Alt+Tab 3 次

以指定间隔多次按下键组合。

```
tool: key_press
args: {"keys": ["alt", "tab"], "presses": 3, "interval": 0.5}
```

### 按住 Shift 键 2 秒

```
tool: key_hold
args: {"keys": ["shift"], "hold_seconds": 2.0}
```

### 输入文本

逐字符输入文本，间隔可配置。

```
tool: key_type
args: {"text": "Hello, World!", "interval": 0.05}
```

### 执行按键序列

执行键盘操作序列，步骤之间有延迟。

```
tool: key_sequence
args: {
  "sequence": [
    {"action": "press", "keys": ["ctrl", "a"], "delay": 0.2},
    {"action": "type", "text": "New content here", "delay": 0.1},
    {"action": "press", "keys": ["enter"], "delay": 0}
  ]
}
```

---

## 5. 组合操作

`mouse_and_keyboard` 工具允许你串联鼠标和键盘操作：

### 打开记事本并输入

通过 Win 键搜索打开记事本，等待加载后输入文本。

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

### 全选文本并替换

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "key_press", "keys": ["ctrl", "a"], "delay": 0.2},
    {"action": "key_type", "text": "Replacement text", "delay": 0.1}
  ]
}
```

### 点击按钮、等待、然后截图

在坐标处点击，等待结果加载，然后截取屏幕。

```
tool: mouse_and_keyboard
args: {
  "actions": [
    {"action": "click", "x": 500, "y": 300, "delay": 0.5},
    {"action": "screenshot", "save_dir": "/tmp/results"}
  ]
}
```

### 拖拽滑块

在起始位置点击并按住，移动到终止位置，然后释放。

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

### 复杂表单填写

点击字段、输入数据、Tab 到下一个字段并重复。最后点击提交并截图。

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

## 6. 附加操作

### 获取剪贴板内容

```
tool: clipboard_get
args: {}
```

### 设置剪贴板并粘贴

设置剪贴板文本，然后使用 `key_press` 传入 `["ctrl", "v"]` 进行粘贴。

```
tool: clipboard_set
args: {"text": "Hello from clipboard!"}
```
然后使用 `key_press` 传入 `["ctrl", "v"]` 粘贴。

### 启动应用程序

通过名称或路径启动应用程序。命令因平台而异。

```
tool: launch_app
args: {"command": "notepad"}   # Windows
tool: launch_app
args: {"command": "TextEdit"}  # macOS
```

### 打开 URL

```
tool: launch_url
args: {"url": "https://example.com"}
```

### 获取像素颜色

返回指定坐标处像素的 RGB 颜色。

```
tool: get_pixel_color
args: {"x": 500, "y": 300}
```

响应: `{"x": 500, "y": 300, "r": 255, "g": 128, "b": 0, "hex": "#ff8000"}`

### 等待

暂停执行指定秒数。

```
tool: wait
args: {"seconds": 2.5}
```

### 快捷键

按下快捷键组合的便捷封装。

```
tool: hotkey
args: {"keys": ["ctrl", "shift", "s"]}  # 另存为
```

---

## 7. 实际场景模式

## 8. 控制平面工作流

### 为模糊桌面指令生成计划

```
tool: plan_desktop_task
args: {"instruction": "打开后台并看下最新报错"}
```

### 执行计划并轮询状态

```
tool: execute_desktop_plan
args: {"plan_id": "plan_abc123"}
```

```
tool: get_execution_status
args: {"run_id": "run_abc123"}
```

### 保存一次成功的操作经验

```
tool: record_workflow_experience
args: {
  "intent": "run_application_flow",
  "instruction": "切到 PyCharm 并运行当前配置",
  "app": "PyCharm",
  "summary": "聚焦窗口、最大化、运行，然后等待控制台稳定",
  "preferred_actions": ["focus_window", "key_press", "wait_until_stable"]
}
```

### 模式：截图→分析→点击

1. 截图
2. LLM 分析图像
3. 点击识别出的元素

```
# Step 1
tool: capture_screen → returns file_path

# [LLM analyzes the image at file_path]

# Step 2
tool: mouse_click → {"x": identified_x, "y": identified_y}
```

### 模式：窗口工作流

1. 查找并聚焦窗口
2. 截取该窗口的截图
3. 在该窗口中执行操作

```
tool: find_windows → {"title_contains": "VS Code"}
tool: capture_window → {"title": "VS Code"}
tool: key_press → {"keys": ["ctrl", "shift", "p"]}
tool: key_type → {"text": "Format Document"}
tool: key_press → {"keys": ["enter"]}
```

### 模式：重复操作循环

使用 `mouse_and_keyboard` 配合包含点击"下一步"按钮的序列：

```
tool: mouse_and_keyboard → {
  "actions": [
    {"action": "click", "x": 500, "y": 300, "delay": 0.5},
    {"action": "key_press", "keys": ["ctrl", "c"], "delay": 0.2},
    {"action": "click", "x": 900, "y": 500, "delay": 0.5}  # 下一步按钮
  ]
}
```

### 模式：等待元素出现后交互

等待页面或元素加载，截屏，确认其出现后进行交互。

```
tool: wait → {"seconds": 3.0}
tool: capture_screen
# [LLM checks if target element appeared]
tool: mouse_click → {"x": element_x, "y": element_y}
```

---

## 按键名称参考

常用按键名称（pyautogui 约定）:

| 按键 | 名称 |
|---|---|
| Enter | `enter` / `return` |
| Tab | `tab` |
| Escape | `escape` |
| Backspace | `backspace` |
| Delete | `delete` |
| Space | `space` |
| 方向键 | `up`, `down`, `left`, `right` |
| 功能键 | `f1` through `f15` |
| 修饰键 | `ctrl`, `alt`, `shift`, `win` (Windows) / `command` (Mac) |
| Home/End | `home`, `end` |
| Page Up/Down | `pageup`, `pagedown` |
| 截屏键 | `printscreen` |

完整列表请参阅 [pyautogui 文档](https://pyautogui.readthedocs.io/en/latest/keyboard.html)。
