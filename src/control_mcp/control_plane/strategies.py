"""Built-in desktop workflow strategies and references."""

from __future__ import annotations

from typing import Any

WINDOWS_SHORTCUTS_REFERENCE_URL = (
    "https://support.microsoft.com/zh-cn/windows/"
    "windows-%E7%9A%84%E9%94%AE%E7%9B%98%E5%BF%AB%E6%8D%B7%E6%96%B9%E5%BC%8F-"
    "dcc61a57-8ff0-cffe-9796-cb9706c75eec#windowsversion=windows_11"
)

BUILTIN_STRATEGIES: list[dict[str, Any]] = [
    {
        "id": "windows-tray-restore",
        "layer": "builtin",
        "title": "Windows 托盘恢复",
        "platform": "Windows",
        "keywords": ["托盘", "后台驻留", "通知区域", "tray", "system tray"],
        "summary": "后台驻留应用优先用 Win+B 进入通知区域，再用 Enter 恢复，不要先重新启动实例。",
        "preferred_actions": [
            "key_press Win+B",
            "wait 0.5s",
            "key_press Enter",
            "capture after restore",
        ],
        "anti_patterns": [
            "single screenshot locate tray icon only",
            "launch_app same application again",
        ],
        "verification_hints": [
            "tray icons can flash and may not appear in a single screenshot",
            "prefer keyboard navigation when tray visibility is unstable",
        ],
    },
    {
        "id": "wechat-tray-restore",
        "layer": "builtin",
        "title": "微信托盘恢复",
        "platform": "Windows",
        "keywords": ["微信", "wechat"],
        "summary": "如果微信已有登录态，优先从托盘恢复主窗口，而不是再次启动一个微信实例。",
        "preferred_actions": [
            "recover_execution_context strategy=wechat_tray_restore",
            "focus_window 微信",
        ],
        "anti_patterns": ["launch_app WeChat.exe repeatedly"],
        "verification_hints": [
            "restore the existing main window before any launch attempt",
        ],
    },
    {
        "id": "occlusion-rescue",
        "layer": "builtin",
        "title": "遮挡恢复",
        "platform": "Windows",
        "keywords": ["遮挡", "挡住", "behind", "occluded", "被其他窗口盖住"],
        "summary": "窗口被遮挡时，优先重新聚焦并最大化；必要时 Win+D 显示桌面后再重新聚焦。",
        "preferred_actions": ["focus_window", "Win+Up", "Win+D then refocus"],
        "anti_patterns": ["keep clicking through overlapped windows"],
        "verification_hints": [
            "after Win+D, refocus the target window instead of assuming visibility",
        ],
    },
    {
        "id": "windows-shortcuts-reference",
        "layer": "builtin",
        "title": "Windows 官方快捷键参考",
        "platform": "Windows",
        "keywords": ["windows 快捷键", "windows shortcuts", "win+b", "win+d"],
        "summary": "Windows 快捷键以 Microsoft 官方文档为准。",
        "reference_url": WINDOWS_SHORTCUTS_REFERENCE_URL,
        "preferred_actions": ["consult official shortcut reference when uncertain"],
        "anti_patterns": ["guess OS-level shortcuts from memory when uncertain"],
        "verification_hints": ["shortcut behavior can vary across applications"],
    },
]


def match_builtin_strategies(instruction: str, app: str | None = None) -> list[dict[str, Any]]:
    lower = instruction.lower()
    app_lower = (app or "").lower()
    matched: list[dict[str, Any]] = []
    for strategy in BUILTIN_STRATEGIES:
        keywords = strategy.get("keywords", [])
        if any(keyword.lower() in lower or keyword.lower() in app_lower for keyword in keywords):
            matched.append(strategy)
    if app_lower in {"wechat", "微信"}:
        for strategy in BUILTIN_STRATEGIES:
            if strategy["id"] == "wechat-tray-restore" and strategy not in matched:
                matched.append(strategy)
    return matched
