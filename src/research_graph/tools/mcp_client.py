from __future__ import annotations

import logging

from research_graph.config import MCPConfig
from research_graph.state import ResearchFinding

logger = logging.getLogger(__name__)


async def _call_mcp_server(query: str, config: MCPConfig) -> list[dict]:
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    if config.transport == "sse":
        async with sse_client(url=config.server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                if tools.tools:
                    result = await session.call_tool(
                        tools.tools[0].name, arguments={"query": query}
                    )
                    return [{"content": str(result), "source": config.server_url}]
    return []


async def mcp_search(query: str, config: MCPConfig) -> list[ResearchFinding]:
    if not config.server_url:
        return []
    try:
        raw_results = await _call_mcp_server(query, config)
        return [
            {
                "query": query,
                "source": r.get("source", "mcp"),
                "content": r.get("content", ""),
                "tool": "mcp",
            }
            for r in raw_results
        ]
    except Exception as e:
        logger.warning("MCP search failed: %s", e)
        return []
