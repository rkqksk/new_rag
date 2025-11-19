# Chat Interface - Testing Guide

**Current File**: `frontend/chat.html`
**URL**: http://localhost:8080/chat.html
**Backend**: http://localhost:8001

---

## 🚀 Quick Start

### 1. Start Backend
```bash
cd /Users/oypnus/Project/rag-enterprise
python run_chat_server.py
# Backend should run on: http://localhost:8001
```

### 2. Start Frontend
```bash
cd frontend
python3 -m http.server 8080
# Frontend available at: http://localhost:8080/chat.html
```

### 3. Open Browser
```
http://localhost:8080/chat.html
```

---

## 📋 Test Checklist

### ✅ Phase 1: Initial Load
- [ ] Page loads with white/minimal design
- [ ] Two-column layout visible (Chat | Products)
- [ ] Backend connection successful (check console)
- [ ] No JavaScript errors in console
- [ ] Session created automatically

### ✅ Phase 2: Basic Chat
**Test Query 1**: "50ml bottle"
- [ ] Message appears in chat (right aligned)
- [ ] Response appears (left aligned)
- [ ] Product panel updates with recommendations
- [ ] Product cards show:
  - Product image
  - Product name
  - Product code
  - Material type
  - Specifications

**Test Query 2**: "PET container for cosmetics"
- [ ] Different products appear
- [ ] Material filter applied (PET)
- [ ] Relevant recommendations only

**Test Query 3**: "Do you have 100ml bottles?"
- [ ] Context-aware response
- [ ] 100ml products highlighted
- [ ] Multiple size options shown

### ✅ Phase 3: Context Continuity
**Sequential Queries**:
1. "Show me 50ml bottles"
2. "Which ones are PET?"
3. "What about 100ml options?"

**Check**:
- [ ] Each query understands previous context
- [ ] Products update based on conversation flow
- [ ] Session maintained throughout

### ✅ Phase 4: Product Panel
- [ ] Product cards are clickable
- [ ] Product details expand on click
- [ ] Images load correctly
- [ ] Specifications formatted properly
- [ ] Material badges have correct colors

### ✅ Phase 5: Edge Cases

**Empty Query**:
- [ ] Try sending empty message
- [ ] System rejects or handles gracefully

**Long Query**:
- [ ] Enter 200+ character query
- [ ] Response handles long text
- [ ] UI doesn't break

**Special Characters**:
- [ ] Query: "50ml & 100ml bottles"
- [ ] Special characters handled correctly

**No Products Found**:
- [ ] Query: "10000ml bottle"
- [ ] Appropriate "no results" message
- [ ] Suggestions provided

### ✅ Phase 6: Session Management
- [ ] Refresh page
- [ ] New session created
- [ ] Previous chat cleared
- [ ] Start new conversation

### ✅ Phase 7: UI/UX Tests

**Responsiveness**:
- [ ] Desktop view (>1024px)
- [ ] Tablet view (768-1024px)
- [ ] Mobile view (<768px)
- [ ] Columns stack on mobile

**Scrolling**:
- [ ] Ask 10+ questions
- [ ] Chat auto-scrolls to bottom
- [ ] Product panel scrolls independently
- [ ] Smooth scroll behavior

**Visual Feedback**:
- [ ] Send button disables during request
- [ ] Loading indicator appears
- [ ] Hover effects on products
- [ ] Transitions smooth

---

## 🧪 API Testing

### Create Session
```bash
curl -X POST http://localhost:8001/chat/create_session \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected:
# {"session_id":"xxx-xxx-xxx","created_at":"2025-11-03T..."}
```

### Query
```bash
curl -X POST http://localhost:8001/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "query": "50ml PET bottle"
  }'

# Expected:
# {
#   "session_id": "xxx",
#   "query": "50ml PET bottle",
#   "intent": {...},
#   "response": "Here are 50ml PET bottles...",
#   "products": [...]
# }
```

### Health Check
```bash
curl http://localhost:8001/health
# Expected: {"status":"healthy"}
```

---

## 🎯 API Endpoints Reference

### Frontend → Backend Communication

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/chat/create_session` | POST | `{}` | `{session_id, created_at}` |
| `/chat/query` | POST | `{session_id, query}` | `{session_id, query, intent, response, products}` |

### Request/Response Models

**CreateSessionRequest**:
```json
{
  "user_id": "optional-user-id"  // Optional
}
```

**ChatQueryRequest**:
```json
{
  "session_id": "required-session-id",
  "query": "50ml PET bottle"
}
```

**ChatQueryResponse**:
```json
{
  "session_id": "xxx-xxx-xxx",
  "query": "50ml PET bottle",
  "intent": {
    "type": "product_search",
    "confidence": 0.95
  },
  "reference_resolved": true,
  "expanded_query": "50ml PET bottle for cosmetics",
  "response": "Here are 50ml PET bottles...",
  "products": [
    {
      "idx": "123",
      "product_name": "50ml PET Bottle",
      "product_code": "PET-50-001",
      "material": "PET",
      "capacity": "50ml",
      "neck_size": "24파이"
    }
  ],
  "context_used": ["previous query context"],
  "answer_type": "product_recommendation"
}
```

---

## 🐛 Troubleshooting

### Issue 1: Backend Connection Failed
**Symptoms**: "Cannot connect to backend" in console
**Solution**:
```bash
# Check backend is running
curl http://localhost:8001/health

# Restart backend
python run_chat_server.py
```

### Issue 2: Session Not Created
**Symptoms**: Cannot send messages
**Check**:
1. Console for errors
2. Backend logs
3. CORS settings in backend

### Issue 3: Products Not Showing
**Symptoms**: Chat works but products panel empty
**Check**:
1. Response has `products` array
2. Product data structure matches expected format
3. Console for rendering errors

### Issue 4: CORS Error
**Symptoms**: Browser blocks requests
**Solution**: Check `src/api/app.py` CORS middleware:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Expected Behavior

### Successful Session Creation
```
Console: "Session created: xxx-xxx-xxx"
```

### Successful Query
```
User: "50ml bottle"
Assistant: "I found several 50ml bottles for you..."
Products Panel: [3-5 product cards]
```

### Context Understanding
```
User: "Show me 50ml bottles"
Assistant: "Here are 50ml bottles..."
User: "Which ones are PET?"
Assistant: "Among the 50ml bottles, here are PET options..."
```

---

## 🔗 Related Files

### Frontend
- `frontend/chat.html` - Main chat interface
- `frontend/TEST_GUIDE.md` - This file

### Backend API
- `src/api/chat.py` - Chat endpoints
- `src/api/app.py` - FastAPI app setup
- `src/core/conversation_manager.py` - Session management
- `src/services/contextual_rag.py` - RAG logic

### Documentation
- `CLAUDE.md` - Quick reference
- `docs/ARCHITECTURE.md` - System architecture
- `README.md` - Project overview

---

## 📌 Notes

- **Port 8001**: Backend API server
- **Port 8080**: Frontend HTTP server
- **Design**: White/minimal (#f3f4f6 background)
- **Layout**: 2-column grid (chat + products)
- **Tech**: Pure HTML/CSS/JavaScript (no frameworks)

---

**Last Updated**: 2025-11-03
**Version**: 1.0
