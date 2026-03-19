def test_research_state_has_required_fields():
    from research_graph.state import ResearchState

    state: ResearchState = {
        "topic": "quantum computing",
        "sub_queries": ["query1"],
        "current_query_index": 0,
        "research_findings": [],
        "criticism": "",
        "critic_approved": False,
        "research_cycle_count": 0,
        "final_report": "",
        "sources": [],
        "status": "planning",
    }
    assert state["topic"] == "quantum computing"
    assert state["status"] == "planning"


def test_research_finding_structure():
    from research_graph.state import ResearchFinding

    finding: ResearchFinding = {
        "query": "test query",
        "source": "https://example.com",
        "content": "some content",
        "tool": "tavily",
    }
    assert finding["tool"] == "tavily"
