from __future__ import annotations

import uuid

import click
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from research_graph.config import load_config
from research_graph.display import (
    display_critic_feedback,
    display_header,
    display_plan,
    display_report_saved,
    display_status,
    get_console,
    prompt_approval,
)
from research_graph.graph import create_research_graph


def _stream_graph(graph, input_value, thread_config):
    """Run graph with streaming, printing node progress."""
    console = get_console()
    for chunk in graph.stream(input_value, thread_config, stream_mode="updates", subgraphs=True):
        # With subgraphs=True, chunk is (namespace_tuple, {node: update})
        if isinstance(chunk, tuple):
            _namespace, data = chunk
        else:
            data = chunk
        for node_name, update in data.items():
            if node_name == "__interrupt__":
                continue
            if not isinstance(update, dict):
                console.print(f"  [dim]{node_name}[/dim] — done")
                continue
            status = update.get("status", "")
            findings_count = len(update.get("research_findings", []))
            sources_count = len(update.get("sources", []))
            sub_queries = update.get("sub_queries", [])
            if sub_queries:
                console.print(f"  [dim]{node_name}[/dim] — generated {len(sub_queries)} queries")
            elif findings_count:
                console.print(
                    f"  [dim]{node_name}[/dim] — found {findings_count} results, "
                    f"{sources_count} sources"
                )
            elif status:
                console.print(f"  [dim]{node_name}[/dim] — {status}")
            else:
                console.print(f"  [dim]{node_name}[/dim] — done")


def _run_interrupt_loop(graph, thread_config):
    """Handle pending interrupts until the graph reaches END."""
    state = graph.get_state(thread_config)
    while state.tasks:
        interrupt_task = state.tasks[0]
        if not interrupt_task.interrupts:
            break
        resume_value = _handle_interrupt(interrupt_task.interrupts[0].value)
        # graph.invoke(Command(resume=resume_value), thread_config)
        _stream_graph(graph, Command(resume=resume_value), thread_config)
        state = graph.get_state(thread_config)


def _handle_interrupt(interrupt_value: dict):
    console = get_console()
    action = interrupt_value.get("action", "")

    if "plan" in action.lower() or "sub_queries" in interrupt_value:
        queries = interrupt_value.get("sub_queries", [])
        display_plan(queries)
        choice = prompt_approval("Approve this plan? [y/n/edit]:")
        if choice.lower() == "y":
            return {"approved": True, "sub_queries": queries}
        elif choice.lower() == "edit":
            console.print("[dim]Enter new queries, one per line. Empty line to finish:[/dim]")
            new_queries = []
            while True:
                line = console.input("  > ")
                if not line.strip():
                    break
                new_queries.append(line.strip())
            return {"approved": True, "sub_queries": new_queries or queries}
        return {"approved": False}

    if "continue" in action.lower() or "cycle" in str(interrupt_value):
        criticism = interrupt_value.get("criticism", "")
        cycle = interrupt_value.get("cycle", 0)
        display_critic_feedback(criticism, False)
        choice = prompt_approval(f"Continue researching? (cycle {cycle + 1}) [y/n]:")
        return choice.lower() == "y"

    if "report" in action.lower():
        findings = interrupt_value.get("findings_count", 0)
        sources = interrupt_value.get("sources_count", 0)
        console.print(
            f"\n[bold]Ready to write report:[/bold] {findings} findings, {sources} sources"
        )
        choice = prompt_approval("Generate final report? [y/n]:")
        return choice.lower() == "y"

    return True


@click.group()
def cli():
    """Deep Research Agent — powered by LangGraph."""
    pass


@cli.command()
@click.argument("topic")
@click.option("--config-path", default="config.yaml", help="Path to config.yaml")
def research(topic: str, config_path: str):
    """Start a new research session on TOPIC."""
    import os

    config = load_config(config_path)
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        click.echo("Error: SUPABASE_DB_URL not set in .env", err=True)
        raise SystemExit(1)

    thread_id = str(uuid.uuid4())
    display_header(topic, thread_id)
    display_status("Starting research...")

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_research_graph(config, checkpointer=checkpointer)
        thread_config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "topic": topic,
            "sub_queries": [],
            "current_query_index": 0,
            "research_findings": [],
            "criticism": "",
            "critic_approved": False,
            "research_cycle_count": 0,
            "final_report": "",
            "sources": [],
            "status": "planning",
        }

        # graph.invoke(initial_state, thread_config)
        _stream_graph(graph, initial_state, thread_config)
        _run_interrupt_loop(graph, thread_config)

        final_state = graph.get_state(thread_config)
        if final_state.values.get("final_report"):
            display_report_saved(f"Report generated for thread {thread_id}")
        else:
            get_console().print("\n[yellow]Research session ended.[/yellow]")


@cli.command()
@click.option("--thread-id", required=True, help="Thread ID to resume")
@click.option("--config-path", default="config.yaml", help="Path to config.yaml")
def resume(thread_id: str, config_path: str):
    """Resume a previous research session."""
    import os

    config = load_config(config_path)
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        click.echo("Error: SUPABASE_DB_URL not set in .env", err=True)
        raise SystemExit(1)

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_research_graph(config, checkpointer=checkpointer)
        thread_config = {"configurable": {"thread_id": thread_id}}

        # graph.invoke(None, thread_config)
        _stream_graph(graph, None, thread_config)
        _run_interrupt_loop(graph, thread_config)

        final_state = graph.get_state(thread_config)
        if final_state.values.get("final_report"):
            display_report_saved(f"Report generated for thread {thread_id}")
        else:
            get_console().print("\n[yellow]Research session ended.[/yellow]")


@cli.command()
@click.option("--config-path", default="config.yaml", help="Path to config.yaml")
def sessions(config_path: str):
    """List past research sessions."""
    import os

    from rich.table import Table

    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        click.echo("Error: SUPABASE_DB_URL not set in .env", err=True)
        raise SystemExit(1)

    console = get_console()
    console.print("\n[bold]Past Research Sessions:[/bold]\n")

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        table = Table(show_header=True)
        table.add_column("Thread ID")
        table.add_column("Status")
        console.print(table)
    console.print(
        "[dim]Tip: Use 'research-graph resume --thread-id <id>' to resume a session.[/dim]"
    )


if __name__ == "__main__":
    cli()
