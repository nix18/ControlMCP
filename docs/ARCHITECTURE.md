# Architecture Design

## 1. System Overview

The ControlMCP server now uses a control-plane-first architecture.
It still exposes low-level atomic tools, but high-precision desktop automation is expected to flow through instruction preprocessing, guarded execution, verification, recovery, and workflow memory.

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
│  │ MCP Protocol│  │        App Registry             │  │
│  │  (server.py)│──│  atomic + control-plane tools   │  │
│  └─────────────┘  └──────────────┬───────────────────┘  │
│                                  │                      │
│  ┌───────────────────────────────▼───────────────────┐  │
│  │                Control Plane                      │  │
│  │ planner -> executor -> verifier -> recovery      │  │
│  │                -> guards -> memory               │  │
│  └───────────────┬──────────────────────────────────┘  │
│                  │                                      │
│  ┌───────────────▼──────────────────────────────────┐  │
│  │               Atomic Tool Modules                │  │
│  │  screen / window / mouse / keyboard / combined   │  │
│  └───────────────┬──────────────────────────────────┘  │
│                  │                                      │
│  ┌───────────────▼──────────────────────────────────┐  │
│  │               Utility Layer                      │  │
│  │      capture.py + platform window backends       │  │
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

## 2. Component Responsibilities

### 2.1 MCP Protocol Layer (`server.py`)

- Creates the MCP `Server` instance
- Loads all tool definitions from the app registry
- Dispatches `call_tool` requests through a shared dispatcher
- Wraps results as `TextContent` responses

### 2.2 App Layer (`app/`)

- Owns the central tool registry and dispatcher
- Keeps `server.py` thin
- Applies guard checks before risky atomic tools run

### 2.3 Control Plane (`control_plane/`)

- `planner`: normalize vague desktop instructions into a typed plan
- `executor`: run plan steps against atomic tools
- `verifier`: confirm that important UI state really changed
- `recovery`: rebuild context after shortcut misuse or UI drift
- `guards`: require explicit confirmation for sensitive actions
- `memory`: save reusable workflow experience

### 2.4 Tool Modules (`tools/`)

Each tool module contains pure functions that:
- Accept typed parameters
- Call utility functions for the actual work
- Return JSON-serialized structured responses
- Are independent of MCP protocol details

### 2.5 Utility Layer (`utils/`)

| Module | Description |
|---|------|
| **`capture.py`** | Platform-agnostic screen/window capture using `mss` + `Pillow` |
| **`_win_window.py`** | Windows-specific window operations via `pygetwindow` |
| **`_mac_window.py`** | macOS-specific window operations via Quartz |
| **`_linux_window.py`** | Linux-specific window operations via `xlib` |

### 2.6 Schema / Domain Layer (`schemas/`, `domain/`)

- Dataclasses for all structured response types
- Typed models for plans, execution runs, confirmation tickets, and workflow experience
- JSON serialization via `to_json()` / `to_dict()` methods
- Filename generation for screenshots

---

## 3. Data Flow

### Screenshot Flow

```
LLM → capture_screen(save_dir="/tmp") → tool_capture_screen()
  → capture_full_screen() → mss.grab() → PIL.save()
  → ScreenshotResult(file_path=..., timestamp=..., width=..., height=...)
  → JSON string → TextContent → MCP Response → LLM
```

### Mouse Click Flow

```
LLM → mouse_click(x=500, y=300, button="left") → tool_mouse_click()
  → pyautogui.moveTo(500, 300) → pyautogui.click()
  → ClickResult(success=True, x=500, y=300, ...)
  → JSON string → TextContent → MCP Response → LLM
```

### Combined Action Flow

```

### Control-Plane Flow

```
LLM → plan_desktop_task(instruction=...) → planner
  → DesktopTaskPlan(steps=[...], needs_confirmation=...)
  → execute_desktop_plan(plan_id=...)
  → guards check sensitive steps
  → executor dispatches atomic tools
  → verifier checks outcome / recovery runs if needed
  → run status / confirmation / workflow memory result
```
LLM → mouse_and_keyboard(actions=[...]) → tool_mouse_and_keyboard()
  → for each action: dispatch to pyautogui operation
  → CompositeActionResult(success=..., steps_completed=..., results=[...])
  → JSON string → TextContent → MCP Response → LLM
```

---

## 4. Technology Choices

| Component | Technology | Rationale |
|---|---|---|
| MCP SDK | `mcp` | Official Python MCP SDK |
| Screen Capture | `mss` + `Pillow` | Fast cross-platform capture, image processing |
| Window Management (Win) | `pygetwindow` | Simple, well-maintained |
| Window Management (Mac) | `Quartz` (pyobjc) | Native macOS API |
| Window Management (Linux) | `python-xlib` | Standard X11 interface |
| Mouse/Keyboard | `pyautogui` | Cross-platform, widely used, reliable |
| Clipboard | `pyperclip` | Simple cross-platform clipboard |
| Packaging | `hatchling` | Modern Python build backend |

---

## 5. Error Handling Strategy

- All tool functions catch exceptions and return structured error responses
- No exceptions propagate to the MCP protocol layer
- Every response includes a `success` field
- Detailed error messages in the `message` field
- Best-effort cleanup (e.g., releasing held keys on error)

---

## 6. Cross-Platform Strategy

- Common interface in `capture.py` for screen operations
- Platform detection at runtime via `platform.system()`
- Dynamic import of platform-specific backend
- Graceful degradation (e.g., clipboard without pyperclip)
