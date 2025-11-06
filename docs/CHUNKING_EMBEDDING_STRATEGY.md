# 청킹 및 임베딩 전략 (Chunking & Embedding Strategy)

**작성일**: 2025-11-06
**버전**: 1.0.0
**목표**: 자연어 검색에 최적화된 계층적 제품 청킹 시스템

---

## 📊 1. 데이터 구조 분석

### 1.1 제품 카테고리

| 카테고리 | 데이터 소스 | 크기 | 주요 속성 |
|---------|------------|------|----------|
| **Bottle** | product_dictionary_with_accessories.json | 12,681 lines | 용량, 재질, 형태, 용도 |
| **Jar** | product_dictionary_with_accessories.json | (포함) | 용량, 재질, 형태, 용도 |
| **Cap** | cap_pump_product_list_complete.json | 3,708 lines | 직경, 타입, 가격 |
| **Pump** | cap_pump_product_list_complete.json | (포함) | 직경, 타입, 가격 |

### 1.2 현재 데이터 스키마

#### Bottle/Jar (용기)
```json
{
  "product_id": "idx_13",
  "product_code": "BE040-R001",
  "product_name": "40ml 브로우용기",
  "enriched_info": {
    "detailed_description": "...",
    "use_cases": ["고농축 에센스", "트래블 사이즈"],
    "target_customers": ["화장품 스타트업", "프리미엄 브랜드"],
    "material_benefits": {
      "material": "PE",
      "advantages": ["식품등급 안전성", "가벼운 무게"]
    },
    "capacity_info": {
      "capacity": "40ml",
      "usage_duration": "1-2주",
      "suitable_products": ["세럼", "에센스", "앰플"]
    },
    "specifications_explained": {
      "dimensions": "28x95(mm)",
      "diameter": "Ø20"
    },
    "keywords": ["소형", "휴대용", "트래블", "세럼"],
    "recommendations": {
      "when_to_use": "고가의 농축 제품",
      "alternatives_if_too_small": "50ml, 65ml 브로우용기"
    }
  },
  "spec": "28x95(mm)/Ø20"
}
```

#### Cap/Pump (부속품)
```json
{
  "vendor": "지에프테크",
  "description": "Ø24 펌프 211AVP",
  "product_code": "PO024-CG01",
  "spec": "24파이 일반펌프",
  "detail": "내경 Ø24",
  "package": "800ea",
  "supply_price": 140.0,
  "selling_price": 240.0
}
```

#### Pricing (가격)
```json
{
  "capacity_ml": 80,
  "material": "PE",
  "material_detail": "PE/PET",
  "regular_price": 160,
  "discount_price": 130
}
```

---

## 🎯 2. 계층적 청킹 전략

### 2.1 청킹 계층 구조

```
Level 0: Product Entity (제품 엔티티)
         ↓
Level 1: Category Chunk (카테고리 청크)
         ↓
Level 2: Specification Chunk (스펙 청크)
         ↓
Level 3: Feature Chunk (특성 청크)
         ↓
Level 4: Use Case Chunk (용도 청크)
```

### 2.2 카테고리별 청킹 매트릭스

#### 🍾 Bottle/Jar 청킹 전략

| 청크 타입 | 내용 | 임베딩 타겟 | 검색 시나리오 |
|----------|------|------------|-------------|
| **Primary Chunk** | 제품명 + 용량 + 재질 + 형태 | ✅ | "100ml PE 용기" |
| **Description Chunk** | 상세 설명 (detailed_description) | ✅ | "가벼운 화장품 용기" |
| **Use Case Chunk** | use_cases + suitable_products | ✅ | "에센스 담을 용기" |
| **Material Chunk** | material + advantages | ✅ | "안전한 재질 용기" |
| **Capacity Chunk** | capacity + usage_duration + positioning | ✅ | "1주일 쓸 용기" |
| **Dimension Chunk** | dimensions + diameter + meaning | ✅ | "슬림한 용기" |
| **Keyword Chunk** | keywords 배열 | ✅ | "휴대용", "트래블" |
| **Recommendation Chunk** | when_to_use + alternatives | ✅ | "고가 제품용 용기" |

