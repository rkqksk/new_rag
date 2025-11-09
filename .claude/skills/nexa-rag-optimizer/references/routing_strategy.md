# Routing Strategy Reference

## Complexity Scoring Algorithm

```python
score = (
    0.2 * min(token_count / 100, 1.0) +      # 20% - Query length
    0.3 * min(entity_count / 10, 1.0) +      # 30% - Entity richness
    0.3 * (1.0 if has_reasoning else 0.0) +  # 30% - Reasoning keywords
    0.2 * (1.0 if has_multimodal else 0.0)   # 20% - Multimodal needs
)
```

## Routing Thresholds

| Score Range | Engine | Model | Use Case |
|-------------|--------|-------|----------|
| < 0.3 | NexaAI | Qwen3-1.7B | Simple lookup, fast response |
| 0.3 - 0.7 | NexaAI | Qwen3-VL-4B | Medium complexity, balanced |
| ≥ 0.7 | Ollama | qwen2.5:7b | Complex reasoning, high quality |

## Entity Patterns

- **Capacity**: `\d+\s*(ml|ML|L|리터|밀리리터)`
- **Neck**: `\d+\s*(파이|Φ|ø|phi)`
- **Material**: `\b(PP|PE|PET|PETG|PS|HDPE|LDPE)\b`
- **MOQ**: `\d+\s*(개|ea|pcs|개입)`
- **Price**: `\d+\s*(원|won|₩)`

## Reasoning Keywords

Korean: 왜, 어떻게, 무엇, 비교, 분석, 설명, 차이
English: why, how, what, compare, analyze, explain, difference
