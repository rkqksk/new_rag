# Observability System - Design Decisions & Rationale

**RAG Enterprise Platform**
**Document Purpose**: Architectural decision record (ADR) for observability system design

---

## Decision Summary

| Decision | Choice | Alternative Considered | Rationale |
|----------|--------|------------------------|-----------|
| **Health Check Execution** | Async Parallel | Sequential Sync | 5s vs 11s total check time (55% faster) |
| **Database Driver** | asyncpg (async) | psycopg2 (sync) | Non-blocking I/O, FastAPI compatibility |
| **Redis Client** | aioredis (async) | redis-py (sync) | Consistent async pattern across stack |
| **Timeout Strategy** | Per-component (2-5s) | Global timeout | Granular control, faster failure detection |
| **Status Hierarchy** | 3-tier (healthy/degraded/unhealthy) | Binary (up/down) | Graceful degradation support |
| **Metrics Middleware** | Automatic collection | Manual instrumentation | Zero developer overhead, consistent coverage |
| **Prometheus Registry** | Custom registry | Default registry | Isolation from other metrics sources |
| **Error Handling** | Structured ComponentHealth | Exception propagation | Controlled failure modes, detailed diagnostics |

---

## 1. Parallel vs Sequential Health Checks

### Decision: Async Parallel Execution

**Implementation**:
```python
check_results = await asyncio.gather(
    *[checker.check_with_timeout() for checker in self.checkers],
    return_exceptions=True
)
```

**Rationale**:
- **Performance**: Worst-case latency = max(individual_timeout) instead of sum(individual_timeouts)
- **Scalability**: Adding new checkers doesn't increase total check time
- **Resource Efficiency**: Better utilization of I/O wait time
- **Production Impact**: Minimal delay on readiness probe responses

**Trade-offs**:
- **Complexity**: Slightly more complex code than sequential loops
- **Resource Burst**: Brief spike in concurrent connections
- **Decision**: Performance gains vastly outweigh complexity cost

**Benchmark**:
```
Sequential: PostgreSQL (2s) + Redis (2s) + Qdrant (2s) + Claude (5s) = 11s
Parallel:   max(2s, 2s, 2s, 5s) = 5s
Improvement: 55% faster
```

---

## 2. Three-Tier Health Status

### Decision: HEALTHY / DEGRADED / UNHEALTHY

**Alternative Considered**: Binary (UP/DOWN)

**Rationale**:
- **Graceful Degradation**: Distinguish between "service impaired" vs "service down"
- **Operational Clarity**: Different response strategies based on severity
- **Business Continuity**: Continue serving requests with reduced functionality

**Status Mapping**:
| Component State | Status | Impact | Action |
|-----------------|--------|--------|--------|
| PostgreSQL down | UNHEALTHY | Critical - no data access | Alert immediately, stop traffic |
| Qdrant down | UNHEALTHY | Critical - no search | Alert immediately, stop traffic |
| Redis down | DEGRADED | Non-critical - cache miss | Log warning, continue serving |
| Claude API slow | DEGRADED | Non-critical - use Ollama | Log warning, continue serving |
| All healthy | HEALTHY | Normal operation | No action |

**Example Scenario**:
```
Redis cache fails → Status: DEGRADED
- Readiness probe: Still returns 200 (service operational)
- Application: Falls back to direct database queries
- Monitoring: Warning alert (not critical)
- User impact: Slightly slower responses (200ms → 500ms)
```

**Decision**: Three-tier provides operational flexibility without excessive complexity.

---

## 3. Timeout Configuration Strategy

### Decision: Per-Component Timeouts

**Configuration**:
```python
PostgreSQLHealthChecker(timeout=2.0)  # Database should be fast
RedisHealthChecker(timeout=2.0)       # Cache should be instant
QdrantHealthChecker(timeout=2.0)      # Vector DB local network
ClaudeAPIHealthChecker(timeout=5.0)   # External API, network dependent
```

