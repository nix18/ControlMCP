# ControlMCP

> 😆你已经是一个成熟的大模型了，要学会自己操作电脑了
</br></br>🛠️用于 LLM 控制电脑的 MCP 服务器 — 屏幕截图、窗口管理、鼠标与键盘自动化。

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

**[English](README.md)**

---

## 概述

ControlMCP 是一个 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 服务器，赋予 LLM **查看和控制电脑**的能力 — 截图、管理窗口、移动/点击鼠标、键盘输入，并将这些操作串联为复杂的自动化工作流。

仓库同时内置了可直接复用的 Agent Skill：[skills/computer-control/](skills/computer-control/)。它把桌面操作 SOP、快捷键经验、JetBrains IDE 工作流以及截图坐标到点击坐标的换算规则打包好了，适合支持 skills 的 Agent 直接接入使用。

## 快速开始

### 安装

从源码安装：

```bash
git clone https://github.com/nix18/ControlMCP.git
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

## 工具列表（共 34 个）

### 控制平面

| 工具 | 描述 |
|------|------|
| `plan_desktop_task` | 将模糊桌面指令归一化为结构化执行计划 |
| `execute_desktop_plan` | 通过带守卫的执行器运行结构化计划 |
| `get_execution_status` | 查询高层执行任务的当前状态 |
| `confirm_sensitive_action` | 显式批准或拒绝敏感操作 |
| `recover_execution_context` | 在快捷键误用或界面跑偏后恢复上下文 |
| `record_workflow_experience` | 持久化可复用的电脑操作经验 |

### 屏幕截图

| 工具 | 描述 |
|------|------|
| `capture_screen` | 全屏或指定显示器截图 |
| `capture_region` | 区域截图（x, y, 宽, 高） |
| `capture_scroll_region` | 在固定区域内滚动并拼接成长截图 |
| `get_screen_info` | 列出所有显示器及其分辨率 |
| `read_screenshot_base64` | 将截图文件读取为 Base64 文本 |
| `resolve_grid_target` | 将网格编号 + 锚点换算成精确屏幕坐标 |
| `click_grid_target` | 直接用截图网格元数据解析并点击 |

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
## 使用示例

完整使用示例请参阅 [docs/zh-CN/TUTORIAL.md](docs/zh-CN/TUTORIAL.md)。

```json
// 先规划模糊桌面任务
{"tool": "plan_desktop_task", "args": {"instruction": "切到 PyCharm 并运行当前配置"}}

// 执行生成后的计划
{"tool": "execute_desktop_plan", "args": {"plan_id": "plan_abc123"}}

// 截取屏幕
{"tool": "capture_screen", "args": {}}

// 对无多模态读取能力的模型，把截图文件读取为 Base64 文本
{"tool": "read_screenshot_base64", "args": {"file_path": "/tmp/screen.jpg"}}

// 在 (500, 300) 处点击
{"tool": "mouse_click", "args": {"x": 500, "y": 300}}

