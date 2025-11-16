# RAG Consultation System - Phase 1 Implementation

**Version**: 1.0.0
**Status**: Production-Ready
**Date**: 2025-10-20

## Overview

Phase 1 implementation of the RAG Consultation System provides intelligent query classification and response generation for manufacturing AI consultation.

### Key Features

- **BERT-based Query Classification**: 7 query types with confidence scoring
- **Multi-label Intent Detection**: 6 intent types with pattern matching
- **Tone Analysis**: Formality, urgency, and expertise level detection
- **Multi-turn Conversation**: Session management with Redis persistence
- **LLM Integration**: Ollama (localhost:11434) with template-based responses
- **Query Expansion**: Synonym-based expansion and retrieval optimization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│                 /api/v1/consultation/query                   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    Classification Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Query      │  │   Intent     │  │    Tone      │      │
│  │ Classifier   │  │  Detector    │  │  Analyzer    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                     Context Layer                            │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Conversation    │◄───────►│  Context Store   │         │
│  │    Manager       │         │     (Redis)      │         │
│  └──────────────────┘         └──────────────────┘         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    Retrieval Layer                           │
│               ┌──────────────────┐                          │
│               │  Query Expander  │                          │
│               └──────────────────┘                          │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    Generation Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Prompt     │  │  Response    │  │  Template    │      │
│  │   Builder    │  │  Generator   │  │   System     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                          │                                   │
│                  ┌───────┴────────┐                         │
│                  │ Ollama LLM     │                         │
│                  │ localhost:11434│                         │
│                  └────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
app/rag_consultation/
├── __init__.py                  # Module exports
├── models.py                    # Pydantic data models
├── README.md                    # This file
│
├── classification/              # Query understanding
│   ├── __init__.py
│   ├── query_classifier.py     # BERT-based classification (7 types)
│   ├── intent_detector.py      # Multi-label intent (6 types)
│   ├── tone_analyzer.py        # Formality/urgency detection
│   └── language_detector.py    # Language identification
│
├── context/                     # Conversation management
│   ├── __init__.py
│   ├── conversation_manager.py # Multi-turn tracking
│   └── context_store.py        # Redis persistence
│
├── retrieval/                   # Query optimization
│   ├── __init__.py
│   └── query_expander.py       # Query expansion
│
└── generation/                  # Response generation
    ├── __init__.py
    ├── prompt_builder.py       # LLM prompt construction
    ├── response_generator.py   # Ollama integration
    └── template_system.py      # Response templates
```

## Configuration

### Critical: Ollama Endpoint

**MUST USE**: `http://localhost:11434`

Ollama runs on macOS via Ollama.app, **NOT** Docker.

```python
# Correct
ollama_url = "http://localhost:11434"

# WRONG - Do not use Docker IPs
ollama_url = "http://172.28.0.6:11434"  # ❌
```

### Environment Variables

Required in `.env`:

```bash
# Redis (for caching and session storage)
REDIS_HOST=172.28.0.3
REDIS_PORT=6379

# Ollama LLM (LOCAL ONLY)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct-q4_K_M
```

## API Endpoints

### POST /api/v1/consultation/query

Submit consultation query with intelligent classification.

**Request**:
```json
{
  "query": "How does RAG work?",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "metadata": {}
}
```

**Response**:
```json
{
  "response": "Generated answer...",
  "session_id": "session_abc123",
  "query_analysis": {
    "query_type": "factual",
    "confidence": 0.87,
    "query_type_scores": {...}
  },
  "intent": {
    "primary_intent": "information_seeking",
    "intents": {...}
  },
  "tone": {
    "formality": "neutral",
    "urgency": "medium",
    "expertise_level": "intermediate"
  },
  "retrieval_strategy": {
    "top_k": 5,
    "expanded_queries": [...],
    "use_hybrid": true
  },
  "confidence": 0.87
}
```

### GET /api/v1/consultation/context/{session_id}

Get conversation context and metadata.

**Response**:
```json
{
  "session_id": "session_abc123",
  "user_id": "user_xyz",
  "turn_count": 3,
  "created_at": "2025-10-20T10:00:00",
  "updated_at": "2025-10-20T10:05:00",
  "duration_minutes": 5.0,
  "summary": "3 turns: Query1; Query2; Query3"
}
```

### DELETE /api/v1/consultation/context/{session_id}

Clear conversation session.

### GET /api/v1/consultation/health

Service health check.

**Response**:
```json
{
  "status": "healthy",
  "ollama": "ok",
  "redis": "ok"
}
```

## Usage Examples

### Basic Query

```python
import httpx

async def query_consultation(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/consultation/query",
            json={"query": query}
        )
        return response.json()

# Example
result = await query_consultation("How does machine learning work?")
print(result["response"])
print(f"Query type: {result['query_analysis']['query_type']}")
```

### Multi-turn Conversation

