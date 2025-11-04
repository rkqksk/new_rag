# Product Recommendation Quality Improvement Plan

## 🎯 Goal
Improve LLM answer quality by enriching product context with detailed descriptions, use cases, and recommendation scenarios.

## 📋 Strategy: Dictionary-Based Enrichment

### Why Dictionary Over Fine-tuning?

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Dictionary** | ✅ Fast implementation<br>✅ Easy updates<br>✅ No training costs<br>✅ Explainable | ⚠️ Manual effort | **✅ Recommended** |
| **Fine-tuning/LORA** | ✅ Adaptive learning | ❌ High cost<br>❌ Training complexity<br>❌ Requires labeled data<br>❌ Hard to update | ❌ Overkill for current scale |

**Decision**: Start with Dictionary approach, consider fine-tuning later if needed.

---

## 🔧 Implementation Plan

### Phase 1: Product Dictionary Creation

#### 1.1 Dictionary Schema
```python
{
  "product_id": "idx_13",
  "product_code": "BE040-R001",
  "enriched_info": {
    "detailed_description": "40ml PE 브로우 용기는 화장품 액상 제품에 최적화된 소형 용기입니다.",
    "use_cases": [
      "에센스, 세럼, 앰플 등 고농축 화장품",
      "트래블 사이즈 제품",
      "샘플 키트 구성용"
    ],
    "target_customers": [
      "화장품 스타트업",
      "샘플 제작 업체",
      "여행용 제품 제조사"
    ],
    "material_benefits": {
      "PE": "안전성 높음, 가벼움, 내충격성 우수"
    },
    "capacity_recommendations": {
      "40ml": "트래블 사이즈, 1-2주 사용량",
      "적합_제품": ["세럼", "에센스", "앰플"]
    },
    "related_products": ["50ml 브로우용기", "30ml 브로우용기"],
    "keywords": ["소형", "휴대용", "트래블", "샘플", "에센스용"]
  }
}
```

#### 1.2 Dictionary Population Methods

**Option A: Manual Creation (Initial 10-20 products)**
- Create template-based enrichment
- Focus on most popular products
- Quick validation

**Option B: LLM-Assisted Generation**
- Use Sonnet 4.5 to generate descriptions
- Human review and refinement
- Scale to all products

**Recommended**: Start with Option A (10 products) → Validate → Scale with Option B

---

### Phase 2: RAG System Enhancement

#### 2.1 Embedding Improvements
```python
# Current: product_name + specifications
full_text = f"{product_name} {spec_text}"

# Enhanced: + enriched descriptions
full_text = f"""
{product_name}
{spec_text}
용도: {use_cases}
추천 고객: {target_customers}
특징: {detailed_description}
"""
```

#### 2.2 Prompt Engineering
```python
# Current prompt: Simple product list
# Enhanced prompt: Rich context + usage scenarios

enhanced_prompt = f"""
당신은 제조업 제품 전문가입니다.

[제품 상세 정보]
{detailed_context}

[사용 시나리오]
- 용도: {use_cases}
- 추천 고객: {target_customers}
- 재질 장점: {material_benefits}

[사용자 질문]
{question}

[답변 규칙]
1. 제품 특징을 구체적으로 설명
2. 사용 시나리오를 포함하여 추천
3. 재질/사양의 장점 강조
4. 대체 제품 제안 가능
"""
```

#### 2.3 Response Quality Metrics
```python
{
  "has_product_code": bool,
  "has_specifications": bool,
  "has_use_case": bool,
  "has_material_info": bool,
  "description_length": int,
  "confidence_score": float
}
```

---

### Phase 3: Sonnet 4.5 + Haiku 4.5 Pattern

#### Architecture
```
┌─────────────────────────────────────────────┐
│ User Query: "50ml 용기 추천해줘"            │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Planning (Sonnet 4.5)              │
│ - Analyze query intent                      │
│ - Extract capacity, material, use case     │
│ - Generate search strategy                  │
│ - Create enriched prompt template          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Step 2: Execution (Haiku 4.5)              │
│ - Vector search with filters               │
│ - Load enriched product info               │
│ - Generate recommendation                   │
│ - Format response                           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Response: Detailed recommendation with      │
│ product specs, use cases, and alternatives  │
└─────────────────────────────────────────────┘
```

