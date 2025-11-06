# Multi-Modal RAG Components

**Phase 4.4 - Multi-Modal Integration**
**Status**: Week 3 Complete ✅

---

## Overview

Unified multi-modal embedding service with Qdrant integration for text, image, and shape embeddings.

**Supported Modalities**:
- ✅ **Text**: Sentence Transformers (384-dim) - Production Ready
- ✅ **Image**: OpenCLIP ViT-H-14 (1024-dim) - Production Ready
- 📋 **Shape**: Custom descriptors (128-dim) - Phase 6

**Qdrant Integration**: ✅
- Named vectors (text/image/shape)
- Multi-vector upload and search
- Batch processing
- Data migration tools

---

## Quick Start

### Installation

```bash
# Core dependencies
pip install torch sentence-transformers qdrant-client

# Image support (optional)
pip install open_clip_torch

# Shape support (Phase 6)
pip install opencv-python rembg

# Progress bar for batch operations
pip install tqdm
```

### Basic Usage

```python
from src.core.multimodal import MultiModalEmbeddingService

# Initialize (text only)
embedder = MultiModalEmbeddingService(enable_image=False)

# Text embedding
text_emb = embedder.embed_text("20파이 캡 5000개")
print(f"Text: {len(text_emb)}-dim")  # 384-dim

# Batch embedding
texts = ["20파이 캡", "100ml PET 보틀", "화장품 용기"]
embeddings = embedder.embed_texts_batch(texts)
print(f"Batch: {len(embeddings)} embeddings")
```

### With Image Support

```python
# Initialize with image support
embedder = MultiModalEmbeddingService(enable_image=True)

# Multi-modal embedding
result = embedder.embed(
    text="100ml PET Bottle",
    image="product.jpg"
)

print(result.keys())  # dict_keys(['text', 'image'])
print(f"Text: {len(result['text'])}-dim")    # 384
print(f"Image: {len(result['image'])}-dim")  # 1024
```

### Batch Multi-Modal

```python
items = [
    {"text": "제품 A", "image": "a.jpg"},
    {"text": "제품 B", "image": "b.jpg"},
    {"text": "제품 C", "image": "c.jpg"}
]

embeddings = embedder.embed_batch(items)

for i, emb in enumerate(embeddings):
    print(f"Item {i+1}: {list(emb.keys())}")
```

---

## Features

### GPU Acceleration

Auto-detects best available device:
- **Mac M4**: MPS (Metal Performance Shaders)
- **NVIDIA GPU**: CUDA
- **Fallback**: CPU

```python
# Auto-detect (default)
embedder = MultiModalEmbeddingService(device='auto')

# Force specific device
embedder = MultiModalEmbeddingService(device='mps')  # or 'cuda', 'cpu'
```

### Batch Processing

Optimized for large-scale processing:

```python
# 1000 texts in batches
texts = [f"Product {i}" for i in range(1000)]
embeddings = embedder.embed_texts_batch(
    texts,
    batch_size=32,        # Adjust for GPU memory
    show_progress=True    # Progress bar
)
```

### Embedding Dimensions

```python
dims = embedder.get_dimensions()
# {'text': 384, 'image': 1024}
```

### Modality Availability

```python
embedder.is_available('text')   # True (always)
embedder.is_available('image')  # True if OpenCLIP installed
embedder.is_available('shape')  # False (Phase 6)
```

---

## Architecture

```
MultiModalEmbeddingService
├── Text Embedder (Sentence Transformers)
│   ├── Model: all-MiniLM-L6-v2
│   ├── Dimension: 384
│   └── Methods: embed_text(), embed_texts_batch()
│
├── Image Embedder (OpenCLIP)
│   ├── Model: ViT-H-14
│   ├── Dimension: 1024
│   └── Methods: embed_image(), embed_images_batch()
│
└── Shape Embedder (Phase 6)
    ├── Model: Custom (Hu Moments + Fourier)
    ├── Dimension: 128
    └── Status: Not yet implemented
```

---

## Performance

### Latency (Single Item)

| Modality | Device | Latency |
|----------|--------|---------|
| Text | CPU | ~50ms |
| Text | GPU | ~10ms |
| Image | CPU | ~500ms |
| Image | GPU | ~50ms |

### Throughput (Batch)

