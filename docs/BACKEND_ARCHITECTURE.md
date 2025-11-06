# Enterprise Backend Architecture

**Philosophy**: 프론트엔드는 미니멀, 백엔드는 맥시멀

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Minimal)                       │
│                      chat.html (Simple UI)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────┴────────────────────────────────────┐
│                      API Gateway Layer                           │
│  - Rate Limiting          - CORS                                 │
│  - Authentication         - Request Validation                   │
│  - Circuit Breaker        - API Versioning (/v1, /v2)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      Service Layer (Core)                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ SearchService                                          │    │
│  │  - Vector Search (Qdrant)                             │    │
│  │  - Tri-Modal Search (Text + Image + Shape)           │    │
│  │  - Hybrid Fusion                                      │    │
│  │  - Cross-Encoder Re-ranking                           │    │
│  │  - Query Routing                                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ PersonalizationService                                 │    │
│  │  - User Profile Management                            │    │
│  │  - Adaptive Weights Learning                          │    │
│  │  - Compatibility Filtering (Hard Filter)              │    │
│  │  - Recommendation Engine                              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ AnalyticsService                                       │    │
│  │  - Global Analytics Tracking                          │    │
│  │  - Keyword Extraction & Ranking                       │    │
│  │  - Trending Queries                                   │    │
│  │  - Product Popularity                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ DocumentProcessingService                              │    │
│  │  - OCR Pipeline (PaddleOCR)                           │    │
│  │  - Multi-Modal Embedding                              │    │
│  │  - Chunking & Indexing                                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ExperimentationService                                 │    │
│  │  - A/B Testing Framework                              │    │
│  │  - Variant Assignment                                 │    │
│  │  - Metrics Collection                                 │    │
│  │  - Statistical Analysis                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ConversationService                                    │    │
│  │  - Conversation Memory                                │    │
│  │  - Context Management                                 │    │
│  │  - Session Management                                 │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    Repository Layer (Data Access)                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Qdrant     │  │  PostgreSQL  │  │    Redis     │         │
│  │  Repository  │  │  Repository  │  │  Repository  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     Infrastructure Layer                         │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Qdrant  │  │ Postgres │  │  Redis   │  │  Ollama  │       │
│  │  Vector  │  │ Database │  │  Cache   │  │   LLM    │       │
│  │   Store  │  │          │  │          │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
rag-enterprise/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry
│   │
│   ├── api/                          # API Routes (by version)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── search.py            # Search endpoints
│   │   │   ├── personalization.py   # Personalization endpoints
│   │   │   ├── analytics.py         # Analytics endpoints
│   │   │   ├── documents.py         # Document processing endpoints
│   │   │   ├── experiments.py       # A/B testing endpoints
│   │   │   └── conversations.py     # Conversation endpoints
│   │   └── dependencies.py          # Shared dependencies
│   │
│   ├── services/                     # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── search_service.py
│   │   ├── personalization_service.py
│   │   ├── analytics_service.py
│   │   ├── document_service.py
│   │   ├── experiment_service.py
│   │   └── conversation_service.py
│   │
│   ├── repositories/                 # Data Access Layer
│   │   ├── __init__.py
│   │   ├── base.py                  # Base repository
│   │   ├── qdrant_repository.py
│   │   ├── postgres_repository.py
│   │   └── redis_repository.py
│   │
│   ├── core/                         # Core Utilities
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration management
│   │   ├── security.py              # Security utilities
│   │   ├── logging.py               # Structured logging
│   │   ├── metrics.py               # Prometheus metrics
│   │   ├── cache.py                 # Caching strategies
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── middleware/                   # Custom Middleware
│   │   ├── __init__.py
│   │   ├── rate_limiter.py          # Rate limiting
│   │   ├── circuit_breaker.py       # Circuit breaker
│   │   ├── request_id.py            # Request ID tracking
│   │   └── error_handler.py         # Global error handler
│   │
│   ├── schemas/                      # Pydantic Models
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── personalization.py
│   │   ├── analytics.py
│   │   └── common.py
│   │
│   └── dependencies/                 # Dependency Injection
│       ├── __init__.py
│       ├── database.py
│       └── services.py
│
├── tests/                            # Comprehensive Testing
│   ├── unit/                         # Unit tests
│   │   ├── services/
│   │   ├── repositories/
│   │   └── core/
│   ├── integration/                  # Integration tests
│   │   ├── api/
│   │   └── services/
│   ├── e2e/                          # End-to-end tests
│   │   └── scenarios/
│   ├── load/                         # Load tests (Locust)
│   │   └── locustfile.py
│   └── conftest.py                   # Pytest configuration
│
├── scripts/                          # Utility Scripts
│   ├── validate_system.py            # System validation
│   ├── run_tests.sh                  # Test runner
│   └── benchmark.py                  # Performance benchmarks
│
├── config/                           # Configuration Files
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
│
└── monitoring/                       # Monitoring & Observability
    ├── prometheus.yml
    ├── grafana/
    │   └── dashboards/
    └── alerts/
