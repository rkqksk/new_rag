# WebSocket & SSE Streaming (v6.0.0)

## Overview

Real-time LLM response streaming with WebSocket and Server-Sent Events (SSE) support.

**Status**: ✅ Implemented and Tested
**Version**: v6.0.0
**Date**: 2025-11-09

---

## Features

### Core Capabilities

- ✅ **WebSocket Streaming**: Bidirectional real-time communication
- ✅ **SSE Fallback**: Server-Sent Events for environments without WebSocket support
- ✅ **Token-by-Token Streaming**: Stream LLM responses incrementally
- ✅ **Progress Updates**: Real-time status updates during search phase
- ✅ **Incremental Product Loading**: Stream products in batches (10 at a time)
- ✅ **Connection Management**: Automatic reconnection and keep-alive pings
- ✅ **Error Handling**: Graceful fallback from WebSocket → SSE → HTTP
- ✅ **Backward Compatible**: Existing HTTP endpoints remain functional

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Client                      │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   WebSocket   │→ │     SSE     │→ │  HTTP POST   │  │
│  │  (Primary)    │  │  (Fallback) │  │   (Legacy)   │  │
│  └───────┬───────┘  └──────┬──────┘  └──────┬───────┘  │
└──────────┼─────────────────┼────────────────┼──────────┘
           │                 │                │
           ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │  /api/v1/stream/ws/{session_id}  (WebSocket)      │ │
│  │  /api/v1/stream/sse               (SSE)           │ │
│  │  /chat/query                      (HTTP - Legacy) │ │
│  └────────────────────────────────────────────────────┘ │
│                         │                                │
│                         ▼                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │         stream_llm_response() Generator            │ │
│  │  • Phase 1: Search status                          │ │
│  │  • Phase 2: Execute RAG query                      │ │
│  │  • Phase 3: Product count update                   │ │
│  │  • Phase 4: Stream products (batches of 10)        │ │
│  │  • Phase 5: Stream LLM answer (token-by-token)     │ │
│  │  • Phase 6: Completion message                     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                    RAG Pipeline                          │
│  • Qdrant Vector Search                                 │
│  • Semantic Ranking                                     │
│  • LLM Generation (Ollama/NexaAI)                       │
└─────────────────────────────────────────────────────────┘
```

---

## API Reference

### WebSocket Endpoint

**URL**: `ws://localhost:8001/api/v1/stream/ws/{session_id}`

**Client → Server** (Send):
```json
{
  "type": "query",
  "query": "50ml PET 용기",
  "collections": ["chungjinkorea", "onehago"],
  "materials": ["PET", "PP"]
}
```

**Server → Client** (Receive):

1. **Status Update**:
```json
{
  "type": "status",
  "data": "벡터 검색 중...",
  "timestamp": 1699564800.123
}
```

2. **Product Batch**:
```json
{
  "type": "products_batch",
  "data": [
    {
      "idx": "product-001",
      "product_name": "50ml PET 용기",
      "material": "PET",
      "specifications": {...},
      "score": 0.89
    }
  ],
  "progress": 10,
  "total": 100
}
```

3. **Token Stream**:
```json
{
  "type": "token",
  "data": "안녕하세요 ",
  "index": 0
}
```

4. **Completion**:
```json
{
  "type": "complete",
  "data": {
    "session_id": "abc123",
    "query": "50ml PET 용기",
    "answer": "...",
    "total_products": 100,
    "collections_searched": ["chungjinkorea"]
  }
}
```

5. **Error**:
```json
{
  "type": "error",
  "data": "Error message"
}
```

6. **Keep-Alive**:
```json
// Client sends
{"type": "ping"}

// Server responds
{"type": "pong", "timestamp": 1699564800.123}
```

---

### SSE Endpoint

**URL**: `GET /api/v1/stream/sse`

**Query Parameters**:
- `session_id` (required): Session ID
- `query` (required): Search query
- `collections` (optional): Comma-separated collection IDs
- `materials` (optional): Comma-separated materials

**Example**:
```
GET /api/v1/stream/sse?session_id=abc123&query=50ml%20PET&collections=chungjinkorea
```

