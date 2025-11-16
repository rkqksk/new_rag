# RAG Optimization Workflow Examples

## Example 1: Improve Korean Search Results

### Problem
Korean product names not matching well in search results.

### Diagnosis
```bash
# Test current search quality
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'

# Results showing low similarity (< 0.75)
```

### Solution Steps

**1. Analyze Current Embeddings**
```bash
python .claude/skills/rag-optimization/scripts/analyze_chunks.py \
  --collection products
```

**2. Switch to Multilingual Model**
```python
# Edit src/core/model_router.py
EMBEDDING_CONFIG = {
    "model": "bge-m3:latest",  # Better Korean support
    "dimension": 1024,
    "provider": "ollama"
}
```

**3. Re-index with New Model**
```bash
# Backup current collection
python scripts/backup_qdrant.py --collection products

# Re-embed and re-index
python scripts/reindex_collection.py \
  --collection products \
  --model bge-m3 \
  --batch-size 100
```

**4. Test Improvements**
```bash
# Same query, better results
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'

# Expected: similarity > 0.85
```

### Results
- Before: avg similarity 0.73
- After: avg similarity 0.88
- Improvement: +20%

---

## Example 2: Optimize Chunking for Large PDFs

### Problem
Large PDF documents creating too many small, disconnected chunks.

### Diagnosis
```bash
# Analyze current chunks
python .claude/skills/rag-optimization/scripts/analyze_chunks.py

# Output shows:
# - 30% chunks < 100 tokens (too small)
# - Mean size: 180 tokens
```

### Solution Steps

**1. Adjust Chunking Parameters**
```python
# Edit src/services/chunking_service.py
CHUNKING_CONFIG = {
    "strategy": "semantic",
    "chunk_size": 512,       # Was: 256
    "overlap": 150,          # Was: 50
    "min_chunk_size": 200,   # Was: 50
    "preserve_boundaries": True
}
```

**2. Implement Hierarchical Chunking**
```python
def chunk_large_document(pdf_path: str):
    """
    Create summary + detail chunks
    """
    # Extract full text
    full_text = extract_pdf_text(pdf_path)

    # Create summary chunk
    summary = generate_summary(full_text, max_tokens=300)
    summary_chunk = {
        "text": summary,
        "metadata": {
            "type": "summary",
            "source": pdf_path,
            "is_parent": True
        }
    }

    # Create detail chunks linked to summary
    detail_chunks = semantic_chunk(full_text, max_size=512)
    for i, chunk_text in enumerate(detail_chunks):
        yield {
            "text": chunk_text,
            "metadata": {
                "type": "detail",
                "source": pdf_path,
                "parent_summary": summary,
                "chunk_index": i
            }
        }
```

**3. Re-process Documents**
```bash
python scripts/reprocess_pdfs.py \
  --input data/pdfs/ \
  --strategy hierarchical \
  --output data/chunks/
```

### Results
- Before: 30% chunks < 100 tokens
- After: 5% chunks < 100 tokens
- Mean size: 180 → 420 tokens
- Retrieval quality (mAP@5): 0.79 → 0.87

---

## Example 3: Speed Up Embedding Generation

### Problem
Embedding generation taking too long (~200ms per query).

### Diagnosis
```bash
# Benchmark current performance
python scripts/benchmark_embeddings.py \
  --model bge-m3 \
  --queries data/test_queries.json

# Output:
# - Average latency: 215ms
# - Throughput: 4.6 queries/sec
```

### Solution Steps

**1. Switch to Faster Model**
```python
# src/core/model_router.py
from nexa.gguf import NexaTextEmbedding

# NexaAI is 4x faster
embedder = NexaTextEmbedding(
    model_path="nomic-embed-text-v1.5",
    local_path="/path/to/models"
)
```

**2. Implement Batch Processing**
```python
# Before: One-by-one
embeddings = [embedder.embed(q) for q in queries]  # Slow

# After: Batch
embeddings = embedder.embed_batch(queries)  # Fast
```

**3. Add Query Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(query: str):
    """
    Cache frequent queries
    """
    return embedder.embed(query)
```

**4. Benchmark Again**
```bash
python scripts/benchmark_embeddings.py \
  --model nomic-embed-text \
  --queries data/test_queries.json \
  --use-cache
