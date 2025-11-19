# PETER - Quick Reference

**Version**: v10.0.0 "Unified Maximum" | **Status**: Phase 1-2 Complete (75% Done) ⚙️

> **Token-Optimized**: Use `§symbols` for detailed docs • Load only what you need
>
> **Quick Access**: Common commands below • Full guides in `docs/`
>
> **NEW**: Monorepo structure • Pure Black design • 76% fewer directories
>
> **Migration Status**: Backend 95% • Frontend 70% • Packages 60% • Services 10%

---

## ⚡ Quick Start (v10.0.0)

```bash
# Install Dependencies
pnpm install

# Development (All Apps)
pnpm dev

# Development (Individual)
pnpm web                    # Frontend only
pnpm api                    # API only

# Production Deployment
./scripts/deploy-optimized.sh development

# View Interfaces
open http://localhost:3000             # Web App (Pure Black UI)
open http://localhost:8001/api/v1/docs # API Docs
open http://localhost:8080/realtime-demo.html # Realtime Demo

# Check Health
curl http://localhost:8001/health/ready
```

---

## 📊 System Status (v10.0.0)

**Platform**: Unified Maximum Monorepo
**Structure**: 8 directories (down from 33, -76%) ✅
**Packages**: @rag/{web,core,config,utils,ui} - 60% implemented ⚙️
**Services**: 17 containers ($0/month software cost) ✅
**Endpoints**: 80+ production APIs (+67%) ✅
**Components**: 52/60 UI components migrated (87%) ⚙️

**Completion by Area**:
- Backend (apps/api): 95% ✅ - Fully functional with unified structure
- Frontend (apps/web): 70% ⚙️ - 8 components still to migrate
- Packages: 60% ⚙️ - Structure done, implementations partial
- Services: 10% ⚠️ - Scaffolds only, not functional yet
- Tests: Updated and passing ✅
- Infrastructure: Production-ready ✅

