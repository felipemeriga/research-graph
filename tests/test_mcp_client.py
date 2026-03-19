from unittest.mock import patch

import pytest

from research_graph.config import MCPConfig


@pytest.mark.asyncio
async def test_mcp_search_disabled_when_no_url():
    from research_graph.tools.mcp_client import mcp_search

    config = MCPConfig(server_url="", transport="stdio")
    results = await mcp_search("test query", config)
    assert results == []


@pytest.mark.asyncio
async def test_mcp_search_returns_findings():
    from research_graph.tools.mcp_client import mcp_search

    config = MCPConfig(server_url="http://localhost:3000", transport="sse")
    mock_result = [{"content": "MCP result", "source": "rag"}]

    with patch("research_graph.tools.mcp_client._call_mcp_server", return_value=mock_result):
        results = await mcp_search("test query", config)
    assert len(results) == 1
    assert results[0]["tool"] == "mcp"


@pytest.mark.asyncio
async def test_mcp_search_handles_connection_error():
    from research_graph.tools.mcp_client import mcp_search

    config = MCPConfig(server_url="http://localhost:3000", transport="sse")
    with patch(
        "research_graph.tools.mcp_client._call_mcp_server",
        side_effect=Exception("Connection refused"),
    ):
        results = await mcp_search("test query", config)
    assert results == []