**예시 청크 생성:**

```python
# Primary Chunk
"40ml PE 브로우용기 (슬림형 원형 Ø20)"

# Description Chunk
"40ml PE 브로우 용기는 소형 액상 화장품에 최적화된 경량 용기입니다. PE(폴리에틸렌) 재질의 안전성과 내구성을 바탕으로 에센스, 세럼 등 고가 화장품 포장에 적합합니다."

# Use Case Chunk
"고농축 에센스 및 세럼 포장, 트래블 사이즈 화장품, 샘플 키트 구성용, 1-2주 사용량 제품에 적합. 세럼, 에센스, 앰플, 오일 제품에 사용 가능."

# Material Chunk
"PE(폴리에틸렌) 재질: 식품등급 안전성, 가벼운 무게로 휴대 편리, 내충격성 우수로 파손 방지, 화학적 안정성, 재활용 가능"

# Capacity Chunk
"40ml 용량 (소형/휴대용 사이즈): 하루 2ml 기준 1-2주 사용량, 세럼/에센스/앰플/오일 제품에 적합"

# Dimension Chunk
"크기 28x95(mm), 직경 Ø20: 손에 쏙 들어오는 슬림형 디자인, 파우치에 넣기 좋은 크기"

# Keyword Chunk
"소형, 휴대용, 트래블, 샘플, 에센스용, 세럼, 슬림, 파우치"

# Recommendation Chunk
"추천: 고가의 농축 제품, 트래블 제품, 테스터 제작 시. 비추천: 대용량 제품, 저가 제품, 바디용 제품. 더 작은 용기: 30ml, 더 큰 용기: 50ml, 65ml 브로우용기"
```

#### 🔘 Cap/Pump 청킹 전략

| 청크 타입 | 내용 | 임베딩 타겟 | 검색 시나리오 |
|----------|------|------------|-------------|
| **Primary Chunk** | description + spec + detail | ✅ | "24파이 펌프" |
| **Specification Chunk** | 직경 + 타입 | ✅ | "28파이 일반펌프" |
| **Pricing Chunk** | vendor + price + package | ✅ | "저렴한 펌프" |
| **Compatibility Chunk** | 호환 용기 정보 (추론) | ✅ | "100ml 용기에 맞는 펌프" |

**예시 청크 생성:**

```python
# Primary Chunk
"Ø24 펌프 211AVP (24파이 일반펌프, 내경 Ø24)"

# Specification Chunk
"24파이(Ø24) 일반펌프, 내경 Ø24mm, GF-211A 모델"

# Pricing Chunk
"지에프테크 제조, 800ea 패키지, 공급가 140원, 판매가 240원"

# Compatibility Chunk
"직경 Ø24 펌프: 24mm 입구를 가진 용기와 호환 (일반적으로 30-80ml 소형 용기)"
```

---

## 🔍 3. 메타데이터 구조 설계

### 3.1 통합 메타데이터 스키마

모든 청크는 다음 메타데이터를 포함:

```python
{
  # 기본 정보
  "product_id": "idx_13",
  "product_code": "BE040-R001",
  "product_name": "40ml 브로우용기",
  "chunk_id": "idx_13_primary",
  "chunk_type": "primary",  # primary, description, use_case, etc.

  # 카테고리 필터
  "category": "bottle",  # bottle, jar, cap, pump
  "sub_category": "blow_bottle",  # blow_bottle, round_jar, cream_jar, pump, cap

  # 수치 필터 (Bottle/Jar)
  "capacity_ml": 40,
  "capacity_range": "small",  # tiny(<30), small(30-100), medium(100-300), large(>300)
  "diameter_mm": 20,

  # 재질 필터 (Bottle/Jar)
  "material": "PE",  # PE, PET, PETG, PP, Glass, Multi-layer
  "material_grade": "premium",  # standard, premium, food_grade

  # 형태 필터
  "shape": "round",  # round, oval, square, rectangle
  "design": "slim",  # slim, wide, tall, short

  # 용도 필터
  "use_cases": ["serum", "essence", "ampoule", "oil"],
  "target_products": ["high_concentration", "travel_size", "sample"],

  # 고객 타입 필터
  "target_customers": ["startup", "premium_brand", "sample_maker"],

  # 키워드
  "keywords": ["small", "portable", "travel", "sample", "serum", "slim"],

  # 직경 필터 (Cap/Pump)
  "pump_diameter_mm": 24,  # 24, 28, 32
  "pump_type": "regular_pump",  # regular_pump, dispenser, cap

  # 가격 필터
  "price_range": "budget",  # budget, standard, premium
  "supply_price": 140.0,
  "selling_price": 240.0,

  # 추천/대안
  "recommended_for": ["concentrated_products", "travel_products"],
  "alternatives": ["50ml", "65ml"],

  # 검색 최적화
  "search_priority": 1.0,  # 0.0-1.0 (primary chunks = 1.0)
  "semantic_cluster": "small_portable_container"
}
```

### 3.2 필터 가능한 속성 (Qdrant Payload Indexing)

#### 인덱싱 필요 필드

```python
# Categorical Filters (Exact Match)
- category (keyword)
- sub_category (keyword)
- material (keyword)
- shape (keyword)
- use_cases (keyword array)

# Numerical Range Filters
- capacity_ml (integer, range)
- diameter_mm (integer, range)
- pump_diameter_mm (integer, range)
- supply_price (float, range)
- selling_price (float, range)

# Text Search Fields
- keywords (keyword array, full-text)
- product_name (text, tokenized)
```

---

## 🧠 4. 자연어 → 구조화 쿼리 변환

### 4.1 쿼리 파싱 전략

#### 단계 1: 엔티티 추출

```python
USER_QUERY = "100ml 정도 되는 가벼운 에센스 용기 찾아줘"

# Entity Extraction
{
  "capacity": {
    "value": 100,
    "unit": "ml",
    "flexibility": "approximate"  # exact, approximate, range
  },
  "attributes": ["가벼운"],
  "use_case": "에센스",
  "product_type": "용기"
}
```

#### 단계 2: 필터 생성

```python
# Qdrant Filter
{
  "must": [
    {"key": "category", "match": {"value": "bottle"}},
    {"key": "capacity_ml", "range": {"gte": 80, "lte": 120}},  # ±20ml
    {"key": "use_cases", "match": {"any": ["serum", "essence"]}}
  ],
  "should": [
    {"key": "keywords", "match": {"any": ["light", "lightweight", "portable"]}},
    {"key": "material", "match": {"value": "PE"}}  # PE = 가볍다
  ]
}
```

#### 단계 3: 검색 쿼리 생성

```python
# Semantic Search Query (Embedding)
search_query = "100ml 가벼운 에센스용 용기"

# Boost Priority
- Primary chunks: 1.0
- Use case chunks: 0.9
- Material chunks: 0.8
- Others: 0.7
```

### 4.2 쿼리 패턴 매트릭스

| 사용자 쿼리 | 추출된 엔티티 | 메타데이터 필터 | 검색 쿼리 |
|-----------|-------------|---------------|----------|
| "100ml 에센스 용기" | capacity=100ml, use_case=에센스 | capacity_ml: 80-120, use_cases: serum | "100ml 에센스용 용기" |
| "휴대하기 좋은 작은 용기" | attributes=휴대, size=small | capacity_range: small, keywords: portable | "휴대용 소형 용기" |
| "24파이 펌프" | diameter=24, type=pump | pump_diameter_mm: 24, category: pump | "24파이 펌프" |
| "저렴한 PET 용기" | material=PET, price=low | material: PET, price_range: budget | "저렴한 PET 플라스틱 용기" |
| "세럼 담을 용기" | use_case=세럼 | use_cases: serum | "세럼 화장품 용기" |
| "트래블 사이즈" | attributes=travel | keywords: travel, capacity_range: small | "트래블 여행용 휴대 용기" |

