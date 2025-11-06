# Atomic Field-Level Chunking 구현 완료

**작성일**: 2025-11-06
**버전**: 1.0.0
**상태**: ✅ 구현 완료

---

## 📋 요약

제품 데이터를 **원자 단위(Atomic Level)**로 분할하여 세밀한 자연어 검색을 지원하는 청킹 시스템 구현 완료.

### 핵심 성과
- ✅ **Atomic Field-Level Chunking**: 각 필드를 독립적인 청크로 분리
- ✅ **Category-Specific Templates**: Bottle/Jar/Cap/Pump 카테고리별 최적화된 템플릿
- ✅ **Multiple Variants**: 필드당 2-3개 표현 버전 생성 (검색 커버리지 극대화)
- ✅ **Extensible Template System**: 신규 필드/카테고리 추가 용이

### 성능 지표
- **평균 14.7개 Atomic Chunks/제품**
- **20+ Field Types** 지원
- **4개 카테고리** (Bottle, Jar, Cap, Pump)
- **우선순위 시스템** (Priority 0.6-1.0)

---

## 🏗️ 구현 아키텍처

### 모듈 구조

```
src/core/
├── product_classifier.py          # 제품 분류기 (Bottle/Jar/Cap/Pump)
├── chunk_templates.py              # 기본 템플릿 + 필드 추출기
├── category_templates.py           # 카테고리별 템플릿
└── advanced_chunk_generator.py    # 통합 파이프라인
```

### 파이프라인 흐름

```
입력 제품 데이터
    ↓
[1] ProductClassifier → 카테고리 분류
    ↓
[2] FieldExtractor → 필드 추출 + 조합 필드 생성
    ↓
[3] CategoryTemplateRegistry → 카테고리별 템플릿 적용
    ↓
[4] AdvancedChunkGenerator → Atomic Chunks 생성
    ↓
출력: List[AtomicChunk]
```

---

## 🎨 구현 상세

### 1. Product Classifier (제품 분류기)

**파일**: `src/core/product_classifier.py`

#### 기능
- 제품명 + 메타데이터 기반 자동 분류
- Main Category: Bottle, Jar, Cap, Pump
- Sub Category: 8가지 (BlowBottle, CreamJar, ScrewCap, RegularPump 등)
- Confidence Score (0.0-1.0)

#### 예시
```python
classifier = ProductClassifier()

result = classifier.classify({
    "product_name": "GY-20-뾰족캡B",
    "neck": "Ø20",
    "material": "PP"
})

# Output:
# category: CAP
# sub_category: SCREW_CAP
# confidence: 0.85
# reasoning: "cap keywords matched"
```

---

### 2. Field Extractor (필드 추출기)

**파일**: `src/core/chunk_templates.py`

#### 지원 필드 (20+ types)

| 필드 그룹 | 필드 타입 | 예시 |
|----------|----------|------|
| **Identity** | PRODUCT_NAME, PRODUCT_CODE | "GY-20-뾰족캡B", "GY-20" |
| **Specifications** | CAPACITY, SIZE, NECK, DIAMETER, DIMENSIONS | "40ml", "Ø23.8 × 51.5", "Ø20" |
| **Materials** | MATERIAL, ORIGIN, MANUFACTURER | "PP", "한국", "금양실업" |
| **Business** | MOQ, PRICE, SUPPLY_PRICE, SELLING_PRICE, PACKAGE | "5,000", "140원", "800ea" |
| **Contact** | PHONE, FAX, EMAIL, MANAGER | "032-671-7630", "toritoya@naver.com" |
| **Use Cases** | USE_CASE, TARGET_PRODUCT | ["에센스", "세럼"] |
| **Descriptions** | DESCRIPTION, KEYWORD | "40ml PE 브로우...", ["소형", "휴대용"] |
| **Composite** | SPEC_COMPOSITE, BUSINESS_COMPOSITE | "Neck Ø20, 사이즈...", "MOQ 5,000개..." |

#### Composite Fields (조합 필드)

복수 필드를 조합하여 복잡한 검색 쿼리 대응:

```python
# SPEC_COMPOSITE
"Neck Ø20, 사이즈 Ø23.8 × 51.5, 직경 Ø20"

# BUSINESS_COMPOSITE
"MOQ 5,000개, PP 재질, 공급가 140원"

# 검색 예시:
# "20파이에 23.8 사이즈" → SPEC_COMPOSITE 매칭
# "PP 재질 MOQ 5000" → BUSINESS_COMPOSITE 매칭
```

---

### 3. Category Templates (카테고리별 템플릿)

**파일**: `src/core/category_templates.py`

#### 같은 필드, 다른 표현

