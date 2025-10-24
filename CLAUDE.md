# RAG Enterprise - Claude Project Context

**Production-grade RAG system with multi-model support, vector search, and monitoring.**

---

## 🎯 Overview

### Core Goals
- **High-quality RAG**: Accurate document-based answers
- **Scalable**: Plugin architecture
- **Production-ready**: Monitoring, logging, error handling
- **Multi-model**: OpenAI, Anthropic, local LLMs

### Tech Stack
- **Backend**: FastAPI (Python 3.11+)
- **Vector DB**: Qdrant + PostgreSQL/pgvector
- **Cache**: Redis
- **Container**: Docker Compose
- **Testing**: pytest (80%+ coverage)
- **Monitoring**: Structlog + Prometheus

---

## 📁 Structure

```
rag-enterprise/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── core/             # Business logic (rag_engine, embeddings, retrieval)
│   ├── models/           # Pydantic schemas
│   ├── services/         # External services
│   └── utils/            # Utilities
├── tests/                # unit/ integration/ e2e/
├── config/               # dev/staging/production.env
├── docs/                 # ARCHITECTURE, API_REFERENCE, DEPLOYMENT, MONITORING
├── scripts/              # setup.sh, benchmark.py, maintenance/
├── plugins/              # Domain experts (manufacturing, packaging)
├── .claude/
│   ├── commands/         # 17 custom commands
│   └── skills/           # 6 project skills
├── docker-compose.yml
├── .mcp.json            # MCP server config
└── requirements.txt
```

---

## 🚀 Quick Start

```bash
# Setup
git clone <repo-url> && cd rag-enterprise
cp .env.example .env    # Edit: add API keys
docker-compose up -d
pip install -r requirements.txt

# Test
pytest tests/ -v --cov=src

# Run
python run_chat_server.py

# Use
curl -X POST http://localhost:8000/api/v1/documents/upload -F "file=@doc.pdf"
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" -d '{"query": "How does auth work?"}'
```

---

## 🛠️ Development

### Code Style
1. Python 3.11+ with type hints
2. Async/await for I/O
3. Pydantic validation
4. Structlog JSON logging
5. Custom exceptions + HTTP status codes

### Testing
- 80%+ coverage
- pytest fixtures
- Mock external APIs
- CI/CD on PRs

---

## 🎨 Skills System

**6 specialized skills**:

| Skill | Role | Trigger |
|-------|------|---------|
| **rag-master** | Orchestration | Overall project work, deployment |
| **rag-document-processor** | Doc parsing | PDF/DOCX/XLSX uploads, OCR |
| **rag-vector-search** | Vector search | Search optimization, reranking |
| **rag_pipeline** | RAG flow | Query → Retrieval → Generation |
| **agent_orchestration** | Multi-agent | Complex task delegation |
| **note_management** | Obsidian | Documentation, knowledge graphs |

---

## 🔌 MCP Servers

**7 servers (profile: max, ~2100 tokens)**:

### 1. filesystem
File system access (auto-enabled)

### 2. claude_api
Claude API integration (Haiku 4.5 + Sonnet 4.5)
```python
response = await call_claude_api({
    "model": "claude-sonnet-4.5",
    "prompt": "Analyze..."
})
```

### 3. chrome_devtools
Browser automation (Chrome DevTools Protocol)

### 4. qdrant
Vector database (semantic search)
```python
await qdrant.upsert(collection="docs", points=[{...}])
results = await qdrant.search(collection="docs", query_vector=..., limit=10)
```

### 5. ollama
Local LLM (cost-free)
```python
response = await ollama.generate(model="llama3.1", prompt="Summarize...")
```

### 6. rag_orchestrator
RAG pipeline orchestration
```python
result = await rag_orchestrator.process_document(
    file_path="doc.pdf", options={"use_domain_expert": True}
)
answer = await rag_orchestrator.query(query="...", collection="tech_docs")
```

### 7. note_keeper
Document management & progress tracking

---

## 🧩 Domain Expert Plugins

**Location**: `plugins/`
**Type**: Python packages (directly executable)
**Status**: ✅ 2 installed & tested

### 1. Manufacturing Expert
**Path**: `plugins/manufacturing_expert/`

**Features**:
- Auto-classify: SOP, FMEA, batch records, defect analysis (8 types)
- Extract: Cpk, OEE, PPM, MTBF (150+ terms)
- Recognize: temp, pressure, time, speed, flow
- Quality metrics: Cpk, OEE, Yield, defect rate
- Standards: ISO 9001, FDA 21 CFR Part 11, GMP

**Usage**:
```python
from plugins.manufacturing_expert import ManufacturingExpertPlugin
plugin = ManufacturingExpertPlugin()
result = plugin.process_document(document)
print(result.metadata.doc_type, result.metadata.terminology)
```

### 2. Packaging Expert
**Path**: `plugins/packaging_expert/`

**Features**:
- Classify: material specs, container drawings, regulatory docs (6 types)
- Identify materials: PET, HDPE, PP, PS, PVC (40+)
- Extract dimensions: height, diameter, thickness, capacity, weight
- Barrier properties: oxygen/moisture permeability
- Compliance: FDA, EU, REACH, RoHS

### Plugin Manager
**File**: `plugins/test_plugins.py`

```python
from plugins.test_plugins import PluginManager
manager = PluginManager()  # Auto-load all plugins
result = manager.process_document(document)  # Auto-select best plugin
```

---

## 🔄 Integration Workflow

