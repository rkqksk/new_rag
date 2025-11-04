# RAG Integration Plan
**Created**: 2025-10-21
**Optimization**: Sonnet 4.5 (planning/complex) + Haiku 4.5 (execution/simple)

## Current State Assessment

### Data Layer ✅
- **Products**: 846 successfully crawled
- **Structure**: Category/Material/{products, images, print_area}
  - Bottle: PE, PET, PETG, PP, Other
  - Jar: PE, PET, PETG, PP, Other
  - CapPump: PE, PET, PETG, PP, Other
  - 특별폴더: Other (uncategorized items)
- **Quality**: A+ grade (100% completeness)
- **Issues**: 95 CapPump products missing material specs (expected)

### Infrastructure Layer ⚠️
- **Docker**: Not running (Colima runtime needed)
- **Qdrant**: Vector DB not started (required for embeddings)
- **Redis**: Cache layer not started
- **FastAPI**: Application server not started
- **Ollama**: LLM runtime status unknown

### Embedding Layer ❌
- **Status**: Old embeddings (398 products from flat structure)
- **Required**: Regenerate for new 846-product hierarchy
- **Models**:
  - Text: gte-Qwen2-7B-instruct (or fallback: all-MiniLM-L6-v2)
  - Image: OpenCLIP-ViT-H-14
- **Target Collections**:
  - `products_bottle`
  - `products_jar`
  - `products_cappump`
  - `products_all` (unified)

### RAG Service Layer ❌
- **Code**: Exists (`app/services/rag_qa_service.py`)
- **Status**: Untested, requires running infrastructure
- **Features**: Capacity filtering, spec extraction, Ollama integration

---

## Task Breakdown (Complexity-Optimized)

### 🧠 COMPLEX TASKS (Sonnet 4.5)

#### Task 1: Infrastructure Architecture Review
**Complexity**: HIGH
**Why Sonnet**: Multi-service dependency analysis, port conflicts, network setup

**Analysis Needed**:
1. Review docker-compose.yml service dependencies
2. Check port availability (5432, 6333, 6379, 8000, 11434)
3. Verify volume mounts and permissions
4. Design startup sequence with health checks
5. Plan rollback strategy if services fail

**Deliverable**: Startup command sequence with validation gates

---

#### Task 2: Embedding Pipeline Architecture Update
**Complexity**: HIGH
**Why Sonnet**: Code analysis, path logic changes, batch optimization

**Analysis Needed**:
1. Analyze current pipeline structure (flat vs hierarchical)
2. Design path resolution for Category/Material/products
3. Plan batch processing strategy (4 workers, memory limits)
4. Calculate optimal chunk sizes for 846 products
5. Design error recovery for failed embeddings

**Code Changes Required**:
```python
# OLD: Flat structure
products_path = os.path.join(self.data_dir, category, "products")

# NEW: Hierarchical structure
for material in ["PE", "PET", "PETG", "PP", "Other"]:
    products_path = os.path.join(
        self.data_dir, category, material, "products"
    )
```

**Deliverable**: Updated `product_embedding_pipeline.py`

---

#### Task 3: RAG Service Integration Testing Strategy
**Complexity**: HIGH
**Why Sonnet**: Test case design, edge case identification, validation logic

**Test Scenarios**:
1. **Capacity Queries**: "50ml 용기 추천해줘"
   - Verify exact match filtering
   - Check fuzzy matching (48ml, 52ml tolerance)
   - Validate response ranking

2. **Material Queries**: "PET 재질 병"
   - Cross-material comparison
   - Material spec extraction accuracy

3. **Edge Cases**:
   - Products without material specs (95 CapPump items)
   - Missing images
   - Special folder products
   - Korean/English mixed queries

**Deliverable**: Test suite with expected outputs

---

### ⚡ SIMPLE TASKS (Haiku 4.5)

#### Task 4: Docker Service Startup
**Complexity**: LOW
**Why Haiku**: Sequential commands, simple validation

**Commands**:
```bash
# 1. Start Colima (if not running)
colima start

# 2. Start services
docker-compose up -d qdrant redis

# 3. Wait for health checks
docker-compose ps

# 4. Verify connectivity
curl http://localhost:6333/collections
curl http://localhost:6379/ping
```

**Validation**: All services show "healthy" status

---

#### Task 5: Run Embedding Pipeline
**Complexity**: LOW (execution only)
**Why Haiku**: Simple script execution, progress monitoring

**Commands**:
```bash
# Execute embedding pipeline
python agents/product_embedding_pipeline.py

# Monitor progress
tail -f logs/embedding_*.log

# Verify completion
cat embedding_report.json | jq '.all.total_products'
```

