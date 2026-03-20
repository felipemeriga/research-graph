# Adjacent Skills

Skills that complement AI engineering and make you more effective.

## Frontend for AI

Most AI applications need a user interface. The most common patterns:

### Chat UI
The default interface for conversational AI. Users send messages, the AI responds.

**Key features:**
- **Streaming responses** — Show tokens as they arrive (SSE or WebSockets)
- **Message history** — Display the conversation thread
- **Tool call visualization** — Show what tools the agent is using
- **Loading states** — Spinners, typing indicators
- **Markdown rendering** — LLMs output markdown, your UI should render it

**Tech stack:**
- **React + Next.js** — Most common for web chat UIs
- **Vercel AI SDK** — Handles streaming, message state, tool calls out of the box
- **Tailwind CSS** — Fast styling for chat interfaces

### Streaming in the frontend
The server sends tokens as Server-Sent Events (SSE):

```javascript
// Frontend
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ message: userInput }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = decoder.decode(value);
  appendToChat(text);
}
```

### Dashboard UI
For monitoring and managing AI workflows:
- Agent execution traces
- Cost tracking per session
- Success/failure rates
- Queue status

### CLI (what you built)
Sometimes the best UI is no UI:
- **Rich** — Terminal formatting, tables, progress bars
- **Click** — Command parsing and help text
- **Streaming in terminal** — `print(token, end="", flush=True)`

Your research agent uses this approach — it's actually great for power users.

## Data Engineering

AI applications are only as good as their data.

### ETL for RAG
Extract-Transform-Load pipelines that feed your vector store:

```
Data Sources → Extract → Clean → Chunk → Embed → Vector Store
(PDFs, web,    (parse)   (remove  (split)  (model)  (store)
 APIs, DBs)              noise)
```

**Key considerations:**
- **Freshness** — How often do you re-index? Real-time, hourly, daily?
- **Deduplication** — Same content from multiple sources
- **Quality** — Bad data = bad retrieval = bad answers
- **Scale** — 1K docs vs 1M docs require different approaches

### Data pipelines

| Tool | Use case |
|------|----------|
| **Apache Airflow** | Scheduled batch ETL |
| **Prefect** | Modern Python-native pipelines |
| **dbt** | SQL transformations |
| **LlamaIndex** | AI-specific data ingestion |

### Data quality for AI
Problems that are unique to AI data:
- **Contradictory sources** — Two documents say different things
- **Stale information** — Outdated docs still in the vector store
- **Incomplete content** — Chunks that lost context from splitting
- **Encoding issues** — Garbled text from PDF extraction

**Solution:** Build quality checks into your ETL:
```python
def validate_chunk(chunk):
    if len(chunk) < 50:
        return False  # Too short, probably noise
    if chunk.count("�") > 5:
        return False  # Encoding issues
    return True
```

## Traditional ML Basics

Not everything needs an LLM. Sometimes classical ML is faster, cheaper, and better.

### When to use ML vs LLM

| Task | ML | LLM |
|------|-----|-----|
| Spam classification | ✅ Fast, cheap, accurate | Overkill |
| Sentiment analysis | ✅ Well-solved problem | Works but expensive |
| Anomaly detection | ✅ Statistical methods | Not great |
| Recommendation | ✅ Collaborative filtering | Can supplement |
| Text generation | ❌ | ✅ This is what LLMs do |
| Complex reasoning | ❌ | ✅ Multi-step logic |
| Conversation | ❌ | ✅ Natural dialogue |
| Code generation | ❌ | ✅ Understands context |

### Key ML concepts to know
You don't need to be an ML expert, but understanding the basics helps you make better architecture decisions:

- **Classification** — Categorizing inputs (spam/not spam, sentiment, intent)
- **Clustering** — Grouping similar items without labels (topic discovery)
- **Regression** — Predicting numbers (cost estimation, scoring)
- **Embeddings** — The bridge between ML and LLMs. Used in RAG, similarity search, clustering

### Practical ML for AI engineers
- **scikit-learn** — Classification, clustering, basic ML
- **XGBoost** — When you need accurate predictions on tabular data
- **sentence-transformers** — Open-source embedding models
- **HDBSCAN** — Clustering (useful for grouping similar queries or documents)

## Domain Knowledge

The most underrated skill. Understanding the business problem matters more than the technology.

### Why domain knowledge matters
Two engineers build a legal document analyzer:
- Engineer A knows AI but not law: builds a generic RAG that misses legal nuances
- Engineer B knows AI AND law: structures the pipeline around legal concepts (precedent, jurisdiction, statute types)

Engineer B's system is dramatically better, not because of better AI code, but because of better problem understanding.

### How to build domain knowledge
1. **Talk to users** — What problem are they actually solving? (Not what they say, what they do)
2. **Use the existing process** — Before automating, understand the manual workflow
3. **Learn the vocabulary** — Every domain has jargon. Use it correctly in your prompts
4. **Understand edge cases** — Where does the current process break? Those are your hardest AI challenges
5. **Read domain literature** — Industry reports, regulations, best practices

### Domain knowledge in prompt engineering
Generic prompt:
```
Summarize this document.
```

Domain-aware prompt:
```
You are a legal analyst reviewing a contract. Identify:
1. Key obligations for each party
2. Termination clauses and conditions
3. Liability limitations and indemnification terms
4. Non-standard clauses that deviate from typical contracts in this jurisdiction
```

The second prompt produces dramatically better results because it knows what matters in the domain.

### High-value AI domains
Areas where AI solutions engineers are in high demand:
- **Legal** — Contract analysis, case research, compliance
- **Healthcare** — Clinical documentation, medical coding, patient triage
- **Finance** — Risk analysis, fraud detection, report generation
- **Customer support** — Ticket routing, response drafting, knowledge base
- **Software engineering** — Code review, documentation, testing
- **Education** — Personalized tutoring, content generation, assessment
