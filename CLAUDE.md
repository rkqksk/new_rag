# RAG Enterprise - Quick Reference

**Version**: v4.0.0 | **Status**: Phase 0-4 Complete ✅ Production-Ready

> **Optimized for Claude Code**: Symbol-based navigation | Token-efficient | Modular architecture
>
> **Symbol System**: Use `§{domain}.{component}` to access detailed information (see §symbols below)

---

## ⚡ Quick Start

```bash
# Deploy (Development)
./scripts/deploy-optimized.sh development

# Test System
./scripts/test-optimized.sh

# Frontend
cd frontend && python3 -m http.server 8080
# → http://localhost:8080/chat.html

# View API Docs
# → http://localhost:8001/api/v1/docs
```

---

## 📊 System Status (Phase 0-4 Complete)

### Current State ✅
- **Data**: 471 products → 3,246 atomic chunks
- **Search Quality**: 0.79-0.82 similarity
- **Vector DB**: Qdrant (3,246 vectors, 384-dim)
- **OCR Pipeline**: 7 modules (~1,850 lines)
- **Debug System**: 10 components
- **Tests**: 122 test cases (95%+ coverage target)
- **API Endpoints**: 18 production endpoints
- **Deployment**: Docker + K8s ready

### Completed Phases
- ✅ **Phase 0**: Initial Setup (Docker, FastAPI, Frontend)
- ✅ **Phase 1**: Atomic Chunking (471 → 3,246 chunks)
- ✅ **Phase 2**: Enhanced Field Extraction
- ✅ **Phase 3**: Search Optimization
- ✅ **Phase 4**: OCR Pipeline (Multi-engine)

### Next: Phase 5-9
- 📋 Phase 5: Advanced RAG Integration
- 📋 Phase 6: Shape Embedding & Image Matching
- 📋 Phase 7: Cloud Data Integration
- 📋 Phase 8: Real-Time Streaming (SSE)
- 📋 Phase 9: Enterprise Deployment (K8s + CI/CD)

**Full Roadmap**: §rag.roadmap → `docs/ROADMAP.md`

---

## 🎯 Symbol Quick Access

> **Purpose**: Lightweight references to avoid context bloat. Load full docs only when needed.

### Core Symbols

| Symbol | Description | Load When | Document |
|--------|-------------|-----------|----------|
| **§rag.status** | RAG system status & metrics | RAG development | §symbols |
| **§rag.core** | Core modules (8 modules) | Module implementation | §symbols |
| **§ocr.pipeline** | OCR workflow (7 modules) | OCR/PDF processing | §symbols |
| **§debug.endpoints** | Debug API (8 endpoints) | Debugging, profiling | §symbols |
| **§deploy.quick** | Quick deployment | Deployment setup | §symbols |
| **§test.coverage** | Test suite (122 tests) | Testing, QA | §symbols |
| **§api.endpoints** | API reference (18 endpoints) | API development | §symbols |
| **§arch.overview** | System architecture | System design | §symbols |

### Symbol Notation

```
§{domain}.{component}.{detail}
Examples:
  §rag.core                # RAG core modules
  §ocr.engines             # OCR engine selection
  §debug.features          # Debug capabilities
  §deploy.docker           # Docker deployment
  §api.endpoints           # API endpoints list
```

### Complete Symbol Map

**→ `docs/reference/SYMBOLS.md`** (Complete reference with all symbols)

---

## 🏗️ Architecture (Symbolized)

```
Frontend (chat.html v2.0.0)
    ↓
API Layer (FastAPI - 18 endpoints)
    ↓
Service Layer (Search, Personalization, Analytics)
    ↓
Repository Layer (Qdrant, Redis, PostgreSQL)
    ↓
Data Layer (Vectors, Cache, DB)
```

**Details**: §arch.overview → `docs/ARCHITECTURE.md`

---

## 🔧 Common Commands

### Development
```bash
# Deploy
./scripts/deploy-optimized.sh development

# Test
./scripts/test-optimized.sh

# Python tests
pytest tests/ -v --cov=src --cov=app

# Docker
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose logs -f api    # Logs
```

### Production
```bash
# Deploy
./scripts/deploy-optimized.sh production

# Health check
curl http://localhost:8001/health/ready

# Performance
curl http://localhost:8001/api/v1/debug/performance/summary
```

**Full Commands**: `docs/guides/QUICK_REFERENCE.md`

---

## 🔄 Session Protocol

