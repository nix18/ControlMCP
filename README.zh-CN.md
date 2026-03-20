# ControlMCP

> 用于 LLM 控制电脑的 MCP 服务器 — 屏幕截图、窗口管理、鼠标与键盘自动化。

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[English](README.md)**

---

## 概述

ControlMCP 是一个 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 服务器，赋予 LLM **查看和控制电脑**的能力 — 截图、管理窗口、移动/点击鼠标、键盘输入，并将这些操作串联为复杂的自动化工作流。

设计为 **pip 安装** 和 **一键启动**。

## 快速开始

### 安装

```bash
pip install control-mcp
```

或从源码安装：

```bash
git clone <repo-url>
cd ControlMCP
pip install -e .
```

### 启动

```bash
control-mcp
```

服务器通过 **stdio**（标准 MCP 传输）通信。请在 MCP 客户端中配置连接到 `control-mcp` 命令。

### MCP 客户端配置

添加到您的 MCP 客户端配置（如 Claude Desktop、Cursor 等）：

```json
{
  "mcpServers": {
    "control-mcp": {
      "command": "control-mcp",
      "args": []
    }
  }
}
```

## 工具列表（共 24 个）

### 屏幕截图

| 工具 | 描述 |
|------|------|
| `capture_screen` | 全屏或指定显示器截图 |
| `capture_region` | 区域截图（x, y, 宽, 高） |
| `get_screen_info` | 列出所有显示器及其分辨率 |

### 窗口管理

| 工具 | 描述 |
|------|------|
| `list_windows` | 列出所有可见窗口 |
| `find_windows` | 按标题子串查找窗口 |
| `focus_window` | 将窗口带到前台 |
| `capture_window` | 聚焦并截取指定窗口 |

### 鼠标控制

| 工具 | 描述 |
|------|------|
| `mouse_click` | 在坐标处点击（单击/双击/多击/长按） |
| `mouse_drag` | 从点 A 拖动到点 B |
| `mouse_move` | 移动光标（不点击） |
| `mouse_position` | 获取当前光标位置 |
| `mouse_scroll` | 滚轮上下滚动 |

### 键盘控制

| 工具 | 描述 |
|------|------|
| `key_press` | 按键或快捷键组合 |
| `key_hold` | 按住指定时间 |
| `key_type` | 逐字输入文本 |
| `key_sequence` | 执行定时键盘操作序列 |

### 组合操作

| 工具 | 描述 |
|------|------|
| `mouse_and_keyboard` | 执行鼠标+键盘+等待+截图的混合操作序列 |

### 附加操作

| 工具 | 描述 |
|------|------|
| `clipboard_get` | 获取剪贴板文本 |
| `clipboard_set` | 设置剪贴板文本 |
| `launch_app` | 启动应用程序 |
| `launch_url` | 在浏览器中打开 URL |
| `wait` | 暂停 N 秒 |
| `get_pixel_color` | 获取屏幕坐标处的 RGB 颜色 |
| `hotkey` | 按下键盘快捷键 |
| `screenshot` | capture_screen 的别名 |

## 使用示例

完整使用示例请参阅 [docs/zh-CN/TUTORIAL.md](docs/zh-CN/TUTORIAL.md)。

```json
// 截取屏幕
{"tool": "capture_screen", "args": {}}

// 在 (500, 300) 处点击
{"tool": "mouse_click", "args": {"x": 500, "y": 300}}

// 组合：点击 → 全选 → 输入
{"tool": "mouse_and_keyboard", "args": {"actions": [
    {"action": "click", "x": 500, "y": 300},
    {"action": "key_press", "keys": ["ctrl", "a"]},
    {"action": "key_type", "text": "新文本"}
]}}
```

## 文档

| 文档 | 描述 |
|------|------|
| [README.md](README.md) | 英文版 |
| [README.zh-CN.md](README.zh-CN.md) | 本文件（中文版） |
| [docs/zh-CN/REQUIREMENTS.md](docs/zh-CN/REQUIREMENTS.md) | 需求分析 |
| [docs/zh-CN/ARCHITECTURE.md](docs/zh-CN/ARCHITECTURE.md) | 架构设计 |
| [docs/zh-CN/MODULE_DESIGN.md](docs/zh-CN/MODULE_DESIGN.md) | 模块设计 |
| [docs/zh-CN/FUNCTIONAL_DESIGN.md](docs/zh-CN/FUNCTIONAL_DESIGN.md) | 功能设计 |
| [docs/zh-CN/TUTORIAL.md](docs/zh-CN/TUTORIAL.md) | 教程与示例 |

## 项目结构

```
ControlMCP/
├── README.md                          # 英文版
├── README.zh-CN.md                    # 本文件
├── LICENSE                            # MIT 许可证
├── pyproject.toml                     # 包配置
├── src/
│   └── control_mcp/
│       ├── __init__.py
│       ├── server.py                  # MCP 服务器 + 工具注册
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── responses.py           # 结构化响应类型
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── screen.py              # 屏幕截图工具
│       │   ├── window.py              # 窗口管理工具
│       │   ├── mouse.py               # 鼠标控制工具
│       │   ├── keyboard.py            # 键盘控制工具
│       │   ├── combined.py            # 组合操作
│       │   └── actions.py             # 附加操作
│       └── utils/
│           ├── __init__.py
│           ├── capture.py             # 截图工具函数
│           ├── _win_window.py         # Windows 后端
│           ├── _mac_window.py         # macOS 后端
│           └── _linux_window.py       # Linux 后端
├── docs/
│   ├── REQUIREMENTS.md                # 英文需求分析
│   ├── ARCHITECTURE.md                # 英文架构设计
│   ├── MODULE_DESIGN.md               # 英文模块设计
│   ├── FUNCTIONAL_DESIGN.md           # 英文功能设计
│   ├── TUTORIAL.md                    # 英文教程
│   └── zh-CN/                        # 中文文档
│       ├── REQUIREMENTS.md
│       ├── ARCHITECTURE.md
│       ├── MODULE_DESIGN.md
│       ├── FUNCTIONAL_DESIGN.md
│       └── TUTORIAL.md
└── tests/
    ├── __init__.py
    ├── test_schemas.py                # 22 个测试
    ├── test_screen.py                 # 6 个测试
    ├── test_window.py                 # 11 个测试
    ├── test_mouse.py                  # 13 个测试
    ├── test_keyboard.py               # 16 个测试
    ├── test_combined.py               # 12 个测试
    └── test_actions.py                # 13 个测试
```

## 平台支持

| 平台 | 屏幕截图 | 窗口管理 | 鼠标/键盘 |
|------|---------|---------|----------|
| Windows | ✅ mss | ✅ pygetwindow | ✅ pyautogui |
| macOS | ✅ mss | ✅ Quartz | ✅ pyautogui |
| Linux | ✅ mss | ✅ xlib | ✅ pyautogui |

## 许可证

MIT