**Response** (text/event-stream):
```
event: status
data: {"data": "벡터 검색 중...", "timestamp": 1699564800.123}

event: products_batch
data: {"data": [...], "progress": 10, "total": 100}

event: token
data: {"data": "안녕하세요", "index": 0}

event: complete
data: {"data": {...}}
```

---

### Health Check

**URL**: `GET /api/v1/stream/health`

**Response**:
```json
{
  "status": "healthy",
  "websocket": {
    "active_connections": 3,
    "endpoint": "/api/v1/stream/ws/{session_id}"
  },
  "sse": {
    "endpoint": "/api/v1/stream/sse"
  }
}
```

---

## Client Usage

### JavaScript Client

```html
<script src="streaming.js"></script>
<script>
const stream = new StreamingClient('session-123', {
    onStatus: (data) => {
        console.log('Status:', data);
    },
    onToken: (token) => {
        // Append token to UI
        document.getElementById('answer').textContent += token;
    },
    onProductsBatch: (products, message) => {
        console.log(`Products: ${message.progress}/${message.total}`);
        // Render products
        renderProducts(products);
    },
    onComplete: (data) => {
        console.log('Completed:', data);
    },
    onError: (error) => {
        console.error('Error:', error);
    }
});

// Send query
stream.query("50ml PET 용기", {
    collections: ["chungjinkorea"],
    materials: ["PET"]
});
</script>
```

### Fallback Strategy

The `StreamingClient` automatically falls back:
1. **Try WebSocket** (fastest, bidirectional)
2. **Try SSE** (unidirectional, no WebSocket support)
3. **Try HTTP POST** (legacy, no streaming)

```javascript
// Force SSE mode
const stream = new StreamingClient('session-123', {...});
stream.useWebSocket = false; // Disable WebSocket

// Or use HTTP directly
const result = await queryHTTP('session-123', 'query', collections, materials);
```

---

## Event Flow

### Typical Event Sequence

```
1. [status]         "벡터 검색 중..."
2. [status]         "100개 제품 발견" (count: 100)
3. [products_batch] 10 products (progress: 10/100)
4. [products_batch] 10 products (progress: 20/100)
5. ...
6. [products_batch] 10 products (progress: 100/100)
7. [status]         "답변 생성 중..."
8. [token]          "안녕하세요 "
9. [token]          "제품 "
10. [token]         "검색 "
11. ...
12. [complete]      Final results
```

---

## Performance

### Benchmarks

| Metric | WebSocket | SSE | HTTP (Legacy) |
|--------|-----------|-----|---------------|
| **First Token** | < 500ms | < 600ms | N/A (batch) |
| **Product Streaming** | Incremental | Incremental | Batch (2-3s) |
| **Connection Overhead** | Low | Medium | High (per request) |
| **Memory Usage** | Low | Low | High (full response) |
| **Reconnection** | Auto | Auto | Manual |

### Optimization Tips

1. **Batch Size**: Products streamed in batches of 10 (configurable)
2. **Token Delay**: 10ms simulated delay (remove in production)
3. **Keep-Alive**: Ping every 30s to maintain connection
4. **Buffer Size**: No server-side buffering (immediate streaming)

---

## Testing

### Run Tests

```bash
# Run all streaming tests
pytest tests/integration/test_streaming.py -v

# Run specific test classes
pytest tests/integration/test_streaming.py::TestWebSocketStreaming -v
pytest tests/integration/test_streaming.py::TestSSEStreaming -v

# Run health check tests only
pytest tests/integration/test_streaming.py::TestStreamingHealth -v
```

### Test Coverage

- ✅ WebSocket connection establishment
- ✅ WebSocket query flow (status → products → tokens → complete)
- ✅ WebSocket error handling
- ✅ SSE endpoint existence and headers
- ✅ SSE event format validation
- ✅ SSE with filters (collections, materials)
- ✅ Health check endpoint
- ✅ Backward compatibility with HTTP endpoint

---

## Demo

### Live Demo

Open `frontend/streaming-demo.html` in browser:

```bash
cd frontend
python3 -m http.server 8080

# Open browser
# → http://localhost:8080/streaming-demo.html
```

