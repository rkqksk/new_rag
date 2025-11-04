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
**Status**: 20% complete (Skill structure + Domain Experts)
**Next**: Phase 2 - Core module development

**§rag.status**:
- Current: Phase 1 완료 (분석)
- Next: Phase 2-5 (7.5-9.5 days)
- Goal: 857개 제품 벡터 검색

**§rag.phase2** - Core Modules (3-4 days):
- `§rag.phase2.vector`: VectorSearch 모듈
  - File: `src/core/vector_search.py` (신규)
  - Qdrant 연결, 벡터 검색, 메타데이터 필터링
  - Main: `VectorSearch(qdrant_url, collection_name)`

- `§rag.phase2.processor`: DocumentProcessor 모듈
  - File: `src/core/document_processor.py` (신규)
  - JSON 파싱, 청킹, 임베딩, Qdrant 업로드
  - 재사용: `.claude/skills/rag-pipeline/scripts/parsers/`

- `§rag.phase2.engine`: RAGEngine 모듈
  - File: `src/core/rag_engine.py` (신규)
  - Query → Retrieval → Generation 파이프라인
  - Ollama 답변 생성, 신뢰도 계산

**Full Details**: docs/RAG_ACTIVATION_STRATEGY.md (18KB)

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
