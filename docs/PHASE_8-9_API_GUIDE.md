# Phase 8-9 API Guide
**Version**: v8.5.0 - v8.6.0
**Date**: 2025-11-12

Complete API reference for Phase 8-9 advanced infrastructure features.

---

## Table of Contents

1. [Metrics API](#metrics-api)
2. [Recommendations API](#recommendations-api)
3. [Search Ranking API](#search-ranking-api)
4. [WebSocket API](#websocket-api)
5. [Rate Limiting](#rate-limiting)
6. [Error Tracking](#error-tracking)

---

## Metrics API

Base URL: `/api/v1/metrics`

### Dashboard Metrics

Get real-time dashboard metrics.

```http
GET /api/v1/metrics/dashboard
Authorization: Bearer {token}
```

**Requires**: Admin or Manager role

**Response**:
```json
{
  "success": true,
  "data": {
    "active_users": 42,
    "recent_searches": 156,
    "cache_hit_rate": 68.5,
    "recent_errors": 3,
    "timestamp": "2025-11-12T10:30:00Z"
  }
}
```

### Search Analytics

Get search analytics with date filters.

```http
GET /api/v1/metrics/search?start_date=2025-11-05&end_date=2025-11-12
Authorization: Bearer {token}
```

**Requires**: Admin or Manager role

**Parameters**:
- `start_date` (optional): ISO format date string
- `end_date` (optional): ISO format date string

**Response**:
```json
{
  "success": true,
  "data": {
    "total_searches": 1547,
    "avg_latency": 0.287,
    "avg_results": 8.3,
    "top_queries": [
      {"query": "50ml PET 용기", "count": 89},
      {"query": "100ml PP 용기", "count": 67}
    ]
  },
  "filters": {
    "start_date": "2025-11-05",
    "end_date": "2025-11-12"
  }
}
```

### Prometheus Metrics

Export metrics in Prometheus text format.

```http
GET /api/v1/metrics/prometheus
Authorization: Bearer {token}
```

**Requires**: Admin role

**Response**: Plain text Prometheus metrics

---

## Recommendations API

Base URL: `/api/v1/recommendations`

### User Recommendations

Get personalized recommendations for a user.

```http
GET /api/v1/recommendations/user/{user_id}?strategy=hybrid&top_k=10
Authorization: Bearer {token} (optional)
```

**Parameters**:
- `strategy`: `collaborative`, `content_based`, `hybrid`, `popular`, `trending`
- `top_k`: Number of recommendations (1-50)
- `collaborative_weight`: Weight for collaborative filtering (0-1, hybrid only)
- `content_weight`: Weight for content-based filtering (0-1, hybrid only)

**Response**:
```json
{
  "success": true,
  "user_id": "user_123",
  "strategy": "hybrid",
  "count": 10,
  "recommendations": [
    {
      "item_id": "product_456",
      "score": 0.89,
      "reason": "Similar users liked this and matches your preferences",
      "metadata": {
        "product_name": "50ml PET 용기",
        "category": "화장품용기",
        "price": 250
      }
    }
  ]
}
```

### Popular Items

Get popular or trending items.

```http
GET /api/v1/recommendations/popular?top_k=10&time_window_days=7
```

**Parameters**:
- `top_k`: Number of items (1-50)
- `time_window_days` (optional): Time window for trending (1-365 days)

**Response**:
```json
{
  "success": true,
  "type": "trending",
  "time_window_days": 7,
  "count": 10,
  "items": [
    {
      "item_id": "product_789",
      "score": 152.0,
      "reason": "Trending in last 7 days",
      "metadata": {}
    }
  ]
}
```

### Similar Items

Get similar items based on content features.

```http
GET /api/v1/recommendations/similar/{item_id}?top_k=5
```

**Parameters**:
- `top_k`: Number of similar items (1-50)

**Response**:
```json
{
  "success": true,
  "item_id": "product_456",
  "count": 5,
  "similar_items": [
    {
      "item_id": "product_457",
      "similarity": 0.94,
      "reason": "Similar to this item",
      "metadata": {}
    }
  ]
}
```

### Track Interaction

Track user-item interaction.

```http
POST /api/v1/recommendations/track
Authorization: Bearer {token}
Content-Type: application/json

{
  "item_id": "product_456",
  "interaction_type": "purchase",
  "score": 5.0
}
```

**Interaction Types**: `view`, `click`, `add_to_cart`, `like`, `share`, `purchase`, `review`

**Response**:
```json
{
  "success": true,
  "message": "Tracked purchase interaction for user user_123"
}
```

---

## Search Ranking API

Base URL: `/api/v1/search`

### Rank Results

Rank search results using advanced algorithms.

```http
POST /api/v1/search/rank
Content-Type: application/json

{
  "query": "50ml PET 용기",
  "results": [
    {"id": "1", "content": "50ml PET 용기..."},
    {"id": "2", "content": "100ml PET 용기..."}
  ],
  "vector_scores": [0.85, 0.78],
  "algorithm": "hybrid",
  "weights": {
    "vector": 0.5,
    "bm25": 0.3,
    "tfidf": 0.2
  }
}
```

**Algorithms**:
- `bm25`: BM25 algorithm (k1=1.5, b=0.75)
- `tfidf`: TF-IDF scoring
- `hybrid`: Combined vector + BM25 + TF-IDF

**Response**:
```json
{
  "success": true,
  "query": "50ml PET 용기",
  "algorithm": "hybrid",
  "count": 2,
  "results": [
    {
      "rank": 1,
      "id": "1",
      "content": "50ml PET 용기...",
      "metadata": {},
      "scores": {
        "final": 0.8245,
        "vector": 0.85,
        "bm25": 2.34,
        "tfidf": 0.45
      }
    }
  ]
}
```

### Re-rank with Features

Re-rank results using feature-based learning-to-rank.

```http
POST /api/v1/search/rerank
Content-Type: application/json

{
  "query": "50ml PET 용기",
  "results": [...],
  "initial_algorithm": "bm25"
}
```

**Response**: Same as rank results

### Build Index

Build search index from documents.

```http
POST /api/v1/search/index/build
Authorization: Bearer {token}
Content-Type: application/json

{
  "documents": [
    {"content": "Document text...", "metadata": {}},
    {"content": "Another document...", "metadata": {}}
  ]
}
```

**Requires**: Authenticated user

**Response**:
```json
{
  "success": true,
  "message": "Search index built successfully",
  "statistics": {
    "doc_count": 100,
    "avg_doc_length": 45.2,
    "unique_terms": 1523
  }
}
```

---

## WebSocket API

### Real-time Notifications

Connect to WebSocket for real-time notifications.

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8001/api/v1/ws/notifications?token=${token}`);

ws.onopen = () => {
    console.log('Connected');

    // Join a room
    ws.send(JSON.stringify({
        command: 'join_room',
        room: 'products'
    }));
};

ws.onmessage = (event) => {
    const notification = JSON.parse(event.data);
    console.log('Notification:', notification);
};
```

### Send Notification

Send notification to specific user.

```http
POST /api/v1/ws/send
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user_123",
  "notification_type": "work_order",
  "data": {
    "wo_number": "WO-2025-001",
    "product_name": "50ml PET 용기"
  },
  "priority": "high",
  "title": "새 작업 지시",
  "message": "50ml PET 용기 100개 - 2025-11-15까지"
}
```

**Notification Types**: `search_result`, `data_update`, `work_order`, `quality_alert`, `inventory_alert`, `system_message`, `user_message`, `error`

**Priority Levels**: `low`, `normal`, `high`, `urgent`

**Response**:
```json
{
  "success": true,
  "sent": true,
  "user_id": "user_123"
}
```

### Broadcast

Broadcast notification to all connected users.

```http
POST /api/v1/ws/broadcast
Authorization: Bearer {token}
Content-Type: application/json

{
  "notification_type": "system_message",
  "data": {},
  "priority": "normal",
  "title": "시스템 메시지",
  "message": "서버 점검 예정: 오늘 밤 11시-12시",
  "exclude_users": ["user_admin"]
}
```

**Response**:
```json
{
  "success": true,
  "recipients": 42
}
```

---

## Rate Limiting

All API endpoints are protected by rate limiting.

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1731398400
```

### Rate Limit Tiers

| Tier | Requests/Min | Requests/Hour | Requests/Day |
|------|--------------|---------------|--------------|
| **Free** | 10 | 100 | 1,000 |
| **Basic** | 60 | 1,000 | 10,000 |
| **Premium** | 300 | 10,000 | 100,000 |
| **Enterprise** | 1,000 | 50,000 | 500,000 |

### 429 Response

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45

{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 45,
  "limit": 60,
  "current": 61
}
```

---

## Error Tracking

All errors are automatically tracked with Sentry integration.

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid request data",
  "context": {
    "field": "email",
    "reason": "Invalid email format"
  }
}
```

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

---

## Frontend Integration

### Analytics Dashboard

```html
<script src="/js/auth.js"></script>
<script>
async function loadDashboard() {
    const response = await auth.fetchWithAuth(
        'http://localhost:8001/api/v1/metrics/dashboard'
    );
    const data = await response.json();
    // Update UI
}
</script>
```

### WebSocket Notifications

```html
<script src="/js/notifications.js"></script>
<script>
const notifications = new NotificationManager({
    apiBase: 'http://localhost:8001/api/v1',
    wsUrl: 'ws://localhost:8001/api/v1/ws/notifications',
    showToasts: true,
    onNotification: (notif) => {
        console.log('Received:', notif);
    }
});
</script>
```

### Recommendations Widget

```html
<div id="recommendations-container"></div>
<script src="/js/recommendations.js"></script>
<script>
const recommendations = new RecommendationsWidget({
    apiBase: 'http://localhost:8001/api/v1',
    containerId: 'recommendations-container',
    strategy: 'hybrid',
    topK: 10
});
</script>
```

---

## Configuration

### Environment Variables

```bash
# Sentry (Error Tracking)
SENTRY_DSN=https://xxx@sentry.io/xxx

# Redis (Rate Limiting & Analytics)
REDIS_URL=redis://localhost:16379/0

# Rate Limiting
RATE_LIMIT_DEFAULT_TIER=free
RATE_LIMIT_ALGORITHM=sliding_window
```

### Docker Compose

```yaml
services:
  api:
    environment:
      - SENTRY_DSN=${SENTRY_DSN}
      - REDIS_URL=redis://redis:6379/0
```

---

## Testing

### cURL Examples

```bash
# Get dashboard metrics
curl -X GET http://localhost:8001/api/v1/metrics/dashboard \
  -H "Authorization: Bearer $TOKEN"

# Get recommendations
curl -X GET "http://localhost:8001/api/v1/recommendations/user/user_123?strategy=hybrid&top_k=10"

# Rank search results
curl -X POST http://localhost:8001/api/v1/search/rank \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","results":[...],"algorithm":"bm25"}'

# Send WebSocket notification
curl -X POST http://localhost:8001/api/v1/ws/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_123","notification_type":"system_message","data":{},"title":"Test","message":"Hello"}'
```

---

## Troubleshooting

### Rate Limit Issues

```bash
# Check current usage
curl -X GET http://localhost:8001/api/v1/metrics/dashboard \
  -H "Authorization: Bearer $TOKEN" \
  -I

# Look for rate limit headers
X-RateLimit-Remaining: 45
```

### WebSocket Connection Issues

```javascript
// Enable debug logging
const ws = new WebSocket('ws://localhost:8001/api/v1/ws/notifications?token=xxx');
ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = () => console.log('WebSocket closed');
```

### Recommendation Issues

```bash
# Check recommendation statistics
curl -X GET http://localhost:8001/api/v1/recommendations/statistics \
  -H "Authorization: Bearer $TOKEN"
```

---

## Support

For issues or questions:
- Check `/api/v1/docs` for interactive API documentation
- View logs in `/var/log/rag-enterprise/`
- Report bugs on GitHub

---

**Version**: v8.6.0
**Last Updated**: 2025-11-12
