# Functional Design

## 1. Tool Invocation Model

All tools follow the same invocation pattern:

```
LLM decides to use a tool
  → MCP client sends: {"method": "tools/call", "params": {"name": "<tool>", "arguments": {...}}}
  → Server dispatches to tool handler function
  → Handler calls utility functions
  → Result serialized to JSON string
  → MCP response: {"content": [{"type": "text", "text": "<JSON>"}]}
  → LLM receives and parses the JSON
```

## 2. Response Format Convention

Every tool returns a JSON object. Common fields:

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether the operation succeeded |
| `message` | str | Human-readable description or error |
| `file_path` | str | Path to saved screenshot (capture tools) |
| `timestamp` | str | ISO-8601 timestamp (capture tools) |

### Example Responses

**Successful click:**
```json
{"success": true, "x": 500, "y": 300, "clicks": 1, "button": "left", "message": "Clicked left 1x at (500, 300)"}
```

**Successful screenshot:**
```json
{"file_path": "/tmp/control_mcp_screenshots/screen_20260320_143022_1920x1080_0_0.png", "timestamp": "2026-03-20T14:30:22.123456", "width": 1920, "height": 1080, "x": 0, "y": 0, "monitor_index": null}
```

**Error:**
```json
{"success": false, "x": 500, "y": 300, "clicks": 1, "button": "left", "message": "pyautogui.FailSafeException: ..."}
```

## 3. Screenshot Filename Convention

Format: `{prefix}_{timestamp}_{WxH}_{x}_{y}.{ext}`

Examples:
- `screen_20260320_143022_123456_1920x1080_0_0.png` — full screen
- `region_20260320_143022_123456_800x600_100_200.png` — region at (100,200), 800x600
- `window_20260320_143022_123456_1024x768_50_80.png` — window at (50,80), 1024x768

## 4. Combined Action Schema

The `mouse_and_keyboard` tool accepts a list of action descriptors. Each action is a dict:

### Mouse Actions

```python
# Move cursor
{"action": "move", "x": 500, "y": 300, "duration": 0.25}

# Click
{"action": "click", "x": 500, "y": 300, "button": "left", "clicks": 1, "hold_seconds": 0}

# Drag
{"action": "drag", "start_x": 100, "start_y": 100, "end_x": 500, "end_y": 500, "button": "left", "duration": 0.5}

# Scroll
{"action": "scroll", "clicks": 3, "x": 500, "y": 300}

# Mouse down (press and hold)
{"action": "mouse_down", "x": 500, "y": 300, "button": "left"}

# Mouse up (release)
{"action": "mouse_up", "x": 500, "y": 300, "button": "left"}
```

### Keyboard Actions

```python
# Press keys
{"action": "key_press", "keys": ["ctrl", "c"]}

# Hold keys
{"action": "key_hold", "keys": ["shift"], "hold_seconds": 2.0}

# Type text
{"action": "key_type", "text": "hello world", "interval": 0.05}
```

### Utility Actions

```python
# Wait
{"action": "wait", "seconds": 1.5}

# Screenshot (inline)
{"action": "screenshot", "save_dir": "/tmp/screenshots"}
```

### Post-Step Delay

Every action accepts an optional `"delay"` field (seconds to wait AFTER the step):

```python
{"action": "click", "x": 500, "y": 300, "delay": 0.5}  # wait 0.5s after clicking
```

## 5. Key Sequence Schema

The `key_sequence` tool accepts a similar list but keyboard-focused:

```python
{"action": "press", "keys": ["ctrl", "a"], "delay": 0.2}
{"action": "type", "text": "Hello", "interval": 0.05, "delay": 0.1}
{"action": "hold", "keys": ["shift"], "hold_seconds": 1.0, "delay": 0}
{"action": "press", "keys": ["enter"], "delay": 0}
```

## 6. Error Handling Flow

```
Tool function called
  → try:
      result = pyautogui_operation()
      return SuccessResult(...)
  except Exception as e:
      return ErrorResult(message=str(e))
```

For combined actions:
- Each step is wrapped in its own try/except
- Failed steps are recorded but don't abort the sequence
- The overall `success` field is `True` only if ALL steps succeeded

## 7. Platform Detection

```python
import platform

system = platform.system()  # "Windows", "Darwin", "Linux"
```

Used in:
- `capture.py`: `_get_platform_window_backend()`
- `server.py`: Windows event loop policy
- `actions.py`: `launch_app()` platform-specific commands

## 8. MCP Server Lifecycle

```
main()
  → asyncio.set_event_loop_policy (Windows only)
  → asyncio.run(_run())
  → stdio_server() context manager
  → server.run(read_stream, write_stream, init_options)
  → [handles list_tools and call_tool requests]
  → [exits when stdin closes]
```

## 9. Tool Registration

Tools are defined as `Tool` objects with:
- `name`: unique identifier
- `description`: what the tool does (LLM reads this)
- `inputSchema`: JSON Schema for parameters

The `@server.list_tools()` handler returns the list.
The `@server.call_tool()` handler dispatches by name.

## 10. Extensibility

To add a new tool:
1. Implement the function in the appropriate `tools/` module
2. Add a `Tool` definition to `TOOLS` in `server.py`
3. Add a dispatch case in `handle_call_tool()`
4. Add tests in `tests/`

No changes to other modules are required.
