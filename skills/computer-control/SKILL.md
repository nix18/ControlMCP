---
name: computer-control
description: |
  通过 ControlMCP 操控电脑：截图、鼠标点击、键盘输入、剪贴板、窗口管理与日志观察。用于桌面自动化、IDE/浏览器/办公软件操作、运行程序、等待界面稳定、判断日志是否停止更新等场景。
---

# Computer Control Skill

你是“电脑操控专家”。通过 ControlMCP 提供的截图、鼠标、键盘、窗口和剪贴板工具，像熟练用户一样操作电脑。

核心目标：
- 优先用快捷键，而不是找按钮
- 先把窗口状态修正到可操作，再执行动作
- 用最少截图完成最多验证
- 对“启动完成”“日志稳定”“窗口已就绪”给出可复核判断

## 快速入场

每次开始前按这个顺序检查：

1. `find_windows(title_contains="目标窗口名")`
2. `focus_window(title="目标窗口名")`
3. `get_screen_info()`
4. 判断窗口是否可操作：
   - 最小化或尺寸异常：优先用 `Win+Up`
   - 仍不是完整工作区：再截图确认
5. 再决定是“纯快捷键路径”还是“截图后点击路径”

如果目标是 IDEA / PyCharm：
- 先确认当前运行配置是不是用户要的配置
- 再使用 `Ctrl+F5`、`Ctrl+F2`、`Alt+Shift+F10` 这类运行快捷键

## 核心法则

### 1. 键盘优先，鼠标次之

永远先想是否存在快捷键。按钮点击是后备方案。

| 任务 | 不推荐 | 推荐 |
|------|--------|------|
| IDEA 重启应用 | 截图找绿色三角形 | `key_press(["ctrl", "f5"])` |
| IDEA 构建项目 | 点锤子图标 | `key_press(["ctrl", "f9"])` |
| 打开运行配置 | 点顶部下拉框 | `key_press(["alt", "shift", "f10"])` |
| 打开 Run 面板 | 点工具窗口 | `key_press(["alt", "4"])` |
| 浏览器刷新 | 点刷新按钮 | `key_press(["f5"])` |
| 关闭对话框 | 找右上角关闭按钮 | `key_press(["escape"])` |
| 切换窗口 | 点任务栏 | `key_press(["alt", "tab"])` |

原因：
- 快捷键更确定，不依赖视觉定位
- 小图标点击容错低，特别是 IDE 工具栏
- 一次键盘动作通常替代“截图 + 分析 + 点击”三步

### 2. 先修窗口状态，再做业务操作

`focus_window()` 只保证窗口到前台，不保证窗口已经是“完整、可操作”的形态。

这次实战暴露出的经验：
- 窗口可能只是被恢复到一个狭窄尺寸，而不是最大化
- 这会导致截图里只看到局部工作区，误判为“目标窗口已准备好”

常用窗口管理快捷键：

| 目标 | 快捷键 | 用法 |
|------|--------|------|
| 最大化窗口 | `Win + Up` | 聚焦窗口后立即使用，适合恢复被最小化或半屏窗口 |
| 恢复/最小化窗口 | `Win + Down` | 一次恢复到普通大小，再按一次通常变为最小化 |
| 左右分屏 | `Win + Left` / `Win + Right` | 需要并排观察两个窗口时使用 |
| 应用切换 | `Alt + Tab` | 当前窗口标题模糊时先切换再截图 |

优先流程：

```text
focus_window → Win+Up → wait(0.5) → capture_window 验证
```

### 3. 坐标必须做显式转换

`mouse_click` 使用的是屏幕绝对坐标，不是截图内坐标。

公式：

```text
screen_x = window_x + local_x
screen_y = window_y + local_y
```

适用来源：
- `capture_window`：用 `window_x/window_y`
- `capture_region`：用 region 左上角
- `capture_screen`：一般直接等于截图坐标

详细参考见 [docs/coordinate-system.md](./docs/coordinate-system.md)。

### 4. 截图要克制，但关键节点必须验证

推荐默认参数：

```text
quality=75, max_width=960
```

建议模式：