| Field | Bottle | Jar | Cap | Pump |
|-------|--------|-----|-----|------|
| **CAPACITY** | "40ml 용량 **보틀**" | "50g 용량 **크림 자**" | - | - |
| **NECK** | "Neck Ø24 보틀 **(캡 호환)**" | - | "Neck Ø20 **호환 캡**" | "Ø24 **병에 맞는 펌프**" |
| **MATERIAL** | "PET 재질 **보틀**" | "PP 재질 **크림 자**" | "PP 재질 **캡**" | "PP 재질 **펌프**" |
| **USE_CASE** | "화장수 **담는 보틀**" | "크림 **담는 크림 자**" | - | - |

#### 템플릿 구조

```python
ChunkTemplate(
    field_type=FieldType.NECK,
    template="Neck {field} 호환 캡",
    priority=0.98,
    search_keywords=["neck", "넥", "호환", "맞는", "파이"]
)
```

#### Multiple Variants (다중 버전)

각 필드마다 2-3개의 표현 버전 생성:

```python
# NECK 필드 (Cap 카테고리)
[
    "Neck Ø20 호환 캡",           # Priority: 0.98
    "Ø20 병에 맞는 캡",           # Priority: 0.95
    "Ø20 입구용 뚜껑"             # Priority: 0.9
]

# 검색 커버리지:
# "20파이 호환" → 1번 매칭
# "20파이 병에 맞는" → 2번 매칭
# "20파이 입구용" → 3번 매칭
```

---

### 4. Advanced Chunk Generator (통합 파이프라인)

**파일**: `src/core/advanced_chunk_generator.py`

#### AtomicChunk 데이터 클래스

```python
@dataclass
class AtomicChunk:
    chunk_id: str                  # "GY-20_neck"
    field_type: FieldType          # FieldType.NECK
    text: str                      # "Neck Ø20 호환 캡"
    priority: float                # 0.98
    metadata: Dict                 # {category, product_id, ...}
    search_keywords: List[str]     # ["neck", "넥", "호환"]
```

#### 생성 로직

```python
generator = AdvancedChunkGenerator()
chunks = generator.generate_chunks(product_data)

# 내부 단계:
# 1. 제품 분류 (Classifier)
# 2. 필드 추출 (Extractor)
# 3. 카테고리별 템플릿 적용 (TemplateRegistry)
# 4. Atomic Chunks 생성
```

---

## 📊 실제 결과 예시

### 예시 1: GY-20-뾰족캡B (Cap)

**입력 데이터**:
```json
{
  "product_name": "GY-20-뾰족캡B",
  "product_code": "GY-20",
  "size": "Ø23.8 × 51.5",
  "neck": "Ø20",
  "moq": "5,000",
  "material": "PP",
  "origin": "한국",
  "manufacturer": "금양실업",
  "phone": "032-671-7630",
  "email": "toritoya@naver.com"
}
```

**출력 청크 (18개)**:

| Chunk ID | Field Type | Text | Priority |
|----------|------------|------|----------|
| GY-20_product_name | PRODUCT_NAME | "GY-20-뾰족캡B 캡" | 1.0 |
| GY-20_product_name_v2 | PRODUCT_NAME | "GY-20-뾰족캡B 뚜껑" | 0.95 |
| GY-20_product_code | PRODUCT_CODE | "GY-20" | 0.7 |
| GY-20_size | SIZE | "사이즈 Ø23.8 × 51.5 캡" | 0.9 |
| GY-20_size_v2 | SIZE | "Ø23.8 × 51.5 규격 뚜껑" | 0.85 |
| **GY-20_neck** | **NECK** | **"Neck Ø20 호환 캡"** | **0.98** |
| GY-20_neck_v2 | NECK | "Ø20 병에 맞는 캡" | 0.95 |
| GY-20_neck_v3 | NECK | "Ø20 입구용 뚜껑" | 0.9 |
| GY-20_material | MATERIAL | "PP 재질 캡" | 0.95 |
| GY-20_material_v2 | MATERIAL | "PP 플라스틱 뚜껑" | 0.9 |
| GY-20_origin | ORIGIN | "한국" | 0.7 |
| GY-20_manufacturer | MANUFACTURER | "금양실업 제조 캡" | 0.95 |
| **GY-20_moq** | **MOQ** | **"최소주문수량 5,000개 (캡)"** | **0.95** |
| GY-20_moq_v2 | MOQ | "5,000개부터 주문 가능한 캡" | 0.9 |
| GY-20_phone | PHONE | "032-671-7630" | 0.7 |
| GY-20_email | EMAIL | "toritoya@naver.com" | 0.7 |
| GY-20_spec_composite | SPEC_COMPOSITE | "Neck Ø20, 사이즈 Ø23.8 × 51.5" | 0.7 |
| GY-20_business_composite | BUSINESS_COMPOSITE | "MOQ 5,000개, PP 재질" | 0.7 |

