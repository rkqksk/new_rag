# Quality Improvement Implementation Guide

## 📋 Overview

This guide provides step-by-step instructions for implementing the two-stage RAG system with product dictionary enrichment.

## 🎯 What We've Built

### 1. Product Dictionary (`data/product_dictionary.json`)
Enriched product information including:
- Detailed descriptions
- Use cases and scenarios
- Target customers
- Material benefits
- Capacity information
- Related products
- Recommendation guidelines

**Sample Coverage**: 5 products (idx_13, idx_30, idx_308, idx_360, idx_417)

### 2. Two-Stage RAG Service (`app/services/two_stage_rag_service.py`)
- **Stage 1 (Planning)**: Claude Sonnet 4.5 analyzes query and creates execution plan
- **Stage 2 (Execution)**: Qwen 2.5 generates answer with enriched context

### 3. Test Script (`scripts/test_quality_improvement.py`)
Compares current vs improved system quality

---

## 🚀 Quick Start

### Prerequisites
```bash
# 1. Ensure services are running
docker-compose up -d  # Qdrant, Ollama

# 2. Set API key (for Sonnet planning)
export ANTHROPIC_API_KEY="your_key_here"

# 3. Verify Qdrant has embedded products
curl -s http://localhost:6333/collections/products_all | jq '.result.points_count'
```

### Run Test
```bash
cd /Users/oypnus/Project/rag-enterprise
python scripts/test_quality_improvement.py
```

**Expected Output**:
```
Query: 50ml 용기 추천해줘
--- Current System ---
Answer: 50ml 브로우용기를 추천합니다...
Quality Score: 4/10
Products: 3 (enriched: 0)

--- Improved System ---
Answer: 50ml PE 브로우용기 (BE050-R001)를 추천드립니다.
추천 이유:
- 용량: 에센스/세럼용 최적 사이즈 (3-4주 사용량)
- 재질: PE 소재로 안전하고 가벼움...
Quality Score: 9/10
Products: 3 (enriched: 1)
Plan: {intent: "제품 추천", capacity_filter: "50ml", ...}
```

---

## 📊 Quality Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Quality Score | 3-4/10 | 8-10/10 | Automated scoring in test script |
| Answer Length | 50-100 chars | 200-400 chars | Character count |
| Has Product Code | 20% | 90% | Regex check for product codes |
| Has Material Info | 30% | 90% | Contains PE/PET/material keywords |
| Has Use Cases | 10% | 80% | Contains "용도", "사용", "적합" |
| Enriched Products | 0% | 60%+ | Products with dictionary data |

---

## 🔧 Extending the Dictionary

### Option 1: Manual Entry (Recommended for critical products)

```python
# Add to data/product_dictionary.json
{
  "idx_XXX": {
    "product_id": "idx_XXX",
    "product_code": "BE050-R001",
    "product_name": "50ml 브로우용기",
    "enriched_info": {
      "detailed_description": "...",
      "use_cases": [...],
      "target_customers": [...],
      "material_benefits": {...},
      "capacity_info": {...},
      "recommendations": {...}
    }
  }
}
```

### Option 2: LLM-Assisted Generation

```python
# scripts/generate_dictionary_entries.py (create this)
import asyncio
from app.services.two_stage_rag_service import TwoStageRAGService

async def generate_entry(product_data):
    """Use Sonnet to generate dictionary entry from product JSON"""
    prompt = f"""
    Create enriched product information for:
    Product: {product_data['product_name']}
    Specs: {product_data['specifications']}

    Generate JSON with: detailed_description, use_cases,
    target_customers, material_benefits, etc.
    """
    # Call Sonnet and parse response
    # ...
```

### Option 3: Template-Based (Fast scaling)

```python
# Use templates based on capacity and material
TEMPLATES = {
    "small_PE": {
        "use_cases": ["에센스", "세럼", "샘플", "트래블"],
        "target_customers": ["스타트업", "샘플 업체"],
        # ...
    },
    "large_PET": {
        "use_cases": ["토너", "바디로션", "대용량"],
        # ...
    }
}
```

---

## 🔄 Integration with Production API

### Step 1: Update API Endpoint

Edit `app/api/main.py`:

```python
from app.services.two_stage_rag_service import TwoStageRAGService

# Add new endpoint
@app.post("/api/v1/qa/improved")
async def improved_qa(request: QARequest):
    """Improved Q&A with two-stage RAG"""
    result = await two_stage_qa_service.answer_question(
        question=request.question,
        collection=request.collection
    )
    return result
```

### Step 2: A/B Testing

```python
# Route 50% traffic to improved system
import random

@app.post("/api/v1/qa")
async def qa_with_ab_test(request: QARequest):
    if random.random() < 0.5:
        # Use improved system
        result = await two_stage_qa_service.answer_question(...)
    else:
        # Use current system
        result = await current_qa_service.answer_question(...)

    # Log for comparison
    log_ab_test_result(result)
    return result
```

### Step 3: Gradual Rollout

1. **Week 1**: 10% traffic to improved system
2. **Week 2**: 30% traffic if metrics improve
3. **Week 3**: 60% traffic if user satisfaction increases
4. **Week 4**: 100% migration

---

## 🧪 Testing Strategy