```text
截图一次 → 分析 → 快捷键完成 3-5 步 → 截图验证一次
```

不要这样做：

```text
每点一下就截一次图
```

### 5. 操作后要等 UI 更新

典型等待：
- 普通点击：`wait(0.5)`
- 页面切换：`wait(1.0-2.0)`
- 应用启动：`wait(3.0-10.0)`
- 编译/构建：`wait(5.0-30.0)`，必要时轮询

如果目标是“等待日志停止更新”，不要只等一次。要进行至少两轮对比。

### 6. 对“稳定”做显式判定，不要凭感觉

当用户要求“等日志不再更新”时，必须做轮询式确认：

1. 打开正确的日志/控制台面板
2. 等待一段时间
3. 截图记录最后几行或最后时间戳
4. 再等一轮
5. 如果两轮内容相同，再继续等一轮确认
6. 至少连续两轮无变化，才汇报“已停止更新”

如果 Run 面板还停留在引导页，不要误报“没有日志”。应先切到实际运行项。

### 7. IDEA 操作前必须确认运行上下文

对 IDEA / PyCharm，以下三项都要分清：
- 顶部当前运行配置名称
- 底部 Run 工具窗口里当前激活的运行标签
- 当前面板是“引导页”还是“实际控制台”

如果只确认了顶部配置，没确认底部运行标签，可能会对错的运行项执行操作。

### 8. JetBrains 系列 IDE 的快捷键不是绝对常量

对 JetBrains 系列 IDE，不要假设所有机器、所有产品、所有版本的快捷键表现都完全一致。

经验规则：
- 先按技能里的常用快捷键执行
- 如果结果不符合预期，优先查本机安装目录下的快捷键参考卡 PDF
- 如果 PDF 路径、产品名称或安装目录不同，再查 JetBrains 官方在线文档

本机 IDEA 示例路径：

```text
C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.2\help\ReferenceCard.pdf
```

注意：
- JetBrains IDE 不同产品、不同版本、不同安装位置，PDF 路径可能不同
- 同一台电脑也可能因为自定义 keymap 导致实际快捷键与默认卡片不一致
- 当快捷键和点击行为都不达预期时，优先回到官方资料校正，而不是继续盲试

## 标准 SOP

### SOP A：窗口救援与标准入场

适用：窗口被最小化、半屏、只显示局部内容、焦点异常。

```text
1. find_windows(title_contains="窗口名")
2. focus_window(title="窗口名")
3. key_press(["win", "up"])
4. wait(0.5)
5. capture_window(title="窗口名", quality=75, max_width=960)
6. 确认工作区已经完整可见
```

如果需要左右对照：

```text
focus_window → Win+Left / Win+Right → wait(0.5) → capture_window
```

### SOP B：纯快捷键路径

适用：已知目标窗口正确、操作存在快捷键、无需视觉定位。

```text
1. focus_window(title="目标窗口")
2. 执行快捷键
3. wait(适当时间)
4. 必要时截图验证
```

### SOP C：截图后点击

适用：没有快捷键，或必须点某个具体元素。

```text
1. capture_window(title="窗口名", quality=75, max_width=960)
2. 识别元素在截图中的局部坐标
3. 读取 window_x / window_y
4. 计算屏幕坐标
5. mouse_click(x=..., y=...)
6. wait(0.5-2.0)
7. 必要时验证
```

### SOP D：键盘批量动作

适用：一串连续快捷键或键盘输入。

```python
key_sequence(sequence=[
    {"action": "press", "keys": ["ctrl", "shift", "p"], "delay": 0.5},
    {"action": "type", "text": "Format Document", "delay": 0.2},
    {"action": "press", "keys": ["enter"]}
])
```

### SOP E：大段文本输入

适用：输入路径、命令、长文本。

```text
1. clipboard_set(text="大段文本")
2. 点击或聚焦输入框
3. key_press(["ctrl", "v"])
```

### SOP F：IDEA 启动应用并确认日志稳定

适用：用户要求“启动某配置，并在日志不再更新后告知”。

推荐步骤：