### 예시 2: 40ml 브로우용기 (Bottle)

**입력 데이터**:
```json
{
  "product_id": "idx_13",
  "product_code": "BE040-R001",
  "product_name": "40ml 브로우용기",
  "enriched_info": {
    "detailed_description": "40ml PE 브로우 용기는...",
    "use_cases": ["고농축 에센스", "트래블 사이즈"],
    "material_benefits": {"material": "PE"},
    "capacity_info": {
      "capacity": "40ml",
      "suitable_products": ["세럼", "에센스"]
    },
    "keywords": ["소형", "휴대용", "트래블"]
  }
}
```

**출력 청크 (18개)** - 주요만 표시:

| Field Type | Text | Priority |
|------------|------|----------|
| PRODUCT_NAME | "40ml 브로우용기 **보틀**" | 1.0 |
| **CAPACITY** | **"40ml 용량 보틀"** | **0.95** |
| CAPACITY_v2 | "40ml **병**" | 0.9 |
| **USE_CASE** | **"고농축 에센스, 트래블 사이즈 담는 보틀"** | **0.95** |
| USE_CASE_v2 | "고농축 에센스, 트래블 사이즈 **포장용 병**" | 0.9 |
| MATERIAL | "PE 재질 보틀" | 0.95 |
| TARGET_PRODUCT | "세럼, 에센스 **담을 수 있는 보틀**" | 0.9 |
| KEYWORD | "소형, 휴대용, 트래블" | 0.7 |

---

## 🔍 자연어 검색 시나리오

### 시나리오 1: "20파이 캡 찾아줘"

**매칭 청크**:
```
✅ GY-20_neck: "Neck Ø20 호환 캡" (Priority: 0.98)
   Keywords: ["neck", "넥", "호환", "맞는", "파이"]

✅ GY-20_neck_v2: "Ø20 병에 맞는 캡" (Priority: 0.95)
   Keywords: ["호환", "맞다", "병"]
```

**검색 프로세스**:
1. "20파이" → "Ø20" 정규화
2. "캡" → category: CAP 필터
3. Semantic search: "20파이 캡"
4. Result: GY-20-뾰족캡B 제품

### 시나리오 2: "최소 주문량 5000개 제품"

**매칭 청크**:
```
✅ GY-20_moq: "최소주문수량 5,000개 (캡)" (Priority: 0.95)
   Keywords: ["MOQ", "최소주문", "수량", "개수"]

✅ GY-20_moq_v2: "5,000개부터 주문 가능한 캡" (Priority: 0.9)
   Keywords: ["주문", "최소", "캡"]
```

### 시나리오 3: "PP 재질 한국산 캡"

**매칭 청크 (Multiple)**:
```
✅ GY-20_material: "PP 재질 캡" (Priority: 0.95)
✅ GY-20_origin: "한국" (Priority: 0.7)
✅ GY-20_business_composite: "MOQ 5,000개, PP 재질" (Priority: 0.7)
```

**Hybrid Search**:
- Metadata Filter: `material: "PP", origin: "한국", category: "cap"`
- Semantic Search: "PP 재질 한국산 캡"
- Re-ranking: 여러 청크 매칭 → 높은 점수

### 시나리오 4: "에센스 담는 40ml 용기"

**매칭 청크**:
```
✅ idx_13_capacity: "40ml 용량 보틀" (Priority: 0.95)
✅ idx_13_use_case: "고농축 에센스, 트래블 사이즈 담는 보틀" (Priority: 0.95)
✅ idx_13_target_product: "세럼, 에센스 담을 수 있는 보틀" (Priority: 0.9)
```

---

## 🚀 확장성

### 신규 필드 추가

```python
# 1. FieldType Enum에 추가
class FieldType(Enum):
    DISCHARGE_VOLUME = "discharge_volume"  # 토출량 (펌프 전용)

# 2. 템플릿 등록
registry.add_custom_template(
    category=ProductCategory.PUMP,
    field_type=FieldType.DISCHARGE_VOLUME,
    template="토출량 {field}ml (1회 펌핑)",
    priority=0.9,
    search_keywords=["토출량", "분사량", "1회", "펌핑"]
)

# 3. 필드 추출 로직 추가
if "discharge_volume" in product_data:
    fields[FieldType.DISCHARGE_VOLUME] = product_data["discharge_volume"]

# 완료! 자동으로 청크 생성됨
```

