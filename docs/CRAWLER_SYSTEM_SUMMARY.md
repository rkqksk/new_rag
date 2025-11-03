# Web Crawler Agent System - Executive Summary

**Status**: Design Blueprint Complete  
**Created**: 2025-01-28  
**Scope**: Production-grade crawler for chunjinkorea.com, freemold.net, onehago.com

---

## What This System Does

A **robust, fault-tolerant web crawler** that:

- Crawls multiple e-commerce websites automatically
- Recovers from failures (network errors, rate limits, timeouts)
- Tracks progress and enables resuming interrupted crawls
- Provides real-time monitoring and detailed logging
- Scales horizontally across multiple server instances

---

## Key Capabilities

### Reliability

| Feature | Benefit |
|---------|---------|
| Exponential backoff retry | Automatic recovery from transient failures |
| Circuit breaker pattern | Prevents cascading failures |
| Dead letter queue | Tracks permanently failed items for review |
| State checkpointing | Resume interrupted crawls without data loss |
| Error classification | Intelligent retry decisions based on error type |

### Observability

| Feature | Benefit |
|---------|---------|
| Structured JSON logging | Machine-readable, queryable logs |
| Prometheus metrics | Performance monitoring and alerting |
| Real-time dashboards | Visual progress tracking |
| Health check endpoints | Automated health monitoring |
| Detailed error reports | Root cause analysis tools |

### Scalability

| Feature | Benefit |
|---------|---------|
| Async/await patterns | Non-blocking I/O for 1000s of concurrent requests |
| Connection pooling | Efficient resource utilization |
| Rate limiting per domain | Prevents overwhelming target sites |
| Horizontal scaling | Add more instances to increase throughput |
| Resource limits | Graceful degradation under load |

### Maintainability

| Feature | Benefit |
|---------|---------|
| Modular architecture | Each site has independent crawler |
| Configuration-driven | No code changes for selector updates |
| Comprehensive testing | 80%+ code coverage |
| Clear documentation | Operational runbooks included |
| Standard patterns | Familiar design patterns for team |

---

## Architecture at a Glance

```
┌─────────────────────────────────────────┐
│  User/Scheduler Request                 │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  CrawlerOrchestrator                    │
│  (Job management & coordination)         │
└──────────────────┬──────────────────────┘
                   ↓
        ┌──────────┼──────────┐
        ↓          ↓          ↓
    ┌────────────────────────────────┐
    │  Site-Specific Crawlers        │
    │  (Chungjin, Freemold, OneHago) │
    └────────────┬───────────────────┘
                 ↓
    ┌─────────────────────────────────┐
    │  Shared Infrastructure          │
    │  • RetryableHTTPClient          │
    │  • ParsingEngine                │
    │  • ErrorRecoveryManager         │
    │  • StateTracker                 │
    └────────────┬────────────────────┘
                 ↓
    ┌─────────────────────────────────┐
    │  Persistence & Monitoring       │
    │  • Database (job state)         │
    │  • Redis (metrics/cache)        │
    │  • File storage (downloads)     │
    │  • Prometheus (metrics)         │
    └─────────────────────────────────┘
```

---

## Error Handling Strategy

### Smart Retry Logic

When an error occurs:

1. **Classify** the error type
2. **Decide** whether to retry, skip, or alert
3. **Apply** appropriate recovery strategy

```
Transient Error (network timeout, 503)
    → Retry with exponential backoff (1s, 2s, 4s)

Rate Limit Error (429)
    → Retry with longer backoff (5s, 10s, 20s)

Permanent Error (404, 401, 403)
    → Skip item + alert operator

Parsing Error (invalid HTML, selector mismatch)
    → Log issue + try fallback selector

Unknown Error
    → Log for investigation + attempt 1 retry
```

### Circuit Breaker for Failing Sites

If a site becomes unreachable:

```
Normal (CLOSED):
  All requests pass through

Failing (OPEN):
  After 5 consecutive errors
  All requests fail immediately (fast-fail)
  Wait 60 seconds for recovery

Testing (HALF_OPEN):
  After timeout expires
  Allow limited requests to test recovery
  Return to CLOSED if successful
  Return to OPEN if failures continue
```

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Success Rate | > 95% | Design Target |
| Error Rate | < 5% | Design Target |
| Avg Latency | < 3s p95 | Design Target |
| Retry Success | > 50% | Design Target |
| Memory per Job | < 500MB | Design Target |
| Concurrent Jobs | 5+ | Design Target |