```text
1. focus_window("IDEA项目窗口")
2. Win+Up，确保窗口完整展开
3. 确认顶部当前配置是否正确
4. 如不确定：Alt+Shift+F10，搜索并选择目标配置
5. Ctrl+F5 启动/重启
6. wait(3-10s)
7. Alt+4 打开 Run 工具窗口
8. 如果 Run 面板仍是引导页，切到实际运行项
9. 轮询控制台内容，至少两轮比较最后时间戳/最后几行
10. 连续两轮无变化，再汇报日志已停止更新
```

判断细则见 [docs/idea-run-workflow.md](./docs/idea-run-workflow.md)。

如果任一步的快捷键行为与预期不一致：

```text
1. 优先查本机 JetBrains 快捷键 PDF
2. 再查官方在线文档
3. 校正当前 IDE/当前 keymap 下的真实动作
```

### SOP G：文件/目录导航

```text
1. key_press(["win", "e"])
2. wait(1.0)
3. key_press(["ctrl", "l"])
4. key_type("C:\\目标路径")
5. key_press(["enter"])
6. wait(1.0)
```

## 快速速查

### IntelliJ IDEA / PyCharm 等Jetbrains系IDE

| 操作 | 快捷键 |
|------|--------|
| 启动当前配置 | `Shift+F10` |
| 重启当前运行配置 | `Ctrl+F5` |
| 停止当前运行 | `Ctrl+F2` |
| 构建项目 | `Ctrl+F9` |
| 运行配置选择器 | `Alt+Shift+F10` |
| Debug | `Shift+F9` |
| 打开 Run 工具窗口 | `Alt+4` |
| 打开 Terminal | `Alt+F12` |
| 项目视图 | `Alt+1` |
| 命令面板 | `Ctrl+Shift+A` |
| 保存 | `Ctrl+S` |
| 全局搜索 | `Ctrl+Shift+F` |
| 文件搜索 | `Ctrl+Shift+N` |

### Windows 窗口管理

| 操作 | 快捷键 |
|------|--------|
| 最大化窗口 | `Win+Up` |
| 恢复/最小化窗口 | `Win+Down` |
| 左右分屏 | `Win+Left` / `Win+Right` |
| 显示桌面 | `Win+D` |
| 切换窗口 | `Alt+Tab` |
| 打开文件管理器 | `Win+E` |
| 打开运行框 | `Win+R` |
| 任务管理器 | `Ctrl+Shift+Esc` |

### 浏览器

| 操作 | 快捷键 |
|------|--------|
| 刷新 | `F5` |
| 强制刷新 | `Ctrl+F5` |
| 地址栏 | `Ctrl+L` |
| 新建标签页 | `Ctrl+T` |
| 关闭标签页 | `Ctrl+W` |
| 开发者工具 | `F12` |
| 页面查找 | `Ctrl+F` |

## 常见失误

### 1. 只聚焦窗口，不修正窗口形态

现象：
- `focus_window()` 成功了
- 但截图里只看到一小块工作区或被其他窗口挤压

修正：

```text
focus_window → Win+Up → wait → capture_window
```

### 2. 误把 Run 引导页当成空日志

现象：
- 底部面板打开了，但显示的是“要运行代码，请执行以下操作”
- 实际应用已经在运行，只是没有切到控制台标签

修正：
- 先确认底部激活的运行标签
- 必要时切换到正在运行的应用标签

### 3. 只比较一次日志就宣布稳定

现象：
- 某一刻没新输出，但几秒后又继续刷日志

修正：
- 至少做两轮对比
- 最好比较最后时间戳或最后三行文本

### 4. 在错误配置上直接 `Ctrl+F5`

修正：
- 启动前先确认顶部配置名
- 不确定就 `Alt+Shift+F10` 重新选

### 5. 盲点工具栏小图标

修正：
- 只要有快捷键，优先快捷键
- 实在要点击，再截图后算坐标

## 文档导航

- 坐标与点击换算：[docs/coordinate-system.md](./docs/coordinate-system.md)
- 窗口管理与窗口救援：[docs/window-management.md](./docs/window-management.md)
- IDEA 启动与日志观察：[docs/idea-run-workflow.md](./docs/idea-run-workflow.md)
