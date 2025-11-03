# RAG Enterprise - Claude Project Context

**Production-grade RAG system with SKILL-based architecture, multi-model support, and vector search.**

---

## 🎯 Overview

### Core Goals
- **High-quality RAG**: Accurate document-based answers with domain expertise
- **Token-efficient**: SKILL-centric architecture (75% token reduction)
- **Scalable**: Modular domain experts for specialized processing
- **Production-ready**: Monitoring, logging, error handling

### Tech Stack
- **Backend**: FastAPI (Python 3.11+)
- **Vector DB**: Qdrant + PostgreSQL/pgvector
- **Cache**: Redis
- **Container**: Docker Compose
- **Skills**: Claude Code SKILL system (Progressive Disclosure)
- **Testing**: pytest (80%+ coverage)

---

## 📁 Structure

```
rag-enterprise/
├── .claude/
│   └── skills/              # ⭐ SKILL-centric architecture
│       ├── manufacturing-expert/  # Manufacturing domain SKILL
│       │   ├── SKILL.md           # Progressive disclosure docs
│       │   └── skill.py           # Executable wrapper
│       ├── packaging-expert/      # Packaging domain SKILL
│       │   ├── SKILL.md
│       │   └── skill.py
│       ├── rag-pipeline/          # Unified RAG orchestration SKILL
│       │   ├── SKILL.md
│       │   └── skill.py
│       └── bottle-expert/         # Cosmetic packaging recommendation
│           ├── SKILL.md
│           └── skill.py
├── plugins/                 # Domain logic (wrapped by SKILLs)
│   ├── base_plugin.py
│   ├── manufacturing_expert/
│   └── packaging_expert/
├── src/
│   ├── api/                # FastAPI endpoints
│   ├── core/               # Business logic
│   ├── models/             # Pydantic schemas
│   ├── services/           # External services
│   └── utils/              # Utilities
├── tests/                  # unit/ integration/ e2e/
├── config/                 # dev/staging/production.env
├── docs/                   # ARCHITECTURE, API_REFERENCE
├── scripts/                # setup, maintenance
├── docker-compose.yml
├── .mcp.json              # ⭐ Minimized: 3 servers (~500 tokens)
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

## 🎨 SKILL System (Token-Efficient Architecture)

### Architecture Evolution

**Before (7 MCP servers, ~2100 tokens)**:
```
❌ .claude/skills/ (no executables) + plugins/ + 7 MCP servers
❌ rag-master, rag-document-processor, rag-vector-search (separate)
❌ claude_api, ollama, rag_orchestrator, note_keeper MCPs
```

**After (3 MCP servers, ~500 tokens - 75% reduction)**:
```
✅ SKILL-centric with executable wrappers
✅ Unified rag-pipeline SKILL
✅ Only essential MCPs: filesystem, chrome_devtools, qdrant
```

### Active SKILLs

| Skill | Domain | Commands | Purpose |
|-------|--------|----------|---------|
| **rag-pipeline** | RAG orchestration | process, query, search, batch_process, batch_search, optimize_index, evaluate, stats | Unified RAG: document processing → vector search → answer generation |
| **manufacturing-expert** | Manufacturing | process, classify, extract | Manufacturing document classification (SOPs, FMEA, quality specs) |
| **packaging-expert** | Packaging | process, classify, extract | Packaging material identification, regulatory compliance |
| **bottle-expert** | Cosmetic packaging | recommend, search, filter | Product recommendations for cosmetic containers |

### SKILL Usage

#### RAG Pipeline
```python
from .claude.skills.rag_pipeline import skill

# Process document with domain expert
skill.execute('process', {
    'file_path': 'manufacturing_sop.pdf',
    'options': {
        'chunk_size': 512,
        'use_ocr': True,
        'use_domain_expert': 'manufacturing'  # Auto-extract: Cpk, OEE, ISO
    }
})

# RAG query with reranking
answer = skill.execute('query', {
    'question': 'What are the Cpk requirements?',
    'top_k': 5,
    'use_rerank': True,
    'filters': {'doc_type': 'sop'}
})

# Vector search only
results = skill.execute('search', {
    'query': '50ml PET bottle',
    'top_k': 10,
    'use_hybrid': True  # Vector + keyword (BM25)
})
```

#### Manufacturing Expert
```python
from .claude.skills.manufacturing_expert import skill