### Manufacturing Document RAG Pipeline
```python
# 1. Load
document = load_pdf("manufacturing_sop.pdf")

# 2. Domain expert processing
manager = PluginManager()
result = manager.process_document(document)

# 3. Enriched metadata
enriched = {
    'content': result.enriched_content,
    'metadata': {
        'doc_type': result.metadata.doc_type,
        'domain': result.metadata.domain,
        'terminology': result.metadata.terminology,
        'quality_metrics': result.metadata.extracted_entities['quality_metrics']
    }
}

# 4. Store in vector DB
await qdrant.upsert(collection="manufacturing_docs", points=[{
    'id': doc_id, 'vector': embed(enriched['content']), 'payload': enriched['metadata']
}])

# 5. Search
results = await qdrant.search(
    collection="manufacturing_docs", query_vector=embed(query), limit=5,
    filter={'doc_type': 'sop', 'terminology': {'$contains': 'calibration'}}
)

# 6. Generate answer
answer = await claude_api.generate(model="claude-sonnet-4.5", context=results, query=query)
```

---

## 📚 Task References

| Task | Reference |
|------|-----------|
| Architecture | `docs/ARCHITECTURE.md` |
| API Dev | `docs/API_REFERENCE.md`, `src/api/README.md` |
| RAG Engine | `src/core/rag_engine.py`, `.claude/skills/rag_pipeline/` |
| Doc Processing | `.claude/skills/rag-document-processor/` |
| Vector Search | `.claude/skills/rag-vector-search/` |
| Testing | `tests/README.md`, `pytest.ini` |
| Deployment | `docs/DEPLOYMENT.md`, `docker-compose.yml` |
| Monitoring | `docs/MONITORING.md`, `src/utils/logging.py` |
| Database | `src/models/`, `alembic/` |
| Docker | `Dockerfile`, `docker-compose.yml` |

---

## 🔧 Commands

### Development
```bash
python run_chat_server.py
pytest tests/ -v --cov=src --cov-report=html
black src/ tests/ && isort src/ tests/
mypy src/
flake8 src/ tests/
```

### Docker
```bash
docker-compose up -d
docker-compose logs -f api
docker-compose restart api
docker-compose down -v
```

### Documents
```bash
python3 scripts/maintenance/auto_organize_docs.py
python3 scripts/maintenance/auto_organize_docs.py --execute
```

### Database
```bash
alembic revision --autogenerate -m "Add table"
alembic upgrade head
alembic downgrade -1
```

---

## 🎯 Scenarios

### Add API Endpoint
1. Activate: `rag-master`
2. Route: `src/api/routes/new_route.py`
3. Logic: `src/core/new_feature.py`
4. Schema: `src/models/schemas.py`
5. Test: `tests/test_new_route.py`
6. Docs: `docs/API_REFERENCE.md`

### Improve Document Processing
1. Activate: `rag-document-processor`
2. Parser: `src/core/document_processor.py`
3. Test: `tests/test_document_processor.py`
4. Benchmark: `scripts/benchmark.py`

### Optimize Search
1. Activate: `rag-vector-search`
2. Index: Qdrant/pgvector settings
3. Rerank: `src/core/retrieval.py`
4. Measure: `scripts/benchmark.py`

### Deploy
1. Activate: `rag-master`
2. Config: `config/production.env`
3. Build: `docker-compose -f docker-compose.production.yml build`
4. Test: `pytest tests/smoke/`
5. Deploy: `docker-compose -f docker-compose.production.yml up -d`

---

## 🐛 Troubleshooting

**Slow API**: Check logs → benchmark → verify cache → optimize index
**Parse fails**: Activate `rag-document-processor` → check logs → reinstall docling → verify OCR
**Low accuracy**: Activate `rag-vector-search` → check model → adjust chunking → apply reranking

---

## 📊 Performance

| Metric | Target | Status |
|--------|--------|--------|
| API response | < 200ms | 🔄 |
| RAG answer | < 2s | 🔄 |
| Doc processing (10p) | < 5s | 🔄 |
| Vector search (top-10) | < 100ms | 🔄 |
| API throughput | > 100 req/s | 🔄 |
| Test coverage | > 80% | 🔄 |

```bash
python scripts/benchmark.py --test=all --output=report.json
```

---

## 🔐 Security

- [ ] API keys in `.env` only
- [ ] `.env` in `.gitignore`
- [ ] Input validation (Pydantic)
- [ ] Rate limiting
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CORS config
- [ ] HTTPS cert (production)

---

## 📖 Resources

**Internal**: [Architecture](docs/ARCHITECTURE.md) | [API Reference](docs/API_REFERENCE.md) | [Deployment](docs/DEPLOYMENT.md) | [Monitoring](docs/MONITORING.md)

**External**: [FastAPI](https://fastapi.tiangolo.com) | [Qdrant](https://qdrant.tech/documentation/) | [Pgvector](https://github.com/pgvector/pgvector) | [Pydantic](https://docs.pydantic.dev/)

---

## 🔄 Dynamic Loading

Load context as needed:
- API routes → `src/api/README.md` + `docs/API_REFERENCE.md`
- RAG engine → `src/core/rag_engine.py` + `.claude/skills/rag_pipeline/`
- Doc processing → `.claude/skills/rag-document-processor/`
- Vector search → `.claude/skills/rag-vector-search/`
- Testing → `tests/README.md` + `pytest.ini`
- Docker → `docker-compose.yml` + `Dockerfile`
- DB → `src/models/` + `alembic/`

---

## 📝 Version

- **Version**: 2.0.0
- **Python**: 3.11+
- **FastAPI**: 0.109+
- **Qdrant**: 1.7+
- **PostgreSQL**: 15+ (pgvector)
- **Redis**: 7.0+

---

**Last Updated**: 2025-01-24
**Maintained By**: RAG Enterprise Team
**License**: MIT
