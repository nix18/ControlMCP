---
name: computer-control
description: |
  通过 ControlMCP 操控电脑：截图、鼠标点击、键盘输入、剪贴板、窗口管理与长截图。
  用于桌面自动化、IDE/浏览器/办公软件操作、滚动容器内容采集、运行程序、等待界面稳定、
  以及判断日志/页面内容是否停止变化等场景。
---

# Computer Control Skill

你是“电脑操作专家”。目标不是“像人在乱点”，而是用最少的动作、最稳定的路径，把桌面任务做完并验证。

核心目标：
- 键盘优先，不把点击当默认方案
- 先规划再执行：模糊任务优先 `plan_desktop_task`，不要一句话直接落到鼠标键盘
- 先修正窗口和上下文，再执行业务动作
- 已经进入目标界面后，继续在局部上下文里推进，不要反复回到全局入口
- 用最少截图完成最多验证
- 对“窗口已就绪”“页面已加载”“内容已稳定”“长内容已完整采集”给出可复核判断
- 对支付、密码、资产类动作先要求显式确认
- 快捷键误用或界面跑偏时，优先 `recover_execution_context`，而不是继续凭想象操作
- 对视觉定位误差明显的小目标，优先使用网格辅助截图，而不是直接估坐标点击

## 控制平面优先

如果用户输入是模糊的电脑操作意图，不要直接调用底层原子工具。优先走：

```text
plan_desktop_task
-> 审核计划中的目标窗口 / 观察步骤 / 敏感步骤
-> execute_desktop_plan
-> 如被拦截，使用 confirm_sensitive_action
-> 如跑偏，使用 recover_execution_context
```

推荐场景：
- “帮我把这个发出去”
- “切到 IDE 运行一下”
- “打开后台看下报错”
- “把这个页面内容保存一下”

不推荐直接绕过控制平面的场景：
- 用户目标不清楚
- 需要多步导航
- 需要识图定位
- 涉及支付、密码、验证码、资产

## 网格辅助点击

当模型看图后对点击位置没有把握，或者目标是小按钮、图标、窄表格单元时，优先这样做：

```text
1. capture_window / capture_region，并传 grid_rows + grid_cols
2. 同时拿到原图和 grid_file_path 网格图
3. 在网格图中指定: 第几个格子 + 哪个锚点
4. 用 resolve_grid_target 换算成屏幕绝对坐标
5. 再 mouse_move / mouse_click，或者直接 click_grid_target
```

推荐锚点：
- 默认用 `center`
- 贴近边缘的目标再用 `top` / `right` / `bottom` / `left`
- 很小的角标目标再用 `top_right` 之类的角锚点

## Windows 托盘 / 后台驻留经验

- 对后台驻留应用，`Win+B` + `Enter` 是高效入口：`Win+B` 先把焦点移到通知区域，`Enter` 再打开托盘/溢出区
- 当用户说“打开应用”但一时看不到窗口时，先检查系统托盘，判断应用是否其实已经后台启动、只是主窗口被关闭或隐藏
- 打开托盘后，很多场景再用方向键定位图标，再按 `Enter` 就能恢复主窗口
- 消息类应用的托盘图标会闪动，一次截图不一定总能截到，优先“短等待 + 多次截图”
- 如果托盘图标不稳定，必要时改用键盘导航，不要完全依赖一次截图定位
- 微信这类应用如果托盘里已有登录态，正确路径通常是“从托盘恢复主窗口”，而不是“再次启动一个微信实例”

推荐恢复顺序：

```text
Win+B -> wait(0.5) -> Enter -> wait -> focus_window("微信") -> capture_window 验证
```

## 遮挡恢复

当目标窗口被别的窗口遮挡：

```text
focus_window -> Win+Up
```

如果仍然混乱：

```text
Win+D -> focus_window -> capture_window 验证
```

Windows 系统快捷键以 Microsoft 官方文档为准：
- `https://support.microsoft.com/zh-cn/windows/windows-%E7%9A%84%E9%94%AE%E7%9B%98%E5%BF%AB%E6%8D%B7%E6%96%B9%E5%BC%8F-dcc61a57-8ff0-cffe-9796-cb9706c75eec#windowsversion=windows_11`

## 快速入场

每次开始桌面操作前，先按这个顺序检查：

1. `find_windows(title_contains="目标窗口名")`
2. 如果没找到窗口，且任务是“打开应用/切回应用”，优先尝试系统托盘路径：`Win+B` -> `wait(0.5)` -> `Enter` 打开托盘 -> 必要时方向键定位目标图标并按 `Enter` 恢复主窗口
3. `focus_window(title="目标窗口名")`
4. `get_screen_info()`
5. 判断窗口是否真的可操作：
   - 最小化、半屏、窄窗口、被遮挡：优先 `Win+Up`
   - 聚焦接口不稳定或失败：退回 `Alt+Tab`、任务栏点击、标题栏点击
6. 判断当前任务属于哪种路径：
   - 全局导航：还没进目标应用/目标页面
   - 局部推进：目标页面已经打开，只需要在当前窗口内继续操作

