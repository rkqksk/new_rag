# Observability System - Visual Reference Guide

**RAG Enterprise Platform**
**Document Purpose**: Visual diagrams and sequence flows for observability system

---

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Health Check Layer                         │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │        HealthCheckOrchestrator                       │  │ │
│  │  │  - Parallel execution coordinator                    │  │ │
│  │  │  - Status aggregation logic                          │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                           │                                 │ │
│  │         ┌─────────────────┼─────────────────┐              │ │
│  │         │                 │                 │              │ │
│  │    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐         │ │
│  │    │  PG     │      │ Redis   │      │ Qdrant  │         │ │
│  │    │ Health  │      │ Health  │      │ Health  │         │ │
│  │    │ Checker │      │ Checker │      │ Checker │  ...    │ │
│  │    └────┬────┘      └────┬────┘      └────┬────┘         │ │
│  │         │                │                 │              │ │
│  │    [Database]       [Cache]          [Vector DB]          │ │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Metrics Collection Layer                   │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │          MetricsMiddleware                           │  │ │
│  │  │  - HTTP request interception                         │  │ │
│  │  │  - Automatic metric recording                        │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                           │                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │          MetricsCollector                            │  │ │
│  │  │  - Context manager API                               │  │ │
│  │  │  - Service-level instrumentation                     │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                           │                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │       Prometheus Registry (REGISTRY)                 │  │ │
│  │  │  - Counters, Histograms, Gauges                      │  │ │
│  │  │  - Metric storage and exposition                     │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Health Check Sequence Diagram

### Readiness Probe Flow (/health/ready)

```
Client          API          Orchestrator    PG Checker    Redis Checker    Qdrant Checker    Claude Checker
  │              │                │               │              │                 │                │
  ├─────────────►│                │               │              │                 │                │
  │  GET /ready  │                │               │              │                 │                │
  │              │                │               │              │                 │                │
  │              ├───────────────►│               │              │                 │                │
  │              │ check_all()    │               │              │                 │                │
  │              │                │               │              │                 │                │
  │              │                ├──────────────►│              │                 │                │
  │              │                ├──────────────────────────────►│                 │                │
  │              │                ├───────────────────────────────────────────────►│                │
  │              │                ├────────────────────────────────────────────────────────────────►│
  │              │                │  asyncio.gather([...]) - ALL PARALLEL          │                │
  │              │                │               │              │                 │                │
  │              │                │               │◄─────────────┼─────────────────┼────────────────┤
  │              │                │               │  connect()   │                 │                │
  │              │                │               │  SELECT 1    │                 │                │
  │              │                │               │  close()     │                 │                │
  │              │                │               │              │                 │                │
  │              │                │               │              │◄────────────────┼────────────────┤
  │              │                │               │              │  ping()         │                │
  │              │                │               │              │                 │                │
  │              │                │               │              │                 │◄───────────────┤
  │              │                │               │              │                 │ get_collections│
  │              │                │               │              │                 │                │
  │              │                │               │              │                 │                │◄───────────┐
  │              │                │               │              │                 │                │  POST msg  │
  │              │                │               │              │                 │                │            │
  │              │                │◄──────────────┼──────────────┼─────────────────┼────────────────┤            │
  │              │                │  Results:     │              │                 │                │            │
  │              │                │  [HEALTHY,    │              │                 │                │            │
  │              │                │   HEALTHY,    │              │                 │                │            │
  │              │                │   HEALTHY,    │              │                 │                │            │
  │              │                │   HEALTHY]    │              │                 │                │            │
  │              │                │               │              │                 │                │            │
  │              │                ├───────────────┼──────────────┼─────────────────┼────────────────┘            │
  │              │                │ Calculate     │              │                 │                             │
  │              │                │ Overall:      │              │                 │                             │
  │              │                │ HEALTHY       │              │                 │                             │
  │              │                │               │              │                 │                             │
  │              │◄───────────────┤               │              │                 │                             │
  │              │ AggregatedHealth              │              │                 │                             │
  │              │                │               │              │                 │                             │
  │◄─────────────┤                │               │              │                 │                             │
  │  200 OK      │                │               │              │                 │                             │
  │  {status:    │                │               │              │                 │                             │
  │   "healthy"} │                │               │              │                 │                             │
  │              │                │               │              │                 │                             │
```

