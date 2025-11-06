# RAG Enterprise - API Documentation

**Version**: 4.0.0
**Last Updated**: 2025-11-06
**Base URL**: `http://localhost:8001`

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Health & Status](#health--status)
4. [Search API](#search-api)
5. [Personalization API](#personalization-api)
6. [Analytics API](#analytics-api)
7. [Debug API](#debug-api)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

---

## Overview

The RAG Enterprise API provides production-grade search, personalization, and analytics capabilities with comprehensive debugging support.

### Base URLs

| Environment | Base URL |
|-------------|----------|
| Development | `http://localhost:8001` |
| Staging | `https://staging-api.your-company.com` |
| Production | `https://api.your-company.com` |

### API Versioning

All endpoints are versioned under `/api/v1/`. Future versions will be available at `/api/v2/`, etc.

### Content Type

All requests and responses use `application/json` unless otherwise specified.

---

## Authentication

**Current Status**: Open API (no authentication required for development)

**Future**: JWT-based authentication will be required for production:

```http
Authorization: Bearer <your_jwt_token>
```

---

## Health & Status

### Liveness Check

**Endpoint**: `GET /health/live`
**Description**: Basic liveness check (returns 200 if server is running)

**Response**:
```json
{
  "status": "alive"
}
```

**Status Codes**:
- `200 OK` - Service is alive

---

### Readiness Check

**Endpoint**: `GET /health/ready`
**Description**: Comprehensive readiness check (validates all dependencies)

**Response**:
```json
{
  "status": "ready",
  "debug_enabled": false,
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  },
  "timestamp": "2025-11-06T12:34:56.789Z"
}
```

**Status Codes**:
- `200 OK` - Service is ready
- `503 Service Unavailable` - One or more components unhealthy

---

## Search API

### Basic Text Search

**Endpoint**: `POST /api/v1/search/`
**Description**: Semantic search using text embedding

**Request Body**:
```json
{
  "query": "50ml PET 용기",
  "top_k": 10,
  "session_id": "optional_session_id",
  "filters": {
    "category": "bottle",
    "min_capacity": 50,
    "max_capacity": 100
  }
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | string | Yes | - | Search query text |
| top_k | integer | No | 10 | Number of results to return (max: 100) |
| session_id | string | No | null | User session ID for personalization |
| filters | object | No | {} | Metadata filters |

**Response**:
```json
{
  "query": "50ml PET 용기",
  "results": [
    {
      "id": "PROD-001",
      "score": 0.87,
      "product": {
        "code": "BOTTLE-50ML-001",
        "name": "50ml PET 원형 병",
        "category": "bottle",
        "capacity_ml": 50,
        "neck": "20파이",
        "material": "PET",
        "moq": 5000,
        "price_krw": 150
      },
      "chunk_type": "SPEC_COMPOSITE",
      "matched_content": "50ml PET 원형 병, 20파이 넥, MOQ 5000개"
    }
  ],
  "total": 10,
  "search_time_ms": 145.32,
  "personalized": true,
  "cached": false
}
```

**Status Codes**:
- `200 OK` - Search successful
- `400 Bad Request` - Invalid query parameters
- `500 Internal Server Error` - Search failed

---

### Image Search

**Endpoint**: `POST /api/v1/search/image`
**Description**: Visual similarity search using image embedding

**Request**: Multipart form data
- `image`: Image file (PNG, JPG, JPEG)
- `top_k`: Number of results (optional, default: 10)
- `session_id`: User session ID (optional)

**Response**:
```json
{
  "results": [
    {
      "id": "PROD-002",
      "score": 0.92,
      "product": {
        "code": "CAP-20MM-001",
        "name": "20파이 스크류 캡",
        "category": "cap",
        "image_url": "https://example.com/images/cap-001.jpg"
      },
      "similarity_type": "visual"
    }
  ],
  "total": 10,
  "search_time_ms": 234.56
}
```

---

### Hybrid Search

**Endpoint**: `POST /api/v1/search/hybrid`
**Description**: Combined text + image search with fusion

**Request Body**:
```json
{
  "text_query": "20파이 캡",
  "image": "base64_encoded_image",
  "text_weight": 0.6,
  "image_weight": 0.4,
  "top_k": 10,
  "session_id": "user_123"
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text_query | string | No | null | Text search query |
| image | string | No | null | Base64-encoded image |
| text_weight | float | No | 0.5 | Weight for text score (0-1) |
| image_weight | float | No | 0.5 | Weight for image score (0-1) |
| top_k | integer | No | 10 | Number of results |
| session_id | string | No | null | User session ID |

**Response**: Same format as text search, with additional `fusion_method` field

---

## Personalization API

### Track Search Event

**Endpoint**: `POST /api/v1/personalization/track`
**Description**: Track user interactions for personalization

**Request Body**:
```json
{
  "session_id": "user_123",
  "event_type": "click",
  "product_id": "PROD-001",
  "query": "50ml PET 용기",
  "product": {
    "code": "BOTTLE-50ML-001",
    "name": "50ml PET 원형 병",
    "category": "bottle"
  }
}
```

**Event Types**:
- `search` - User performed search
- `click` - User clicked on result
- `view` - User viewed product details
- `purchase` - User purchased product

**Response**:
```json
{
  "status": "tracked",
  "session_id": "user_123",
  "event_id": "evt_abc123"
}
```

**Status Codes**:
- `201 Created` - Event tracked successfully
- `400 Bad Request` - Invalid event data

---

### Get User Profile

**Endpoint**: `GET /api/v1/personalization/profile/{session_id}`
**Description**: Retrieve user behavior profile

**Response**:
```json
{
  "session_id": "user_123",
  "search_count": 45,
  "top_categories": ["bottle", "cap"],
  "top_keywords": ["PET", "50ml", "20파이"],
  "recent_searches": [
    {
      "query": "50ml PET 용기",
      "timestamp": "2025-11-06T12:30:00Z"
    }
  ],
  "preferences": {
    "capacity_range": [50, 200],
    "preferred_materials": ["PET", "HDPE"]
  }
}
```

---

## Analytics API

### Top Keywords

**Endpoint**: `GET /api/v1/analytics/keywords`
**Description**: Get most searched keywords

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of keywords to return |
| days | integer | 7 | Time window in days |

**Response**:
```json
{
  "keywords": [
    {
      "keyword": "PET",
      "count": 1234,
      "trend": "up"
    },
    {
      "keyword": "50ml",
      "count": 987,
      "trend": "stable"
    }
  ],
  "period": {
    "start": "2025-10-30",
    "end": "2025-11-06"
  }
}
```

---

### Trending Queries

**Endpoint**: `GET /api/v1/analytics/trending`
**Description**: Get trending search queries

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 5 | Number of queries to return |
| hours | integer | 24 | Time window in hours |

**Response**:
```json
{
  "trending": [
    {
      "query": "20파이 캡 5000개",
      "count": 156,
      "growth_rate": 2.3
    }
  ],
  "updated_at": "2025-11-06T12:00:00Z"
}
```

---

### Analytics Summary

**Endpoint**: `GET /api/v1/analytics/summary`
**Description**: Get overall analytics summary

**Response**:
```json
{
  "total_searches": 12345,
  "total_sessions": 3456,
  "avg_searches_per_session": 3.57,
  "top_categories": [
    {"category": "bottle", "count": 5678},
    {"category": "cap", "count": 3456}
  ],
  "period": {
    "start": "2025-11-01",
    "end": "2025-11-06"
  }
}
```

---

## Debug API

**Note**: Debug endpoints are only available when `DEBUG_ENABLED=true`

### Search Explanation

**Endpoint**: `POST /api/v1/debug/search/explain`
**Description**: Explain search result ranking

**Request Body**:
```json
{
  "query": "50ml PET 용기",
  "result_id": "PROD-001"
}
```

**Response**:
```json
{
  "query": "50ml PET 용기",
  "result_id": "PROD-001",
  "vector_score": 0.87,
  "reranking_score": 0.92,
  "personalization_boost": 0.05,
  "final_score": 0.97,
  "matched_chunks": [
    {
      "chunk_type": "SPEC_COMPOSITE",
      "content": "50ml PET 원형 병...",
      "similarity": 0.87
    }
  ]
}
```

---

### User Profile Inspector

**Endpoint**: `GET /api/v1/debug/profile/{session_id}`
**Description**: Detailed user profile with debug info

**Response**:
```json
{
  "session_id": "user_123",
  "search_history": [...],
  "interaction_counts": {
    "searches": 45,
    "clicks": 23,
    "views": 12
  },
  "preference_vector": [0.1, 0.2, ...],
  "cache_status": "active"
}
```

---

### Cache Statistics

**Endpoint**: `GET /api/v1/debug/cache/stats`
**Description**: Redis cache statistics

**Response**:
```json
{
  "total_keys": 1234,
  "hit_rate": 0.87,
  "memory_used_mb": 45.6,
  "evicted_keys": 12,
  "expired_keys": 34
}
```

---

### Vector Database Stats

**Endpoint**: `GET /api/v1/debug/qdrant/stats`
**Description**: Qdrant vector database statistics

**Response**:
```json
{
  "collections": [
    {
      "name": "products_multimodal",
      "vectors_count": 3246,
      "indexed_vectors_count": 3246,
      "points_count": 471,
      "segments_count": 1
    }
  ]
}
```

---

### Recent Queries

**Endpoint**: `GET /api/v1/debug/queries/recent`
**Description**: Recent query log

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 100 | Number of queries to return |
| slow_only | boolean | false | Only show slow queries (>100ms) |

**Response**:
```json
{
  "queries": [
    {
      "query": "50ml PET 용기",
      "duration_ms": 145.32,
      "timestamp": "2025-11-06T12:34:56Z",
      "correlation_id": "req_abc123",
      "cache_hit": false
    }
  ],
  "total": 100
}
```

---

### Performance Summary

**Endpoint**: `GET /api/v1/debug/performance/summary`
**Description**: System performance metrics

**Response**:
```json
{
  "avg_search_time_ms": 167.45,
  "p50_ms": 145.0,
  "p95_ms": 234.0,
  "p99_ms": 456.0,
  "cache_hit_rate": 0.67,
  "slow_queries_count": 12,
  "period_minutes": 60
}
```

---

### Detailed Health Check

**Endpoint**: `GET /api/v1/debug/health/detailed`
**Description**: Comprehensive health check with component details

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.3,
      "connections": 5
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 0.8,
      "memory_mb": 45.6
    },
    "qdrant": {
      "status": "healthy",
      "latency_ms": 12.4,
      "collections": 1
    }
  },
  "timestamp": "2025-11-06T12:34:56Z"
}
```

---

### Clear Cache

**Endpoint**: `POST /api/v1/debug/cache/clear`
**Description**: Clear Redis cache

**Request Body**:
```json
{
  "pattern": "search:*"
}
```

**Response**:
```json
{
  "status": "cleared",
  "keys_deleted": 234
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": "SearchException",
  "message": "Vector search failed: timeout",
  "context": {
    "query": "50ml PET 용기",
    "collection": "products_multimodal"
  },
  "correlation_id": "req_abc123",
  "timestamp": "2025-11-06T12:34:56Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Types

| Error Type | HTTP Code | Description |
|------------|-----------|-------------|
| ValidationException | 400 | Invalid input data |
| SearchException | 500 | Search operation failed |
| CacheException | 500 | Cache operation failed |
| DatabaseException | 500 | Database operation failed |
| VectorSearchException | 500 | Vector search failed |

---

## Rate Limiting

**Current Status**: No rate limiting (development)

**Future**:
- Anonymous users: 100 requests/minute
- Authenticated users: 1000 requests/minute
- Premium tier: 10,000 requests/minute

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1699280400
```

---

## Examples

### Python Client Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8001"

# Basic search
def search_products(query: str, top_k: int = 10):
    response = requests.post(
        f"{BASE_URL}/api/v1/search/",
        json={
            "query": query,
            "top_k": top_k,
            "session_id": "user_123"
        }
    )
    return response.json()

# Search and track interaction
def search_and_track(query: str):
    # 1. Perform search
    results = search_products(query)

    # 2. Track search event
    requests.post(
        f"{BASE_URL}/api/v1/personalization/track",
        json={
            "session_id": "user_123",
            "event_type": "search",
            "query": query
        }
    )

    # 3. If user clicks on result, track click
    if results["results"]:
        first_result = results["results"][0]
        requests.post(
            f"{BASE_URL}/api/v1/personalization/track",
            json={
                "session_id": "user_123",
                "event_type": "click",
                "product_id": first_result["id"],
                "query": query,
                "product": first_result["product"]
            }
        )

    return results

# Usage
results = search_and_track("50ml PET 용기")
print(f"Found {results['total']} results")
for result in results["results"]:
    print(f"- {result['product']['name']} (score: {result['score']})")
```

### JavaScript/Fetch Example

```javascript
// Basic search
async function searchProducts(query, topK = 10) {
  const response = await fetch('http://localhost:8001/api/v1/search/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      top_k: topK,
      session_id: 'user_123'
    })
  });

  return await response.json();
}

// Track interaction
async function trackInteraction(sessionId, eventType, productId, query) {
  await fetch('http://localhost:8001/api/v1/personalization/track', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      event_type: eventType,
      product_id: productId,
      query: query
    })
  });
}

// Usage
const results = await searchProducts('50ml PET 용기');
console.log(`Found ${results.total} results`);
```

### cURL Examples

```bash
# Basic search
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "50ml PET 용기",
    "top_k": 10,
    "session_id": "user_123"
  }'

# Get user profile
curl http://localhost:8001/api/v1/personalization/profile/user_123

# Get analytics summary
curl http://localhost:8001/api/v1/analytics/summary

# Debug: Get cache stats (requires DEBUG_ENABLED=true)
curl http://localhost:8001/api/v1/debug/cache/stats

# Health check
curl http://localhost:8001/health/ready
```

---

## Interactive API Documentation

**Swagger UI**: `http://localhost:8001/api/v1/docs`
**ReDoc**: `http://localhost:8001/api/v1/redoc`

The interactive documentation provides:
- Complete API specification
- Try-it-out functionality
- Request/response examples
- Schema definitions

---

## Support

**Documentation**:
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Debug System](./DEBUG_SYSTEM.md)
- [Roadmap](./ROADMAP.md)

**Issues**: Report at GitHub Issues

---

**Last Updated**: 2025-11-06
**Version**: 4.0.0
**Status**: Production-Ready ✅
