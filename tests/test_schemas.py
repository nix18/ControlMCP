"""Tests for schema response types."""

import json
from control_mcp.schemas.responses import (
    OperationResult,
    ScreenshotResult,
    WindowScreenshotResult,
    WindowInfo,
    WindowListResult,
    ClickResult,
    DragResult,
    KeyResult,
    MousePosition,
    MonitorInfo,
    ScreenInfoResult,
    ClipboardResult,
    CompositeActionResult,
    make_screenshot_filename,
)


class TestOperationResult:
    def test_success(self):
        r = OperationResult(success=True, message="ok")
        d = r.to_dict()
        assert d["success"] is True
        assert d["message"] == "ok"
        assert d["details"] == {}

    def test_with_details(self):
        r = OperationResult(success=False, message="fail", details={"code": 42})
        j = json.loads(r.to_json())
        assert j["success"] is False
        assert j["details"]["code"] == 42


class TestScreenshotResult:
    def test_fields(self):
        r = ScreenshotResult(
            file_path="/tmp/test.png",
            timestamp="2026-03-20T14:00:00",
            width=1920,
            height=1080,
            x=0,
            y=0,
            monitor_index=1,
        )
        d = r.to_dict()
        assert d["file_path"] == "/tmp/test.png"
        assert d["width"] == 1920
        assert d["monitor_index"] == 1

    def test_defaults(self):
        r = ScreenshotResult(
            file_path="/tmp/test.png",
            timestamp="2026-03-20T14:00:00",
            width=800,
            height=600,
        )
        assert r.x == 0
        assert r.y == 0
        assert r.monitor_index is None

    def test_json_roundtrip(self):
        r = ScreenshotResult(
            file_path="/tmp/a.png", timestamp="t", width=100, height=200, x=10, y=20
        )
        j = json.loads(r.to_json())
        assert j["x"] == 10
        assert j["y"] == 20


class TestWindowScreenshotResult:
    def test_fields(self):
        r = WindowScreenshotResult(
            file_path="/tmp/win.png",
            timestamp="t",
            window_title="Notepad",
            window_x=100,
            window_y=200,
            window_width=800,
            window_height=600,
            screenshot_width=800,
            screenshot_height=600,
        )
        j = json.loads(r.to_json())
        assert j["window_title"] == "Notepad"
        assert j["window_x"] == 100


class TestWindowInfo:
    def test_to_dict(self):
        w = WindowInfo(title="Chrome", x=0, y=0, width=1024, height=768)
        d = w.to_dict()
        assert d["title"] == "Chrome"
        assert d["is_visible"] is True


class TestWindowListResult:
    def test_empty(self):
        r = WindowListResult()
        j = json.loads(r.to_json())
        assert j["windows"] == []

    def test_with_windows(self):
        r = WindowListResult(
            windows=[
                WindowInfo(title="A", x=0, y=0, width=100, height=100),
                WindowInfo(title="B", x=100, y=100, width=200, height=200),
            ]
        )
        assert len(r.to_dict()["windows"]) == 2


class TestClickResult:
    def test_success(self):
        r = ClickResult(success=True, x=500, y=300, clicks=1, button="left")
        j = json.loads(r.to_json())
        assert j["success"] is True
        assert j["button"] == "left"

    def test_failure(self):
        r = ClickResult(success=False, x=0, y=0, clicks=2, button="right", message="error")
        assert r.success is False


class TestDragResult:
    def test_fields(self):
        r = DragResult(success=True, start_x=10, start_y=20, end_x=100, end_y=200, button="left")
        d = r.to_dict()
        assert d["start_x"] == 10
        assert d["end_y"] == 200


class TestKeyResult:
    def test_press(self):
        r = KeyResult(success=True, keys=["ctrl", "c"], action="press")
        j = json.loads(r.to_json())
        assert j["keys"] == ["ctrl", "c"]
        assert j["action"] == "press"


class TestMousePosition:
    def test_fields(self):
        r = MousePosition(x=960, y=540)
        j = json.loads(r.to_json())
        assert j["x"] == 960
        assert j["y"] == 540


class TestMonitorInfo:
    def test_to_dict(self):
        m = MonitorInfo(index=1, x=0, y=0, width=1920, height=1080, is_primary=True)
        d = m.to_dict()
        assert d["is_primary"] is True


class TestScreenInfoResult:
    def test_empty(self):
        r = ScreenInfoResult()
        assert r.to_dict()["monitors"] == []


class TestClipboardResult:
    def test_get(self):
        r = ClipboardResult(success=True, content="hello", action="get")
        j = json.loads(r.to_json())
        assert j["content"] == "hello"


class TestCompositeActionResult:
    def test_all_success(self):
        r = CompositeActionResult(
            success=True,
            steps_completed=3,
            total_steps=3,
            results=[
                {"step": 0, "success": True},
                {"step": 1, "success": True},
                {"step": 2, "success": True},
            ],
        )
        j = json.loads(r.to_json())
        assert j["success"] is True
        assert j["steps_completed"] == 3

    def test_partial_failure(self):
        r = CompositeActionResult(
            success=False,
            steps_completed=2,
            total_steps=3,
            results=[
                {"step": 0, "success": True},
                {"step": 1, "success": False},
                {"step": 2, "success": True},
            ],
        )
        assert r.success is False


class TestMakeScreenshotFilename:
    def test_with_region(self):
        name = make_screenshot_filename(prefix="test", region=(10, 20, 800, 600))
        assert "test_" in name
        assert "800x600" in name
        assert "10_20" in name
        assert name.endswith(".png")

    def test_without_region(self):
        name = make_screenshot_filename(prefix="screen")
        assert "screen_" in name
        assert name.endswith(".png")

    def test_custom_extension(self):
        name = make_screenshot_filename(extension="jpg")
        assert name.endswith(".jpg")

    def test_unique_filenames(self):
        import time

        a = make_screenshot_filename()
        time.sleep(0.002)
        b = make_screenshot_filename()
        assert a != b