---

## 🔧 5. 임베딩 파이프라인 설계

### 5.1 단계별 프로세스

```
Step 1: 원본 데이터 로드
        ↓
Step 2: 카테고리 분류 (Bottle/Jar/Cap/Pump)
        ↓
Step 3: 청크 생성 (계층별 8개 청크 타입)
        ↓
Step 4: 메타데이터 추출 및 구조화
        ↓
Step 5: 텍스트 임베딩 (sentence-transformers)
        ↓
Step 6: Qdrant 업로드 (vectors + payloads)
        ↓
Step 7: 인덱스 최적화 (payload indexing)
```

### 5.2 청크 생성 로직 (Pseudo-code)

```python
def generate_chunks(product: dict, category: str) -> List[Chunk]:
    chunks = []

    if category in ["bottle", "jar"]:
        # Primary Chunk
        chunks.append(Chunk(
            type="primary",
            text=f"{product['capacity']} {product['material']} {product['product_name']}",
            metadata={...},
            priority=1.0
        ))

        # Description Chunk
        chunks.append(Chunk(
            type="description",
            text=product['enriched_info']['detailed_description'],
            metadata={...},
            priority=0.9
        ))

        # Use Case Chunk
        use_cases_text = ", ".join(product['enriched_info']['use_cases'])
        suitable_products = ", ".join(product['enriched_info']['capacity_info']['suitable_products'])
        chunks.append(Chunk(
            type="use_case",
            text=f"{use_cases_text}에 적합. {suitable_products} 제품에 사용 가능.",
            metadata={...},
            priority=0.9
        ))

        # Material Chunk
        material_info = product['enriched_info']['material_benefits']
        advantages = ", ".join(material_info['advantages'])
        chunks.append(Chunk(
            type="material",
            text=f"{material_info['material']} 재질: {advantages}",
            metadata={...},
            priority=0.8
        ))

        # ... (나머지 청크들)

    elif category in ["cap", "pump"]:
        # Cap/Pump Chunks
        chunks.append(Chunk(
            type="primary",
            text=f"{product['description']} ({product['spec']}, {product['detail']})",
            metadata={...},
            priority=1.0
        ))

        # ... (나머지 청크들)

    return chunks
```

### 5.3 임베딩 모델 설정

```python
# Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Fine-tuning Options (선택)
# - Domain-specific training on packaging vocabulary
# - Korean language optimization
# - Multi-lingual support (Korean + English)

# Vector Configuration
{
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  },
  "payload_schema": {
    "category": {"type": "keyword"},
    "capacity_ml": {"type": "integer", "indexed": True},
    "material": {"type": "keyword", "indexed": True},
    "keywords": {"type": "keyword[]", "indexed": True}
  }
}
```

---

## 📈 6. 검색 품질 최적화

### 6.1 하이브리드 검색 전략

```python
def hybrid_search(query: str, filters: dict, top_k: int = 10):
    # Step 1: Entity Extraction
    entities = extract_entities(query)

    # Step 2: Generate Metadata Filters
    metadata_filters = build_filters(entities)

    # Step 3: Semantic Search
    query_embedding = embed(query)
    semantic_results = qdrant.search(
        query_vector=query_embedding,
        filter=metadata_filters,
        limit=top_k * 2,  # Over-fetch
        score_threshold=0.5
    )

    # Step 4: Re-ranking
    # - Boost by chunk_type priority
    # - Boost by exact keyword matches
    # - Boost by capacity/diameter proximity
    ranked_results = rerank(semantic_results, entities)

    # Step 5: Deduplication
    # - Group by product_id
    # - Keep highest scoring chunk per product
    final_results = deduplicate(ranked_results, top_k)

    return final_results
```

### 6.2 Re-ranking 로직

