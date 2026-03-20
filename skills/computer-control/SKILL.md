---
name: computer-control
description: |
  通过 ControlMCP 操控电脑：截图、鼠标点击、键盘输入、窗口管理。
  内置常见 IDE/浏览器/办公软件操作 SOP，让 Agent 像熟练用户一样操作电脑。
metadata:
  trigger: 操作电脑 / 控制桌面 / 自动化操作
  tools: control-mcp (MCP server)
  requires: control-mcp MCP server running
---

# Computer Control Skill

你是"电脑操控专家"。通过 ControlMCP 提供的截图、鼠标、键盘、窗口工具来操控电脑。

**核心使命：像一个熟练用户一样操作电脑——优先用快捷键，精确点击，最小化截图。**

---

## 第零章：前置检查

每次操作前，按顺序确认：

1. **目标窗口存在**：`find_windows(title_contains="窗口名")`
2. **窗口已聚焦**：`focus_window(title="窗口名")`
3. **了解屏幕信息**：`get_screen_info()` → 确认坐标空间

---

## 第一章：黄金法则

### 法则 1：键盘优先，鼠标次之

**永远先想有没有快捷键。** 鼠标点击是最后手段。

| 你可能想做的 | ❌ 低效方式 | ✅ 高效方式 |
|-------------|-----------|-----------|
| IDEA 重启应用 | 截图→找绿按钮→点 | `key_press(["ctrl", "f5"])` |
| IDEA 构建项目 | 截图→找锤子图标→点 | `key_press(["ctrl", "f9"])` |
| VS Code 命令面板 | 截图→找菜单→点 | `key_press(["ctrl", "shift", "p"])` |
| 关闭弹窗/对话框 | 截图→找X按钮→点 | `key_press(["escape"])` |
| 选中全部文本 | 鼠标拖拽 | `key_press(["ctrl", "a"])` |
| 浏览器刷新 | 点击地址栏旁刷新 | `key_press(["f5"])` |
| 切换窗口 | 截图找任务栏→点 | `key_press(["alt", "tab"])` |
| 保存文件 | 截图找软盘图标→点 | `key_press(["ctrl", "s"])` |
| 复制粘贴 | 右键菜单 | `key_press(["ctrl", "c"])` / `key_press(["ctrl", "v"])` |

**为什么？**
- 快捷键是确定性操作，100% 精准，不需要截图验证
- 小按钮（IDEA 顶部工具栏图标只有 16-20px）点击容易偏 5-15px
- 快捷键只需 1 次工具调用，鼠标点击需要截图+分析+点击 = 3+ 次调用

**注意**
- IDEA所有操作前需要确定**当前的配置是否为用户所需要操作的配置（下方运行栏的激活子窗口名）**，否则键盘快捷键将操作错误的运行配置

### 法则 2：坐标系必须转换

```
屏幕坐标系 (所有 mouse_click 的参数都是这个):
(0,0)┌──────────────────────────────────────┐
     │  主显示器 1920×1080                   │
     │  ┌────────────────────────────┐      │
     │  │ IDEA窗口                   │      │
     │  │ window_x=286, window_y=22  │      │
     │  │                            │      │
     │  │   窗口内局部坐标 (0,0)      │      │
     │  │   ┌──────┐                │      │
     │  │   │按钮  │ at (50, 30)    │      │
     │  │   └──────┘                │      │
     │  └────────────────────────────┘      │
     └──────────────────────────────────────┘

按钮的屏幕坐标 = (286+50, 22+30) = (336, 52)
```

**转换公式（必须掌握）:**
```
screen_x = window_x + local_x
screen_y = window_y + local_y
```

`capture_window` 返回的 `window_x`, `window_y` 是窗口左上角的屏幕坐标。
截图中的像素坐标是窗口内局部坐标。

### 法则 3：截图有成本，验证要克制

每次截图消耗约 **800-2000 token**（取决于分辨率）。遵循"截一次，做多步，再验证"：

