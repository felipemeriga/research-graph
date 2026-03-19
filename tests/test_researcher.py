from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_researcher_processes_all_queries():
    from research_graph.agents.researcher import create_researcher_graph
    from research_graph.config import MCPConfig

    mock_findings = [
        {"query": "q1", "source": "https://example.com", "content": "result", "tool": "tavily"}
    ]

    with (
        patch("research_graph.agents.researcher.search_web", return_value=mock_findings),
        patch(
            "research_graph.agents.researcher.scrape_page",
            new_callable=AsyncMock,
            return_value="scraped content",
        ),
        patch(
            "research_graph.agents.researcher.mcp_search",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        graph = create_researcher_graph(MCPConfig())
        compiled = graph.compile()
        result = await compiled.ainvoke(
            {
                "topic": "test",
                "sub_queries": ["query 1", "query 2"],
                "current_query_index": 0,
                "research_findings": [],
                "sources": [],
                "status": "researching",
                "criticism": "",
                "critic_approved": False,
                "research_cycle_count": 0,
                "final_report": "",
            }
        )
    assert len(result["research_findings"]) > 0
    assert len(result["sources"]) > 0
