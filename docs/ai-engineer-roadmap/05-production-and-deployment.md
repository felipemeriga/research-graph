# Production & Deployment

Taking AI applications from prototype to production.

## LLM Ops (Observability)

You can't improve what you can't measure. LLM ops is about understanding what your AI is doing in production.

### Tracing
Record every LLM call, tool use, and decision in your agent's execution. Like logging, but structured for AI workflows.

```
Research session trace:
├─ planner (GPT-4o-mini, 340 tokens, 1.2s, $0.0003)
│  ├─ generate_queries: 6 queries generated
│  └─ approve_plan: user approved
├─ researcher (3 Tavily calls, 2 scrapes, 4.5s)
├─ critic (GPT-4o-mini, 890 tokens, 2.1s, $0.0008)
│  └─ result: not approved, 2 additional queries
├─ researcher (2 Tavily calls, 1 scrape, 3.2s)
├─ critic (approved)
└─ writer (GPT-4o-mini, 2400 tokens, 3.8s, $0.002)
Total: 14.8s, $0.003
```

### Tools

**LangSmith** — First-party tracing for LangChain/LangGraph. Set two env vars and it works:
```bash
LANGSMITH_API_KEY=ls-...
LANGSMITH_PROJECT=research-graph
```

**Langfuse** — Open-source alternative. Self-host or use cloud.

**Helicone** — Proxy-based. Route API calls through Helicone to get automatic logging.

### What to monitor in production
- **Latency** — How long each step takes
- **Cost** — Token usage per session
- **Error rate** — Failed LLM calls, tool errors
- **Quality** — User feedback, automated eval scores
- **Token efficiency** — Are you wasting tokens on redundant context?

## Guardrails

Preventing your AI from doing harmful or unexpected things.

### Input validation
Check user input before it reaches the LLM:
- **Prompt injection detection** — "Ignore your instructions and..."
- **Topic filtering** — Block off-topic requests
- **Length limits** — Prevent context window overflow
- **PII detection** — Redact personal information before sending to LLM

### Output validation
Check LLM output before returning to the user:
- **Format validation** — Did it return valid JSON?
- **Content filtering** — Block harmful/inappropriate content
- **Factual grounding** — Does the output match the retrieved sources?
- **Hallucination detection** — Flag claims not supported by provided context

### Libraries
- **Guardrails AI** — Define validators in RAIL XML, auto-retry on failure
- **NeMo Guardrails** — NVIDIA's toolkit for dialogue safety
- **Custom validators** — Often simpler to write your own for specific use cases

### Example guardrail in LangGraph
```python
def validate_output(state):
    report = state["final_report"]
    if len(report) < 100:
        return {"status": "error", "criticism": "Report too short"}
    if not any(source in report for source in state["sources"]):
        return {"status": "error", "criticism": "No sources cited"}
    return {"status": "complete"}
```

## Cost Optimization

LLM APIs are metered. At scale, costs matter.

### Model routing
Use expensive models only when needed:
```python
if task_complexity == "simple":
    llm = ChatOpenAI(model="gpt-4o-mini")    # $0.15/1M input tokens
else:
    llm = ChatOpenAI(model="gpt-4o")          # $2.50/1M input tokens
```

### Caching
Don't call the LLM for the same prompt twice:
```python
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))
```

### Prompt compression
Remove unnecessary tokens from prompts:
- Summarize long documents before including
- Remove formatting that doesn't affect output
- Use shorter system prompts

### Batch processing
Some APIs offer cheaper rates for batch (non-real-time) processing. Good for evaluation runs and bulk processing.

## Latency Optimization

Making AI applications feel fast.

### Streaming
Don't wait for the full response — stream tokens as they're generated:
```python
for chunk in graph.stream(input, config, stream_mode="messages"):
    token, metadata = chunk
    print(token.content, end="", flush=True)
```

### Parallel tool calls
Run independent operations simultaneously:
```python
# Instead of sequential:
result_a = tool_a(query)  # 2s
result_b = tool_b(query)  # 2s
# Total: 4s

# Run in parallel:
result_a, result_b = await asyncio.gather(
    tool_a(query),
    tool_b(query),
)
# Total: 2s
```

### Speculative execution
Start the next step before the current one finishes, if you can predict the outcome.

### Right-size your model
Smaller models are faster:
- GPT-4o-mini: ~500ms for simple tasks
- GPT-4o: ~2-5s for the same tasks
- Use mini for classification/routing, full model for generation

## Fine-Tuning

Training a model on your specific data to improve performance for your use case.

### When to fine-tune
- The model needs to follow a very specific output format consistently
- You need domain-specific knowledge the base model lacks
- Prompt engineering has hit its limits
- You want to use a smaller (cheaper, faster) model but need better quality

### When NOT to fine-tune
- RAG can solve it (just give the model the right context)
- You haven't tried prompt engineering thoroughly
- Your training data is small (< 100 examples)
- The task changes frequently (fine-tuning is slow to update)

### Techniques

**Full fine-tuning** — Update all model weights. Expensive, needs lots of data and compute.

**LoRA (Low-Rank Adaptation)** — Only update a small set of adapter weights. 10-100x cheaper than full fine-tuning.

**QLoRA** — LoRA on a quantized model. Even cheaper. Can fine-tune a 70B model on a single GPU.

### Training data preparation
The most important part. Garbage in, garbage out.
- **Quality over quantity** — 100 excellent examples beat 10,000 mediocre ones
- **Format** — Input/output pairs matching your use case
- **Diversity** — Cover edge cases and variations
- **Validation set** — Hold out 10-20% to measure improvement

## Deployment

Getting your AI application running in production.

### Containerization
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync
COPY src/ src/
CMD ["uv", "run", "research-graph", "research"]
```

### Deployment options

| Option | Best for | Scaling |
|--------|----------|---------|
| **LangGraph Platform** | LangGraph apps | Managed, auto-scaling |
| **AWS Lambda / Cloud Functions** | Simple agents, APIs | Pay-per-invocation |
| **Docker + ECS/GKE** | Full control | Manual or auto-scaling |
| **LangServe** | Exposing chains as REST APIs | Moderate |
| **Modal** | GPU workloads, fine-tuning | Auto-scaling, pay-per-second |

### API design for AI applications
- **Streaming endpoints** — Use SSE or WebSockets for real-time token output
- **Async processing** — Long-running agents should return a job ID, not block
- **Idempotency** — Agent retries shouldn't create duplicate side effects
- **Timeouts** — Set reasonable limits (30s for simple, 5min for research agents)

## Scaling

Handling multiple users and high throughput.

### Queue-based architecture
Don't process agent requests synchronously in your web server:
```
API Server → Queue (Redis/SQS) → Worker Pool → Results Store
     ↑                                              │
     └──────────── Poll / WebSocket ────────────────┘
```

### Horizontal scaling
Run multiple worker instances. Each picks tasks from the queue independently. Checkpointer (Postgres) is the shared state.

### Rate limit management
- Pool API keys across multiple accounts
- Implement token bucket rate limiting
- Queue requests and process at the provider's rate
- Use fallback providers when primary is throttled
