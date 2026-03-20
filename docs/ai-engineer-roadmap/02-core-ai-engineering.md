# Core AI Engineering

The essential skills for building AI-powered applications.

## RAG (Retrieval-Augmented Generation)

The most common production AI pattern. Instead of relying solely on the LLM's training data, you retrieve relevant documents and include them in the prompt.

**Why RAG exists:**
- LLMs have a knowledge cutoff date
- LLMs hallucinate when they don't know something
- You need answers from YOUR data (internal docs, databases, codebases)

**The RAG pipeline:**
```
User query → Embed query → Search vector store → Retrieve top-K docs → Stuff into prompt → LLM generates answer
```

**Key components:**
1. **Document loading** — Ingest PDFs, web pages, markdown, databases
2. **Chunking** — Split documents into smaller pieces (512-1000 tokens each)
3. **Embedding** — Convert text chunks into numerical vectors
4. **Vector store** — Store and search embeddings by similarity
5. **Retrieval** — Find the most relevant chunks for a query
6. **Generation** — Send retrieved chunks + query to the LLM

**When to use RAG vs fine-tuning:**
- RAG: when you need factual answers from specific documents
- Fine-tuning: when you need the model to adopt a specific style or behavior

## Tool Use / Function Calling

Letting the LLM decide which tools to call based on the user's request.

**How it works:**
1. You define available tools with names, descriptions, and parameter schemas
2. The LLM reads the user's request and decides which tool(s) to call
3. You execute the tool and return the result
4. The LLM incorporates the result into its response

**Example:**
```python
tools = [
    {
        "name": "search_web",
        "description": "Search the web for current information",
        "parameters": {"query": {"type": "string"}}
    },
    {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {"city": {"type": "string"}}
    }
]
```

User asks "What's the weather in Tokyo?" → LLM calls `get_weather(city="Tokyo")` → You execute it → Return result → LLM says "It's 22°C and sunny in Tokyo."

**Key patterns:**
- **Single tool call** — LLM calls one tool per turn
- **Parallel tool calls** — LLM calls multiple tools simultaneously
- **Sequential tool calls** — LLM uses one tool's output to decide the next
- **Tool error handling** — Return errors as tool results so the LLM can retry or adapt

## Agent Frameworks

Libraries that simplify building AI agents. Each has different tradeoffs.

| Framework | Strength | When to use |
|-----------|----------|-------------|
| **LangChain** | Broad ecosystem, tools, RAG | Single-purpose agents, quick prototypes |
| **LangGraph** | Fine-grained control, state, loops | Complex workflows, HITL, custom routing |
| **CrewAI** | Role-based multi-agent | Team simulation, collaborative tasks |
| **AutoGen** | Conversational agents | Multi-agent conversations |
| **Semantic Kernel** | Microsoft ecosystem | .NET/C# projects, Azure integration |

**Choosing a framework:**
- Need full control over the flow? → LangGraph
- Just need an agent that uses tools? → LangChain `create_agent`
- Need multiple agents with roles? → CrewAI
- Working in .NET? → Semantic Kernel

## Memory Systems

How agents remember things across interactions.

### Short-term memory (conversation)
The chat history within a single session. Stored in the checkpointer, scoped to a `thread_id`.

```python
# LangGraph: automatic with checkpointer
graph = builder.compile(checkpointer=PostgresSaver(...))
config = {"configurable": {"thread_id": "session-1"}}
```

### Long-term memory (cross-session)
Facts, preferences, and knowledge that persist across conversations. Stored in a `Store`.

```python
# LangGraph Store
store.put(("user-123", "preferences"), "style", {"preference": "concise answers"})
```

### Episodic memory
Remembering specific past interactions. "Last time you asked about quantum computing, here's what we found." Implemented by storing summaries of past sessions and retrieving relevant ones.

**Memory architecture patterns:**
- **Buffer** — Keep last N messages (simple, limited)
- **Summary** — Summarize old messages to save context space
- **Vector** — Embed memories and retrieve by relevance
- **Hybrid** — Combine buffer (recent) + vector (relevant past)

## Evaluation

How do you know if your agent is good? Without evaluation, you're guessing.

**Types of evaluation:**

### Unit evaluation
Test individual components:
- Does the planner generate relevant queries?
- Does the critic correctly identify gaps?
- Does the retriever find the right documents?

### End-to-end evaluation
Test the full pipeline:
- Given topic X, is the final report comprehensive?
- Does it cite real sources?
- Is it factually accurate?

### Automated scoring
Use an LLM to judge output quality:
```python
# "LLM-as-judge" pattern
score = judge_llm.invoke(
    f"Rate this research report 1-10 for completeness: {report}"
)
```

### Human evaluation
The gold standard. Have humans review agent outputs and rate them.

**Tools:**
- **LangSmith** — tracing, datasets, evaluators, A/B comparisons
- **RAGAS** — automated RAG evaluation (faithfulness, relevance, recall)
- **Custom evals** — pytest-based tests with assertions on output quality

## Structured Output

Getting LLMs to return data in a specific format instead of free text.

**Approaches:**

### JSON mode
```python
response = llm.invoke(prompt, response_format={"type": "json_object"})
```

### Pydantic schemas (LangChain)
```python
from pydantic import BaseModel

class CriticEvaluation(BaseModel):
    approved: bool
    criticism: str
    additional_queries: list[str]

structured_llm = llm.with_structured_output(CriticEvaluation)
result = structured_llm.invoke(prompt)
# result.approved, result.criticism — typed Python object
```

### Why it matters
- Eliminates parsing errors ("the LLM returned markdown instead of JSON")
- Type safety in your application code
- Easier to test and validate outputs
