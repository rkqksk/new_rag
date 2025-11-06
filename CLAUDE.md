# RAG Enterprise - Quick Reference (Symbolized)

**Production-grade RAG with SKILL-based architecture, multi-model support, vector search.**

> **Symbol System**: Use `§{category}.{document}.{section}` for detailed references.
> See: `docs/SYMBOL_SYSTEM.md` for complete symbol map.

---

## 🎯 Core Commands

```bash
# Quick Access
/workflow document-processing
/workflow rag-query
/component skills
/guide development
```

---

## 🏗️ Architecture (Symbolized)

```
User → SKILL → Plugin → MCP → Result
```

| Layer | Location | Details |
|-------|----------|---------|
| SKILL | `.claude/skills/` | §arch.core.skills |
| Plugin | `plugins/` | §arch.core.plugins |
| MCP | `.mcp.json` | §arch.core.mcp |

**Full Architecture**: §arch.overview

---

## 🎨 Active SKILLs

| Skill | Status | Commands |
|-------|--------|----------|
| rag-pipeline | ✅ Phase 0-4 Complete | process, query, search |
| manufacturing-expert | ✅ | process, classify |
| packaging-expert | ✅ | process, classify |
| web-crawler-pipeline | ✅ | crawl, monitor |

**Details**: §arch.core.skills
**Roadmap**: See [ROADMAP.md](docs/ROADMAP.md) for Phase 5-9 plans

---

## 🔄 Session Protocol

### Start
```bash
git status && git branch
```

### Changes
1. TodoWrite if >2 steps
2. Run tests before commit
3. Update CHANGELOG.md

### End
- Git status clean
- Todos resolved
- Background processes killed

---

## 🎨 Frontend

**File**: `frontend/chat.html` (v2.0.0)
**Design**: ChatGPT-style gray tones, minimal

### Colors
```
Background: #ffffff
Text: #2d333a
Secondary: #f7f7f8
Border: #d1d5db
```

**Full Specs**: §ui.design

### API
```
POST /chat/create_session
POST /chat/query
```

### Run
```bash
cd frontend && python3 -m http.server 8080
open http://localhost:8080/chat.html
```

---

## 🔧 Common Commands

```bash
# Backend
python run_chat_server.py              # Start API (port 8001)
pytest tests/ -v --cov=src             # Run tests

# Frontend
cd frontend && python3 -m http.server 8080

# Docker
docker-compose up -d                   # Start services
colima start --cpu 4 --memory 8        # Start Colima

# Ollama (Fixed Models)
ollama list                            # Check models
# Production: qwen2.5:7b-instruct, nomic-embed-text
```

**Ollama Policy**: §ollama.production

---

## 📊 Tech Stack

- Python 3.11+, FastAPI
- Qdrant, PostgreSQL/pgvector
- Docker Compose, Redis
- Ollama (qwen2.5:7b-instruct)

**Details**: §tech.backend

---

## 📖 Symbol References

### When to Load Full Docs

| Task | Symbol | Load When |
|------|--------|-----------|
| Architecture work | §arch.* | System design, integration |
| RAG development | §rag.* | Vector search, embedding |
| OCR/Document processing | §ocr.* | PDF/Image extraction, parsing |
| Multi-Modal integration | §multimodal.* | Embedding, Image search, Hybrid search |
| Debug & observability | §debug.* | Debugging, profiling, monitoring |
| UI changes | §ui.* | Design updates, components |
| Model management | §ollama.* | Model updates, performance |
| Deployment | §deploy.* | Infrastructure setup |

### Quick Access (Expanded)

#### §rag - RAG System Status
**Status**: **Phase 0-4 Complete** ✅ Production-Ready (2025-11-06 업데이트)
**Next**: Phase 5-9 (Advanced RAG, Image Matching, Cloud Integration)

