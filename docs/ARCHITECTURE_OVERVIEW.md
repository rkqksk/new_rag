# Architecture Overview - v10.0.0

**Version**: 10.0.0 "Unified Maximum"
**Philosophy**: Maximal Features + Minimal Structure
**Last Updated**: 2025-11-16

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USERS / CLIENTS                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              │                 │
         [Web Apps]        [Mobile Apps]
       ┌──────────┐       ┌─────────────┐
       │ Next.js  │       │ Expo/React  │
       │   PWA    │       │   Native    │
       └─────┬────┘       └──────┬──────┘
             │                   │
             └───────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │    API Gateway/Ingress  │
        │   (Nginx + Kubernetes)  │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────┐
        │     FastAPI Backend     │
        │    (apps/api - 3 pods)  │
        └────────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
[PostgreSQL]    [Redis Cache]    [Qdrant]
  + pgvector      + Sessions      Vector DB
  Structured      Real-time       Embeddings
    Data          Updates         Semantic
                                  Search
```

---

## Monorepo Structure

```
new_rag/
├── apps/                   # Applications (4)
│   ├── api/               # FastAPI backend (Python)
│   ├── web/               # Next.js web app
│   ├── pwa/               # Vite PWA
│   └── mobile/            # Expo mobile app
│
├── packages/               # Shared packages (5)
│   ├── core/              # Business logic
│   ├── ui/                # React components
│   ├── config/            # Shared config
│   ├── utils/             # Utilities
│   └── mobile-ui/         # Mobile components
│
├── infrastructure/         # DevOps
│   ├── k8s/               # Kubernetes manifests
│   ├── terraform/         # Multi-cloud IaC
│   └── observability/     # Monitoring configs
│
├── services/              # Microservices (planned)
│   ├── rag/               # RAG service
│   ├── collector/         # Data collection
│   ├── manufacturing/     # Vision inspection
│   └── realtime/          # Real-time updates
│
└── workflows/             # Automation
```

---

## Technology Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **UI Library**: React 18
- **State**: Zustand + React Query
- **Styling**: Tailwind CSS
- **PWA**: Vite PWA plugin
- **Mobile**: Expo (React Native)

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Async**: asyncio + aiohttp
- **API Docs**: OpenAPI 3.0

### Databases
- **PostgreSQL 16** + pgvector
  - Primary data store
  - Full-text search
  - Vector similarity
- **Redis 7**
  - Session storage
  - Pub/sub messaging
  - Cache layer
- **Qdrant**
  - Vector database
  - Semantic search
  - Embeddings storage

### DevOps
- **Containers**: Docker
- **Orchestration**: Kubernetes
- **IaC**: Terraform (AWS/GCP/Azure)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Tracing**: Jaeger
- **Logging**: Structured JSON

### Monorepo Tools
- **Package Manager**: pnpm v9
- **Build System**: Turborepo
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript 5.3

---

## Data Flow

### Search Request Flow

```
1. User enters query
   ↓
2. Web/Mobile App
   ↓
3. API Gateway (Nginx Ingress)
   ↓
4. FastAPI Backend
   ├→ Cache Check (Redis)
   │   └→ Cache Hit → Return
   │
   └→ Cache Miss
       ↓
5. Query Processing
   ├→ Text preprocessing
   ├→ Embedding generation
   └→ Query expansion
       ↓
6. Vector Search (Qdrant)
   └→ Semantic similarity
       ↓
7. Hybrid Search (PostgreSQL)
   └→ Keyword + vector
       ↓
8. Result Ranking
   └→ Score fusion
       ↓
9. Cache Result (Redis)
   ↓
10. Return to Client
```

### Real-time Update Flow

```
1. Database Change
   ↓
2. PostgreSQL NOTIFY
   ↓
3. Backend Listener
   ↓
4. Redis Pub/Sub
   ↓
5. Socket.IO Broadcast
   ↓
6. Connected Clients Updated
```

---

## Security Architecture

### Authentication & Authorization

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. Login Request
       ↓
┌─────────────────┐
│  Keycloak OAuth │ ←→ User Database
└────────┬────────┘
         │ 2. JWT Token
         ↓
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │ 3. Verify Token
         ↓
┌─────────────────┐
│   FastAPI       │
│  + Middleware   │
└────────┬────────┘
         │ 4. Authorized Request
         ↓
    [Resources]
```

