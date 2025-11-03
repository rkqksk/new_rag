# SOP: Embedding Generation for Vector Search

## Purpose
텍스트 데이터를 벡터 임베딩으로 변환하여 의미 기반 검색 가능하게 함

## Scope
- **Input**: JSON 제품 데이터 (specifications, descriptions)
- **Output**: 768-dim vector embeddings
- **Model**: sentence-transformers (paraphrase-multilingual-mpnet-base-v2)

## Prerequisites
- [ ] Product data available (`data/products/crawled/`)
- [ ] `agents/embedding_agent.py` executable
- [ ] Embedding model downloaded (huggingface cache)
- [ ] Sufficient disk space for embeddings (~100MB per 1,000 products)

## Standard Operating Procedure

### 1. 데이터 준비
```python
# Load product data
import json
from pathlib import Path

product_files = list(Path("data/products/crawled").rglob("*.json"))
print(f"Found {len(product_files)} products to embed")
```

### 2. 텍스트 추출 및 전처리
```python
# Extract text for embedding
def extract_text_for_embedding(product: dict) -> str:
    """제품 정보를 임베딩용 텍스트로 변환"""

    text_parts = [
        f"제품명: {product['product_name']}",
        f"제품코드: {product['product_code']}",
        f"카테고리: {product.get('category', '')}",
    ]

    specs = product.get('specifications', {})
    if specs:
        text_parts.append(f"용량: {specs.get('capacity', '')}")
        text_parts.append(f"재질: {specs.get('material', '')}")
        text_parts.append(f"Neck: {specs.get('neck_size', '')}")

    return " | ".join(text_parts)
```

### 3. 임베딩 생성
```bash
# Run embedding agent
python3 agents/embedding_agent.py \
  --input data/products/crawled/ \
  --output data/products/embeddings/ \
  --model paraphrase-multilingual-mpnet-base-v2 \
  --batch-size 32
```

**Python Code (Alternative)**:
```python
from agents.embedding_agent import EmbeddingAgent
from sentence_transformers import SentenceTransformer

# Initialize agent
agent = EmbeddingAgent(
    model_name="paraphrase-multilingual-mpnet-base-v2"
)

# Generate embeddings
results = await agent.generate_embeddings(
    input_dir="data/products/crawled/",
    batch_size=32,
    show_progress=True
)

print(f"✅ Generated {len(results['embeddings'])} embeddings")
print(f"✅ Avg time: {results['avg_time_per_batch']:.2f}s per batch")
```

### 4. 임베딩 검증
```python
# Validate embedding quality
import numpy as np

embeddings = np.load("data/products/embeddings/embeddings.npy")

# Check dimensions
assert embeddings.shape[1] == 768, "Wrong embedding dimension"

# Check for NaN/Inf
assert not np.isnan(embeddings).any(), "NaN values detected"
assert not np.isinf(embeddings).any(), "Inf values detected"

# Check normalization (optional)
norms = np.linalg.norm(embeddings, axis=1)
print(f"Embedding norms: min={norms.min():.3f}, max={norms.max():.3f}")
```

## Quality Checks

### Semantic Similarity Test
```python
# Test semantic similarity
from sentence_transformers import util

# Similar products should have high cosine similarity
bottle_50ml_idx = 0  # "PET 50ml 보틀"
bottle_100ml_idx = 1  # "PET 100ml 보틀"
jar_50ml_idx = 2  # "PET 50ml 크림용기"

sim_bottle = util.cos_sim(
    embeddings[bottle_50ml_idx],
    embeddings[bottle_100ml_idx]
)
sim_jar = util.cos_sim(
    embeddings[bottle_50ml_idx],
    embeddings[jar_50ml_idx]
)

# Expected: same material/similar capacity → higher similarity
print(f"Bottle 50ml ↔ Bottle 100ml: {sim_bottle[0][0]:.3f}")  # Should be > 0.7
print(f"Bottle 50ml ↔ Jar 50ml: {sim_jar[0][0]:.3f}")  # Should be 0.5-0.7
```

### Performance Benchmarks
- **Speed**: 100-150 products/second (batch_size=32)
- **Memory**: ~2GB RAM for 10,000 products
- **Accuracy**: Semantic similarity >0.7 for same-category products

## Error Handling

### Case 1: OOM (Out of Memory)
```python
# Reduce batch size
agent = EmbeddingAgent(model_name="...", batch_size=16)  # Default: 32

# Or use streaming
for batch in agent.generate_embeddings_stream(input_dir, batch_size=8):
    save_batch_embeddings(batch)
```

### Case 2: Model Download Failure
```bash
# Pre-download model
python3 -c "from sentence_transformers import SentenceTransformer; \
             SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"

# Or use local model path
agent = EmbeddingAgent(model_name="/path/to/local/model")
```

### Case 3: Text Encoding Errors
```python
# Handle encoding errors
try:
    text = extract_text_for_embedding(product)
except UnicodeDecodeError as e:
    print(f"⚠️ Encoding error for product {product['product_code']}")
    text = product['product_name']  # Fallback to name only
```

## Output Format

### Embeddings File
```python
# Save embeddings as numpy array
np.save("data/products/embeddings/embeddings.npy", embeddings)

# Save metadata (product_id → embedding_index mapping)
metadata = {
    "product_ids": [p['product_code'] for p in products],
    "embedding_model": "paraphrase-multilingual-mpnet-base-v2",
    "dimension": 768,
    "created_at": "2025-10-26T10:30:00Z"
}
with open("data/products/embeddings/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

## Monitoring

### Metrics to Track
- **Throughput**: Products embedded per second
- **Quality**: Semantic similarity scores for known pairs
- **Coverage**: % of products successfully embedded

### Alerts
- Throughput < 50 products/sec → Performance issue
- Similarity scores < 0.5 for same-category → Model issue
- Coverage < 99% → Data quality problem

## Next Steps
임베딩 생성 완료 후 자동 연계:
1. **Vector Indexing** (agents/vector_db_loader_agent.py)
2. **Search Quality Testing** (scripts/test_search_quality.py)

---

**Owner**: ML Engineering Team
**Last Updated**: 2025-10-26
**Version**: 1.0
