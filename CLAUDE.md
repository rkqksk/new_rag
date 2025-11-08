# RAG Enterprise - Quick Reference

**Version**: v5.0.0 | **Status**: Enterprise Platform Complete ✅ Production-Ready

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

## 📊 System Status (v5.0.0 Complete)

### Current State ✅
- **Platform Type**: Enterprise SaaS + Manufacturing Automation + Universal RAG
- **API Endpoints**: 35+ production endpoints (RAG, SaaS, Manufacturing, Data Collector)
- **Data Pipeline**: 471 products → 3,246 atomic chunks
- **Search Quality**: 0.79-0.82 similarity
- **Vector DB**: Qdrant (3,246 vectors, 384-dim)
- **LLM Engines**: NexaAI (< 500ms) + Ollama (~2s) with intelligent routing
- **OCR Pipeline**: 3-engine fallback (PaddleOCR → EasyOCR → Tesseract)
- **Vision Inspection**: YOLOv8/v10 (120 FPS on Jetson, 15 FPS on Pi)
- **Multi-Tenancy**: Row-Level Security, JWT + API Key auth
- **Billing**: Stripe integration (Free/Pro/Enterprise tiers)
- **Data Collection**: Web scraping, API polling, file parsing (6 formats)
- **Tests**: 122+ test cases (95%+ coverage target)
- **Deployment**: Docker + K8s ready

### Completed Modules
- ✅ **RAG System**: Multi-modal search, atomic chunking, OCR pipeline
- ✅ **SaaS Platform**: Multi-tenancy, billing, usage tracking, API keys
- ✅ **Manufacturing**: Vision inspection, defect detection, quality control
- ✅ **Data Collector**: Universal collection, processing pipeline, DB integration

**Full Details**: README.md (v5.0.0)

---

## 🎯 Symbol Quick Access

> **Purpose**: Lightweight references to avoid context bloat. Load full docs only when needed.

### Core Symbols

| Symbol | Description | Load When | Document |
|--------|-------------|-----------|----------|
| **§rag.status** | RAG system status & metrics | RAG development | §symbols |
| **§rag.core** | Core modules (8 modules) | Module implementation | §symbols |
| **§saas.auth** | Multi-tenancy & auth (JWT + API key) | SaaS development | §symbols |
| **§saas.billing** | Stripe billing & subscriptions | Billing integration | §symbols |
| **§saas.usage** | Usage tracking & quotas | Usage monitoring | §symbols |
| **§collector.pipeline** | Data collection pipeline | Data ingestion | §symbols |
| **§collector.sources** | Collection sources (web/API/file) | Source integration | §symbols |
| **§manufacturing.vision** | Vision inspection system | Quality control | §symbols |
| **§ocr.pipeline** | OCR workflow (3 engines) | OCR/PDF processing | §symbols |
| **§debug.endpoints** | Debug API (8 endpoints) | Debugging, profiling | §symbols |
| **§api.endpoints** | API reference (35+ endpoints) | API development | §symbols |
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
API Gateway (FastAPI - 35+ endpoints)
  ├─ RAG API (search, chat, recommendations)
  ├─ SaaS API (auth, billing, usage, tenants)
  ├─ Manufacturing API (vision, inspection, quality)
  └─ Data Collector API (collect, process, schedule)
    ↓
Service Layer
  ├─ RAG Services (search, personalization, analytics)
  ├─ SaaS Services (billing, usage tracking, auth)
  ├─ Manufacturing Services (vision inspection, defect detection)
  └─ Data Services (collection, processing, enrichment)
    ↓
Repository Layer (Qdrant, Redis, PostgreSQL, MinIO)
    ↓
Data Layer (Vectors, Cache, DB, Object Storage)
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

### Core RAG & Data Processing

| Skill | Status | Commands | Purpose |
|-------|--------|----------|---------|
| rag-pipeline | ✅ | process, query, search | RAG orchestration & search |
| **chunking-expert** | ✅ **NEW** | analyze, apply, compare, optimize | Advanced chunking strategies (atomic/semantic/hierarchical) |
| **embedding-expert** | ✅ **NEW** | generate, optimize, finetune, metrics | Embedding & vectorization optimization |
| **web-scraping-expert** | ✅ **NEW** | scrape, extract, evade, parallel | Advanced web scraping (BeautifulSoup/Playwright/Selenium) |
| nexa-rag-optimizer | ✅ | analyze, optimize-search, tune-routing | Query optimization & routing |
| multimodal-processor | ✅ | analyze-image, ocr-document, visual-search | Multi-modal processing |
| web-crawler-pipeline | ✅ | crawl, monitor | Web scraping automation |

