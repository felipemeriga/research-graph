from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from research_graph.state import ResearchState

CRITIC_PROMPT = """\
You are a rigorous research critic. Your job is to find gaps, not to approve.

Topic: {topic}
Sub-queries investigated: {sub_queries}

Findings:
{findings}

Evaluate the findings using these criteria:
1. **Coverage** — Are there major angles of the topic that were NOT investigated?
2. **Depth** — Are findings superficial summaries or do they contain specific data, \
numbers, examples, or expert opinions?
3. **Recency** — Is the information current? Flag anything that seems outdated.
4. **Contradictions** — Do any findings contradict each other? If so, note which ones.
5. **Source diversity** — Are findings from varied sources, or mostly from one site?

Only approve if the findings would be sufficient to write a thorough, well-sourced report.
When not approving, suggest 2-3 additional search queries that target the specific gaps \
you identified (phrased as web searches, not essay questions).

Return ONLY a JSON object with:
- "approved": true/false
- "criticism": your evaluation covering the criteria above (2-4 sentences)
- "additional_queries": list of new web search queries to fill gaps (empty if approved)

JSON response:"""


def _evaluate_findings(state: ResearchState, llm: BaseChatModel) -> dict:
    findings_text = "\n\n".join(
        f"[{f['tool']}] {f['query']}: {f['content'][:800]}" for f in state["research_findings"]
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
