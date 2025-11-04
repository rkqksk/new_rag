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
| rag-pipeline | 20% | process, query, search |
| manufacturing-expert | ✅ | process, classify |
| packaging-expert | ✅ | process, classify |
| web-crawler-pipeline | ✅ | crawl, monitor |

**Details**: §arch.core.skills

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
| UI changes | §ui.* | Design updates, components |
| Model management | §ollama.* | Model updates, performance |
| Deployment | §deploy.* | Infrastructure setup |

### Quick Access (Expanded)

#### §rag - RAG Activation Strategy
**Status**: ~~20%~~ → **85% complete** ✅ (2025-11-04 업데이트)
**Next**: Production 배포 최적화 (15%)

**§rag.status** - 완성된 항목:
- ✅ Phase 1: 분석 완료
- ✅ Phase 2: Core 모듈 개발 완료
- ✅ Phase 3: 인프라 설정 완료
- ✅ Phase 4: Skill 통합 완료
- ✅ Phase 5: 857개 제품 임베딩 완료 (100%)

**§rag.core** - 완성된 Core 모듈:
- ✅ `src/core/rag_pipeline.py` (262 lines)
  - `RAGPipeline`: 통합 파이프라인 (ingest, retrieve, generate)
  - `ingest_documents()`: 문서 → 임베딩 → Qdrant
  - `retrieve()`: 벡터 검색 (metadata filters 지원)
  - `generate_response()`: Ollama 답변 생성
  - **Test**: ✅ All passed (Score: 0.7254)

- ✅ `src/core/embedding_service.py` (72 lines)
  - Model: all-MiniLM-L6-v2 (384 dim)
  - GPU 지원 (CUDA/MPS)
  - **Test**: ✅ Passed

- ✅ `src/api/chat.py` (450 lines)
  - Feature flag: `USE_VECTOR_RAG=true`
  - `/chat/query`: 벡터 검색 + RAG 답변
  - Backward compatibility 유지
  - **Test**: ✅ Passed (Score: 0.5678)

**§rag.skill** - Skill 래퍼 완성:
- ✅ `.claude/skills/rag-pipeline/scripts/skill.py`
  - `process_document()`: Core RAGPipeline 사용
  - `vector_search()`: 실제 벡터 검색
  - `rag_query()`: 검색 + 답변 생성 (타이밍 포함)

**§rag.data** - 임베딩 현황:
- ✅ 857/857 products (Bottle: 675, Jar: 42, Cap: 118, Pump: 22)
- ✅ Collection: `products` @ Qdrant
- ✅ Search test passed (Score: 0.6405)

**§rag.infra** - 인프라:
- ✅ Colima (4 CPU, 8GB RAM)
- ✅ Qdrant v1.11.3 (http://localhost:6333)
- ✅ Ollama (qwen2.5:7b-instruct)

**Full Details**: docs/RAG_ACTIVATION_STRATEGY.md (20KB)

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
| UI Policy | §ui.* | 13KB | Frontend work |
| Ollama Policy | §ollama.* | 6.5KB | Model management |
| Symbol System | - | 3KB | Reference guide |

**Full Map**: `docs/SYMBOL_SYSTEM.md`

---

**v3.2.0** | **2025-11-04** | **MIT**
