# RAG Enterprise

**Production-grade Retrieval-Augmented Generation system with SKILL-based architecture.**

> **For Developers**: See `CLAUDE.md` for quick reference and symbol system.
>
> **한국어 지원**: Korean language support enabled for chat interface and documentation.

---

## Features

- 🔍 Multi-format document processing (PDF, DOCX, XLSX)
- 📄 **Production OCR Pipeline** - PaddleOCR + EasyOCR + Tesseract multi-engine fallback
- 💡 Semantic search with vector database (§rag.*)
- 🤖 Multi-model support (Ollama: qwen2.5:7b-instruct)
- 🔌 Domain expert plugins (manufacturing, packaging)
- 📊 Token-efficient symbol architecture
- 🐛 **Enterprise Debug System** - Correlation IDs, performance profiling, query logging
- 🌏 Korean language support for international users

---

## Quick Start

### Prerequisites

- Python 3.11.14 (required)
- Docker Desktop or Colima
- 10GB free disk space

### Installation

```bash
# 1. Clone
git clone <repo-url> && cd rag-enterprise

# 2. Automated Setup
./scripts/setup_dev_environment.sh

# 3. Verify
./scripts/verify_environment.sh

# 4. Prepare Data (choose one)
./scripts/prepare_data.sh --snapshot    # Fast (5 min, production data)
./scripts/prepare_data.sh --sample      # Quick (1 min, test data)

# 5. Run Backend
python scripts/run_chat_server.py

# 6. Run Frontend (new terminal)
cd frontend && python3 -m http.server 8080
# Open: http://localhost:8080/chat.html
```

### Manual Setup (if automated fails)

See detailed guides:
- `docs/LOCAL_SETUP.md` - Local environment setup
- `docs/DATA_PREPARATION.md` - Data preparation options
- `docs/ENVIRONMENT_PARITY.md` - Environment consistency guide

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

## Documentation

### Core Docs
- `CLAUDE.md` - Quick reference (symbolized)
- `docs/SYMBOL_SYSTEM.md` - Symbol reference guide
- `docs/ARCHITECTURE.md` - System architecture (§arch.*)
- `docs/RAG_ACTIVATION_STRATEGY.md` - RAG development plan (§rag.*)

### Policies & Guides
- `docs/OLLAMA_MODEL_POLICY.md` - Model management (§ollama.*)
- `docs/FRONTEND_UI_POLICY.md` - UI/UX guidelines (§ui.*)
- `docs/DEPLOYMENT_GUIDE.md` - Production deployment (§deploy.*)
- `docs/DEBUG_SYSTEM.md` - Debug & observability (§debug.*)
- `docs/OCR_PARSING_STRATEGY.md` - OCR architecture (§ocr.*)

**Symbol Map**: See `docs/SYMBOL_SYSTEM.md` for complete reference system.

---

## Current Status

**Phase 0-4 Complete** ✅ (2025-11-06)

- **Frontend**: ✅ v2.0.0 (ChatGPT-style UI complete)
- **Backend**: ✅ Enterprise architecture (Repository + Service layers)
- **RAG System**: ✅ Phase 0-4 complete (Atomic chunking, search optimization)
- **OCR Pipeline**: ✅ Multi-engine OCR (PaddleOCR → EasyOCR → Tesseract)
- **Debug System**: ✅ Production debugging (correlation IDs, profiling, query logs)
- **Testing**: ✅ 122 test cases (repositories, services, integration)
- **Documentation**: ✅ Symbolized + deployment guides
- **Deployment**: ✅ Production-ready (Docker Compose + K8s manifests)

**System Statistics:**
- 471 products → 3,246 atomic chunks
- Search quality: 0.79-0.82 similarity
- 7 OCR modules (~1,850 lines)
- 10 debug components
- 122 comprehensive tests

**Next**: Phase 5-9 (Advanced RAG, Image Matching, Cloud Integration)

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

**v4.0.0** | **2025-11-06** | **Phase 0-4 Complete - Production Ready**