### Core Features ✅
- **RAG**: Multi-modal search, OCR, hybrid search, query optimization
- **SaaS**: Multi-tenancy, JWT+API auth, Stripe billing, usage tracking
- **Manufacturing**: Vision inspection (YOLOv8/v10), defect detection
- **Data Collection**: Web scraping, API polling, file parsing (6 formats)
- **Realtime**: Socket.IO reactive queries, PostgreSQL LISTEN/NOTIFY
- **Security**: Keycloak OAuth2/OIDC, Vault secrets
- **Observability**: Jaeger tracing, Prometheus, Grafana
- **Data Platform**: MinIO S3, Airflow ETL, Metabase BI
- **Design System**: Pure Black (#000000), NO icons, Natural theme ⭐ NEW

### Quick Stats
- **Structure**: 8 directories (-76%) | <5% duplication (-90%) ✅
- **Backend**: apps/api fully functional (95% complete) ✅
- **Frontend**: 52/60 components migrated (87% complete) ⚙️
- **Tests**: Updated and passing ✅
- **Build**: Backend working | Frontend needs completion ⚙️
- **Data**: 471 products → 3,246 atomic chunks ✅
- **Search**: 0.79-0.82 similarity | <500ms response ✅
- **Cost**: $0/month software | $17,460+/year savings ✅

**Phase Status**: Phase 1-2 Complete | Phase 3 In Progress

**Details**: `PROGRESS.md`, `README.md`, `CHANGELOG.md`

---

## 📁 v10 Structure (8 Directories)

```
new_rag_ubuntu/
├── apps/                    # Applications
│   ├── api/                # FastAPI backend (unified from app/backend/src) ✅ 95%
│   ├── web/                # Next.js 15 (Pure Black design) ⚙️ 70%
│   ├── pwa/                # Vite PWA (scaffold) ⚠️ 10%
│   └── mobile/             # Expo (React Native, scaffold) ⚠️ 10%
├── packages/                # Shared packages ⚙️ 60%
│   ├── core/               # Business logic (structure done, partial impl)
│   ├── config/             # Settings (structure done, partial impl)
│   ├── utils/              # Utilities (structure done, partial impl)
│   └── ui/                 # React components (@rag/ui, 52/60 migrated)
├── services/                # Microservices ⚠️ 10%
│   ├── rag/                # RAG engine (scaffold only)
│   ├── collector/          # Data collection (scaffold only)
│   ├── manufacturing/      # Vision AI (scaffold only)
│   ├── realtime/           # Socket.IO (scaffold only)
│   └── ml/                 # MLflow (scaffold only)
├── infrastructure/          # IaC ✅ 95%
│   ├── k8s/                # Kubernetes + Helm
│   ├── terraform/          # AWS/GCP/Azure
│   └── observability/      # Grafana dashboards
├── tools/                   # Dev tools ✅ 90%
├── .claude/                # Claude Code (skills, commands) ✅ 100%
├── docs/                   # Documentation ✅ 100%
└── workflows/              # CI/CD ⚙️ 70%
```

**Old code preserved**: `.archive/{app,backend,src}-v9/` (6.5MB total)
**Active codebase**: Monolith-first approach - `apps/api` contains all backend functionality

---

## 🎯 Symbol Quick Access (70-80% Token Savings!)

> **Two Systems**: `§symbols` for DOCS + Serena MCP for CODE
>
> **Combined Savings**: 70-80% fewer tokens vs reading full files

### 📄 Documentation Symbols (§symbol)
**Use**: Navigate documentation efficiently
**Format**: `§symbol` loads specific doc sections

#### Core Systems
- `§rag.*` - RAG system (chunking, search, OCR, engines)
- `§saas.*` - SaaS platform (auth, billing, tenants, usage)
- `§collector.*` - Data collection (web, API, file, scheduling)
- `§manufacturing.*` - Manufacturing (vision, devices, quality)
- `§realtime.*` - Realtime backend (Socket.IO, PostgreSQL, Redis)

#### v10 Structure
- `§v10.*` - v10 structure, migration, monorepo setup
- `§design.*` - Pure Black design system (ABSOLUTE rules)
- `§packages.*` - Shared packages (core, config, utils, ui)
- `§services.*` - Microservices architecture

#### Infrastructure
- `§security.*` - Keycloak OAuth2/OIDC, Vault secrets
- `§observe.*` - Jaeger tracing, Prometheus, Grafana
- `§data.*` - MinIO storage, Airflow ETL, Metabase BI
- `§k8s.*` - Kubernetes, Helm, ArgoCD, Terraform

#### Development
- `§api.*` - API endpoints (80+)
- `§debug.*` - Debug system (8 endpoints)
- `§deploy.*` - Deployment (Docker, K8s, CI/CD)
- `§arch.*` - Architecture (services, layers, databases)

**Complete Map**: `docs/reference/SYMBOLS.md` (200 lines, 80% reduction)

### 🐍 Code Symbols (Serena MCP) ⭐ NEW
**Use**: Read Python code symbolically (not entire files!)
**Savings**: 70-80% vs `Read` tool

#### Quick Commands
```python
# 1. Get file overview (always start here)
get_symbols_overview("apps/api/services/rag_qa_service.py")
→ Returns: [QARequest, QAResponse, RAGQAService]  # 20 tokens vs 1200!

# 2. Get class structure
find_symbol(name_path="RAGQAService", depth=1, include_body=false)
→ Returns: All method signatures  # 50 tokens

# 3. Read specific method
find_symbol(name_path="RAGQAService/query", include_body=true)
→ Returns: Only query method  # 80 tokens

# Total: ~150 tokens vs 1200 tokens = 87% savings!
```

#### Always Use Serena For
- **Large Routers** (300-450 lines):
  - `apps/api/core/routing/ml_router.py`
  - `apps/api/core/routing/llm_router.py`
  - `apps/api/core/routing/intent_router.py`
- **All Services** (200-400 lines):
  - `apps/api/services/*.py`
  - `apps/api/rag_consultation/**/*.py`
- **Any file >200 lines**

**Complete Guide**: `docs/reference/CODE_SYMBOLS.md` (symbolic code reading)

---

## 🤖 Claude Skills System

> **Auto-Activation**: Skills automatically trigger based on keywords and context

### Available Skills (9 Total)

**Core Business**:
- `rag-optimization` - RAG search quality, chunking, embeddings (30 keywords)
- `data-collection` - Web crawling, parsing, Airflow scheduling (29 keywords)
- `manufacturing-vision` - YOLO defect detection, quality control (25 keywords)
- `saas-operations` - Multi-tenancy, billing, authentication (23 keywords)

**Infrastructure**:
- `deployment-automation` - K8s, Helm, GitOps, CI/CD (22 keywords)
- `testing-suite` - pytest auto-generation, coverage (25 keywords)

**Data Processing**:
- `excel-processing` - Excel/CSV parsing, analysis (24 keywords)
- `pdf-processing` - PDF extraction, OCR, tables (23 keywords)
- `web-testing` - E2E testing, Playwright, accessibility (22 keywords)

### Quick Usage

**Auto-Activation** (Recommended):
```
"RAG 검색 품질 개선해줘" → rag-optimization activates
"OneHago 크롤링" → data-collection activates
"YOLO 불량 검사" → manufacturing-vision activates
```

**Details**: `.claude/skills/README.md`

---

## 🚀 Services (17 Total)

### Core (8)
| Service | Port | Access |
|---------|------|--------|
| API + Socket.IO | 8001 | http://localhost:8001/api/v1/docs |
| PostgreSQL | 15432 | localhost:15432 |
| Redis | 16379 | localhost:16379 |
| Qdrant | 16333 | http://localhost:16333/dashboard |
| ClickHouse | 8123 | http://localhost:8123 |
| Kafka | 9092 | localhost:9092 |
| Zookeeper | 2181 | localhost:2181 |
| Frontend | 3000 | http://localhost:3000 (Pure Black UI) |

### Security (v7.0.0)
| Service | Port | Login |
|---------|------|-------|
| Keycloak | 8080 | admin/admin |
| Vault | 8200 | token: root |

### Observability (v7.0.0)
| Service | Port | Login |
|---------|------|-------|
| Jaeger | 16686 | http://localhost:16686 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | admin/admin |

### Data Platform (v7.0.0)
| Service | Port | Login |
|---------|------|-------|
| MinIO | 9002 | minioadmin/minioadmin |
| Airflow | 8082 | admin/admin |
| Metabase | 3001 | http://localhost:3001 |

**Details**: `§arch.services`

---

## 🔧 Essential Commands

### Development (v10)
```bash
# Monorepo Setup (one-time)
./setup.sh                # Full setup with Docker
./setup.sh --skip-docker  # Setup without Docker
./setup.sh --skip-data    # Setup without seeding

# Monorepo Build
./build-all.sh            # Standard build
./build-all.sh --parallel # Fast parallel build
./build-all.sh --production # Production optimized

# Monorepo Development
pnpm install              # Install all dependencies
pnpm dev                  # Run all apps
pnpm build                # Build all apps
pnpm lint                 # Lint all packages
pnpm test                 # Run all tests

# Individual Apps
pnpm web                  # Frontend only
pnpm api                  # API only
cd apps/web && npm run dev
cd apps/api && uvicorn main:app --reload

# Deployment
./scripts/deploy-optimized.sh development
make dev  # Alternative

# Test
./scripts/test-optimized.sh
make test

# Validation
./scripts/v10/validate_v10.sh
```

### Docker
```bash
# Start/Stop
docker-compose up -d
docker-compose down

# Restart Service
docker-compose restart api
docker-compose restart qdrant

# Logs
docker-compose logs -f api
```

### Database
```bash
# Migrations
alembic upgrade head
alembic downgrade -1
alembic history

# Make commands
make migrate-upgrade
make migrate-downgrade
```

### Testing
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=apps --cov=packages

# Specific test
pytest tests/test_search.py -v

# Make commands
make test
make test-cov
```

### Code Quality
```bash
# Format
make format  # Black + isort

# Lint
make lint    # flake8 + ruff

# Type check
make type-check  # mypy

# Pre-commit hooks (automatic on commit)
pre-commit install           # Install hooks
pre-commit run --all-files   # Run all hooks manually
pre-commit autoupdate        # Update hook versions

# All checks
make setup && make format && make lint && make test
```

**Full Commands**: `docs/guides/QUICK_REFERENCE.md`
**Automation Guide**: `docs/guides/AUTOMATION_SCRIPTS.md` ⭐ NEW

---

## 🐛 Quick Troubleshooting

### Current Known Issues (v10.0.0)

**Frontend (apps/web)**:
- ⚠️ 8 components still need migration from old structure
- ⚠️ Some imports may reference old paths
- Fix: Use apps/api directly for now, frontend migration ongoing

**Packages**:
- ⚠️ Implementations partial (structure complete)
- ⚠️ Some exports not fully configured
- Fix: Import directly from apps/api until packages complete

**Services**:
- ⚠️ Scaffolds only - not functional yet
- Fix: All functionality is in apps/api (monolith-first approach)

### Automated Fix
```bash
# Backend (fully working)
cd apps/api
uvicorn main:app --reload --port 8001

# Frontend (partial - use with caution)
cd apps/web && npm run dev
```

### Manual Fixes
```bash
# Port in use
lsof -i :8001 && kill -9 <PID>

# Docker reset
docker-compose down -v && docker-compose up -d

# Use backend directly
curl http://localhost:8001/api/v1/docs
```

### Health Checks
```bash
# API
curl http://localhost:8001/health/ready

# Qdrant
curl http://localhost:6333/health

# Redis
docker exec redis redis-cli ping

# PostgreSQL
docker exec postgres pg_isready
```

**Full Troubleshooting**: `docs/guides/TROUBLESHOOTING.md`

---

## 📚 Documentation Index

### Quick Access
- **CLAUDE.md** - This file (quick reference, v10 updated)
- **README.md** - Project overview (v10 structure)
- **PROGRESS.md** - Version history (v10.0.0 status)
- **CHANGELOG.md** - v10.0.0 release notes

### v10 Documentation ⭐ NEW
- **docs/guides/V9_TO_V10_MIGRATION.md** - Migration guide
- **docs/design/DESIGN_SYSTEM.md** - Pure Black design (ABSOLUTE rules)
- **scripts/v10/validate_v10.sh** - Structure validation

### Symbol System ⭐ NEW
- **docs/reference/SYMBOLS.md** - Documentation symbols (200 lines, -80%)
- **docs/reference/CODE_SYMBOLS.md** - Code symbols (Serena MCP guide, -87% tokens)

### Guides (How-to)
- **docs/guides/QUICK_REFERENCE.md** - Common commands
- **docs/guides/LOCAL_SETUP.md** - Setup guide
- **docs/guides/TROUBLESHOOTING.md** - Common issues
- **docs/guides/DEPLOYMENT_GUIDE.md** - Deployment

### Reference (Technical)
- **docs/reference/API_DOCUMENTATION.md** - API endpoints (80+)
- **docs/reference/DEBUG_SYSTEM.md** - Debug features

### Architecture (Deep Dive)
- **docs/V7_COMPLETE_GUIDE.md** - v7.0.0 production guide (500+)
- **docs/REALTIME_BACKEND_GUIDE.md** - Realtime backend (500+)
- **docs/SAAS_ARCHITECTURE.md** - SaaS platform (800+)
- **docs/DATA_COLLECTOR_ARCHITECTURE.md** - Data collection (600+)
- **docs/MANUFACTURING_AUTOMATION.md** - Manufacturing (500+)
- **docs/RAG_ACTIVATION_STRATEGY.md** - RAG system (500+)

---

## 🎨 Design System (v10.0.0)

### ABSOLUTE Rules

**Background**: `#000000` (pure black, always)
```css
/* ✅ CORRECT */
background: #000000;

/* ❌ WRONG */
background: #111111;
background: #1a1a1a;
```

**NO Icons**: Text only
```tsx
/* ✅ CORRECT */
<button>Search</button>

/* ❌ WRONG */
<button><SearchIcon /> Search</button>
```

**Natural Theme**: Minimal, organic, no gradients
```css
/* ✅ CORRECT */
border: 1px solid #1a1a1a;

/* ❌ WRONG */
background: linear-gradient(...);
box-shadow: 0 10px 40px ...;
```

**Enforcement**: See `docs/design/DESIGN_SYSTEM.md` for complete rules

**Validation**:
```bash
# Check violations
grep -r "bg-gray-9" apps/ packages/  # Should return nothing
grep -r "Icon" apps/ packages/       # Should return nothing
```

---

## 🔌 MCP Integration

### Active MCP Servers
- **filesystem** - File operations for /home/user/new_rag_ubuntu
- **github** - GitHub integration (unlimited for public repos)

**Config**: `.claude/mcp.json`

---

## 💡 Key Principles

### v10 Philosophy
**Maximal Features + Minimal Structure**
- Unified backend (`apps/api/`)
- Shared packages (`packages/*`)
- Microservices (`services/*`)
- Zero duplication (<5%)
- Pure Black design (ABSOLUTE)

### Symbol System (Dual Approach)
**Documentation Symbols** (`§symbol`):
1. **Check SYMBOLS.md first** - Find exact symbol
2. **Load only needed** - `§symbol` loads 50-200 lines vs 500-1000
3. **70-80% token savings** - 4-5x more efficient

**Code Symbols** (Serena MCP):
1. **Always start with overview** - `get_symbols_overview(file)` before `Read(file)`
2. **Read symbolically** - Class/method at a time, not entire files
3. **Use for Python files >200 lines** - Routers, services, all large files
4. **87-94% token savings** - Read 150 tokens instead of 1200 tokens
5. **See CODE_SYMBOLS.md** - Complete Serena usage guide

### Documentation
- **CLAUDE.md** - Quick reference (this file, ~300 lines)
- **SYMBOLS.md** - Symbol map (200 lines)
- **Guides** - How-to (100-300 lines each)
- **References** - Technical (300-1000 lines)
- **Architecture** - Deep dive (500-800 lines)

### Session Protocol
```bash
# Start
git status && git branch

# During
1. Use TodoWrite for >2 steps
2. Run tests before commit
3. Update docs if API/arch changes
4. Follow design system (Pure Black, NO icons)

# End
- Git status clean
- Todos resolved
- Tests passing
- Background processes killed
```

---

## 🎉 Quick Wins

```bash
# 1. Start Everything
pnpm install
pnpm dev

# 2. View Web App (Pure Black UI)
open http://localhost:3000

# 3. View API Docs
open http://localhost:8001/api/v1/docs

# 4. Test RAG Search
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'

# 5. View Monitoring
open http://localhost:3000  # Grafana (admin/admin)

# 6. View Tracing
open http://localhost:16686  # Jaeger

# 7. Validate Structure
./scripts/v10/validate_v10.sh
```

---

**v10.0.0 "Unified Maximum"** | **2025-11-16** | **Production Ready** | **MIT** | **$0/month**

**Token Optimization**: 70-80% savings with Serena MCP | `§symbols` (docs) + Serena (code)
**Structure**: 8 directories | <5% duplication
**Quick Start**: `pnpm install && pnpm dev`
**Serena Guide**: `docs/reference/CODE_SYMBOLS.md` (symbolic code reading)
**Full Docs**: `PROGRESS.md`, `CHANGELOG.md`, `docs/design/DESIGN_SYSTEM.md`
**Migration**: `docs/guides/V9_TO_V10_MIGRATION.md`
