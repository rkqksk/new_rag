# Changelog

## [10.0.0] - 2025-11-16

### 🎉 Major Release: "Unified Maximum"

**Philosophy**: Maximal Features + Minimal Structure

### ✨ Added

#### Structure
- **Backend Unified**: `app/ + backend/ + src/` → `apps/api/` (zero duplication)
- **Frontend Monorepo**: `apps/{web,pwa,mobile}` (Turborepo)
- **Shared Packages**: `packages/{core,config,utils}` (DRY principle)
- **8 top-level directories** (down from 33, -76% complexity)

#### Features
- **Advanced RAG**:
  - Cross-encoder re-ranking
  - Hybrid search (BM25 + semantic)
  - Query expansion (LLM-powered)
  - Contextual compression
  - Chat history (Redis + PostgreSQL)
  - Citations tracking
- **MLOps**: MLflow experiment tracking, A/B testing framework
- **Modern UI**: Next.js 15 + Pure Black theme + NO Icons + Natural design
- **Real-time**: Socket.IO client, reactive queries
- **i18n**: Korean, English, Japanese, Chinese
- **Offline**: Service Worker + IndexedDB
- **Testing**: 80%+ coverage (unit + integration + E2E)

#### Infrastructure
- **Terraform**: AWS/GCP/Azure modules
- **Helm**: Kubernetes charts
- **GitOps**: ArgoCD integration
- **Observability**: 20+ Grafana dashboards

### 🎨 Design System
- **Pure Black** (#000000) - absolute rule
- **NO Icons** - text-only UI
- **Natural Theme** - minimal, organic
- **shadcn UI** - customized for black theme

### 🔧 Changed
- Import paths: `from app.*` → `from apps.api.*`
- Configuration: Centralized in `packages/config/settings.py`
- API routes: `/api/v1/` (stable), `/api/v2/` (experimental)

### 🗑️ Removed
- Duplicate backend directories (`app/`, `backend/`, `src/`)
- Fragmented frontends (`frontend/`, `frontend-next/`, `frontend-v2/`)
- Dead code (coverage analysis)
- TODO/FIXME comments (resolved or tracked in issues)

### 📊 Metrics
- **Directories**: 33 → 8 (-76%)
- **Code Duplication**: 40-60% → <5% (-90%)
- **Test Coverage**: 40-50% → 80%+ (+60%)
- **Build Time**: 8+ min → <3 min (-62%)
- **APIs**: 48+ → 80+ (+32)
- **Components**: ~20 → 60+ (+40)

### 🚀 Migration
See [V9_TO_V10_MIGRATION.md](docs/guides/V9_TO_V10_MIGRATION.md)

### 📝 Rollback
```bash
git reset --hard v9.3.0-backup
./scripts/restart-all.sh
```

---

## [9.3.0] - 2025-11-09

See PROGRESS.md for v9.3.0 details.