#### Implementation
```python
class TwoStageRAGService:
    def __init__(self):
        self.planner = ClaudeHaikuServer()  # Sonnet for planning
        self.executor = LocalLLM()  # Haiku for execution

    async def answer_question(self, query: str):
        # Stage 1: Planning with Sonnet
        plan = await self.planner.call_haiku(
            prompt=f"Analyze query and create search plan: {query}",
            model="claude-sonnet-4.5",
            temperature=0.3
        )

        # Stage 2: Execute with Haiku
        products = await self.search_products(
            query=query,
            filters=plan["filters"],
            top_k=plan["top_k"]
        )

        # Enrich with dictionary
        enriched_products = self.enrich_with_dictionary(products)

        # Generate answer
        answer = await self.executor.generate(
            prompt=plan["answer_template"],
            context=enriched_products
        )

        return answer
```

---

## 📊 Quality Improvement Metrics

### Before (Current State)
```json
{
  "query": "50ml 용기 추천해줘",
  "response": "50ml 브로우용기를 추천합니다. (BE050-R001)",
  "quality_score": 3/10,
  "issues": [
    "No use case explanation",
    "No material benefits",
    "No customer targeting",
    "Generic recommendation"
  ]
}
```

### After (Enhanced)
```json
{
  "query": "50ml 용기 추천해줘",
  "response": """
  50ml PE 브로우용기 (BE050-R001)를 추천드립니다.

  **추천 이유**:
  - 용량: 에센스/세럼용 최적 사이즈 (3-4주 사용량)
  - 재질: PE 소재로 안전하고 가벼움
  - 용도: 고농축 화장품, 트래블 제품에 적합

  **적합 고객**:
  - 화장품 스타트업 (소량 생산)
  - 프리미엄 세럼 제조사
  - 트래블 키트 제작 업체

  **대체 제품**: 60ml, 40ml 브로우용기도 검토해보세요.
  """,
  "quality_score": 9/10,
  "improvements": [
    "✅ Detailed use cases",
    "✅ Material benefits explained",
    "✅ Customer targeting",
    "✅ Alternative suggestions"
  ]
}
```

---

## 🚀 Action Items

### Immediate (Week 1)
- [ ] Create product dictionary schema
- [ ] Manually enrich 10 representative products
- [ ] Implement dictionary loader in RAG service
- [ ] Update embedding pipeline to include enriched data

### Short-term (Week 2-3)
- [ ] Integrate Claude Haiku Server for Sonnet planning
- [ ] Implement two-stage RAG pattern
- [ ] Create enriched prompt templates
- [ ] Test with 20+ queries and measure quality

### Long-term (Month 2+)
- [ ] LLM-assisted dictionary generation for all products
- [ ] A/B testing of different prompt strategies
- [ ] User feedback collection system
- [ ] Consider fine-tuning if needed

---

## 📁 Additional Data Requirements

### Need to Collect/Create:
1. **Product Usage Scenarios**: For each product category
2. **Customer Personas**: Who buys what and why
3. **Material Knowledge Base**: Benefits of PE/PET/PP/Glass
4. **Capacity Guidelines**: Typical use durations per capacity
5. **Industry Terminology**: Common terms in cosmetics manufacturing

### Data Sources:
- Existing customer inquiries
- Industry standards
- Competitor analysis
- Material supplier specs
- Domain expert input

---

## ✅ Success Criteria

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Response Completeness** | 40% | 90% | Has specs + use case + material info |
| **User Satisfaction** | 3.5/5 | 4.5/5 | User feedback survey |
| **Answer Length** | 50 chars | 200-300 chars | Token count |
| **Recommendation Accuracy** | 60% | 85% | Expert validation |
| **Context Richness** | Low | High | # of context elements included |

---

## 🎓 Lessons Learned (To Be Updated)

- Dictionary approach effectiveness
- Optimal enrichment depth
- Sonnet vs Haiku performance comparison
- User preference patterns

