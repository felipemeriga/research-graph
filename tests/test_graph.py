from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from research_graph.config import AppConfig


def _make_mock_llm(responses: list[str]) -> MagicMock:
    mock = MagicMock()
    mock.invoke.side_effect = [AIMessage(content=r) for r in responses]
    return mock


def test_full_graph_reaches_plan_interrupt():
    from research_graph.graph import create_research_graph

    config = AppConfig()
    mock_llm = _make_mock_llm(['["Query 1", "Query 2"]'])

    checkpointer = InMemorySaver()
    with (
        patch("research_graph.graph.create_llm", return_value=mock_llm),
        patch("research_graph.graph.create_tavily_tool"),
    ):
        graph = create_research_graph(config, checkpointer=checkpointer)

    thread_config = {"configurable": {"thread_id": "test-full-1"}}

    graph.invoke(
        {
            "topic": "test topic",
            "sub_queries": [],
            "status": "planning",
            "current_query_index": 0,
            "research_findings": [],
            "criticism": "",
            "critic_approved": False,
            "research_cycle_count": 0,
            "final_report": "",
            "sources": [],
        },
        thread_config,
    )
    # Should pause at plan approval interrupt
    state = graph.get_state(thread_config)
    assert len(state.tasks) > 0


def test_full_graph_plan_rejection_ends():
    from research_graph.graph import create_research_graph

    config = AppConfig()
    mock_llm = _make_mock_llm(['["Query 1", "Query 2"]'])

    checkpointer = InMemorySaver()
    with (
        patch("research_graph.graph.create_llm", return_value=mock_llm),
        patch("research_graph.graph.create_tavily_tool"),
    ):
        graph = create_research_graph(config, checkpointer=checkpointer)

    thread_config = {"configurable": {"thread_id": "test-reject-1"}}

    graph.invoke(
        {
            "topic": "test topic",
            "sub_queries": [],
            "status": "planning",
            "current_query_index": 0,
            "research_findings": [],
            "criticism": "",
            "critic_approved": False,
            "research_cycle_count": 0,
            "final_report": "",
            "sources": [],
        },
        thread_config,
    )
    # Reject plan
    result = graph.invoke(Command(resume={"approved": False}), thread_config)
    assert result["status"] == "error"