result = skill.execute('process', {
    'content': 'SOP-001: Cpk 1.33, OEE 85%, ISO 9001 compliant',
    'filename': 'sop.pdf'
})
# → Auto-extract: doc_type=sop, terminology=[cpk, oee, iso9001]
```

#### Packaging Expert
```python
from .claude.skills.packaging_expert import skill

result = skill.execute('process', {
    'content': 'PET bottle 500ml, 28/410 neck, FDA 21 CFR 177',
    'filename': 'spec.pdf'
})
# → Auto-extract: materials=[PET], capacity=500ml, regulatory=[FDA]
```

---

## 🔌 MCP Servers (Minimized)

**3 essential servers (~500 tokens)**:

### 1. filesystem
File system access (auto-enabled)

### 2. chrome_devtools
Browser automation (Chrome DevTools Protocol)

### 3. qdrant
Vector database (semantic search)
```python
await qdrant.upsert(collection="docs", points=[{...}])
results = await qdrant.search(collection="docs", query_vector=..., limit=10)
```

**Removed MCPs** (functionality moved to SKILLs):
- ❌ `claude_api` → Direct API calls in SKILLs
- ❌ `ollama` → Direct ollama calls in SKILLs
- ❌ `rag_orchestrator` → **rag-pipeline SKILL**
- ❌ `note_keeper` → Direct file writing

---

## 🧩 Domain Expert Integration

### Manufacturing Expert
**Path**: `.claude/skills/manufacturing-expert/`

**Auto-classification**: SOP, FMEA, batch records, defect analysis (8 types)
**Extraction**: Cpk, OEE, PPM, MTBF (150+ terms)
**Standards**: ISO 9001, FDA 21 CFR Part 11, GMP

### Packaging Expert
**Path**: `.claude/skills/packaging-expert/`

**Auto-classification**: Material specs, container drawings, regulatory docs (6 types)
**Materials**: PET, PETG, PP, HDPE, LLDPE, LDPE, PS (7 core plastics + barrier films)
**Regulatory**:
- **US**: FDA 21 CFR 177 (Food Contact Substances)
- **Europe**: EU 10/2011 (Plastic Materials), REACH (Chemical Safety)
- **Korea**: 식품위생법 (Food Sanitation Act), 식품용기규격 (Food Container Standards)

### Integration Workflow
```python
# 1. Load document
document = load_pdf("manufacturing_sop.pdf")

# 2. Process with domain expert (via SKILL)
from .claude.skills.manufacturing_expert import skill
result = skill.execute('process', {'content': document, 'filename': 'sop.pdf'})

# 3. Enriched metadata
enriched = {
    'content': result.enriched_content,
    'metadata': {
        'doc_type': 'sop',
        'domain': 'manufacturing',
        'terminology': ['Cpk', 'OEE', 'ISO 9001'],
        'quality_metrics': {'cpk': ['1.33'], 'oee': ['85%']}
    }
}

# 4. Index to Qdrant
await qdrant.upsert(collection="manufacturing_docs", points=[{
    'id': doc_id, 'vector': embed(enriched['content']), 'payload': enriched['metadata']
}])

