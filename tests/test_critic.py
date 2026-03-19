from unittest.mock import MagicMock

from langchain_core.messages import AIMessage


def test_critic_approves_sufficient_findings():
    from research_graph.agents.critic import create_critic_graph

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content=(
            '{"approved": true, "criticism": "Comprehensive coverage.", "additional_queries": []}'
        )
    )

    graph = create_critic_graph(mock_llm)
    compiled = graph.compile()
    result = compiled.invoke(
        {
            "topic": "test topic",
            "sub_queries": ["q1"],
            "current_query_index": 0,
            "research_findings": [
                {"query": "q1", "source": "url", "content": "good content", "tool": "tavily"}
            ],
            "criticism": "",
            "critic_approved": False,
            "research_cycle_count": 0,
            "sources": [],
            "final_report": "",
            "status": "critiquing",
        }
    )
    assert result["critic_approved"] is True
    assert result["criticism"] == "Comprehensive coverage."


def test_critic_requests_more_research():
    from research_graph.agents.critic import create_critic_graph

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content=(
            '{"approved": false, "criticism": "Missing details on X.",'
            ' "additional_queries": ["What about X?"]}'
        )
    )

    graph = create_critic_graph(mock_llm)
    compiled = graph.compile()
    result = compiled.invoke(
        {
            "topic": "test topic",
            "sub_queries": ["q1"],
            "current_query_index": 0,
            "research_findings": [
                {"query": "q1", "source": "url", "content": "partial", "tool": "tavily"}
            ],
            "criticism": "",
            "critic_approved": False,
            "research_cycle_count": 0,
            "sources": [],
            "final_report": "",
            "status": "critiquing",
        }
    )
    assert result["critic_approved"] is False
    assert "What about X?" in result["sub_queries"]
