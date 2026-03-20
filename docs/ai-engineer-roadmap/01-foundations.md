# Foundations

The baseline knowledge every AI solutions engineer needs before building anything.

## Python

Python is the default language for AI engineering. Not because it's the fastest, but because every AI library, framework, and API has Python as the primary SDK.

**What to know:**
- Data structures: dicts, lists, sets, comprehensions
- Async programming: `async/await`, `asyncio.run()`, event loops
- Type hints: `TypedDict`, `Annotated`, `Literal`, generics
- Package management: `pip`, `uv`, `poetry`, virtual environments
- Standard library: `operator`, `functools`, `dataclasses`, `pathlib`

**Why it matters for AI:**
- LangChain, LangGraph, OpenAI SDK, Anthropic SDK — all Python-first
- Most AI research papers release Python code
- Jupyter notebooks are the standard for prototyping
- Type hints become critical when defining state schemas (like `ResearchState` in LangGraph)

## LLM Fundamentals

Understanding how LLMs work under the hood helps you debug issues, optimize costs, and choose the right model.

**Key concepts:**

### Transformers
The architecture behind all modern LLMs (GPT, Claude, Gemini). The key innovation is the **attention mechanism** — the model can look at all previous tokens simultaneously instead of sequentially.

### Tokens
LLMs don't read words — they read tokens. A token is roughly 3-4 characters in English. "Hello world" is 2 tokens, but "unconventional" might be 3.

**Why tokens matter:**
- **Cost** — you pay per token (input + output)
- **Context window** — the max tokens the model can process (e.g., 128K for GPT-4o, 200K for Claude)
- **Speed** — more output tokens = longer response time

### Temperature
Controls randomness in the output:
- `temperature=0` — deterministic, always picks the most likely token
- `temperature=0.3` — slightly creative (good for research, analysis)
- `temperature=0.7-1.0` — more creative (good for brainstorming, writing)

### Top-p (Nucleus Sampling)
An alternative to temperature. Instead of scaling probabilities, it considers only the top tokens whose cumulative probability reaches `p`. `top_p=0.9` means "only consider tokens in the top 90% probability mass."

In practice, adjust temperature OR top-p, not both.

### Context Window
The maximum amount of text (in tokens) that the model can process in a single request. This includes both your input (prompt + history) and the model's output.

| Model | Context Window |
|-------|---------------|
| GPT-4o | 128K tokens |
| GPT-4o-mini | 128K tokens |
| Claude Sonnet/Opus | 200K tokens |
| Gemini 1.5 Pro | 2M tokens |

**Practical implications:**
- A 128K context ≈ a 300-page book
- Longer context = higher cost and latency
- Just because a model CAN process 128K tokens doesn't mean it performs well at that length (the "lost in the middle" problem)

## Prompt Engineering

The fastest, cheapest way to improve AI output quality. No code changes, no fine-tuning — just better instructions.

**Core techniques:**

### Zero-shot
Just ask directly. No examples.
```
Classify this email as spam or not spam: "You've won $1M!"
```

### Few-shot
Provide examples of the desired input/output pattern.
```
Classify emails:
Email: "Meeting at 3pm" → not spam
Email: "You've won $1M!" → spam
Email: "Invoice attached" → ?
```

### Chain-of-thought (CoT)
Ask the model to think step by step. Dramatically improves reasoning tasks.
```
Solve this step by step:
If a train travels 60mph for 2.5 hours, how far does it go?
```

### System prompts
Set the model's role and behavior upfront. Every production app uses these.
```
You are a research critic. Evaluate findings for completeness and accuracy.
Return JSON with "approved" (boolean) and "criticism" (string).
```

### Structured output
Tell the model exactly what format you want. Reduces parsing errors.
```
Return ONLY a JSON object with these fields:
- "approved": true/false
- "criticism": brief evaluation
- "additional_queries": list of strings
```

## API Integration

Knowing how to call LLM APIs efficiently, handle errors, and manage costs.

**Key topics:**

### Provider APIs
Each provider has an SDK:
- `openai` — OpenAI (GPT-4o, o3)
- `anthropic` — Anthropic (Claude)
- `google-generativeai` — Google (Gemini)

Or use LangChain's unified interface (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`) to switch providers without changing code.

### Rate limiting
Every API has limits (requests per minute, tokens per minute). Handle them with:
- Exponential backoff with retry
- Request queuing
- LangGraph's `RetryPolicy(max_attempts=3, initial_interval=1.0)`

### Error handling
Common failure modes:
- Rate limits (429) — retry with backoff
- Context too long (400) — truncate input or use a model with a larger window
- API down (500/503) — retry or failover to another provider
- Timeout — set reasonable timeouts, use streaming for long responses

### Cost management
LLM calls are metered:
- Track token usage per request
- Use cheaper models for simple tasks (GPT-4o-mini for classification, GPT-4o for reasoning)
- Cache repeated queries
- Compress prompts (remove redundant context)

**Example cost comparison (per 1M tokens):**

| Model | Input | Output |
|-------|-------|--------|
| GPT-4o-mini | $0.15 | $0.60 |
| GPT-4o | $2.50 | $10.00 |
| Claude Sonnet | $3.00 | $15.00 |
| Claude Opus | $15.00 | $75.00 |

Choosing the right model for each task can reduce costs 10-100x.