```
❌ 烧 token 模式:
  截图 → 分析 → 点击 → 截图 → 分析 → 点击 → 截图 → 分析  (3张 = 3倍 token)

✅ 节省模式:
  截图 → 分析 → 快捷键操作 3-5 步 → 截图验证  (1-2张)
```

**截图参数选择:**

| 场景 | quality | max_width | 预估大小 | token 消耗 |
|------|---------|-----------|---------|-----------|
| 快速状态检查 | 60 | 640 | ~30KB | 低 |
| 通用操作验证 | 75 | 960 | ~80KB | 中 |
| 需要读小字 | 85 | 1280 | ~200KB | 高 |
| 完整记录 | 100 | null | ~500KB | 很高 |

**推荐默认参数：** `quality=75, max_width=960` — 平衡清晰度与 token 成本。

### 法则 4：操作后必须等待

UI 响应需要时间。不要操作后立即截图。

```
❌ 错误:
  mouse_click(x=500, y=300)
  capture_screen()  # UI 还没响应，截图看到的还是旧状态

✅ 正确:
  mouse_click(x=500, y=300)
  wait(1.0)  # 等待 UI 更新
  capture_screen()
```

典型等待时间：
- 按钮点击 → `wait(0.5)`
- 页面跳转 → `wait(2.0)`
- 应用启动/重启 → `wait(3.0-5.0)`
- 文件保存 → `wait(1.0)`
- 编译/构建 → `wait(5.0-30.0)` 或多次截图轮询

### 法则 5：先验证再操作

不要假设 UI 状态。如果不确定，花 1 次截图确认。

```
❌ 假设按钮位置固定:
  mouse_click(x=1488, y=37)  # 窗口大小变了就点错

✅ 先确认再操作:
  capture_window(title="IDEA", quality=75, max_width=960)
  # [分析截图，确认按钮实际位置]
  mouse_click(x=actual_x, y=actual_y)
```

---

## 第二章：标准操作流程 (SOP)

### SOP A：窗口切换与操作（最常用）

```
步骤1: focus_window(title="目标窗口")
步骤2: 用快捷键执行操作（不需要截图）
步骤3: wait(适当时间)
步骤4: [必要时] capture_window(title="...", quality=75, max_width=960) 验证
```

### SOP B：截图-定位-点击（需要鼠标时）

```
步骤1: capture_window(title="窗口名", quality=75, max_width=960)
步骤2: 分析截图 → 识别目标元素 → 读取局部坐标 (local_x, local_y)
步骤3: 从截图响应获取 window_x, window_y
步骤4: 计算 screen_x = window_x + local_x, screen_y = window_y + local_y
步骤5: mouse_click(x=screen_x, y=screen_y)
步骤6: wait(0.5-2.0)
步骤7: [必要时截图验证]
```

### SOP C：键盘序列操作

```
# 一步完成多步键盘操作，减少工具调用次数
key_sequence(sequence=[
    {"action": "press", "keys": ["ctrl", "shift", "p"], "delay": 0.5},
    {"action": "type", "text": "Format Document"},
    {"action": "press", "keys": ["enter"]},
])
```

### SOP D：复合操作（鼠标+键盘混合）

```
mouse_and_keyboard(actions=[
    {"action": "click", "x": 400, "y": 300, "delay": 0.3},
    {"action": "key_press", "keys": ["ctrl", "a"]},
    {"action": "key_type", "text": "新内容"},
    {"action": "key_press", "keys": ["tab"]},
    {"action": "key_type", "text": "更多内容"},
    {"action": "key_press", "keys": ["enter"], "delay": 1.0},
    {"action": "screenshot", "quality": 75, "max_width": 960}
])
```

### SOP E：像素颜色验证（高精度点击）

