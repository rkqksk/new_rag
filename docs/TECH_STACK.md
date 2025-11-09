# RAG Enterprise - Complete Technology Stack Documentation

**Version**: v4.0.0 + NexaAI Integration
**Last Updated**: 2025-11-08
**Python Version**: 3.11+

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Backend Technologies](#backend-technologies)
3. [Database Layer](#database-layer)
4. [AI/ML Stack](#aiml-stack)
5. [OCR & Image Processing](#ocr--image-processing)
6. [Frontend Technologies](#frontend-technologies)
7. [Infrastructure](#infrastructure)
8. [MCP Servers](#mcp-servers)
9. [Testing & Quality](#testing--quality)
10. [Monitoring & Observability](#monitoring--observability)
11. [Development Tools](#development-tools)

---

## 🎯 Overview

RAG Enterprise is a production-ready Retrieval-Augmented Generation system built with modern Python technologies, featuring:

- **Dual-engine LLM routing** (NexaAI + Ollama)
- **Multi-modal RAG** (text, images, documents)
- **Advanced OCR pipeline** (PaddleOCR, EasyOCR, Tesseract)
- **Vector search** (Qdrant)
- **Real-time caching** (Redis)
- **Microservices architecture** (Docker, MCP)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  HTML/CSS/JS (chat.html) + Dashboard (rag_dashboard.html)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│    18 REST Endpoints + WebSocket + Admin API + Debug API   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Service Layer                          │
│  Search • Personalization • Analytics • Unified LLM         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   LLM Routing Layer                          │
│         NexaAI (Fast) ←→ Router ←→ Ollama (Quality)        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data & Storage Layer                      │
│   Qdrant (Vectors) • Redis (Cache) • PostgreSQL (DB)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend Technologies

### FastAPI (0.104.1)

**Purpose**: Modern, high-performance Python web framework for building APIs

**Why FastAPI?**
- ✅ **Async Support**: Native asyncio support for concurrent requests
- ✅ **Auto Documentation**: OpenAPI/Swagger UI auto-generation
- ✅ **Type Safety**: Pydantic integration for validation
- ✅ **Performance**: Comparable to Node.js and Go
- ✅ **Developer Experience**: Intuitive API, less boilerplate

**Key Features Used**:
- Dependency injection
- Background tasks
- WebSocket support
- CORS middleware
- Exception handlers

**Configuration**: `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG Enterprise API",
    version="4.0.0",
    description="Production-ready RAG system with NexaAI integration"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Performance Metrics**:
- Request latency: < 100ms (simple queries)
- Throughput: ~1000 req/s (single worker)
- Memory: ~200MB base + ~500MB with models

**References**:
- [Official Docs](https://fastapi.tiangolo.com/)
- Project: `docs/technologies/backend.md`

---

### Uvicorn (0.24.0)

**Purpose**: Lightning-fast ASGI server

**Features**:
- HTTP/1.1 and HTTP/2 support
- WebSocket support
- Graceful shutdown
- Auto-reload in development

**Production Configuration**:
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 4 \
  --loop uvloop \
  --log-level info
```

---

### Pydantic (2.5.0)

**Purpose**: Data validation and settings management

**Why Pydantic v2?**
- ✅ **50% faster** than v1
- ✅ **Better type hints** with TypeAdapter
- ✅ **JSON Schema** generation
- ✅ **Strict mode** for validation

**Usage Examples**:

```python
from pydantic import BaseModel, Field, validator

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict | None = None

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
```

---

## 💾 Database Layer

### Qdrant (v1.7.0)

**Purpose**: Vector database for semantic search

**Why Qdrant?**
- ✅ **Fast**: Written in Rust, ~10ms query latency
- ✅ **Scalable**: Handles billions of vectors
- ✅ **Filters**: Rich metadata filtering
- ✅ **Cloud-native**: Kubernetes-ready
- ✅ **Python SDK**: Excellent client library

**Current Stats**:
- **Vectors**: 3,246 (atomic chunks)
- **Dimension**: 384 (all-MiniLM-L6-v2)
- **Collections**: 3 (text, images, shapes)
- **Index**: HNSW (M=16, ef_construct=100)

**Configuration**:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(
    host="localhost",
    port=6333,
    timeout=10.0
)

# Create collection
client.create_collection(
    collection_name="products",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE
    )
)
```

**Performance Tuning**:
- HNSW parameters: `M=16`, `ef_construct=100`
- Payload indexing: keyword fields
- Quantization: scalar (4x storage reduction)

**References**:
- [Official Docs](https://qdrant.tech/documentation/)
- Project: `docs/technologies/vector-database.md`

---

### Redis (7-alpine)

**Purpose**: In-memory cache and session store

**Why Redis?**
- ✅ **Speed**: Sub-millisecond latency
- ✅ **Data structures**: Strings, hashes, lists, sets
- ✅ **Persistence**: RDB + AOF
- ✅ **Pub/Sub**: Real-time messaging

**Usage in Project**:
- Query result caching (TTL: 5 minutes)
- User session management
- Rate limiting
- Real-time analytics

**Configuration**:

```python
import redis.asyncio as redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    max_connections=50
)

# Cache example
await redis_client.setex(
    f"search:{query_hash}",
    300,  # 5 minutes
    json.dumps(results)
)
```

**Cache Hit Rate**: ~35% (based on logs)

---

### PostgreSQL (15-alpine)

**Purpose**: Relational database for structured data

**Schema**:
- `users` - User accounts and preferences
- `queries` - Search query logs
- `feedback` - User feedback on results
- `analytics` - Aggregated metrics

**Key Features Used**:
- JSONB for flexible schemas
- Full-text search (tsvector)
- Async queries (asyncpg)
- Connection pooling

**Configuration**:

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/rag_enterprise",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

---

## 🤖 AI/ML Stack

### NexaAI (Latest)

**Purpose**: Fast local LLM inference

**Models Used**:
- `Qwen3-1.7B` - Simple queries (< 500ms)
- `Qwen3-VL-4B-Instruct` - Vision + medium complexity

**Why NexaAI?**
- ✅ **Speed**: 3-5x faster than Ollama for simple queries
- ✅ **Local**: No API keys, runs on NPU/GPU/CPU
- ✅ **Vision**: Built-in vision-language models
- ✅ **OpenAI Compatible**: Drop-in replacement

**Performance**:
| Model | Latency | Throughput | Use Case |
|-------|---------|------------|----------|
| Qwen3-1.7B | < 500ms | ~100 tok/s | Simple lookup |
| Qwen3-VL-4B | < 1s | ~60 tok/s | Vision + medium |

**Configuration**: See `docs/technologies/llm-engines.md`

---

### Ollama (qwen2.5:7b-instruct)

**Purpose**: High-quality LLM for complex reasoning

**Why Ollama?**
- ✅ **Quality**: Better reasoning than smaller models
- ✅ **Local**: Privacy-first, no cloud
- ✅ **Easy**: Simple CLI, Docker support
- ✅ **Models**: Access to 100+ models

**Model Details**:
- **Size**: 4.7GB (quantized)
- **Context**: 32K tokens
- **Latency**: ~2s (complex queries)

**Usage**:

```python
import ollama

response = ollama.generate(
    model='qwen2.5:7b-instruct',
    prompt=prompt,
    stream=True
)
```

**References**: `docs/technologies/llm-engines.md`

---

### Sentence Transformers (2.2.2)

**Purpose**: Text embeddings for semantic search

**Model**: `all-MiniLM-L6-v2`
- **Dimension**: 384
- **Speed**: ~500 sentences/sec (CPU)
- **Quality**: 0.82 avg similarity on test set

**Why this model?**
- ✅ **Balanced**: Good quality/speed tradeoff
- ✅ **Small**: 80MB model size
- ✅ **Multilingual**: Supports Korean + English

**Usage**:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode([
    "50ml PET 용기",
    "100ml PP 반투명 용기"
])
# Output: (2, 384) numpy array
```

---

### PyTorch (2.1.1)

**Purpose**: Deep learning framework

**Used For**:
- Sentence Transformers backend
- Custom embedding models (future)
- ONNX export (optimization)

**Configuration**:
```python
import torch

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Inference mode (no gradients)
with torch.inference_mode():
    embeddings = model.encode(texts)
```

---

## 📸 OCR & Image Processing

### Multi-Engine OCR Pipeline

**Strategy**: Waterfall approach with 3 engines

```
Input Document
    ↓
[PaddleOCR] (Primary, GPU-accelerated)
    ↓ (if confidence < 0.8)
[EasyOCR] (Fallback, better for complex layouts)
    ↓ (if confidence < 0.6)
[Tesseract] (Final fallback, best for printed text)
    ↓
Structured Output
```

---

### PaddleOCR (2.7.0.3)

**Purpose**: Primary OCR engine

**Why PaddleOCR?**
- ✅ **Accuracy**: 95%+ on Korean text
- ✅ **Speed**: GPU acceleration, 10 images/sec
- ✅ **Multilingual**: 80+ languages
- ✅ **Layout**: Table detection, angle correction

**Configuration**:

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,  # Angle detection
    lang='korean',
    use_gpu=True,
    show_log=False
)

result = ocr.ocr(image_path, cls=True)
```

**Performance**: ~100ms per image (GPU)

---

### EasyOCR (1.7.0)

**Purpose**: Fallback OCR for complex layouts

**Features**:
- Better paragraph detection
- Good for mixed Korean/English
- Handles rotated text

**Usage**:

```python
import easyocr

reader = easyocr.Reader(['ko', 'en'], gpu=True)
result = reader.readtext(image_path)
```

---

### Pytesseract (0.3.10)

**Purpose**: Final fallback for printed text

**Best For**:
- Clean printed documents
- High-contrast text
- Standard fonts

---

### OpenCV (4.8.1.78)

**Purpose**: Image preprocessing

**Operations**:
- Resize, rotate, crop
- Noise removal (Gaussian blur)
- Contrast enhancement (CLAHE)
- Binarization (Otsu's method)

**Example**:

```python
import cv2

# Preprocess for better OCR
img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
img = cv2.GaussianBlur(img, (5, 5), 0)
img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
```

**References**: `docs/technologies/ocr-pipeline.md`

---

## 🎨 Frontend Technologies

### Vanilla HTML/CSS/JavaScript

**Purpose**: Lightweight, fast, no build step

**Files**:
- `chat.html` (32KB) - Main chat interface
- `dashboard.html` (16KB) - Analytics dashboard
- `rag_dashboard.html` (13KB) - RAG-specific metrics

**Why No Framework?**
- ✅ **Performance**: Zero bundle size, instant load
- ✅ **Simplicity**: No build tools, easy to debug
- ✅ **Compatibility**: Works everywhere
- ✅ **Maintainability**: Less dependencies

**Features**:
- Real-time chat with WebSocket
- Markdown rendering
- Syntax highlighting (code blocks)
- Responsive design (mobile-first)
- Dark mode support

**Tech Stack**:
- Fetch API for HTTP requests
- WebSocket for real-time updates
- CSS Grid + Flexbox for layout
- LocalStorage for user preferences

**References**: `docs/technologies/frontend.md`

---

## 🏗️ Infrastructure

### Docker & Docker Compose

**Purpose**: Container orchestration

**Services**:
```yaml
services:
  postgres:    # PostgreSQL 15
  redis:       # Redis 7
  qdrant:      # Qdrant v1.7.0
  api:         # FastAPI application
```

**Production Configuration**:
- Multi-stage builds (optimization)
- Health checks for all services
- Volume mounts for persistence
- Network isolation

**Build**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**References**: `docs/technologies/infrastructure.md`

---

### Kubernetes (Optional)

**Purpose**: Production orchestration

**Manifests**:
- `k8s/deployment.yaml` - API deployment
- `k8s/service.yaml` - Load balancer
- `k8s/configmap.yaml` - Configuration
- `k8s/secret.yaml` - Sensitive data

**Features**:
- Auto-scaling (HPA)
- Rolling updates
- Health checks
- Resource limits

---

## 🔌 MCP Servers

### What are MCP Servers?

**MCP (Model Context Protocol)**: Standardized way to expose tools to LLMs

**Available Servers** (6 total):
1. `filesystem` - File system access
2. `chrome_devtools` - Browser automation
3. `qdrant` - Vector database operations
4. `ollama` - Local LLM server
5. `rag-orchestrator` - RAG pipeline
6. `query-router` - Model routing

**Configuration**: `.mcp.json`

```json
{
  "mcpServers": {
    "qdrant": {
      "command": "python3",
      "args": ["-m", "mcp_servers.qdrant_server"],
      "env": {
        "PYTHONPATH": "${PWD}"
      }
    }
  }
}
```

**References**: `docs/technologies/mcp-servers.md`

---

## ✅ Testing & Quality

### Pytest (7.4.3)

**Purpose**: Testing framework

**Test Coverage**:
- Unit tests: 122 test cases
- Integration tests: 32 test cases (NexaAI)
- E2E tests: 4 test cases
- **Coverage**: 95%+ target

**Plugins**:
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support

**Running Tests**:

```bash
# All tests
pytest tests/ -v --cov=src --cov=app

# Specific module
pytest tests/test_nexa_service.py -v

# With coverage report
pytest --cov --cov-report=html
```

**References**: `docs/technologies/testing.md`

---

### Code Quality Tools

**Black (23.11.0)**: Code formatter
```bash
black src/ app/ tests/
```

**Ruff (0.1.6)**: Fast linter
```bash
ruff check src/ app/
```

**MyPy (1.7.1)**: Static type checker
```bash
mypy src/ app/
```

---

## 📊 Monitoring & Observability

### Prometheus (0.19.0)

**Purpose**: Metrics collection

**Metrics Exposed**:
- Request latency (histogram)
- Request count (counter)
- Active connections (gauge)
- Error rate (counter)
- Cache hit rate (gauge)

**Endpoint**: `http://localhost:8001/metrics`

---

### Logging (python-json-logger)

**Purpose**: Structured logging

**Format**: JSON for easy parsing

```python
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter())

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

**Log Levels**:
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical issues

---

## 🛠️ Development Tools

### Additional Libraries

**HTTP Clients**:
- `httpx` (0.25.2) - Async HTTP client
- `aiohttp` (3.9.1) - Alternative async client

**Data Processing**:
- `pandas` (2.1.4) - Data analysis
- `openpyxl` (3.1.2) - Excel files
- `PyMuPDF` (1.23.8) - PDF processing

**Image Processing**:
- `Pillow` (10.1.0) - Image manipulation
- `scikit-image` (0.22.0) - Image algorithms

---

## 📚 Complete Technology Matrix

| Category | Technology | Version | Purpose | Status |
|----------|-----------|---------|---------|--------|
| **Backend** | FastAPI | 0.104.1 | Web framework | ✅ Prod |
| | Uvicorn | 0.24.0 | ASGI server | ✅ Prod |
| | Pydantic | 2.5.0 | Data validation | ✅ Prod |
| **Database** | Qdrant | v1.7.0 | Vector DB | ✅ Prod |
| | Redis | 7-alpine | Cache | ✅ Prod |
| | PostgreSQL | 15-alpine | Relational DB | ✅ Prod |
| **AI/ML** | NexaAI | Latest | Fast LLM | ✅ Prod |
| | Ollama | qwen2.5:7b | Quality LLM | ✅ Prod |
| | Sentence Transformers | 2.2.2 | Embeddings | ✅ Prod |
| | PyTorch | 2.1.1 | DL framework | ✅ Prod |
| **OCR** | PaddleOCR | 2.7.0.3 | Primary OCR | ✅ Prod |
| | EasyOCR | 1.7.0 | Fallback OCR | ✅ Prod |
| | Pytesseract | 0.3.10 | Final fallback | ✅ Prod |
| | OpenCV | 4.8.1.78 | Image processing | ✅ Prod |
| **Frontend** | HTML/CSS/JS | - | UI | ✅ Prod |
| **Infrastructure** | Docker | Latest | Containers | ✅ Prod |
| | Docker Compose | v3.8 | Orchestration | ✅ Prod |
| | Kubernetes | v1.28+ | Production | 📋 Optional |
| **Testing** | Pytest | 7.4.3 | Test framework | ✅ Prod |
| | Pytest-asyncio | 0.21.1 | Async tests | ✅ Prod |
| **Monitoring** | Prometheus | 0.19.0 | Metrics | ✅ Prod |
| | JSON Logger | 2.0.7 | Logging | ✅ Prod |

---

## 🎯 Technology Selection Principles

### Why These Technologies?

1. **Performance First**
   - FastAPI: Fastest Python web framework
   - Qdrant: Rust-based vector DB
   - Redis: In-memory cache

2. **Developer Experience**
   - Type safety (Pydantic, MyPy)
   - Auto documentation (FastAPI)
   - Easy testing (pytest)

3. **Production Ready**
   - Battle-tested libraries
   - Active maintenance
   - Strong community support

4. **Cost Effective**
   - Open source
   - Local deployment
   - No API costs (NexaAI, Ollama)

5. **Scalability**
   - Async I/O (FastAPI, asyncpg)
   - Horizontal scaling (K8s)
   - Efficient caching (Redis)

---

## 📖 Detailed Documentation

For in-depth information on each technology:

- **Backend**: `docs/technologies/backend.md`
- **Vector Database**: `docs/technologies/vector-database.md`
- **LLM Engines**: `docs/technologies/llm-engines.md`
- **OCR Pipeline**: `docs/technologies/ocr-pipeline.md`
- **Frontend**: `docs/technologies/frontend.md`
- **Infrastructure**: `docs/technologies/infrastructure.md`
- **MCP Servers**: `docs/technologies/mcp-servers.md`
- **Testing**: `docs/technologies/testing.md`
- **Monitoring**: `docs/technologies/monitoring.md`

---

**Version**: v4.0.0 + NexaAI Integration
**Last Updated**: 2025-11-08
**Maintained by**: RAG Enterprise Team
