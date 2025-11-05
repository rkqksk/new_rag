# RAG Pipeline - Architecture Reference

Comprehensive reference for RAG (Retrieval-Augmented Generation) system architecture and best practices.

---

## RAG System Architecture

### Components Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Document Processing                                     │
│     ├── PDF/DOCX/XLSX Parsing                             │
│     ├── OCR (Optical Character Recognition)               │
│     ├── Domain Expert Enhancement                         │
│     └── Chunking & Metadata Extraction                    │
│                                                             │
│  2. Embedding Generation                                    │
│     ├── Text Embedding Models                             │
│     ├── Multimodal Embeddings (text + image)              │
│     └── Batch Processing                                   │
│                                                             │
│  3. Vector Storage                                          │
│     ├── Qdrant Vector Database                            │
│     ├── PostgreSQL + pgvector                             │
│     └── Index Optimization                                 │
│                                                             │
│  4. Retrieval System                                        │
│     ├── Vector Search (Semantic)                          │
│     ├── Keyword Search (BM25)                             │
│     ├── Hybrid Search (Vector + Keyword)                 │
│     └── Cross-Encoder Reranking                           │
│                                                             │
│  5. Answer Generation                                       │
│     ├── Context Assembly                                   │
│     ├── Prompt Engineering                                 │
│     ├── LLM Generation (OpenAI/Anthropic/Local)          │
│     └── Citation & Source Attribution                     │
│                                                             │
│  6. Monitoring & Evaluation                                 │
│     ├── Quality Metrics                                    │
│     ├── Performance Tracking                               │
│     └── User Feedback Loop                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Document Processing Pipeline

### 1. Document Parsing

**Supported Formats**:
- PDF (text, scanned images with OCR)
- DOCX (Microsoft Word)
- XLSX (Microsoft Excel)
- TXT (plain text)
- HTML/Markdown

**Parsing Libraries**:
- **Docling**: Enterprise-grade document understanding
- **PyMuPDF**: Fast PDF processing
- **python-docx**: DOCX parsing
- **openpyxl**: Excel handling
- **Tesseract OCR**: Optical character recognition

### 2. Text Chunking Strategies

#### Fixed-Size Chunking
```python
chunk_size = 512  # tokens
overlap = 50      # tokens
```
- **Pros**: Simple, predictable
- **Cons**: May split sentences/paragraphs awkwardly

#### Semantic Chunking
```python
# Chunk by natural boundaries
- Paragraphs
- Sections
- Sentences
```
- **Pros**: Preserves context, more meaningful chunks
- **Cons**: Variable chunk sizes

#### Sliding Window
```python
window_size = 512
stride = 256  # overlap
```
- **Pros**: Ensures no information loss at boundaries
- **Cons**: Redundancy, increased storage

**Recommended**: Semantic chunking with max size limit (512 tokens)

### 3. Domain Expert Enhancement

**Integration Points**:
```python
# Manufacturing documents
from plugins.manufacturing_expert import ManufacturingExpertPlugin

expert = ManufacturingExpertPlugin()
result = expert.process_document(document)

# Enhanced metadata:
- doc_type: "sop", "fmea", etc.
- terminology: ["Cpk", "OEE", "PPM"]
- quality_metrics: extracted values
- standards: ["ISO 9001", "FDA 21 CFR"]
```

**Benefits**:
- Better search relevance through domain-specific metadata
- Automatic extraction of key metrics and terminology
- Enhanced context for answer generation

---

## Embedding Models

### Text Embedding Models

#### OpenAI Embeddings
```python
model: "text-embedding-3-large"
dimensions: 3072
max_input: 8191 tokens
cost: $0.00013 / 1K tokens
```
- **Pros**: High quality, multilingual, production-ready
- **Cons**: API cost, latency

#### OpenAI Embedding (Small)
```python
model: "text-embedding-3-small"
dimensions: 1536
max_input: 8191 tokens
cost: $0.00002 / 1K tokens
```
- **Pros**: Fast, cost-effective
- **Cons**: Lower quality than large model

