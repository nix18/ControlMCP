# computer-control

> 让 Agent 通过 ControlMCP 更稳定地操作桌面应用，重点覆盖窗口恢复、键盘优先、局部上下文推进、截图点击换算，以及滚动区域长截图。

## 目录结构

```text
computer-control/
├── SKILL.md
├── docs/
│   ├── coordinate-system.md
│   ├── window-management.md
│   └── idea-run-workflow.md
└── README.md
```

## 这个 Skill 解决什么问题

- 避免“窗口到了前台但其实还不可操作”的误判
- 避免目标页面已经打开后，又重复回到搜索/主页入口
- 在必须点击时，明确完成截图坐标到屏幕坐标的换算
- 在长内容场景里，优先用 `capture_scroll_region` 做连续采集，而不是手动滚动+单张截图
- 在 IDE、聊天软件、浏览器、设置页这类多面板应用中，降低误操作率
- 先把模糊操作指令转成结构化计划，再执行
- 对支付、密码、资产类动作先走确认闸门
- 在快捷键误用或界面跑偏后，优先走恢复流程而不是继续幻觉操作
- 对于小按钮、小图标、密集表格，优先使用“网格辅助截图 + 网格定位”来修正点击偏差

## 重构后的推荐入口

优先顺序从：

```text
直接截图/直接按键/直接点击
```

升级为：

```text
plan_desktop_task -> execute_desktop_plan -> 必要时 confirm_sensitive_action / recover_execution_context
```

只有在你已经非常明确知道要做哪一个原子动作时，才直接调用底层工具。

## 这次重构后的重点

- 从“特定程序经验”升级为“通用桌面操作原则”
- 强化“全局导航 vs 局部推进”的区分
- 把聚焦失败视为常态场景，加入 `Alt+Tab` / 任务栏 / 标题栏点击兜底
- 增加滚动区域长截图 SOP，适配新的 `capture_scroll_region` tool
- 增加 Windows 托盘恢复、遮挡恢复、微信托盘登录态恢复的双层策略

## 什么时候该用这个 Skill

- 要操作聊天软件、浏览器、IDE、系统设置、办公软件
- 要读取一个已经打开的滚动页面或长列表
- 要做截图驱动的精确点击
- 要判断页面、日志或滚动内容是否稳定

## 推荐阅读顺序

1. 先读 `SKILL.md`
2. 需要点击换算时看 `docs/coordinate-system.md`
3. 窗口异常时看 `docs/window-management.md`
4. 要操作 JetBrains IDE 时看 `docs/idea-run-workflow.md`

## 安装到 Agent

你可以把这个目录复制到 Agent 的 `skills/` 目录，或者直接做软链接。

### 方式 1：复制目录

```bash
# Codex CLI
cp -r skills/computer-control ~/.codex/skills/

# Claude Code
cp -r skills/computer-control ~/.claude/skills/

# OpenCode
cp -r skills/computer-control ~/.config/opencode/skills/
```

### 方式 2：创建软链接

macOS / Linux:

```bash
ln -s "$(pwd)/skills/computer-control" ~/.codex/skills/computer-control
ln -s "$(pwd)/skills/computer-control" ~/.claude/skills/computer-control
ln -s "$(pwd)/skills/computer-control" ~/.config/opencode/skills/computer-control
```

Windows:

```bat
mklink /D "%USERPROFILE%\.codex\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.claude\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.config\opencode\skills\computer-control" "%CD%\skills\computer-control"
```

如果你会频繁迭代这个 Skill，优先用软链接。
