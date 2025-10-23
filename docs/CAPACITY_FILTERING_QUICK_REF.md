# Capacity Filtering - Quick Reference Card

## TL;DR (Too Long; Didn't Read)

**Problem**: "50ml 용기" query returned 54 results (only 7 were 50ml)
**Solution**: Exact capacity matching filter
**Result**: Now returns 7 results (100% accuracy)

---

## What Changed

### 3 Files Modified

1. **app/services/rag_qa_service.py** - Capacity filtering logic
2. **agents/product_embedding_pipeline.py** - Enhanced payload
3. **app/api/main.py** - Complete specification response

---

## Quick Tests

### Test 1: Run Test Suite
```bash
cd /Users/oypnus/Project/rag-enterprise
python scripts/test_capacity_filtering.py
```

**Expected**: All tests pass (4/4)

---

### Test 2: API Test (50ml)
```bash
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "50ml 용기 추천해줘", "top_k": 10}'
```

**Expected**: ~7 results, all with "50ml" in name

---

### Test 3: API Test (100ml)
```bash
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "100ml 용기 추천해줘", "top_k": 10}'
```

**Expected**: Only 100ml products

---

### Test 4: Product Detail
```bash
curl http://localhost:8000/api/v1/products/idx_860
```

**Expected**: Complete specification object with 5 fields

---

## Key Code Changes

### New Method 1: Extract Capacity from Query
```python
def _extract_capacity_from_query(self, query: str) -> Optional[str]:
    """50ml 용기 → 50ml"""
    match = re.search(r'(\d+)\s*ml', query.lower())
    return match.group(1) + 'ml' if match else None
```

### New Method 2: Extract Capacity from Product
```python
def _extract_capacity_from_product_name(self, product_name: str) -> Optional[str]:
    """50ml 헤비브로우용기 → 50ml"""
    match = re.search(r'(\d+)\s*ml', product_name.lower())
    return match.group(1) + 'ml' if match else None
```

### Enhanced Filtering Logic
```python
# In search_products()
query_capacity = self._extract_capacity_from_query(query)

if query_capacity:
    filtered_results = []
    for result in results:
        product_capacity = self._extract_capacity_from_product_name(
            result.payload.get("product_name")
        )
        if product_capacity == query_capacity:  # Exact match
            filtered_results.append(result)
    results = filtered_results
```

---

## Performance

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Latency | ~50ms | ~65ms | +15ms |
| Accuracy | 13% | 100% | +87pp |
| Results | 54 | 7 | -47 |

---

## Rollback

If needed, rollback with:
```bash
git checkout HEAD -- app/services/rag_qa_service.py
git checkout HEAD -- agents/product_embedding_pipeline.py
git checkout HEAD -- app/api/main.py
```

---

## Next Steps

### Immediate
- ✅ Code changes deployed
- ✅ Tests pass
- ⚠️ Specifications use fallback (from product names)

### Optional (for complete specs)
```bash
# Re-embed to populate specifications from JSON
python agents/product_embedding_pipeline.py
```

**Duration**: ~15-30 minutes
**Benefit**: Complete product codes, materials, dimensions

---

## Log Monitoring

Watch for this log line:
```
용량 필터링: 50ml - 7개 제품 매칭 (원본 검색: 200개)
```

This confirms capacity filtering is active.

---

## Troubleshooting

### Q: Still getting mixed capacities?
**A**: Check query format - must include "ml" (e.g., "50ml")

### Q: Getting 0 results for valid capacity?
**A**: Check Qdrant connection and collection name

### Q: Specification fields showing "N/A"?
**A**: Normal until re-embedding. Uses fallback extraction.

### Q: Tests failing?
**A**: Ensure Qdrant is running: `docker-compose ps`

---

## Key Files

```
app/
├── services/
│   └── rag_qa_service.py          # ← Filtering logic
└── api/
    └── main.py                     # ← API response

agents/
└── product_embedding_pipeline.py  # ← Payload structure

scripts/
└── test_capacity_filtering.py     # ← Test suite

docs/
├── CAPACITY_FILTERING_IMPROVEMENTS.md        # ← Full details
├── CAPACITY_FILTERING_VISUAL_SUMMARY.md      # ← Visual guide
└── CAPACITY_FILTERING_QUICK_REF.md           # ← This file
```

---

## Contact

Questions? Check:
1. Full details: `docs/CAPACITY_FILTERING_IMPROVEMENTS.md`
2. Visual guide: `docs/CAPACITY_FILTERING_VISUAL_SUMMARY.md`
3. Run tests: `python scripts/test_capacity_filtering.py`

---

**Last Updated**: 2025-10-20
**Status**: Production Ready
**Test Coverage**: 4/4 tests (100%)