| Modality | Batch Size | Device | Throughput |
|----------|-----------|--------|------------|
| Text | 32 | GPU | ~640 items/s |
| Image | 8 | GPU | ~160 items/s |

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/test_multimodal_embedder.py -v

# Run specific test
pytest tests/test_multimodal_embedder.py::test_text_embedding_single -v

# Run with coverage
pytest tests/test_multimodal_embedder.py --cov=src.core.multimodal
```

### Demo Script

```bash
# Interactive demo
python scripts/demo_multimodal.py
```

---

## Integration

### With Qdrant (Week 2) ✅

#### Setup Collection

```bash
# Create multi-modal collection with named vectors
python scripts/create_multimodal_collection.py

# Options
python scripts/create_multimodal_collection.py \
  --host localhost \
  --port 6333 \
  --collection products_multimodal \
  --recreate  # Delete if exists
```

#### Upload with MultiModalQdrantUploader

```python
from qdrant_client import QdrantClient
from src.core.multimodal import MultiModalEmbeddingService, MultiModalQdrantUploader

# Initialize
embedder = MultiModalEmbeddingService()
client = QdrantClient(host="localhost", port=6333)
uploader = MultiModalQdrantUploader(client, "products_multimodal")

# Generate embeddings
text_emb = embedder.embed_text("100ml PET Bottle")
image_emb = embedder.embed_image("bottle.jpg")

# Upload single product
uploader.upload_product(
    product_id="BOTTLE-001",
    text_embedding=text_emb,
    image_embedding=image_emb,
    payload={
        "product_name": "100ml PET Bottle",
        "category": "Bottle",
        "specifications": {"capacity": "100ml"}
    }
)

# Batch upload
products = [
    {
        "product_id": "BOTTLE-002",
        "text_embedding": embedder.embed_text("200ml PET Bottle"),
        "payload": {"name": "200ml Bottle"}
    },
    # ... more products
]
stats = uploader.upload_batch(products)
print(f"Uploaded {stats['success']}/{stats['total']}")
```

#### Search with Named Vectors

```python
# Text-only search
results = client.search(
    collection_name="products_multimodal",
    query_vector=("text", text_query_emb),  # Named vector
    limit=10
)

# Image-only search
results = client.search(
    collection_name="products_multimodal",
    query_vector=("image", image_query_emb),  # Named vector
    limit=10
)
```

#### Migrate Existing Data

```bash
# Migrate from single-vector to multi-vector collection
python scripts/migrate_to_multimodal.py \
  --source products_atomic \
  --target products_multimodal \
  --vector-name text \
  --batch-size 100

# Dry run (preview only)
python scripts/migrate_to_multimodal.py --dry-run
```

#### End-to-End Demo

```bash
# Full integration demo (embeddings + upload + search)
python scripts/demo_week2_integration.py
```

### With HybridSearchEngine (Week 3) ✅

#### Basic Hybrid Search

```python
from qdrant_client import QdrantClient
from src.core.multimodal import MultiModalEmbeddingService, HybridSearchEngine

# Initialize
embedder = MultiModalEmbeddingService()
client = QdrantClient(host="localhost", port=6333)

# Create hybrid search engine
engine = HybridSearchEngine(
    client,
    collection_name="products_multimodal",
    fusion_strategy="rrf"  # or "weighted", "learned"
)

# Generate embeddings
text_emb = embedder.embed_text("100ml PET Bottle")
image_emb = embedder.embed_image("bottle.jpg")

# Hybrid search
results = engine.search_hybrid(
    embeddings={"text": text_emb, "image": image_emb},
    limit=10
)

# Print results
for result in results:
    print(f"{result.rank}. {result.product_id}")
    print(f"   Score: {result.score:.4f}")
    print(f"   Text score: {result.modality_scores['text']:.4f}")
    print(f"   Image score: {result.modality_scores['image']:.4f}")
```

#### Fusion Strategies

**1. RRF (Reciprocal Rank Fusion)** ⭐ Recommended

```python
# Robust, no tuning required
engine = HybridSearchEngine(
    client,
    "products_multimodal",
    fusion_strategy="rrf",
    rrf_k=60
)

results = engine.search_hybrid(
    embeddings={"text": text_emb, "image": image_emb},
    limit=10
)
```

**Benefits:**
- No score normalization needed
- Robust to score scale differences
- No hyperparameter tuning required
- Works well in most scenarios

**2. Weighted Fusion**

```python
# Custom weights for each modality
engine = HybridSearchEngine(
    client,
    "products_multimodal",
    fusion_strategy="weighted"
)

