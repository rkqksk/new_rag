# Microservices Extraction Roadmap

**Version**: v10.0.0  
**Status**: Planned (Post-v10.0.0)  
**Last Updated**: 2025-11-19

## Overview

The current architecture consolidates all business logic in `apps/api/` (monolithic FastAPI backend). This roadmap outlines the planned extraction of functionality into independent microservices.

**Philosophy**: Extract after core implementation matures, not before.

---

## Current Architecture (v10.0.0)

### Monolithic Backend (`apps/api/`)

All services currently integrated into single FastAPI application:

```
apps/api/
├── core/                     # Core business logic
│   ├── routing/             # Request routing (intent, ML, LLM)
│   ├── realtime/            # WebSocket + Socket.IO
│   └── health/              # Health checks
├── rag_consultation/         # RAG engine
│   ├── retrieval/           # Search & context
│   ├── generation/          # Response generation
│   └── context/             # Conversation state
├── services/                # Business services
│   ├── rag_qa_service.py   # Q&A logic
│   ├── search_service.py    # Search logic
│   └── analytics_service.py # Analytics
├── repositories/            # Data access layer
│   ├── postgres_repository  # SQL queries
│   ├── qdrant_repository    # Vector search
│   └── redis_repository     # Caching
└── middleware/              # Cross-cutting concerns
    ├── auth                 # JWT/API key
    ├── logging              # Structured logging
    └── monitoring           # Metrics & tracing
```

**Benefits**: Unified code, shared libraries, simpler development  
**Trade-offs**: Monolithic scaling, slower deployment cycles

---

## Phase-Based Extraction Plan

### Phase 1: Foundation (Current - v10.0.0)

**Goal**: Stabilize core implementation in monolithic app

**Activities**:
- Complete RAG engine implementation
- Finalize SaaS infrastructure (auth, billing, tenants)
- Implement manufacturing vision pipelines
- Establish data collection patterns
- Build realtime messaging foundation
- Achieve 80%+ test coverage
- Document all APIs and architectural decisions

**Timeline**: In progress (Completed 2025-11-19)

**Outcome**: Production-ready monolith with clear service boundaries

---

### Phase 2: Service Extraction (Post-v10.0.0)

**Goal**: Extract services into independent deployable units

**Timeline**: Q2 2025 (6-12 months after v10 stabilization)

#### 2a. RAG Service

**What to Extract**:
- `apps/api/rag_consultation/`
- `apps/api/services/rag_qa_service.py`
- `apps/api/services/advanced_query_optimizer.py`
- Vector/semantic search logic

**Service Scope**:
```
RAG Service
├── retrieval/           # Semantic search + context
├── generation/          # Response generation with LLM
├── query_optimization/  # Query expansion & rewriting
└── conversation/        # Multi-turn Q&A state
```

**Port**: `8002`  
**Tech**: FastAPI + Qdrant + OpenAI/Claude  
**Scaling**: Horizontal (stateless)

**Dependencies**:
- Qdrant (vector DB)
- PostgreSQL (conversation history)
- OpenAI/Claude APIs
- Redis (caching)

**Extraction Effort**: Medium (2-3 weeks)

#### 2b. Data Collector Service

**What to Extract**:
- Web scraping logic
- API polling mechanisms
- File parsing (Excel, PDF, CSV, JSON, XML, HTML)
- Data validation & transformation
- Job scheduling (Airflow integration)

**Service Scope**:
```
Collector Service
├── scraper/             # Web scraping + crawling
├── api_poller/          # REST API polling
├── file_parser/         # Multi-format parsing
├── validator/           # Data quality checks
└── scheduler/           # Job orchestration
```

**Port**: `8004`  
**Tech**: FastAPI + Scrapy + Airflow  
**Scaling**: Horizontal (distributed collectors)

**Dependencies**:
- PostgreSQL (job metadata)
- Redis (job queue)
- Airflow (scheduling)
- S3/MinIO (file storage)

**Extraction Effort**: Medium (2-3 weeks)

#### 2c. Manufacturing Vision Service

**What to Extract**:
- YOLO model integration
- Image classification logic
- Defect detection pipelines
- Quality metrics calculation
- Model serving (ONNX, TensorRT)

**Service Scope**:
```
Manufacturing Service
├── inference/           # Model inference (YOLO)
├── preprocessing/       # Image processing
├── postprocessing/      # Result formatting
├── metrics/             # Quality metrics
└── models/              # Model management
```

**Port**: `8005`  
**Tech**: FastAPI + YOLO + TensorRT  
**Scaling**: Horizontal (with GPU support)