```
步骤1: mouse_move(x=approx_x, y=approx_y)
步骤2: color = get_pixel_color(x=approx_x, y=approx_y)
步骤3: 检查颜色是否匹配预期（如绿色按钮 RGB ≈ 76,175,80）
步骤4: 如果不匹配，微调坐标 ±5px 重试
步骤5: 确认后 mouse_click(x=final_x, y=final_y)
```

### SOP F：剪贴板大段文本输入

```
# 比 key_type 一个字符一个字符敲快 100 倍
步骤1: clipboard_set(text="大段文本内容")
步骤2: mouse_click(x=input_x, y=input_y)  # 点击输入框
步骤3: key_press(["ctrl", "v"])  # 粘贴
```

### SOP G：文件/文件夹导航

```
步骤1: key_press(["win", "e"])  # 打开文件管理器
步骤2: wait(1.0)
步骤3: key_press(["ctrl", "l"])  # 聚焦地址栏
步骤4: key_type(text="C:\\目标路径")
步骤5: key_press(["enter"])
步骤6: wait(1.0)
```

---

## 第三章：IDE 操作速查

### IntelliJ IDEA / PyCharm

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 运行/重启 | `Ctrl+F5` | 如果已有运行配置，直接重启 |
| 停止 | `Ctrl+F2` | 停止当前运行 |
| 构建 | `Ctrl+F9` | 增量编译 |
| 保存全部 | `Ctrl+S` | |
| 全局搜索 | `Ctrl+Shift+F` | 在所有文件中搜索 |
| 文件搜索 | `Ctrl+Shift+N` | 按文件名查找 |
| 命令面板 | `Ctrl+Shift+A` | 查找任何操作 |
| 格式化 | `Ctrl+Alt+L` | 代码格式化 |
| 注释 | `Ctrl+/` | 单行注释 |
| 块注释 | `Ctrl+Shift+/` | 多行注释 |
| 查找替换 | `Ctrl+R` | |
| 跳转定义 | `Ctrl+B` | |
| 错误修复 | `Alt+Enter` | 快速修复建议 |
| 运行配置 | `Alt+Shift+F10` | 打开运行配置选择器 |
| Debug | `Shift+F9` | 以调试模式运行 |
| 项目视图 | `Alt+1` | 切换到项目面板 |
| 终端 | `Alt+F12` | 打开终端 |
| 最近文件 | `Ctrl+E` | 最近打开的文件列表 |
| 重构-重命名 | `Shift+F6` | 重命名符号 |
| 提取变量 | `Ctrl+Alt+V` | 提取为变量 |
| 提取方法 | `Ctrl+Alt+M` | 提取为方法 |

### VS Code

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 命令面板 | `Ctrl+Shift+P` | 所有命令 |
| 文件搜索 | `Ctrl+P` | 快速打开文件 |
| 终端 | `` Ctrl+` `` | 集成终端 |
| 运行 | `F5` | 启动调试 |
| 无调试运行 | `Ctrl+F5` | 直接运行 |
| 保存 | `Ctrl+S` | |
| 格式化 | `Shift+Alt+F` | |
| 注释 | `Ctrl+/` | |
| 多光标 | `Ctrl+Alt+↑/↓` | 上下加光标 |
| 行操作 | `Alt+↑/↓` | 上下移动行 |
| 侧边栏 | `Ctrl+B` | 切换侧边栏 |
| 新建终端 | `` Ctrl+Shift+` `` | |
| 关闭编辑器 | `Ctrl+W` | 关闭当前标签 |
| 切换标签 | `Ctrl+Tab` | 切换编辑器标签 |

### Eclipse

| 操作 | 快捷键 |
|------|--------|
| 运行 | `Ctrl+F11` |
| 调试 | `F11` |
| 保存 | `Ctrl+S` |
| 格式化 | `Ctrl+Shift+F` |
| 注释 | `Ctrl+/` |
| 查找 | `Ctrl+H` |
| 重构 | `Alt+Shift+T` |

---

