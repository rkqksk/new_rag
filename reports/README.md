# Performance Baseline Reports - v10.0.0

**Date**: 2025-11-19
**Status**: Ready for Testing

---

## Quick Navigation

### Main Documents

1. **[Performance Baseline Summary](./PERFORMANCE_BASELINE_SUMMARY.md)** (22 KB)
   - Executive overview of all performance baselines
   - Quick start guide
   - Optimization roadmap
   - Industry benchmarks
   - **Start here** for high-level understanding

2. **[API Performance Baseline](./PERFORMANCE_BASELINE_API.md)** (17 KB)
   - API endpoint performance targets
   - Load testing scenarios
   - Bottleneck analysis
   - Optimization recommendations
   - Test commands and expected results

3. **[Frontend Performance Baseline](./PERFORMANCE_BASELINE_FRONTEND.md)** (21 KB)
   - Build performance metrics
   - Bundle size analysis
   - Core Web Vitals
   - Lighthouse testing
   - Image and code optimization

4. **[Database Performance Baseline](./PERFORMANCE_BASELINE_DATABASE.md)** (25 KB)
   - PostgreSQL query performance
   - Qdrant vector search
   - Redis caching
   - ClickHouse analytics
   - Index optimization

5. **[Load Testing Script](../scripts/load-test-baseline.sh)** (18 KB)
   - Automated load testing
   - Light, medium, heavy, stress tests
   - Python-based concurrent testing
   - JSON results output

---

## Quick Start

### 1. Run Load Tests
```bash
# Run all tests (light, medium, heavy)
/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh all

# Or run specific test
/home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh light

# View results
cat /home/rkqksk/projects/new_rag/reports/load-test-results.json
```

### 2. Test API Performance
```bash
# Health endpoint
time curl http://localhost:8001/health/ready

# Search endpoint
time curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"PET 용기","top_k":5}'
```

### 3. Test Frontend Performance
```bash
cd /home/rkqksk/projects/new_rag/apps/web

# Build test
time pnpm build

# Lighthouse test
npm install -g lighthouse
pnpm dev &
sleep 10
lighthouse http://localhost:3000 --output html
```

### 4. Test Database Performance
```bash
# PostgreSQL
docker exec -it new_rag-postgres-1 psql -U postgres -d rag_db
\timing on
SELECT * FROM products WHERE category = 'PET' LIMIT 20;

# Qdrant
curl -X POST http://localhost:16333/collections/products/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.1,0.2,...], "limit":5}'
```

---

## Performance Targets Summary

| Component | Metric | Target | Status |
|-----------|--------|--------|--------|
| **API** | Health endpoint | <50ms | ⏳ To test |
| **API** | Search endpoint | <500ms | ⏳ To test |
| **API** | QA endpoint | <1000ms | ⏳ To test |
| **API** | Throughput (100 users) | >100 req/s | ⏳ To test |
| **Frontend** | First Contentful Paint | <1.8s | ⏳ To test |
| **Frontend** | Time to Interactive | <3.8s | ⏳ To test |
| **Frontend** | Build time (cold) | <3min | ⏳ To test |
| **Frontend** | Bundle size | <200 KB | ⏳ To test |
| **PostgreSQL** | Simple SELECT | <20ms | ⏳ To test |
| **PostgreSQL** | JOIN query | <80ms | ⏳ To test |
| **Qdrant** | Vector search | <100ms | ⏳ To test |
| **Redis** | GET/SET | <5ms | ⏳ To test |

---

## Document Structure

### Each baseline document includes:

1. **Executive Summary** - Quick overview and targets
2. **Test Commands** - Copy-paste commands to run tests
3. **Expected Results** - What you should see
4. **Performance Breakdown** - Detailed analysis
5. **Bottlenecks** - Known performance issues
6. **Optimization Recommendations** - How to improve
7. **Industry Benchmarks** - How we compare
8. **Testing Checklist** - Pre-deployment checks
9. **Next Steps** - What to do after testing

---

## Optimization Roadmap

### Phase 1: Zero-Cost (Immediate)
- Enable response compression (40-60% bandwidth reduction)
- Implement Redis caching (80-95% latency reduction)
- Add database indexes (50-70% query speedup)
- Use Next.js Image component (70-85% smaller images)

**Expected Impact**: 40-70% performance improvement, $0 cost

### Phase 2: Low-Cost (1-4 weeks)
- Deploy to Vercel/Netlify (CDN)
- Add query queue and rate limiting
- Setup read replicas (PostgreSQL)
- Implement service worker (PWA)

**Expected Impact**: 50-80% performance improvement, $0-50/month

### Phase 3: Production (1-3 months)
- Horizontal scaling (2-5 API instances)
- Load balancer (Nginx/HAProxy)
- APM (Sentry, Datadog)
- Kubernetes orchestration

**Expected Impact**: 2-5x performance improvement, $50-500/month

---

## Testing Schedule

### Weekly
- [ ] Review performance metrics
- [ ] Check error logs
- [ ] Analyze slow queries

### Monthly
- [ ] Run full load tests
- [ ] Update baselines
- [ ] Implement optimizations

### Quarterly
- [ ] Comprehensive performance audit
- [ ] Benchmark against competitors
- [ ] Plan infrastructure upgrades

---

## Key Metrics to Track

### User-Centric
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)
- Cumulative Layout Shift (CLS)

### System
- API response time (p50, p95, p99)
- Error rate (%)
- Cache hit rate (%)
- Database query time

### Business
- Searches per minute
- QA queries per hour
- User engagement time
- Conversion rate

---

## Resources

### Internal
- **API Docs**: http://localhost:8001/api/v1/docs
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

### External
- **Web Vitals**: https://web.dev/vitals/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **PostgreSQL Performance**: https://www.postgresql.org/docs/16/performance-tips.html
- **Qdrant Docs**: https://qdrant.tech/documentation/

---

## Getting Help

### Common Issues

**API not responding**:
```bash
docker-compose up -d api postgres redis qdrant
docker-compose logs api
```

**Frontend build fails**:
```bash
cd apps/web
rm -rf .next node_modules
pnpm install
pnpm build
```

**Database connection error**:
```bash
docker-compose restart postgres
docker exec new_rag-postgres-1 pg_isready
```

**Load test script fails**:
```bash
# Install dependencies
python3 -m pip install requests aiohttp

# Make script executable
chmod +x /home/rkqksk/projects/new_rag/scripts/load-test-baseline.sh
```

---

## Contributing

### Adding New Benchmarks

1. Create test commands and expected results
2. Document in appropriate baseline file
3. Add to load testing script if applicable
4. Update summary document

### Updating Baselines

1. Run actual tests
2. Replace [TBD] with measured values
3. Update status from ⏳ to ✅ or ❌
4. Document any deviations from targets

---

## Changelog

### v1.0.0 (2025-11-19)
- Initial performance baseline documentation
- Created API, Frontend, Database baseline documents
- Implemented load testing script
- Established targets and optimization roadmap

---

**Version**: 1.0.0
**Last Updated**: 2025-11-19
**Status**: ✅ Ready for Testing
**Next Review**: After first load test execution