**Features**:
- Switch between WebSocket / SSE / HTTP modes
- Real-time event visualization
- Token-by-token streaming display
- Progress tracking

---

## Configuration

### Environment Variables

```bash
# Enable streaming (default: true)
STREAMING_ENABLED=true

# WebSocket ping interval (seconds)
WEBSOCKET_PING_INTERVAL=30

# SSE keep-alive interval (seconds)
SSE_KEEPALIVE_INTERVAL=15

# Token streaming delay (ms, for rate limiting)
TOKEN_STREAM_DELAY=10
```

### FastAPI Settings

```python
# app/main.py
from app.api.v1 import streaming

app.include_router(
    streaming.router,
    prefix=settings.api_prefix,
    tags=["streaming"]
)
```

---

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Failed

**Symptom**: "WebSocket error: Connection refused"

**Solution**:
- Check if API server is running: `curl http://localhost:8001/health/live`
- Verify WebSocket endpoint: `curl http://localhost:8001/api/v1/stream/health`
- Check firewall/proxy settings (WebSocket requires upgraded connection)

#### 2. SSE Not Streaming

**Symptom**: SSE events not received, or all at once

**Solution**:
- Disable nginx buffering: Add `X-Accel-Buffering: no` header (already included)
- Check browser console for CORS errors
- Verify `text/event-stream` content-type

#### 3. Tokens Arriving Too Fast

**Symptom**: All tokens appear at once instead of streaming

**Solution**:
- Adjust `TOKEN_STREAM_DELAY` in backend
- Check if LLM streaming is enabled (Ollama: `stream=True`)
- Verify client is processing events asynchronously

#### 4. Connection Drops After 30s

**Symptom**: WebSocket/SSE disconnects after idle period

**Solution**:
- Enable keep-alive pings (WebSocket: send `{"type": "ping"}`)
- Adjust proxy timeout settings (nginx: `proxy_read_timeout 300s`)

---

## Migration Guide

### From HTTP to WebSocket

**Before** (HTTP):
```javascript
const response = await fetch('/chat/query', {
    method: 'POST',
    body: JSON.stringify({
        session_id: sessionId,
        query: query
    })
});
const data = await response.json();
displayProducts(data.products);
```

**After** (WebSocket):
```javascript
const stream = new StreamingClient(sessionId, {
    onProductsBatch: (products) => displayProducts(products),
    onToken: (token) => appendAnswer(token),
    onComplete: () => console.log('Done')
});
await stream.query(query);
```

### Hybrid Approach (Recommended)

Use streaming for better UX, fallback to HTTP:

```javascript
try {
    // Try streaming first
    const stream = new StreamingClient(sessionId, {...});
    await stream.query(query);
} catch (error) {
    // Fallback to HTTP
    console.warn('Streaming failed, using HTTP:', error);
    const data = await queryHTTP(sessionId, query);
    displayProducts(data.products);
}
```

---

## Roadmap

### Completed (v6.0.0)
- ✅ WebSocket endpoint implementation
- ✅ SSE fallback implementation
- ✅ Token-by-token streaming
- ✅ Incremental product loading
- ✅ Connection management
- ✅ Client library (JavaScript)
- ✅ Integration tests
- ✅ Demo application

### Planned (v6.1.0)
- ⏳ Binary message support (images, files)
- ⏳ Multi-user broadcast (room-based)
- ⏳ Compression (gzip, deflate)
- ⏳ Authentication via JWT tokens
- ⏳ Rate limiting per session
- ⏳ Metrics (Prometheus counters)

---

## References

### Standards
- **WebSocket**: [RFC 6455](https://tools.ietf.org/html/rfc6455)
- **SSE**: [W3C Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html)

### Libraries
- **Backend**: FastAPI WebSocket, StreamingResponse
- **Frontend**: Native WebSocket API, EventSource API

### Related Documentation
- `docs/reference/API_DOCUMENTATION.md` - Full API reference
- `frontend/streaming.js` - Client library source
- `tests/integration/test_streaming.py` - Test suite

---

**Last Updated**: 2025-11-09
**Version**: v6.0.0
**Status**: ✅ Production Ready