# Text-heavy search
results = engine.search_hybrid(
    embeddings={"text": text_emb, "image": image_emb},
    weights={"text": 0.7, "image": 0.3},
    limit=10
)

# Image-heavy search
results = engine.search_hybrid(
    embeddings={"text": text_emb, "image": image_emb},
    weights={"text": 0.3, "image": 0.7},
    limit=10
)
```

**Benefits:**
- Simple and interpretable
- Fine control over modality importance
- Good for domain-specific tuning

**3. Learned Fusion**

```python
# ML-based fusion (requires trained model)
engine = HybridSearchEngine(
    client,
    "products_multimodal",
    fusion_strategy="learned"
)

results = engine.search_hybrid(
    embeddings={"text": text_emb, "image": image_emb},
    limit=10
)
```

**Benefits:**
- Optimal fusion learned from data
- Adapts to user behavior
- Best accuracy (when trained properly)

**Note:** Currently falls back to weighted fusion. Training requires relevance labels.

#### Single Modality Search

```python
# Text-only search
results = engine.search_text(text_emb, limit=10)

# Image-only search
results = engine.search_image(image_emb, limit=10)

# Shape-only search (Phase 6)
results = engine.search_shape(shape_emb, limit=10)
```

#### Result Explanation

```python
# Search
results = engine.search_hybrid(
    embeddings={"text": text_emb, "image": image_emb},
    limit=10
)

# Explain top results
explanation = engine.explain_results(results, top_k=3)

print(f"Fusion strategy: {explanation['fusion_strategy']}")
for result_info in explanation['results']:
    print(f"\nRank {result_info['rank']}: {result_info['product_id']}")
    print(f"Final score: {result_info['final_score']:.4f}")

    # Modality contributions
    for modality, contrib in result_info['modality_contributions'].items():
        print(f"  {modality}: {contrib['contribution_pct']:.1f}%")
```

#### Demo Script

```bash
# Interactive demo with 7 scenarios
python scripts/demo_week3_hybrid_search.py
```

### With OCR Pipeline (Week 4)

```python
from src.core.ocr_processors.ocr_pipeline import OCRPipeline
from src.core.multimodal import MultiModalEmbeddingService

ocr = OCRPipeline()
embedder = MultiModalEmbeddingService()

# Process PDF
ocr_result = await ocr.process_document("catalog.pdf")

# Generate embeddings
embeddings = embedder.embed(
    text=ocr_result.text,
    image=ocr_result.images[0] if ocr_result.images else None
)
```

---

## Models

### Text Models (Sentence Transformers)

| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| **all-MiniLM-L6-v2** ⭐ | 384 | ⚡⚡⚡ | 🎯🎯 | **Production** (current) |
| all-mpnet-base-v2 | 768 | ⚡⚡ | 🎯🎯🎯 | High accuracy |
| multilingual-e5-large | 1024 | ⚡ | 🎯🎯🎯 | Best Korean support |

### Image Models (OpenCLIP)

| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| **ViT-H-14** ⭐ | 1024 | ⚡⚡ | 🎯🎯🎯 | **Production** (current) |
| ViT-B/32 | 512 | ⚡⚡⚡ | 🎯🎯 | Lightweight |
| ViT-L-14 | 768 | ⚡⚡ | 🎯🎯🎯 | Alternative |

---

## Roadmap

### ✅ Week 1 (Complete)
- [x] MultiModalEmbeddingService class
- [x] Text embedding (Sentence Transformers)
- [x] Image embedding (OpenCLIP)
- [x] Batch processing
- [x] GPU optimization
- [x] Unit tests
- [x] Demo script

### ✅ Week 2 (Complete)
- [x] Qdrant multi-vector collection setup
- [x] MultiModalQdrantUploader
- [x] Data migration script
- [x] Integration tests
- [x] Named vector search support
- [x] Batch upload optimization
- [x] Collection management tools

### ✅ Week 3 (Complete)
- [x] HybridSearchEngine class
- [x] Fusion strategies (Weighted, RRF, Learned)
- [x] Single modality search methods
- [x] Result explanation with modality contributions
- [x] Performance benchmarking
- [x] Integration tests (20+ test cases)
- [x] Demo script with 7 scenarios
- [x] Cross-encoder re-ranker (placeholder for production)

### 📋 Week 4
- [ ] OCR pipeline integration
- [ ] End-to-end testing
- [ ] Caching layer integration
- [ ] Production deployment

---

## Dependencies

```txt
# Core (required)
torch>=2.0.0
sentence-transformers>=2.2.0
qdrant-client>=1.7.0

