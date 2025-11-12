# PETER - Quick Reference

**Version**: v7.0.0+ | **Status**: Ultimate Open Source Platform ✅

> **Token-Optimized**: Use `§symbols` for detailed docs • Load only what you need
>
> **Quick Access**: Common commands below • Full guides in `docs/`

---

## ⚡ Quick Start

```bash
# Deploy (Development)
./scripts/deploy-optimized.sh development

# Open Realtime Demo
open http://localhost:8080/realtime-demo.html

# Open Chat Interface
open http://localhost:8080/chat.html

# View API Docs
open http://localhost:8001/api/v1/docs

# Check Health
curl http://localhost:8001/health/ready
```

---

## 📊 System Status (v7.0.0+)

**Platform**: Ultimate Open Source Enterprise
**Services**: 17 containers ($0/month software cost)
**Endpoints**: 48+ production APIs
**LOC**: 16,500+ lines

### Core Features ✅
- **RAG**: Multi-modal search, OCR, hybrid search, query optimization
- **SaaS**: Multi-tenancy, JWT+API auth, Stripe billing, usage tracking
- **Manufacturing**: Vision inspection (YOLOv8/v10), defect detection
- **Data Collection**: Web scraping, API polling, file parsing (6 formats)
- **Realtime**: Socket.IO reactive queries, PostgreSQL LISTEN/NOTIFY ⭐ NEW
- **Security**: Keycloak OAuth2/OIDC, Vault secrets ⭐ v7.0.0
- **Observability**: Jaeger tracing, Prometheus, Grafana ⭐ v7.0.0
- **Data Platform**: MinIO S3, Airflow ETL, Metabase BI ⭐ v7.0.0
- **CI/CD**: GitHub Actions (5 workflows) ⭐ v7.0.0

### Quick Stats
- **Data**: 471 products → 3,246 atomic chunks
- **Search Quality**: 0.79-0.82 similarity
- **Response Time**: < 500ms (NexaAI) / ~2s (Ollama)
- **WebSocket Latency**: < 10ms
- **Cost Savings**: $17,460+/year vs commercial alternatives

**Details**: `§rag.status`, `PROGRESS.md`, `README.md`

---

## 🎯 Symbol Quick Access

> **Load specific docs**: Use `§symbol` to load 50-200 lines instead of 500-1000 lines

### Core Systems
- `§rag.*` - RAG system (chunking, search, OCR, engines)
- `§saas.*` - SaaS platform (auth, billing, tenants, usage)
- `§collector.*` - Data collection (web, API, file, scheduling)
- `§manufacturing.*` - Manufacturing (vision, devices, quality)
- `§realtime.*` - Realtime backend (Socket.IO, PostgreSQL, Redis) ⭐ NEW

### Infrastructure (v7.0.0)
- `§security.*` - Keycloak OAuth2/OIDC, Vault secrets
- `§observe.*` - Jaeger tracing, Prometheus, Grafana
- `§data.*` - MinIO storage, Airflow ETL, Metabase BI

### Development
- `§api.*` - API endpoints (48+)
- `§debug.*` - Debug system (8 endpoints)
- `§deploy.*` - Deployment (Docker, K8s, CI/CD)
- `§arch.*` - Architecture (services, layers, databases)

**Complete Map**: `docs/reference/SYMBOLS.md` (200 lines, 80% reduction)

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
| Frontend | 8080 | http://localhost:8080/realtime-demo.html |

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