## 第四章：浏览器操作速查

| 操作 | 快捷键 |
|------|--------|
| 刷新 | `F5` |
| 强制刷新(跳缓存) | `Ctrl+F5` |
| 新建标签页 | `Ctrl+T` |
| 关闭标签页 | `Ctrl+W` |
| 恢复关闭的标签 | `Ctrl+Shift+T` |
| 地址栏 | `Ctrl+L` 或 `F6` |
| 开发者工具 | `F12` |
| 查找页面 | `Ctrl+F` |
| 放大 | `Ctrl+=` |
| 缩小 | `Ctrl+-` |
| 重置缩放 | `Ctrl+0` |
| 下一个标签 | `Ctrl+Tab` |
| 上一个标签 | `Ctrl+Shift+Tab` |
| 打开下载 | `Ctrl+J` |
| 打开历史 | `Ctrl+H` |
| 打开书签 | `Ctrl+Shift+O` |
| 全屏 | `F11` |
| 页面顶部 | `Home` |
| 页面底部 | `End` |
| 向下翻页 | `Page Down` 或 `Space` |

---

## 第五章：系统操作速查

### Windows

| 操作 | 快捷键/命令 |
|------|------------|
| 打开文件管理器 | `win+e` |
| 锁屏 | `win+l` |
| 显示桌面 | `win+d` |
| 任务管理器 | `ctrl+shift+esc` |
| 截图(系统) | `win+shift+s` |
| 运行对话框 | `win+r` |
| 设置 | `win+i` |
| 虚拟桌面新建 | `win+ctrl+d` |
| 切换虚拟桌面 | `win+ctrl+←/→` |
| Alt+Tab 切换 | `alt+tab` |

### macOS

| 操作 | 快捷键 |
|------|--------|
| Finder | `Cmd+Space` → "Finder" |
| Spotlight | `Cmd+Space` |
| 强制退出 | `Cmd+Option+Esc` |
| 截图 | `Cmd+Shift+4` |
| 切换应用 | `Cmd+Tab` |
| 隐藏当前窗口 | `Cmd+H` |
| 最小化 | `Cmd+M` |
| 新建Finder窗口 | `Cmd+N` |

---

## 第六章：常见陷阱与解决方案

### 陷阱 1：坐标系混淆

```python
# ❌ 把截图中的局部坐标当屏幕坐标
capture_window(title="IDEA")  # 返回 window_x=286, window_y=22
mouse_click(x=50, y=30)  # 点到了屏幕左上角，不是 IDEA 中的按钮！

# ✅ 正确转换
mouse_click(x=286+50, y=22+30)  # = (336, 52)
```

### 陷阱 2：忽略 DPI 缩放

高 DPI 屏幕（如 150% 缩放）下，截图尺寸和物理像素不一致。

```
# 如果 get_screen_info 返回 width=2560, height=1440
# 但 Windows 设置了 150% 缩放
# 实际逻辑像素 = 2560/1.5 ≈ 1707, 1440/1.5 = 960
# capture_window 的 window_x/y 使用逻辑像素
```

**解决方案：** 先 `get_screen_info()` 了解实际坐标空间。

### 陷阱 3：窗口遮挡

目标窗口可能被其他窗口部分遮挡。

```python
# ✅ 总是先 focus 再操作
focus_window(title="目标窗口")
wait(0.3)  # 等窗口动画
# 然后再截图或点击
```

### 陷阱 4：key_sequence 不支持 wait action（旧版本 bug）

```json
// ❌ 旧版本报 "unknown action"
{"action": "wait", "seconds": 0.3}

// ✅ 方式1：用 delay 字段（所有版本）
{"action": "press", "keys": ["esc"], "delay": 0.3}

// ✅ 方式2：新版本支持 wait action
{"action": "wait", "seconds": 0.3}
```

### 陷阱 5：弹窗/对话框阻断

操作触发了弹窗，后续操作全失效。

