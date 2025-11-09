# Dependency Compatibility Matrix

**Version**: v5.0.0
**Last Updated**: 2025-11-08
**Python Version**: 3.11+

---

## Executive Summary

All major dependencies have been verified for compatibility with Python 3.11+ and each other through official PyPI documentation. The system is ready for upgrade with **6 major package updates**.

**Risk Level**: 🟡 **MEDIUM** - Requires testing due to 2 major version jumps (sentence-transformers, torch)

---

## Version Comparison

### Critical Updates

| Package | Current | Latest | Release Date | Risk | Priority |
|---------|---------|--------|--------------|------|----------|
| **sentence-transformers** | 2.2.2 | 5.1.2 | 2025-10-22 | 🔴 HIGH | ⭐⭐⭐ |
| **torch** | 2.1.1 | 2.9.0 | 2025-10-15 | 🔴 HIGH | ⭐⭐⭐ |
| **transformers** | 4.35.2 | 4.57.1 | 2025-10-14 | 🟡 MEDIUM | ⭐⭐ |
| **FastAPI** | 0.104.1 | 0.121.0 | 2025-11-03 | 🟢 LOW | ⭐⭐ |
| **Pydantic** | 2.5.0 | 2.12.4 | 2025-11-05 | 🟢 LOW | ⭐⭐ |
| **qdrant-client** | 1.7.0 | 1.15.1 | 2025-07-31 | 🟡 MEDIUM | ⭐ |

### Stable Packages (No Update Needed)

| Package | Current | Status | Notes |
|---------|---------|--------|-------|
| uvicorn | 0.24.0 | ✅ Stable | ASGI server |
| redis | 5.0.1 | ✅ Stable | Cache & rate limiting |
| psycopg2-binary | 2.9.9 | ✅ Stable | PostgreSQL driver |
| sqlalchemy | 2.0.23 | ✅ Stable | ORM |
| paddleocr | 2.7.0.3 | ✅ Stable | OCR engine |

---

## Compatibility Verification

### Python 3.11+ Requirements

✅ **All packages compatible with Python 3.11**

| Package | Min Python | Max Python | Status |
|---------|------------|------------|--------|
| FastAPI 0.121.0 | 3.8 | 3.14 | ✅ Compatible |
| Pydantic 2.12.4 | 3.9 | 3.14 | ✅ Compatible |
| torch 2.9.0 | 3.10 | 3.14 | ✅ Compatible |
| transformers 4.57.1 | 3.9 | 3.13 | ✅ Compatible |
| sentence-transformers 5.1.2 | 3.9 | 3.13 | ✅ Compatible |
| qdrant-client 1.15.1 | 3.9 | 3.13 | ✅ Compatible |

### Cross-Package Dependencies

```
FastAPI 0.121.0
├─ Requires: Python ≥3.8
├─ Requires: Pydantic 1.x or 2.x  ✅ (we have 2.12.4)
└─ Compatible: ✅

Pydantic 2.12.4
├─ Requires: Python ≥3.9
└─ Compatible: ✅

sentence-transformers 5.1.2
├─ Requires: Python 3.9-3.13
├─ Requires: PyTorch ≥1.11.0  ✅ (we have 2.9.0)
├─ Requires: transformers ≥4.34.0  ✅ (we have 4.57.1)
└─ Compatible: ✅

torch 2.9.0
├─ Requires: Python ≥3.10
└─ Compatible: ✅

transformers 4.57.1
├─ Requires: Python ≥3.9
├─ Requires: PyTorch ≥2.1  ✅ (we have 2.9.0)
└─ Compatible: ✅

qdrant-client 1.15.1
├─ Requires: Python ≥3.9
└─ Compatible: ✅
```

**Result**: ✅ **All dependencies are compatible**

---

## Breaking Changes & Migration Notes

### 1. sentence-transformers 2.2.2 → 5.1.2 (MAJOR UPGRADE)

**Risk**: 🔴 **HIGH** - Major version jump (2 → 5)