### Platform & Infrastructure

| Skill | Status | Commands | Purpose |
|-------|--------|----------|---------|
| **data-collector** | ✅ | collect, process, schedule, monitor | Universal data collection |
| **saas-platform** | ✅ | auth, billing, usage, tenants | SaaS management |
| **frontend-platform** | ✅ | design-system, create-page, component | Monochrome UI design system |
| **debugging-expert** | ✅ **NEW** | inspect, console-log, network-log, performance | Live browser debugging with Chrome DevTools |

### Domain Experts

| Skill | Status | Commands | Purpose |
|-------|--------|----------|---------|
| manufacturing-expert | ✅ | process, classify, inspect | Manufacturing docs processing |
| packaging-expert | ✅ | process, classify | Packaging docs processing |

**Location**: `.claude/skills/`
**Note**: Skills use progressive disclosure (references/ folder) for token efficiency

---

## 🔌 MCP Server Integration

> **Model Context Protocol (MCP)**: Standardized integration between Claude and external tools/data sources
>
> **Architecture**: Token-optimized with main project (filesystem + git only) + specialized sub-agents

### Main Project MCPs (Token-Optimized)

**Only 2 MCPs enabled** for maximum token efficiency:

| MCP Server | Status | Purpose | Cost |
|------------|--------|---------|------|
| **filesystem** | ✅ | Secure file operations | $0/month |
| **git** | ✅ | Git repository operations | $0/month |

**Why Only 2?** Token efficiency + delegation to sub-agents for specialized tasks.

### Sub-Agent Architecture

**8 specialized sub-agents** for parallel processing and token efficiency:

#### 1. Crawling Agent (`.claude/agents/crawling-agent`)

| MCP Server | Purpose | Cost |
|------------|---------|------|
| **puppeteer** | Browser automation | $0/month |
| **fetch** | Web content fetching | $0/month |
| **chrome-devtools** | Live debugging | $0/month |
| **tavily** | AI search (optional) | $0/month (1000 req/month free) |

**Skills**: web-scraping-expert, web-crawler-pipeline, advanced-data-acquisition
**Use for**: Web scraping, data acquisition, anti-bot evasion

#### 2. Frontend Agent (`.claude/agents/frontend-agent`)

| MCP Server | Purpose | Cost |
|------------|---------|------|
| **shadcn-ui** | React component library | $0/month |
| **chrome-devtools** | Live browser debugging | $0/month |

**Skills**: frontend-platform, debugging-expert
**Use for**: React/Tailwind development, UI components, responsive design

#### 3. Data Agent (`.claude/agents/data-agent`)

| MCP Server | Purpose | Cost |
|------------|---------|------|
| **postgres** | Production database | $0/month (software only) |
| **sqlite** | Local cache | $0/month |

**Skills**: saas-platform, data-collector
**Use for**: Database operations, SQL queries, data analysis

#### 4. Code Review Agent (`.claude/agents/code-review-agent`)

| MCP Server | Purpose | Cost |
|------------|---------|------|
| **github** | GitHub API | $0/month (unlimited for public repos) |

**Skills**: pcb-expert, mold-expert
**Use for**: PR reviews, issue management, repository operations

#### 5. RAG Agent (`.claude/agents/rag-agent`)

**MCPs**: None (pure Python tools)

**Skills**: rag-pipeline, embedding-expert, chunking-expert, nexa-rag-optimizer, multimodal-processor
**Use for**: RAG optimization, embeddings, chunking, vector search

#### 6. Testing Agent (`.claude/agents/testing-agent`)

**MCPs**: None (uses pytest framework)

**Use for**: Unit tests, integration tests, coverage analysis

#### 7. Deployment Agent (`.claude/agents/deployment-agent`)

**MCPs**: None (uses Docker/K8s CLI)

**Use for**: Docker deployment, Kubernetes orchestration, CI/CD

#### 8. Monitoring Agent (`.claude/agents/monitoring-agent`)

**MCPs**: None (uses Prometheus/Grafana)

**Use for**: Performance monitoring, metrics, logs, profiling

### MCP Priority Levels

