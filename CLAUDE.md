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

### Quick Access

```bash
# Architecture
§arch.core.layers          # Core architecture
§arch.data.flow            # Data processing

# RAG Activation (Current: 20%)
§rag.status                # Current status
§rag.phase2                # Next: Core modules
§rag.phase2.vector         # VectorSearch specs
§rag.phase2.processor      # DocumentProcessor specs
§rag.phase2.engine         # RAGEngine specs

# Frontend
§ui.design.colors          # Color system
§ui.components             # Component specs

# Operations
§ollama.production         # Production models
§deploy.local              # Local setup
```

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