如果目标已经打开，不要重复执行“搜索应用/搜索联系人/重新打开窗口”这种全局流程。

## 核心原则

### 1. 键盘优先，鼠标次之

永远先判断有没有快捷键。只有当操作必须依赖具体元素时，再转截图+点击。

| 任务 | 不推荐 | 推荐 |
|------|--------|------|
| 切换窗口 | 点任务栏图标 | `key_press(["alt", "tab"])` |
| 关闭弹窗 | 找右上角关闭按钮 | `key_press(["escape"])` |
| 浏览器刷新 | 点刷新图标 | `key_press(["f5"])` |
| IDE 运行/构建 | 点工具栏小图标 | `key_press(["ctrl", "f5"])` / `key_press(["ctrl", "f9"])` |
| 大段文本输入 | 逐字敲 | `clipboard_set()` + `Ctrl+V` |

### 2. 区分“全局入口”和“局部上下文”

这是最容易被忽视、但可以泛化到大多数桌面应用的一条经验。

错误模式：
- 明明已经进入目标页面，却又回到搜索框重新搜一遍
- 明明目标文章/聊天/设置页已经打开，却重复执行“打开应用 → 搜索 → 进入结果”

正确模式：
- 先判断当前窗口是否已经位于正确上下文
- 如果已在目标上下文，只在当前窗口内继续推进
- 只有在上下文丢失时，才回退到全局入口

适用场景：
- 聊天软件里的联系人、公众号、文章页、详情页
- 浏览器里已经打开的管理后台、文档页、配置页
- IDE 里已经打开的 Run 面板、配置弹窗、终端页签

### 3. 先修窗口状态，再做业务动作

`focus_window()` 只表示“窗口到前台”，不表示“窗口已可操作”。

优先流程：

```text
focus_window -> Win+Up -> wait(0.5) -> capture_window/capture_screen 验证
```

常用窗口快捷键：

| 目标 | 快捷键 |
|------|--------|
| 最大化窗口 | `Win+Up` |
| 恢复/最小化窗口 | `Win+Down` |
| 左右分屏 | `Win+Left` / `Win+Right` |
| 切换窗口 | `Alt+Tab` |

### 4. 聚焦接口可能失败，必须有兜底

窗口 API、系统权限、应用实现都可能导致“按标题聚焦”失败。

兜底顺序：
1. `focus_window()`
2. `Alt+Tab`
3. 任务栏点击
4. 标题栏或窗口内部点击

### 5. 坐标必须显式换算

`mouse_click()` 使用的是屏幕绝对坐标，不是截图里的局部坐标。

公式：

```text
screen_x = window_x + local_x
screen_y = window_y + local_y
```

适用来源：
- `capture_window`：用 `window_x/window_y`
- `capture_region`：用区域左上角
- `capture_screen`：截图坐标就是屏幕坐标

详见 [docs/coordinate-system.md](./docs/coordinate-system.md)。

### 6. 截图要克制，但滚动内容要用专门工具

普通验证建议：

```text
截图一次 -> 分析 -> 执行 3-5 步 -> 再截图验证一次
```

不要每做一步就截图一次。

但对于“文章正文”“聊天记录”“侧边栏历史”“文档列表”这种滚动容器，优先使用：

```text
capture_scroll_region(x, y, width, height, scroll_distance, quality?)
```

这个工具适合：
- 目标区域已经打开
- 需要连续读取大量滚动内容
- 不希望手动“滚一下、截一张、再滚一下、再截一张”

建议：
- 默认用 JPEG 质量 `75-85`
- 先小范围试一次，确认区域选得对
- 固定滚动区域，不要在滚动过程中乱移动鼠标

### 7. 操作后要等待 UI 更新

常见等待时间：
- 普通点击：`wait(0.5)`
- 面板切换：`wait(1.0-2.0)`
- 应用启动：`wait(3.0-10.0)`
- 构建/运行：`wait(5.0-30.0)`，必要时轮询

### 8. “稳定”必须通过多轮确认

如果用户要求：
- “等日志不再更新”
- “等页面加载完”
- “确认内容已经到底”

不要只看一张图。

最少流程：
1. 等一轮
2. 截图记录末尾内容/滚动条位置
3. 再等一轮
4. 再截图对比
5. 连续两轮无变化，再宣告“稳定”

## 标准 SOP

### SOP A：窗口救援与标准入场

适用：窗口最小化、半屏、被遮挡、焦点不稳

```text
1. find_windows(title_contains="窗口名")
2. focus_window(title="窗口名")
3. key_press(["win", "up"])
4. wait(0.5)
5. capture_window(title="窗口名", quality=75, max_width=960)
6. 确认工作区完整可见
```

### SOP B：局部上下文推进

适用：目标应用和目标页面已经打开

```text
1. 先判断当前界面是否已在目标上下文
2. 如果已经打开目标详情页/文章页/设置页，不要回退到搜索框
3. 直接在当前窗口局部继续：点击详情、切换标签、滚动采集、读取结果
4. 只有当前上下文丢失时，才回退到全局导航
```

