# RAG Enterprise Platform v10.0.0 "Unified Maximum"

**Philosophy**: Maximal Features + Minimal Structure

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-10.0.0-green.svg)](CHANGELOG.md)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](tests/)

---

## 🎯 What is RAG Enterprise?

Ultimate open-source RAG (Retrieval-Augmented Generation) platform with:
- **Pure Black Design** (#000000, no icons, natural theme)
- **20 Services** ($0/month software cost)
- **80+ APIs** (FastAPI, production-ready)
- **4 Apps** (Web, PWA, Mobile, API)
- **Zero Duplication** (monorepo, shared packages)
- **80%+ Test Coverage** (unit + integration + E2E)

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/rkqksk/new_rag_ubuntu.git
cd new_rag_ubuntu

# 2. Deploy
./scripts/deploy-optimized.sh development

# 3. Open
open http://localhost:3000  # Web app (Pure Black UI)
open http://localhost:8001/api/v1/docs  # API docs
open http://localhost:5000  # MLflow (experiments)
open http://localhost:3000  # Grafana (monitoring)
```

---

## 📁 Structure (8 Directories)

```
new_rag_ubuntu/
├── apps/                   # Applications
│   ├── api/               # FastAPI backend (unified)
│   ├── web/               # Next.js 15 (Pure Black)
│   ├── pwa/               # Vite PWA
│   └── mobile/            # Expo (React Native)
├── packages/              # Shared packages
│   ├── ui/                # React components (shadcn)
│   ├── core/              # Business logic
│   ├── config/            # Settings
│   └── utils/             # Utilities
├── services/              # Microservices
│   ├── rag/              # RAG engine
│   ├── collector/        # Data collection
│   ├── manufacturing/    # Vision AI (YOLO)
│   ├── realtime/         # Socket.IO
│   └── ml/               # MLflow experiments
├── infrastructure/        # IaC
│   ├── docker/           # Docker Compose
│   ├── k8s/              # Kubernetes + Helm
│   ├── terraform/        # AWS/GCP/Azure
│   └── observability/    # Grafana dashboards
├── tools/                 # Dev tools
│   ├── scripts/          # Automation
│   ├── cli/              # CLI tools
│   └── generators/       # Code generators
├── .claude/              # Claude Code
│   ├── skills/           # 9 Skills (100% validated)
│   ├── commands/         # Slash commands
│   └── mcp/              # MCP servers
├── docs/                  # Documentation
│   ├── guides/           # How-to
│   ├── reference/        # API docs
│   ├── architecture/     # Architecture
│   └── design/           # Design system
└── workflows/            # CI/CD
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

| Metric | v9.3.0 | v10.0.0 | Change |
|--------|--------|---------|--------|
| Top-level dirs | 33 | 8 | -76% |
| Code duplication | 40-60% | <5% | -90% |
| Test coverage | 40-50% | 80%+ | +60% |
| Build time | 8+ min | <3 min | -62% |
| APIs | 48+ | 80+ | +67% |
| Components | ~20 | 60+ | +200% |

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
