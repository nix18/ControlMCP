# computer-control

> 让 Agent 通过 ControlMCP 稳定地操控桌面应用，重点覆盖窗口管理、快捷键优先、截图点击、IDE 运行与日志观察。

## 目录结构

```text
computer-control/
├── SKILL.md                   # 主技能文档：法则、SOP、速查、常见失误
├── docs/
│   ├── coordinate-system.md   # 坐标体系与点击换算
│   ├── window-management.md   # 窗口管理快捷键与窗口救援流程
│   └── idea-run-workflow.md   # IDEA 启动应用与日志稳定判定
└── README.md
```

## 覆盖能力

- 桌面自动化：窗口聚焦、窗口修正、键盘操作、鼠标点击、剪贴板输入
- 低成本验证：截图参数选择、关键节点验证、轮询式稳定判断
- IDE 工作流：运行配置确认、Run 面板切换、日志停止更新判定
- 常见问题处理：窗口虽聚焦但未展开、Run 面板停留在引导页、日志误判为稳定

## 本次重构新增重点

- 把“窗口状态修复”提升为入场必做项，不再把 `focus_window()` 误当成“窗口已经可操作”
- 补充常用窗口管理快捷键：
  - 最大化窗口：`Win + Up`
  - 恢复/最小化窗口：`Win + Down`
  - 分屏/对齐窗口：`Win + Left` / `Win + Right`
- 增加 IDEA 启动应用后“等待日志不再更新”的明确判定流程
- 增加 JetBrains 系列 IDE 的兜底资料规则：快捷键不达预期时先查本机 `ReferenceCard.pdf`，再查官方在线文档

## 使用建议

- 简单操作先读 `SKILL.md`
- 需要精确点击时看 `docs/coordinate-system.md`
- 遇到窗口尺寸、最小化、分屏问题时看 `docs/window-management.md`
- 需要启动 IDEA 配置并观察日志时看 `docs/idea-run-workflow.md`

## 安装到 Agent

你可以把这个目录复制到 Agent 的 `skills/` 目录，也可以直接创建软链接。

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

macOS / Linux：

```bash
# Codex CLI
ln -s "$(pwd)/skills/computer-control" ~/.codex/skills/computer-control

# Claude Code
ln -s "$(pwd)/skills/computer-control" ~/.claude/skills/computer-control

# OpenCode
ln -s "$(pwd)/skills/computer-control" ~/.config/opencode/skills/computer-control
```

Windows：

```bat
mklink /D "%USERPROFILE%\.codex\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.claude\skills\computer-control" "%CD%\skills\computer-control"
mklink /D "%USERPROFILE%\.config\opencode\skills\computer-control" "%CD%\skills\computer-control"
```

如果你正在频繁修改这个 Skill，优先使用软链接，这样不需要每次重新复制目录。