### 1. Unit Tests
```python
# tests/test_two_stage_rag.py
def test_query_planning():
    plan = await service.plan_query("50ml 용기 추천해줘")
    assert plan.capacity_filter == "50ml"
    assert plan.top_k >= 3

def test_dictionary_enrichment():
    product = {"product_id": "idx_13", ...}
    enriched = dictionary.enrich_product(product)
    assert "enriched" in enriched
    assert enriched["enriched"]["detailed_description"]
```

### 2. Integration Tests
```bash
# Test full pipeline
pytest tests/test_two_stage_rag.py -v

# Test with real Qdrant and Ollama
pytest tests/integration/ -v
```

### 3. Quality Regression Tests
```python
# Ensure quality doesn't degrade
MIN_QUALITY_SCORE = 7.0

def test_quality_regression():
    results = run_test_queries()
    avg_score = calculate_avg_quality(results)
    assert avg_score >= MIN_QUALITY_SCORE
```

---

## 📈 Monitoring in Production

### Metrics to Track

```python
# Log these metrics for each query
{
  "query": "...",
  "quality_score": 8.5,
  "has_enriched_products": true,
  "num_enriched": 2,
  "latency_ms": 1250,
  "plan_latency_ms": 350,
  "execution_latency_ms": 900,
  "user_feedback": null  # to be collected
}
```

### Dashboard (Grafana/Kibana)

**Quality Panel**:
- Avg quality score (7-day moving average)
- % queries with enriched products
- User satisfaction rating

**Performance Panel**:
- P50, P95, P99 latency
- Sonnet API call rate
- Ollama error rate

**Business Impact**:
- Conversion rate (if applicable)
- User engagement time
- Repeat query rate

---

## 🎓 Best Practices

### 1. Dictionary Maintenance
- ✅ Review and update monthly
- ✅ Prioritize top 20% most-queried products
- ✅ Use customer feedback to improve descriptions
- ❌ Don't over-enrich (quality > quantity)

### 2. Prompt Engineering
- ✅ Test multiple prompt variations
- ✅ Keep templates modular
- ✅ Version control prompts
- ❌ Don't hardcode product-specific logic in prompts

### 3. Performance Optimization
- ✅ Cache Sonnet planning results (similar queries)
- ✅ Batch dictionary lookups
- ✅ Use async operations
- ❌ Don't call Sonnet for every simple query (use fallback)

### 4. Cost Management
- ✅ Monitor Anthropic API usage
- ✅ Use simple planning for straightforward queries
- ✅ Cache frequent queries
- ❌ Don't use Sonnet for queries that can be rule-based

---

## 🔍 Troubleshooting

### Issue: Low Quality Scores

**Symptoms**: Quality score < 5/10

**Diagnosis**:
```bash
# Check if dictionary is loaded
python -c "
from app.services.two_stage_rag_service import ProductDictionary
d = ProductDictionary('data/product_dictionary.json')
print(f'Loaded {len(d.dictionary)} products')
"

# Check if products are enriched
# Look for "enriched" key in search results
```

**Solutions**:
1. Verify dictionary file path
2. Add more products to dictionary
3. Check prompt templates
4. Review Ollama model performance

### Issue: Sonnet Planning Failures

**Symptoms**: All queries use simple planning

**Diagnosis**:
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test Anthropic connection
python -c "
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model='claude-sonnet-4-5-20250929',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'test'}]
)
print('API OK')
"
```

**Solutions**:
1. Set ANTHROPIC_API_KEY environment variable
2. Check API quota/limits
3. Verify network connectivity
4. Review error logs

### Issue: Slow Response Times

**Symptoms**: Latency > 3 seconds

**Diagnosis**:
```python
# Add timing logs
import time

start = time.time()
plan = await service.plan_query(query)
print(f"Planning: {time.time() - start:.2f}s")

start = time.time()
products = await service.search_products(...)
print(f"Search: {time.time() - start:.2f}s")

start = time.time()
answer = await service.generate_answer(...)
print(f"Generation: {time.time() - start:.2f}s")
```

**Solutions**:
1. Cache planning results
2. Optimize Qdrant search (adjust top_k)
3. Use faster embedding model
4. Scale Ollama resources

---

## 📚 Additional Resources

- **Product Dictionary Schema**: See `data/product_dictionary.json`
- **API Documentation**: `docs/API_REFERENCE.md`
- **Prompt Templates**: In `two_stage_rag_service.py`
- **Test Results**: `qa_quality_comparison.json` (after running tests)

---

## ✅ Success Checklist

- [ ] Product dictionary created with 5+ products
- [ ] Two-stage RAG service implemented
- [ ] Test script runs successfully
- [ ] Quality improvement > 50% demonstrated
- [ ] API endpoint updated (optional)
- [ ] Monitoring dashboards configured (production)
- [ ] Documentation updated
- [ ] Team trained on new system

---

## 🚦 Next Steps

### Immediate (This Week)
1. Run `test_quality_improvement.py` and review results
2. Add 5-10 more products to dictionary
3. Test with real user queries

### Short-term (Next 2 Weeks)
1. Integrate with production API (A/B test)
2. Collect user feedback
3. Iterate on prompt templates

### Long-term (Next Month)
1. LLM-assisted dictionary generation for all products
2. Fine-tune Qwen model if needed
3. Implement user feedback loop
4. Consider vector search optimization

---

**Questions?** Check `docs/QUALITY_IMPROVEMENT_PLAN.md` for strategy details.