---

## Key Components

### 1. RetryableHTTPClient
Handles HTTP requests with intelligent retries
- Exponential backoff with jitter
- Circuit breaker per domain
- Connection pooling
- Configurable timeouts

### 2. ErrorRecoveryManager
Classifies errors and decides recovery action
- 7 error types (transient, rate limit, auth, etc.)
- Per-error-type recovery strategy
- Automatic alert triggering for critical errors

### 3. ParsingEngine
Extracts data from HTML with flexibility
- CSS selector-based extraction
- Fallback selector support
- Data validation and type coercion
- Image/file download handling

### 4. StateTracker
Maintains crawling progress for resume capability
- Job-level state (CREATED → PENDING → IN_PROGRESS → COMPLETED)
- Item-level tracking (success/failed/skipped)
- Checkpoint snapshots for recovery

### 5. Site-Specific Crawlers
Implements site-specific logic
- ChungjinCrawler: Handles group pagination, definition lists
- FreemoldCrawler: Site-specific selectors and logic
- OneHagoCrawler: Site-specific selectors and logic

### 6. CrawlerOrchestrator
Coordinates all crawling operations
- Job queue management
- Multi-site coordination
- Resource allocation
- Health monitoring

---

## Monitoring Capabilities

### Real-Time Metrics

```
Active Jobs: 3
Success Rate: 94.2%
Total Items Processed: 1,245
Average Latency: 2.3s

Per-Site Breakdown:
  chunjinkorea.com: 450/480 success (93.8%)
  freemold.net:     380/395 success (96.2%)
  onehago.com:      315/370 success (85.1%)

Error Analysis:
  Timeout: 27 (37.5%)
  Rate Limit (429): 24 (33.3%)
  Parsing: 16 (22.2%)
  Other: 5 (6.9%)
```

### Structured Logging (JSON)

Every significant event is logged in JSON format:

```json
{
  "timestamp": "2025-01-28T10:45:32.123Z",
  "level": "INFO",
  "event": "item_processed",
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "site_id": "chunjin",
  "item_id": "idx_960",
  "status": "success",
  "duration_ms": 2340,
  "attempts": 1
}
```

### Health Checks

Automated health checks provide system status:
- Site connectivity
- Circuit breaker state
- Error rate (last 1 hour)
- Response time (p95)
- Queue depth
- DLQ item count

---

## Resume Capability

**Problem**: What if crawler crashes or is manually stopped?

**Solution**: Automatic state checkpointing

```
While Crawling:
  Save after every page: "Processed page 5/68, items: 45"
  
On Failure:
  All progress is saved to database + checkpoint file
  
On Resume:
  Load last checkpoint
  Continue from "page 5, next item 46"
  No duplicate processing
```

**Result**: Zero data loss on interruption

---

## Database Schema

### Core Tables

```sql
CrawlJob
├── id: UUID
├── site_id: string (chunjin|freemold|onehago)
├── status: enum (pending, in_progress, paused, completed, failed)
├── config: JSON (selectors, retry policy, etc.)
├── stats: JSON (success/failure counts)
└── created_at, updated_at, completed_at

CrawlItem
├── id: UUID
├── job_id: FK → CrawlJob
├── item_id: string (product_id)
├── url: string
├── status: enum (pending, success, failed, skipped)
├── retries_count: int
├── last_error: JSON
└── crawled_data: JSONB

DeadLetterQueue
├── id: UUID
├── job_id: FK → CrawlJob
├── item_id: string
├── error_type: string
├── error_details: JSON
└── created_at: timestamp
```

---

## Deployment & Operations

### Pre-Deployment Checklist

- [ ] Unit tests passing (80%+ coverage)
- [ ] Integration tests passing
- [ ] Load tests completed
- [ ] Database migrations verified
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Runbooks documented

### Operational Metrics

```
Daily Report:
  Items crawled: 5,000
  Success rate: 94.2%
  Failed items in DLQ: 287
  Average response time: 2.3s
  Longest job duration: 2h 15m
  Total bandwidth used: 150MB
```