### Security Layers

1. **Network**: TLS 1.3, HTTPS only
2. **Application**: JWT tokens, RBAC
3. **Database**: Row-level security, encryption at rest
4. **Infrastructure**: Network policies, secrets management
5. **Monitoring**: Audit logs, intrusion detection

---

## Scalability

### Horizontal Scaling

| Component | Min | Max | Auto-scale |
|-----------|-----|-----|------------|
| API Pods | 3 | 20 | CPU > 70% |
| Web Pods | 2 | 10 | CPU > 70% |
| PostgreSQL | 1 | 3 | Manual |
| Redis | 1 | 3 | Manual |
| Qdrant | 1 | 5 | Manual |

### Load Balancing

```
     [Nginx Ingress]
           │
    ┌──────┼──────┐
    │      │      │
 [API-1] [API-2] [API-3]
    │      │      │
    └──────┼──────┘
           │
     [PostgreSQL]
        (PgBouncer)
```

---

## Deployment Strategy

### Blue-Green Deployment

```
Production Traffic
       │
       ↓
  [Load Balancer]
       │
  ┌────┴────┐
  │         │
[Blue]   [Green] ← New version deployed
  │
  └→ Old version (3 pods)
```

**Process**:
1. Deploy new version to green
2. Run smoke tests on green
3. Switch traffic: blue → green
4. Monitor for 30 minutes
5. Scale down blue

---

## Monitoring & Observability

### Metrics Collection

```
Application → Prometheus
    │            │
    │            ↓
    │        Grafana Dashboards
    │
    └→ Jaeger (Distributed Tracing)
```

### Key Metrics

**Application**:
- Request rate
- Error rate
- Response time (p50, p95, p99)
- Active users

**Infrastructure**:
- CPU usage
- Memory usage
- Disk I/O
- Network throughput

**Business**:
- Search queries/minute
- Conversion rate
- User retention

---

## Disaster Recovery

### Backup Strategy

| Component | Frequency | Retention | RPO | RTO |
|-----------|-----------|-----------|-----|-----|
| PostgreSQL | Hourly | 30 days | 1 hour | 1 hour |
| Redis | Daily | 7 days | 24 hours | 30 min |
| Qdrant | Daily | 7 days | 24 hours | 1 hour |
| Configs | On change | Forever | 0 | 10 min |

### Recovery Procedures

1. **Database Failure**: Restore from latest backup
2. **Pod Failure**: Kubernetes auto-restart
3. **Node Failure**: Kubernetes reschedule
4. **Cluster Failure**: Failover to DR cluster

---

## Future Architecture (Microservices)

```
                [API Gateway]
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
[RAG Service]  [Collector]  [Manufacturing]
    │                 │                 │
    └─────────────────┼─────────────────┘
                      │
              [Message Bus (Kafka)]
                      │
                [Event Store]
```

**Benefits**:
- Independent scaling
- Technology diversity
- Fault isolation
- Team autonomy

---

## Design Principles

### v10.0.0 Philosophy

1. **Maximal Features**: All v9 capabilities preserved
2. **Minimal Structure**: 8 top-level directories (76% reduction)
3. **Zero Duplication**: <5% code duplication
4. **Single Source**: Packages shared across apps
5. **Type Safety**: TypeScript + Pydantic everywhere

### Code Organization

- **Co-location**: Related code together
- **Clear Boundaries**: Apps vs Packages vs Services
- **Shared First**: DRY via packages
- **Feature Folders**: Organized by domain

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response (p95) | <500ms | 234ms ✅ |
| Page Load (FCP) | <1.5s | 1.2s ✅ |
| Search Query | <300ms | 245ms ✅ |
| Build Time | <3min | 2.5min ✅ |
| Deploy Time | <5min | 3min ✅ |

---

**Contact**: architecture@rag-enterprise.com
**Last Review**: 2025-11-16
**Next Review**: 2025-12-16