```python
# First turn
result1 = await query_consultation("What is RAG?")
session_id = result1["session_id"]

# Second turn with session
async with httpx.AsyncClient() as client:
    result2 = await client.post(
        "http://localhost:8000/api/v1/consultation/query",
        json={
            "query": "How does it work?",
            "session_id": session_id
        }
    )

# Query "it" will be resolved to "RAG" from conversation history
```

## Query Type Classification

### 7 Query Types

1. **Factual**: "What is X?", "Define Y"
2. **Procedural**: "How to do X?", "Steps for Y"
3. **Comparison**: "X vs Y", "Difference between"
4. **Troubleshooting**: "Error in X", "Fix Y"
5. **Recommendation**: "Best X for Y", "Suggest Z"
6. **Exploratory**: Open-ended research
7. **Conversational**: Follow-ups, clarifications

### Intent Detection

6 multi-label intents:

- **information_seeking**: Looking for facts/data
- **problem_solving**: Fixing issues
- **decision_making**: Choosing options
- **learning**: Understanding concepts
- **validation**: Confirming correctness
- **clarification**: Seeking explanation

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/rag_consultation/ -v

# Specific module
pytest tests/unit/rag_consultation/test_query_classifier.py -v
```

### Integration Tests

```bash
# Run integration tests (requires fakeredis)
pytest tests/integration/rag_consultation/ -v

# Full pipeline test
pytest tests/integration/rag_consultation/test_consultation_pipeline.py::TestConsultationPipeline::test_end_to_end_consultation_flow -v
```

### Manual Testing

```bash
# Start services
docker-compose up -d redis

# Start Ollama (macOS)
# Ollama.app should be running

# Start FastAPI
uvicorn app.api.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/api/v1/consultation/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RAG work?"}'
```

## Performance Characteristics

### Latency

- **Query Classification**: ~100-200ms (cached: <10ms)
- **Intent Detection**: ~100-200ms (cached: <10ms)
- **Tone Analysis**: ~10-20ms (pattern-based)
- **LLM Generation**: ~2-5s (depends on Ollama model)
- **Total Pipeline**: ~3-6s per query

### Caching

- **Classification Cache**: 1 hour TTL
- **Session Storage**: 24 hour TTL
- **Redis Connection Pool**: 50 max connections

### Resource Usage

- **Memory**: ~500MB (with sentence transformer)
- **CPU**: 1-2 cores during classification
- **Disk**: Minimal (Redis persistence only)

## Dependencies

### Required Packages

```python
# Add to requirements.txt
sentence-transformers>=2.2.2  # Query classification
jinja2>=3.1.2                # Template rendering
httpx>=0.25.2                # Ollama client
```

### Optional (for testing)

```python
fakeredis>=2.20.0            # Redis mocking
pytest-asyncio>=0.21.1       # Async test support
```

## Error Handling

### Graceful Degradation

1. **Ollama Unavailable**: Return error with 503 status
2. **Redis Unavailable**: Classification works without caching
3. **Classification Timeout**: Default to conversational type
4. **Low Confidence**: Default to conversational with warning

### Error Responses

```json
{
  "detail": "Ollama service unavailable",
  "status_code": 503
}
```

## Security Considerations

1. **Input Validation**: All queries validated with Pydantic
2. **Rate Limiting**: TODO - Add rate limiting middleware
3. **Session Isolation**: Redis key namespacing prevents leaks
4. **Localhost Only**: Ollama restricted to localhost access

## Future Enhancements (Phase 2+)

1. **Actual Retrieval**: Integrate with Qdrant vector search
2. **Cross-encoder Reranking**: Improve result relevance
3. **Streaming Responses**: Real-time LLM output
4. **Multi-language**: Full i18n support
5. **Analytics**: Query pattern analysis and insights
6. **Fine-tuning**: Domain-specific model adaptation

## Troubleshooting

### Common Issues

**1. Ollama Connection Failed**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check Ollama.app is running on macOS
# Or start: ollama serve
```

**2. Redis Connection Failed**
```bash
# Check Redis container
docker-compose ps redis

# Test connection
redis-cli -h 172.28.0.3 -p 6379 ping
```

**3. Classification Slow**
```bash
# First run downloads model (~100MB)
# Subsequent runs use cached model
# Check: ~/.cache/huggingface/
```

**4. Import Errors**
```bash
# Install dependencies
pip install sentence-transformers jinja2 httpx
```

## Code Quality Standards

- **Type Hints**: 100% coverage with PEP 484
- **Docstrings**: Google-style for all public methods
- **Error Handling**: Comprehensive try-except with logging
- **Testing**: Unit + integration tests for all modules
- **Logging**: Structured logging with contextual info
- **Validation**: Pydantic models for all data structures

## License

Internal use only - RAG Enterprise Project

## Contact

For questions or issues, contact the RAG Enterprise team.

---

**Last Updated**: 2025-10-20
**Implementation**: Phase 1 Complete
**Next Phase**: Retrieval Integration (Phase 2)
