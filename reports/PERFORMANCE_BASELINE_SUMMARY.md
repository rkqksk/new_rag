# Performance Baseline Summary - v10.0.0

**Date**: 2025-11-19
**System**: v10 Unified Maximum
**Status**: Ready for Testing
**Version**: 1.0.0

---

## Executive Summary

This document provides a comprehensive overview of performance baselines established for the v10.0.0 system. It consolidates findings from API, frontend, and database performance testing, providing a complete picture of system capabilities and optimization opportunities.

### Document Structure
1. **API Performance** - `/reports/PERFORMANCE_BASELINE_API.md`
2. **Frontend Performance** - `/reports/PERFORMANCE_BASELINE_FRONTEND.md`
3. **Database Performance** - `/reports/PERFORMANCE_BASELINE_DATABASE.md`
4. **Load Testing Script** - `/scripts/load-test-baseline.sh`

---

## Performance Targets Overview

### API Performance
| Endpoint | Target | Industry Standard | Expected Status |
|----------|--------|-------------------|----------------|
| Health Check | <50ms | <100ms | ✅ Excellent |
| Search | <500ms | <1000ms | ✅ Excellent |
| QA | <1000ms | <2000ms | ✅ Good |
| Products List | <200ms | <500ms | ✅ Excellent |
| Concurrent (100 users) | >100 req/s | >50 req/s | ✅ Good |

### Frontend Performance
| Metric | Target | Industry Standard | Expected Status |
|--------|--------|-------------------|----------------|
| First Contentful Paint | <1.8s | <2.5s | ✅ Excellent |
| Time to Interactive | <3.8s | <5.0s | ✅ Good |
| Largest Contentful Paint | <2.5s | <4.0s | ✅ Excellent |
| Bundle Size | <200 KB | <300 KB | ✅ Excellent |
| Build Time (cold) | <3min | <5min | ✅ Good |
| Lighthouse Score | >90 | >80 | ✅ Excellent |

### Database Performance
| Database | Operation | Target | Industry Standard | Expected Status |
|----------|-----------|--------|-------------------|----------------|
| PostgreSQL | Simple SELECT | <20ms | <50ms | ✅ Excellent |
| PostgreSQL | JOIN Query | <80ms | <200ms | ✅ Good |
| PostgreSQL | Full-text Search | <200ms | <500ms | ✅ Good |
| Qdrant | Vector Search | <100ms | <200ms | ✅ Excellent |
| Redis | GET/SET | <5ms | <10ms | ✅ Excellent |
| ClickHouse | Aggregation | <100ms | <500ms | ✅ Excellent |

---

## System Architecture Overview

### Technology Stack
```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  Next.js 15 + React 19 + Pure Black Design                  │
│  Bundle: 150-200 KB (gzipped)                                │
│  Performance: FCP <1.8s, TTI <3.8s                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       API Layer                              │
│  FastAPI (Python 3.11) + Uvicorn                             │
│  Endpoints: 80+ production APIs                              │
│  Performance: <500ms p95 latency                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  RAG Service | Search Service | QA Service                   │
│  Analytics | Personalization | Multi-Agent                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                           │
│  PostgreSQL (471 products, 3246 chunks)                      │
│  Qdrant (3246 vectors, 768 dimensions)                       │
│  Redis (1000+ cached keys)                                   │
│  ClickHouse (analytics)                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### Running Performance Tests

#### 1. API Performance Test
```bash
# Ensure API is running
docker-compose up -d api postgres redis qdrant

# Test health endpoint
time curl -s http://localhost:8001/health/ready

# Test search endpoint
time curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"PET 용기","top_k":5}'

# See full tests in:
# /reports/PERFORMANCE_BASELINE_API.md
```

#### 2. Frontend Performance Test
```bash
# Build frontend
cd /home/rkqksk/projects/new_rag/apps/web
time pnpm build

# Run Lighthouse
npm install -g lighthouse
pnpm dev &
sleep 10
lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report.html

# See full tests in:
# /reports/PERFORMANCE_BASELINE_FRONTEND.md
```

#### 3. Database Performance Test
```bash
# PostgreSQL
docker exec -it new_rag-postgres-1 psql -U postgres -d rag_db
\timing on
SELECT * FROM products WHERE category = 'PET' LIMIT 20;

# Qdrant
curl -X POST http://localhost:16333/collections/products/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.1,0.2,...], "limit":5}'

# See full tests in:
# /reports/PERFORMANCE_BASELINE_DATABASE.md
```

#### 4. Load Testing
```bash
# Run all load tests
/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh all

