from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt

from research_graph.agents.critic import create_critic_graph
from research_graph.agents.planner import create_planner_graph
from research_graph.agents.researcher import create_researcher_graph
from research_graph.agents.writer import create_writer_graph
from research_graph.config import AppConfig
from research_graph.llm import create_llm
from research_graph.state import ResearchState
from research_graph.tools.tavily_search import create_tavily_tool


def _after_planner(state: ResearchState) -> Literal["researcher", "__end__"]:
    if state["status"] == "error":
        return END
    return "researcher"


def _should_continue_research(state: ResearchState) -> Literal["cycle_approval", "report_approval"]:
    if state["critic_approved"]:
        return "report_approval"
    return "cycle_approval"


def _make_cycle_approval(max_cycles: int):
    def _cycle_approval(state: ResearchState) -> Command[Literal["researcher", "report_approval"]]:
        if state["research_cycle_count"] >= max_cycles:
            return Command(update={"status": "writing"}, goto="report_approval")

        decision = interrupt(
            {
                "criticism": state["criticism"],
                "cycle": state["research_cycle_count"],
                "action": "Continue researching? [y/n]",
            }
        )
        if decision:
            return Command(
                update={"research_cycle_count": state["research_cycle_count"] + 1},
                goto="researcher",
            )
        return Command(update={"status": "writing"}, goto="report_approval")

    return _cycle_approval


def _report_approval(state: ResearchState) -> Command[Literal["writer", "__end__"]]:
    decision = interrupt(
        {
            "findings_count": len(state["research_findings"]),
            "sources_count": len(state["sources"]),
            "action": "Generate final report? [y/n]",
        }
    )
    if decision:
        return Command(update={"status": "writing"}, goto="writer")
    return Command(update={"status": "error"}, goto=END)


def create_research_graph(
    config: AppConfig,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    llm = create_llm(config.llm)
    create_tavily_tool(max_results=config.research.max_sources_per_query)

    # Create subgraphs
    planner = create_planner_graph(llm).compile()
    researcher = create_researcher_graph(config.mcp).compile()
    critic = create_critic_graph(llm).compile()
    writer = create_writer_graph(llm, output_dir=config.report.output_dir).compile()

    retry = RetryPolicy(max_attempts=3, initial_interval=1.0)

    # Build parent orchestrator
    builder = StateGraph(ResearchState)
    builder.add_node("planner", planner, retry_policy=retry)
    builder.add_node("researcher", researcher, retry_policy=retry)
    builder.add_node("critic", critic, retry_policy=retry)
    builder.add_node("cycle_approval", _make_cycle_approval(config.research.max_cycles))
    builder.add_node("report_approval", _report_approval)
    builder.add_node("writer", writer, retry_policy=retry)

    # Edges
    builder.add_edge(START, "planner")
    builder.add_conditional_edges("planner", _after_planner, ["researcher", END])
    builder.add_edge("researcher", "critic")
    builder.add_conditional_edges(
        "critic", _should_continue_research, ["cycle_approval", "report_approval"]
    )
    builder.add_edge("writer", END)

    return builder.compile(checkpointer=checkpointer)