# 5. Search with filters
results = await qdrant.search(
    collection="manufacturing_docs",
    query_vector=embed(query),
    filter={'doc_type': 'sop', 'terminology': {'$contains': 'calibration'}}
)
```

---

## 📚 Task References

| Task | Reference |
|------|-----------|
| Architecture | `docs/ARCHITECTURE.md` |
| SKILL Development | `.claude/skills/*/SKILL.md` |
| RAG Pipeline | `.claude/skills/rag-pipeline/` |
| Manufacturing Docs | `.claude/skills/manufacturing-expert/` |
| Packaging Docs | `.claude/skills/packaging-expert/` |
| API Dev | `docs/API_REFERENCE.md`, `src/api/README.md` |
| Testing | `tests/README.md`, `pytest.ini` |
| Deployment | `docs/DEPLOYMENT.md`, `docker-compose.yml` |
| Monitoring | `docs/MONITORING.md`, `src/utils/logging.py` |

---

## 🔄 SESSION PROTOCOL (MANDATORY)

### Session Start (REQUIRED)
```bash
git status && git branch  # Verify state
```
1. Review PROGRESS.md current state
2. Check background processes explicitly
3. State current work to user
4. **No "check later" promises** - monitor NOW or don't mention

### Change Management (REQUIRED)
**Before ANY code/config change:**
1. Classify: Feature/Bug/Config/Schema/Docs
2. Verify SKILL-centric architecture compliance
3. TodoWrite if >2 steps
4. Complete fully before next task

**After change completion:**
1. **Update CHANGELOG.md immediately** (semver format)
2. Update PROGRESS.md with technical details
3. Run tests if applicable
4. Mark todo complete only when FULLY done

### Session End (REQUIRED)
1. All todos resolved or explicitly noted as pending
2. Documentation updated (CHANGELOG.md + PROGRESS.md if changed)
3. Background processes killed or documented
4. Git status clean or changes explained

### Enforcement
- Ref: `docs/CHANGE_MANAGEMENT_GOVERNANCE.md`
- Breaking protocol = user intervention required
- Session protocol > convenience

---

## 🔧 Commands

### Development
```bash
python run_chat_server.py
pytest tests/ -v --cov=src --cov-report=html
black src/ tests/ && isort src/ tests/
mypy src/
```

### SKILL Testing
```bash
# Test individual skills
python3 .claude/skills/manufacturing-expert/skill.py
python3 .claude/skills/packaging-expert/skill.py
python3 .claude/skills/rag-pipeline/skill.py
python3 .claude/skills/bottle-expert/skill.py
```

### Docker
```bash
docker-compose up -d
docker-compose logs -f api
docker-compose restart api
docker-compose down -v
```

---

## 🎯 Scenarios

### Add API Endpoint
1. Route: `src/api/routes/new_route.py`
2. Logic: `src/core/new_feature.py`
3. Schema: `src/models/schemas.py`
4. Test: `tests/test_new_route.py`

### Improve Document Processing
1. Activate: **rag-pipeline SKILL**
2. Modify: SKILL.md for documentation, skill.py for logic
3. Test: `python3 .claude/skills/rag-pipeline/skill.py`

### Add New Domain Expert
1. Create plugin: `plugins/new_domain_expert/plugin.py`
2. Create SKILL: `.claude/skills/new-domain-expert/SKILL.md` + `skill.py`
3. Wrapper pattern: Import plugin, execute() function, commands
4. Test: `python3 .claude/skills/new-domain-expert/skill.py`

---

## 📊 Performance

| Metric | Target | Status |
|--------|--------|--------|
| Token efficiency | 75% reduction | ✅ 2100 → 500 |
| API response | < 200ms | 🔄 |
| RAG answer | < 2s | 🔄 |
| Doc processing (10p) | < 5s | 🔄 |
| Vector search (top-10) | < 100ms | 🔄 |
| Test coverage | > 80% | 🔄 |

---

## 🔐 Security

- [x] API keys in `.env` only
- [x] `.env` in `.gitignore`
- [x] Input validation (Pydantic)
- [ ] Rate limiting
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CORS config
- [ ] HTTPS cert (production)

---

## 📖 Resources

**Internal**: [Architecture](docs/ARCHITECTURE.md) | [API Reference](docs/API_REFERENCE.md) | [Deployment](docs/DEPLOYMENT.md)

**SKILLs**: [RAG Pipeline](.claude/skills/rag-pipeline/SKILL.md) | [Manufacturing](.claude/skills/manufacturing-expert/SKILL.md) | [Packaging](.claude/skills/packaging-expert/SKILL.md)

**External**: [FastAPI](https://fastapi.tiangolo.com) | [Qdrant](https://qdrant.tech/documentation/) | [Claude SKILLS](https://docs.claude.com/en/docs/claude-code/skills)

---

## 📝 Version

- **Version**: 3.1.0 (Materials & regulatory enhancement)
- **Python**: 3.11+
- **FastAPI**: 0.109+
- **Qdrant**: 1.7+
- **Architecture**: Token-efficient SKILL system

---

**Last Updated**: 2025-11-03 (Materials & regulatory standards update - Version 3.1.0)
**Maintained By**: RAG Enterprise Team
**License**: MIT