**Priority 1: No API Key Required** ($0/month)
- `filesystem`, `git`, `fetch`, `puppeteer`, `shadcn-ui`, `chrome-devtools`
- **Use freely** - no setup required

**Priority 2: Free Tier Available** ($0/month with limits)
- `tavily` - 1000 requests/month free ([get key](https://tavily.com))
- `github` - Unlimited for public repos ([get token](https://github.com/settings/tokens))

**Priority 3: Removed** (paid or complex)
- ~~`brave-search`~~ - Paid ($5/month minimum) → use self-crawling
- ~~`google-drive`~~ - Complex OAuth → use local filesystem

### Configuration

**Location**: `.claude/mcp.json` (main project), `.claude/agents/*/agent.json` (sub-agents)

**Main Project** (no setup):
```bash
# Already enabled: filesystem + git
# No configuration needed
```

**Sub-Agents** (optional setup):
```bash
# Tavily (optional - 1000 free requests/month)
export TAVILY_API_KEY="tvly-..."  # Get at https://tavily.com

# GitHub (optional - for private repos only)
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."  # Get at https://github.com/settings/tokens

# PostgreSQL (production)
export POSTGRES_URL="postgresql://user:password@localhost:5432/rag_enterprise"

# SQLite (create database)
mkdir -p data && touch data/cache.db
```

### Using Sub-Agents

Launch sub-agents via Task tool for **parallel processing** and specialized work:

```python
# 1. Web scraping and data acquisition
Task(subagent_type="crawling-agent", prompt="Scrape product data from example.com")

# 2. Frontend development
Task(subagent_type="frontend-agent", prompt="Create dashboard with shadcn/ui components")

# 3. Database operations
Task(subagent_type="data-agent", prompt="Analyze user activity patterns from PostgreSQL")

# 4. Code review and GitHub integration
Task(subagent_type="code-review-agent", prompt="Review PR #123 and suggest improvements")

# 5. RAG system optimization
Task(subagent_type="rag-agent", prompt="Optimize embedding model for Korean text")

# 6. Automated testing
Task(subagent_type="testing-agent", prompt="Run all tests and generate coverage report")

# 7. Deployment automation
Task(subagent_type="deployment-agent", prompt="Deploy to production with zero downtime")

# 8. Performance monitoring
Task(subagent_type="monitoring-agent", prompt="Analyze system performance and identify bottlenecks")
```

**Parallel Execution Example**:
```python
# Run multiple agents in parallel for maximum efficiency
Task(subagent_type="testing-agent", prompt="Run tests")
Task(subagent_type="monitoring-agent", prompt="Check performance")
Task(subagent_type="deployment-agent", prompt="Prepare deployment")
# All 3 tasks execute in parallel!
```

### MCP Installation

**Automatic** (via npx):
```bash
# MCPs are auto-installed when first used
# No manual installation required
```

**Manual** (for development):
```bash
# Install specific MCP server globally
npm install -g @modelcontextprotocol/server-puppeteer
npm install -g @modelcontextprotocol/server-postgres
npm install -g @modelcontextprotocol/server-github
```

### MCP Resources

- **Official Docs**: https://modelcontextprotocol.io/
- **Server List**: https://github.com/modelcontextprotocol/servers
- **Awesome MCPs**: https://github.com/wong2/awesome-mcp-servers
- **Examples**: https://modelcontextprotocol.io/examples

---

## 📖 Documentation Index

### Quick Access Guides
- **Quick Reference**: `docs/guides/QUICK_REFERENCE.md` ⭐ Start here
- **Complete Symbols**: `docs/reference/SYMBOLS.md` ⭐ All § references
- **API Documentation**: `docs/reference/API_DOCUMENTATION.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`

### Platform Documentation (NEW v5.0.0)
- **Open Source Architecture**: `docs/OPEN_SOURCE_ARCHITECTURE.md` ⭐ 100% open-source, $0 software costs
- **SaaS Architecture**: `docs/SAAS_ARCHITECTURE.md` (§saas.*)
- **Data Collector**: `docs/DATA_COLLECTOR_ARCHITECTURE.md` (§collector.*)
- **Manufacturing Automation**: `docs/MANUFACTURING_AUTOMATION.md` (§manufacturing.*)
- **System Integration**: `docs/SYSTEM_INTEGRATION_GUIDE.md`
- **NexaAI Integration**: `docs/NEXA_SDK_INTEGRATION_PLAN.md`

### RAG Documentation
- **RAG Strategy**: `docs/RAG_ACTIVATION_STRATEGY.md` (§rag.*)
- **OCR Strategy**: `docs/OCR_PARSING_STRATEGY.md` (§ocr.*)
- **Multi-Modal Strategy**: `docs/MULTIMODAL_RAG_STRATEGY.md` (§multimodal.*)
- **Debug System**: `docs/reference/DEBUG_SYSTEM.md` (§debug.*)

### Directory Structure
```
docs/
├── guides/           # User guides (quick reference, testing)
├── reference/        # Technical reference (symbols, API, debug)
└── [root]/           # Architecture & integration docs
```

---

## 🔍 Quick Symbol Lookups

### Most Used Symbols

**RAG System** (§rag.*):
- `§rag.status` - Current state: v5.0.0 complete, 3,246 chunks
- `§rag.core` - 8 modules: classifier, chunker, search, etc.
- `§rag.engines` - NexaAI (< 500ms) + Ollama (~2s) routing

**SaaS Platform** (§saas.* - NEW):
- `§saas.auth` - JWT (24h) + API key authentication
- `§saas.billing` - Stripe integration, Free/Pro/Enterprise tiers
- `§saas.usage` - Usage tracking, quotas, rate limiting
- `§saas.tenants` - Multi-tenancy with Row-Level Security

**Data Collector** (§collector.* - NEW):
- `§collector.pipeline` - Collection → Processing → DB integration
- `§collector.sources` - Web scraping, API polling, file parsing
- `§collector.processing` - Validation, cleaning, transformation, enrichment
- `§collector.scheduling` - APScheduler, daily jobs, retry logic

**Manufacturing** (§manufacturing.* - NEW):
- `§manufacturing.vision` - YOLOv8/v10 defect detection
- `§manufacturing.devices` - Jetson (120 FPS), Pi (15 FPS)
- `§manufacturing.quality` - SPC, defect trends, alerts

**OCR Pipeline** (§ocr.*):
- `§ocr.pipeline` - Multi-engine: PaddleOCR → EasyOCR → Tesseract
- `§ocr.engines` - 3-engine fallback strategy
- `§ocr.entities` - 8 entity types (code, name, capacity, etc.)

**API** (§api.*):
- `§api.endpoints` - 35+ production endpoints (RAG, SaaS, Manufacturing, Collector)
- `§api.docs` - Swagger UI at `/api/v1/docs`

**Deployment** (§deploy.*):
- `§deploy.quick` - One-command deployment
- `§deploy.docker` - Docker Compose (dev/prod)
- `§deploy.k8s` - Kubernetes manifests

**Load Complete Map**: `docs/reference/SYMBOLS.md`

---

## 🚀 Services & Ports

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| API | http://localhost:8001 | 8001 | Main FastAPI server |
| API Docs | http://localhost:8001/api/v1/docs | 8001 | Swagger UI |
| Qdrant UI | http://localhost:6333/dashboard | 6333 | Vector DB admin |
| Redis | localhost:6379 | 6379 | Cache & rate limiting |
| PostgreSQL | localhost:5432 | 5432 | Tenants, users, billing, usage |
| MinIO | http://localhost:9000 | 9000 | Object storage (optional) |
| Frontend | http://localhost:8080 | 8080 | Chat interface |
| NexaAI | http://localhost:8080/v1 | 8080 | Fast LLM (optional) |
| Ollama | http://localhost:11434 | 11434 | Quality LLM |

---

## 🛠️ Tech Stack

### Backend
- Python 3.11+, FastAPI, Pydantic v2
- Qdrant (vectors), Redis (cache), PostgreSQL (DB), MinIO (object storage)

### ML/AI
- **LLM**: NexaAI (Qwen3-1.7B/VL-4B) + Ollama (qwen2.5:7b) with intelligent routing
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2, 384-dim)
- **OCR**: PaddleOCR v2.7.0.3 (primary) + EasyOCR + Tesseract (fallback)
- **Vision**: YOLOv8/v10 for defect detection, TensorRT (Jetson), ONNX (Pi)

### SaaS
- **Auth**: JWT (PyJWT) + API keys (SHA-256 hashed)
- **Billing**: Stripe SDK (subscriptions, webhooks, invoices)
- **Multi-Tenancy**: Row-Level Security (PostgreSQL)
- **Usage Tracking**: Redis (counters) + PostgreSQL (analytics)

### Data Collection
- **Web**: BeautifulSoup (static), Playwright (dynamic), Selenium (complex)
- **API**: httpx (async), OAuth2, retry logic, pagination
- **Files**: openpyxl (Excel), pandas (CSV), PyPDF2 (PDF), lxml (XML)
- **Scheduling**: APScheduler (cron triggers, daily jobs)

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

# SaaS (NEW)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# NexaAI (optional)
NEXA_ENABLED=true
NEXA_BASE_URL=http://localhost:8080/v1
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7

# Debug (optional)
DEBUG_ENABLED=true
DEBUG_PROFILE_REQUESTS=true
```

**Complete Config**: `.env.example`

---

## 🆘 Troubleshooting

### Automated Troubleshooting

**One-Command Fix** (Recommended):
```bash
# Restart everything (kills all processes, resets services)
./scripts/restart-all.sh
```

This script automatically:
1. Kills all running services (Docker, Ollama, NexaAI, Python servers)
2. Cleans up Docker resources (containers, volumes, networks)
3. Restarts all services in correct order
4. Waits for health checks
5. Displays service status

### Manual Quick Fixes

```bash
# Full reset (Docker + volumes)
docker-compose down -v && docker-compose up -d

# Restart without losing data
docker-compose restart

# Kill specific service
docker-compose restart api        # Restart API only
docker-compose restart qdrant     # Restart vector DB

# Check health
curl http://localhost:8001/health/ready

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f api
docker-compose logs -f qdrant

# Debug performance
curl http://localhost:8001/api/v1/debug/performance/summary
```

### Common Issues

**1. Port Already in Use**
```bash
# Find process using port 8001
lsof -i :8001

# Kill process
kill -9 <PID>

# Or use restart-all.sh (kills all automatically)
./scripts/restart-all.sh
```

**2. Docker Services Won't Start**
```bash
# Clean everything and restart
docker-compose down -v
docker system prune -af
./scripts/deploy-optimized.sh development
```

**3. Ollama Not Responding**
```bash
# Restart Ollama
docker-compose restart ollama

# Check Ollama health
curl http://localhost:11434/api/tags

# Pull model again if needed
docker exec -it ollama ollama pull qwen2.5:7b
```

**4. Qdrant Connection Errors**
```bash
# Restart Qdrant
docker-compose restart qdrant

# Check Qdrant health
curl http://localhost:6333/health

# View Qdrant dashboard
open http://localhost:6333/dashboard
```

**5. API Server Crashes**
```bash
# View error logs
docker-compose logs --tail=100 api

# Restart API
docker-compose restart api

# Full reset if needed
./scripts/restart-all.sh
```

**6. Out of Memory**
```bash
# Check Docker resource usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase to 8GB+

# Or reduce batch sizes in .env
EMBEDDING_BATCH_SIZE=16  # Default: 32
```

**7. Frontend Not Loading**
```bash
# Check if frontend server is running
lsof -i :8080

# Restart frontend
cd frontend && python3 -m http.server 8080

# Or use background server
cd frontend && python3 -m http.server 8080 &
```

### Service Ports Reference

| Service | Port | Check Command |
|---------|------|---------------|
| API | 8001 | `curl http://localhost:8001/health` |
| Frontend | 8080 | `curl http://localhost:8080` |
| Qdrant | 6333 | `curl http://localhost:6333/health` |
| Redis | 6379 | `docker exec redis redis-cli ping` |
| PostgreSQL | 5432 | `docker exec postgres pg_isready` |
| Ollama | 11434 | `curl http://localhost:11434/api/tags` |
| NexaAI | 8080 | `curl http://localhost:8080/v1/models` |

### Health Check Script

```bash
# Check all services
./scripts/health-check.sh

# Manual health check
curl http://localhost:8001/health/ready && echo "✅ API OK" || echo "❌ API FAIL"
curl http://localhost:6333/health && echo "✅ Qdrant OK" || echo "❌ Qdrant FAIL"
docker exec redis redis-cli ping && echo "✅ Redis OK" || echo "❌ Redis FAIL"
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

**v5.0.0** | **2025-11-08** | **Enterprise Platform Complete - Production Ready** | **MIT**

**Quick Start**: `./scripts/deploy-optimized.sh development`
**Full Symbols**: `docs/reference/SYMBOLS.md`
**Platform Docs**: README.md (35+ features, 4 major modules)