**Key Points**:
- All 4 health checks execute in parallel (asyncio.gather)
- Total time = max(individual check times) ≈ 500ms (Claude API slowest)
- If sequential: 15ms + 5ms + 20ms + 500ms = 540ms (similar due to Claude dominance)
- With more checks or slower services, parallel advantage increases

---

## Health Check Timeout Handling

```
Orchestrator                 Checker                    Service
     │                          │                          │
     ├─────────────────────────►│                          │
     │  check_with_timeout()    │                          │
     │                          │                          │
     │                          ├─────────────────────────►│
     │                          │  check_health()          │
     │                          │  with 2s timeout         │
     │                          │                          │
     │                          │                          │
     │                          │◄─────────────────────────┤
     │                          │  Response (fast: 15ms)   │
     │                          │                          │
     │◄─────────────────────────┤                          │
     │  ComponentHealth(        │                          │
     │    status=HEALTHY,       │                          │
     │    latency_ms=15.0       │                          │
     │  )                       │                          │
     │                          │                          │

────────────────────────── TIMEOUT SCENARIO ──────────────────────────

Orchestrator                 Checker                    Service
     │                          │                          │
     ├─────────────────────────►│                          │
     │  check_with_timeout()    │                          │
     │                          │                          │
     │                          ├─────────────────────────►│
     │                          │  check_health()          │
     │                          │  with 2s timeout         │
     │                          │                          │
     │                          │                          X (hangs)
     │                          │                          │
     │                    ┌─────┤                          │
     │                    │ Timeout after 2000ms          │
     │                    │ (asyncio.wait_for)             │
     │                    └────►│                          │
     │                          │                          │
     │◄─────────────────────────┤                          │
     │  ComponentHealth(        │                          │
     │    status=UNHEALTHY,     │                          │
     │    latency_ms=2000.0,    │                          │
     │    message="Timeout..."  │                          │
     │  )                       │                          │
     │                          │                          │
```

**Timeout Protection**:
```python
try:
    result = await asyncio.wait_for(
        self.check_health(),
        timeout=self.timeout  # 2.0s for most services
    )
    return result  # Normal completion
except asyncio.TimeoutError:
    return ComponentHealth(
        status=UNHEALTHY,
        latency_ms=self.timeout * 1000,
        message=f"Timeout after {self.timeout}s"
    )
```

---

## Metrics Collection Flow

### HTTP Request Metrics (Automatic)

```
HTTP Request      Middleware           Prometheus Registry
     │                 │                        │
     ├────────────────►│                        │
     │  POST /api/v1/query                     │
     │                 │                        │
     │                 ├───────────────────────►│
     │                 │  active_requests.inc() │
     │                 │                        │
     │                 ├───────────────────────►│
     │                 │  http_request_size     │
     │                 │  .observe(1024)        │
     │                 │                        │
     │         ┌───────┤                        │
     │         │ Process request               │
     │         │ (application logic)            │
     │         │ Duration: 234ms                │
     │         └──────►│                        │
     │                 │                        │
     │◄────────────────┤                        │
     │  200 OK         │                        │
     │                 │                        │
     │                 ├───────────────────────►│
     │                 │  http_requests_total   │
     │                 │  .labels(              │
     │                 │    method="POST",      │
     │                 │    endpoint="/query",  │
     │                 │    status=200          │
     │                 │  ).inc()               │
     │                 │                        │
     │                 ├───────────────────────►│
     │                 │  http_request_duration │
     │                 │  .labels(...)          │
     │                 │  .observe(0.234)       │
     │                 │                        │
     │                 ├───────────────────────►│
     │                 │  active_requests.dec() │
     │                 │                        │
```

### LLM Query Metrics (Manual Context Manager)