**Potential Breaking Changes**:
- API changes in model loading
- Encoding method signatures may differ
- Default hyperparameters may change
- Embedding output format changes

**Migration Actions**:
```python
# OLD (2.2.2)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)

# NEW (5.1.2) - API should be similar, but verify
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, normalize_embeddings=True)
```

**Testing Required**:
- [ ] Model loading (`SentenceTransformer()`)
- [ ] Batch encoding (`model.encode()`)
- [ ] Embedding dimensionality (should remain 384 for all-MiniLM-L6-v2)
- [ ] Vector search accuracy (compare similarity scores)

**Current Production Impact**:
- **Dataset**: 471 products → 3,246 chunks
- **Embeddings**: 384-dimensional vectors
- **Search Quality**: 0.79-0.82 similarity
- **Risk**: Embedding values may change slightly → **Re-embedding recommended**

---

### 2. torch 2.1.1 → 2.9.0 (MAJOR UPGRADE)

**Risk**: 🔴 **HIGH** - Major version jump (2.1 → 2.9)

**Potential Breaking Changes**:
- PyTorch 2.x compilation features
- CUDA compatibility (check GPU drivers)
- Memory management improvements
- Performance optimizations

**Migration Actions**:
```python
# Verify CUDA compatibility
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
```

**Testing Required**:
- [ ] GPU acceleration (if using CUDA)
- [ ] Model inference speed
- [ ] Memory usage patterns
- [ ] Embedding generation performance

**Current Production Impact**:
- **Embedding Speed**: 0.3ms/chunk (batch-32)
- **GPU Throughput**: 3,000 sentences/sec
- **Risk**: Performance may improve or degrade → **Benchmark required**

---

### 3. transformers 4.35.2 → 4.57.1 (MINOR UPGRADE)

**Risk**: 🟡 **MEDIUM** - Many new features, potential API changes

**Potential Breaking Changes**:
- Tokenizer improvements
- New model architectures
- Pipeline API changes

**Migration Actions**:
```python
# Verify transformers compatibility
from transformers import __version__
print(f"Transformers version: {__version__}")
```

**Testing Required**:
- [ ] Tokenizer loading
- [ ] Model loading
- [ ] NexaAI integration (Qwen models)

---

### 4. qdrant-client 1.7.0 → 1.15.1 (MINOR UPGRADE)

**Risk**: 🟡 **MEDIUM** - Many new features

**Potential Breaking Changes**:
- Collection management API
- Search parameters
- Scroll/filter syntax

**Migration Actions**:
```python
# Verify Qdrant client
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
print(client.get_collections())
```

**Testing Required**:
- [ ] Collection creation/deletion
- [ ] Vector search (`client.search()`)
- [ ] Scroll API
- [ ] Filter queries

**Current Production Impact**:
- **Collections**: 1 main collection (rag_enterprise_products)
- **Vectors**: 3,246 vectors (384-dim)
- **Search Latency**: < 100ms (top-5)
- **Risk**: API changes may require code updates

---

### 5. FastAPI 0.104.1 → 0.121.0 (PATCH UPGRADE)

**Risk**: 🟢 **LOW** - Patch release, backward compatible

**Potential Breaking Changes**: Minimal

**Migration Actions**:
```python
# Verify FastAPI + Pydantic compatibility
from fastapi import __version__ as fastapi_version
from pydantic import __version__ as pydantic_version
print(f"FastAPI: {fastapi_version}, Pydantic: {pydantic_version}")
```

**Testing Required**:
- [ ] API endpoint responses
- [ ] Pydantic validation
- [ ] Swagger UI (`/api/v1/docs`)

---

### 6. Pydantic 2.5.0 → 2.12.4 (PATCH UPGRADE)

**Risk**: 🟢 **LOW** - Patch release within v2 series

**Potential Breaking Changes**: Minimal (bug fixes only)

**Migration Actions**:
```python
# Verify Pydantic models
from pydantic import BaseModel
class TestModel(BaseModel):
    field: str
print(TestModel(field="test"))
```

