"""Tests for dual-layer strategy hint collection."""

from control_mcp.control_plane.memory import collect_strategy_hints


def test_collect_strategy_hints_returns_builtin_tray_rules():
    hints = collect_strategy_hints("从托盘恢复微信主窗口")
    ids = [hint["id"] for hint in hints]
    assert "windows-tray-restore" in ids
    assert "wechat-tray-restore" in ids


def test_collect_strategy_hints_deduplicates_memory_and_builtin(monkeypatch):
    monkeypatch.setattr(
        "control_mcp.control_plane.memory.list_experiences",
        lambda limit=50: [
            {
                "experience_id": "windows-tray-restore",
                "instruction": "托盘恢复",
                "summary": "duplicate builtin",
                "app": "微信",
            },
            {
                "experience_id": "exp_custom",
                "instruction": "托盘恢复微信主窗口",
                "summary": "custom memory hint",
                "app": "微信",
            },
        ],
    )
    hints = collect_strategy_hints("托盘恢复微信主窗口", app="微信")
    ids = [hint["id"] for hint in hints]
    assert ids.count("windows-tray-restore") == 1
    assert "exp_custom" in ids