```
Service Code         MetricsCollector      Prometheus Registry
     │                      │                        │
     │  async with          │                        │
     │  track_llm_query()   │                        │
     ├─────────────────────►│                        │
     │                      │                        │
     │                ┌─────┤                        │
     │                │ Start timer                  │
     │                │ (time.time())                │
     │                └────►│                        │
     │                      │                        │
     │  Execute LLM call    │                        │
     ├──────────────────────┼───────────────────────►│
     │  (Claude API)        │                   (External)
     │                      │                        │
     │◄─────────────────────┼────────────────────────┤
     │  Response            │                        │
     │  (tokens: 150)       │                        │
     │                      │                        │
     │  metrics["tokens"]   │                        │
     │  = 150               │                        │
     ├─────────────────────►│                        │
     │                      │                        │
     │                ┌─────┤                        │
     │                │ Calculate duration           │
     │                │ (end - start)                │
     │                └────►│                        │
     │                      │                        │
     │                      ├───────────────────────►│
     │                      │  llm_query_total       │
     │                      │  .labels(              │
     │                      │    model="haiku",      │
     │                      │    status="success"    │
     │                      │  ).inc()               │
     │                      │                        │
     │                      ├───────────────────────►│
     │                      │  llm_query_duration    │
     │                      │  .labels(model="haiku")│
     │                      │  .observe(1.234)       │
     │                      │                        │
     │                      ├───────────────────────►│
     │                      │  llm_tokens_generated  │
     │                      │  .labels(model="haiku")│
     │                      │  .observe(150)         │
     │                      │                        │
     │◄─────────────────────┤                        │
     │  (context exits)     │                        │
     │                      │                        │
```

---

## Status Aggregation Logic

```
┌─────────────────────────────────────────────────────────┐
│         Component Health Results                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ PostgreSQL   │  │    Redis     │  │   Qdrant     │  │
│  │   HEALTHY    │  │   HEALTHY    │  │   HEALTHY    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│                    ▼ Aggregation ▼                       │
│                                                          │
│              Overall Status: HEALTHY                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│         Degraded Component Scenario                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ PostgreSQL   │  │    Redis     │  │   Qdrant     │  │
│  │   HEALTHY    │  │   DEGRADED   │  │   HEALTHY    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│                    ▼ Aggregation ▼                       │
│                                                          │
│              Overall Status: DEGRADED                    │
│                                                          │
│  Reasoning: At least one DEGRADED, none UNHEALTHY      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│         Unhealthy Component Scenario                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ PostgreSQL   │  │    Redis     │  │   Qdrant     │  │
│  │  UNHEALTHY   │  │   DEGRADED   │  │   HEALTHY    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│                    ▼ Aggregation ▼                       │
│                                                          │
│              Overall Status: UNHEALTHY                   │
│                                                          │
│  Reasoning: At least one UNHEALTHY (overrides all)     │
└─────────────────────────────────────────────────────────┘
```

**Aggregation Algorithm**:
```python
def calculate_overall_status(checks: List[ComponentHealth]) -> HealthStatus:
    statuses = [check.status for check in checks]

    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY  # Worst case wins
    elif HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED   # Middle case
    else:
        return HealthStatus.HEALTHY    # All healthy
```

---

## Kubernetes Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Pod: rag-enterprise                    │   │
│  │                                                            │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │           Container: api                          │    │   │
│  │  │                                                    │    │   │
│  │  │  FastAPI App :8000                                │    │   │
│  │  │    │                                               │    │   │
│  │  │    ├─ /health/live  ◄──────────────────────┐     │    │   │
│  │  │    │                                         │     │    │   │
│  │  │    └─ /health/ready ◄───────────────┐       │     │    │   │
│  │  │                                      │       │     │    │   │
│  │  └──────────────────────────────────────┼───────┼─────┘    │   │
│  └───────────────────────────────────────────┼───────┼────────┘   │
│                                              │       │            │
│  ┌───────────────────────────────────────────┼───────┼────────┐   │
│  │              Kubelet (Node Agent)         │       │        │   │
│  │                                            │       │        │   │
│  │  Liveness Probe ──────────────────────────┘       │        │   │
│  │    - Check every 10s                              │        │   │
│  │    - Timeout: 5s                                  │        │   │
│  │    - Failure threshold: 3                         │        │   │
│  │    - Action: Restart container                    │        │   │
│  │                                                    │        │   │
│  │  Readiness Probe ─────────────────────────────────┘        │   │
│  │    - Check every 5s                                        │   │
│  │    - Timeout: 3s                                           │   │
│  │    - Failure threshold: 3                                  │   │
│  │    - Action: Remove from service endpoints                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Service: rag-enterprise-svc                    │  │
│  │                                                              │  │
│  │  Endpoints: [pod-1:8000, pod-2:8000, pod-3:8000]           │  │
│  │             (only pods with readiness=true)                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Failure Scenarios