```python
def calculate_final_score(
    semantic_score: float,
    chunk_priority: float,
    keyword_match_count: int,
    capacity_proximity: float
) -> float:
    return (
        semantic_score * 0.5 +           # 50%: Semantic similarity
        chunk_priority * 0.2 +           # 20%: Chunk type priority
        (keyword_match_count / 10) * 0.2 +  # 20%: Keyword matches
        capacity_proximity * 0.1         # 10%: Numerical proximity
    )
```

---

## 🎯 7. 구현 로드맵

### Phase 1: 데이터 준비 (1-2일)
- [ ] 제품 카테고리 자동 분류 (Bottle/Jar/Cap/Pump)
- [ ] 메타데이터 추출 및 정규화
- [ ] 누락된 필드 추론 (capacity, material 등)

### Phase 2: 청킹 파이프라인 (2-3일)
- [ ] 카테고리별 청크 생성 함수 구현
- [ ] 메타데이터 스키마 구조화
- [ ] 청크 검증 및 품질 체크

### Phase 3: 임베딩 & 인덱싱 (1일)
- [ ] sentence-transformers 임베딩 생성
- [ ] Qdrant collection 생성 (payload indexing)
- [ ] 벡터 업로드 및 검증

### Phase 4: 쿼리 파싱 (2-3일)
- [ ] 자연어 → 엔티티 추출 (용량, 재질, 용도 등)
- [ ] 엔티티 → 메타데이터 필터 변환
- [ ] 쿼리 확장 및 동의어 처리

### Phase 5: 검색 최적화 (2일)
- [ ] 하이브리드 검색 구현
- [ ] Re-ranking 로직
- [ ] A/B 테스트 및 튜닝

### Phase 6: 평가 & 개선 (1-2일)
- [ ] 검색 품질 평가 (Precision@K, Recall@K)
- [ ] 사용자 피드백 수집
- [ ] 지속적 개선

---

## 📊 8. 예상 성능 지표

### 8.1 데이터 볼륨

| 항목 | 원본 제품 수 | 청크 수 (x8) | 벡터 크기 | 총 크기 |
|------|------------|-------------|----------|---------|
| Bottles/Jars | ~200 | ~1,600 | 384 dim | ~2.4MB |
| Caps/Pumps | ~50 | ~200 | 384 dim | ~0.3MB |
| **Total** | **~250** | **~1,800** | **384 dim** | **~2.7MB** |

### 8.2 검색 성능 목표

- **Latency**: < 100ms (p95)
- **Precision@5**: > 85%
- **Recall@10**: > 90%
- **User Satisfaction**: > 4.0/5.0

---

## 🔄 9. 유지보수 & 확장

### 9.1 신규 제품 추가 프로세스

```bash
# 1. 신규 제품 데이터 추가
python scripts/add_new_products.py --input new_products.json

# 2. 자동 청킹 & 임베딩
python scripts/process_new_embeddings.py --products new_products.json

# 3. Qdrant 증분 업데이트
python scripts/update_qdrant.py --collection products --mode incremental
```

### 9.2 검색 품질 모니터링

```python
# 주간 품질 리포트
python scripts/generate_search_quality_report.py --period weekly

# Output:
# - Top 10 failed queries (no results)
# - Low-scoring queries (< 0.5)
# - User feedback trends
# - Suggested improvements
```

---

## 📚 10. 참고 자료

### 관련 문서
- `docs/RAG_ACTIVATION_STRATEGY.md` - RAG 활성화 전략
- `docs/ARCHITECTURE.md` - 시스템 아키텍처
- `data/processed/products/metadata/` - 원본 제품 데이터

### 외부 참조
- [Qdrant Filtering](https://qdrant.tech/documentation/concepts/filtering/)
- [Sentence Transformers](https://www.sbert.net/)
- [Hybrid Search Strategies](https://www.pinecone.io/learn/hybrid-search/)

---

**Status**: 설계 완료 ✅
**Next**: Phase 1 구현 시작 → 데이터 준비 및 카테고리 분류

**v1.0.0** | **2025-11-06**
