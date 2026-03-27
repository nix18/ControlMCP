# ControlMCP

> MCP server for LLM-controlled computer operations — screen capture, window management, mouse & keyboard automation.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

**[中文文档](README.zh-CN.md)**

---

## Overview

ControlMCP is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives LLMs the ability to **see and control a computer** — take screenshots, manage windows, move/click the mouse, type on the keyboard, and chain all of these into complex automation workflows.

The repository also ships with a reusable agent skill at [skills/computer-control/](skills/computer-control/). It packages desktop-operation SOPs, shortcut guidance, JetBrains IDE workflows, and screenshot-to-click coordinate rules for agents that support skills.

## Quick Start

### Installation

install from source:

```bash
git clone https://github.com/nix18/ControlMCP.git
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

## Tools (34 total)

### Control Plane

| Tool | Description |
|------|-------------|
| `plan_desktop_task` | Convert a vague desktop instruction into a structured plan |
| `execute_desktop_plan` | Run a structured plan through the guarded executor |
| `get_execution_status` | Query the current status of a high-level execution run |
| `confirm_sensitive_action` | Explicitly approve or reject a sensitive action |
| `recover_execution_context` | Rebuild context after shortcut misuse or UI drift |
| `record_workflow_experience` | Persist reusable workflow experience |

### Screen Capture

| Tool | Description |
|------|-------------|
| `capture_screen` | Full screen or monitor screenshot |
| `capture_region` | Region screenshot (x, y, width, height) |
| `capture_scroll_region` | Stitch a long screenshot while scrolling inside a fixed region |
| `get_screen_info` | List all monitors with resolution |
| `read_screenshot_base64` | Read a screenshot file as Base64 text |
| `resolve_grid_target` | Convert a grid cell + anchor into precise screen coordinates |
| `click_grid_target` | Resolve screenshot grid metadata and click directly |

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

## Examples

See [docs/TUTORIAL.md](docs/TUTORIAL.md) for comprehensive usage examples.

```json
// Plan a vague desktop task first
{"tool": "plan_desktop_task", "args": {"instruction": "Switch to PyCharm and run the current config"}}

// Execute a generated plan
{"tool": "execute_desktop_plan", "args": {"plan_id": "plan_abc123"}}

// Take a screenshot
{"tool": "capture_screen", "args": {}}

// Read that screenshot as Base64 text for non-multimodal models
{"tool": "read_screenshot_base64", "args": {"file_path": "/tmp/screen.jpg"}}

// Click at (500, 300)
{"tool": "mouse_click", "args": {"x": 500, "y": 300}}

// Combined: click → select all → type
{"tool": "mouse_and_keyboard", "args": {"actions": [
    {"action": "click", "x": 500, "y": 300},
    {"action": "key_press", "keys": ["ctrl", "a"]},
    {"action": "key_type", "text": "New text"}
]}}
```

## Rebuilt Workflow

ControlMCP now supports a control-plane-first workflow for higher precision desktop automation:

1. Normalize the user instruction with `plan_desktop_task`
2. Review or directly execute the structured plan
3. Let the guarded executor choose a faster observation strategy (`capture_window` / `capture_region` / `capture_scroll_region`)
4. Verify each critical step and recover when context is lost
5. Require explicit confirmation for payment/password/asset-related actions
6. Save successful workflow experience for future runs

For small or visually ambiguous targets, you can also ask `capture_screen`, `capture_region`,
or `capture_window` to generate a second `grid_file_path` overlay image with `grid_rows` and
`grid_cols`, then convert a chosen cell + anchor through `resolve_grid_target` before clicking.

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
| [skills/computer-control/README.md](skills/computer-control/README.md) | Skill-specific install and usage guide |
| [skills/computer-control/docs/window-management.md](skills/computer-control/docs/window-management.md) | Window rescue and window shortcut reference |
| [skills/computer-control/docs/idea-run-workflow.md](skills/computer-control/docs/idea-run-workflow.md) | JetBrains IDE run/log observation workflow |

## Agent Skill

The `skills/computer-control/` folder contains a ready-to-use Agent Skill that teaches LLMs how to operate computers proficiently.

### What is included

- `SKILL.md`: the main skill instructions, SOPs, shortcut tables, and common failure patterns
- `docs/coordinate-system.md`: coordinate conversion reference for screenshot-to-click workflows
- `docs/window-management.md`: window maximize/restore/snap shortcuts and window recovery workflow
- `docs/idea-run-workflow.md`: JetBrains IDE startup, run-panel switching, and log stabilization workflow
- `README.md`: skill-local installation and usage notes

### What the skill covers

- **Keyboard-first automation**: prefer shortcuts over UI clicking whenever possible
- **Plan-before-act control plane**: normalize ambiguous instructions before touching the desktop
- **Window recovery**: fix minimized, half-screen, or partially restored windows before further actions
- **Coordinate-safe clicking**: convert screenshot-local coordinates into screen coordinates explicitly
- **IDE workflows**: IntelliJ IDEA / PyCharm run-configuration selection, run-panel switching, and log monitoring
- **Sensitive-action gating**: require confirmation before payment/password/asset-related steps
- **Operational fallback**: when JetBrains shortcuts do not behave as expected, check the local `ReferenceCard.pdf` or JetBrains official documentation

### Install the skill into your agent

You can either copy `skills/computer-control/` into your agent's skill directory, or add it via a symbolic link.

Option 1: copy the directory

```bash
# Codex CLI
cp -r skills/computer-control ~/.codex/skills/

# Claude Code
cp -r skills/computer-control ~/.claude/skills/

# OpenCode
cp -r skills/computer-control ~/.config/opencode/skills/
```

Option 2: create a symbolic link

On macOS / Linux:

```bash
# Codex CLI
ln -s "$(pwd)/skills/computer-control" ~/.codex/skills/computer-control

# Claude Code
ln -s "$(pwd)/skills/computer-control" ~/.claude/skills/computer-control

# OpenCode
ln -s "$(pwd)/skills/computer-control" ~/.config/opencode/skills/computer-control
```

On Windows (Command Prompt as Administrator when required):

```bat
mklink /D "%USERPROFILE%\.codex\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.claude\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.config\opencode\skills\computer-control" "%CD%\skills\computer-control"
```

Using a symbolic link is convenient while iterating on the skill, because changes in this repository are reflected immediately in the agent's skills directory.

If your agent supports custom skill paths, you can also reference this folder directly.

### Use the skill

After installation, invoke it naturally in prompts such as:

- `Use $computer-control to restart the IDEA app and wait until logs stop updating`
- `Use $computer-control to maximize the target window and capture it`
- `Use $computer-control to operate PyCharm with keyboard shortcuts first`

For skill-specific details, see [skills/computer-control/README.md](skills/computer-control/README.md).

## Project Structure

```
ControlMCP/
├── README.md                          # This file
├── README.zh-CN.md                    # Chinese README
├── LICENSE                            # GNU GPLv3 license
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
│       │   ├── coordinate-system.md   # Coordinate system reference
│       │   ├── window-management.md   # Window management reference
│       │   └── idea-run-workflow.md   # JetBrains IDE run/log workflow
│       └── README.md                  # Skill install & usage guide
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

GNU General Public License v3.0 (GPLv3)
