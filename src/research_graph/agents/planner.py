from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from research_graph.state import ResearchState

PLANNER_PROMPT = """You are a research planner. Given a research topic, break it down into 3-6
specific sub-queries that would comprehensively cover the topic.

Return ONLY a JSON array of strings, no other text.

Topic: {topic}"""


def _generate_queries(state: ResearchState, llm: BaseChatModel) -> dict:
    prompt = PLANNER_PROMPT.format(topic=state["topic"])
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    # Parse JSON array from response
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    queries = json.loads(raw)
    return {"sub_queries": queries, "status": "planning"}


def _approve_plan(state: ResearchState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {"sub_queries": state["sub_queries"], "action": "Approve this research plan? [y/n/edit]"}
    )
    if not decision.get("approved", False):
        return Command(update={"status": "error"}, goto=END)
    edited_queries = decision.get("sub_queries", state["sub_queries"])
    return Command(
        update={"sub_queries": edited_queries, "status": "researching"},
        goto=END,
    )


def create_planner_graph(llm: BaseChatModel) -> StateGraph:
    def generate(state: ResearchState) -> dict:
        return _generate_queries(state, llm)

    builder = StateGraph(ResearchState)
    builder.add_node("generate_queries", generate)
    builder.add_node("approve_plan", _approve_plan)
    builder.add_edge(START, "generate_queries")
    builder.add_edge("generate_queries", "approve_plan")
    return builder
