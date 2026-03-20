# ControlMCP

> MCP server for LLM-controlled computer operations — screen capture, window management, mouse & keyboard automation.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[中文文档](README.zh-CN.md)**

---

## Overview

ControlMCP is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives LLMs the ability to **see and control a computer** — take screenshots, manage windows, move/click the mouse, type on the keyboard, and chain all of these into complex automation workflows.

It is designed to be **pip-installable** and **one-command startable**.

## Quick Start

### Installation

```bash
pip install control-mcp
```

Or install from source:

```bash
git clone <repo-url>
cd ControlMCP
pip install -e .
```

### Launch

```bash
control-mcp
```

The server communicates over **stdio** (standard MCP transport). Configure your MCP client to connect to the `control-mcp` command.

### MCP Client Configuration

Add to your MCP client config (e.g. Claude Desktop, Cursor, etc.):

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

## Tools (24 total)

### Screen Capture

| Tool | Description |
|------|-------------|
| `capture_screen` | Full screen or monitor screenshot |
| `capture_region` | Region screenshot (x, y, width, height) |
| `get_screen_info` | List all monitors with resolution |

### Window Management

| Tool | Description |
|------|-------------|
| `list_windows` | List all visible windows |
| `find_windows` | Find windows by title substring |
| `focus_window` | Bring a window to the foreground |
| `capture_window` | Focus + screenshot a specific window |

### Mouse Control

| Tool | Description |
|------|-------------|
| `mouse_click` | Click at coordinates (single/double/multi/hold) |
| `mouse_drag` | Drag from point A to point B |
| `mouse_move` | Move cursor without clicking |
| `mouse_position` | Get current cursor position |
| `mouse_scroll` | Scroll wheel up/down |

### Keyboard Control

| Tool | Description |
|------|-------------|
| `key_press` | Press keys or hotkey combinations |
| `key_hold` | Hold keys for a duration |
| `key_type` | Type text character by character |
| `key_sequence` | Execute a timed sequence of key actions |

### Combined Operations

| Tool | Description |
|------|-------------|
| `mouse_and_keyboard` | Execute a mixed sequence of mouse + keyboard + wait + screenshot actions |

### Additional Actions

| Tool | Description |
|------|-------------|
| `clipboard_get` | Get clipboard text |
| `clipboard_set` | Set clipboard text |
| `launch_app` | Launch an application |
| `launch_url` | Open a URL in the browser |
| `wait` | Pause for N seconds |
| `get_pixel_color` | Get RGB color at screen coordinates |
| `hotkey` | Press a keyboard shortcut |
| `screenshot` | Alias for capture_screen |

## Examples

See [docs/TUTORIAL.md](docs/TUTORIAL.md) for comprehensive usage examples.

```json
// Take a screenshot
{"tool": "capture_screen", "args": {}}

// Click at (500, 300)
{"tool": "mouse_click", "args": {"x": 500, "y": 300}}

// Combined: click → select all → type
{"tool": "mouse_and_keyboard", "args": {"actions": [
    {"action": "click", "x": 500, "y": 300},
    {"action": "key_press", "keys": ["ctrl", "a"]},
    {"action": "key_type", "text": "New text"}
]}}
```

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file |
| [README.zh-CN.md](README.zh-CN.md) | Chinese version of this file |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Requirements analysis |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture design |
| [docs/MODULE_DESIGN.md](docs/MODULE_DESIGN.md) | Module design |
| [docs/FUNCTIONAL_DESIGN.md](docs/FUNCTIONAL_DESIGN.md) | Functional design |
| [docs/TUTORIAL.md](docs/TUTORIAL.md) | Tutorial & examples |
| [skills/computer-control/](skills/computer-control/) | Agent Skill: computer operation SOPs |

## Agent Skill

The `skills/computer-control/` folder contains a ready-to-use Agent Skill that teaches LLMs how to operate computers proficiently:

- **5 Golden Rules**: Keyboard-first, coordinate conversion, screenshot cost awareness, wait after action, verify before click
- **7 Standard SOPs**: Window ops, screenshot-click, key sequences, compound ops, pixel verification, clipboard input, file navigation
- **IDE Shortcut Tables**: IntelliJ IDEA, VS Code, Eclipse (40+ shortcuts)
- **Browser/System Shortcuts**: 20+ browser shortcuts, Windows/macOS operations
- **7 Common Pitfalls**: Coordinate confusion, DPI scaling, window occlusion, input method, dual monitors, etc.

Copy `skills/computer-control/` to your Agent's skills directory to enable.

## Project Structure

```
ControlMCP/
├── README.md                          # This file
├── README.zh-CN.md                    # Chinese README
├── LICENSE                            # MIT License
├── pyproject.toml                     # Package config
├── src/
│   └── control_mcp/
│       ├── __init__.py
│       ├── server.py                  # MCP server + tool registration
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── responses.py           # Structured response types
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── screen.py              # Screen capture tools
│       │   ├── window.py              # Window management tools
│       │   ├── mouse.py               # Mouse control tools
│       │   ├── keyboard.py            # Keyboard control tools
│       │   ├── combined.py            # Combined operations
│       │   └── actions.py             # Additional actions
│       └── utils/
│           ├── __init__.py
│           ├── capture.py             # Capture utilities (JPEG, resize)
│           ├── _win_window.py         # Windows backend
│           ├── _mac_window.py         # macOS backend
│           └── _linux_window.py       # Linux backend
├── skills/
│   └── computer-control/              # Agent Skill: computer operation SOPs
│       ├── SKILL.md                   # Main skill instructions
│       ├── docs/
│       │   └── coordinate-system.md   # Coordinate system reference
│       └── README.md                  # Installation guide
├── docs/
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── MODULE_DESIGN.md
│   ├── FUNCTIONAL_DESIGN.md
│   ├── TUTORIAL.md
│   └── zh-CN/                        # Chinese documentation
│       ├── REQUIREMENTS.md
│       ├── ARCHITECTURE.md
│       ├── MODULE_DESIGN.md
│       ├── FUNCTIONAL_DESIGN.md
│       └── TUTORIAL.md
└── tests/
    ├── __init__.py
    ├── test_schemas.py                # 22 tests
    ├── test_screen.py                 # 6 tests
    ├── test_window.py                 # 11 tests
    ├── test_mouse.py                  # 13 tests
    ├── test_keyboard.py               # 16 tests
    ├── test_combined.py               # 12 tests
    └── test_actions.py                # 13 tests
```

## Platform Support

| Platform | Screen Capture | Window Management | Mouse/Keyboard |
|----------|---------------|-------------------|----------------|
| Windows  | ✅ mss        | ✅ pygetwindow    | ✅ pyautogui   |
| macOS    | ✅ mss        | ✅ Quartz         | ✅ pyautogui   |
| Linux    | ✅ mss        | ✅ xlib           | ✅ pyautogui   |

## License

MIT
