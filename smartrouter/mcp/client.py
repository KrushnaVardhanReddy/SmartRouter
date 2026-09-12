import logging
import os
import shlex
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Model Context Protocol (MCP) Client for interacting with osmcp server.
    """

    def _get_server_command(self, server_command: list[str]) -> list[str]:
        if server_command:
            return server_command
        env_cmd = os.getenv("SMARTROUTER_MCP_SERVER_CMD")
        if env_cmd:
            return shlex.split(env_cmd)
        return ["npx", "-y", "@modelcontextprotocol/server-git"]

    async def fetch_tools(self, server_command: list[str]) -> list[dict[str, Any]]:
        """
        Fetches tools from the given MCP server command.
        Returns a list of JSON-schema tools.
        """
        cmd_list = self._get_server_command(server_command)
        command, args = cmd_list[0], cmd_list[1:]

        server_params = StdioServerParameters(command=command, args=args, env=None)

        try:
            async with (
                stdio_client(server_params) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.list_tools()

                tools = []
                # mcp.types.ListToolsResult contains a 'tools' attribute, which is a list of mcp.types.Tool objects.
                for tool in result.tools:
                    tools.append(
                        {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema
                            if hasattr(tool, "inputSchema")
                            else getattr(tool, "input_schema", {}),
                        }
                    )
                return tools
        except Exception as e:
            logger.warning(
                f"Failed to fetch tools from {cmd_list}: {e}. Returning dummy tools."
            )
            # Dummy tools as fallback for now
            return [
                {
                    "name": "grep",
                    "description": "Search for a pattern in files",
                    "parameters": {
                        "type": "object",
                        "properties": {"pattern": {"type": "string"}},
                        "required": ["pattern"],
                    },
                },
                {
                    "name": "git_status",
                    "description": "Get git status",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            ]

    async def execute_tool(
        self, server_command: list[str], tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Executes a specific tool on the MCP server.
        """
        cmd_list = self._get_server_command(server_command)
        command, args = cmd_list[0], cmd_list[1:]

        server_params = StdioServerParameters(command=command, args=args, env=None)

        try:
            async with (
                stdio_client(server_params) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)

                # CallToolResult contains content list, isError bool. We'll map it to dict.
                output_data: dict[str, Any] = {}
                if result.content:
                    # Assuming text content
                    output_data["content"] = [
                        c.model_dump()
                        if hasattr(c, "model_dump")
                        else (c.dict() if hasattr(c, "dict") else c)
                        for c in result.content
                    ]
                is_error = getattr(
                    result, "isError", getattr(result, "is_error", False)
                )
                if is_error:
                    output_data["isError"] = True
                return output_data
        except Exception as e:
            logger.warning(
                f"Failed to execute tool {tool_name} on {cmd_list}: {e}. Returning dummy result."
            )
            return {
                "status": "error",
                "message": f"Dummy fallback for execution of {tool_name}",
            }