**Dependencies**:
- PostgreSQL (results storage)
- S3/MinIO (model storage)
- Redis (job queue)
- NVIDIA GPU (inference)

**Extraction Effort**: Medium (2-3 weeks)

#### 2d. ML Service

**What to Extract**:
- Embeddings generation
- LLM inference
- Model serving
- Batch processing
- Model management

**Service Scope**:
```
ML Service
├── embeddings/          # Text embeddings
├── inference/           # LLM inference
├── models/              # Model management
├── batch/               # Batch processing
└── optimization/        # ONNX/TensorRT
```

**Port**: `8006`  
**Tech**: FastAPI + Sentence Transformers + PyTorch  
**Scaling**: Horizontal (with GPU for LLMs)

**Dependencies**:
- PostgreSQL (cache metadata)
- Redis (request queue)
- S3/MinIO (model storage)
- GPU (optional, LLM inference)

**Extraction Effort**: Low-Medium (1-2 weeks)

#### 2e. Realtime Service

**What to Extract**:
- WebSocket/Socket.IO logic
- Redis Pub/Sub integration
- PostgreSQL LISTEN/NOTIFY
- Connection management
- Room-based broadcasting

**Service Scope**:
```
Realtime Service
├── websocket/           # Socket.IO server
├── pubsub/              # Redis Pub/Sub
├── listeners/           # PostgreSQL LISTEN
├── rooms/               # Room management
└── presence/            # User presence
```

**Port**: `8003`  
**Tech**: Node.js + Socket.IO + Redis  
**Scaling**: Horizontal (stateless with Redis Adapter)

**Dependencies**:
- Redis (Pub/Sub + Adapter)
- PostgreSQL (event listener)
- Main API (event source)

**Extraction Effort**: Low (1 week)

---

### Phase 3: Service Optimization (Post-Phase 2)

**Goal**: Optimize services for production deployment

**Timeline**: Q3 2025 (After extraction)

**Activities**:
- Edge deployment optimization (ONNX, TensorRT)
- Service-to-service communication patterns
- Distributed tracing across services
- Service mesh (Istio) integration
- Circuit breakers and resilience patterns
- Database per service strategy (if needed)
- API gateway consolidation

**Key Decisions**:
- **Communication**: REST APIs vs gRPC vs Kafka (event-driven)
- **Data Sync**: ETL pipelines vs event sourcing
- **Deployment**: Independent or coordinated scaling
- **Observability**: Centralized logging and tracing

---

### Phase 4: Production Kubernetes Deployment (Post-Phase 3)

**Goal**: Deploy all services independently to K8s

**Timeline**: Q4 2025

**Infrastructure**:
- Kubernetes cluster (EKS/GKE/AKS)
- Helm charts for each service
- ArgoCD for GitOps
- Service mesh (Istio)
- Centralized logging (ELK/Loki)
- Metrics (Prometheus)
- Distributed tracing (Jaeger)

**CI/CD Pipeline**:
- Build service docker images
- Push to container registry
- ArgoCD triggers K8s deployment
- Automated health checks
- Blue-green deployments

---

## Service Interaction Patterns

### Phase 2 Era (Services Extract)

```
┌─────────────────────────────────────────┐
│         API Gateway                      │
│     (Request routing)                    │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    v        v        v
 ┌──────┐ ┌──────┐ ┌──────┐
 │ RAG  │ │ ML   │ │Realtime
 │ Svc  │ │ Svc  │ │ Svc
 └──────┘ └──────┘ └──────┘
    │        │        │
    └────────┼────────┘
             │
    ┌────────┴────────┐
    │                 │
    v                 v
┌─────────┐      ┌──────────┐
│ Shared  │      │ Collector│
│ Infra   │      │ Svc      │
└─────────┘      └──────────┘
```

**Communication Patterns**:
- **Sync**: REST APIs (service-to-service)
- **Async**: Redis Pub/Sub or Kafka
- **Data**: PostgreSQL (shared DB) or service-specific

---

## Extraction Effort Estimate

| Service | Extraction | Testing | Deployment | Total |
|---------|-----------|---------|-----------|-------|
| RAG | 2-3 weeks | 1-2 weeks | 1 week | 4-6 weeks |
| Collector | 2-3 weeks | 1-2 weeks | 1 week | 4-6 weeks |
| Manufacturing | 2-3 weeks | 1-2 weeks | 1-2 weeks | 4-7 weeks |
| ML | 1-2 weeks | 1 week | 1 week | 3-4 weeks |
| Realtime | 1 week | 3-5 days | 3-5 days | 2-3 weeks |
| **Total** | **9-13 weeks** | **5-8 weeks** | **5-7 weeks** | **19-28 weeks** |

