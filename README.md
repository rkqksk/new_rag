# RAG Enterprise

**Production-grade Retrieval-Augmented Generation system with SKILL-based architecture.**

> **For Developers**: See `CLAUDE.md` for quick reference and symbol system.
>
> **한국어 지원**: Korean language support enabled for chat interface and documentation.

---

## Features

- 🔍 Multi-format document processing (PDF, DOCX, XLSX)
- 💡 Semantic search with vector database (§rag.*)
- 🤖 Multi-model support (Ollama: qwen2.5:7b-instruct)
- 🔌 Domain expert plugins (manufacturing, packaging)
- 📊 Token-efficient symbol architecture
- 🌏 **NEW**: Korean language support for international users

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

### Policies
- `docs/OLLAMA_MODEL_POLICY.md` - Model management (§ollama.*)
- `docs/FRONTEND_UI_POLICY.md` - UI/UX guidelines (§ui.*)
- `docs/DEPLOYMENT_STRATEGY.md` - Deployment guide (§deploy.*)

**Symbol Map**: See `docs/SYMBOL_SYSTEM.md` for complete reference system.

---

## Current Status

- **Frontend**: ✅ v2.0.0 (ChatGPT-style UI complete)
- **Backend**: ✅ File-based search operational
- **RAG System**: 🚧 20% (§rag.status - Vector search in development)
- **Documentation**: ✅ Symbolized for token efficiency

**Next**: Phase 2 - Core RAG modules (§rag.phase2)

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

**v3.2.0** | **2025-11-04** | **Symbol System Enabled**