#### Local Models (Sentence Transformers)
```python
model: "all-MiniLM-L6-v2"
dimensions: 384
max_input: 256 tokens
cost: Free (local inference)
```
- **Pros**: No API cost, privacy, fast
- **Cons**: Quality trade-off, limited max input

**Recommendation**: Use `text-embedding-3-large` for production quality RAG systems.

---

## Vector Storage Systems

### Qdrant (Primary)

**Features**:
- Fast approximate nearest neighbor (ANN) search
- HNSW (Hierarchical Navigable Small World) index
- Filtering by metadata
- Hybrid search (vector + keyword)
- Distributed architecture

**Configuration**:
```python
collection_config = {
    "vectors": {
        "size": 3072,  # Match embedding dimension
        "distance": "Cosine"  # Cosine similarity
    },
    "optimizers_config": {
        "indexing_threshold": 20000  # HNSW build threshold
    }
}
```

**Search Parameters**:
```python
search_params = {
    "hnsw_ef": 128,  # Accuracy vs speed trade-off
    "exact": False   # Use ANN for speed
}
```

### PostgreSQL + pgvector (Alternative)

**Features**:
- SQL-based vector storage
- ACID compliance
- Good for small-medium datasets (<1M vectors)
- Integrated with relational data

**Index Types**:
- `ivfflat`: Fast approximate search
- `hnsw`: Better recall, slower build

---

## Retrieval Strategies

### 1. Vector Search (Semantic)

```python
# Cosine similarity search
results = qdrant.search(
    collection="documents",
    query_vector=embed(query),
    limit=10,
    score_threshold=0.7  # Minimum similarity
)
```

**Pros**: Captures semantic meaning, handles synonyms
**Cons**: May miss exact keyword matches

### 2. Keyword Search (BM25)

```python
# Traditional keyword-based search
results = bm25_search(
    query=query,
    documents=corpus,
    k1=1.5,  # Term frequency saturation
    b=0.75   # Document length normalization
)
```

**Pros**: Exact keyword matches, fast
**Cons**: No semantic understanding

### 3. Hybrid Search (Recommended)

```python
# Combine vector + keyword search
vector_results = vector_search(query, top_k=20)
keyword_results = bm25_search(query, top_k=20)

# Merge with reciprocal rank fusion (RRF)
combined_results = rrf_merge(
    vector_results,
    keyword_results,
    k=60  # RRF parameter
)
```

**Formula**:
```
RRF_score = Σ (1 / (k + rank_i))
```

**Pros**: Best of both worlds - semantic + exact matching
**Cons**: More complex, slower

### 4. Cross-Encoder Reranking

```python
# First-stage retrieval (fast, lower quality)
candidates = hybrid_search(query, top_k=100)

# Second-stage reranking (slow, higher quality)
reranked = cross_encoder.rerank(
    query=query,
    documents=candidates,
    top_k=5
)
```

**Models**:
- `cross-encoder/ms-marco-MiniLM-L-6-v2` (fast)
- `cross-encoder/ms-marco-electra-base` (better quality)

**Pros**: Significantly improves relevance
**Cons**: Slower, can't scale to large corpora

---

## Answer Generation

### Prompt Engineering

**RAG Prompt Template**:
```
You are a helpful assistant answering questions based on provided context.

CONTEXT:
{retrieved_documents}

QUESTION:
{user_question}

INSTRUCTIONS:
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so
3. Cite sources using [Source N] notation
4. Be concise and accurate

ANSWER:
```

### Context Assembly

**Best Practices**:
1. **Deduplication**: Remove duplicate chunks
2. **Ordering**: Most relevant first
3. **Token Budget**: Fit within LLM context window
4. **Citation Metadata**: Include source references

```python
def assemble_context(chunks, max_tokens=2000):
    context = []
    total_tokens = 0

    for i, chunk in enumerate(chunks):
        tokens = count_tokens(chunk.content)
        if total_tokens + tokens > max_tokens:
            break

        context.append(f"[Source {i+1}]\n{chunk.content}\n")
        total_tokens += tokens

    return "\n".join(context)
```

### LLM Selection

