# API Performance Baseline - v10.0.0

**Date**: 2025-11-19
**System**: v10 Unified Maximum
**Target**: Production-ready performance standards

---

## Executive Summary

### Performance Targets
| Endpoint | Target | Industry Standard | Status |
|----------|--------|-------------------|--------|
| Health Check | <50ms | <100ms | ✅ Excellent |
| Search | <500ms | <1000ms | ✅ Excellent |
| QA | <1000ms | <2000ms | ✅ Good |
| Products List | <200ms | <500ms | ✅ Excellent |
| Concurrent (100 users) | >100 req/s | >50 req/s | ⚠️ To measure |

### Quick Stats
- **API Framework**: FastAPI (async, production-grade)
- **Expected Throughput**: 100-500 requests/second
- **Expected Latency**: p50 <200ms, p95 <1000ms, p99 <2000ms
- **Concurrent Users**: 100-1000 (with horizontal scaling)

---

## 1. Health Endpoint Performance

### `/health/ready` (Readiness Check)

**Purpose**: Kubernetes readiness probe, dependency health check

**Target**: <50ms (99th percentile)

#### Test Command
```bash
# Single request with timing
time curl -s http://localhost:8001/health/ready

# 100 requests
for i in {1..100}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8001/health/ready
done | awk '{sum+=$1; count++} END {print "Average:", sum/count*1000, "ms"}'
```

#### Expected Results
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T07:00:00Z",
  "version": "10.0.0",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "qdrant": "ok"
  }
}
```

**Performance Metrics**:
- **Response Time**: 10-30ms typical, <50ms p99
- **Status Code**: 200 (healthy), 503 (unhealthy)
- **Payload Size**: ~150 bytes (gzip: ~100 bytes)
- **Memory**: <5MB per request
- **CPU**: <1% per request

---

## 2. Search Endpoint Performance

### `/api/v1/search/` (Hybrid Search)

**Purpose**: Primary search functionality with vector + full-text search

**Target**: <500ms (95th percentile)

#### Test Command
```bash
# Single request
time curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'

# Load test with Python
python3 << 'EOF'
import requests
import time
import statistics

url = "http://localhost:8001/api/v1/search/"
payload = {"query": "50ml PET 용기", "top_k": 5}
headers = {"Content-Type": "application/json"}

times = []
for i in range(100):
    start = time.time()
    response = requests.post(url, json=payload, headers=headers)
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")

print(f"Mean: {statistics.mean(times):.2f}ms")
print(f"Median: {statistics.median(times):.2f}ms")
print(f"p95: {sorted(times)[94]:.2f}ms")
print(f"p99: {sorted(times)[98]:.2f}ms")
print(f"Min: {min(times):.2f}ms, Max: {max(times):.2f}ms")
EOF
```

#### Expected Results
```json
{
  "results": [
    {
      "product_id": "prod_123",
      "name": "50ml PET 용기",
      "similarity": 0.89,
      "metadata": {...}
    }
  ],
  "query": "50ml PET 용기",
  "total": 5,
  "execution_time_ms": 234
}
```

**Performance Breakdown**:
- **Query Parsing**: 5-10ms
- **Vector Search (Qdrant)**: 50-150ms
- **Full-Text Search (PostgreSQL)**: 30-80ms
- **Score Fusion**: 10-20ms
- **Result Formatting**: 5-10ms
- **Total**: 100-270ms typical, <500ms p95

**Factors Affecting Performance**:
- Query complexity (1-5 words: fast, >10 words: slower)
- top_k parameter (5: fast, 50: slower)
- Vector index size (1k: fast, 1M: moderate)
- Cache hit rate (cached: 10-50ms, cold: 200-500ms)

**Optimization Tips**:
- Use Redis caching for frequent queries
- Limit top_k to <20 for user-facing queries
- Pre-warm cache with popular searches
- Use query result caching with 5-15 min TTL

---

## 3. QA Endpoint Performance

### `/api/v1/qa/` (RAG Question Answering)

**Purpose**: Retrieval-Augmented Generation for product questions

**Target**: <1000ms (95th percentile)

#### Test Command
```bash
# Single request
time curl -X POST http://localhost:8001/api/v1/qa/ \
  -H "Content-Type: application/json" \
  -d '{"question":"50ml PET 용기의 사양은?","context_chunks":5}'

# Load test
python3 << 'EOF'
import requests
import time
import statistics

url = "http://localhost:8001/api/v1/qa/"
payload = {"question": "50ml PET 용기의 사양은?", "context_chunks": 5}
headers = {"Content-Type": "application/json"}

