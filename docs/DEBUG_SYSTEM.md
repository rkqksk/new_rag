# Debug System - Complete Documentation

**Status**: ✅ Complete - Option B Implementation  
**Date**: 2025-11-06

## Overview

Enterprise-grade debugging and observability system for RAG Enterprise backend. Provides comprehensive request tracing, performance profiling, and query logging.

## Table of Contents

1. [Features](#features)
2. [Configuration](#configuration)
3. [Middleware Stack](#middleware-stack)
4. [Debug Endpoints](#debug-endpoints)
5. [Usage Examples](#usage-examples)
6. [Performance Profiling](#performance-profiling)
7. [Query Logging](#query-logging)
8. [Troubleshooting](#troubleshooting)

---

## Features

### ✅ Implemented (Option B)

1. **Request Tracing** ✨
   - Correlation IDs for distributed tracing
   - Follows requests through entire pipeline
   - Context variables for cross-component tracing

2. **Request/Response Logging** 📝
   - Structured JSON logging
   - Sensitive data sanitization
   - Configurable verbosity

3. **Performance Timing** ⚡
   - Automatic request duration tracking
   - Slow request detection (configurable threshold)
   - Performance breakdown per checkpoint

4. **Enhanced Exceptions** 🔍
   - Context-rich error messages
   - Full stack traces with metadata
   - Structured exception logging

5. **Debug Endpoints** 🔧
   - `/debug/search/explain` - Search result explanation
   - `/debug/profile/{session_id}` - User profile inspector
   - `/debug/cache/stats` - Cache statistics
   - `/debug/qdrant/stats` - Vector DB statistics
   - `/debug/queries/recent` - Recent query log
   - `/debug/performance/summary` - Performance summary
   - `/debug/health/detailed` - Detailed health check

6. **Query Logging** 📊
   - PostgreSQL queries logged
   - Qdrant vector searches logged
   - Redis cache operations logged
   - Slow query detection

7. **Performance Profiler** 🎯
   - Bottleneck detection
   - Checkpoint-based profiling
   - Global statistics tracking
   - Actionable recommendations

8. **Debug Mode Configuration** ⚙️
   - Environment-based enabling
   - Granular feature control
   - Production-safe (disabled by default)

---

## Configuration

### Environment Variables

```bash
# Enable debug mode
DEBUG_ENABLED=true

# Request/Response logging
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=false  # Can be verbose

# Query logging
DEBUG_LOG_SQL=true
DEBUG_LOG_CACHE=true

# Performance profiling
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=500  # Threshold for slow requests

# Search explanations
DEBUG_EXPLAIN_SEARCH=true
```

### `.env` Example

```bash
# Development Environment with Full Debugging
ENVIRONMENT=development
DEBUG_ENABLED=true
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=true
DEBUG_LOG_SQL=true
DEBUG_LOG_CACHE=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=300
DEBUG_EXPLAIN_SEARCH=true
```

### Production Configuration

```bash
# Production Environment (Debug Disabled)
ENVIRONMENT=production
DEBUG_ENABLED=false
```

**⚠️ Important**: Debug mode should be disabled in production for performance and security.

---

## Middleware Stack

Middleware is applied in this order (important!):

```python
1. CORS Middleware          # Handle preflight requests
2. Request Tracing          # Add correlation IDs
3. Performance Timing       # Track request duration
4. Request Logging          # Log requests/responses (if enabled)
```

### Request Tracing Middleware

**Features:**
- Generates unique correlation ID per request
- Accepts `X-Correlation-ID` header from client
- Sets context variables for cross-component tracing
- Returns correlation ID in response headers

**Response Headers Added:**
```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
X-Request-Duration-Ms: 145.32
```

### Performance Timing Middleware

**Features:**
- Measures total request duration
- Detects slow requests (>500ms default)
- Provides timing breakdown hooks
- Logs slow requests automatically

**Slow Request Log Example:**
```json
{
  "timestamp": "2025-11-06T12:34:56Z",
  "level": "WARNING",
  "message": "⚠️ SLOW REQUEST: POST /api/v1/search/",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 687.5,
  "threshold_ms": 500
}
```

### Request Logging Middleware

**Features:**
- Logs request body (sanitized)
- Logs response status
- Redacts sensitive fields (password, token, api_key, secret)

**Log Example:**
```json
{
  "timestamp": "2025-11-06T12:34:56Z",
  "level": "DEBUG",
  "message": "Request body: POST /api/v1/search/",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_body": {
    "query": "50ml PET 용기",
    "top_k": 20,
    "session_id": "sess_123"
  }
}
```

---

## Debug Endpoints

All debug endpoints require `DEBUG_ENABLED=true` and are under `/api/v1/debug`.

### 1. Search Explanation

**Endpoint:** `POST /api/v1/debug/search/explain`

**Purpose:** Understand why products rank the way they do.

**Request:**
```json
{
  "query": "50ml PET 용기",
  "session_id": "sess_123",
  "top_k": 10
}
```

**Response:**
```json
{
  "query": "50ml PET 용기",
  "routing": {
    "query_type": "PRODUCT_SEARCH",
    "strategy": "TEXT_ONLY",
    "confidence": 0.95,
    "detected_entities": ["50ml", "PET", "용기"]
  },
  "embeddings": {
    "text_embedding_dim": 384,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_time_ms": 45.2
  },
  "vector_search": {
    "collection": "products_multimodal",
    "search_type": "text_only",
    "results_count": 20,
    "search_time_ms": 12.5,
    "avg_similarity": 0.78
  },
  "reranking": {
    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "input_count": 20,
    "output_count": 10,
    "reranking_time_ms": 85.3
  },
  "personalization": {
    "session_id": "sess_123",
    "focus_type": "compatibility",
    "boosts_applied": 3,
    "filters_applied": ["20파이 neck compatibility"]
  },
  "final_results": [
    {
      "rank": 1,
      "product_id": "PROD-001",
      "scores": {
        "vector_similarity": 0.85,
        "reranker_score": 0.92,
        "personalization_boost": 0.05,
        "final_score": 0.97
      },
      "explanation": "High semantic match + user preference"
    }
  ]
}
```

**Use Case:**
- Debug ranking issues
- Understand personalization impact
- Verify query routing works correctly

### 2. Profile Inspector

**Endpoint:** `GET /api/v1/debug/profile/{session_id}`

**Purpose:** Inspect user profile and behavior.

**Response:**
```json
{
  "profile": {
    "session_id": "sess_123",
    "search_history": ["50ml 용기", "20파이 캡"],
    "clicked_products": ["PROD-001", "PROD-002"],
    "preferences": {
      "categories": {"bottle": 0.6, "cap": 0.4},
      "suppliers": {"천진코리아": 0.8}
    },
    "focus_type": "compatibility"
  },
  "stats": {
    "total_searches": 15,
    "total_clicks": 8,
    "profile_age_hours": 24
  },
  "insights": {
    "most_searched_category": "bottle",
    "favorite_supplier": "천진코리아",
    "engagement_level": "high"
  }
}
```

**Use Case:**
- Debug personalization issues
- Understand user behavior
- Verify preference learning

### 3. Cache Statistics

**Endpoint:** `GET /api/v1/debug/cache/stats`

**Purpose:** Monitor cache performance.

**Response:**
```json
{
  "total_keys": 1250,
  "memory_used_mb": 45.8,
  "hit_rate_percent": 78.5,
  "miss_rate_percent": 21.5,
  "avg_ttl_seconds": 3600,
  "popular_keys": [
    {"pattern": "search:*", "count": 850},
    {"pattern": "profile:*", "count": 320}
  ],
  "recent_activity": {
    "last_5_minutes": {
      "hits": 1250,
      "misses": 340,
      "sets": 340
    }
  }
}
```

**Use Case:**
- Optimize cache strategy
- Identify cache misses
- Monitor memory usage

### 4. Recent Queries

**Endpoint:** `GET /api/v1/debug/queries/recent?limit=20&slow_only=false`

**Purpose:** View recent database/cache queries.

**Response:**
```json
{
  "queries": [
    {
      "timestamp": "2025-11-06T12:34:56Z",
      "type": "postgres",
      "query": "SELECT * FROM search_events WHERE session_id = $1",
      "duration_ms": 5.2,
      "rows_affected": 10
    },
    {
      "timestamp": "2025-11-06T12:34:55Z",
      "type": "qdrant",
      "query": "search(collection=products, vector=text, limit=20)",
      "duration_ms": 12.5,
      "results_count": 20
    }
  ]
}
```

**Use Case:**
- Identify slow queries
- Debug database issues
- Monitor query patterns

### 5. Performance Summary

**Endpoint:** `GET /api/v1/debug/performance/summary`

**Purpose:** System performance overview with bottleneck analysis.

**Response:**
```json
{
  "last_hour": {
    "total_requests": 1250,
    "avg_response_time_ms": 145.5,
    "p95_response_time_ms": 320.2,
    "slow_requests": 45
  },
  "bottlenecks": [
    {
      "component": "cross_encoder_reranking",
      "avg_time_ms": 85.3,
      "percent_of_total": 58.6,
      "recommendation": "Consider caching re-ranking results"
    }
  ],
  "by_endpoint": {
    "/api/v1/search/": {"count": 850, "avg_ms": 150.2}
  }
}
```

**Use Case:**
- Identify performance bottlenecks
- Optimize slow components
- Monitor system health

---

## Usage Examples

### 1. Debugging Slow Requests

```bash
# Enable debug mode
export DEBUG_ENABLED=true
export DEBUG_SLOW_REQUEST_MS=200

# Start server
python -m uvicorn app.main:app --reload

# Make request
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "50ml PET 용기", "top_k": 20}'

# Check logs for slow request warnings
# Look for: "⚠️ SLOW REQUEST: POST /api/v1/search/"
```

### 2. Tracing Requests with Correlation ID

```bash
# Send request with correlation ID
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "X-Correlation-ID: my-trace-123" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 10}'

# Response will include:
# X-Correlation-ID: my-trace-123
# X-Request-Duration-Ms: 145.32

# All logs will include correlation_id="my-trace-123"
# grep logs: jq 'select(.correlation_id=="my-trace-123")'
```

### 3. Explaining Search Results

```bash
# Get detailed explanation
curl -X POST http://localhost:8001/api/v1/debug/search/explain \
  -H "Content-Type: application/json" \
  -d '{
    "query": "20파이 캡 5000개",
    "session_id": "sess_123",
    "top_k": 5
  }'

# Response shows:
# - How query was routed
# - Embedding generation time
# - Vector search scores
# - Re-ranking changes
# - Personalization boosts
# - Final rankings with explanations
```

### 4. Inspecting User Profile

```bash
# View user's learned preferences
curl http://localhost:8001/api/v1/debug/profile/sess_123

# Response shows:
# - Search history
# - Interaction history
# - Learned preferences
# - Focus type (supplier/compatibility/material)
```

### 5. Monitoring Cache Performance

```bash
# Get cache statistics
curl http://localhost:8001/api/v1/debug/cache/stats

# Check hit rate:
# - High hit rate (>70%) = good caching
# - Low hit rate (<50%) = review cache strategy
```

---

## Performance Profiling

### Using the Profiler in Code

```python
from app.core.profiler import RequestProfiler, profile_checkpoint

async def search_with_profiling(query: str):
    with RequestProfiler("search_request") as profiler:
        # Checkpoint 1: Embedding
        profiler.checkpoint("embedding_start")
        embedding = await generate_embedding(query)
        profiler.checkpoint("embedding_done")
        
        # Checkpoint 2: Vector Search
        profiler.checkpoint("vector_search_start")
        results = await qdrant.search(embedding)
        profiler.checkpoint("vector_search_done")
        
        # Checkpoint 3: Re-ranking
        profiler.checkpoint("reranking_start")
        reranked = await reranker.rerank(query, results)
        profiler.checkpoint("reranking_done")
    
    # Get summary with bottleneck analysis
    summary = profiler.get_summary()
    
    # summary.bottlenecks shows which steps took >20% of time
    # summary.recommendations provides actionable advice
    
    return reranked
```

### Reading Profiler Output

```json
{
  "total_duration_ms": 145.5,
  "checkpoints": [
    {"name": "embedding", "duration_ms": 45.2},
    {"name": "vector_search", "duration_ms": 12.5},
    {"name": "reranking", "duration_ms": 85.3}
  ],
  "bottlenecks": [
    {
      "name": "reranking",
      "duration_ms": 85.3,
      "percent_of_total": 58.6
    }
  ],
  "recommendations": [
    "Re-ranking is taking 58.6% - consider reducing candidates"
  ]
}
```

---

## Query Logging

### How It Works

Query logging automatically captures:
- **PostgreSQL**: All SQL queries via decorator
- **Qdrant**: All vector searches
- **Redis**: All cache operations

### Viewing Query Log

```bash
# Get recent queries
curl http://localhost:8001/api/v1/debug/queries/recent?limit=20

# Get only slow queries (>100ms)
curl "http://localhost:8001/api/v1/debug/queries/recent?slow_only=true"
```

### Slow Query Detection

Queries are automatically flagged as slow if:
- Duration > 100ms
- Logged with `⚠️ SLOW QUERY:` prefix

**Example Slow Query Log:**
```json
{
  "timestamp": "2025-11-06T12:34:56Z",
  "level": "WARNING",
  "message": "⚠️ SLOW QUERY: postgres SELECT",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_type": "postgres",
  "operation": "SELECT",
  "duration_ms": 125.5,
  "query": "SELECT * FROM search_events WHERE timestamp > $1"
}
```

---

## Troubleshooting

### Debug Mode Not Working

**Problem:** Debug endpoints return 403 Forbidden

**Solution:**
```bash
# Check environment variable
echo $DEBUG_ENABLED  # Should be "true"

# Set in .env file
DEBUG_ENABLED=true

# Restart server
```

### Correlation IDs Not Showing in Logs

**Problem:** Logs don't include correlation_id

**Solution:**
- Ensure `RequestTracingMiddleware` is active
- Check middleware order (should be early in stack)
- Verify structured logging is enabled

### Slow Requests Not Logged

**Problem:** Slow requests not triggering warnings

**Solution:**
```bash
# Lower threshold
export DEBUG_SLOW_REQUEST_MS=200

# Enable profiling
export DEBUG_PROFILE_REQUESTS=true

# Restart server
```

### Too Much Logging in Production

**Problem:** Production logs too verbose

**Solution:**
```bash
# Disable debug mode
export DEBUG_ENABLED=false

# Or selectively disable features
export DEBUG_LOG_RESPONSES=false
export DEBUG_LOG_SQL=false
```

---

## Best Practices

### Development Environment

```bash
# Full debugging enabled
DEBUG_ENABLED=true
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=true
DEBUG_LOG_SQL=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=200
```

### Staging Environment

```bash
# Moderate debugging
DEBUG_ENABLED=true
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=false  # Can be verbose
DEBUG_LOG_SQL=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=500
```

### Production Environment

```bash
# Debug disabled (use only when troubleshooting)
DEBUG_ENABLED=false

# If troubleshooting in production:
# 1. Enable temporarily
# 2. Use high thresholds
# 3. Disable response logging
DEBUG_ENABLED=true
DEBUG_LOG_RESPONSES=false
DEBUG_SLOW_REQUEST_MS=1000
```

---

## Summary

| Feature | Status | Configuration |
|---------|--------|---------------|
| Request Tracing | ✅ Complete | Always on |
| Performance Timing | ✅ Complete | Always on |
| Request Logging | ✅ Complete | DEBUG_ENABLED=true |
| Debug Endpoints | ✅ Complete | DEBUG_ENABLED=true |
| Query Logging | ✅ Complete | DEBUG_LOG_SQL=true |
| Performance Profiler | ✅ Complete | DEBUG_PROFILE_REQUESTS=true |
| Exception Context | ✅ Complete | Always on |
| Slow Query Detection | ✅ Complete | DEBUG_SLOW_REQUEST_MS |

**Total Implementation**: **10 components** (Option B Complete)

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-06  
**Philosophy**: "백앤드는 맥시멀" - Maximum debugging capabilities for production-grade quality