**Testing Required**:
- [ ] Data model validation
- [ ] API request/response schemas
- [ ] Configuration settings

---

## Upgrade Procedure

### Step 1: Backup Current Environment

```bash
# Save current dependencies
pip freeze > requirements-backup-$(date +%Y%m%d).txt

# Backup database (optional but recommended)
docker exec -it qdrant bash -c "tar -czf /qdrant_backup.tar.gz /qdrant/storage"
docker cp qdrant:/qdrant_backup.tar.gz ./backups/
```

### Step 2: Update Dependencies

```bash
# Update pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install updated dependencies
pip install -r requirements-updated.txt
```

### Step 3: Verify Installation

```bash
# Check installed versions
pip list | grep -E "fastapi|pydantic|torch|transformers|sentence-transformers|qdrant-client"

# Expected output:
# fastapi                     0.121.0
# pydantic                    2.12.4
# torch                       2.9.0
# transformers                4.57.1
# sentence-transformers       5.1.2
# qdrant-client               1.15.1
```

### Step 4: Run Critical Tests

```bash
# Test 1: Import checks
python3 << EOF
import fastapi
import pydantic
import torch
import transformers
import sentence_transformers
from qdrant_client import QdrantClient
print("✅ All imports successful")
EOF

# Test 2: Embedding generation
python3 << EOF
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["test sentence"], normalize_embeddings=True)
print(f"✅ Embedding shape: {embeddings.shape}")
EOF

# Test 3: Qdrant connection
python3 << EOF
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections()
print(f"✅ Qdrant collections: {len(collections.collections)}")
EOF
```

### Step 5: Run Full Test Suite

```bash
# Run all tests
pytest tests/ -v --cov=src --cov=app

# Expected: 122+ tests passing
```

### Step 6: Re-embed Dataset (If Needed)

If sentence-transformers API changes affect embedding values:

```bash
# Backup current Qdrant data
docker exec -it qdrant bash -c "tar -czf /qdrant_backup.tar.gz /qdrant/storage"

# Re-run embedding pipeline
python3 scripts/pipeline/embed_products.py

# Verify vector count
curl http://localhost:6333/collections/rag_enterprise_products
# Expected: 3,246 vectors
```

### Step 7: Test API Endpoints

```bash
# Health check
curl http://localhost:8001/health/ready

# Search test
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'

# Expected: 5 results with similarity 0.79-0.82
```

### Step 8: Rollback (If Needed)

```bash
# If any issues occur, rollback
pip install -r requirements-backup-YYYYMMDD.txt

# Restore Qdrant data
docker cp ./backups/qdrant_backup.tar.gz qdrant:/
docker exec -it qdrant bash -c "tar -xzf /qdrant_backup.tar.gz -C /"
docker-compose restart qdrant
```

---

## Testing Checklist

### Core RAG Pipeline

- [ ] **Embedding Generation**
  - [ ] Model loading (sentence-transformers)
  - [ ] Batch encoding (32 chunks/batch)
  - [ ] Embedding dimensionality (384-dim)
  - [ ] Performance (0.3ms/chunk target)

- [ ] **Vector Search**
  - [ ] Qdrant connection
  - [ ] Search query (top-5)
  - [ ] Similarity scores (0.79-0.82 target)
  - [ ] Latency (< 100ms target)

- [ ] **LLM Integration**
  - [ ] NexaAI routing (< 500ms)
  - [ ] Ollama fallback (~2s)
  - [ ] Model inference (torch)

### API Endpoints (35+ endpoints)

- [ ] **RAG APIs**
  - [ ] POST /api/v1/search/
  - [ ] POST /api/v1/chat/
  - [ ] GET /api/v1/recommendations/

- [ ] **SaaS APIs**
  - [ ] POST /api/v1/saas/auth/register
  - [ ] POST /api/v1/saas/billing/subscribe
  - [ ] GET /api/v1/saas/usage/stats

