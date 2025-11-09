# Query Analysis Examples

## Example 1: Simple Query

**Input**: "50ml 용기"

**Analysis**:
```json
{
  "complexity": 0.2,
  "tokens": 2,
  "entities": ["capacity: 50ml"],
  "has_reasoning": false,
  "routing": {
    "engine": "NexaAI",
    "model": "Qwen3-1.7B",
    "reason": "simple_query_fast_inference",
    "expected_time": "< 500ms"
  }
}
```

**Optimization Suggestions**:
1. Add material filter for precision
2. Consider related queries: "50ml PET", "50ml PP"

---

## Example 2: Complex Reasoning Query

**Input**: "100ml 투명 PET 용기와 PP 용기의 재질 특성, 내구성, 가격을 비교 분석하고 각각의 장단점을 상세히 설명해주세요"

**Analysis**:
```json
{
  "complexity": 0.85,
  "tokens": 16,
  "entities": [
    "capacity: 100ml",
    "material: PET",
    "material: PP"
  ],
  "has_reasoning": true,
  "routing": {
    "engine": "Ollama",
    "model": "qwen2.5:7b-instruct",
    "reason": "complex_reasoning_required",
    "expected_time": "~2s"
  }
}
```

**Search Filters Applied**:
```python
{
  "capacity": "100ml",
  "material": {"$in": ["PET", "PP"]},
  "transparency": "투명"
}
```

---

## Example 3: Router Tuning

**Command**: `tune-routing`

**Output**:
```
✓ Routing Analysis (last 100 queries):

Current Configuration:
  • Simple threshold: 0.30
  • Complex threshold: 0.70

Query Distribution:
  • Simple (< 0.3): 45 queries → NexaAI (420ms avg)
  • Medium (0.3-0.7): 30 queries → NexaAI (850ms avg)
  • Complex (> 0.7): 25 queries → Ollama (1.8s avg)

Performance Metrics:
  • Overall avg latency: 750ms
  • Error rate: 0.5%
  • Cache hit rate: 35%

Recommendations:
  ✓ Current thresholds are optimal
  • 75% queries use fast model (good balance)
  • No adjustment needed
```