**Alternative Considered**: Global 5s timeout for all checks

**Rationale**:
- **Faster Failure Detection**: Internal services should respond in <100ms, timeout after 2s
- **Realistic Expectations**: External APIs (Claude) legitimately take longer
- **Operational Insights**: Timeout indicates specific problem (slow database vs slow API)
- **Customization**: Adjust per environment (local dev vs production)

**Trade-offs**:
- **Configuration Complexity**: More parameters to manage
- **Decision**: Operational benefits outweigh configuration overhead

---

## 4. Async-First Database Drivers

### Decision: asyncpg + aioredis

**Alternative Considered**: psycopg2 + redis-py with thread pools

**Rationale**:
- **FastAPI Alignment**: Native async/await support
- **Resource Efficiency**: Single-threaded event loop, no thread context switching
- **Performance**: ~20% faster than sync drivers in thread pools
- **Consistency**: Entire stack is async (FastAPI → Health Checks → Database)

**Implementation Pattern**:
```python
# Async pattern (chosen)
async def check_health(self):
    conn = await asyncpg.connect(...)
    await conn.execute('SELECT 1')
    await conn.close()

# Sync pattern (rejected)
def check_health_sync(self):
    conn = psycopg2.connect(...)  # Blocks event loop
    conn.execute('SELECT 1')
    conn.close()
```

**Trade-offs**:
- **Dependency Addition**: Requires asyncpg, aioredis (vs already installed psycopg2)
- **Decision**: Performance and consistency benefits justify additional dependencies

---

## 5. Error Handling Philosophy

### Decision: Structured ComponentHealth Returns

**Implementation**:
```python
try:
    # Perform health check
    return ComponentHealth(status=HEALTHY, ...)
except Exception as e:
    return ComponentHealth(status=UNHEALTHY, message=str(e))
```

**Alternative Considered**: Raise exceptions, catch at orchestrator level

**Rationale**:
- **Controlled Failures**: Every check always returns ComponentHealth (never None)
- **Partial Results**: One failing check doesn't crash entire health endpoint
- **Detailed Diagnostics**: Exception message preserved in ComponentHealth.message
- **Type Safety**: Consistent return type for all checkers

**Error Information Preservation**:
```python
ComponentHealth(
    component="postgresql",
    status=UNHEALTHY,
    latency_ms=2000.0,
    message="Connection timeout after 2.0s",  # Original error context
    metadata={"host": "172.28.0.4"}
)
```

**Decision**: Structured returns provide better observability than exception propagation.

---

## 6. Metrics Collection Architecture

### Decision: Automatic Middleware + Manual Instrumentation

**Two-Layer Approach**:

**Layer 1 - Automatic (Middleware)**:
```python
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Automatically track ALL requests
        http_requests_total.inc()
        http_request_duration_seconds.observe(duration)
```
- **Coverage**: Every HTTP request/response
- **Developer Effort**: Zero - automatic
- **Metrics**: Request count, latency, size, status codes

**Layer 2 - Manual (Context Managers)**:
```python
async with metrics_collector.track_llm_query(model) as m:
    response = await llm.generate(prompt)
    m["tokens"] = response.usage.total_tokens
```
- **Coverage**: Application-specific operations (LLM calls, RAG pipeline)
- **Developer Effort**: Explicit context managers in service code
- **Metrics**: Business logic metrics (tokens, confidence, chunks)

**Alternative Considered**: Manual instrumentation everywhere

**Rationale**:
- **Completeness**: Middleware ensures no request goes untracked
- **Flexibility**: Manual instrumentation for domain-specific metrics
- **Maintainability**: Add middleware once vs instrument every endpoint
- **Performance**: Middleware overhead <1ms, negligible impact

**Decision**: Hybrid approach maximizes coverage with minimal effort.

---

## 7. Prometheus Registry Isolation

### Decision: Custom Registry (REGISTRY)

**Implementation**:
```python
from prometheus_client import CollectorRegistry
REGISTRY = CollectorRegistry()

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY  # Custom registry
)
```