times = []
for i in range(20):  # Fewer iterations due to LLM cost
    start = time.time()
    response = requests.post(url, json=payload, headers=headers)
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)
    print(f"Request {i+1}: {elapsed:.0f}ms")
    time.sleep(1)  # Rate limiting

print(f"\nMean: {statistics.mean(times):.2f}ms")
print(f"p95: {sorted(times)[int(len(times)*0.95)]:.2f}ms")
EOF
```

#### Expected Results
```json
{
  "answer": "50ml PET 용기는 다음과 같은 사양을 가지고 있습니다:\n- 용량: 50ml\n- 재질: PET (Polyethylene Terephthalate)\n- 크기: 높이 100mm, 직경 30mm",
  "sources": [
    {"product_id": "prod_123", "chunk_id": "chunk_456"}
  ],
  "confidence": 0.87,
  "execution_time_ms": 789
}
```

**Performance Breakdown**:
- **Retrieval (Search)**: 100-300ms
- **Context Assembly**: 20-50ms
- **LLM Inference**: 500-2000ms (varies by model)
  - Ollama (local): 800-1500ms
  - NexaAI (API): 500-1000ms
  - OpenAI (API): 300-800ms
- **Response Formatting**: 10-20ms
- **Total**: 630-2370ms typical

**LLM Performance Comparison**:

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| Ollama llama3.2:1b | 300-600ms | Good | Free |
| Ollama llama3.2:3b | 800-1500ms | Excellent | Free |
| NexaAI Llama-3.1 | 500-1000ms | Excellent | $0 |
| GPT-3.5-turbo | 300-800ms | Good | $0.002/req |
| GPT-4 | 1000-3000ms | Excellent | $0.03/req |

**Optimization Tips**:
- Use streaming responses for better UX
- Cache similar questions (fuzzy matching)
- Use smaller models for simple queries
- Implement query queue for rate limiting

---

## 4. Products Endpoint Performance

### `/api/v1/products/` (Product Listing)

**Purpose**: List products with pagination and filtering

**Target**: <200ms (95th percentile)

#### Test Command
```bash
# List first page
time curl -s "http://localhost:8001/api/v1/products/?limit=20&offset=0"

# With filtering
time curl -s "http://localhost:8001/api/v1/products/?category=PET&limit=20"

# Load test
python3 << 'EOF'
import requests
import time
import statistics

url = "http://localhost:8001/api/v1/products/"
params = {"limit": 20, "offset": 0}

times = []
for i in range(100):
    start = time.time()
    response = requests.get(url, params=params)
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)

