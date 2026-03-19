from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

_console = Console()


def get_console() -> Console:
    return _console


def display_header(topic: str, thread_id: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(
        Panel(
            f"Topic: {topic}\nThread: {thread_id}",
            title="Research Agent",
            border_style="blue",
        )
    )


def display_plan(sub_queries: list[str], console: Console | None = None) -> None:
    c = console or _console
    lines = [f"  {i + 1}. {q}" for i, q in enumerate(sub_queries)]
    c.print(Panel("\n".join(lines), title="Plan", border_style="green"))


def display_critic_feedback(criticism: str, approved: bool, console: Console | None = None) -> None:
    c = console or _console
    style = "green" if approved else "yellow"
    title = "Critic: Approved" if approved else "Critic Feedback"
    c.print(Panel(criticism, title=title, border_style=style))


def display_research_progress(
    query_index: int, total: int, query: str, console: Console | None = None
) -> None:
    c = console or _console
    c.print(f'\n[bold]Researching sub-query {query_index + 1}/{total}:[/bold] "{query}"')


def display_finding_source(tool: str, detail: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"  [dim]├── {tool}: {detail}[/dim]")


def display_report_saved(path: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"\n[bold green]✓ Report saved to {path}[/bold green]")


def display_status(status: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"\n[bold cyan]⠋ {status}[/bold cyan]")


def prompt_approval(message: str, console: Console | None = None) -> str:
    c = console or _console
    return c.input(f"\n[bold yellow]? {message}[/bold yellow] ")
