from unittest.mock import patch


def test_create_tavily_tool():
    from research_graph.tools.tavily_search import create_tavily_tool

    with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
        tool = create_tavily_tool(max_results=3)
    assert tool is not None
    assert tool.name == "tavily_search"


def test_search_returns_findings():
    from research_graph.tools.tavily_search import search_web

    mock_results = [
        {"url": "https://example.com/1", "content": "Result 1"},
        {"url": "https://example.com/2", "content": "Result 2"},
    ]
    with patch("research_graph.tools.tavily_search._tavily_tool") as mock_tool:
        mock_tool.invoke.return_value = mock_results
        findings = search_web("test query", max_results=2)
    assert len(findings) == 2
    assert findings[0]["source"] == "https://example.com/1"
    assert findings[0]["tool"] == "tavily"
