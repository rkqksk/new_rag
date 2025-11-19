# RAG Enterprise Platform v10.0.0 "Unified Maximum"

**Philosophy**: Maximal Features + Minimal Structure

**Status**: Phase 1-2 Complete (75% Overall) - Backend Ready, Frontend In Progress

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-10.0.0-orange.svg)](CHANGELOG.md)
[![Migration](https://img.shields.io/badge/migration-75%25-yellow.svg)](V10_EXECUTION_PLAN.md)
[![Backend](https://img.shields.io/badge/backend-95%25-brightgreen.svg)](apps/api)
[![Frontend](https://img.shields.io/badge/frontend-70%25-yellow.svg)](apps/web)

---

## 🎯 What is RAG Enterprise?

Ultimate open-source RAG (Retrieval-Augmented Generation) platform with:
- **Pure Black Design** (#000000, no icons, natural theme) ✅
- **20 Services** ($0/month software cost) ✅
- **80+ APIs** (FastAPI, production-ready) ✅
- **Unified Backend** (apps/api, 95% complete) ✅
- **Multi-platform Frontend** (Web 70%, PWA/Mobile scaffolds) ⚙️
- **Monorepo Structure** (8 directories, -76% from v9) ✅
- **Monolith-First** (services/ are scaffolds, apps/api has all features) ⚙️

## 🚧 Migration Status

**Completed (Phase 1-2)**:
- ✅ Backend unification: `app/ + backend/ + src/` → `apps/api/` (95%)
- ✅ Directory restructuring: 33 → 8 directories (-76%)
- ✅ Legacy code archived: `.archive/{app,backend,src}-v9/`
- ✅ Tests updated and passing
- ✅ Icon violations removed
- ✅ Infrastructure configs ready

**In Progress (Phase 3)**:
- ⚙️ Frontend migration: 52/60 components (87%)
- ⚙️ Package implementations: Structure done, logic partial (60%)
- ⚙️ Remaining 8 components to migrate

**Future (Phase 4+)**:
- ⚠️ Microservices: Scaffolds only (10%)
- ⚠️ PWA/Mobile apps: Scaffolds only (10%)

**Overall**: ~75% complete (not 100% as previously claimed)

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/rkqksk/new_rag_ubuntu.git
cd new_rag_ubuntu

# 2. Start Backend (Fully Working)
cd apps/api
uvicorn main:app --reload --port 8001

# 3. View API
open http://localhost:8001/api/v1/docs  # Swagger UI

# 4. Frontend (Partial - 8 components to migrate)
cd apps/web
npm run dev
open http://localhost:3000  # Web app (70% complete)

# Note: Use backend API directly until frontend migration completes
```

---

## 📁 Structure (8 Directories)

```
new_rag_ubuntu/
├── apps/                   # Applications
│   ├── api/               # FastAPI backend (unified) ✅ 95%
│   ├── web/               # Next.js 15 (Pure Black) ⚙️ 70%
│   ├── pwa/               # Vite PWA (scaffold) ⚠️ 10%
│   └── mobile/            # Expo (React Native, scaffold) ⚠️ 10%
├── packages/              # Shared packages ⚙️ 60%
│   ├── ui/                # React components (52/60 migrated)
│   ├── core/              # Business logic (structure done)
│   ├── config/            # Settings (structure done)
│   └── utils/             # Utilities (structure done)
├── services/              # Microservices ⚠️ 10%
│   ├── rag/              # RAG engine (scaffold only)
│   ├── collector/        # Data collection (scaffold only)
│   ├── manufacturing/    # Vision AI (scaffold only)
│   ├── realtime/         # Socket.IO (scaffold only)
│   └── ml/               # MLflow (scaffold only)
│   Note: All functionality currently in apps/api (monolith-first)
├── infrastructure/        # IaC ✅ 95%
│   ├── docker/           # Docker Compose
│   ├── k8s/              # Kubernetes + Helm
│   ├── terraform/        # AWS/GCP/Azure
│   └── observability/    # Grafana dashboards
├── tools/                 # Dev tools ✅ 90%
├── .claude/              # Claude Code ✅ 100%
│   ├── skills/           # 9 Skills (validated)
│   ├── commands/         # Slash commands
│   └── mcp/              # MCP servers
├── docs/                  # Documentation ✅ 100%
└── workflows/            # CI/CD ⚙️ 70%
└── .archive/             # Preserved v9 code ✅
    ├── app-v9/           # 1.9M
    ├── backend-v9/       # 2.1M
    └── src-v9/           # 2.5M
```

---

## ✨ Features

### Advanced RAG
- Cross-encoder re-ranking
- Hybrid search (BM25 + semantic)
- Query expansion (LLM-powered)
- Multi-language (KR, EN, JP, CN)
- Chat history + citations

### Pure Black Design
- **Background**: #000000 (pure black, always)
- **Icons**: None (text-only UI)
- **Theme**: Natural, minimal, organic
- **Components**: shadcn UI (customized)

See [Design System](docs/design/DESIGN_SYSTEM.md)

### MLOps
- MLflow experiment tracking
- A/B testing framework
- Model monitoring (drift detection)

### Infrastructure
- 20 containerized services
- Kubernetes + Helm charts
- Terraform (AWS/GCP/Azure)
- GitOps (ArgoCD)
- 20+ Grafana dashboards

---

## 📊 Metrics

| Metric | v9.3.0 | v10.0.0 (Target) | v10.0.0 (Actual) | Status |
|--------|--------|------------------|------------------|--------|
| Top-level dirs | 33 | 8 | 8 | ✅ -76% |
| Code duplication | 40-60% | <5% | <5% | ✅ -90% |
| Backend completion | Fragmented | 100% | 95% | ✅ Functional |
| Frontend completion | Multiple versions | 100% | 70% | ⚙️ 52/60 components |
| Package completion | Mixed | 100% | 60% | ⚙️ Structure done |
| Services completion | N/A | 100% | 10% | ⚠️ Scaffolds only |
| Test coverage | 40-50% | 80%+ | Tests passing | ✅ Updated |
| APIs | 48+ | 80+ | 80+ | ✅ +67% |

---

## 🛠️ Development

```bash
# Backend
cd apps/api
uvicorn main:app --reload --port 8001

# Frontend
cd apps/web
npm run dev  # http://localhost:3000

# Tests
pytest tests/ -v --cov=apps --cov=packages

# Code quality
ruff check . --fix
black . --line-length 100
```

---

## 📚 Documentation

- **Quick Start**: This file
- **Migration**: [V9_TO_V10_MIGRATION.md](docs/guides/V9_TO_V10_MIGRATION.md)
- **Design System**: [DESIGN_SYSTEM.md](docs/design/DESIGN_SYSTEM.md)
- **API Reference**: [openapi-v10.json](docs/reference/openapi-v10.json)
- **Architecture**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Full Guide**: [V10_MAXIMAL_UPGRADE_PLAN.md](V10_MAXIMAL_UPGRADE_PLAN.md)

---

## 🤝 Contributing

1. Read [Design System](docs/design/DESIGN_SYSTEM.md) (ABSOLUTE rules)
2. Check coverage: `pytest --cov=. --cov-report=html`
3. Format code: `black . && ruff check . --fix`
4. Submit PR (follow template)

**Design Rules**:
- ✅ Pure black background (#000000)
- ❌ NO icons (text only)
- ✅ Natural theme (minimal, organic)

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- **shadcn/ui** - Component base (customized for black theme)
- **FastAPI** - Backend framework
- **Next.js** - Frontend framework
- **Claude Code** - Development environment

---

**Built with**: Maximal → Minimal philosophy 🖤
