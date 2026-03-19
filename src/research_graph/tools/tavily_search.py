from __future__ import annotations

from langchain_tavily import TavilySearch

from research_graph.state import ResearchFinding

_tavily_tool: TavilySearch | None = None


def create_tavily_tool(max_results: int = 5) -> TavilySearch:
    global _tavily_tool
    _tavily_tool = TavilySearch(max_results=max_results)
    _tavily_tool.name = "tavily_search"
    return _tavily_tool


def search_web(query: str, max_results: int = 5) -> list[ResearchFinding]:
    if _tavily_tool is None:
        raise RuntimeError("Tavily tool not initialized. Call create_tavily_tool() first.")
    results = _tavily_tool.invoke(query)
    if isinstance(results, str):
        return [{"query": query, "source": "tavily", "content": results, "tool": "tavily"}]
    findings: list[ResearchFinding] = []
    for r in results[:max_results]:
        findings.append(
            {
                "query": query,
                "source": r.get("url", "unknown"),
                "content": r.get("content", ""),
                "tool": "tavily",
            }
        )
    return findings
