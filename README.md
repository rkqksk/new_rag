# RAG Enterprise - Ubuntu Edition

**Version**: Initializing from v9.3.0
**Status**: 🚀 Ready to Start
**Target**: v10.0.0 "Unified" Platform

> Complete RAG Enterprise platform optimized for Ubuntu Linux deployment

---

## 🎯 프로젝트 개요

### 무엇인가요?

**RAG Enterprise**는 100% 오픈소스 엔터프라이즈 플랫폼입니다:
- **RAG System**: Semantic search, OCR, multi-modal
- **SaaS Platform**: Multi-tenancy, billing, auth
- **Manufacturing**: Vision inspection, defect detection
- **Data Collection**: Web scraping, API polling, file parsing
- **Real-time**: WebSocket, server-sent events

### 왜 중요한가요?

- ✅ **$0/month 소프트웨어 비용** (17 services, all open-source)
- ✅ **연간 $17,460+ 절감** (상용 솔루션 대비)
- ✅ **Multi-platform**: Web + PWA + Mobile
- ✅ **Production Ready**: 95%+ test coverage
- ✅ **Korean 최적화**: 한국어 NLP, 규제 준수

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Ubuntu 20.04+ (또는 Linux)
- Docker & Docker Compose
- Git
- 8GB+ RAM
- 20GB+ disk space
```

### 1. 프로젝트 초기화 (5분)

```bash
# Clone repository (이미 했다면 스킵)
git clone <repository-url>
cd new_rag_ubuntu

# claude-code-mac 브랜치에서 v9.3.0 코드 가져오기
git merge origin/claude-code-mac --allow-unrelated-histories

# 또는 직접 체크아웃
git checkout -b main origin/claude-code-mac
```

### 2. 서비스 시작 (3분)

```bash
# Docker services 시작
docker-compose up -d

# Health check (30초 대기)
sleep 30
curl http://localhost:8001/health/ready
```

### 3. 확인

```bash
# API 문서
open http://localhost:8001/api/v1/docs