### Troubleshooting

**Problem**: High error rate (> 20%)
→ Check logs, verify site connectivity, review recent changes

**Problem**: Crawler slow (> 5s per item)
→ Increase concurrency, reduce delays, optimize parsing

**Problem**: Out of memory
→ Process in batches, save intermediate results, limit cache

**Problem**: Stuck job
→ Check database, review circuit breaker, manually restart

---

## Implementation Phases

### Phase 1: Core Foundation (2 weeks)
- RetryableHTTPClient
- ErrorRecoveryManager
- StateTracker
- Unit tests

### Phase 2: Site Crawlers (2 weeks)
- ChungjinCrawler (improve existing)
- FreemoldCrawler
- OneHagoCrawler
- Integration tests

### Phase 3: Orchestration (2 weeks)
- CrawlerOrchestrator
- Job queue
- Rate limiting
- Concurrency tests

### Phase 4: Monitoring (2 weeks)
- Prometheus metrics
- Dashboard API
- Health checks
- Alerting

### Phase 5: Advanced Features (2+ weeks)
- Circuit breaker
- Dead letter queue processing
- Auto recovery strategies
- Performance tuning

**Total**: ~10 weeks to production-ready system

---

## Success Criteria

### Reliability
- ✓ 95%+ success rate on clean data
- ✓ Automatic recovery from transient errors
- ✓ Zero data loss on interruption

### Performance
- ✓ < 3s p95 latency per item
- ✓ 5+ concurrent jobs without degradation
- ✓ < 500MB memory per crawler instance

### Observability
- ✓ Every event logged in structured format
- ✓ Real-time progress dashboard
- ✓ Automated alerting on failures
- ✓ Root cause analysis tools

### Maintainability
- ✓ 80%+ test coverage
- ✓ Configuration-driven selectors
- ✓ Clear error messages
- ✓ Operational runbooks

---

## Files Created

This design includes:

1. **CRAWLER_AGENT_DESIGN.md** (12,500 words)
   - Comprehensive architecture blueprint
   - Detailed component specifications
   - Error handling strategy
   - Monitoring & observability design
   - Scalability considerations
   - State management details

2. **CRAWLER_IMPLEMENTATION_GUIDE.md** (5,000 words)
   - Core patterns with code examples
   - Code templates for common scenarios
   - Testing checklist
   - Deployment checklist
   - Troubleshooting guide
   - Quick reference commands

3. **CRAWLER_SYSTEM_SUMMARY.md** (this file)
   - Executive summary
   - Key capabilities overview
   - Architecture at a glance
   - Performance targets
   - Implementation roadmap

---

## Next Steps

1. **Review**: Share design with team, gather feedback
2. **Refine**: Adjust based on feedback and constraints
3. **Plan**: Create detailed sprint tasks
4. **Implement**: Start with Phase 1 (Core Foundation)
5. **Test**: Comprehensive unit, integration, load testing
6. **Deploy**: Staged rollout (dev → staging → production)
7. **Monitor**: Track metrics, adjust as needed

---

## Questions to Answer

Before implementation:

- [ ] Database choice: PostgreSQL + Redis confirmed?
- [ ] Async framework: asyncio or other?
- [ ] Browser automation: Playwright or Selenium?
- [ ] Monitoring: Prometheus + Grafana?
- [ ] Alerting: Slack, PagerDuty, email?
- [ ] Deployment target: Docker, Kubernetes, or other?
- [ ] Team size: How many developers?
- [ ] Timeline: Hard deadline for production?

---

## References

**Internal**:
- `/docs/CRAWLER_AGENT_DESIGN.md` - Full design details
- `/docs/CRAWLER_IMPLEMENTATION_GUIDE.md` - Implementation patterns
- `/scripts/crawlers/chungjin_crawler.py` - Existing crawler reference

**External**:
- Exponential Backoff: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- Circuit Breaker: https://martinfowler.com/bliki/CircuitBreaker.html
- Prometheus: https://prometheus.io/
- Async Python: https://docs.python.org/3/library/asyncio.html

---

**Prepared by**: Claude Code  
**Date**: 2025-01-28  
**Status**: Ready for Review