**Alternative Considered**: Use default prometheus_client registry

**Rationale**:
- **Isolation**: Separate RAG Enterprise metrics from potential other sources
- **Testing**: Can reset custom registry between tests without affecting globals
- **Namespace Control**: Explicit control over metric namespace
- **Multi-tenancy**: Future-proof for multi-service deployments

**Trade-offs**:
- **Explicit Registration**: Must pass `registry=REGISTRY` to all metrics
- **Decision**: Isolation benefits outweigh registration verbosity

---

## 8. Health Check Dependency Injection

### Decision: Singleton HealthCheckOrchestrator via FastAPI DI

**Implementation**:
```python
@lru_cache()
def get_health_orchestrator(config: AppConfig = Depends(get_config)):
    checkers = [
        PostgreSQLHealthChecker(host=config.postgres_host, ...),
        RedisHealthChecker(host=config.redis_host, ...),
        # ...
    ]
    return HealthCheckOrchestrator(checkers)

@router.get("/health/ready")
async def readiness_probe(
    orchestrator = Depends(get_health_orchestrator)
):
    return await orchestrator.check_readiness()
```

**Alternative Considered**: Global orchestrator instance

**Rationale**:
- **Testability**: Easy to override with mocks in tests
- **Configuration Integration**: Uses existing `get_config()` dependency
- **Lazy Initialization**: Orchestrator created on first health check, not startup
- **Consistency**: Matches existing dependency injection patterns in codebase

**Benefits**:
```python
# Testing is trivial
def get_mock_orchestrator():
    return MockHealthCheckOrchestrator()

app.dependency_overrides[get_health_orchestrator] = get_mock_orchestrator
```

**Decision**: DI pattern provides testability without sacrificing simplicity.

---

## 9. Claude API Health Check Design

### Decision: Minimal Test Prompt (10 tokens)

**Implementation**:
```python
response = await client.post(
    "https://api.anthropic.com/v1/messages",
    json={
        "model": "claude-3-haiku-20240307",  # Fastest, cheapest model
        "max_tokens": 10,                     # Minimal tokens
        "messages": [{"role": "user", "content": "ping"}]
    }
)
```

**Alternative Considered**: Just check API endpoint availability (no actual call)

**Rationale**:
- **Realistic Test**: Verifies actual API functionality, not just network reachability
- **Cost Efficiency**: 10 tokens ≈ $0.000025 per check (negligible)
- **Error Detection**: Catches authentication, rate limiting, model availability issues
- **Latency Measurement**: Provides real-world API latency metrics

**Cost Analysis** (assuming health check every 10s):
```
Checks per day: 86400s / 10s = 8640 checks
Cost per check: 10 tokens × $0.0000025 = $0.000025
Daily cost: 8640 × $0.000025 = $0.216
Monthly cost: $0.216 × 30 = $6.48
```

**Decision**: $6.48/month is acceptable cost for production confidence.

---

## 10. Liveness vs Readiness Separation

### Decision: Separate /live and /ready Endpoints

**Liveness Probe** (`/health/live`):
```python
async def check_liveness(self):
    # No dependency checks - just return HEALTHY
    return ComponentHealth(
        component="liveness",
        status=HealthStatus.HEALTHY,
        latency_ms=0,
        message="Server is running"
    )
```

**Readiness Probe** (`/health/ready`):
```python
async def check_readiness(self):
    # Full dependency checks in parallel
    return await self.check_all()
```

**Rationale**:
- **Kubernetes Best Practice**: Liveness detects server crashes, readiness detects service unavailability
- **Restart Prevention**: Liveness probe never fails due to dependency issues (prevents restart loops)
- **Traffic Control**: Readiness probe controls pod traffic routing based on dependency health
- **Operational Clarity**: Clear separation of concerns