#### Claude (Anthropic)
```python
model: "claude-sonnet-4.5"
context_window: 200K tokens
output: 8K tokens
strength: Instruction following, citations
```

#### GPT-4 (OpenAI)
```python
model: "gpt-4-turbo"
context_window: 128K tokens
output: 4K tokens
strength: General reasoning
```

#### Local LLMs (Ollama)
```python
model: "llama3.1:8b"
context_window: 8K tokens
output: 2K tokens
strength: Cost-free, privacy
```

---

## Quality Metrics

### Retrieval Quality

#### Precision@K
```
Precision@K = (Relevant docs in top K) / K
```
- Measures: How many retrieved docs are relevant
- Target: > 0.8 for top 5

#### Recall@K
```
Recall@K = (Relevant docs in top K) / (Total relevant docs)
```
- Measures: Coverage of all relevant docs
- Target: > 0.9 for top 10

#### MRR (Mean Reciprocal Rank)
```
MRR = (1 / Rank of first relevant doc)
```
- Measures: Position of first relevant result
- Target: > 0.7

#### NDCG (Normalized Discounted Cumulative Gain)
```
NDCG@K = DCG@K / Ideal_DCG@K
```
- Measures: Ranking quality
- Target: > 0.8

### Answer Quality

#### Faithfulness
```
Faithfulness = (Claims supported by context) / (Total claims)
```
- Measures: Factual accuracy
- Target: > 0.95

#### Relevance
```
Relevance = (Relevant information in answer) / (Total information)
```
- Measures: Answer relevance to question
- Target: > 0.9

#### Context Utilization
```
Utilization = (Context chunks used) / (Context chunks provided)
```
- Measures: Efficiency of context usage
- Target: 0.6 - 0.8 (balanced)

---

## Performance Optimization

### Embedding Generation

**Batch Processing**:
```python
# Process in batches for efficiency
batch_size = 100
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    embeddings = embedding_model.embed(batch)
```

**Caching**:
```python
# Cache embeddings to avoid recomputation
cache_key = hash(text)
if cache_key in embedding_cache:
    return embedding_cache[cache_key]
```

### Vector Search

**Index Optimization**:
```python
# HNSW parameters
{
    "m": 16,          # Number of connections (higher = better recall)
    "ef_construct": 100,  # Construction time accuracy
    "ef_search": 64   # Search time accuracy
}
```

**Query Optimization**:
```python
# Use filters to reduce search space
results = qdrant.search(
    collection="docs",
    query_vector=vector,
    query_filter={
        "must": [
            {"key": "domain", "match": {"value": "manufacturing"}},
            {"key": "year", "range": {"gte": 2020}}
        ]
    }
)
```

### LLM Generation

**Streaming**:
```python
# Stream responses for better UX
for chunk in llm.generate_stream(prompt):
    yield chunk
```

**Prompt Caching** (Claude):
```python
# Cache system prompts for efficiency
response = anthropic.messages.create(
    model="claude-sonnet-4.5",
    system=[
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}
        }
    ]
)
```

---

## Best Practices

### Document Processing
1. **OCR Quality**: Use high-quality scans (300 DPI+)
2. **Metadata Enrichment**: Add domain expert metadata
3. **Chunking**: Preserve semantic boundaries
4. **Deduplication**: Remove duplicate content

### Retrieval
1. **Hybrid Search**: Combine vector + keyword
2. **Reranking**: Use cross-encoder for top results
3. **Filtering**: Apply metadata filters when possible
4. **Query Expansion**: Expand queries for better recall

### Generation
1. **Context Quality**: Provide high-quality, relevant context
2. **Prompt Engineering**: Clear, specific instructions
3. **Citation**: Always include source attribution
4. **Hallucination Detection**: Verify claims against context

### Monitoring
1. **Track Metrics**: Precision, recall, latency, cost
2. **User Feedback**: Collect thumbs up/down
3. **Error Logging**: Log failures and edge cases
4. **A/B Testing**: Test prompt/retrieval variations

---

**Last Updated**: 2025-01-25
**Version**: 1.0
**Maintained By**: RAG Pipeline SKILL
