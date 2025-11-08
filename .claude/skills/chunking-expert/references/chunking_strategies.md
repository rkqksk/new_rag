# Chunking Strategies - Detailed Reference

## Strategy Comparison Matrix

| Aspect | Atomic | Semantic | Hierarchical | Fixed-Size | Sliding Window | Document-Level |
|--------|--------|----------|--------------|------------|----------------|----------------|
| **Complexity** | Medium | High | High | Low | Low | Minimal |
| **Speed** | Fast | Slow | Medium | Fastest | Medium | Fast |
| **Context** | Good | Excellent | Excellent | Poor | Good | Perfect |
| **Precision** | Excellent | Good | Medium | Poor | Excellent | Medium |
| **Storage** | 1x | 0.5x | 1.5x | 0.9x | 2.5x | 0.3x |
| **Maintenance** | Medium | Low | High | Low | Low | Low |

## Production Metrics (RAG Enterprise)

### Current System (Atomic Chunking)
```
Input: 471 products
Output: 3,246 chunks (6.9 chunks/product)

Chunk Distribution:
- Main product chunks: 471 (14.5%)
- Material chunks: 471 (14.5%)
- Specification chunks: 2,304 (71%)

Size Distribution:
- Min: 23 tokens
- Max: 487 tokens
- Avg: 127 tokens
- Median: 98 tokens

Search Performance:
- Avg similarity: 0.79-0.82
- Retrieval time: < 100ms (top-5)
- Precision@5: 0.89
- Recall@10: 0.94
```

## Chunking Strategy Pseudocode

### Atomic Chunking (Production)
```
FOR each product IN catalog:
    main_chunk = CREATE_CHUNK(
        text = product.code + product.name + product.capacity,
        metadata = {type: "main", code: product.code}
    )

    material_chunk = CREATE_CHUNK(
        text = product.code + product.material,
        metadata = {type: "material", code: product.code}
    )

    FOR each spec IN product.specifications:
        spec_chunk = CREATE_CHUNK(
            text = product.code + spec.key + spec.value,
            metadata = {type: "spec", spec_key: spec.key}
        )

    STORE_CHUNKS([main_chunk, material_chunk, ...spec_chunks])
```

### Semantic Chunking
```
sentences = SPLIT_INTO_SENTENCES(document)
embeddings = EMBED_ALL(sentences)

chunks = []
current_chunk = [sentences[0]]

FOR i IN range(1, len(sentences)):
    similarity = COSINE_SIM(embeddings[i-1], embeddings[i])

    IF similarity < THRESHOLD:
        // Semantic boundary detected
        chunks.APPEND(JOIN(current_chunk))
        current_chunk = [sentences[i]]
    ELSE:
        current_chunk.APPEND(sentences[i])

chunks.APPEND(JOIN(current_chunk))
RETURN chunks
```

### Hierarchical Chunking
```
root = {
    id: GENERATE_ID(),
    text: SUMMARIZE(document),
    level: 0,
    children: []
}

FOR chapter IN DETECT_CHAPTERS(document):
    chapter_node = {
        id: GENERATE_ID(),
        text: chapter.content,
        parent_id: root.id,
        level: 1,
        children: []
    }

    FOR section IN DETECT_SECTIONS(chapter):
        section_node = {
            id: GENERATE_ID(),
            text: section.content,
            parent_id: chapter_node.id,
            level: 2
        }
        chapter_node.children.APPEND(section_node)

    root.children.APPEND(chapter_node)

RETURN root
```

## Optimization Techniques

### 1. Chunk Size Optimization
```python
def optimize_chunk_size(documents, target_metric='similarity'):
    """Find optimal chunk size for dataset."""
    sizes = [128, 256, 512, 1024]
    results = {}

    for size in sizes:
        chunker = FixedSizeChunker(chunk_size=size)
        chunks = chunker.chunk_all(documents)

        # Embed and evaluate
        embeddings = embed_batch(chunks)
        similarity = evaluate_search_quality(embeddings)

        results[size] = {
            'similarity': similarity,
            'chunk_count': len(chunks),
            'avg_retrieval_time': benchmark_retrieval(embeddings)
        }

    return max(results.items(), key=lambda x: x[1][target_metric])
```

### 2. Boundary Detection Optimization
```python
def optimize_semantic_threshold(documents, ground_truth):
    """Find optimal similarity threshold for semantic chunking."""
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

    best_f1 = 0
    best_threshold = 0.7

    for threshold in thresholds:
        chunker = SemanticChunker(similarity_threshold=threshold)
        predicted = chunker.chunk_all(documents)

        precision, recall = evaluate_boundaries(predicted, ground_truth)
        f1 = 2 * (precision * recall) / (precision + recall)

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    return best_threshold
```

## Advanced Patterns

### Hybrid Chunking (Atomic + Semantic)
```python
class HybridChunker:
    """Combines atomic and semantic chunking."""

    def chunk(self, products):
        chunks = []

        for product in products:
            # Atomic chunking for structured fields
            atomic_chunks = self.atomic_chunker.chunk(product)

            # Semantic chunking for long description
            if len(product.description) > 500:
                semantic_chunks = self.semantic_chunker.chunk(
                    product.description
                )
                for i, chunk in enumerate(semantic_chunks):
                    chunks.append({
                        'text': f"{product.code} {chunk}",
                        'metadata': {
                            'type': 'description_semantic',
                            'chunk_index': i
                        }
                    })

            chunks.extend(atomic_chunks)

        return chunks
```

### Context-Aware Chunking
```python
class ContextAwareChunker:
    """Preserves critical context in every chunk."""

    def chunk_with_context(self, document, metadata):
        """Add document context to each chunk."""
        chunks = self.base_chunker.chunk(document)

        context_prefix = f"Document: {metadata['title']}\n"
        context_prefix += f"Category: {metadata['category']}\n\n"

        enriched_chunks = []
        for chunk in chunks:
            enriched_chunks.append({
                'text': context_prefix + chunk['text'],
                'metadata': {
                    **chunk['metadata'],
                    'document_title': metadata['title'],
                    'document_category': metadata['category']
                }
            })

        return enriched_chunks
```

---

**Related**: SKILL.md (main reference), chunking_algorithms.md (implementation details)