// 组合：点击 → 全选 → 输入
{"tool": "mouse_and_keyboard", "args": {"actions": [
    {"action": "click", "x": 500, "y": 300},
    {"action": "key_press", "keys": ["ctrl", "a"]},
    {"action": "key_type", "text": "新文本"}
]}}
```

## 重构后的推荐工作流

ControlMCP 现在支持“控制平面优先”的桌面自动化工作流：

1. 用 `plan_desktop_task` 先把自然语言操作意图拆成结构化计划
2. 审核或直接执行该计划
3. 让 guarded executor 自动选择更高效的观察方式（窗口截图 / 区域截图 / 长截图）
4. 对关键步骤做验证，并在上下文丢失时恢复
5. 对支付、密码、资产类动作强制要求显式确认
6. 把成功经验沉淀下来供后续复用

对于目标很小或视觉定位不稳定的点击，还可以给 `capture_screen`、`capture_region`、
`capture_window` 传入 `grid_rows` 和 `grid_cols`，同时生成一张 `grid_file_path`
网格图，再用 `resolve_grid_target` 把“网格编号 + 锚点”换算成更稳定的点击坐标。

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
| [skills/computer-control/](skills/computer-control/) | Agent Skill：电脑操作 SOP |
| [skills/computer-control/README.md](skills/computer-control/README.md) | Skill 安装与使用说明 |
| [skills/computer-control/docs/window-management.md](skills/computer-control/docs/window-management.md) | 窗口修复与窗口快捷键参考 |
| [skills/computer-control/docs/idea-run-workflow.md](skills/computer-control/docs/idea-run-workflow.md) | JetBrains IDE 启动与日志观察流程 |

## Agent Skill

项目内置了一个可直接复用的 Agent Skill：`skills/computer-control/`。

### Skill 包含内容

- `SKILL.md`：主技能文档，包含操作法则、SOP、快捷键速查与常见误判
- `docs/coordinate-system.md`：从截图坐标到屏幕点击坐标的换算说明
- `docs/window-management.md`：窗口最大化、恢复、分屏与窗口救援流程
- `docs/idea-run-workflow.md`：JetBrains IDE 启动配置、切换 Run 面板、判断日志稳定的流程
- `README.md`：Skill 局部安装与使用说明

### Skill 能解决什么

- 键盘优先的桌面自动化
- 先规划后执行的高精度桌面控制
- 窗口被最小化、半屏、布局异常时的修复
- 精确点击前的坐标换算
- IntelliJ IDEA / PyCharm 的运行配置选择、Run 面板切换与日志停止更新判定
- 支付、密码、资产类动作的确认闸门
- JetBrains 快捷键与点击行为不达预期时的官方资料兜底

### 如何安装到 Agent

你可以选择“复制目录”或“创建软链接”两种方式，把 `skills/computer-control/` 加到对应 Agent 的技能目录。

方式 1：复制目录

```bash
# Codex CLI
cp -r skills/computer-control ~/.codex/skills/

# Claude Code
cp -r skills/computer-control ~/.claude/skills/

# OpenCode
cp -r skills/computer-control ~/.config/opencode/skills/
```

方式 2：创建软链接

macOS / Linux：

```bash
# Codex CLI
ln -s "$(pwd)/skills/computer-control" ~/.codex/skills/computer-control

# Claude Code
ln -s "$(pwd)/skills/computer-control" ~/.claude/skills/computer-control

# OpenCode
ln -s "$(pwd)/skills/computer-control" ~/.config/opencode/skills/computer-control
```

Windows（必要时以管理员身份运行命令提示符）：

```bat
mklink /D "%USERPROFILE%\.codex\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.claude\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.config\opencode\skills\computer-control" "%CD%\skills\computer-control"
```

软链接方式更适合持续迭代 Skill，因为仓库里的修改会立即反映到 Agent 的技能目录。

如果你的 Agent 支持自定义技能路径，也可以直接引用当前目录。

### 如何使用

安装后，可以直接在提示词里这样使用：

- `使用 $computer-control 重启 IDEA 中的应用，并等待日志停止更新`
- `使用 $computer-control 最大化目标窗口后截图`
- `使用 $computer-control 优先通过快捷键操作 PyCharm`

Skill 的详细说明可继续阅读 [skills/computer-control/README.md](skills/computer-control/README.md)。

## 项目结构

```
ControlMCP/
├── README.md                          # 英文版
├── README.zh-CN.md                    # 本文件
├── LICENSE                            # GNU GPLv3 许可证
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
├── skills/
│   └── computer-control/              # Agent Skill：电脑操作 SOP
│       ├── SKILL.md                   # 主技能文档
│       ├── docs/
│       │   ├── coordinate-system.md   # 坐标体系参考
│       │   ├── window-management.md   # 窗口管理参考
│       │   └── idea-run-workflow.md   # JetBrains IDE 启动与日志流程
│       └── README.md                  # Skill 安装与使用说明
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

GNU General Public License v3.0（GPLv3）
