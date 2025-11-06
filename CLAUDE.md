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
| rag-pipeline | ✅ Phase 0-3 Complete | process, query, search |
| manufacturing-expert | ✅ | process, classify |
| packaging-expert | ✅ | process, classify |
| web-crawler-pipeline | ✅ | crawl, monitor |

**Details**: §arch.core.skills
**Roadmap**: See [ROADMAP.md](docs/ROADMAP.md) for Phase 4-9 plans

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
| UI changes | §ui.* | Design updates, components |
| Model management | §ollama.* | Model updates, performance |
| Deployment | §deploy.* | Infrastructure setup |

### Quick Access (Expanded)

#### §rag - RAG System Status
**Status**: **Phase 0-3 Complete** ✅ Production-Ready (2025-11-06 업데이트)
**Next**: Phase 4-9 (Multi-Modal, Image Matching, Cloud Integration)

**§rag.status** - 완성된 Phase:
- ✅ **Phase 0**: Initial Setup (Docker, FastAPI, Frontend)
- ✅ **Phase 1**: Atomic Chunking (471 products → 3,246 chunks)
- ✅ **Phase 2**: Enhanced Field Extraction (Neck, MOQ, Material, Price)
- ✅ **Phase 3**: Search Optimization (0.79-0.82 quality)

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

**§rag.roadmap** - 향후 계획 (Phase 4-9):
- 📋 Phase 4: Multi-Modal Data Processing (PDF, Image, Excel/CSV)
- 📋 Phase 5: Advanced RAG Integration Pipeline
- 📋 Phase 6: Image Matching Service
- 📋 Phase 7: Cloud Data Integration
- 📋 Phase 8: Real-Time Chat Optimization
- 📋 Phase 9: Enterprise Deployment

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
**Status**: Strategy Designed (Phase 4.2 준비 완료)
**Goal**: Production-grade OCR for PDF/Image → Structured data

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

**§ocr.roadmap** - Implementation Plan (Phase 4.2):
- Week 1-2: Core OCR Engine (multi-engine fallback)
- Week 3-4: Layout Analysis (tables, multi-column)
- Week 5-6: Entity Recognition & NER (custom training)
- Week 7-8: Integration & Testing

**Quick Start**:
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
- scripts/archive/experiments/paddleocr_excel_parser.py - Existing prototype

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

## 🚀 Current Focus: RAG Activation

**Status**: §rag.status (20% complete)
**Next**: §rag.phase2 (Core module development)

### Immediate Tasks
1. Phase 2.1: VectorSearch (§rag.phase2.vector)
2. Phase 2.2: DocumentProcessor (§rag.phase2.processor)
3. Phase 2.3: RAGEngine (§rag.phase2.engine)

**Full Strategy**: §rag.strategy

---

## 📝 Documentation Index

| Document | Symbol | Size | Load When |
|----------|--------|------|-----------|
| Architecture | §arch.* | 31KB | Design, integration |
| RAG Strategy | §rag.* | 18KB | RAG development |
| OCR & Parsing Strategy | §ocr.* | 50KB | OCR/PDF/Image processing |
| OCR Quick Start | §ocr.quickstart | 30KB | Practical OCR examples |
| UI Policy | §ui.* | 13KB | Frontend work |
| Ollama Policy | §ollama.* | 6.5KB | Model management |
| Symbol System | - | 3KB | Reference guide |

**Full Map**: `docs/SYMBOL_SYSTEM.md`

---

**v3.2.0** | **2025-11-04** | **MIT**
