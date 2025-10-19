# CLAUDE.md

**RAG Enterprise**: Production-grade RAG system with multi-model support, vector search, and monitoring.

## Core Rules

1. **Python 3.11+** - Type hints required, async/await for I/O operations
2. **FastAPI** - RESTful API design, Pydantic models for validation
3. **PostgreSQL + pgvector** - Primary storage with vector similarity search
4. **Redis** - Caching layer for embeddings and query results
5. **Docker Compose** - All services containerized, health checks mandatory
6. **pytest + coverage** - Min 80% coverage, integration tests for APIs
7. **Logging** - Structured JSON logs via `structlog`, centralized in `/logs`
8. **Error Handling** - Custom exceptions, proper HTTP status codes
9. **Security** - API keys via env vars, input sanitization, rate limiting
10. **Documentation** - Docstrings (Google style), OpenAPI auto-generated

## Folder Map

| Path | Purpose |
|------|---------|
| `src/api/` | FastAPI routes and endpoints |
| `src/core/` | Business logic (RAG, embeddings, retrieval) |
| `src/models/` | Pydantic schemas and DB models |
| `src/services/` | External integrations (OpenAI, Anthropic, Cohere) |
| `src/utils/` | Helpers (logging, config, validators) |
| `tests/` | Unit and integration tests |
| `docs/` | Architecture, API specs, guides |
| `scripts/` | Setup, migration, benchmark scripts |
| `config/` | Environment configs (dev/staging/prod) |

## Task References

- **Architecture**: `docs/ARCHITECTURE.md`
- **Setup**: `docs/GETTING_STARTED.md`
- **API Docs**: `docs/API_REFERENCE.md`
- **Testing**: `tests/README.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Monitoring**: `docs/MONITORING.md`

## Dynamic Loading

**When to load additional context:**
- Modifying API routes → Load `src/api/README.md` + `docs/API_REFERENCE.md`
- Changing RAG logic → Load `src/core/rag_engine.py` + `docs/ARCHITECTURE.md`
- Adding tests → Load `tests/README.md` + `pytest.ini`
- Docker issues → Load `docker-compose.yml` + `Dockerfile`
- Database changes → Load `src/models/` + `alembic/` migration files

**Quick Start**: `docker-compose up -d && pytest tests/`

---
*Last updated: 2025-01-24 | Size: ~1.4KB*