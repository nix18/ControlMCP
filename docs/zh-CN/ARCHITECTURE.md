# 架构设计

## 1. 系统概览

ControlMCP 服务器充当 LLM 客户端和操作系统之间的桥梁，提供基于工具的屏幕截图、窗口管理、鼠标控制、键盘控制等功能。

```
┌─────────────────────────────────────────────────────────┐
│                   MCP Client (LLM)                      │
│           (Claude Desktop, Cursor, custom client)       │
└────────────────────────┬────────────────────────────────┘
                         │  stdio (JSON-RPC)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   ControlMCP Server                     │
│                                                         │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │ MCP Protocol│  │         Tool Registry            │  │
│  │  (server.py)│──│  24 tools across 6 modules       │  │
│  └─────────────┘  └──────────────┬───────────────────┘  │
│                                  │                      │
│  ┌───────────────────────────────▼───────────────────┐  │
│  │              Tool Modules                         │  │
│  │  ┌──────┐ ┌──────┐ ┌─────┐ ┌──────┐ ┌────────┐  │  │
│  │  │screen│ │window│ │mouse│ │ kbd  │ │combined│  │  │
│  │  └──┬───┘ └──┬───┘ └──┬──┘ └──┬───┘ └───┬────┘  │  │
│  │     │        │        │       │         │        │  │
│  └─────┼────────┼────────┼───────┼─────────┼────────┘  │
│        │        │        │       │         │           │
│  ┌─────▼────────▼────────▼───────▼─────────▼────────┐  │
│  │              Utility Layer                        │  │
│  │  ┌────────────┐  ┌──────────────────────────┐    │  │
│  │  │ capture.py │  │ Platform Backends         │    │  │
│  │  │ (mss+PIL)  │  │ _win / _mac / _linux      │    │  │
│  │  └────────────┘  └──────────────────────────┘    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Schema Layer                         │  │
│  │  ScreenshotResult, ClickResult, DragResult, ...   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    OS / Hardware                         │
│         Screen, Mouse, Keyboard, Window Manager         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 组件职责

### 2.1 MCP 协议层 (`server.py`)

- 创建 MCP `Server` 实例
- 使用 JSON schema 定义所有 `Tool` 对象
- 将 `call_tool` 请求分发到对应的处理函数
- 将结果包装为 `TextContent` 响应
- 优雅地处理错误

### 2.2 工具模块 (`tools/`)

每个工具模块包含纯函数，它们：
- 接受类型化参数
- 调用工具函数执行实际工作
- 返回 JSON 序列化的结构化响应
- 独立于 MCP 协议细节

### 2.3 工具层 (`utils/`)

| 模块 | 描述 |
|---|------|
| **`capture.py`** | 使用 `mss` + `Pillow` 的跨平台屏幕/窗口捕获 |
| **`_win_window.py`** | 通过 `pygetwindow` 的 Windows 特定窗口操作 |
| **`_mac_window.py`** | 通过 Quartz 的 macOS 特定窗口操作 |
| **`_linux_window.py`** | 通过 `xlib` 的 Linux 特定窗口操作 |

### 2.4 Schema 层 (`schemas/`)

- 所有结构化响应类型的数据类
- 通过 `to_json()` / `to_dict()` 方法进行 JSON 序列化
- 截图的文件名生成

---

## 3. 数据流

### 截图流程

```
LLM → capture_screen(save_dir="/tmp") → tool_capture_screen()
  → capture_full_screen() → mss.grab() → PIL.save()
  → ScreenshotResult(file_path=..., timestamp=..., width=..., height=...)
  → JSON string → TextContent → MCP Response → LLM
```

### 鼠标点击流程

```
LLM → mouse_click(x=500, y=300, button="left") → tool_mouse_click()
  → pyautogui.moveTo(500, 300) → pyautogui.click()
  → ClickResult(success=True, x=500, y=300, ...)
  → JSON string → TextContent → MCP Response → LLM
```

### 组合操作流程

```
LLM → mouse_and_keyboard(actions=[...]) → tool_mouse_and_keyboard()
  → for each action: dispatch to pyautogui operation
  → CompositeActionResult(success=..., steps_completed=..., results=[...])
  → JSON string → TextContent → MCP Response → LLM
```

---

## 4. 技术选型

| 组件 | 技术 | 选择理由 |
|---|---|---|
| MCP SDK | `mcp` | 官方 Python MCP SDK |
| 屏幕截图 | `mss` + `Pillow` | 快速跨平台截图、图像处理 |
| 窗口管理 (Win) | `pygetwindow` | 简洁、维护良好 |
| 窗口管理 (Mac) | `Quartz` (pyobjc) | 原生 macOS API |
| 窗口管理 (Linux) | `python-xlib` | 标准 X11 接口 |
| 鼠标键盘 | `pyautogui` | 跨平台、广泛使用、可靠 |
| 剪贴板 | `pyperclip` | 简单的跨平台剪贴板 |
| 打包 | `hatchling` | 现代 Python 构建后端 |

---

## 5. 错误处理策略

- 所有工具函数捕获异常并返回结构化错误响应
- 没有异常会传播到 MCP 协议层
- 每个响应都包含 `success` 字段
- 详细错误信息在 `message` 字段中
- 尽力进行清理（例如，出错时释放按住的键）

---

## 6. 跨平台策略

- `capture.py` 中为屏幕操作提供公共接口
- 运行时通过 `platform.system()` 检测平台
- 动态导入平台特定后端
- 优雅降级（例如，无 pyperclip 时的剪贴板操作）