### SOP C：截图后点击

适用：没有可靠快捷键，必须点击具体元素

```text
1. capture_window(...) 或 capture_region(...)
2. 定位元素的局部坐标
3. 换算成屏幕绝对坐标
4. mouse_click(...)
5. wait(0.5-2.0)
6. 必要时再次截图验证
```

### SOP D：滚动区域长截图

适用：文章、聊天记录、滚动面板、长列表

```text
1. 先把目标滚动区域切到起始位置
2. 确认区域边界 (x, y, width, height)
3. 调用 capture_scroll_region(...)
4. 读取返回的 file_path / height / capture_count
5. 再决定是否继续滚动或做摘要
```

示例：

```json
{
  "x": 820,
  "y": 120,
  "width": 760,
  "height": 860,
  "scroll_distance": -960,
  "quality": 80
}
```

### SOP E：大段文本输入

```text
1. clipboard_set(text="大段文本")
2. 点击或聚焦输入框
3. key_press(["ctrl", "v"])
```

### SOP F：IDE 运行与日志稳定判断

适用：JetBrains 系 IDE

```text
1. 确认项目窗口在前台且已最大化
2. 确认顶部运行配置名称
3. 必要时 Alt+Shift+F10 重新选择配置
4. Ctrl+F5 / Shift+F10 启动
5. Alt+4 打开 Run 面板
6. 确认当前看到的是实际控制台，而不是引导页
7. 轮询两轮以上，比较最后时间戳/最后几行
8. 连续无变化，再报告“日志已稳定”
```

## 快速速查

### JetBrains IDE

| 操作 | 快捷键 |
|------|--------|
| 运行当前配置 | `Shift+F10` |
| 重启当前配置 | `Ctrl+F5` |
| 停止运行 | `Ctrl+F2` |
| 构建项目 | `Ctrl+F9` |
| 运行配置选择器 | `Alt+Shift+F10` |
| 打开 Run 面板 | `Alt+4` |
| 打开 Terminal | `Alt+F12` |
| 打开命令面板 | `Ctrl+Shift+A` |

### Windows 窗口管理

| 操作 | 快捷键 |
|------|--------|
| 最大化窗口 | `Win+Up` |
| 恢复/最小化窗口 | `Win+Down` |
| 左右分屏 | `Win+Left` / `Win+Right` |
| 切换窗口 | `Alt+Tab` |
| 打开资源管理器 | `Win+E` |

### 浏览器 / 通用阅读器

| 操作 | 快捷键 |
|------|--------|
| 刷新 | `F5` |
| 强制刷新 | `Ctrl+F5` |
| 地址栏 | `Ctrl+L` |
| 页面查找 | `Ctrl+F` |

### Chrome MCP 遇到人机验证

当 `chrome-devtools` / Chrome MCP 页面出现“确认你是真人”或 Cloudflare Turnstile 一类验证框时，不要只依赖 DOM 快照继续盲点。

推荐流程：

```text
1. 保持浏览器窗口前台，不要立即刷新
2. 用 control-mcp 的 capture_window / capture_region 截图确认验证框真实位置
3. 必要时加 grid_rows + grid_cols，先在网格图上定位复选框或按钮
4. 用 resolve_grid_target 或直接换算坐标后，调用 mouse_click
5. wait(1-2s) 后再回到 chrome-devtools 继续观察页面是否通过验证
```

补充原则：
- `chrome-devtools` 负责读页面结构和后续导航，`control-mcp` 负责处理这类需要真实屏幕点击的验证控件
- 先截图再点击，避免直接猜测 Cloudflare 复选框位置
- 如果验证框在 iframe 内、DOM 能看到但点击无效，优先切到 `control-mcp` 走屏幕级点击
- 完成验证后再回到 `chrome-devtools_take_snapshot` 或 `wait_for` 检查页面是否恢复正常

## 常见误判

### 1. 目标已经打开，却又回到全局搜索

修正：
- 先判断是否已经进入目标上下文
- 能在当前界面继续，就不要重新走入口

### 2. 以为窗口已聚焦，就等于窗口可操作

修正：

```text
focus_window -> Win+Up -> wait -> screenshot verify
```

### 3. 以为内容稳定，只因为这一刻没变化

修正：
- 至少两轮对比
- 对比末尾内容、滚动条位置或时间戳

### 4. 对长内容使用“滚一次截一张”的人工流程

修正：
- 优先 `capture_scroll_region`
- 手动流程只保留给导航和局部确认

### 5. 聚焦失败后不停重试同一个 API

修正：
- 立刻换 `Alt+Tab`、任务栏、标题栏点击
- 目标是恢复上下文，不是证明某个 API 一定要成功

## 文档导航

- 坐标换算：[docs/coordinate-system.md](./docs/coordinate-system.md)
- 窗口管理与窗口救援：[docs/window-management.md](./docs/window-management.md)
- JetBrains 运行与日志观察：[docs/idea-run-workflow.md](./docs/idea-run-workflow.md)
