from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from research_graph.config import MCPConfig
from research_graph.state import ResearchState
from research_graph.tools.mcp_client import mcp_search
from research_graph.tools.scraper import scrape_page
from research_graph.tools.tavily_search import search_web

logger = logging.getLogger(__name__)


async def _research_queries(state: ResearchState, mcp_config: MCPConfig) -> dict:
    all_findings = []
    all_sources = []

    for query in state["sub_queries"]:
        # Tavily search (sync call, safe in async context)
        tavily_results = []
        try:
            tavily_results = search_web(query)
            all_findings.extend(tavily_results)
            all_sources.extend([f["source"] for f in tavily_results])
        except Exception as e:
            logger.warning("Tavily search failed for '%s': %s", query, e)

        # Scrape top URLs from Tavily results
        urls_to_scrape = [f["source"] for f in tavily_results[:2] if f["source"].startswith("http")]
        for url in urls_to_scrape:
            try:
                content = await scrape_page(url)
                if not content.startswith("Error"):
                    all_findings.append(
                        {
                            "query": query,
                            "source": url,
                            "content": content[:3000],
                            "tool": "playwright",
                        }
                    )
            except Exception as e:
                logger.warning("Scrape failed for '%s': %s", url, e)

        # MCP search
        try:
            mcp_results = await mcp_search(query, mcp_config)
            all_findings.extend(mcp_results)
            all_sources.extend([f["source"] for f in mcp_results])
        except Exception as e:
            logger.warning("MCP search failed for '%s': %s", query, e)

    if not all_findings:
        all_findings.append(
            {"query": "all", "source": "none", "content": "No results found", "tool": "none"}
        )

    return {
        "research_findings": all_findings,
        "sources": all_sources,
        "status": "critiquing",
    }


def create_researcher_graph(mcp_config: MCPConfig) -> StateGraph:
    async def research(state: ResearchState) -> dict:
        return await _research_queries(state, mcp_config)

    builder = StateGraph(ResearchState)
    builder.add_node("research", research)
    builder.add_edge(START, "research")
    builder.add_edge("research", END)
    return builder
