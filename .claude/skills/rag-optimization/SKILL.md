---
name: rag-optimization
description: RAG search quality chunking embedding vector similarity Qdrant retrieval 검색 최적화 청킹 임베딩 벡터 유사도 쿼리 향상 semantic search performance tuning Korean multilingual NexaAI Ollama indexing 데이터 인덱싱 품질 개선
---

# RAG Optimization

## When to Use
- 검색 품질 개선, search quality improvement
- 청킹 전략 변경, chunking strategy
- 임베딩 모델 선택, embedding model selection
- 쿼리 향상, query enhancement
- 유사도 낮음, low similarity scores
- 한글 검색 문제, Korean search issues
- 성능 튜닝, performance tuning
- Qdrant 인덱싱, vector database indexing

## Core Capabilities
1. **Chunking Optimization** - Semantic, fixed-size, hybrid strategies
2. **Embedding Selection** - NexaAI (50ms), Ollama bge-m3 (200ms), sentence-transformers
3. **Query Enhancement** - Rewriting, expansion, routing
4. **Search Tuning** - Similarity thresholds (0.75-0.85), top-k selection
5. **Performance Monitoring** - Grafana dashboards, Prometheus metrics

## Quick Actions

### Analyze Current Performance
```python
# Check search quality
python scripts/benchmark_search.py --queries data/test_queries.json

# Analyze chunks
python scripts/analyze_chunks.py --collection products
```

### Optimize Chunking
```python
# Switch to semantic chunking
# Edit src/services/chunking_service.py
strategy = "semantic"  # or "hybrid", "fixed"
chunk_size = 512
overlap = 150  # tokens
```

### Test Embedding Models
```python
# Compare models
python scripts/test_embeddings.py \
  --models nomic,bge-m3,mpnet \
  --metrics precision,recall,latency
```

### Tune Search Parameters
```python
# Adjust thresholds in src/services/rag_service.py
similarity_threshold = 0.80  # Default
top_k = 5
reranking = True  # Optional
```

## Integration
- **data-collection**: Index newly crawled data
- **testing-suite**: Generate RAG component tests
- **excel-processing**: Handle tabular data chunks
- **pdf-processing**: Process PDF documents

## Key Files
- `src/services/rag_service.py` - Main RAG logic
- `src/services/chunking_service.py` - Chunking strategies
- `src/core/model_router.py` - Embedding model selection

## Resources
- `resources/chunking_strategies.md` - Detailed chunking guide
- `resources/embedding_comparison.md` - Model benchmarks
- `resources/query_enhancement.md` - Query processing techniques