### Start Session
```bash
git status && git branch
```

### During Session
1. **TodoWrite** if >2 steps
2. **Run tests** before commit
3. **Update docs** if API/arch changes

### End Session
- ✅ Git status clean
- ✅ Todos resolved
- ✅ Tests passing
- ✅ Background processes killed

---

## 🎨 Active SKILLs

| Skill | Status | Commands |
|-------|--------|----------|
| rag-pipeline | ✅ Phase 0-4 | process, query, search |
| manufacturing-expert | ✅ | process, classify |
| packaging-expert | ✅ | process, classify |
| web-crawler-pipeline | ✅ | crawl, monitor |
| **nexa-rag-optimizer** | ✅ **NEW** | analyze, optimize-search, tune-routing, benchmark |
| **multimodal-processor** | ✅ **NEW** | analyze-image, ocr-document, visual-search, hybrid-search |

**Location**: `.claude/skills/`
**Note**: Skills use progressive disclosure (references/ folder) for token efficiency

---

## 📖 Documentation Index

### Quick Access Guides
- **Quick Reference**: `docs/guides/QUICK_REFERENCE.md` ⭐ Start here
- **Complete Symbols**: `docs/reference/SYMBOLS.md` ⭐ All § references
- **API Documentation**: `docs/API_DOCUMENTATION.md` (30KB)
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md` (30KB)

### Strategy Documents
- **RAG Strategy**: `docs/RAG_ACTIVATION_STRATEGY.md` (§rag.*)
- **OCR Strategy**: `docs/OCR_PARSING_STRATEGY.md` (§ocr.*)
- **Multi-Modal Strategy**: `docs/MULTIMODAL_RAG_STRATEGY.md` (§multimodal.*)
- **Debug System**: `docs/DEBUG_SYSTEM.md` (§debug.*)

### Reports
- **Completion Report**: `docs/COMPLETION_REPORT.md` (Phase 0-4 summary)
- **Roadmap**: `docs/ROADMAP.md` (Phase 5-9 plans)
- **Architecture**: `docs/ARCHITECTURE.md` (§arch.*)

### Directory Structure
```
docs/
├── guides/           # User guides (quick reference, testing)
├── reference/        # Technical reference (symbols, API)
├── strategies/       # Implementation strategies
└── reports/          # Status reports, summaries
```

---

## 🔍 Quick Symbol Lookups

### Most Used Symbols

**RAG System** (§rag.*):
- `§rag.status` - Current state: Phase 0-4 complete, 3,246 chunks
- `§rag.core` - 8 modules: classifier, chunker, search, etc.
- `§rag.roadmap` - Phase 5-9 future plans

**OCR Pipeline** (§ocr.*):
- `§ocr.pipeline` - Multi-engine: PaddleOCR → EasyOCR → Tesseract
- `§ocr.engines` - Engine selection strategy
- `§ocr.entities` - 8 entity types (code, name, capacity, etc.)

**Debug System** (§debug.*):
- `§debug.endpoints` - 8 debug API endpoints
- `§debug.features` - Correlation IDs, profiling, query logging
- `§debug.config` - Environment variables

**Deployment** (§deploy.*):
- `§deploy.quick` - One-command deployment
- `§deploy.docker` - Docker Compose (dev/prod)
- `§deploy.k8s` - Kubernetes manifests

**Testing** (§test.*):
- `§test.coverage` - 122 test cases, 95%+ target
- `§test.quick` - `./scripts/test-optimized.sh`
- `§test.pytest` - Python test suite

**API** (§api.*):
- `§api.endpoints` - 18 production endpoints
- `§api.docs` - Swagger UI at `/api/v1/docs`

**Load Complete Map**: `docs/reference/SYMBOLS.md`

---

## 🚀 Services & Ports

| Service | URL | Port |
|---------|-----|------|
| API | http://localhost:8001 | 8001 |
| API Docs | http://localhost:8001/api/v1/docs | 8001 |
| Qdrant UI | http://localhost:6333/dashboard | 6333 |
| Redis | localhost:6379 | 6379 |
| PostgreSQL | localhost:5432 | 5432 |
| Frontend | http://localhost:8080 | 8080 |

---

## 🛠️ Tech Stack

### Backend
- Python 3.11+, FastAPI, Pydantic v2
- Qdrant (vectors), Redis (cache), PostgreSQL (DB)

### ML/AI
- Sentence Transformers (all-MiniLM-L6-v2, 384-dim)
- Ollama (qwen2.5:7b-instruct, 4.7GB)
- PaddleOCR + EasyOCR + Tesseract

### Infrastructure
- Docker Compose, Kubernetes (optional)
- Modular scripts (scripts/lib/)

**Full Stack**: `docs/TECHNOLOGY_STACK.md`

---

## 🤖 NexaAI Integration (NEW)

### Dual-Engine Architecture

**NexaAI** (Fast) + **Ollama** (Quality) = Optimal Performance

| Engine | Model | Use Case | Latency | Activation |
|--------|-------|----------|---------|------------|
| NexaAI | Qwen3-1.7B | Simple queries | < 500ms | Score < 0.3 |
| NexaAI | Qwen3-VL-4B | Medium + Vision | < 1s | 0.3 ≤ Score < 0.7 |
| Ollama | qwen2.5:7b | Complex reasoning | ~2s | Score ≥ 0.7 |

### Quick Start

```bash
# 1. Install NexaAI SDK (optional - can run without)
pip install nexaai

