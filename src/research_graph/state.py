from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class ResearchFinding(TypedDict):
    query: str
    source: str
    content: str
    tool: str


class ResearchState(TypedDict):
    topic: str
    sub_queries: list[str]
    current_query_index: int
    research_findings: Annotated[list[ResearchFinding], operator.add]
    criticism: str
    critic_approved: bool
    research_cycle_count: int
    final_report: str
    sources: Annotated[list[str], operator.add]
    status: Literal["planning", "researching", "critiquing", "writing", "complete", "error"]
