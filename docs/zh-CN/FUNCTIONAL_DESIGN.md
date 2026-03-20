# 功能设计

## 1. 工具调用模型

所有工具遵循相同的调用模式：

```
LLM decides to use a tool
  → MCP client sends: {"method": "tools/call", "params": {"name": "<tool>", "arguments": {...}}}
  → Server dispatches to tool handler function
  → Handler calls utility functions
  → Result serialized to JSON string
  → MCP response: {"content": [{"type": "text", "text": "<JSON>"}]}
  → LLM receives and parses the JSON
```

---

## 2. 响应格式约定

每个工具返回一个 JSON 对象。通用字段如下：

| 字段 | 类型 | 描述 |
|---|---|---|
| `success` | bool | 操作是否成功 |
| `message` | str | 可读的描述或错误信息 |
| `file_path` | str | 截图保存路径（截图工具） |
| `timestamp` | str | ISO-8601 时间戳（截图工具） |

### 响应示例

**成功点击:**
```json
{"success": true, "x": 500, "y": 300, "clicks": 1, "button": "left", "message": "Clicked left 1x at (500, 300)"}
```

**成功截图:**
```json
{"file_path": "/tmp/control_mcp_screenshots/screen_20260320_143022_1920x1080_0_0.png", "timestamp": "2026-03-20T14:30:22.123456", "width": 1920, "height": 1080, "x": 0, "y": 0, "monitor_index": null}
```

**错误:**
```json
{"success": false, "x": 500, "y": 300, "clicks": 1, "button": "left", "message": "pyautogui.FailSafeException: ..."}
```

---

## 3. 截图文件名约定

格式：`{prefix}_{timestamp}_{WxH}_{x}_{y}.{ext}`

- `screen_20260320_143022_123456_1920x1080_0_0.png` — 全屏
- `region_20260320_143022_123456_800x600_100_200.png` — (100,200) 处的 800x600 区域
- `window_20260320_143022_123456_1024x768_50_80.png` — (50,80) 处的 1024x768 窗口

---

## 4. 组合操作 Schema

`mouse_and_keyboard` 工具接受操作描述符列表。每个操作是一个字典：

### 鼠标操作

```python
# 移动光标
{"action": "move", "x": 500, "y": 300, "duration": 0.25}

# 点击
{"action": "click", "x": 500, "y": 300, "button": "left", "clicks": 1, "hold_seconds": 0}

# 拖拽
{"action": "drag", "start_x": 100, "start_y": 100, "end_x": 500, "end_y": 500, "button": "left", "duration": 0.5}

# 滚动
{"action": "scroll", "clicks": 3, "x": 500, "y": 300}

# 鼠标按下（按住）
{"action": "mouse_down", "x": 500, "y": 300, "button": "left"}

# 鼠标释放
{"action": "mouse_up", "x": 500, "y": 300, "button": "left"}
```

### 键盘操作

```python
# 按键
{"action": "key_press", "keys": ["ctrl", "c"]}

# 按住键
{"action": "key_hold", "keys": ["shift"], "hold_seconds": 2.0}

# 输入文本
{"action": "key_type", "text": "hello world", "interval": 0.05}
```

### 辅助操作

```python
# 等待
{"action": "wait", "seconds": 1.5}

# 截图（内联）
{"action": "screenshot", "save_dir": "/tmp/screenshots"}
```

### 步骤后延迟

每个操作都接受一个可选的 `"delay"` 字段（步骤执行后等待的秒数）：

```python
{"action": "click", "x": 500, "y": 300, "delay": 0.5}  # 点击后等待 0.5 秒
```

---

## 5. 按键序列 Schema

`key_sequence` 工具接受类似的列表，但专注于键盘操作：

```python
{"action": "press", "keys": ["ctrl", "a"], "delay": 0.2}         # 按下 Ctrl+A
{"action": "type", "text": "Hello", "interval": 0.05, "delay": 0.1}  # 输入 "Hello"
{"action": "hold", "keys": ["shift"], "hold_seconds": 1.0, "delay": 0}  # 按住 Shift
{"action": "press", "keys": ["enter"], "delay": 0}               # 按下 Enter
```

---

## 6. 错误处理流程

```
Tool function called
  → try:
      result = pyautogui_operation()
      return SuccessResult(...)
  except Exception as e:
      return ErrorResult(message=str(e))
```

对于组合操作：
- 每个步骤都包裹在自己的 try/except 中
- 失败的步骤会被记录但不会中止序列
- 仅当所有步骤都成功时，整体 `success` 字段才为 `True`

---

## 7. 平台检测

```python
import platform

system = platform.system()  # "Windows", "Darwin", "Linux"
```

使用位置：
- `capture.py`: `_get_platform_window_backend()`
- `server.py`: Windows 事件循环策略
- `actions.py`: `launch_app()` 平台特定命令

---

## 8. MCP 服务器生命周期

```
main()
  → asyncio.set_event_loop_policy (Windows only)
  → asyncio.run(_run())
  → stdio_server() context manager
  → server.run(read_stream, write_stream, init_options)
  → [handles list_tools and call_tool requests]
  → [exits when stdin closes]
```

---

## 9. 工具注册

工具定义为 `Tool` 对象，包含：
- `name`：唯一标识符
- `description`：工具功能描述（LLM 读取此信息）
- `inputSchema`：参数的 JSON Schema

`@server.list_tools()` 处理器返回工具列表。
`@server.call_tool()` 处理器按名称分发调用。

---

## 10. 可扩展性

添加新工具的步骤：
1. 在相应的 `tools/` 模块中实现函数
2. 在 `server.py` 的 `TOOLS` 中添加 `Tool` 定义
3. 在 `handle_call_tool()` 中添加分发分支
4. 在 `tests/` 中添加测试

无需修改其他模块。