# 2. Start NexaAI server (localhost)
nexa server start

# 3. System auto-routes to optimal engine
curl -X POST http://localhost:8001/api/v1/search \
  -d '{"query":"50ml PET 용기"}'
# → Auto-routes to NexaAI (fast)

curl -X POST http://localhost:8001/api/v1/search \
  -d '{"query":"PET와 PP의 화학적 특성 비교 분석"}'
# → Auto-routes to Ollama (quality)
```

### Configuration

```bash
# Enable NexaAI (optional)
NEXA_ENABLED=true
NEXA_BASE_URL=http://localhost:8080/v1

# Router thresholds
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7
```

### Admin API

```bash
# Check system health
curl http://localhost:8001/api/v1/admin/health

# View routing statistics
curl http://localhost:8001/api/v1/admin/stats

# List available models
curl http://localhost:8001/api/v1/admin/models
```

**Full Documentation**: `docs/NEXA_SDK_INTEGRATION_PLAN.md`

---

## 📝 Environment Configuration

### Essential Variables
```bash
# API
API_PORT=8001
API_HOST=0.0.0.0

# Databases
QDRANT_HOST=qdrant
QDRANT_PORT=6333
REDIS_HOST=redis
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=your_password

# Debug (optional)
DEBUG_ENABLED=true
DEBUG_PROFILE_REQUESTS=true
```

**Complete Config**: `.env.example`

---

## 🆘 Troubleshooting

### Quick Fixes
```bash
# Reset everything
docker-compose down -v && docker-compose up -d

# Check health
curl http://localhost:8001/health/ready

# View logs
docker-compose logs -f

# Debug performance
curl http://localhost:8001/api/v1/debug/performance/summary
```

**Full Guide**: `docs/DEPLOYMENT_GUIDE.md` → Troubleshooting section

---

## 📌 Key Principles

### Symbol System (§)
- **Use symbols first**: Check `docs/reference/SYMBOLS.md`
- **Load docs when needed**: Only load full docs for implementation
- **Update symbols**: Keep §* references current

### Modularity
- **Scripts**: `scripts/lib/` for reusable functions
- **Docs**: `docs/guides/` for user guides, `docs/reference/` for technical specs
- **Code**: Clean layers (API → Service → Repository → Data)

### Documentation
- **Quick Reference**: This file (CLAUDE.md)
- **Complete Symbols**: `docs/reference/SYMBOLS.md`
- **Deep Dive**: Strategy docs (`docs/strategies/`)

---

## 🎉 Quick Wins

### For Development
```bash
# Start everything
./scripts/deploy-optimized.sh development && ./scripts/test-optimized.sh

# Search test
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'
```

### For Debugging
```bash
# Enable debug mode
echo "DEBUG_ENABLED=true" >> .env && docker-compose restart api

# Check slow queries
curl http://localhost:8001/api/v1/debug/queries/recent?slow_only=true
```

### For Deployment
```bash
# Production deploy
./scripts/deploy-optimized.sh production

# Health check
curl http://localhost:8001/health/ready
```

---

**v4.0.0** | **2025-11-06** | **Phase 0-4 Complete - Production Ready** | **MIT**

**Quick Start**: `./scripts/deploy-optimized.sh development`
**Full Symbols**: `docs/reference/SYMBOLS.md`
**Quick Reference**: `docs/guides/QUICK_REFERENCE.md`
