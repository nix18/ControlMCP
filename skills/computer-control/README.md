# Computer Control Skill

> 让 Agent 熟练操作电脑的 Skill — 配合 ControlMCP 使用。

## 安装

将 `computer-control` 文件夹复制到你的 Agent 配置目录下的 `skills/` 文件夹：

```bash
# Claude Code
cp -r skills/computer-control ~/.claude/skills/

# OpenCode
cp -r skills/computer-control ~/.config/opencode/skills/

# 或直接在 Agent 配置中引用本文件夹路径
```

## 前置条件

1. **安装 ControlMCP:**
   ```bash
   pip install control-mcp
   ```

2. **配置 MCP Server**（在 Agent 客户端配置中添加）:
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

## 文件结构

```
computer-control/
├── SKILL.md                          # 主文档：操作原则 + SOP + 速查表
├── docs/
│   └── coordinate-system.md          # 坐标系统详细参考
└── README.md                         # 本文件
```

## 覆盖内容

- **5 大黄金法则**: 键盘优先、坐标转换、截图成本、操作等待、先验证再操作
- **7 个标准 SOP**: 窗口操作、截图点击、键盘序列、复合操作、像素验证、剪贴板输入、文件导航
- **IDE 速查表**: IntelliJ IDEA (20+ 快捷键)、VS Code (15+ 快捷键)、Eclipse
- **浏览器速查表**: 20+ 快捷键
- **系统速查表**: Windows/macOS 常用操作
- **7 个常见陷阱**: 坐标混淆、DPI、窗口遮挡、key_sequence、弹窗阻断、输入法、双屏
- **6 个 Token 优化策略**: JPEG压缩、缩小分辨率、截窗口、批量操作、wait 替代轮询、剪贴板替代输入
- **坐标系统详解**: 从截图到点击的完整转换流程

## 使用方式

安装后，在与 Agent 对话时只需说：

- "帮我操作 IDEA 重启项目"
- "打开浏览器搜索 xxx"
- "在 VS Code 里格式化代码"

Agent 会自动按照 SKILL.md 中的 SOP 执行操作。