**Scenario Example**:
```
PostgreSQL goes down:
- Liveness: Still returns 200 (server running)
- Readiness: Returns 503 (dependencies unhealthy)
- K8s action: Removes pod from load balancer (no restart)
- Result: Traffic stops, but pod remains for debugging
```

**Decision**: Separation prevents cascading failures and restart loops.

---

## 11. Metric Cardinality Management

### Decision: Bounded Label Sets

**Safe Labels** (bounded cardinality):
```python
http_requests_total.labels(
    method="GET",              # ~10 values
    endpoint="/api/v1/query",  # ~50 values
    status="200"               # ~20 values
)
# Total combinations: 10 × 50 × 20 = 10,000 time series (safe)
```

**Dangerous Labels** (unbounded cardinality - AVOIDED):
```python
# ANTI-PATTERN - DO NOT DO THIS
http_requests_total.labels(
    user_id="user-12345",           # Millions of values
    request_id="req-abc123",        # Infinite values
    ip_address="192.168.1.1"        # Thousands of values
)
# This would create millions of time series → Prometheus crash
```

**Cardinality Budget**:
| Metric Type | Max Labels | Max Values per Label | Max Total Series |
|-------------|------------|----------------------|------------------|
| HTTP metrics | 3 | 50 | 10,000 |
| LLM metrics | 2 | 10 | 100 |
| DB metrics | 2 | 5 | 50 |
| RAG metrics | 1 | 3 | 10 |

**Decision**: Strict cardinality limits prevent Prometheus resource exhaustion.

---

## 12. Structured Logging Integration

### Decision: Use Existing structlog System

**Integration Pattern**:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# In health checker
if check.status != HealthStatus.HEALTHY:
    logger.warning(
        "component_health_degraded",
        component=check.component,
        status=check.status.value,
        latency_ms=check.latency_ms,
        message=check.message
    )
```

**Alternative Considered**: Separate logging system for health checks

**Rationale**:
- **Consistency**: Same structured logging as rest of application
- **Automatic Masking**: Sensitive data filtering already implemented
- **Correlation**: Health logs correlate with application logs via request_id
- **No Duplication**: Avoid maintaining two logging systems

**Decision**: Leverage existing logging infrastructure for consistency.

---

## Summary of Design Principles

1. **Async-First**: All I/O operations use async/await for efficiency
2. **Parallel by Default**: Independent operations execute concurrently
3. **Graceful Degradation**: Three-tier status supports partial functionality
4. **Fail-Safe Design**: Structured returns instead of exception propagation
5. **Zero Developer Overhead**: Automatic middleware for basic metrics
6. **Testability**: Dependency injection enables easy mocking
7. **Production-Ready**: Timeout protection, error handling, monitoring
8. **Cost-Conscious**: Minimal Claude API usage in health checks
9. **Operational Clarity**: Separate liveness/readiness for K8s orchestration
10. **Resource Protection**: Bounded metric cardinality prevents explosions

---

## Future Enhancements

### Planned (Next Quarter)

1. **Health Check Caching**: Cache health results for 10s to reduce load
2. **Circuit Breaker**: Skip checks for consistently failing components
3. **Distributed Tracing**: OpenTelemetry integration for request tracing
4. **Custom Business Metrics**: User journey tracking, revenue impact metrics

### Under Consideration

1. **Health History API**: Endpoint to query historical health data
2. **Predictive Health**: ML-based prediction of component failures
3. **Auto-Remediation**: Automatic restart of unhealthy components
4. **Multi-Region Health**: Cross-region health aggregation for global deployments

---

## References

- FastAPI Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/
- Prometheus Best Practices: https://prometheus.io/docs/practices/naming/
- Kubernetes Health Probes: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- asyncpg Documentation: https://magicstack.github.io/asyncpg/current/
- aioredis Documentation: https://aioredis.readthedocs.io/

---

**Document Status**: Architecture Finalized
**Next Action**: Begin Phase 1 Implementation (Core Health System)
**Owner**: System Architecture Team
**Last Updated**: 2025-10-19
