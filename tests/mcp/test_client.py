import httpx
import pytest
import respx

from smartrouter.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_fetch_tools_success() -> None:
    client = MCPClient()
    server_url = "http://localhost:8000"

    mock_tools = [{"name": "test_tool", "description": "A test tool"}]

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(f"{server_url}/tools").mock(
            return_value=httpx.Response(200, json=mock_tools)
        )

        tools = await client.fetch_tools(server_url)
        assert tools == mock_tools


@pytest.mark.asyncio
async def test_fetch_tools_fallback() -> None:
    client = MCPClient()
    server_url = "http://localhost:8000"

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(f"{server_url}/tools").mock(return_value=httpx.Response(500))

        tools = await client.fetch_tools(server_url)
        assert len(tools) == 2
        assert tools[0]["name"] == "grep"
        assert tools[1]["name"] == "git_status"


@pytest.mark.asyncio
async def test_execute_tool_success() -> None:
    client = MCPClient()
    server_url = "http://localhost:8000"
    tool_name = "test_tool"
    arguments = {"arg1": "val1"}

    mock_result = {"status": "success", "data": "output"}

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.post(f"{server_url}/tools/{tool_name}/execute").mock(
            return_value=httpx.Response(200, json=mock_result)
        )

        result = await client.execute_tool(server_url, tool_name, arguments)
        assert result == mock_result


@pytest.mark.asyncio
async def test_execute_tool_fallback() -> None:
    client = MCPClient()
    server_url = "http://localhost:8000"
    tool_name = "test_tool"
    arguments = {"arg1": "val1"}

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.post(f"{server_url}/tools/{tool_name}/execute").mock(
            return_value=httpx.Response(500)
        )

        result = await client.execute_tool(server_url, tool_name, arguments)
        assert result["status"] == "error"
        assert "Dummy fallback for execution of test_tool" in result["message"]