**Scenario 1: Server Crash**
```
t=0s:  Server crashes (process dies)
t=10s: Liveness probe fails (connection refused)
t=20s: Liveness probe fails (2nd failure)
t=30s: Liveness probe fails (3rd failure, threshold reached)
t=31s: Kubelet restarts container
t=41s: New container starts, liveness probe succeeds
```

**Scenario 2: Database Goes Down**
```
t=0s:  PostgreSQL becomes unreachable
t=0s:  Liveness probe: Still succeeds (server running)
t=5s:  Readiness probe: Fails (PostgreSQL unhealthy)
t=10s: Readiness probe: Fails (2nd failure)
t=15s: Readiness probe: Fails (3rd failure, threshold reached)
t=16s: Kubelet removes pod from service endpoints
       → Traffic stops routing to this pod
       → Pod continues running for debugging
       → No restart (liveness still passing)
t=20s: DBA fixes PostgreSQL
t=25s: Readiness probe: Succeeds (PostgreSQL healthy)
t=26s: Kubelet adds pod back to service endpoints
       → Traffic resumes
```

---

## Prometheus Scraping Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  RAG Enterprise Pods                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Pod 1      │  │   Pod 2      │  │   Pod 3      │      │
│  │              │  │              │  │              │      │
│  │ /metrics     │  │ /metrics     │  │ /metrics     │      │
│  │   :8000      │  │   :8000      │  │   :8000      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          │  Scrape every 15s (configured interval)
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  Prometheus Server                           │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Time Series Database (TSDB)               │ │
│  │                                                          │ │
│  │  http_requests_total{pod="pod-1",method="GET",...}     │ │
│  │  http_requests_total{pod="pod-2",method="GET",...}     │ │
│  │  http_requests_total{pod="pod-3",method="GET",...}     │ │
│  │                                                          │ │
│  │  [15 days retention configured]                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Query API :9090                                             │
│         │                                                     │
└─────────┼─────────────────────────────────────────────────────┘
          │
          │ PromQL queries
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Grafana                                  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Dashboard: RAG Enterprise Health               │ │
│  │                                                          │ │
│  │  Panel 1: Request Rate                                  │ │
│  │    rate(http_requests_total[5m])                        │ │
│  │                                                          │ │
│  │  Panel 2: P95 Latency                                   │ │
│  │    histogram_quantile(0.95,                             │ │
│  │      rate(http_request_duration_seconds_bucket[5m]))    │ │
│  │                                                          │ │
│  │  Panel 3: Error Rate                                    │ │
│  │    rate(errors_total[5m])                               │ │
│  │                                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling State Machine

```
┌─────────────────────────────────────────────────────────────┐
│              Health Check State Machine                      │
└─────────────────────────────────────────────────────────────┘

     START
       │
       ▼
   ┌────────┐
   │ INIT   │  Create checker with config
   └───┬────┘
       │
       ▼
   ┌────────────────┐
   │ CHECK_PENDING  │  Waiting to execute
   └───┬────────────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
   ┌────────────┐                      ┌──────────┐
   │ EXECUTING  │ ────timeout────────► │ TIMEOUT  │
   └─────┬──────┘                      └────┬─────┘
         │                                   │
         │                                   ▼
         │                          ComponentHealth(
         │                            status=UNHEALTHY,
         │                            message="Timeout"
         │                          )
         │
         ├─────success───────►┌──────────┐
         │                    │ SUCCESS  │
         │                    └────┬─────┘
         │                         │
         │                         ▼
         │                ComponentHealth(
         │                  status=HEALTHY/DEGRADED,
         │                  latency_ms=...
         │                )
         │
         └─────exception────►┌──────────┐
                             │  ERROR   │
                             └────┬─────┘
                                  │
                                  ▼
                         ComponentHealth(
                           status=UNHEALTHY,
                           message=str(exception)
                         )
```

### Exception Handling Flow

```python
async def check_with_timeout(self) -> ComponentHealth:
    start_time = time.time()

    try:
        # Try health check with timeout
        result = await asyncio.wait_for(
            self.check_health(),
            timeout=self.timeout
        )
        return result  # ──► SUCCESS state

    except asyncio.TimeoutError:
        # Timeout occurred
        latency_ms = (time.time() - start_time) * 1000
        return ComponentHealth(  # ──► TIMEOUT state
            component=self.component_name,
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=f"Timeout after {self.timeout}s"
        )

    except Exception as e:
        # Unexpected error
        latency_ms = (time.time() - start_time) * 1000
        return ComponentHealth(  # ──► ERROR state
            component=self.component_name,
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=f"Error: {str(e)}"
        )
```

