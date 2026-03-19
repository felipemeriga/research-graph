from unittest.mock import MagicMock

from langchain_core.messages import AIMessage


def test_writer_generates_report(tmp_path):
    from research_graph.agents.writer import create_writer_graph

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="# Research Report\n\n## Summary\nGreat findings."
    )

    graph = create_writer_graph(mock_llm, output_dir=str(tmp_path))
    compiled = graph.compile()
    result = compiled.invoke(
        {
            "topic": "test topic",
            "sub_queries": ["q1"],
            "current_query_index": 0,
            "research_findings": [
                {"query": "q1", "source": "url", "content": "content", "tool": "tavily"}
            ],
            "criticism": "",
            "critic_approved": True,
            "research_cycle_count": 1,
            "sources": ["https://example.com"],
            "final_report": "",
            "status": "writing",
        }
    )
    assert "# Research Report" in result["final_report"]
    assert result["status"] == "complete"
    # Verify file was saved
    report_files = list(tmp_path.glob("*.md"))
    assert len(report_files) == 1