```

### Results
- Before: 215ms per query
- After: 52ms per query (4x faster)
- Cache hit rate: 35%
- Throughput: 4.6 → 19 queries/sec

---

## Example 4: Implement Hybrid Search

### Problem
Pure vector search misses exact product code matches.

### Example
```
Query: "KR-PET-50ML-001"  (exact product code)
Vector search returns: Generic 50ml bottles (irrelevant)
```

### Solution: Vector + Keyword Hybrid

**1. Add PostgreSQL Full-Text Search**
```sql
-- Enable full-text search extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add GIN index for fast text search
CREATE INDEX idx_products_fulltext
ON products USING GIN (to_tsvector('korean', name || ' ' || description));

-- Add trigram index for fuzzy matching
CREATE INDEX idx_products_trigram
ON products USING GIN (name gin_trgm_ops);
```

**2. Implement Hybrid Search**
```python
async def hybrid_search(query: str, top_k: int = 5, alpha: float = 0.7):
    """
    Combine vector search + keyword search

    alpha: weight for vector search (0.7 = 70% vector, 30% keyword)
    """
    # Vector search (Qdrant)
    vector_results = await vector_search(query, top_k=top_k*2)

    # Keyword search (PostgreSQL)
    keyword_results = await keyword_search(query, top_k=top_k*2)

    # Normalize scores
    vector_scores = normalize_scores([r.score for r in vector_results])
    keyword_scores = normalize_scores([r.score for r in keyword_results])

    # Combine with weighted sum
    combined = {}
    for i, result in enumerate(vector_results):
        combined[result.id] = alpha * vector_scores[i]

    for i, result in enumerate(keyword_results):
        if result.id in combined:
            combined[result.id] += (1 - alpha) * keyword_scores[i]
        else:
            combined[result.id] = (1 - alpha) * keyword_scores[i]

    # Sort by combined score
    sorted_ids = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return sorted_ids[:top_k]
```

**3. Test Hybrid Search**
```bash
curl -X POST http://localhost:8001/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "KR-PET-50ML-001",
    "top_k": 5,
    "alpha": 0.7
  }'
```

### Results
- Exact product code matches: 100% (was 40%)
- Overall relevance: +15%
- Latency: +30ms (acceptable trade-off)

---

## Example 5: Monitor Search Quality Over Time

### Setup Continuous Monitoring

**1. Create Test Query Set**
```python
# data/test_queries.json
[
    {
        "query": "50ml PET 용기",
        "expected_results": ["KR-PET-50ML-001", "KR-PET-50ML-002"],
        "min_similarity": 0.85
    },
    {
        "query": "불량 검사 기준",
        "expected_results": ["DOC-QC-001"],
        "min_similarity": 0.80
    }
]
```

**2. Automated Testing**
```python
# scripts/test_search_quality.py
def test_search_quality():
    """
    Run daily search quality tests
    """
    test_queries = load_test_queries()
    results = []

    for test in test_queries:
        search_results = search(test['query'], top_k=5)

        # Check if expected results are in top-K
        found = [r.id for r in search_results]
        expected = test['expected_results']

        precision = len(set(found) & set(expected)) / len(found)
        recall = len(set(found) & set(expected)) / len(expected)

        # Check similarity threshold
        avg_similarity = sum(r.score for r in search_results) / len(search_results)

        results.append({
            "query": test['query'],
            "precision": precision,
            "recall": recall,
            "avg_similarity": avg_similarity,
            "passed": avg_similarity >= test['min_similarity']
        })

    # Send to monitoring
    send_to_prometheus(results)

    return results
```

**3. Grafana Dashboard**
```yaml
# grafana/rag_quality_dashboard.json
{
  "dashboard": {
    "title": "RAG Search Quality",
    "panels": [
      {
        "title": "Average Similarity Score",
        "targets": [
          "avg(search_similarity)"
        ]
      },
      {
        "title": "Precision@5",
        "targets": [
          "avg(search_precision_at_5)"
        ]
      },
      {
        "title": "Failed Queries (< 0.75)",
        "targets": [
          "count(search_similarity < 0.75)"
        ]
      }
    ]
  }
}
```

**4. Alerts**
```yaml
# prometheus/alerts.yml
groups:
  - name: rag_quality
    rules:
      - alert: LowSearchQuality
        expr: avg(search_similarity) < 0.75
        for: 1h
        annotations:
          summary: "Search quality degraded"
          description: "Average similarity below 0.75 for 1 hour"
```

### Results
- Continuous quality monitoring
- Early detection of issues
- Historical trend analysis