```

## 🎯 Design Principles

### 1. **Layered Architecture**
- **API Layer**: Request/Response handling, validation
- **Service Layer**: Business logic, orchestration
- **Repository Layer**: Data access abstraction
- **Infrastructure Layer**: External services

### 2. **Dependency Injection**
```python
# Example
class SearchService:
    def __init__(
        self,
        qdrant_repo: QdrantRepository,
        redis_cache: RedisCache,
        metrics: MetricsCollector
    ):
        self.qdrant = qdrant_repo
        self.cache = redis_cache
        self.metrics = metrics
```

### 3. **Repository Pattern**
```python
class BaseRepository(ABC):
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
```

### 4. **Circuit Breaker Pattern**
```python
@circuit_breaker(failure_threshold=5, timeout=30)
async def call_external_service():
    # Automatically breaks circuit if too many failures
    pass
```

### 5. **Retry Logic with Exponential Backoff**
```python
@retry(max_attempts=3, backoff=exponential_backoff)
async def call_unreliable_service():
    pass
```

## 🛡️ Enterprise Features

### 1. **Rate Limiting**
- Per-user rate limits
- Per-endpoint rate limits
- Token bucket algorithm

### 2. **Circuit Breaker**
- Automatic failure detection
- Graceful degradation
- Health-based recovery

### 3. **Caching Strategy**
- L1: In-memory cache (TTL: 60s)
- L2: Redis cache (TTL: 1h)
- Cache invalidation on updates

### 4. **Observability**
- **Metrics**: Prometheus (request rate, latency, errors)
- **Logging**: Structured JSON logging
- **Tracing**: OpenTelemetry (distributed tracing)
- **Health Checks**: Liveness & Readiness probes

### 5. **Security**
- API key authentication
- Rate limiting
- CORS configuration
- Request validation
- SQL injection prevention
- XSS protection

### 6. **Error Handling**
- Structured error responses
- Error tracking (Sentry)
- Automatic retry for transient errors
- Graceful degradation

## 📊 Monitoring & Metrics

### Key Metrics
```python
# Request metrics
http_requests_total
http_request_duration_seconds
http_requests_in_flight

# Business metrics
search_queries_total
personalization_applied_total
compatibility_filter_blocks_total

# System metrics
qdrant_vector_search_duration_seconds
redis_cache_hit_rate
ollama_generation_duration_seconds
```

### Health Checks
```
GET /health/live    # Liveness probe
GET /health/ready   # Readiness probe
GET /health/metrics # Prometheus metrics
```

## 🧪 Testing Strategy

### 1. **Unit Tests** (95% coverage target)
- Services
- Repositories
- Core utilities
- Isolated, fast tests

### 2. **Integration Tests**
- API endpoints
- Service integration
- Database operations

### 3. **E2E Tests**
- Complete user flows
- Multi-step scenarios
- Real dependencies

### 4. **Load Tests**
- Concurrent users: 100-1000
- Request rate: 100-1000 req/s
- Performance baselines

### 5. **Validation Tests**
- System validation script
- Data integrity checks
- Configuration validation

## 🚀 Deployment Strategy

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Staging
```bash
kubectl apply -f k8s/staging/
```

### Production
```bash
kubectl apply -f k8s/production/
# Blue-green deployment
# Canary deployment (10% → 50% → 100%)
```

## 📈 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Search latency (p95) | < 200ms | TBD |
| API availability | > 99.9% | TBD |
| Error rate | < 0.1% | TBD |
| Cache hit rate | > 80% | TBD |
| Concurrent users | 1000+ | TBD |

## 🔧 Configuration Management

### Environment-based
```python
# config/development.yaml
database:
  host: localhost
  pool_size: 10

# config/production.yaml
database:
  host: prod-db.example.com
  pool_size: 50
  ssl: true
```

### Secret Management
```python
# Kubernetes secrets
# Vault integration
# Environment variables
```

## 📝 API Versioning

```
/api/v1/search          # Stable API
/api/v2/search          # New features
/api/internal/search    # Internal use
```

## 🎯 Success Criteria

- ✅ 95%+ test coverage
- ✅ < 200ms p95 latency
- ✅ 99.9% availability
- ✅ Zero downtime deployments
- ✅ Comprehensive monitoring
- ✅ Automated validation
- ✅ Production-ready configuration

---

**Next Steps**: Implement each layer progressively