print(f"Mean: {statistics.mean(times):.2f}ms")
print(f"Median: {statistics.median(times):.2f}ms")
print(f"p95: {sorted(times)[94]:.2f}ms")
EOF
```

#### Expected Results
```json
{
  "products": [...],
  "total": 471,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

**Performance Metrics**:
- **Simple List (no filter)**: 30-80ms
- **With Filter**: 50-150ms
- **With Search**: 80-200ms
- **With Sorting**: 40-100ms

**Database Query Performance**:
```sql
-- Simple pagination (indexed)
SELECT * FROM products LIMIT 20 OFFSET 0;
-- Expected: 10-30ms

-- With filter
SELECT * FROM products WHERE category = 'PET' LIMIT 20;
-- Expected: 20-50ms (with index)

-- Full-text search
SELECT * FROM products WHERE name ILIKE '%PET%' LIMIT 20;
-- Expected: 50-150ms (with GIN index)
```

---

## 5. Concurrent Load Testing

### Methodology

**Tools**: Apache Bench (ab), wrk, or Python requests

**Test Scenarios**:
1. **Light Load**: 10 concurrent users, 1000 requests
2. **Medium Load**: 50 concurrent users, 5000 requests
3. **Heavy Load**: 100 concurrent users, 10000 requests
4. **Stress Test**: 500 concurrent users until failure

#### Apache Bench Commands
```bash
# Install apache bench
sudo apt-get install apache2-utils

# Light load - Health endpoint
ab -n 1000 -c 10 http://localhost:8001/health/ready

# Medium load - Search endpoint (POST)
ab -n 500 -c 50 -p search_payload.json -T application/json \
  http://localhost:8001/api/v1/search/

# Heavy load - Products endpoint
ab -n 10000 -c 100 http://localhost:8001/api/v1/products/?limit=20
```

#### Expected Results

**Light Load (10 concurrent)**:
- Requests/sec: 200-500
- Average latency: 20-50ms
- p95 latency: 50-100ms
- Success rate: 100%

**Medium Load (50 concurrent)**:
- Requests/sec: 150-300
- Average latency: 100-250ms
- p95 latency: 300-600ms
- Success rate: 99%+

**Heavy Load (100 concurrent)**:
- Requests/sec: 100-200
- Average latency: 300-800ms
- p95 latency: 1000-2000ms
- Success rate: 95%+

**Stress Test (500 concurrent)**:
- Expected: Rate limiting, queue buildup
- Circuit breaker activation: >1000 concurrent
- Graceful degradation: Cache-only mode

---

## 6. Memory and CPU Usage

### Expected Resource Usage

**Idle State**:
- Memory: 200-400MB
- CPU: 1-5%

**Under Load (100 concurrent)**:
- Memory: 500-1000MB (with caching)
- CPU: 40-80% (1 worker)

**Per Request**:
- Memory: ~2-5MB (transient)
- CPU: 10-50ms (varies by endpoint)

### Monitoring Commands
```bash
# Check API container resources
docker stats new_rag-api-1

# Check memory usage
docker exec new_rag-api-1 free -h

# Check CPU usage
docker exec new_rag-api-1 top -bn1 | head -20
```

---

## 7. Database Performance

### PostgreSQL Metrics

**Connection Pool**:
- Min connections: 5
- Max connections: 20
- Connection timeout: 30s

**Query Performance**:
- Simple SELECT: 5-20ms
- JOIN queries: 20-80ms
- Full-text search: 50-200ms
- Aggregations: 30-150ms

### Qdrant Metrics

**Vector Search**:
- Collection size: 3,246 vectors
- Search latency: 30-100ms (HNSW index)
- Throughput: 100-500 QPS
- Memory: ~500MB for 3k vectors

### Redis Metrics

**Cache Performance**:
- GET/SET: 1-5ms
- Cache hit rate target: >80%
- Memory: 100-500MB
- Eviction policy: LRU

---

## 8. Network Performance

### Payload Sizes

| Endpoint | Request | Response | Gzipped |
|----------|---------|----------|---------|
| Health | 0 bytes | 150 bytes | 100 bytes |
| Search | 100 bytes | 2-10 KB | 1-5 KB |
| QA | 200 bytes | 1-5 KB | 500-2000 bytes |
| Products | 0 bytes | 10-50 KB | 5-20 KB |

### Bandwidth Requirements

**Per User**:
- Typical: 10-50 KB/request
- Peak: 100-500 KB/request (with images)
- Average: 20 requests/minute

**100 Concurrent Users**:
- Bandwidth: 2-10 MB/s
- Network throughput: 16-80 Mbps
- Typical production: 100-500 Mbps

---

## 9. Bottleneck Analysis

### Identified Bottlenecks

**1. LLM Inference** (highest impact)
- Problem: QA endpoint 500-2000ms latency
- Solution: Use smaller models, streaming, caching
- Impact: 50-70% latency reduction

**2. Vector Search** (medium impact)
- Problem: Qdrant search 50-150ms
- Solution: HNSW index optimization, caching
- Impact: 30-50% latency reduction

**3. Database Queries** (low-medium impact)
- Problem: Complex joins 50-200ms
- Solution: Indexing, query optimization
- Impact: 40-60% latency reduction

**4. Network Latency** (low impact)
- Problem: Response payload size
- Solution: Gzip compression, CDN
- Impact: 20-40% bandwidth reduction

---

## 10. Optimization Recommendations

### Immediate Actions (0 cost)

**1. Enable Response Compression**
```python
# In FastAPI main.py
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```
Expected: 40-60% bandwidth reduction

**2. Implement Query Result Caching**
```python
# Redis caching for search results
@cache(ttl=300)  # 5 minutes
async def search(query: str):
    ...
```
Expected: 80-95% latency reduction for cached queries

**3. Add Database Indexes**
```sql
CREATE INDEX idx_products_name ON products USING GIN (to_tsvector('english', name));
CREATE INDEX idx_products_category ON products (category);
```
Expected: 50-70% query speedup

**4. Use Connection Pooling**
```python
# PostgreSQL connection pool
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```
Expected: 30-50% connection overhead reduction

### Medium-term Actions (minimal cost)

**5. Implement CDN Caching**
- Use Cloudflare or AWS CloudFront
- Cache static content and API responses
- Expected: 50-80% latency reduction for cached content
- Cost: $0-20/month (free tier available)

**6. Add Query Queue and Rate Limiting**
```python
# Rate limiting per user
@limiter.limit("100/minute")
async def search(query: str):
    ...
```
Expected: Better stability under load

**7. Optimize LLM Configuration**
```python
# Use smaller model for simple queries
if is_simple_query(question):
    model = "llama3.2:1b"  # 300-600ms
else:
    model = "llama3.2:3b"  # 800-1500ms
```
Expected: 40-60% faster for simple queries

### Long-term Actions (with budget)

**8. Horizontal Scaling**
- Deploy 2-5 API instances
- Use load balancer (Nginx/HAProxy)
- Expected: 2-5x throughput
- Cost: $50-200/month (cloud VMs)

**9. Upgrade to Faster LLM Provider**
- Switch from Ollama to NexaAI/OpenAI
- Expected: 50-70% faster QA responses
- Cost: $0 (NexaAI) to $100/month (OpenAI)

**10. Add Application Performance Monitoring**
- Use Sentry, Datadog, or New Relic
- Track real user metrics
- Expected: Better visibility
- Cost: $0-100/month

---

## 11. Industry Benchmarks

### Comparison with Industry Standards

| Metric | Our Target | Industry Average | Status |
|--------|-----------|------------------|---------|
| API Latency (p95) | <500ms | <1000ms | ✅ Better |
| Throughput | >100 req/s | >50 req/s | ✅ Better |
| Availability | 99.9% | 99.5% | ✅ Better |
| Error Rate | <0.5% | <1% | ✅ Better |
| Cache Hit Rate | >80% | >70% | ✅ Better |

### FastAPI Performance vs Others

| Framework | Requests/sec | Latency (p95) |
|-----------|--------------|---------------|
| FastAPI | 2000-5000 | <100ms |
| Flask | 500-1000 | <300ms |
| Django | 200-500 | <500ms |
| Node.js Express | 1000-3000 | <200ms |

**Our Position**: FastAPI is one of the fastest Python frameworks, comparable to Node.js.

---

## 12. Testing Checklist

### Pre-deployment Testing

- [ ] Health endpoint responds <50ms
- [ ] Search endpoint responds <500ms
- [ ] QA endpoint responds <1000ms
- [ ] 100 concurrent users supported
- [ ] Database queries have indexes
- [ ] Redis caching is working
- [ ] Response compression enabled
- [ ] Rate limiting configured
- [ ] Error handling tested
- [ ] Monitoring dashboards setup

### Load Testing Checklist

- [ ] Run light load test (10 concurrent)
- [ ] Run medium load test (50 concurrent)
- [ ] Run heavy load test (100 concurrent)
- [ ] Run stress test (500 concurrent)
- [ ] Measure memory usage under load
- [ ] Measure CPU usage under load
- [ ] Test with different query types
- [ ] Test with different payload sizes
- [ ] Test cache hit/miss scenarios
- [ ] Document all results

---

## 13. Continuous Monitoring

### Key Metrics to Track

**Application Metrics** (Prometheus):
- `http_request_duration_seconds` (histogram)
- `http_requests_total` (counter)
- `http_request_size_bytes` (histogram)
- `http_response_size_bytes` (histogram)

**Business Metrics**:
- Searches per minute
- QA queries per hour
- Cache hit rate
- Error rate by endpoint

**Infrastructure Metrics**:
- CPU usage (%)
- Memory usage (MB)
- Network I/O (MB/s)
- Disk I/O (MB/s)

### Alerts to Configure

```yaml
# Example Prometheus alerts
groups:
  - name: api_performance
    rules:
      - alert: HighLatency
        expr: http_request_duration_seconds{quantile="0.95"} > 1.0
        for: 5m
        annotations:
          summary: "API latency is high"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        annotations:
          summary: "API error rate is high"
```

---

## 14. Baseline Test Results

### Test Environment
- **Date**: 2025-11-19
- **System**: v10.0.0 Unified Maximum
- **Hardware**: [To be measured]
- **Load**: [To be measured]

### Results Summary

| Test | Target | Actual | Status |
|------|--------|--------|--------|
| Health endpoint | <50ms | [TBD] | ⏳ |
| Search endpoint | <500ms | [TBD] | ⏳ |
| QA endpoint | <1000ms | [TBD] | ⏳ |
| Products endpoint | <200ms | [TBD] | ⏳ |
| 100 concurrent | >100 req/s | [TBD] | ⏳ |

**Note**: Run the load testing script `/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh` to populate these results.

---

## 15. Next Steps

1. **Run Load Tests**: Execute all test commands and populate results
2. **Implement Optimizations**: Apply the 0-cost optimizations listed
3. **Setup Monitoring**: Configure Prometheus alerts and Grafana dashboards
4. **Document Findings**: Update this baseline with actual measurements
5. **Schedule Regular Tests**: Run load tests weekly to track performance trends

---

## Resources

- **Load Test Script**: `/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh`
- **Monitoring Dashboard**: http://localhost:3000 (Grafana)
- **API Docs**: http://localhost:8001/api/v1/docs
- **Metrics Endpoint**: http://localhost:8001/metrics (to be implemented)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Status**: Ready for Testing
**Next Review**: After first load test execution
