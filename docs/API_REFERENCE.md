# API Reference - v10.0.0

**Base URL**: `https://api.rag-enterprise.com`
**Version**: 10.0.0
**Authentication**: JWT Bearer Token

---

## Table of Contents

1. [Authentication](#authentication)
2. [Search API](#search-api)
3. [User Management](#user-management)
4. [Admin API](#admin-api)
5. [Health & Monitoring](#health--monitoring)

---

## Authentication

### POST /api/v1/auth/login

Login with email and password.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "usr_123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "customer",
    "tenantId": "ten_456"
  }
}
```

**Errors**:
- `401` - Invalid credentials
- `429` - Too many requests

---

### POST /api/v1/auth/register

Register new user account.

**Request**:
```json
{
  "email": "newuser@example.com",
  "password": "securepassword",
  "name": "Jane Smith",
  "tenantName": "ACME Corp"
}
```

**Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "usr_789",
    "email": "newuser@example.com",
    "name": "Jane Smith",
    "role": "customer"
  }
}
```

---

## Search API

### POST /api/v1/search/

Semantic search across indexed documents.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request**:
```json
{
  "query": "50ml PET bottle containers",
  "top_k": 5,
  "filters": {
    "category": "packaging",
    "min_price": 0,
    "max_price": 1000
  },
  "hybrid": true
}
```

**Response** (200 OK):
```json
{
  "query": "50ml PET bottle containers",
  "results": [
    {
      "id": "doc_123",
      "score": 0.89,
      "title": "50ml PET Clear Bottle",
      "content": "High-quality PET bottle...",
      "metadata": {
        "category": "packaging",
        "price": 0.45,
        "stock": 10000
      }
    }
  ],
  "total": 127,
  "took_ms": 45
}
```

---

### GET /api/v1/search/history

Get user's search history.

**Query Parameters**:
- `limit` (int, default: 20) - Number of results
- `offset` (int, default: 0) - Pagination offset

**Response** (200 OK):
```json
{
  "history": [
    {
      "id": "hist_456",
      "query": "packaging materials",
      "timestamp": "2025-11-16T10:30:00Z",
      "results_count": 15
    }
  ],
  "total": 50
}
```

---

## User Management

### GET /api/v1/users/me

Get current user profile.

**Response** (200 OK):
```json
{
  "id": "usr_123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "customer",
  "tenantId": "ten_456",
  "createdAt": "2025-01-01T00:00:00Z",
  "subscription": {
    "plan": "professional",
    "status": "active",
    "usageQuota": {
      "searches": 1000,
      "searchesUsed": 45
    }
  }
}
```

---

### PATCH /api/v1/users/me

Update user profile.

**Request**:
```json
{
  "name": "John Smith",
  "phone": "+1-555-0123"
}
```

**Response** (200 OK):
```json
{
  "message": "Profile updated",
  "user": { /* updated user object */ }
}
```

---

## Admin API

### GET /api/v1/admin/users

List all users (admin only).

**Query Parameters**:
- `page` (int, default: 1)
- `per_page` (int, default: 20)
- `role` (string) - Filter by role

**Response** (200 OK):
```json
{
  "users": [
    {
      "id": "usr_123",
      "email": "user@example.com",
      "role": "customer",
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

### GET /api/v1/admin/analytics

Get system analytics.

**Response** (200 OK):
```json
{
  "period": "2025-11",
  "metrics": {
    "total_searches": 15420,
    "total_users": 342,
    "active_users": 89,
    "avg_response_time_ms": 234
  },
  "top_queries": [
    {"query": "packaging", "count": 450},
    {"query": "containers", "count": 320}
  ]
}
```

---

## Health & Monitoring

### GET /health

Basic health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "10.0.0",
  "timestamp": "2025-11-16T22:45:00Z"
}
```

---

### GET /health/ready

Readiness probe (checks dependencies).

**Response** (200 OK):
```json
{
  "status": "ready",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  }
}
```

**Response** (503 Service Unavailable) - If dependencies down

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Email is required",
    "details": {
      "field": "email",
      "reason": "missing"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Bad request format |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limits

| Plan | Requests/minute | Requests/hour |
|------|----------------|---------------|
| Free | 10 | 100 |
| Starter | 60 | 1,000 |
| Professional | 120 | 5,000 |
| Enterprise | Unlimited | Unlimited |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

---

## OpenAPI Specification

Full OpenAPI 3.0 spec available at:
- **JSON**: `/api/v1/openapi.json`
- **YAML**: `/api/v1/openapi.yaml`
- **Swagger UI**: `/api/v1/docs`

---

**Last Updated**: 2025-11-16
**Support**: api-support@rag-enterprise.com