# Or run specific test
/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh light

# Options: light, medium, heavy, stress, all
```

---

## Performance Breakdown by Component

### 1. API Layer (FastAPI)

**Strengths**:
- FastAPI is one of the fastest Python frameworks
- Async/await for concurrent request handling
- Automatic OpenAPI documentation
- Built-in validation with Pydantic

**Expected Performance**:
- Simple endpoints: 10-50ms
- Search endpoints: 100-500ms
- QA endpoints: 500-1500ms (includes LLM)
- Throughput: 100-500 requests/second

**Bottlenecks**:
1. **LLM Inference** (highest impact): 500-2000ms
2. **Vector Search** (medium impact): 50-150ms
3. **Database Queries** (low-medium impact): 20-200ms

**Optimization Opportunities**:
- ✅ Response compression (40-60% bandwidth reduction)
- ✅ Redis caching (80-95% latency reduction for cached queries)
- ✅ Connection pooling (30-50% connection overhead reduction)
- ⚠️ Rate limiting (stability under load)
- ⚠️ Query queue (better load distribution)

---

### 2. Frontend Layer (Next.js 15)

**Strengths**:
- Next.js automatic code splitting
- Image optimization (Next/Image)
- Static site generation (SSG)
- Pure Black design = minimal assets

**Expected Performance**:
- Build time (cold): 2-4 minutes
- Build time (hot): 5-30 seconds
- Bundle size: 150-200 KB (gzipped)
- First Contentful Paint: 1.0-1.8s
- Time to Interactive: 2.0-3.8s

**Bottlenecks**:
1. **Bundle Size** (medium impact): Affects load time
2. **Image Loading** (low-medium impact): Can delay LCP
3. **JavaScript Execution** (low impact): Affects TTI

**Optimization Opportunities**:
- ✅ Next.js Image component (70-85% smaller images)
- ✅ Dynamic imports (30-50% smaller initial bundle)
- ✅ Static generation (50-90% faster page loads)
- ⚠️ CDN caching (50-80% latency reduction for global users)
- ⚠️ Service Worker (PWA) (instant offline support)

---

### 3. Database Layer

#### PostgreSQL (Transactional)

**Strengths**:
- ACID compliance
- Rich query capabilities (JOINs, aggregations)
- Full-text search (GIN indexes)
- Mature and stable

**Expected Performance**:
- Simple SELECT: 3-20ms
- JOIN queries: 35-80ms
- Full-text search: 85-200ms
- Transactions: 8-60ms

**Optimization Opportunities**:
- ✅ Add indexes (50-70% query speedup)
- ✅ Connection pooling (30-50% overhead reduction)
- ✅ Query optimization (40-60% latency reduction)
- ⚠️ Partitioning (for large tables >1M rows)
- ⚠️ Read replicas (horizontal scaling)

#### Qdrant (Vector Search)

**Strengths**:
- Purpose-built for vector search
- HNSW index for fast approximate nearest neighbor
- Filtering capabilities
- Scales to millions of vectors

**Expected Performance**:
- Top 5 search: 45-85ms
- With filter: 68-135ms
- Throughput: 100-500 QPS

**Optimization Opportunities**:
- ✅ HNSW parameter tuning (speed vs accuracy tradeoff)
- ✅ Payload indexes (faster filtering)
- ⚠️ Sharding (for >1M vectors)

#### Redis (Caching)

**Strengths**:
- In-memory storage (extremely fast)
- Rich data structures (strings, hashes, lists, sets)
- Pub/Sub messaging
- TTL support

**Expected Performance**:
- GET/SET: 0.8-2.5ms
- Hash operations: 1.2-3.5ms
- List operations: 0.9-2.8ms
- Cache hit rate target: >80%

**Optimization Opportunities**:
- ✅ LRU eviction policy (automatic memory management)
- ✅ Persistence (RDB/AOF for durability)
- ⚠️ Redis Cluster (horizontal scaling)

#### ClickHouse (Analytics)

**Strengths**:
- Columnar storage (fast aggregations)
- Scales to billions of rows
- SQL interface
- Real-time ingestion

**Expected Performance**:
- Aggregations: 35-180ms
- Insert throughput: >10,000 rows/second

**Optimization Opportunities**:
- ✅ Partitioning by date (faster queries)
- ✅ Materialized views (pre-aggregated queries)
- ⚠️ Distributed tables (cluster setup)

---

## Load Testing Scenarios

### Test Levels

#### 1. Light Load (Baseline)
- **Concurrent Users**: 10
- **Total Requests**: 1000
- **Duration**: ~10-30 seconds
- **Purpose**: Establish baseline performance
- **Expected**: 200-500 req/s, <100ms latency

#### 2. Medium Load (Typical Production)
- **Concurrent Users**: 50
- **Total Requests**: 5000
- **Duration**: ~30-60 seconds
- **Purpose**: Simulate typical production load
- **Expected**: 150-300 req/s, 100-300ms latency

#### 3. Heavy Load (Peak Traffic)
- **Concurrent Users**: 100
- **Total Requests**: 10000
- **Duration**: ~60-120 seconds
- **Purpose**: Test system capacity at peak
- **Expected**: 100-200 req/s, 300-1000ms latency

#### 4. Stress Test (Breaking Point)
- **Concurrent Users**: 500
- **Total Requests**: 50000
- **Duration**: ~2-5 minutes
- **Purpose**: Find system limits and breaking point
- **Expected**: Rate limiting, circuit breaker activation

---

## Optimization Roadmap

### Phase 1: Zero-Cost Optimizations (Immediate)

**API**:
- [ ] Enable response compression (40-60% bandwidth reduction)
- [ ] Implement Redis caching (80-95% latency reduction)
- [ ] Add database indexes (50-70% query speedup)
- [ ] Configure connection pooling (30-50% overhead reduction)

**Frontend**:
- [ ] Use Next.js Image component everywhere (70-85% smaller)
- [ ] Enable static generation (50-90% faster loads)
- [ ] Add loading states (better UX)
- [ ] Implement code splitting (30-50% smaller bundle)

**Database**:
- [ ] Create missing indexes (50-70% speedup)
- [ ] Run VACUUM ANALYZE (maintenance)
- [ ] Optimize HNSW parameters (speed vs accuracy)
- [ ] Configure Redis persistence (durability)

**Expected Impact**: 40-70% performance improvement, $0 cost

---

### Phase 2: Low-Cost Optimizations (1-4 weeks)

**API**:
- [ ] Add query queue and rate limiting
- [ ] Implement result caching (5-15 min TTL)
- [ ] Optimize LLM configuration (model selection)
- [ ] Add request timeout handling

**Frontend**:
- [ ] Deploy to Vercel/Netlify (CDN)
- [ ] Optimize fonts (variable fonts)
- [ ] Implement prefetching
- [ ] Add service worker (PWA)

**Database**:
- [ ] Setup read replicas (PostgreSQL)
- [ ] Enable query monitoring
- [ ] Add slow query alerts
- [ ] Configure auto-vacuum

**Expected Impact**: 50-80% performance improvement, $0-50/month

---

### Phase 3: Production Optimizations (1-3 months)

**Infrastructure**:
- [ ] Horizontal scaling (2-5 API instances)
- [ ] Load balancer (Nginx/HAProxy)
- [ ] CDN for static assets (Cloudflare)
- [ ] APM (Sentry, Datadog, or New Relic)

**Services**:
- [ ] Upgrade to faster LLM provider
- [ ] Database sharding (if needed)
- [ ] Message queue (RabbitMQ/Kafka)
- [ ] Container orchestration (Kubernetes)

**Monitoring**:
- [ ] Real User Monitoring (RUM)
- [ ] Synthetic monitoring
- [ ] Log aggregation (ELK stack)
- [ ] Custom dashboards (Grafana)

**Expected Impact**: 2-5x performance improvement, $50-500/month

---

## Industry Benchmarks Comparison

### API Performance

| Framework | Requests/sec | Latency (p95) | Memory | Our Position |
|-----------|--------------|---------------|---------|--------------|
| FastAPI | 2000-5000 | <100ms | 200-500 MB | ✅ Using |
| Flask | 500-1000 | <300ms | 150-300 MB | - |
| Django | 200-500 | <500ms | 300-600 MB | - |
| Node.js Express | 1000-3000 | <200ms | 300-600 MB | - |

**Verdict**: FastAPI is one of the best choices for Python APIs.

---

### Frontend Performance

| Metric | Our Target | Top 10% Sites | Average Site | Bottom 10% Sites |
|--------|-----------|---------------|--------------|------------------|
| LCP | <2.5s | <2.5s | 4.0s | >6.0s |
| FCP | <1.8s | <1.8s | 3.0s | >5.0s |
| TTI | <3.8s | <3.8s | 7.0s | >12.0s |
| Bundle Size | 150 KB | 150 KB | 300 KB | >500 KB |

**Verdict**: Our targets align with top 10% of websites.

---

### Database Performance

| Database | Use Case | Latency | Throughput | Our Choice |
|----------|----------|---------|------------|------------|
| PostgreSQL | Transactional | <50ms | 1000 TPS | ✅ |
| MySQL | Transactional | <50ms | 800 TPS | - |
| MongoDB | Document Store | <30ms | 1500 TPS | - |
| Qdrant | Vector Search | <100ms | 500 QPS | ✅ |
| Pinecone | Vector Search | <50ms | 1000 QPS | ❌ Paid |
| Redis | Cache | <5ms | 10000 QPS | ✅ |
| Memcached | Cache | <3ms | 15000 QPS | - |

**Verdict**: Our database choices are industry-standard and performant.

---

## Cost Analysis

### Current Stack ($0/month Software Cost)

| Component | Service | Cost | Alternative | Alt Cost |
|-----------|---------|------|-------------|----------|
| API | FastAPI | $0 | Flask/Django | $0 |
| Frontend | Next.js | $0 | React/Vue | $0 |
| Database | PostgreSQL | $0 | MySQL | $0 |
| Vector DB | Qdrant | $0 | Pinecone | $70/mo |
| Cache | Redis | $0 | Memcached | $0 |
| Analytics | ClickHouse | $0 | BigQuery | $100/mo |
| LLM | Ollama/NexaAI | $0 | OpenAI | $100/mo |
| Monitoring | Prometheus/Grafana | $0 | Datadog | $100/mo |
| **Total** | | **$0** | | **$370/mo** |

**Annual Savings**: $4,440 vs paid alternatives

---

### Infrastructure Cost Estimate

**Self-hosted (Current)**:
- Server: $20-100/month (VPS/dedicated)
- Bandwidth: Included
- Storage: Included
- **Total**: $20-100/month

**Cloud (AWS/GCP/Azure)**:
- Compute: $50-200/month (2-4 instances)
- Database: $30-100/month (RDS)
- Cache: $20-50/month (ElastiCache)
- Storage: $10-30/month (S3)
- Bandwidth: $20-100/month
- **Total**: $130-480/month

**Serverless (Vercel/Netlify)**:
- Hosting: $20-100/month
- Functions: $20-100/month
- Database: $30-100/month (external)
- **Total**: $70-300/month

**Recommendation**: Start self-hosted, migrate to cloud at scale.

---

## Testing Checklist

### Pre-deployment Testing

**API**:
- [ ] All endpoints respond within target latency
- [ ] 100 concurrent users supported
- [ ] Error handling tested
- [ ] Rate limiting configured
- [ ] Monitoring dashboards setup

**Frontend**:
- [ ] Lighthouse score >90 on all pages
- [ ] Bundle size <200 KB
- [ ] Mobile testing (3G network)
- [ ] PWA features working
- [ ] SEO meta tags present

**Database**:
- [ ] All indexes created
- [ ] Connection pooling configured
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Query performance acceptable

**Load Testing**:
- [ ] Light load test passed
- [ ] Medium load test passed
- [ ] Heavy load test passed
- [ ] Stress test completed (breaking point identified)
- [ ] Results documented

---

## Monitoring Strategy

### Key Performance Indicators (KPIs)

**User-Centric Metrics**:
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)
- Cumulative Layout Shift (CLS)
- API response time (p50, p95, p99)

**System Metrics**:
- CPU usage (%)
- Memory usage (MB)
- Disk I/O (MB/s)
- Network I/O (MB/s)
- Error rate (%)

**Business Metrics**:
- Searches per minute
- QA queries per hour
- Cache hit rate (%)
- Conversion rate (%)
- User engagement time

---

### Alert Thresholds

**Critical Alerts** (immediate action):
- API error rate >5%
- API p95 latency >2000ms
- Database connection pool >90% full
- Memory usage >90%
- Disk usage >90%

**Warning Alerts** (investigate soon):
- API p95 latency >1000ms
- Cache hit rate <70%
- Database slow queries >10/min
- Memory usage >70%
- CPU usage >80% for >5 min

**Info Alerts** (track trends):
- API request rate changes >50%
- Unusual traffic patterns
- New error types appearing
- Performance degradation trends

---

## Continuous Improvement

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check error logs
- [ ] Analyze slow queries
- [ ] Update cache strategies
- [ ] Review user feedback

### Monthly Tasks
- [ ] Run full load tests
- [ ] Review and update baselines
- [ ] Analyze trends and patterns
- [ ] Implement optimizations
- [ ] Update documentation

### Quarterly Tasks
- [ ] Comprehensive performance audit
- [ ] Benchmark against competitors
- [ ] Evaluate new technologies
- [ ] Plan infrastructure upgrades
- [ ] Review cost optimization

---

## Resources

### Documentation
- **API Baseline**: `/reports/PERFORMANCE_BASELINE_API.md`
- **Frontend Baseline**: `/reports/PERFORMANCE_BASELINE_FRONTEND.md`
- **Database Baseline**: `/reports/PERFORMANCE_BASELINE_DATABASE.md`
- **Load Test Script**: `/scripts/load-test-baseline.sh`

### Tools
- **Load Testing**: `/scripts/load-test-baseline.sh`
- **Lighthouse**: `npm install -g lighthouse`
- **PostgreSQL**: `docker exec -it new_rag-postgres-1 psql`
- **Redis**: `docker exec -it new_rag-redis-1 redis-cli`
- **Monitoring**: http://localhost:3000 (Grafana)
- **API Docs**: http://localhost:8001/api/v1/docs

### External Resources
- **Web Vitals**: https://web.dev/vitals/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **PostgreSQL Performance**: https://www.postgresql.org/docs/16/performance-tips.html
- **Qdrant Docs**: https://qdrant.tech/documentation/

---

## Next Steps

### Immediate Actions (This Week)
1. **Run Load Tests**: Execute `/scripts/load-test-baseline.sh all`
2. **Measure Actual Performance**: Populate [TBD] values in baseline docs
3. **Implement Quick Wins**: Apply zero-cost optimizations
4. **Setup Monitoring**: Configure Prometheus alerts

### Short-term Actions (This Month)
1. **Optimize Code**: Implement caching and indexing
2. **Load Testing**: Weekly load tests to track improvements
3. **Documentation**: Update baselines with real measurements
4. **User Testing**: Get feedback on perceived performance

### Long-term Actions (This Quarter)
1. **Infrastructure**: Consider horizontal scaling
2. **APM**: Implement application performance monitoring
3. **CDN**: Setup CDN for global users
4. **Automation**: Continuous performance testing in CI/CD

---

## Conclusion

This performance baseline provides a comprehensive framework for measuring and optimizing the v10.0.0 system. Key highlights:

### Strengths
✅ **Modern Stack**: FastAPI, Next.js 15, PostgreSQL, Qdrant
✅ **Zero Cost**: $0/month software, $4,440/year savings
✅ **Performance Targets**: Aligned with top 10% of websites
✅ **Comprehensive Testing**: API, frontend, database, load tests
✅ **Optimization Ready**: Clear roadmap with expected impact

### Opportunities
⚠️ **LLM Optimization**: Biggest performance bottleneck (500-2000ms)
⚠️ **Caching**: Can reduce latency by 80-95% for common queries
⚠️ **Indexing**: Can speed up queries by 50-70%
⚠️ **CDN**: Can reduce latency by 50-80% for global users

### Action Items
1. Run load tests to establish actual baselines
2. Implement zero-cost optimizations (expected: 40-70% improvement)
3. Setup monitoring and alerts
4. Review and iterate monthly

### Expected Outcomes
- **Performance**: 40-70% improvement in first month
- **Cost**: Maintain $0/month software cost
- **Scalability**: Support 100-500 concurrent users
- **Reliability**: 99.9% uptime target

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-19
**Status**: ✅ Ready for Testing
**Next Review**: After first load test execution (TBD)

---

## Appendix: Quick Reference

### Test Commands

**API Health**:
```bash
curl http://localhost:8001/health/ready
```

**API Search**:
```bash
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"PET 용기","top_k":5}'
```

**Frontend Build**:
```bash
cd apps/web && time pnpm build
```

**Lighthouse Test**:
```bash
lighthouse http://localhost:3000 --output html
```

**Database Query**:
```bash
docker exec -it new_rag-postgres-1 psql -U postgres -d rag_db \
  -c "SELECT * FROM products LIMIT 10;"
```

**Load Test**:
```bash
/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh light
```

### Service Ports

| Service | Port | URL |
|---------|------|-----|
| API | 8001 | http://localhost:8001 |
| Frontend | 3000 | http://localhost:3000 |
| PostgreSQL | 15432 | localhost:15432 |
| Redis | 16379 | localhost:16379 |
| Qdrant | 16333 | http://localhost:16333 |
| Grafana | 3000 | http://localhost:3000 |
| Prometheus | 9090 | http://localhost:9090 |

---

**End of Performance Baseline Summary**