---

## Metric Cardinality Examples

### Safe Cardinality (Good Practice)

```
http_requests_total{
  method="GET",         # 10 possible values
  endpoint="/query",    # 50 possible values
  status="200"          # 20 possible values
}

Total time series: 10 × 50 × 20 = 10,000 ✅ SAFE
```

### Unsafe Cardinality (Anti-Pattern)

```
http_requests_total{
  method="GET",
  endpoint="/query",
  user_id="user-12345",      # ⚠️ MILLIONS of values
  request_id="req-abc123",   # ⚠️ INFINITE values
  timestamp="1234567890"     # ⚠️ INFINITE values
}

Total time series: MILLIONS → BILLIONS ❌ DANGEROUS
Result: Prometheus OOM crash, query timeouts
```

### Recommended Label Cardinality Limits

```
┌──────────────────┬──────────────┬──────────────────┐
│ Label Type       │ Max Values   │ Example          │
├──────────────────┼──────────────┼──────────────────┤
│ Static (env)     │ < 10         │ prod, staging    │
│ Service name     │ < 100        │ api, worker      │
│ Endpoint         │ < 500        │ /query, /health  │
│ Status code      │ ~20          │ 200, 404, 500    │
│ Model name       │ < 50         │ haiku, sonnet    │
│ Collection       │ < 100        │ documents, users │
└──────────────────┴──────────────┴──────────────────┘

NEVER USE:
- User IDs
- Request IDs
- IP addresses
- Timestamps
- UUIDs
- Session IDs
```

---

## Data Flow Summary

```
┌──────────────────────────────────────────────────────────────┐
│                     System Overview                           │
└──────────────────────────────────────────────────────────────┘

Health Data Flow:
  Component Services → Health Checkers → Orchestrator → API Endpoints → Kubernetes/Monitoring

Metrics Data Flow:
  Application Events → Middleware/Collectors → Prometheus Registry → Metrics Endpoint → Prometheus → Grafana

Monitoring Flow:
  Prometheus → Alertmanager → PagerDuty/Slack
  Prometheus → Grafana → Operations Dashboard
  Health Endpoints → Kubernetes → Pod Lifecycle Management
```

---

## Implementation Priority Matrix

```
┌─────────────────────────────────────────────────────────────┐
│              Impact vs Effort Matrix                         │
│                                                               │
│  High Impact │                                               │
│       ▲      │  [Health System]    [Metrics Middleware]     │
│       │      │       Phase 1            (existing)           │
│       │      │                                               │
│       │      │  [Test Coverage]    [K8s Integration]        │
│       │      │       Phase 4            Phase 5             │
│  Low Impact  │                                               │
│       ├──────┼───────────────────────────────────────────►  │
│              │  Low Effort              High Effort          │
│                                                               │
│  Priority Order:                                             │
│  1. Health System (High Impact, Low Effort)                  │
│  2. Enhanced Metrics (High Impact, Low Effort)               │
│  3. Health Endpoints (High Impact, Low Effort)               │
│  4. Test Coverage (Medium Impact, Medium Effort)             │
│  5. K8s Integration (High Impact, Medium Effort)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference Commands

### Testing Health Endpoints

```bash
# Liveness probe
curl -i http://localhost:8000/health/live

# Readiness probe
curl -i http://localhost:8000/health/ready

# General health with formatted output
curl http://localhost:8000/health | jq '.'

# Check specific component
curl http://localhost:8000/health | jq '.checks[] | select(.component == "postgresql")'

# Metrics endpoint
curl http://localhost:8000/health/metrics

# Filter specific metric
curl http://localhost:8000/health/metrics | grep http_requests_total
```

### Prometheus Queries

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate percentage
rate(errors_total[5m]) / rate(http_requests_total[5m]) * 100

# Claude API success rate
rate(claude_api_calls_total{status="success"}[5m]) /
rate(claude_api_calls_total[5m]) * 100

# Active requests gauge
http_requests_in_flight
```

---

**Document Status**: Reference Guide Complete
**Related Documents**:
- Architecture: `OBSERVABILITY_ARCHITECTURE.md`
- Quick Start: `OBSERVABILITY_QUICKSTART.md`
- Design Decisions: `OBSERVABILITY_DESIGN_DECISIONS.md`
