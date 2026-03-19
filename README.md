# Research Graph

A deep research agent powered by [LangGraph](https://github.com/langchain-ai/langgraph). Give it a topic, and it will plan research queries, search the web, evaluate findings, and generate a structured markdown report.

![Graph Diagram](graph_diagram.png)

## How It Works

The agent follows a multi-step workflow with human-in-the-loop checkpoints:

1. **Planner** — An LLM breaks your topic into focused sub-queries
2. **You approve the plan** (or edit the queries)
3. **Researcher** — Searches the web via Tavily and scrapes pages with Playwright
4. **Critic** — An LLM evaluates whether the findings are comprehensive
5. **You decide** whether to continue researching or move on
6. **Writer** — Generates a structured markdown report with sources
7. **You approve** the final report generation

The critic creates a feedback loop: if findings have gaps, it suggests new queries and the researcher runs again. This cycle repeats until the critic approves or you decide to stop.

## LangGraph Concepts Used

| Concept | Where |
|---------|-------|
| StateGraph + Reducers | `state.py` — shared state with `operator.add` for accumulating lists |
| Subgraph composition | `graph.py` — each agent is its own StateGraph, composed into a parent |
| Conditional edges | `graph.py` — dynamic routing based on critic approval |
| Command (update + goto) | `planner.py`, `graph.py` — combine state updates with routing |
| interrupt() / Command(resume) | `planner.py`, `graph.py` — pause for human input |
| Checkpointer (PostgresSaver) | `cli.py` — persist state to Supabase Postgres |
| RetryPolicy | `graph.py` — automatic retry with backoff on failures |
| Streaming | `cli.py` — real-time node progress output |

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- A Supabase project (free tier works)
- API keys for OpenAI (or Anthropic/Google) and Tavily

### Install

```bash
git clone https://github.com/felipemeriga/research-graph.git
cd research-graph
uv sync
```

### Configure

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
SUPABASE_DB_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres
```

The Supabase connection string is found in your Supabase dashboard under **Project Settings > Database > Connection string > URI** (use the pooler connection).

Edit `config.yaml` to customize the LLM and research settings:

```yaml
llm:
  provider: "openai"       # openai, anthropic, or google
  model: "gpt-4o-mini"     # any model from the provider
  temperature: 0.3

research:
  max_cycles: 5            # max research-critic loops
  max_sources_per_query: 5

report:
  output_dir: "./reports"

mcp:
  server_url: ""           # optional MCP server, leave empty to skip
  transport: "stdio"
```

### Install Playwright (optional, for web scraping)

```bash
uv run playwright install chromium
```

## Usage

### Start a research session

```bash
uv run research-graph research "your topic here"
```

The agent will:
- Generate sub-queries and ask for your approval
- Search the web for each query
- Show critic feedback and ask if you want to continue
- Generate a markdown report saved to `./reports/`

### Resume a previous session

```bash
uv run research-graph resume --thread-id <thread-id>
```

Sessions are persisted in Supabase, so you can resume hours or days later.

### List past sessions

```bash
uv run research-graph sessions
```

## Project Structure

```
src/research_graph/
├── state.py              # Shared state schema (ResearchState)
├── graph.py              # Parent orchestrator — wires all agents together
├── cli.py                # CLI interface with interrupt handling
├── config.py             # YAML + .env config loading
├── llm.py                # Provider-agnostic LLM factory
├── display.py            # Rich terminal output
├── agents/
│   ├── planner.py        # Breaks topic into sub-queries
│   ├── researcher.py     # Searches web via Tavily + Playwright
│   ├── critic.py         # Evaluates research quality
│   └── writer.py         # Generates markdown report
└── tools/
    ├── tavily_search.py  # Tavily web search wrapper
    ├── scraper.py        # Playwright page scraper
    └── mcp_client.py     # MCP server client (optional)
```

## Development

```bash
# Run tests
uv run --extra dev pytest

# Lint and format
uv run --extra dev ruff check --fix && uv run --extra dev ruff format
```

## License

MIT