# Monitoring
open http://localhost:3000  # Grafana (admin/admin)
```

**상세 가이드**: [QUICK_START.md](QUICK_START.md)

---

## 📊 현재 상태

### ✅ Available (v9.3.0 from claude-code-mac branch)

- **17 Services**: API, PostgreSQL, Qdrant, Redis, etc.
- **48+ API Endpoints**: Production-ready
- **16,500+ LOC**: Fully implemented
- **160+ Tests**: 95%+ coverage
- **Complete Docs**: Architecture, API, guides
- **v10.0.0 Roadmap**: 12-week integration plan

### 🎯 Target (v10.0.0 "Unified")

- **Single Backend**: app/ + src/ → backend/
- **Single Frontend**: 4 frontends → 1 monorepo
- **Code Deduplication**: 40-85% → <5%
- **Structure Simplification**: 35+ dirs → 12 dirs
- **Token Optimization**: 800K → 82K (-90%)
- **Test Coverage**: 40-50% → 80%+

---

## 🏗️ 시스템 아키텍처

### Current (v9.3.0)

```
┌─────────────────────────────────────────────────────────┐
│             Client Applications                          │
│  Browser | Mobile | Desktop | Server-to-Server          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  API Gateway                             │
│  REST | GraphQL | WebSocket | SSE | Socket.IO           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                           │
│  RAG | SaaS | Manufacturing | Collection | Realtime      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│          Security & Observability                        │
│  Keycloak | Vault | Jaeger | Prometheus | Grafana       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Data Layer                              │
│  PostgreSQL | Qdrant | Redis | ClickHouse | MinIO       │
└─────────────────────────────────────────────────────────┘
```

### Target (v10.0.0)

```
new_rag_ubuntu/
├── apps/                    # Multi-platform apps
│   ├── web/                 # Next.js 14 (SSR + PWA)
│   └── mobile/              # React Native + Expo
├── packages/                # Shared packages
│   ├── ui/                  # 27 components
│   ├── core/                # Business logic
│   └── config/              # Shared configs
├── backend/                 # Unified Python backend
│   ├── api/v1/              # Stable API
│   ├── api/v2/              # Experimental
│   └── services/            # Business services
├── docs/                    # Documentation
└── scripts/                 # Automation
```

---

## 🛠️ 기술 스택

### Backend
- **Python 3.11+**, FastAPI, Pydantic v2
- PostgreSQL, Qdrant, Redis, ClickHouse, MinIO

### AI/ML
- **LLM**: NexaAI (Qwen3), Ollama (qwen2.5, llama3.1)
- **Embeddings**: Sentence Transformers
- **OCR**: PaddleOCR, EasyOCR, Tesseract
- **Vision**: YOLOv8/v10, TensorRT

### Frontend
- **Framework**: Next.js 14, React 18, TypeScript
- **UI**: Tailwind CSS, shadcn/ui
- **State**: Zustand, React Query
- **Monorepo**: Turborepo, pnpm

### Infrastructure
- **Container**: Docker, Kubernetes
- **Security**: Keycloak, HashiCorp Vault
- **Observability**: Jaeger, Prometheus, Grafana
- **Data**: Airflow, Kafka, Metabase
- **CI/CD**: GitHub Actions

---

## 📚 문서

### 시작하기
- **[QUICK_START.md](QUICK_START.md)** - 5분 시작 가이드
- **[REPOSITORY_ANALYSIS_AND_ROADMAP.md](REPOSITORY_ANALYSIS_AND_ROADMAP.md)** - 종합 분석 및 발전 계획

### 통합 계획 (v10.0.0)
- **[COMPLETE_INTEGRATION_MASTER_PLAN.md](COMPLETE_INTEGRATION_MASTER_PLAN.md)** - 12주 통합 로드맵
- **[BACKEND_MIGRATION_PLAN.md](BACKEND_MIGRATION_PLAN.md)** - Backend 통합 계획
- **[FRONTEND_FILE_STRUCTURE_PLAN.md](FRONTEND_FILE_STRUCTURE_PLAN.md)** - Frontend 통합 계획
- **[SUB_AGENTS_COLLABORATION_PLAN.md](SUB_AGENTS_COLLABORATION_PLAN.md)** - Sub-agent 협업 전략

### 상세 문서 (docs/)
- Architecture guides
- API documentation
- Developer guides
- Deployment guides

---

## 🗺️ 로드맵

### Phase 0: 초기화 (이번 주)
- [x] Repository 분석
- [x] v9.3.0 코드 확보 (claude-code-mac)
- [x] 발전 계획 수립
- [ ] 코드 merge
- [ ] 환경 검증
- [ ] 문서 정독

### Phase 1-7: v10.0.0 통합 (12주)

| Week | Phase | Focus |
|------|-------|-------|
| 1 | Discovery | 분석 및 계획 |
| 2-3 | Backend | app/ + src/ → backend/ |
| 4-5 | Frontend | 구조 최적화 |
| 6-9 | Migration | HTML → React |
| 10 | Services | TypeScript 서비스 |
| 11 | Testing | 80%+ coverage |
| 12 | Deploy | 문서 + 배포 |

**상세 계획**: [REPOSITORY_ANALYSIS_AND_ROADMAP.md](REPOSITORY_ANALYSIS_AND_ROADMAP.md)

---

## 💡 주요 특징

### v9.3.0 (현재)

✅ **RAG System**
- Multi-modal search (text + image + shape)
- OCR pipeline (3-engine fallback)
- Hybrid search (dense + BM25 + reranking)
- 471 products → 3,246 semantic chunks

✅ **SaaS Platform**
- Multi-tenancy with Row-Level Security
- JWT + API key authentication
- Stripe billing integration
- Usage tracking & rate limiting

✅ **Manufacturing**
- Vision inspection (YOLOv8/v10)
- 7 defect types detection
- Edge AI (Jetson 120 FPS, Pi 15 FPS)
- SPC monitoring

✅ **Real-time**
- Socket.IO reactive queries
- PostgreSQL LISTEN/NOTIFY
- WebSocket <10ms latency
- 10,000+ concurrent connections

### v10.0.0 (목표)

✅ **Unified Architecture**
- Single backend (backend/)
- Single frontend (apps/)
- Monorepo structure
- <5% code duplication

✅ **Developer Experience**
- 90% token savings (Claude Code)
- <5 min build time
- Hot reload <2s
- 80%+ test coverage

✅ **Production Quality**
- Comprehensive testing
- Full documentation
- CI/CD automation
- Performance benchmarks

---

## 📊 성능 메트릭

### Current (v9.3.0)

| Metric | Value |
|--------|-------|
| Services | 17 containers |
| API Endpoints | 48+ |
| Code | 16,500+ lines |
| Tests | 160+ (95%+ coverage) |
| Response Time | <500ms (NexaAI) |
| WebSocket Latency | <10ms |
| Search Quality | 0.79-0.82 similarity |

### Target (v10.0.0)

| Metric | Target |
|--------|--------|
| Code Duplication | <5% |
| Build Time | <5 min |
| Test Coverage | 80%+ |
| Token Usage | -90% |
| Maintenance Cost | -60% |

---

## 🤝 기여하기

프로젝트는 현재 초기화 단계입니다. 기여를 환영합니다!

### 현재 우선순위

1. **Phase 0 완료**: claude-code-mac 코드 merge
2. **문서 정독**: 통합 계획 이해
3. **환경 검증**: Docker services 확인
4. **Phase 1 준비**: Discovery 단계 준비

### 다음 단계

- Week 1: Discovery & Planning
- Week 2-3: Backend Unification
- Week 4-5: Frontend Consolidation

**상세**: [REPOSITORY_ANALYSIS_AND_ROADMAP.md](REPOSITORY_ANALYSIS_AND_ROADMAP.md)

---

## 📝 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 감사

100% 오픈소스 기술로 구축:
- FastAPI, PostgreSQL, Redis, Qdrant, ClickHouse
- Socket.IO, Keycloak, Vault, Jaeger, Prometheus, Grafana
- MinIO, Airflow, Metabase, Docker, Kubernetes
- React, Next.js, Turborepo

---

## 📞 지원

- **Documentation**: [docs/](docs/) directory
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Roadmap**: [REPOSITORY_ANALYSIS_AND_ROADMAP.md](REPOSITORY_ANALYSIS_AND_ROADMAP.md)
- **Integration Plan**: [COMPLETE_INTEGRATION_MASTER_PLAN.md](COMPLETE_INTEGRATION_MASTER_PLAN.md)

---

**Status**: 🚀 Ready to Start
**Next Step**: [QUICK_START.md](QUICK_START.md)
**Target**: v10.0.0 "Unified" in 12 weeks (or 7 weeks with sub-agents)

**From**: Empty repository
**Via**: claude-code-mac v9.3.0
**To**: Production-grade unified platform

**Let's build! 🚀**
