# Vector Database - Qdrant

**High-performance vector similarity search for RAG Enterprise**

---

## Table of Contents

1. [Overview](#overview)
2. [Why Qdrant?](#why-qdrant)
3. [Architecture](#architecture)
4. [Collections & Schema](#collections--schema)
5. [Vector Operations](#vector-operations)
6. [Search & Filtering](#search--filtering)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring](#monitoring)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Qdrant?

**Qdrant** is a high-performance, open-source vector database written in Rust, designed for semantic search and similarity matching.

**Key Features**:
- ✅ **Fast**: Rust-based, HNSW algorithm, ~2ms search latency (P95)
- ✅ **Rich Filtering**: Combines vector search with metadata filtering
- ✅ **Multi-Vector**: Multiple vectors per document (text, image, shape)
- ✅ **Scalable**: Distributed mode, sharding, replication
- ✅ **Production-Ready**: ACID guarantees, snapshots, backups
- ✅ **Easy**: REST API, Python SDK, web UI

### Current Usage in RAG Enterprise

```
Data Volume:
- Collections: 3 (products_text, products_image, products_shape)
- Vectors: 3,246 text + 471 image + 471 shape = 4,188 total
- Dimensions: 384 (text), 1024 (image), 128 (shape)
- Storage: ~45MB

Performance:
- Search Latency: 1.8ms (P50), 4.2ms (P95), 12ms (P99)
- Indexing Speed: ~850 vectors/sec
- Throughput: ~500 QPS (single node)
- Memory: ~280MB resident
```

---

## Why Qdrant?

### Comparison with Alternatives

| Feature | Qdrant | Pinecone | Weaviate | Milvus |
|---------|--------|----------|----------|--------|
| **License** | Apache 2.0 | Proprietary | BSD-3 | Apache 2.0 |
| **Deployment** | Local + Cloud | Cloud only | Local + Cloud | Local + Cloud |
| **Performance** | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| **Filtering** | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **Multi-Vector** | ✅ | ❌ | ✅ | ✅ |
| **Ease of Use** | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| **Cost** | Free (local) | $$$ | Free (local) | Free (local) |

### Why We Chose Qdrant

1. **Local-First**: No vendor lock-in, works offline
2. **Performance**: Rust-based, fastest in benchmarks
3. **Rich Filtering**: Essential for product search (material, capacity, price)
4. **Multi-Vector**: Supports text + image + shape embeddings
5. **Production-Ready**: Used by major companies (Red Hat, Twilio, etc.)
6. **Simple**: Easy setup, great documentation

---

## Architecture

### System Architecture

```
Application Layer
    ↓
[Qdrant Python SDK]
    ↓ (gRPC / HTTP)
[Qdrant Server]
    ↓
┌─────────────────────────────────┐
│  Collection: products_text      │
│  - HNSW Index (m=16, ef=128)    │
│  - Payload Index (material, etc)│
│  - 3,246 vectors (384-dim)      │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│  Collection: products_image     │
│  - 471 vectors (1024-dim)       │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│  Collection: products_shape     │
│  - 471 vectors (128-dim)        │
└─────────────────────────────────┘
    ↓
[Storage: /qdrant/storage]
```

### HNSW Algorithm

**Hierarchical Navigable Small World (HNSW)**:
- **Index Type**: Graph-based approximate nearest neighbor
- **Trade-off**: Speed vs accuracy (we use balanced settings)
- **Parameters**:
  - `m=16`: Number of connections per node (higher = more accurate, slower)
  - `ef_construct=128`: Search depth during indexing (higher = better quality)
  - `ef=128`: Search depth during querying (higher = more accurate)

**Performance Characteristics**:
- Build time: O(n log n)
- Query time: O(log n)
- Memory: ~32 bytes per vector (for m=16)

---

## Collections & Schema

### Collection: `products_text`

**Purpose**: Semantic search on product descriptions

**Schema**:
```python
{
    "name": "products_text",
    "vectors": {
        "size": 384,  # all-MiniLM-L6-v2 dimension
        "distance": "Cosine"
    },
    "hnsw_config": {
        "m": 16,
        "ef_construct": 128
    },
    "optimizers_config": {
        "indexing_threshold": 20000
    }
}
```

**Payload Schema**:
```python
{
    "product_id": "string",          # Unique ID (e.g., "P001")
    "chunk_id": "string",            # Chunk ID (e.g., "P001_chunk_0")
    "chunk_type": "string",          # "atomic" | "field" | "full"
    "text": "string",                # Original text

    # Extracted fields
    "product_code": "string",        # "A-100"
    "product_name": "string",        # "50ml PET 투명 용기"
    "capacity_ml": "float",          # 50.0
    "neck_size": "float",            # 20.0
    "material": "string",            # "PET"
    "moq": "integer",                # 1000
    "unit_price": "float",           # 120.0

    # Metadata
    "source_file": "string",         # "chunjinkorea_products.json"
    "crawl_date": "string",          # "2025-11-01"
    "chunk_index": "integer",        # 0
    "total_chunks": "integer"        # 5
}
```

### Collection: `products_image`

**Purpose**: Visual similarity search

**Schema**:
```python
{
    "name": "products_image",
    "vectors": {
        "size": 1024,  # CLIP ViT-B/32 dimension
        "distance": "Cosine"
    },
    "hnsw_config": {
        "m": 16,
        "ef_construct": 100
    }
}
```

**Payload Schema**:
```python
{
    "product_id": "string",
    "image_url": "string",
    "image_path": "string",          # Local cache path
    "dominant_color": "string",      # "#FF5733"
    "has_transparency": "boolean",
    "aspect_ratio": "float"
}
```

### Collection: `products_shape`

**Purpose**: Shape-based similarity (3D geometry)

**Schema**:
```python
{
    "name": "products_shape",
    "vectors": {
        "size": 128,  # Custom shape encoder
        "distance": "Euclidean"
    }
}
```

**Payload Schema**:
```python
{
    "product_id": "string",
    "shape_type": "string",          # "cylinder", "cube", "sphere"
    "dimensions": "object",          # {"height": 100, "diameter": 50}
    "volume_ml": "float"
}
```

---

## Vector Operations

### Create Collection

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, HnswConfigDiff

client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="products_text",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE
    ),
    hnsw_config=HnswConfigDiff(
        m=16,
        ef_construct=128
    )
)
```

### Upsert Vectors

**Single Vector**:
```python
from qdrant_client.models import PointStruct

client.upsert(
    collection_name="products_text",
    points=[
        PointStruct(
            id="P001_chunk_0",
            vector=[0.1, 0.2, ...],  # 384-dim
            payload={
                "product_id": "P001",
                "text": "50ml PET 투명 용기",
                "capacity_ml": 50.0,
                "material": "PET"
            }
        )
    ]
)
```

**Batch Upsert** (Recommended):
```python
from typing import List
from qdrant_client.models import Batch

def batch_upsert(
    client: QdrantClient,
    collection_name: str,
    ids: List[str],
    vectors: List[List[float]],
    payloads: List[dict],
    batch_size: int = 100
):
    """Efficient batch upsert"""
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_vectors = vectors[i:i+batch_size]
        batch_payloads = payloads[i:i+batch_size]

        client.upsert(
            collection_name=collection_name,
            points=Batch(
                ids=batch_ids,
                vectors=batch_vectors,
                payloads=batch_payloads
            )
        )
```

### Delete Vectors

```python
# Delete by ID
client.delete(
    collection_name="products_text",
    points_selector=["P001_chunk_0", "P001_chunk_1"]
)

# Delete by filter
from qdrant_client.models import Filter, FieldCondition, MatchValue

client.delete(
    collection_name="products_text",
    points_selector=Filter(
        must=[
            FieldCondition(
                key="product_id",
                match=MatchValue(value="P001")
            )
        ]
    )
)
```

### Update Payload

```python
# Update single field
client.set_payload(
    collection_name="products_text",
    payload={"unit_price": 150.0},
    points=["P001_chunk_0"]
)

# Delete field
client.delete_payload(
    collection_name="products_text",
    keys=["unit_price"],
    points=["P001_chunk_0"]
)
```

---

## Search & Filtering

### Basic Vector Search

```python
results = client.search(
    collection_name="products_text",
    query_vector=[0.1, 0.2, ...],  # 384-dim
    limit=5
)

for result in results:
    print(f"ID: {result.id}")
    print(f"Score: {result.score}")
    print(f"Payload: {result.payload}")
```

### Filtered Search

**Single Filter**:
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="products_text",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="material",
                match=MatchValue(value="PET")
            )
        ]
    ),
    limit=5
)
```

**Range Filter**:
```python
from qdrant_client.models import Range

results = client.search(
    collection_name="products_text",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="capacity_ml",
                range=Range(gte=50.0, lte=100.0)
            ),
            FieldCondition(
                key="unit_price",
                range=Range(lte=200.0)
            )
        ]
    ),
    limit=5
)
```

**Complex Filter** (AND/OR/NOT):
```python
results = client.search(
    collection_name="products_text",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            # AND: Material must be PET or PP
            FieldCondition(
                key="material",
                match=MatchAny(any=["PET", "PP"])
            )
        ],
        should=[
            # OR: Capacity 50ml or 100ml (boosts score)
            FieldCondition(
                key="capacity_ml",
                match=MatchAny(any=[50.0, 100.0])
            )
        ],
        must_not=[
            # NOT: Exclude high prices
            FieldCondition(
                key="unit_price",
                range=Range(gte=500.0)
            )
        ]
    ),
    limit=5
)
```

### Multi-Vector Search (Hybrid)

```python
from qdrant_client.models import ScoredPoint

# 1. Search text collection
text_results = client.search(
    collection_name="products_text",
    query_vector=text_embedding,
    limit=10
)

# 2. Search image collection
image_results = client.search(
    collection_name="products_image",
    query_vector=image_embedding,
    limit=10
)

# 3. Merge results (Reciprocal Rank Fusion)
def reciprocal_rank_fusion(
    results_list: List[List[ScoredPoint]],
    k: int = 60
) -> List[ScoredPoint]:
    """Combine multiple search results"""
    scores = {}

    for results in results_list:
        for rank, result in enumerate(results):
            product_id = result.payload.get("product_id")
            if product_id not in scores:
                scores[product_id] = {"score": 0, "result": result}

            # RRF formula: 1 / (k + rank)
            scores[product_id]["score"] += 1.0 / (k + rank + 1)

    # Sort by combined score
    combined = sorted(
        scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return [item["result"] for item in combined]

# Merge
final_results = reciprocal_rank_fusion([text_results, image_results])
```

### Scroll (Retrieve All)

```python
# Get all vectors in batches
offset = None
all_points = []

while True:
    results, next_offset = client.scroll(
        collection_name="products_text",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )

    all_points.extend(results)

    if next_offset is None:
        break

    offset = next_offset

print(f"Total points: {len(all_points)}")
```

---

## Performance Optimization

### 1. HNSW Parameter Tuning

**Default Settings** (Balanced):
```python
hnsw_config = HnswConfigDiff(
    m=16,              # Connections per node
    ef_construct=128   # Build-time search depth
)

# Query-time
search_params = models.SearchParams(
    hnsw_ef=128        # Query-time search depth
)
```

**High Accuracy** (Slower):
```python
hnsw_config = HnswConfigDiff(
    m=32,
    ef_construct=256
)
search_params = models.SearchParams(hnsw_ef=256)
```

**High Speed** (Lower accuracy):
```python
hnsw_config = HnswConfigDiff(
    m=8,
    ef_construct=64
)
search_params = models.SearchParams(hnsw_ef=64)
```

### 2. Payload Indexing

**Index Frequently Filtered Fields**:
```python
from qdrant_client.models import PayloadSchemaType, TextIndexParams

client.create_payload_index(
    collection_name="products_text",
    field_name="material",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="products_text",
    field_name="capacity_ml",
    field_schema=PayloadSchemaType.FLOAT
)

# Text search index
client.create_payload_index(
    collection_name="products_text",
    field_name="text",
    field_schema=TextIndexParams(
        type="text",
        tokenizer="word",
        min_token_len=2,
        max_token_len=20
    )
)
```

### 3. Quantization (Reduce Memory)

**Scalar Quantization** (Fastest):
```python
from qdrant_client.models import ScalarQuantization, ScalarType

client.update_collection(
    collection_name="products_text",
    quantization_config=ScalarQuantization(
        scalar=ScalarType.INT8,
        always_ram=True
    )
)
# Memory reduction: ~75% (384 * 4 bytes → 384 * 1 byte)
# Accuracy loss: < 1%
```

**Product Quantization** (Higher accuracy):
```python
from qdrant_client.models import ProductQuantization

client.update_collection(
    collection_name="products_image",
    quantization_config=ProductQuantization(
        product=models.ProductQuantizationConfig(
            compression=models.CompressionRatio.X16,
            always_ram=True
        )
    )
)
# Memory reduction: ~93% (1024 * 4 → 1024 / 16)
# Accuracy loss: < 3%
```

### 4. Batch Operations

**Always use batching**:
```python
# ❌ Bad: One-by-one
for vector_id, vector, payload in data:
    client.upsert(
        collection_name="products_text",
        points=[PointStruct(id=vector_id, vector=vector, payload=payload)]
    )
# Speed: ~50 vectors/sec

# ✅ Good: Batched
client.upsert(
    collection_name="products_text",
    points=Batch(
        ids=vector_ids,
        vectors=vectors,
        payloads=payloads
    )
)
# Speed: ~850 vectors/sec (17x faster)
```

### 5. Connection Pooling

```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import UpdateStatus

# Use single client instance (reuse HTTP connections)
client = QdrantClient(
    host="localhost",
    port=6333,
    grpc_port=6334,
    prefer_grpc=True,  # 2-3x faster than HTTP
    timeout=60
)

# Configure FastAPI with dependency injection
from fastapi import Depends

def get_qdrant_client():
    """Reusable client (singleton pattern)"""
    return client

@app.get("/search")
async def search(
    query: str,
    client: QdrantClient = Depends(get_qdrant_client)
):
    results = client.search(...)
    return results
```

### 6. Optimization Status

**Check optimization progress**:
```python
collection_info = client.get_collection(collection_name="products_text")

print(f"Status: {collection_info.status}")
print(f"Vectors: {collection_info.vectors_count}")
print(f"Indexed: {collection_info.indexed_vectors_count}")
print(f"Optimizer status: {collection_info.optimizer_status}")

# Wait for optimization to complete
if collection_info.optimizer_status != "ok":
    print("⚠️ Collection is being optimized...")
```

---

## Monitoring

### Collection Statistics

```python
collection_info = client.get_collection(collection_name="products_text")

print(f"""
Collection: {collection_info.config.params.vectors.size}-dim
Status: {collection_info.status}
Vectors: {collection_info.vectors_count:,}
Points: {collection_info.points_count:,}
Segments: {len(collection_info.segments)}
Optimizer: {collection_info.optimizer_status}
""")
```

### Performance Metrics

```python
import time

def benchmark_search(client, collection_name, query_vector, iterations=100):
    """Measure search latency"""
    latencies = []

    for _ in range(iterations):
        start = time.perf_counter()
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=5
        )
        latency = (time.perf_counter() - start) * 1000  # ms
        latencies.append(latency)

    latencies.sort()

    print(f"""
    Search Performance (n={iterations}):
    - P50: {latencies[len(latencies)//2]:.2f}ms
    - P95: {latencies[int(len(latencies)*0.95)]:.2f}ms
    - P99: {latencies[int(len(latencies)*0.99)]:.2f}ms
    - Mean: {sum(latencies)/len(latencies):.2f}ms
    """)

# Run benchmark
benchmark_search(client, "products_text", query_embedding)
```

### Health Check

```python
def check_qdrant_health(client: QdrantClient) -> dict:
    """Health check for monitoring"""
    try:
        # Try to get collections
        collections = client.get_collections()

        health = {
            "status": "healthy",
            "collections": len(collections.collections),
            "details": []
        }

        for collection in collections.collections:
            info = client.get_collection(collection.name)
            health["details"].append({
                "name": collection.name,
                "vectors": info.vectors_count,
                "status": info.status
            })

        return health

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Use in FastAPI
@app.get("/health/qdrant")
async def qdrant_health():
    return check_qdrant_health(client)
```

---

## Configuration

### Environment Variables

```bash
# Qdrant Connection
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=          # Optional (for Qdrant Cloud)
QDRANT_PREFER_GRPC=true  # 2-3x faster

# Collection Names
QDRANT_COLLECTION_TEXT=products_text
QDRANT_COLLECTION_IMAGE=products_image
QDRANT_COLLECTION_SHAPE=products_shape

# Performance
QDRANT_TIMEOUT=60
QDRANT_BATCH_SIZE=100
```

### Docker Compose

```yaml
services:
  qdrant:
    image: qdrant/qdrant:v1.8.0
    container_name: qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      # Performance tuning
      QDRANT__SERVICE__MAX_REQUEST_SIZE_MB: 128
      QDRANT__SERVICE__GRPC_PORT: 6334
      QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS: 4
    restart: unless-stopped

volumes:
  qdrant_storage:
    driver: local
```

### Python Client Configuration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Local deployment
client = QdrantClient(
    host="localhost",
    port=6333,
    grpc_port=6334,
    prefer_grpc=True,
    timeout=60
)

# Qdrant Cloud
client = QdrantClient(
    url="https://xyz.cloud.qdrant.io",
    api_key=os.getenv("QDRANT_API_KEY"),
    prefer_grpc=True
)

# In-memory (for testing)
client = QdrantClient(":memory:")
```

---

## Troubleshooting

### Issue: Slow Search Performance

**Problem**: Search taking > 50ms

**Solutions**:

1. **Enable gRPC**:
```python
client = QdrantClient(
    host="localhost",
    port=6333,
    grpc_port=6334,
    prefer_grpc=True  # 2-3x faster
)
```

2. **Reduce ef parameter**:
```python
search_params = models.SearchParams(
    hnsw_ef=64  # Default: 128
)

results = client.search(
    collection_name="products_text",
    query_vector=query_embedding,
    search_params=search_params,
    limit=5
)
```

3. **Enable quantization**:
```python
# Scalar quantization (fastest)
client.update_collection(
    collection_name="products_text",
    quantization_config=ScalarQuantization(
        scalar=ScalarType.INT8,
        always_ram=True
    )
)
```

### Issue: Out of Memory

**Problem**: Qdrant crashes with OOM

**Solutions**:

1. **Enable quantization** (see above)

2. **Limit RAM usage**:
```yaml
# docker-compose.yml
services:
  qdrant:
    mem_limit: 2g
    environment:
      QDRANT__STORAGE__PERFORMANCE__OPTIMIZER__MAX_OPTIMIZATION_THREADS: 1
```

3. **Use mmap storage**:
```python
from qdrant_client.models import OptimizersConfigDiff

client.update_collection(
    collection_name="products_text",
    optimizers_config=OptimizersConfigDiff(
        memmap_threshold=20000  # Use disk for large segments
    )
)
```

### Issue: Collection Not Found

**Problem**: `CollectionNotFoundError`

**Solutions**:

1. **Check collection exists**:
```python
collections = client.get_collections()
print([c.name for c in collections.collections])
```

2. **Create collection if missing**:
```python
try:
    client.get_collection(collection_name="products_text")
except Exception:
    client.create_collection(
        collection_name="products_text",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
```

### Issue: Connection Refused

**Problem**: Cannot connect to Qdrant

**Solutions**:

1. **Check Qdrant is running**:
```bash
docker ps | grep qdrant
curl http://localhost:6333/health
```

2. **Verify ports**:
```bash
lsof -i :6333
lsof -i :6334
```

3. **Check firewall**:
```bash
# Linux
sudo ufw allow 6333/tcp
sudo ufw allow 6334/tcp

# Docker networking
docker network inspect rag-enterprise_default
```

### Issue: Incorrect Search Results

**Problem**: Low similarity scores or irrelevant results

**Solutions**:

1. **Verify embedding dimensions**:
```python
collection_info = client.get_collection("products_text")
expected_dim = collection_info.config.params.vectors.size
print(f"Expected: {expected_dim}, Got: {len(query_embedding)}")
```

2. **Check distance metric**:
```python
# Cosine: Use for normalized embeddings (most common)
# Euclidean: Use for non-normalized embeddings
# Dot: Use for specific algorithms

distance = collection_info.config.params.vectors.distance
print(f"Distance metric: {distance}")
```

3. **Normalize embeddings** (if using Cosine):
```python
import numpy as np

def normalize_embedding(embedding: List[float]) -> List[float]:
    """Normalize to unit length"""
    arr = np.array(embedding)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return embedding
    return (arr / norm).tolist()

query_embedding = normalize_embedding(raw_embedding)
```

---

## Best Practices

### 1. Collection Design

**Do**:
- ✅ Separate collections for different embedding types (text, image, shape)
- ✅ Use meaningful collection names (`products_text` not `collection1`)
- ✅ Index frequently filtered fields
- ✅ Use quantization for large collections (> 100K vectors)

**Don't**:
- ❌ Mix different embedding dimensions in one collection
- ❌ Store large payloads (> 1KB) - use external storage
- ❌ Create too many collections (> 100) - merge similar ones

### 2. Payload Design

**Do**:
- ✅ Keep payloads small (< 1KB)
- ✅ Use simple types (string, int, float, bool)
- ✅ Index filter fields
- ✅ Store product_id for joining

**Don't**:
- ❌ Store full documents (use external DB)
- ❌ Store large arrays or nested objects
- ❌ Use complex data types

### 3. Search Strategy

**Do**:
- ✅ Use filters to reduce search space
- ✅ Limit results (top_k=5-10)
- ✅ Cache frequent queries
- ✅ Use gRPC for production

**Don't**:
- ❌ Search entire collection without filters
- ❌ Request too many results (> 100)
- ❌ Run searches synchronously in loops

### 4. Performance

**Do**:
- ✅ Batch upsert operations
- ✅ Use connection pooling
- ✅ Enable quantization for large datasets
- ✅ Monitor latency and memory

**Don't**:
- ❌ Insert one vector at a time
- ❌ Create new client for each request
- ❌ Skip optimization checks

---

## References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Python Client API](https://github.com/qdrant/qdrant-client)
- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)
- [Vector Search Best Practices](https://qdrant.tech/articles/vector-search-best-practices/)

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
