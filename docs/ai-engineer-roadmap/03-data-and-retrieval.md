# Data & Retrieval

The data layer that powers RAG and intelligent search in AI applications.

## Vector Databases

Specialized databases that store and search high-dimensional vectors (embeddings). When you convert text to an embedding, you need somewhere to store it and search by similarity.

| Database | Type | Best for |
|----------|------|----------|
| **Pinecone** | Managed cloud | Production, zero ops, scales automatically |
| **Chroma** | Embedded/local | Prototyping, local dev, simple setup |
| **Qdrant** | Self-hosted/cloud | High performance, filtering, Rust-based |
| **Weaviate** | Self-hosted/cloud | Hybrid search, GraphQL API |
| **pgvector** | PostgreSQL extension | Already using Postgres, don't want another DB |
| **FAISS** | In-memory library | Benchmarking, research, no persistence needed |

**Choosing a vector database:**
- Just prototyping? → Chroma (zero setup)
- Already have Postgres/Supabase? → pgvector
- Production SaaS? → Pinecone (managed) or Qdrant (performance)
- Need hybrid search (vector + keyword)? → Weaviate

**Key operations:**
```python
# Store
collection.add(ids=["doc1"], embeddings=[vector], documents=["text"])

# Search (find similar)
results = collection.query(query_embeddings=[query_vector], n_results=5)

# Filter + search
results = collection.query(
    query_embeddings=[query_vector],
    where={"category": "science"},
    n_results=5
)
```

## Embedding Models

Models that convert text into numerical vectors. Similar texts produce similar vectors.

| Model | Dimensions | Provider | Notes |
|-------|-----------|----------|-------|
| `text-embedding-3-small` | 1536 | OpenAI | Cheap, good quality |
| `text-embedding-3-large` | 3072 | OpenAI | Best quality, 2x cost |
| `embed-english-v3.0` | 1024 | Cohere | Good for English, has multilingual variant |
| `all-MiniLM-L6-v2` | 384 | Open source | Free, runs locally, good enough for prototypes |
| `nomic-embed-text` | 768 | Open source | Good quality, runs on Ollama |

**Key concepts:**

### Cosine similarity
How similar two vectors are. Range: -1 (opposite) to 1 (identical). Most vector DBs use this by default.

### Dimensionality
Higher dimensions = more information captured, but more storage and slower search. 1536 is the sweet spot for most use cases.

### Embedding the same model
Always use the same embedding model for storing AND searching. Mixing models produces garbage results because their vector spaces are different.

## Document Processing

Getting data from various formats into a form the AI can use.

### PDF
The hardest format. PDFs are visual documents, not structured text.
- **Simple PDFs** — `PyPDF2`, `pdfplumber` extract text directly
- **Scanned PDFs** — Need OCR (`Tesseract`, `AWS Textract`, `Google Document AI`)
- **Complex layouts** — Tables, multi-column → `unstructured.io`, `LlamaParse`

### HTML
Web pages need cleaning before use:
- Strip navigation, ads, footers
- Extract main content (`BeautifulSoup`, `trafilatura`, `readability`)
- Handle JavaScript-rendered pages (`Playwright`, like in your researcher)

### Markdown
Easiest format. Already structured with headers, lists, code blocks.
- Split by headers for natural chunking
- Preserve code blocks as atomic units

### Tables
Particularly challenging for LLMs:
- Convert to markdown tables or CSV
- Or describe each row in natural language
- Some models handle tables better than others (Gemini is strong here)

## Chunking Strategies

How you split documents into smaller pieces for embedding. This is one of the most impactful decisions in a RAG system.

### Recursive character splitting
The default. Splits by paragraphs, then sentences, then characters, keeping chunks under a size limit.
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,     # max characters per chunk
    chunk_overlap=200,   # overlap between chunks for context continuity
)
chunks = splitter.split_documents(docs)
```

### Semantic chunking
Groups sentences that are semantically related. Better quality but slower.
```python
from langchain_experimental.text_splitter import SemanticChunker

splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
```

### By structure
Split by document structure (headers, sections). Best for well-structured docs.
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
splitter = MarkdownHeaderTextSplitter(headers)
```

### Parent-child
Store small chunks for retrieval but return the larger parent chunk for context. Gives you precision in search + completeness in the answer.

**Chunking guidelines:**
- **Too small** (100 tokens) — loses context, retrieves noise
- **Too large** (2000+ tokens) — dilutes relevance, wastes context window
- **Sweet spot** — 500-1000 tokens with 100-200 token overlap
- **Always test** — the "right" size depends on your documents and queries

## Search

Finding the right information from your stored data.

### Semantic search
Search by meaning using embeddings. "How do airplanes fly?" matches "principles of aerodynamic lift" even though they share no keywords.

**Pros:** Understands meaning, handles synonyms
**Cons:** Can miss exact keyword matches, computationally expensive

### Keyword search (BM25)
Traditional text search. Looks for exact word matches with TF-IDF scoring.

**Pros:** Fast, precise for exact terms, no embedding needed
**Cons:** Misses synonyms, doesn't understand meaning

### Hybrid search
Combines semantic + keyword search. The best of both worlds.
```
Score = α × semantic_score + (1-α) × keyword_score
```

Most production RAG systems use hybrid search. Weaviate and Qdrant support it natively.

### Reranking
A second pass that re-scores retrieved results for relevance. Dramatically improves quality.

```python
# Retrieve 20 candidates with cheap search
candidates = vector_store.similarity_search(query, k=20)

# Rerank to find the best 5
reranked = reranker.rerank(query, candidates, top_n=5)
```

**Reranking models:**
- **Cohere Rerank** — managed API, easy to use
- **ColBERT** — open source, very fast
- **Cross-encoder models** — highest quality, slower

**The full retrieval pipeline:**
```
Query → Hybrid search (20 results) → Rerank (top 5) → Stuff into prompt → LLM
```