```python
# 如果操作后可能出现弹窗
mouse_click(x=500, y=300)
wait(1.0)
capture_screen(quality=75, max_width=960)
# [分析是否有弹窗]
# 如果有弹窗，先处理弹窗（通常是按 escape 或点击确认）
```

### 陷阱 6：输入法干扰

中文输入法开启时，key_type 会输入拼音而非英文。

```python
# ✅ 输入英文/快捷键前，先切换到英文输入
key_press(["shift"])  # 切换中英文（部分输入法）
# 或者
key_press(["ctrl", "space"])  # 微软拼音切换中英文
```

### 陷阱 7：双屏坐标偏移

第二显示器的坐标不是从 (0,0) 开始。

```python
# get_screen_info 会返回所有显示器信息
# 显示器1: {x: 0, y: 0, width: 1920, height: 1080}
# 显示器2: {x: 1920, y: 0, width: 2560, height: 1440}
# 点击显示器2中的元素时，x 要加上显示器2的 x 偏移
mouse_click(x=1920+500, y=300)  # 显示器2上 (500, 300) 的屏幕坐标
```

---

## 第七章：Token 优化策略

### 策略 1：JPEG 压缩

默认 `quality=80` 已经是 JPEG。需要更小时用 `quality=60-70`。

### 策略 2：缩小分辨率

`max_width=960` 将 1920px 宽的截图缩小一半，token 减半。

### 策略 3：截取窗口而非全屏

`capture_window` 只截目标窗口，比 `capture_screen`（全屏）文件更小。

### 策略 4：批量操作

```
# ❌ 3 次工具调用
key_press(["ctrl", "a"])
key_press(["ctrl", "c"])
key_press(["ctrl", "v"])

# ✅ 1 次工具调用
key_sequence(sequence=[
    {"action": "press", "keys": ["ctrl", "a"], "delay": 0.1},
    {"action": "press", "keys": ["ctrl", "c"], "delay": 0.1},
    {"action": "press", "keys": ["ctrl", "v"]},
])
```

### 策略 5：用 wait 替代截图轮询

```
# ❌ 反复截图检查进度
while not_done: capture_screen()

# ✅ 等待合理时间
wait(5.0)
capture_screen(quality=75, max_width=960)  # 验证一次
```

### 策略 6：剪贴板替代逐字输入

```
# ❌ 慢且 token 多
key_type(text="这是一段很长的文本...")

# ✅ 快且精准
clipboard_set(text="这是一段很长的文本...")
key_press(["ctrl", "v"])
```

---

## 第八章：安全与边界

### 不要做

- 不要在生产环境执行破坏性操作（删除文件、格式化等）前跳过确认
- 不要在密码输入框中 key_type 敏感密码（用 clipboard_set + paste，然后清空剪贴板）
- 不要对不确定的坐标盲目点击（特别是关闭按钮、删除按钮）
- 不要在没有焦点确认的情况下操作（可能误操作到其他窗口）

### 要做

- 操作前 `focus_window` 确认窗口
- 点击危险按钮前截图确认位置
- 批量操作后截图验证
- 保留操作日志（哪些步骤成功/失败）

---

## 附录：快速决策树

```
用户请求操作电脑
  │
  ├─ 操作某个 IDE？
  │   └─ YES → 查第三章速查表 → 用快捷键 → 结束
  │
  ├─ 操作浏览器？
  │   └─ YES → 查第四章速查表 → 用快捷键 → 结束
  │
  ├─ 操作系统级？
  │   └─ YES → 查第五章速查表 → 用快捷键 → 结束
  │
  ├─ 没有快捷键？
  │   └─ 需要点击 UI 元素
  │       ├─ 已知坐标？ → mouse_click → 结束
  │       └─ 未知坐标？ → SOP B (截图→定位→转换→点击)
  │
  └─ 复杂多步操作？
      └─ 拆解为上面的原子操作组合
```
