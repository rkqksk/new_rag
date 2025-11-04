# RAG Enterprise

**Production-grade Retrieval-Augmented Generation system with SKILL-based architecture.**

## Features

- 🔍 Multi-format document processing (PDF, DOCX, XLSX)
- 💡 Semantic search with vector database
- 🤖 Multi-model support (Ollama, OpenAI, Claude)
- 🔌 Domain expert plugins (manufacturing, packaging)
- 📊 Token-efficient hybrid architecture

## Quick Start

```bash
# Clone and install
git clone <repo-url> && cd rag-enterprise
pip install -r requirements.txt

# Setup environment
cp .env.example .env  # Add your API keys

# Start services
docker-compose up -d

# Run server
python run_chat_server.py

# Start frontend (in another terminal)
cd frontend && python3 -m http.server 8080
# Open: http://localhost:8080/chat.html
```

## Frontend

**Location**: `frontend/chat.html`
- 💬 White/minimal design chat interface
- 📦 Real-time product recommendations
- 🔍 RAG-powered search
- 📊 Session management

**API Endpoints**:
- `POST /chat/create_session` - Create new chat session
- `POST /chat/query` - Query with RAG context

## Documentation

- **Quick Start**: `QUICK_START.md`
- **Architecture**: `/workflow ARCHITECTURE`
- **Usage Guide**: `/workflow USAGE_GUIDE`
- **Development**: `/guide development`

## Tech Stack

- FastAPI (Python 3.11+)
- Qdrant vector database
- Sentence Transformers
- Docker Compose

## License

MIT License - See `LICENSE` file

---

**v3.1.0** | **2025-11-03**
