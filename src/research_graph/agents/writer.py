from __future__ import annotations

import re
import uuid
from datetime import date
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from research_graph.state import ResearchState

WRITER_PROMPT = """\
You are a research report writer producing content for a technical audience.

Topic: {topic}

Research Findings:
{findings}

Sources:
{sources}

Write a well-structured markdown report following this structure:

1. **Title** — Clear, specific title (not just the topic name)
2. **TL;DR** — 2-3 sentence summary of the key takeaways
3. **Body sections** — Organize by theme, not by source. Each section should:
   - Have a descriptive heading
   - Synthesize information from multiple findings (don't just list them)
   - Include specific data, numbers, or examples where available
   - Cite sources inline as markdown links: [source name](url)
   - Note any contradictions or debates between sources
4. **Key Takeaways** — 3-5 bullet points with the most important insights
5. **References** — All sources as a numbered list with URLs

Writing guidelines:
- Be specific: prefer "reduced latency by 40%" over "significantly improved performance"
- When sources disagree, present both sides and note the disagreement
- Skip sections where you have no substantial findings — don't pad with filler
- Write for someone who is knowledgeable but unfamiliar with this specific topic

Report:"""


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:50].rstrip("-")


def _write_report(state: ResearchState, llm: BaseChatModel, output_dir: str) -> dict:
    findings_text = "\n\n".join(
        f"### {f['query']}\nSource: {f['source']} ({f['tool']})\n{f['content'][:2000]}"
        for f in state["research_findings"]
    )
    sources_text = "\n".join(f"- {s}" for s in set(state["sources"]))
    prompt = WRITER_PROMPT.format(
        topic=state["topic"], findings=findings_text, sources=sources_text
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    report = response.content.strip()

    # Save to file
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    short_id = uuid.uuid4().hex[:6]
    filename = f"{date.today().isoformat()}-{_slugify(state['topic'])}-{short_id}.md"
    report_path = out_path / filename
    report_path.write_text(report)

    return {"final_report": report, "status": "complete"}


def create_writer_graph(llm: BaseChatModel, output_dir: str = "./reports") -> StateGraph:
    def write(state: ResearchState) -> dict:
        return _write_report(state, llm, output_dir)

    builder = StateGraph(ResearchState)
    builder.add_node("write_report", write)
    builder.add_edge(START, "write_report")
    builder.add_edge("write_report", END)
    return builder
