"""Tests for MCP server wiring of registry-dispatched tools."""

import json
from unittest.mock import patch

import pytest

import control_mcp.server as server_module


def test_tools_expose_capture_scroll_region():
    assert any(tool.name == "capture_scroll_region" for tool in server_module.TOOLS)


@pytest.mark.asyncio
@patch("control_mcp.server.dispatch_tool")
async def test_handle_call_tool_dispatches_capture_scroll_region(mock_dispatch):
    mock_dispatch.return_value = '{"file_path": "/tmp/scroll.jpg", "capture_count": 2}'

    result = await server_module.handle_call_tool(
        "capture_scroll_region",
        {
            "x": 10,
            "y": 20,
            "width": 300,
            "height": 400,
            "scroll_distance": -480,
            "save_dir": "/shots",
            "quality": 75,
            "max_width": 800,
        },
    )

    mock_dispatch.assert_called_once_with(
        "capture_scroll_region",
        {
            "x": 10,
            "y": 20,
            "width": 300,
            "height": 400,
            "scroll_distance": -480,
            "save_dir": "/shots",
            "quality": 75,
            "max_width": 800,
        },
    )
    assert json.loads(result[0].text)["capture_count"] == 2
