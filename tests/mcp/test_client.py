from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from smartrouter.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_fetch_tools_success() -> None:
    client = MCPClient()
    server_command = ["npx", "-y", "@modelcontextprotocol/server-git"]

    mock_tool_kwargs: dict[str, Any] = {
        "name": "test_tool",
        "description": "A test tool",
    }
    if "inputSchema" in Tool.model_fields:
        mock_tool_kwargs["inputSchema"] = {"type": "object"}
    else:
        mock_tool_kwargs["input_schema"] = {"type": "object"}

    mock_tool = Tool(**mock_tool_kwargs)
    mock_list_tools_result = ListToolsResult(tools=[mock_tool])

    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=mock_list_tools_result)

    mock_stdio_client = AsyncMock()
    mock_stdio_client.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    mock_stdio_client.__aexit__ = AsyncMock()

    mock_client_session_context = AsyncMock()
    mock_client_session_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_client_session_context.__aexit__ = AsyncMock()

    with (
        patch("smartrouter.mcp.client.stdio_client", return_value=mock_stdio_client),
        patch(
            "smartrouter.mcp.client.ClientSession",
            return_value=mock_client_session_context,
        ),
    ):
        tools = await client.fetch_tools(server_command)
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["description"] == "A test tool"
        assert tools[0]["parameters"] == {"type": "object"}


@pytest.mark.asyncio
async def test_fetch_tools_fallback() -> None:
    client = MCPClient()
    server_command = ["npx", "-y", "@modelcontextprotocol/server-git"]

    with patch(
        "smartrouter.mcp.client.stdio_client",
        side_effect=Exception("Connection failed"),
    ):
        tools = await client.fetch_tools(server_command)
        assert len(tools) == 2
        assert tools[0]["name"] == "grep"
        assert tools[1]["name"] == "git_status"


@pytest.mark.asyncio
async def test_execute_tool_success() -> None:
    client = MCPClient()
    server_command = ["npx", "-y", "@modelcontextprotocol/server-git"]
    tool_name = "test_tool"
    arguments = {"arg1": "val1"}

    mock_content = TextContent(type="text", text="output data")

    # Constructing CallToolResult
    kwargs: dict[str, Any] = {"content": [mock_content]}
    if "isError" in CallToolResult.model_fields:
        kwargs["isError"] = False
    else:
        kwargs["is_error"] = False

    mock_call_tool_result = CallToolResult(**kwargs)

    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(return_value=mock_call_tool_result)

    mock_stdio_client = AsyncMock()
    mock_stdio_client.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    mock_stdio_client.__aexit__ = AsyncMock()

    mock_client_session_context = AsyncMock()
    mock_client_session_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_client_session_context.__aexit__ = AsyncMock()

    with (
        patch("smartrouter.mcp.client.stdio_client", return_value=mock_stdio_client),
        patch(
            "smartrouter.mcp.client.ClientSession",
            return_value=mock_client_session_context,
        ),
    ):
        result = await client.execute_tool(server_command, tool_name, arguments)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["text"] == "output data"
        assert "isError" not in result


@pytest.mark.asyncio
async def test_execute_tool_fallback() -> None:
    client = MCPClient()
    server_command = ["npx", "-y", "@modelcontextprotocol/server-git"]
    tool_name = "test_tool"
    arguments = {"arg1": "val1"}

    with patch(
        "smartrouter.mcp.client.stdio_client",
        side_effect=Exception("Connection failed"),
    ):
        result = await client.execute_tool(server_command, tool_name, arguments)
        assert result["status"] == "error"
        assert "Dummy fallback for execution of test_tool" in result["message"]