**§rag.status** - 완성된 Phase:
- ✅ **Phase 0**: Initial Setup (Docker, FastAPI, Frontend)
- ✅ **Phase 1**: Atomic Chunking (471 products → 3,246 chunks)
- ✅ **Phase 2**: Enhanced Field Extraction (Neck, MOQ, Material, Price)
- ✅ **Phase 3**: Search Optimization (0.79-0.82 quality)
- ✅ **Phase 4**: OCR Pipeline (Multi-engine, 7 modules, ~1,850 lines)

**§rag.core** - 완성된 Core 모듈:
- ✅ `src/core/product_classifier.py` - 제품 분류기 (Bottle/Jar/Cap/Pump)
- ✅ `src/core/chunk_templates.py` - 20+ 필드 타입 템플릿
- ✅ `src/core/category_templates.py` - 카테고리별 특화 템플릿
- ✅ `src/core/advanced_chunk_generator.py` - 통합 청킹 파이프라인
- ✅ `src/core/enhanced_field_extractor.py` ⭐ **NEW** - 강화된 필드 추출기
  - Bottle/Jar: `enriched_info` 기반 자동 추출
  - Cap/Pump: spec/detail/description 파싱
  - Neck, MOQ, Material, Price 추출
  - Composite fields (SPEC_COMPOSITE, BUSINESS_COMPOSITE)
- ✅ `src/core/query_parser.py` - 자연어 엔티티 추출기
- ✅ `src/core/search_engine.py` - 하이브리드 검색 엔진
- ✅ `src/core/natural_language_response.py` - 자연어 답변 생성기

**§rag.data** - 데이터 현황:
- ✅ **471 products** → **3,246 atomic chunks** (+56% from 2,073)
- ✅ Avg 6.9 chunks/product (enhanced field extraction)
- ✅ Collection: `products_atomic` @ Qdrant
- ✅ Search quality: **0.79-0.82 similarity** ⭐
- ✅ Model: sentence-transformers/all-MiniLM-L6-v2 (384 dim)

