from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


def test_planner_generates_sub_queries():
    from research_graph.agents.planner import create_planner_graph

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content='["What is quantum computing?", "How does it affect cryptography?"]'
    )

    graph = create_planner_graph(mock_llm)
    checkpointer = InMemorySaver()
    compiled = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-1"}}

    compiled.invoke(
        {"topic": "quantum computing and cryptography", "sub_queries": [], "status": "planning"},
        config,
    )
    # Should hit interrupt for plan approval
    state = compiled.get_state(config)
    assert state.next == ("approve_plan",)
    assert len(state.tasks) > 0


def test_planner_applies_edited_queries():
    from research_graph.agents.planner import create_planner_graph

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content='["Query 1", "Query 2"]')

    graph = create_planner_graph(mock_llm)
    checkpointer = InMemorySaver()
    compiled = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-2"}}

    # First invoke — hits interrupt
    compiled.invoke(
        {"topic": "test topic", "sub_queries": [], "status": "planning"},
        config,
    )

    # Resume with edited queries
    result = compiled.invoke(
        Command(resume={"approved": True, "sub_queries": ["Edited Q1", "Edited Q2"]}),
        config,
    )
    assert result["sub_queries"] == ["Edited Q1", "Edited Q2"]
