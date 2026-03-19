from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from research_graph.state import ResearchState

CRITIC_PROMPT = """\
You are a research critic. Evaluate the research findings against the original topic.

Topic: {topic}
Sub-queries investigated: {sub_queries}

Findings:
{findings}

Evaluate whether the findings comprehensively answer the research topic.
Return ONLY a JSON object with:
- "approved": true/false
- "criticism": brief evaluation of what's good and what's missing
- "additional_queries": list of new sub-queries to investigate (empty if approved)

JSON response:"""


def _evaluate_findings(state: ResearchState, llm: BaseChatModel) -> dict:
    findings_text = "\n\n".join(
        f"[{f['tool']}] {f['query']}: {f['content'][:500]}" for f in state["research_findings"]
    )
    prompt = CRITIC_PROMPT.format(
        topic=state["topic"],
        sub_queries=", ".join(state["sub_queries"]),
        findings=findings_text,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw)

    update: dict = {
        "criticism": result["criticism"],
        "critic_approved": result["approved"],
        "status": "critiquing",
    }
    additional = result.get("additional_queries", [])
    if additional:
        update["sub_queries"] = state["sub_queries"] + additional

    return update


def create_critic_graph(llm: BaseChatModel) -> StateGraph:
    def evaluate(state: ResearchState) -> dict:
        return _evaluate_findings(state, llm)

    builder = StateGraph(ResearchState)
    builder.add_node("evaluate", evaluate)
    builder.add_edge(START, "evaluate")
    builder.add_edge("evaluate", END)
    return builder
