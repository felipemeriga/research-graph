# Multi-Agent & Orchestration

Building systems where multiple AI agents collaborate to solve complex problems.

## Multi-Agent Architectures

When a single agent can't handle the full task, you break it into specialized agents.

### Supervisor pattern
One "boss" agent delegates tasks to specialized workers.

```
User → Supervisor → Research Agent
                  → Code Agent
                  → Writing Agent
                  → Supervisor (aggregates results) → User
```

The supervisor decides which agent to call based on the task. Each worker has its own tools and prompts optimized for its specialty.

**When to use:** Tasks that require different expertise (research + code + writing)

### Hierarchical pattern
Multiple layers of supervisors. A top-level supervisor delegates to mid-level supervisors, who delegate to workers.

```
CEO Agent → Research Lead → Web Searcher
                          → Document Analyst
           → Writing Lead → Draft Writer
                          → Editor
```

**When to use:** Very complex workflows with clear organizational structure

### Debate / adversarial pattern
Two agents argue opposing sides. A judge evaluates.

```
Agent A (Pro) ←→ Agent B (Con)
       ↓              ↓
       Judge Agent (decides winner)
```

**When to use:** Decision-making, exploring tradeoffs, reducing bias

### Consensus pattern
Multiple agents independently solve the same problem. Results are compared and merged.

```
Agent 1 → Result 1 ─┐
Agent 2 → Result 2 ──┼→ Merge Agent → Final Result
Agent 3 → Result 3 ─┘
```

**When to use:** High-stakes tasks where you want multiple perspectives (code review, medical diagnosis)

### Your research agent as a multi-agent system
Your project already uses a simple version:
```
Planner Agent → Researcher Agent → Critic Agent → Writer Agent
```
Each is a separate subgraph with its own logic. The parent orchestrator controls the flow.

## Workflow Orchestration

Managing the execution flow of complex AI workflows.

### State machines
Your LangGraph graph IS a state machine:
- **States** — the values in `ResearchState`
- **Transitions** — edges between nodes
- **Conditions** — conditional edges that route based on state

### DAGs (Directed Acyclic Graphs)
Workflows without loops. Good for pipelines where each step happens once:
```
Extract → Transform → Load → Validate → Notify
```

### Cyclic graphs
Workflows with loops (like your research agent):
```
Research → Critique → (not good enough) → Research → Critique → (approved) → Write
```

LangGraph supports both DAGs and cycles.

### Human-in-the-loop
Three patterns for involving humans:

1. **Approval gates** — Pause before critical actions
   ```python
   decision = interrupt({"action": "Send email to 1000 users?"})
   ```

2. **Validation loops** — Ask for input, validate, re-ask if invalid
   ```python
   while True:
       answer = interrupt("What's your budget?")
       if is_valid_number(answer):
           break
   ```

3. **Editing** — Show a draft, let the human modify
   ```python
   decision = interrupt({"draft": report, "action": "Edit or approve?"})
   edited = decision.get("edited_text", report)
   ```

### Error recovery in workflows
How to handle failures without losing progress:

| Strategy | Implementation | When to use |
|----------|---------------|-------------|
| Retry | `RetryPolicy(max_attempts=3)` | Transient errors (network, rate limits) |
| Fallback | Try model A, fall back to model B | API outages |
| Checkpoint + resume | Checkpointer saves state | Long-running workflows |
| Human escalation | `interrupt("I'm stuck, help?")` | Ambiguous situations |

## MCP (Model Context Protocol)

A standard protocol for connecting LLMs to external tools and data sources. Think of it as "USB for AI" — a universal connector.

### How MCP works
```
LLM ←→ MCP Client ←→ MCP Server ←→ External System
                                     (database, API, filesystem)
```

### Key concepts

**MCP Server** — Exposes tools and resources that an LLM can use. Example: a server that exposes a `search_database` tool.

**MCP Client** — Connects to an MCP server and calls its tools. Your `mcp_client.py` is an MCP client.

**Transport** — How client and server communicate:
- **stdio** — Standard input/output (local processes)
- **SSE** — Server-Sent Events over HTTP (remote servers)

### Why MCP matters
Before MCP, every tool integration was custom. With MCP:
- Build a tool server once, use it from any MCP-compatible client
- Claude Desktop, Cursor, your own agents — all can use the same server
- Growing ecosystem of pre-built servers (GitHub, Slack, databases)

### Building an MCP server
```python
from mcp.server import Server
from mcp.types import Tool

server = Server("my-tools")

@server.tool()
async def search_docs(query: str) -> str:
    """Search internal documentation."""
    results = my_search_function(query)
    return format_results(results)
```

## Task Decomposition

Breaking complex tasks into smaller, manageable subtasks.

### Why decompose
LLMs perform better on focused, specific tasks than on broad, complex ones. "Research quantum computing and write a report" works worse than:
1. "Generate 5 specific research questions about quantum computing"
2. "Search the web for each question"
3. "Evaluate if the findings are comprehensive"
4. "Write a report based on the findings"

### Decomposition strategies

**Sequential** — Each step depends on the previous:
```
Plan → Research → Evaluate → Write
```

**Parallel** — Independent tasks run simultaneously:
```
Search Tavily ─┐
Scrape pages  ──┼→ Merge results
Query MCP     ─┘
```

**Hierarchical** — Break into sub-problems recursively:
```
"Build a web app" →
  "Design the API" →
    "Define endpoints"
    "Choose auth strategy"
  "Build the frontend" →
    "Create components"
    "Add routing"
```

### LangGraph's Send API for parallel decomposition
```python
def orchestrator(state):
    # Fan out tasks to parallel workers
    return [Send("worker", {"task": task}) for task in state["tasks"]]
```

This is the map-reduce pattern: one node spawns multiple parallel workers, results are collected via a reducer.