### Development
\`\`\`bash
# Deploy
./scripts/deploy-optimized.sh development
make dev  # Alternative

# Test
./scripts/test-optimized.sh
make test

# Restart Everything
./scripts/restart-all.sh

# Check Health
curl http://localhost:8001/health/ready
\`\`\`

### Docker
\`\`\`bash
# Start/Stop
docker-compose up -d
docker-compose down

# Restart Service
docker-compose restart api
docker-compose restart qdrant

# Logs
docker-compose logs -f api
\`\`\`

### Database
\`\`\`bash
# Migrations
alembic upgrade head
alembic downgrade -1
alembic history

# Make commands
make migrate-upgrade
make migrate-downgrade
\`\`\`

### Testing
\`\`\`bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov=app

# Specific test
pytest tests/test_search.py -v

# Make commands
make test
make test-cov
\`\`\`

### Code Quality
\`\`\`bash
# Format
make format  # Black + isort

# Lint
make lint    # flake8

# Type check
make type-check  # mypy

# All checks
make setup && make format && make lint && make test
\`\`\`

**Full Commands**: `docs/guides/QUICK_REFERENCE.md`

---

## 🐛 Quick Troubleshooting

### Automated Fix
\`\`\`bash
# One-command restart everything
./scripts/restart-all.sh
\`\`\`

### Manual Fixes
\`\`\`bash
# Port in use
lsof -i :8001 && kill -9 <PID>

# Docker reset
docker-compose down -v && docker-compose up -d

# Ollama not responding
docker-compose restart ollama

# Frontend not loading
cd frontend && python3 -m http.server 8080 &
\`\`\`

### Health Checks
\`\`\`bash
# API
curl http://localhost:8001/health/ready

# Qdrant
curl http://localhost:6333/health

# Redis
docker exec redis redis-cli ping

# PostgreSQL
docker exec postgres pg_isready
\`\`\`

**Full Troubleshooting**: `docs/guides/TROUBLESHOOTING.md`

---

## 📚 Documentation Index

### Quick Access
- **CLAUDE.md** - This file (quick reference, 300 lines)
- **README.md** - Project overview (simplified)
- **PROGRESS.md** - Version history (v1.0.0 → v7.0.0+)

### Symbol System
- **docs/reference/SYMBOLS.md** - Complete symbol map (200 lines, -80%)

### Guides (How-to)
- **docs/guides/QUICK_REFERENCE.md** - Common commands
- **docs/guides/LOCAL_SETUP.md** - Setup guide
- **docs/guides/TROUBLESHOOTING.md** - Common issues
- **docs/guides/DEPLOYMENT_GUIDE.md** - Deployment

### Reference (Technical)
- **docs/reference/API_DOCUMENTATION.md** - API endpoints
- **docs/reference/DEBUG_SYSTEM.md** - Debug features

### Architecture (Deep Dive)
- **docs/V7_COMPLETE_GUIDE.md** - v7.0.0 production guide (500+)
- **docs/REALTIME_BACKEND_GUIDE.md** - Realtime backend (500+)
- **docs/SAAS_ARCHITECTURE.md** - SaaS platform (800+)
- **docs/DATA_COLLECTOR_ARCHITECTURE.md** - Data collection (600+)
- **docs/MANUFACTURING_AUTOMATION.md** - Manufacturing (500+)
- **docs/RAG_ACTIVATION_STRATEGY.md** - RAG system (500+)
- **docs/OCR_PARSING_STRATEGY.md** - OCR pipeline (300+)
- **docs/NEXA_SDK_INTEGRATION_PLAN.md** - NexaAI integration (400+)
- **docs/OPEN_SOURCE_ARCHITECTURE.md** - Open source stack (400+)
- **docs/ARCHITECTURE.md** - System architecture (600+)

---

## 🎨 Active SKILLs

### RAG & Data
- **rag-pipeline** - RAG orchestration
- **chunking-expert** - Advanced chunking strategies ⭐
- **embedding-expert** - Embedding optimization ⭐
- **nexa-rag-optimizer** - Query optimization
- **multimodal-processor** - Multi-modal processing
- **data-collector** - Universal data collection ⭐

### Platform
- **saas-platform** - SaaS management ⭐
- **frontend-platform** - UI design system ⭐
- **debugging-expert** - Chrome DevTools debugging ⭐

### Domain
- **manufacturing-expert** - Manufacturing docs ⭐
- **packaging-expert** - Packaging docs ⭐
- **web-crawler-pipeline** - Web scraping automation ⭐

**Location**: `.claude/skills/` (progressive disclosure)

---

## 🔌 MCP Integration

### Main Project (Token-Optimized)
- **filesystem** - File operations ($0)

### Sub-Agents (8 Specialized Agents)
1. **crawling-agent** - Web scraping (puppeteer, fetch, chrome-devtools)
2. **frontend-agent** - React/Tailwind (shadcn-ui, chrome-devtools)
3. **data-agent** - Database ops (postgres, sqlite)
4. **code-review-agent** - PR reviews (github)
5. **rag-agent** - RAG optimization (pure Python)
6. **testing-agent** - Test automation (pytest)
7. **deployment-agent** - Docker/K8s (CLI)
8. **monitoring-agent** - Performance (Prometheus/Grafana)

**Priority MCPs**:
- ⭐ **testsprite** - AI testing (1000 free/month, 42% → 93% quality)
- **tavily** - AI search (1000 free/month)
- **github** - Unlimited for public repos

**Config**: `.claude/mcp.json`, `.claude/agents/*/agent.json`

---

## 💡 Key Principles

### Symbol System
1. **Check SYMBOLS.md first** - Find exact symbol
2. **Load only needed** - `§symbol` loads 50-200 lines vs 500-1000
3. **70-80% token savings** - 4-5x more efficient

### Documentation
- **CLAUDE.md** - Quick reference (this file, 300 lines)
- **SYMBOLS.md** - Symbol map (200 lines)
- **Guides** - How-to (100-300 lines each)
- **References** - Technical (300-1000 lines)
- **Architecture** - Deep dive (500-800 lines)

### Session Protocol
\`\`\`bash
# Start
git status && git branch

# During
1. Use TodoWrite for >2 steps
2. Run tests before commit
3. Update docs if API/arch changes

# End
- Git status clean
- Todos resolved
- Tests passing
- Background processes killed
\`\`\`

---

## 🎉 Quick Wins

\`\`\`bash
# 1. Start Everything
./scripts/deploy-optimized.sh development

# 2. Test Realtime Backend (NEW!)
open http://localhost:8080/realtime-demo.html

# 3. Test RAG Search
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'

# 4. View Monitoring
open http://localhost:3000  # Grafana (admin/admin)

# 5. View Tracing
open http://localhost:16686  # Jaeger
\`\`\`

---

**v7.0.0+** | **2025-11-09** | **Production Ready** | **MIT** | **$0/month**

**Token Optimization**: 946 → 300 lines (-68%) • Use `§symbols` for details
**Quick Start**: `./scripts/deploy-optimized.sh development && open http://localhost:8080/realtime-demo.html`
**Full Docs**: `docs/V7_COMPLETE_GUIDE.md`, `docs/REALTIME_BACKEND_GUIDE.md`, `PROGRESS.md`
