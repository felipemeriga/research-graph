from __future__ import annotations

from langchain_tavily import TavilySearch

from research_graph.state import ResearchFinding

_tavily_tool: TavilySearch | None = None
_tavily_news_tool: TavilySearch | None = None


def create_tavily_tool(max_results: int = 5) -> TavilySearch:
    global _tavily_tool, _tavily_news_tool
    _tavily_tool = TavilySearch(max_results=max_results)
    _tavily_news_tool = TavilySearch(
        max_results=max_results,
        topic="news",
        time_range="month",
    )
    return _tavily_tool


def _is_news_query(query: str) -> bool:
    """Detect if a query is looking for recent news/events."""
    news_signals = [
        "news",
        "latest",
        "recent",
        "update",
        "2025",
        "2026",
        "this week",
        "this month",
        "today",
        "announce",
        "release",
        "launch",
        "new feature",
    ]
    query_lower = query.lower()
    return any(signal in query_lower for signal in news_signals)


def _parse_results(query: str, raw) -> list[ResearchFinding]:
    if isinstance(raw, str):
        return [{"query": query, "source": "tavily", "content": raw, "tool": "tavily"}]
    # TavilySearch returns {"query": ..., "results": [...]}
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    findings: list[ResearchFinding] = []
    for r in results:
        findings.append(
            {
                "query": query,
                "source": r.get("url", "unknown"),
                "content": r.get("content", ""),
                "tool": "tavily",
            }
        )
    return findings


def search_web(query: str, max_results: int = 5) -> list[ResearchFinding]:
    if _tavily_tool is None or _tavily_news_tool is None:
        raise RuntimeError("Tavily tool not initialized. Call create_tavily_tool() first.")

    tool = _tavily_news_tool if _is_news_query(query) else _tavily_tool
    raw = tool.invoke(query)
    return _parse_results(query, raw)[:max_results]