**Expected**: 846 products embedded, uploaded to Qdrant

---

#### Task 6: Verify Qdrant Collections
**Complexity**: LOW
**Why Haiku**: Simple API checks, count validation

**Verification**:
```bash
# Check collections exist
curl http://localhost:6333/collections | jq '.result.collections[].name'

# Verify counts
curl http://localhost:6333/collections/products_all | jq '.result.points_count'
curl http://localhost:6333/collections/products_bottle | jq '.result.points_count'
curl http://localhost:6333/collections/products_jar | jq '.result.points_count'
curl http://localhost:6333/collections/products_cappump | jq '.result.points_count'
```

**Expected**:
- `products_all`: 846 points
- `products_bottle`: ~500 points
- `products_jar`: ~200 points
- `products_cappump`: ~100 points

---

#### Task 7: Start FastAPI Service
**Complexity**: LOW
**Why Haiku**: Simple service startup, health check

**Commands**:
```bash
# Start FastAPI
docker-compose up -d fastapi

# Verify health
curl http://localhost:8000/health

# Check API docs
curl http://localhost:8000/docs
```

---

#### Task 8: Run Basic RAG Tests
**Complexity**: LOW (execution only)
**Why Haiku**: API calls with pre-defined test cases

**Test Commands**:
```bash
# Test 1: Simple capacity query
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "50ml 용기 추천해줘", "top_k": 5}'

# Test 2: Material query
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "PET 재질 병", "top_k": 5}'

# Test 3: General query
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "헤비브로우 용기", "top_k": 5}'
```

**Validation**: Each returns relevant products with confidence scores

---

## Execution Strategy

### Phase 1: Planning (Sonnet 4.5) ← YOU ARE HERE
- [x] Create comprehensive integration plan
- [ ] Review infrastructure architecture (Task 1)
- [ ] Design embedding pipeline updates (Task 2)
- [ ] Design test strategy (Task 3)

### Phase 2: Infrastructure Setup (Haiku 4.5)
- [ ] Start Docker services (Task 4)
- [ ] Verify service health

### Phase 3: Data Pipeline (Haiku 4.5 execution)
- [ ] Update embedding pipeline code (based on Sonnet design)
- [ ] Run embedding generation (Task 5)
- [ ] Verify Qdrant upload (Task 6)

### Phase 4: Service Deployment (Haiku 4.5)
- [ ] Start FastAPI service (Task 7)
- [ ] Verify API health

### Phase 5: Testing (Haiku 4.5 execution)
- [ ] Run basic tests (Task 8)
- [ ] Run comprehensive test suite (based on Sonnet design)

### Phase 6: Validation (Sonnet 4.5)
- [ ] Analyze test results
- [ ] Identify failure patterns
- [ ] Recommend optimizations

---

## Success Criteria

### Must Have ✅
1. All 846 products embedded in Qdrant
2. FastAPI service running and healthy
3. Basic queries return relevant results
4. Response time < 2 seconds per query

### Should Have 🎯
1. Capacity filtering working (exact + fuzzy)
2. Material filtering accurate
3. Image embeddings functional
4. Test coverage > 80%

### Nice to Have 🌟
1. Query result caching (Redis)
2. Multi-turn conversation support
3. Product recommendations
4. Admin UI for monitoring

---

## Risk Mitigation

### High Risk 🔴
**Docker services won't start**
- Mitigation: Check Colima status first, verify ports free
- Fallback: Use host-installed Qdrant/Redis

**Embedding fails for large models**
- Mitigation: Test with fallback model first (all-MiniLM-L6-v2)
- Fallback: Text-only embeddings (skip images)

### Medium Risk 🟡
**Old embeddings conflict with new data**
- Mitigation: Drop all collections before re-uploading
- Command: `curl -X DELETE http://localhost:6333/collections/products_all`

**Path resolution breaks for nested structure**
- Mitigation: Extensive logging, dry-run mode
- Validation: Check 5 sample products before full run

### Low Risk 🟢
**API quota exceeded**
- Already mitigated: Using local Ollama, not Claude API for RAG

---

## Next Steps

**IMMEDIATE** (Need user decision):
1. Confirm Docker/Colima should be started
2. Approve embedding pipeline architecture changes
3. Set priority: Speed vs. Quality (affects model selection)

**BLOCKED** (Waiting on decisions):
- Infrastructure startup (need approval to start Docker)
- Code changes (need architecture review)
- Testing (need running services)

**READY** (Can start immediately):
- Architecture review (Sonnet Task 1)
- Test strategy design (Sonnet Task 3)
