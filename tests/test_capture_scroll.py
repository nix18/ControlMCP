"""Tests for stitched scroll-capture helpers."""

import pytest
from PIL import Image, ImageDraw

from control_mcp.utils.capture import (
    _compose_vertical,
    _extract_new_scrolled_part,
    capture_scroll_region,
)


def _make_canvas(width: int = 120, height: int = 720, stripe_height: int = 40) -> Image.Image:
    canvas = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(canvas)

    for index, top in enumerate(range(0, height, stripe_height)):
        color = (
            (index * 23) % 255,
            (index * 47) % 255,
            (index * 71) % 255,
        )
        draw.rectangle((0, top, width, min(height, top + stripe_height)), fill=color)

    return canvas


def test_extract_new_part_for_downward_scroll():
    canvas = _make_canvas()
    previous = canvas.crop((0, 0, 120, 240))
    current = canvas.crop((0, 120, 120, 360))

    new_part = _extract_new_scrolled_part(previous, current, scroll_down=True)

    assert new_part is not None
    stitched = _compose_vertical([previous, new_part])
    expected = canvas.crop((0, 0, 120, 360))
    assert stitched.size == expected.size
    assert list(stitched.getdata()) == list(expected.getdata())


def test_extract_new_part_for_upward_scroll():
    canvas = _make_canvas()
    previous = canvas.crop((0, 200, 120, 440))
    current = canvas.crop((0, 80, 120, 320))

    new_part = _extract_new_scrolled_part(previous, current, scroll_down=False)

    assert new_part is not None
    stitched = _compose_vertical([new_part, previous])
    expected = canvas.crop((0, 80, 120, 440))
    assert stitched.size == expected.size
    assert list(stitched.getdata()) == list(expected.getdata())


def test_capture_scroll_region_public_api(tmp_path, monkeypatch):
    canvas = _make_canvas()
    initial = canvas.crop((0, 0, 120, 240))
    current = canvas.crop((0, 120, 120, 360))
    move_calls: list[tuple[int, int, float]] = []
    scroll_calls: list[tuple[int, int, int]] = []

    images = iter([initial, current])

    monkeypatch.setattr(
        "control_mcp.utils.capture._capture_region_image",
        lambda *args, **kwargs: next(images),
    )
    monkeypatch.setattr(
        "control_mcp.utils.capture.pyautogui.moveTo",
        lambda x, y, duration=0.0: move_calls.append((x, y, duration)),
    )
    monkeypatch.setattr(
        "control_mcp.utils.capture.pyautogui.scroll",
        lambda clicks, x=None, y=None: scroll_calls.append((clicks, x, y)),
    )
    monkeypatch.setattr("control_mcp.utils.capture.time.sleep", lambda seconds: None)
    monkeypatch.setattr(
        "control_mcp.utils.capture._save_image",
        lambda img, save_path, filename, quality: (str(tmp_path / "stitched.jpg"), 2048),
    )

    result = capture_scroll_region(
        x=10,
        y=20,
        width=120,
        height=240,
        scroll_distance=-120,
        save_dir=tmp_path,
        quality=75,
        max_width=80,
        settle_time=0.1,
    )

    assert move_calls == [(70, 140, 0.05)]
    assert scroll_calls == [(-120, 70, 140)]
    assert result.file_path.endswith("stitched.jpg")
    assert result.capture_count == 2
    assert result.scroll_distance == -120
    assert result.quality == 75
    assert result.file_size == 2048
    assert result.width == 80
    assert result.height == 240


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"width": 0, "height": 240, "scroll_distance": -120}, "width and height must be positive"),
        ({"width": 120, "height": 240, "scroll_distance": 0}, "scroll_distance must be non-zero"),
    ],
)
def test_capture_scroll_region_rejects_invalid_input(kwargs, message):
    with pytest.raises(ValueError, match=message):
        capture_scroll_region(x=10, y=20, save_dir=".", **kwargs)
