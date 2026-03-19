from io import StringIO

from rich.console import Console


def test_display_header():
    from research_graph.display import display_header

    console = Console(file=StringIO(), force_terminal=True)
    display_header("Test Topic", "abc123", console=console)
    output = console.file.getvalue()
    assert "Test Topic" in output


def test_display_plan():
    from research_graph.display import display_plan

    console = Console(file=StringIO(), force_terminal=True)
    queries = ["Query 1", "Query 2", "Query 3"]
    display_plan(queries, console=console)
    output = console.file.getvalue()
    assert "Query 1" in output
    assert "Query 2" in output


def test_display_critic_feedback():
    from research_graph.display import display_critic_feedback

    console = Console(file=StringIO(), force_terminal=True)
    display_critic_feedback("Good coverage overall", True, console=console)
    output = console.file.getvalue()
    assert "Good coverage" in output