### 신규 카테고리 추가

```python
# 1. ProductCategory Enum에 추가
class ProductCategory(Enum):
    LABEL = "label"  # 라벨

# 2. 카테고리별 템플릿 등록
def _register_label_templates(self):
    label = self.category_templates[ProductCategory.LABEL]

    label[FieldType.PRODUCT_NAME] = [
        ChunkTemplate(
            field_type=FieldType.PRODUCT_NAME,
            template="{field} 라벨",
            priority=1.0,
            search_keywords=["라벨", "스티커", "label"]
        ),
    ]

    # ... 나머지 필드 템플릿
```

---

## 📈 성능 & 통계

### 청크 생성 통계 (테스트 3개 제품)

```json
{
  "total_chunks": 44,
  "by_category": {
    "cap": 18,
    "bottle": 18,
    "pump": 8
  },
  "by_field_type": {
    "product_name": 6,
    "product_code": 3,
    "size": 2,
    "neck": 3,
    "material": 5,
    "moq": 2,
    "use_case": 2,
    "capacity": 3,
    "..." : "..."
  },
  "by_priority": {
    "1.0": 3,    # Highest priority (Product Name)
    "0.9": 19,   # High priority (Specs, Use Cases)
    "0.8": 4,    # Medium-high
    "0.7": 18    # Medium (Contact, Generic)
  }
}
```

### 전체 데이터셋 예상

- **134 Bottles/Jars**: ~2,400 chunks (평균 18개/제품)
- **337 Caps/Pumps**: ~3,000 chunks (평균 9개/제품)
- **총 471 제품**: **~5,400 Atomic Chunks**

임베딩 크기:
- 5,400 chunks × 384 dim = **~8.1MB** (매우 가볍고 빠름)

---

## 🎯 다음 단계

### Phase 1: 전체 데이터셋 처리 ✅ 준비 완료

```python
# Load all products
with open('data/processed/products/metadata/product_dictionary_with_accessories.json') as f:
    bottles_jars = json.load(f)

with open('data/processed/products/metadata/cap_pump_product_list_complete.json') as f:
    caps_pumps = json.load(f)

# Generate all chunks
all_chunks = generate_all_chunks_atomic(
    list(bottles_jars.values()) + caps_pumps
)

print(f"Generated {len(all_chunks)} atomic chunks")
```

### Phase 2: 임베딩 & Qdrant 업로드

```python
# 1. Embedding generation
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

embeddings = model.encode([chunk.text for chunk in all_chunks])

# 2. Qdrant upload
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")

client.upload_collection(
    collection_name="products_atomic",
    vectors=embeddings,
    payloads=[chunk.metadata for chunk in all_chunks]
)
```

### Phase 3: 하이브리드 검색

```python
# User query
query = "20파이 캡 MOQ 5000개"

# 1. Metadata filters
filters = {
    "must": [
        {"key": "category", "match": {"value": "cap"}},
        {"key": "moq", "range": {"gte": 4000, "lte": 6000}}
    ]
}

# 2. Semantic search
results = client.search(
    collection_name="products_atomic",
    query_vector=model.encode(query),
    query_filter=filters,
    limit=10
)

# 3. Re-ranking (by priority + relevance)
# ...
```

---

## 📝 구현 파일 목록

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `src/core/product_classifier.py` | ~350 | 제품 분류기 |
| `src/core/chunk_templates.py` | ~450 | 기본 템플릿 + 필드 추출기 |
| `src/core/category_templates.py` | ~420 | 카테고리별 템플릿 |
| `src/core/advanced_chunk_generator.py` | ~280 | 통합 파이프라인 |
| **Total** | **~1,500 lines** | **Production-ready code** |

---

## ✅ 요구사항 충족 확인

| 요구사항 | 상태 | 설명 |
|---------|------|------|
| **아주 잘게 잘라서** | ✅ | Atomic Field-Level (필드당 독립 청크) |
| **템플릿을 만들고** | ✅ | ChunkTemplate 시스템 (20+ 필드 타입) |
| **확장 가능한 형태** | ✅ | add_custom_template() 동적 추가 |
| **카테고리별 다양성** | ✅ | 4개 카테고리별 최적화된 템플릿 |
| **자연어 검색 대응** | ✅ | Multiple Variants + Search Keywords |
| **모든 정보 출력** | ✅ | 15+ 필드 (Name, Code, Size, Neck, MOQ, Material, Origin, Manufacturer, Contact 등) |

---

**구현 완료일**: 2025-11-06
**작성자**: Claude (Sonnet 4.5)
**버전**: 1.0.0
**상태**: ✅ Production Ready