**§rag.infra** - 인프라:
- ✅ Colima (4 CPU, 8GB RAM)
- ✅ Qdrant v1.11.3 (http://localhost:6333)
- ✅ Ollama (qwen2.5:7b-instruct)

**§rag.roadmap** - 향후 계획 (Phase 5-9):
- 📋 Phase 5: Advanced RAG Integration Pipeline
- 📋 Phase 6: Image Matching Service (Shape Embedding)
- 📋 Phase 7: Cloud Data Integration
- 📋 Phase 8: Real-Time Streaming (SSE)
- 📋 Phase 9: Enterprise Deployment (K8s + CI/CD)

**Full Details**:
- [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - Current status
- [ROADMAP.md](docs/ROADMAP.md) - Phase 4-9 detailed plans (26KB)
- [MAIN_INTEGRATION_REPORT.md](docs/MAIN_INTEGRATION_REPORT.md) - Integration report

---

#### §arch - System Architecture
**Layers**: UI → API → Service → Core → Data
**Pipeline**: SKILL → Plugin → MCP

**§arch.core.layers**:
- SKILL: `.claude/skills/` (interface, triggers)
- Plugin: `plugins/` (business logic)
- MCP: `.mcp.json` (external services)

**§arch.core.skills** - 이미 구현된 모듈:
- `src/core/rag_pipeline.py` ✅ (완전한 RAG 파이프라인)
- `src/core/embedding_service.py` ✅ (Sentence Transformers)
- `src/core/document_loader.py` ✅
- `src/core/metadata_filter.py` ✅
- `src/core/response_generator.py` ✅

**Full Details**: docs/ARCHITECTURE.md (31KB)

---

#### §ui - Frontend UI/UX
**Version**: 2.0.0 (ChatGPT-style)
**Design**: Gray tones only, minimal, no header

**§ui.design.colors**:
- Background: `#ffffff`
- Text: `#2d333a` (primary), `#6e6e80` (secondary)
- Border: `#d1d5db`
- Hover: `#ececf1`

**§ui.design.layout**:
- Max width: 768px
- Full page chat
- Input at bottom
- Card grid: auto-fill 240px

**Full Details**: docs/FRONTEND_UI_POLICY.md (13KB)

---

#### §ollama - Model Management
**Production Models** (FIXED):
- `qwen2.5:7b-instruct` (4.7GB) - Main generation
- `nomic-embed-text` (274MB) - Embeddings

**§ollama.production**:
- 변경 금지 (Approval required)
- 삭제됨: qwen2.5:3b, qwen2.5:7b-instruct-q4_K_M
- Config: `config/ollama_models.yaml`

**Full Details**: docs/OLLAMA_MODEL_POLICY.md (6.5KB)

---

#### §ocr - OCR & Document Processing
**Status**: ✅ **COMPLETE** - Phase 4 Implemented (2025-11-06)
**Goal**: Production-grade OCR for PDF/Image → Structured data

**§ocr.implemented** - Complete OCR Pipeline (7 modules, ~1,850 lines):
- ✅ `src/core/ocr/image_preprocessor.py` (310 lines) - Deskew, denoise, CLAHE, binarization
- ✅ `src/core/ocr/ocr_engine.py` (450 lines) - Multi-engine with auto-fallback
- ✅ `src/core/ocr/pdf_extractor.py` (140 lines) - PyMuPDF-based PDF processing
- ✅ `src/core/ocr/excel_parser.py` (220 lines) - Excel/CSV + screenshot OCR
- ✅ `src/core/ocr/entity_recognizer.py` (190 lines) - Regex-based entity extraction
- ✅ `src/core/ocr/document_processor.py` (350 lines) - Unified processing layer
- ✅ `src/core/ocr/__init__.py` - Module exports

**§ocr.strategy** - Multi-Engine OCR Architecture:
- **Primary**: PaddleOCR (Korean, 85-90% accuracy, GPU-accelerated)
- **Fallback**: EasyOCR (complex fonts), Tesseract (last resort)
- **Table**: PP-Structure (table detection & extraction)
- **Layout**: LayoutLMv3 (document structure analysis)
- **Entity**: Pattern-based + NER (KoELECTRA fine-tuned)

**§ocr.pipeline** - Complete Processing Flow:
```
Image/PDF → Preprocessing → Multi-Engine OCR → Layout Analysis
  → Table Extraction → Entity Recognition → Validation → Chunks
```

**§ocr.engines** - Engine Selection Guide:
- Korean product catalogs → PaddleOCR ⭐ (fastest, most accurate)
- Artistic fonts/logos → EasyOCR (handles unusual fonts)
- Handwritten notes → TrOCR (transformer-based)
- Tables → PP-Structure (preserves structure)

**§ocr.entities** - Extracted Fields:
- Product code, Name, Category
- Specifications (capacity, neck, dimensions)
- Business info (MOQ, price, material)
- Pattern-based regex + NER model

**§ocr.usage** - Quick Start:
```bash
# Install PaddleOCR
pip install paddlepaddle paddleocr

# Basic usage
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='korean', use_gpu=True)
result = ocr.ocr("product_catalog.jpg")
```

**Full Details**:
- docs/OCR_PARSING_STRATEGY.md (50KB) - Complete architecture
- docs/OCR_QUICKSTART.md (30KB) - Practical examples
- `src/core/ocr/` - Production implementation

---

#### §debug - Debug & Observability System
**Status**: ✅ **COMPLETE** - Enterprise Debug System (2025-11-06)
**Goal**: Production debugging and observability

**§debug.implemented** - Complete Debug System (10 components):
- ✅ `app/core/config.py` - Enhanced DebugConfig with feature flags
- ✅ `app/core/logging.py` - ContextVar-based correlation IDs
- ✅ `app/core/exceptions.py` - Context-aware exceptions
- ✅ `app/middleware/request_tracing.py` - Request correlation IDs
- ✅ `app/middleware/performance_timing.py` - Performance tracking
- ✅ `app/middleware/request_logging.py` - Structured request logging
- ✅ `app/api/v1/debug.py` - 8 debug endpoints
- ✅ `app/core/query_logger.py` - In-memory query log (slow query detection)
- ✅ `app/core/profiler.py` - Checkpoint-based profiler with bottleneck detection
- ✅ `app/main.py` - Full integration with middleware stack

**§debug.features** - Debug Capabilities:
- **Request Tracing**: Correlation IDs (UUID v4) across all components
- **Performance Profiling**: Checkpoint-based with bottleneck detection (>20% threshold)
- **Query Logging**: In-memory log with slow query detection (>100ms)
- **Structured Logging**: JSON format with context propagation (correlation_id, request_path, user_session)
- **Exception Context**: Full traceback + context dict in all errors
- **Debug Endpoints**: 8 endpoints for inspection (search explanation, cache stats, query log, performance summary)

**§debug.endpoints** - Debug API:
- POST `/api/v1/debug/search/explain` - Explain search results
- GET `/api/v1/debug/profile/{session_id}` - User profile inspector
- GET `/api/v1/debug/cache/stats` - Cache statistics
- GET `/api/v1/debug/qdrant/stats` - Vector DB stats
- GET `/api/v1/debug/queries/recent` - Recent query log
- GET `/api/v1/debug/performance/summary` - Performance summary
- GET `/api/v1/debug/health/detailed` - Detailed health check
- POST `/api/v1/debug/cache/clear` - Clear cache

**§debug.config** - Configuration:
```bash
# Enable debug mode
DEBUG_ENABLED=true

# Feature flags
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=true
DEBUG_LOG_SQL=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=300  # Threshold for slow request warnings
```

**§debug.usage** - Usage Example:
```python
# Auto-injection via middleware
from app.core.logging import correlation_id_var

# Correlation ID automatically available
correlation_id = correlation_id_var.get()  # Returns current request's correlation ID

# Performance profiling
from app.core.profiler import RequestProfiler

with RequestProfiler("search_operation") as profiler:
    profiler.checkpoint("embedding")
    # ... work ...
    profiler.checkpoint("vector_search")
    # ... work ...
    summary = profiler.get_summary()  # Get bottlenecks + recommendations
```

**Full Details**:
- docs/DEBUG_SYSTEM.md - Complete documentation
- `app/core/profiler.py` - Profiler implementation
- `app/api/v1/debug.py` - Debug endpoints

---

#### §multimodal - Multi-Modal RAG System
**Status**: Strategy Designed (Phase 4.4 + 6 준비 완료)
**Goal**: OCR + Text Embedding + Image Embedding 통합 검색

**§multimodal.architecture** - Three-Modal Pipeline:
- **Text Embedding**: Sentence Transformers (all-MiniLM-L6-v2, 384-dim)
- **Image Embedding**: OpenCLIP ViT-H-14 (1024-dim)
- **Shape Embedding**: Hu Moments + Fourier Descriptors (128-dim)
- **Vector DB**: Qdrant Named Vectors (text, image, shape)
- **Search**: Hybrid fusion (weighted, RRF, learned)

**§multimodal.pipeline** - Complete Flow:
```
Input (PDF/Image/Text/Excel)
  ↓
Multi-Modal Processing:
  ├── Text → Sentence Transformers (384-dim)
  ├── Image → OpenCLIP (1024-dim)
  └── Shape → Contour Descriptors (128-dim)
  ↓
Qdrant Multi-Vector Storage
  ↓
Hybrid Search (Text + Image + Shape)
  ↓
Re-ranking + Filtering → Results
```

**§multimodal.models** - Embedding Models:
- Text (Current): all-MiniLM-L6-v2 ⭐ Production
- Text (Upgrade): multilingual-e5-large (better Korean)
- Image (Current): OpenCLIP ViT-H-14 ⭐ Production
- Image (Alternative): Fine-tuned ResNet50 (packaging domain)
- Shape (New): Custom descriptors (geometric similarity)

**§multimodal.search** - Search Strategies:
- **Text-only**: Semantic search (current)
- **Image-only**: Visual similarity (implemented)
- **Hybrid**: Text + Image fusion (85% + 90% → **95%** accuracy)
- **Tri-modal**: Text + Image + Shape (best accuracy)

**§multimodal.fusion** - Fusion Techniques:
- Weighted Linear: Simple, interpretable
- RRF (Reciprocal Rank Fusion): Robust, no tuning
- Learned Fusion: ML-based, optimal (requires training data)

**§multimodal.performance** - Target Metrics:
- Text search accuracy: >85% @ Top-10
- Image search accuracy: >80% @ Top-10
- Hybrid search accuracy: >90% @ Top-10
- Search latency (cached): <50ms
- Search latency (uncached): <500ms
- OCR → Embedding: <5s per page

**§multimodal.roadmap** - Implementation (Phase 4.4):
- Week 1: Unified Embedding Pipeline
- Week 2: Qdrant Multi-Vector Setup
- Week 3: Hybrid Search Engine
- Week 4: OCR Integration + Testing

**Quick Start**:
```python
# Multi-modal search
from src.core.multimodal.hybrid_search import HybridSearchEngine

engine = HybridSearchEngine()
results = engine.search_hybrid(
    text_query="20파이 캡 5000개",
    image_query="product_photo.jpg",
    text_weight=0.6,
    image_weight=0.4
)
```

**Full Details**:
- docs/MULTIMODAL_RAG_STRATEGY.md (80KB) - Complete architecture
- app/services/image_search_service.py - Current image search
- src/core/embedding_service.py - Current text embedding

---

## 📁 Project Structure

```
rag-enterprise/
├── .claude/skills/        # SKILL implementations
├── src/                   # Core modules
│   ├── api/              # FastAPI routes
│   ├── core/             # RAG, embeddings, search
│   └── services/         # Business logic
├── frontend/             # chat.html (v2.0.0)
├── docs/                 # Documentation + symbols
├── tests/                # Test suite
└── data/                 # Crawled products (857)
```

---

## 🚀 Current Status: Phase 0-4 Complete

**Status**: ✅ **Production Ready** (Phase 0-4 complete - 2025-11-06)
**Next**: Phase 5-9 (Advanced RAG, Image Matching, Cloud Integration)

### Completed Components
1. ✅ RAG Pipeline (Phase 0-3): Atomic chunking, enhanced field extraction, search optimization
2. ✅ OCR Pipeline (Phase 4): Multi-engine OCR, 7 modules, ~1,850 lines
3. ✅ Debug System: 10 components, correlation IDs, profiling, query logging
4. ✅ Enterprise Backend: Repository + Service layers, dependency injection
5. ✅ Testing: 122 test cases (repositories, services, integration)
6. ✅ Deployment: Docker Compose + K8s manifests, testing scripts

### System Statistics
- **Data**: 471 products → 3,246 atomic chunks
- **Search Quality**: 0.79-0.82 similarity
- **Code**: ~9,850 lines (Phase 4 implementation)
- **Tests**: 122 test cases, 95%+ coverage target
- **Documentation**: Complete deployment guide + API docs

**Full Roadmap**: docs/ROADMAP.md

---

## 📝 Documentation Index

| Document | Symbol | Size | Load When |
|----------|--------|------|-----------|
| Architecture | §arch.* | 31KB | Design, integration |
| RAG Strategy | §rag.* | 18KB | RAG development |
| OCR & Parsing Strategy | §ocr.* | 50KB | OCR/PDF/Image processing |
| OCR Quick Start | §ocr.quickstart | 30KB | Practical OCR examples |
| Multi-Modal RAG Strategy | §multimodal.* | 80KB | Embedding, Image matching, Hybrid search |
| Debug System | §debug.* | 15KB | Debugging, observability |
| Deployment Guide | §deploy.* | 30KB | Production deployment |
| UI Policy | §ui.* | 13KB | Frontend work |
| Ollama Policy | §ollama.* | 6.5KB | Model management |
| Symbol System | - | 3KB | Reference guide |

**Full Map**: `docs/SYMBOL_SYSTEM.md`

---

**v4.0.0** | **2025-11-06** | **Phase 0-4 Complete - Production Ready** | **MIT**
