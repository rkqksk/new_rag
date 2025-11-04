# RAG Query Workflow

**Purpose**: Execute RAG queries with retrieval, reranking, and answer generation.

---

## Overview

This workflow handles the complete RAG query pipeline from user question to final answer with sources.

### Key Features
- Semantic vector search
- Hybrid search (vector + keyword/BM25)
- Reranking for relevance
- Context-aware answer generation
- Source attribution

---

## Components Involved

### 1. SKILL: rag-pipeline
**Location**: `.claude/skills/rag-pipeline/`
**Role**: Orchestrates query execution
**Commands**: `query`, `search`

### 2. MCP: qdrant
**Role**: Vector search and retrieval
**Operations**: Search vectors, filter by metadata

### 3. LLM: Claude or Ollama
**Role**: Answer generation from retrieved context
**Models**: Claude (via API), Ollama (local)

---

## Step-by-Step Flow

### Step 1: User Query
```python
user_question = "What are the Cpk requirements for critical processes?"
```

### Step 2: SKILL Activation
```python
from .claude.skills.rag_pipeline import skill

answer = skill.execute('query', {
    'question': user_question,
    'top_k': 5,
    'use_rerank': True,
    'use_hybrid': False,
    'filters': {
        'doc_type': 'sop',
        'domain': 'manufacturing'
    }
})
```

### Step 3: Query Embedding
```python
# Convert question to vector
query_vector = embed_text(user_question)
```

### Step 4: Vector Search (Qdrant)
```python
# Search in Qdrant
search_results = qdrant.search(
    collection="documents",
    query_vector=query_vector,
    limit=top_k,
    filter={
        'must': [
            {'key': 'doc_type', 'match': {'value': 'sop'}},
            {'key': 'domain', 'match': {'value': 'manufacturing'}}
        ]
    }
)

# Results include:
# - id: chunk ID
# - score: similarity score
# - payload: chunk content + metadata
```

### Step 5: Hybrid Search (Optional)
```python
if use_hybrid:
    # Combine vector search + keyword search (BM25)
    vector_results = vector_search(query_vector)
    keyword_results = keyword_search(user_question)

    # Merge and deduplicate
    search_results = merge_results(vector_results, keyword_results)
```

### Step 6: Reranking (Optional)
```python
if use_rerank:
    # Rerank results for better relevance
    reranked = rerank_model.rerank(
        query=user_question,
        documents=[r.payload.content for r in search_results]
    )

    # Sort by rerank scores
    search_results = sort_by_rerank_scores(search_results, reranked)
```

### Step 7: Context Assembly
```python
# Build context from top results
context_chunks = []
for result in search_results[:5]:
    chunk = {
        'content': result.payload.content,
        'source': result.payload.filename,
        'doc_type': result.payload.doc_type,
        'score': result.score
    }
    context_chunks.append(chunk)

context_text = "\n\n".join([c['content'] for c in context_chunks])
```

### Step 8: Answer Generation (LLM)
```python
# Generate answer using LLM
prompt = f"""Based on the following context, answer the question.

Context:
{context_text}

Question: {user_question}

Answer (be specific and cite sources):"""

answer_text = llm.generate(prompt)
```

### Step 9: Return Result
```python
return {
    'answer': answer_text,
    'sources': [
        {
            'content': c['content'][:200],  # Preview
            'source': c['source'],
            'score': c['score']
        }
        for c in context_chunks
    ],
    'metadata': {
        'chunks_retrieved': len(search_results),
        'reranked': use_rerank,
        'hybrid': use_hybrid
    }
}
```

---

## Usage Examples

### Basic RAG Query
```python
from .claude.skills.rag_pipeline import skill

answer = skill.execute('query', {
    'question': 'What are the temperature requirements?'
})

print(answer['answer'])
print(f"\nSources: {len(answer['sources'])}")
```

### With Filters (Manufacturing)
```python
answer = skill.execute('query', {
    'question': 'What are Cpk requirements?',
    'top_k': 10,
    'filters': {
        'doc_type': 'sop',
        'domain': 'manufacturing',
        'terminology': {'$contains': 'cpk'}
    }
})
```

### With Reranking
```python
answer = skill.execute('query', {
    'question': 'Explain calibration procedures',
    'top_k': 20,  # Get more candidates
    'use_rerank': True  # Rerank to top 5
})
```

### Hybrid Search
```python
answer = skill.execute('query', {
    'question': 'ISO 9001 compliance requirements',
    'use_hybrid': True  # Vector + keyword search
})
```

### Vector Search Only (No Generation)
```python
results = skill.execute('search', {
    'query': '50ml PET bottle',
    'top_k': 10,
    'filters': {
        'domain': 'packaging'
    }
})

# Returns raw search results without answer generation
for r in results:
    print(f"{r['score']:.3f}: {r['content'][:100]}")
```

---

## Error Handling

### Common Issues

#### 1. No Results Found
```
Error: No relevant documents found
Solution:
- Check if documents are indexed
- Try broader query
- Remove strict filters
```

#### 2. Low Quality Answers
```
Issue: Answer is generic or not helpful
Solution:
- Use reranking: use_rerank=True
- Increase top_k for more context
- Add domain filters
```

#### 3. Qdrant Connection Error
```
Error: Cannot connect to Qdrant
Solution: docker-compose ps && docker-compose up -d
```

#### 4. LLM Error
```
Error: LLM generation failed
Solution:
- Check API keys in .env
- Verify Ollama is running (if using local)
- Check rate limits
```

---

## Performance Tuning

### Search Parameters

| Parameter | Fast | Balanced | Thorough |
|-----------|------|----------|----------|
| `top_k` | 3 | 5-10 | 20+ |
| `use_rerank` | False | False | True |
| `use_hybrid` | False | False | True |

### Speed vs Quality

**Fast Mode** (~500ms):
```python
{
    'top_k': 3,
    'use_rerank': False,
    'use_hybrid': False
}
```

**Balanced Mode** (~1-2s):
```python
{
    'top_k': 5,
    'use_rerank': False,
    'use_hybrid': False,
    'filters': {...}  # Use filters for precision
}
```

**Thorough Mode** (~3-5s):
```python
{
    'top_k': 20,
    'use_rerank': True,
    'use_hybrid': True
}
```

---

## Advanced Filtering

### Filter by Document Type
```python
filters = {'doc_type': {'$in': ['sop', 'spec', 'drawing']}}
```

### Filter by Domain
```python
filters = {'domain': 'manufacturing'}
```

### Filter by Terminology
```python
filters = {
    'terminology': {
        '$contains': 'cpk'  # Documents containing Cpk term
    }
}
```

### Combined Filters
```python
filters = {
    '$and': [
        {'doc_type': 'sop'},
        {'domain': 'manufacturing'},
        {'terminology': {'$contains': 'calibration'}}
    ]
}
```

---

## Related Workflows

- `/workflow document-processing` - How documents are indexed
- `/workflow vector-search` - Deep dive into vector search
- `/workflow domain-expert` - Domain-specific metadata filtering

---

## Component Details

- `/component skills` - rag-pipeline SKILL implementation
- `/component mcp` - Qdrant MCP configuration
- `/guide development` - Development commands and scenarios

---

**Last Updated**: 2025-11-03