# Progress bar (batch operations)
tqdm>=4.65.0

# Image support (optional)
open_clip_torch>=2.20.0
Pillow>=10.0.0

# Shape support (Phase 6)
opencv-python>=4.8.0
rembg>=2.0.0
```

---

## API Reference

### MultiModalEmbeddingService

```python
class MultiModalEmbeddingService:
    """Unified multi-modal embedding service"""

    def __init__(
        self,
        text_model: str = 'all-MiniLM-L6-v2',
        image_model: str = 'ViT-H-14',
        device: str = 'auto',
        enable_image: bool = True,
        enable_shape: bool = False
    )

    # Text methods
    def embed_text(self, text: str) -> List[float]
    def embed_texts_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]

    # Image methods
    def embed_image(self, image_path: Union[str, Path]) -> List[float]
    def embed_images_batch(self, image_paths: List[Union[str, Path]], batch_size: int = 8) -> List[List[float]]

    # Multi-modal methods
    def embed(self, text: Optional[str] = None, image: Optional[str] = None) -> Dict[str, List[float]]
    def embed_batch(self, items: List[Dict], batch_size: int = 32) -> List[Dict[str, List[float]]]

    # Utility methods
    def get_dimensions(self) -> Dict[str, int]
    def is_available(self, modality: str) -> bool
```

### HybridSearchEngine

```python
class HybridSearchEngine:
    """Hybrid search engine with fusion strategies"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str = "products_multimodal",
        fusion_strategy: Literal["weighted", "rrf", "learned"] = "rrf",
        rrf_k: int = 60
    )

    # Single modality search
    def search_text(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ScoredPoint]

    def search_image(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ScoredPoint]

    def search_shape(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ScoredPoint]

    # Hybrid search
    def search_hybrid(
        self,
        embeddings: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        retrieve_limit: int = None
    ) -> List[SearchResult]

    # Hybrid search with re-ranking
    def search_hybrid_with_rerank(
        self,
        embeddings: Dict[str, List[float]],
        query_text: str,
        weights: Optional[Dict[str, float]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        rerank_top_k: int = 50
    ) -> List[SearchResult]

    # Result explanation
    def explain_results(
        self,
        results: List[SearchResult],
        top_k: int = 5
    ) -> Dict[str, Any]
```

### SearchResult

```python
@dataclass
class SearchResult:
    """Search result with multi-modal scores"""
    product_id: str
    score: float
    payload: Dict[str, Any]
    modality_scores: Dict[str, float]  # Individual scores per modality
    rank: int
```

---

## Troubleshooting

### Issue: ModuleNotFoundError: torch

```bash
# Install PyTorch
pip install torch

# For Mac M4 (MPS support)
pip install torch torchvision torchaudio

# For CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: OpenCLIP not available

```bash
# Install OpenCLIP
pip install open_clip_torch

# Verify
python -c "import open_clip; print(open_clip.list_pretrained())"
```

### Issue: Out of memory (GPU)

```python
# Reduce batch size
embeddings = embedder.embed_texts_batch(texts, batch_size=16)  # Default: 32

# Or use CPU
embedder = MultiModalEmbeddingService(device='cpu')
```

---

## Examples

See:
- `scripts/demo_multimodal.py` - Week 1: Embedding demo
- `scripts/demo_week2_integration.py` - Week 2: Qdrant integration
- `scripts/demo_week3_hybrid_search.py` - Week 3: Hybrid search ⭐
- `tests/test_multimodal_embedder.py` - Unit tests (embeddings)
- `tests/test_qdrant_uploader.py` - Integration tests (Qdrant)
- `tests/test_hybrid_search.py` - Integration tests (hybrid search)
- `docs/MULTIMODAL_RAG_STRATEGY.md` - Complete strategy

---

**Version**: 1.3.0 (Phase 4.4 Week 3)
**Status**: Hybrid Search Ready ✅
**Next**: Week 4 - OCR Integration
