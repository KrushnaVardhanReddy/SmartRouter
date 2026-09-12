import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Model Context Protocol (MCP) Client for interacting with osmcp server.
    """

    async def fetch_tools(self, server_url: str) -> list[dict[str, Any]]:
        """
        Fetches tools from the given MCP server URL.
        Returns a list of JSON-schema tools.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server_url}/tools")
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return data
                return []
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch tools from {server_url}: {e}. Returning dummy tools.")
            # Dummy tools as fallback for now
            return [
                {
                    "name": "grep",
                    "description": "Search for a pattern in files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string"}
                        },
                        "required": ["pattern"]
                    }
                },
                {
                    "name": "git_status",
                    "description": "Get git status",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    }
                }
            ]

    async def execute_tool(self, server_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a specific tool on the MCP server.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{server_url}/tools/{tool_name}/execute",
                    json=arguments
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    return data
                return {"result": data}
        except httpx.HTTPError as e:
            logger.warning(f"Failed to execute tool {tool_name} on {server_url}: {e}. Returning dummy result.")
            return {"status": "error", "message": f"Dummy fallback for execution of {tool_name}"}