**Parallelization**: All services can be extracted in parallel = 6-8 weeks total

---

## Risk Mitigation

### Risk: Service Coupling
**Mitigation**: 
- Defined API contracts before extraction
- Async communication where possible
- API versioning strategy

### Risk: Data Consistency
**Mitigation**:
- Shared PostgreSQL initially (Phase 3+)
- Event sourcing for audit trail
- Distributed transaction handling (Saga pattern)

### Risk: Operational Complexity
**Mitigation**:
- Comprehensive monitoring and alerting
- Centralized logging (ELK/Loki)
- Service mesh (Istio) for traffic management
- Clear runbooks for each service

### Risk: Deployment Issues
**Mitigation**:
- Blue-green deployments
- Canary deployments (10% → 50% → 100%)
- Automated rollback triggers
- Health checks on all services

---

## Cost Implications

### Phase 1 (Current - Monolithic)
- **Infrastructure**: 1 API server instance
- **Cost**: ~$50-100/month (single server)

### Phase 2 (Service Extraction)
- **Services**: 5 services × 2 instances (HA) = 10 total
- **Cost**: ~$500-1000/month (multiple servers)
- **GPU**: Manufacturing service (optional) = +$100-200/month

### Optimization Opportunities
- Reserved instances (-30%)
- Spot instances for batch jobs (-70%)
- Containerization and K8s autoscaling
- Serverless for collector service (Lambda)

---

## Success Metrics

### Phase 1 (v10.0.0)
- ✅ All APIs functional
- ✅ 80%+ test coverage
- ✅ <500ms API latency (p95)
- ✅ Production deployment tested

### Phase 2 (Service Extraction)
- ✅ Each service deployed independently
- ✅ Service-to-service communication working
- ✅ No performance degradation vs monolithic
- ✅ Service auto-scaling operational

### Phase 3 (Optimization)
- ✅ <100ms p95 latency (optimized)
- ✅ 99.99% availability target
- ✅ Distributed tracing working
- ✅ Services scale independently

### Phase 4 (Kubernetes)
- ✅ Full K8s deployment operational
- ✅ ArgoCD GitOps active
- ✅ Service mesh traffic management
- ✅ Automated deployments from CI/CD

---

## Decision: Why Not Extract Now?

### Current Approach (Monolithic - v10.0.0)

**Advantages**:
- Single codebase → easier debugging
- Shared libraries → less duplication
- Faster development cycles
- Lower operational overhead
- Clear testing/coverage boundaries

**Trade-offs**:
- Single point of failure
- Slower deployment cycles
- Harder to scale individual services
- Technology stack locked to FastAPI

### Extraction Benefits (Phase 2+)

**Advantages**:
- Independent scaling
- Parallel development teams
- Technology flexibility (Python for RAG, Node for realtime)
- Fault isolation
- Faster iteration cycles

**Trade-offs**:
- Operational complexity
- Service-to-service communication overhead
- Data consistency challenges
- Debugging distributed systems

**Decision**: Extract after v10.0.0 stabilization when business requirements demand independent scaling.

---

## Related Documents

- **Architecture**: `docs/V7_COMPLETE_GUIDE.md`
- **Realtime**: `docs/REALTIME_BACKEND_GUIDE.md`
- **RAG System**: `docs/RAG_ACTIVATION_STRATEGY.md`
- **SaaS Platform**: `docs/SAAS_ARCHITECTURE.md`
- **Data Collection**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`
- **Manufacturing**: `docs/MANUFACTURING_AUTOMATION.md`

---

## Appendix: Service Templates

Each extracted service will follow this structure:

```
services/{service-name}/
├── src/
│   ├── main.py                 # FastAPI or Express app
│   ├── config.py               # Configuration
│   ├── schemas.py              # Request/response models
│   ├── api/
│   │   └── routes.py           # API endpoints
│   ├── services/               # Business logic
│   └── repositories/           # Data access
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile                  # Production image
├── docker-compose.yml          # Local dev
├── requirements.txt (Python) or package.json (Node)
├── README.md                   # Service documentation
├── .env.example                # Environment variables
└── helm/                       # Kubernetes deployment
```

---

**Last Updated**: 2025-11-19  
**Next Review**: Post-v10.0.0 stabilization (Q1 2025)
