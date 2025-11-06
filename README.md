# RAG Enterprise

**Version**: v4.0.0 | **Status**: Phase 0-4 Complete ✅ Production-Ready

> **Production-grade RAG system** with multi-engine OCR, debug observability, and symbol-based documentation.
>
> **For Developers**: See `CLAUDE.md` for quick reference and `docs/reference/SYMBOLS.md` for complete symbol map.

---

## ✨ Features

- 📄 **Multi-Engine OCR**: PaddleOCR → EasyOCR → Tesseract with auto-fallback
- 🔍 **Semantic Search**: 471 products → 3,246 atomic chunks (search quality: 0.79-0.82)
- 🐛 **Enterprise Debug**: Correlation IDs, performance profiling, query logging
- 🤖 **Multi-Model Support**: Ollama (qwen2.5:7b-instruct, nomic-embed-text)
- 🔌 **Domain Experts**: Manufacturing & packaging plugins
- 📊 **Symbol System**: Token-efficient navigation (§rag.*, §ocr.*, §debug.*)
- 🌏 **Korean Support**: Full Korean language support
- ✅ **Production Ready**: 122 tests, Docker + K8s deployment

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Docker Desktop or Colima
- 10GB free disk space

### One-Command Start
```bash
# Clone repository
git clone <repo-url> && cd rag-enterprise

# Deploy (development)
./scripts/deploy-optimized.sh development

# Test system
./scripts/test-optimized.sh

# Open frontend (new terminal)
cd frontend && python3 -m http.server 8080
# → http://localhost:8080/chat.html
```

### Services
- **API**: http://localhost:8001
- **API Docs**: http://localhost:8001/api/v1/docs
- **Qdrant UI**: http://localhost:6333/dashboard
- **Frontend**: http://localhost:8080

---

## Development with Claude Code

This project is optimized for **Claude Code** (CLI and Web).

### Claude Code CLI

```bash
# Start in project directory
cd /path/to/rag-enterprise
claude-code

# Project configuration is auto-loaded:
# - .claude/skills/ - Custom skills (rag-pipeline, manufacturing-expert)
# - .mcp.json - MCP server config (filesystem)
# - CLAUDE.md - Project guidelines & symbol system
```

### Claude Code Web

**Repository**: Push to GitHub and open in [Claude Code Web](https://claude.ai/code)

**Synced files**:
- `.claude/` - Skills and commands
- `.mcp.json` - MCP server configuration
- `CLAUDE.md` - Development guidelines
- `docs/` - Architecture and policies

**Quick commands**:
```
/workflow rag-query
/component skills
§rag.status
§arch.overview
```

**Symbol system**: Use `§{category}.{section}` for efficient documentation access (see `CLAUDE.md`)

---

## Frontend

**File**: `frontend/chat.html` (v2.0.0)
- ChatGPT-style gray tones, minimal design
- Real-time product search
- RAG-powered recommendations

**Design Specs**: §ui.design (see `CLAUDE.md`)

---

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Vector DB**: Qdrant
- **Models**: Ollama (qwen2.5:7b-instruct, nomic-embed-text)
- **Frontend**: Vanilla HTML/CSS/JS
- **Infrastructure**: Docker Compose, Redis

**Full Details**: §tech.* (see `docs/SYMBOL_SYSTEM.md`)

---

## 📖 Documentation

### Quick Access ⭐
- **Quick Reference**: `docs/guides/QUICK_REFERENCE.md` - Start here
- **Complete Symbols**: `docs/reference/SYMBOLS.md` - All § references
- **CLAUDE.md**: Quick reference for Claude Code (optimized: 380 lines)

### Guides
- **Deployment**: `docs/guides/DEPLOYMENT_GUIDE.md` (Docker, K8s, cloud)
- **Testing**: `docs/guides/QUICK_REFERENCE.md` → Testing section

### Reference
- **API Documentation**: `docs/reference/API_DOCUMENTATION.md` (18 endpoints)
- **Symbol Map**: `docs/reference/SYMBOLS.md` (Complete § references)
- **Debug System**: `docs/reference/DEBUG_SYSTEM.md` (10 components)

### Strategies
- **RAG Strategy**: `docs/strategies/RAG_ACTIVATION_STRATEGY.md`
- **OCR Strategy**: `docs/strategies/OCR_PARSING_STRATEGY.md`
- **Multi-Modal Strategy**: `docs/strategies/MULTIMODAL_RAG_STRATEGY.md`

### Reports
- **Completion Report**: `docs/reports/COMPLETION_REPORT.md` (Phase 0-4)
- **Session Summary**: `docs/reports/SESSION_SUMMARY.md`

### Directory Structure
```
docs/
├── guides/           # User guides (quick reference, deployment)
├── reference/        # Technical reference (API, symbols, debug)
├── strategies/       # Implementation strategies (RAG, OCR, multi-modal)
└── reports/          # Status reports (completion, session summaries)
```

---

## 📊 System Status

### Phase 0-4 Complete ✅
- **Data**: 471 products → 3,246 atomic chunks
- **Search Quality**: 0.79-0.82 similarity
- **OCR Pipeline**: 7 modules (~1,850 lines)
- **Debug System**: 10 components
- **Tests**: 122 test cases (95%+ coverage)
- **API Endpoints**: 18 production endpoints
- **Deployment**: Docker Compose + K8s ready

### Completed Phases
- ✅ **Phase 0**: Initial Setup (Docker, FastAPI, Frontend)
- ✅ **Phase 1**: Atomic Chunking (471 → 3,246 chunks)
- ✅ **Phase 2**: Enhanced Field Extraction (8 entity types)
- ✅ **Phase 3**: Search Optimization (hybrid search, re-ranking)
- ✅ **Phase 4**: OCR Pipeline (multi-engine fallback)

### Next: Phase 5-9
- 📋 **Phase 5**: Advanced RAG Integration (unified vector store)
- 📋 **Phase 6**: Shape Embedding & Image Matching (tri-modal RAG)
- 📋 **Phase 7**: Cloud Data Integration (multi-source)
- 📋 **Phase 8**: Real-Time Streaming (SSE)
- 📋 **Phase 9**: Enterprise Deployment (K8s + CI/CD)

**Full Roadmap**: `docs/ROADMAP.md`

---

## Contributing

See `CLAUDE.md` for:
- Session protocol
- Development workflow
- Testing requirements
- Symbol reference system

---

## License

MIT License - See `LICENSE` file

---

**v4.0.0** | **2025-11-06** | **Phase 0-4 Complete** | **Production Ready** ✅

**Quick Start**: `./scripts/deploy-optimized.sh development`
**Documentation**: `docs/guides/QUICK_REFERENCE.md`
**Symbol Map**: `docs/reference/SYMBOLS.md`