- [ ] **Manufacturing APIs**
  - [ ] POST /api/v1/manufacturing/vision/inspect
  - [ ] GET /api/v1/manufacturing/quality/trends

- [ ] **Data Collector APIs**
  - [ ] POST /api/v1/collector/collect
  - [ ] GET /api/v1/collector/jobs/status

### Data Models (Pydantic)

- [ ] **Request Validation**
  - [ ] SearchRequest
  - [ ] ChatRequest
  - [ ] ProductCreate

- [ ] **Response Serialization**
  - [ ] SearchResponse
  - [ ] ChatResponse
  - [ ] ProductResponse

### Integration Tests

- [ ] **Skills → MCP → Services**
  - [ ] rag-pipeline skill → filesystem MCP → RAG service
  - [ ] web-scraping-expert → puppeteer MCP → scraping service
  - [ ] debugging-expert → chrome-devtools MCP → browser automation

- [ ] **End-to-End Flow**
  - [ ] User query → Classification → Retrieval → Generation → Response
  - [ ] Data collection → Processing → Embedding → Indexing

---

## Performance Benchmarks

### Before Upgrade (Current)

| Metric | Current Value | Target |
|--------|---------------|--------|
| Embedding Speed | 0.3ms/chunk | < 0.5ms |
| Vector Search | < 100ms (top-5) | < 100ms |
| NexaAI Inference | < 500ms | < 500ms |
| Ollama Inference | ~2s | < 3s |
| API Latency (P95) | < 200ms | < 200ms |

### After Upgrade (Expected)

| Metric | Expected | Notes |
|--------|----------|-------|
| Embedding Speed | 0.2-0.4ms/chunk | May improve with torch 2.9.0 |
| Vector Search | < 100ms | qdrant-client 1.15.1 optimizations |
| NexaAI Inference | < 500ms | No change expected |
| Ollama Inference | ~2s | No change expected |
| API Latency (P95) | < 200ms | FastAPI 0.121.0 improvements |

---

## Risk Mitigation

### High-Risk Packages (sentence-transformers, torch)

**Mitigation Strategies**:
1. Test in development environment first
2. Compare embedding outputs before/after upgrade
3. Benchmark inference speed
4. Keep backup of current embeddings
5. Re-embed dataset if needed

### Medium-Risk Packages (transformers, qdrant-client)

**Mitigation Strategies**:
1. Test API compatibility
2. Verify search results quality
3. Check for deprecation warnings

### Low-Risk Packages (FastAPI, Pydantic)

**Mitigation Strategies**:
1. Run existing test suite
2. Check API documentation generation

---

## Rollback Plan

If critical issues occur during or after upgrade:

1. **Stop all services**:
   ```bash
   ./scripts/restart-all.sh --clean
   ```

2. **Rollback Python packages**:
   ```bash
   pip install -r requirements-backup-YYYYMMDD.txt
   ```

3. **Restore Qdrant data** (if re-embedded):
   ```bash
   docker cp ./backups/qdrant_backup.tar.gz qdrant:/
   docker exec -it qdrant bash -c "tar -xzf /qdrant_backup.tar.gz -C /"
   ```

4. **Restart services**:
   ```bash
   ./scripts/deploy-optimized.sh development
   ```

5. **Verify health**:
   ```bash
   ./scripts/health-check.sh --verbose
   ```

---

## Approval & Sign-off

### Pre-Upgrade Checklist

- [ ] All compatibility checks passed
- [ ] Backup created (requirements, Qdrant data)
- [ ] Testing environment prepared
- [ ] Rollback plan documented

### Post-Upgrade Checklist

- [ ] All tests passing (122+ tests)
- [ ] Performance benchmarks met
- [ ] API endpoints functional
- [ ] No critical errors in logs
- [ ] Documentation updated

### Approved By

- **Technical Lead**: _________________ Date: _________
- **DevOps Lead**: _________________ Date: _________

---

**Version**: v5.0.0 | **Status**: Ready for Upgrade | **Risk**: 🟡 MEDIUM | **Priority**: ⭐⭐⭐ HIGH
