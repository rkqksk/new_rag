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

```bash
# 1. Install
git clone <repo-url> && cd rag-enterprise
pip install -r requirements.txt

# 2. Environment
cp .env.example .env

# 3. Start services
docker-compose up -d

# 4. Run backend
python run_chat_server.py

# 5. Run frontend (new terminal)
cd frontend && python3 -m http.server 8080
# Open: http://localhost:8080/chat.html
```

**Detailed Guide**: `docs/QUICK_START.md`

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
