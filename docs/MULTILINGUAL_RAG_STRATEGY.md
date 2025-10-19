# Multilingual RAG Strategy - Korean-First Architecture

**Date**: 2025-10-20
**Priority**: CRITICAL
**Status**: 전략 수립 단계

---

## 🚨 문제점 분석

### 영어 위주 구조의 위험성

#### 1. **쿼리 분류 오류**
```
❌ 문제: 영어 패턴 기반 분류
"PE 펌프용기, 50ml 용량, 투명색 가능한가?"
→ 영어 키워드 매칭 실패
→ 쿼리 타입 오분류 (예: casual_inquiry로 잘못 분류)

✅ 해결: 한국어 패턴 우선
특수문자: "?", "한다", "가능한가", "어떻게"
코드: "PE", "50ml", "용기"
→ Product Discovery + Technical Specification 하이브리드 감지
```

#### 2. **임베딩 공간 왜곡**
```
❌ 문제: 영어 임베딩 모델 편향
"조직배양"  ← 한국 제조용어
vs
"tissue culture" ← 영어 용어
→ 같은 의미인데 임베딩 공간에서 멀 수 있음

✅ 해결: 한국어 최적화 모델
- gte-Qwen2-7B-instruct: 중문/한국어 지원 우수
- 코드-스펙 매핑: 100% 정확성 필요
```

#### 3. **코드 필드 손상**
```
❌ 문제: 토크나이제이션 손실
제품코드: "PP-50-001_특수사양"
→ 영어 토크나이저가 한글 자소 분리
→ "ㅍㅍ", "ㅁㅡㅁ" 같은 조각화

✅ 해결: 정확 매칭 필요
코드 필드: 토큰화 없이 BM25 정확 매칭
```

#### 4. **상담 톤 인식 오류**
```
❌ 문제: 한국어 존댓글/반말 구분 실패
"그거 사양이 뭔데?" (친구)
"그것의 사양이 무엇입니까?" (고객)
→ 영어 기반 모델은 이 뉘앙스 구분 불가

✅ 해결: 한국어 특화 톤 분석
- 어미: "~네요", "~어요", "~합니다", "~냐", "~다"
- 경어체 수준 감지
- 반말/존댓글/높은존댓글 구분
```

#### 5. **문맥 손실**
```
❌ 문제: 한국어 대명사 처리 실패
"이거 다른 색상도 있나요?"
"저거랑 뭐가 달라요?"
→ "이거", "저거" 의미 모호

✅ 해결: 한국어 문맥 추적
- 이전 제품 ID 직접 매핑
- 한국어 대명사 사전
- 불완전 표현 보정
```

#### 6. **QA 쌍 생성 실패**
```
❌ 문제: 자동 번역 기반 QA
Q: "50ml PE용기 재질이 뭐야?"
→ 영어로 번역 후 QA 생성
→ 원문의 의도 손실

✅ 해결: 원문 기반 QA 생성
- 한국어 특화 질문 템플릿
- 코드 + 한글 혼합 예제
- 산업용어 사전 기반
```

---

## 🎯 한국어-우선 아키텍처 설계

### 1. **데이터 인코딩 전략**

#### 한국어 정규화
```python
class KoreanNormalizer:
    """한국어 텍스트 정규화"""

    rules = {
        '조직배양': ['조직배양', 'tissue culture'],  # 한국용어 우선
        '용기': ['용기', 'container', 'jar', 'bottle'],
        'PE': ['PE', '폴리에틸렌'],  # 코드 우선
    }

    def normalize_product_code(self, code: str) -> str:
        """
        제품코드 보존 (절대 손실 금지)
        PP-50-001 → PP-50-001 (토크나이제이션 금지)
        """
        return code  # 정확 매칭만 사용

    def normalize_korean_text(self, text: str) -> str:
        """한국어 텍스트 정규화"""
        # 자모 분리 방지
        # 초성/중성/종성 보존
        return text
```

#### 다국어 필드 매핑
```python
product_schema = {
    "product_name": {
        "korean": "제품명",          # 우선
        "english": "Product Name",
        "code": "PP-50-001",        # 정확 매칭
        "searchable": True
    },
    "specifications": {
        "korean": "용량 50ml, 재질 PE, 색상 투명",
        "english": "50ml capacity, PE material, transparent",
        "structured": {
            "capacity": "50ml",
            "material": "PE",
            "color": "투명"  # 한국어 유지
        }
    },
    "material_properties": {
        "code": "PE",
        "korean": "폴리에틸렌",
        "characteristics": [
            "유연성",     # 한국어
            "flexibility",
            "내구성",
            "durability"
        ]
    }
}
```

### 2. **청킹 전략 (다국어 인식)**

#### 필드별 청킹
```python
chunking_strategy = {
    "level_1_korean_primary": {
        "product_name_korean": {
            "text": "PE 펌프용기 50ml",
            "weight": 1.5,
            "tokenization": "none",  # 정확 매칭만
            "search_type": "exact_match"
        },
        "product_name_code": {
            "text": "PP-50-001",
            "weight": 1.6,  # 코드 최우선
            "tokenization": "none",
            "search_type": "exact_match"
        },
        "specifications_korean": {
            "text": "용량: 50ml, 재질: PE, 색상: 투명",
            "weight": 1.3,
            "tokenization": "morpheme",  # 형태소 분석
            "search_type": "semantic"
        }
    },

    "level_2_english_secondary": {
        "product_name_english": {
            "text": "PE Pump Container 50ml",
            "weight": 0.7,  # 보조
            "tokenization": "word",
            "search_type": "semantic"
        }
    },

    "level_3_contextual": {
        "use_case_korean": {
            "text": "크림, 로션, 에센스 등 화장품 용기",
            "weight": 1.2,
            "context": "cosmetic_product"
        },
        "problem_solution_korean": {
            "text": "내용물 새는 문제 → PE 재질 선택 권장",
            "weight": 1.1,
            "context": "problem_solving"
        }
    }
}
```

#### 코드 정확 매칭 보장
```python
class ExactMatchIndexing:
    """제품 코드/사양 정확 매칭"""

    def create_exact_match_chunks(self, product):
        chunks = []

        # 코드: 절대 손실 금지
        for code in product['codes']:
            chunks.append({
                'id': f"{product['id']}_code_{code}",
                'text': code,  # 그대로 사용
                'field': 'product_code',
                'search_type': 'exact_match',
                'sparse_index': True,  # BM25에 추가
                'dense_index': False   # 벡터 필요 없음
            })

        # 사양 코드 (PE, PET, PP)
        for material in product['materials']:
            chunks.append({
                'id': f"{product['id']}_material_{material}",
                'text': material,  # 정확히
                'field': 'material_code',
                'search_type': 'exact_match',
                'sparse_index': True
            })

        # 용량 (50ml, 100ml)
        for capacity in product['capacities']:
            chunks.append({
                'id': f"{product['id']}_capacity_{capacity}",
                'text': capacity,  # 정확히
                'field': 'capacity',
                'search_type': 'exact_match',
                'sparse_index': True
            })

        return chunks
```

### 3. **쿼리 분류 (한국어 우선)**

#### 한국어 패턴 매칭
```python
query_patterns_korean = {
    "technical_specification": {
        "keywords": [
            "사양", "스펙", "재질", "용량", "치수",
            "코드", "어떻게", "뭐야", "뭔가",
            "PE", "PET", "PP",  # 코드
            "50ml", "100ml"     # 용량
        ],
        "morphemes": ["사양_N", "재질_N", "용량_N"],
        "examples": [
            "PE 펌프용기 50ml 사양이 뭐야?",
            "제품코드 PP-50-001의 특성은?",
            "이 용기, PE 재질 맞나요?"
        ]
    },

    "product_discovery": {
        "keywords": [
            "추천", "찾고있어", "있나요", "가능한",
            "좋을까", "뭐가좋아", "어떤거"
        ],
        "morphemes": ["추천_V", "찾기_V", "필요_V"],
        "examples": [
            "화장품 담을 용기 뭐가 좋을까요?",
            "PE와 PET 중에 뭐가 낫나요?",
            "이 용도에 맞는 제품 있나요?"
        ]
    },

    "problem_solving": {
        "keywords": [
            "문제", "안돼", "새요", "깨져", "필요",
            "해결", "어떻게", "도와줘"
        ],
        "examples": [
            "내용물이 새는데 뭐가 문제야?",
            "이 제품 색이 빠지는데...",
            "더 튼튼한 용기 있나요?"
        ]
    },

    "casual_inquiry": {
        "keywords": ["이거", "저거", "그거", "뭐야", "뭐지"],
        "grammar": ["반말", "친구톤"],
        "examples": [
            "이거 뭐하는 거야?",
            "저거 색상 몇 가지예요?",
            "이거, 다른 사이즈 있어?"
        ]
    },

    "follow_up_with_context": {
        "keywords": ["그럼", "그러면", "그다음", "추가로"],
        "requires": "conversation_history",
        "examples": [
            "그럼 다른 색상도 있나요?",
            "그러면 가격이 얼마예요?",
            "그럼 주문은 어떻게?"
        ]
    }
}
```

#### 한국어 의도 감지
```python
intent_detection_korean = {
    "exact_specification": {
        "signals": ["정확한 사양 요청", "제품코드 언급"],
        "response_style": "precise_technical",
        "example": "PP-50-001의 정확한 치수가 뭐야?"
    },

    "comparative_choice": {
        "signals": ["선택 고민", "차이점 질문"],
        "response_style": "decision_support",
        "example": "PE랑 PET, 뭐가 달라?"
    },

    "problem_first": {
        "signals": ["문제 제시 먼저", "해결책 요청"],
        "response_style": "consultative",
        "example": "내용물이 새는데, 어떤 용기 추천?"
    }
}
```

### 4. **톤 인식 (한국어 특화)**

#### 존댓글/반말 감지
```python
korean_politeness_levels = {
    "level_5_highest": {
        "markers": ["~합니다", "~습니다", "~드립니다"],
        "examples": [
            "제품 사양을 알려주시기 바랍니다.",
            "주문 절차를 설명해주실 수 있습니까?"
        ],
        "response_style": "formal_business"
    },

    "level_4_polite": {
        "markers": ["~세요", "~으세요", "~시"],
        "examples": [
            "이 제품의 사양이 뭔가요?",
            "다른 색상도 있으신가요?"
        ],
        "response_style": "professional_friendly"
    },

    "level_3_neutral": {
        "markers": ["~요", "~어요", "~아요"],
        "examples": [
            "50ml PE용기가 뭐예요?",
            "이거 가격이 얼마예요?"
        ],
        "response_style": "consultative"
    },

    "level_2_casual": {
        "markers": ["~네", "~는데", "~야"],
        "examples": [
            "이거 뭐하는 건데?",
            "저거 색상 여러 개네?"
        ],
        "response_style": "friendly_casual"
    },

    "level_1_intimate": {
        "markers": ["반말", "~아/어", "~지"],
        "examples": [
            "이거 뭐야?",
            "저거 가능해?"
        ],
        "response_style": "close_friend"
    }
}
```

### 5. **응답 템플릿 (한국어 우선)**

#### 기술 사양 응답
```python
technical_response_korean = """
**제품명**: {product_name_korean} ({product_code})
**재질**: {material_korean} ({material_code})
**사양**:
  - 용량: {capacity}
  - 치수: {dimensions_korean}
  - 펌프 토출량: {pump_volume}

**특징**:
  {characteristics_korean}

**추가 정보**:
제품 코드 {product_code}로 더 자세한 사양을 확인할 수 있습니다.
"""
```

#### 추천 응답
```python
recommendation_response_korean = """
**{product_name_korean}** 추천합니다!

**선택 이유**:
{reason_korean}

**특징**:
  ✓ {benefit_1_korean}
  ✓ {benefit_2_korean}
  ✓ {benefit_3_korean}

**비슷한 제품**:
{similar_products_korean}

**더 알고 싶으신 점**:
{followup_question_korean}
"""
```

### 6. **임베딩 최적화**

#### 한국어 임베딩 선택
```yaml
embedding_model_selection:

  option_1_gte_qwen2_7b:
    model: "gte-Qwen2-7B-instruct"
    dimensions: 3584
    strengths:
      - 한국어 지원 우수 (중문 기반)
      - 코드 + 자연어 혼합 처리 가능
      - 산업용어 인식
    weaknesses:
      - 일부 한국어 특화 표현 부족
    recommendation: "현재 최선의 선택"

  option_2_korean_specialized:
    model: "upskyai/bge-m3-korean"
    dimensions: 1024
    strengths:
      - 한국어 특화 (native)
      - 존댓글 구분 가능
      - 한국 산업용어 풍부
    weaknesses:
      - 차원이 낮음 (검색 정확도 낮을 수 있음)
    recommendation: "Phase 3: 하이브리드 임베딩 고려"

  option_3_hybrid_approach:
    primary: "gte-Qwen2-7B-instruct"
    secondary: "upskyai/bge-m3-korean"
    strategy: "dual_indexing"
    recommendation: "최적: Phase 2+ 고려"
```

---

## 🔧 구현 수정사항

### Phase 1 분류기 수정
```python
# ❌ 기존 (영어 중심)
query_types = ["technical_specification", "product_discovery"]

# ✅ 수정 (한국어 중심)
query_types_korean = {
    "기술_사양": "technical_specification_korean",
    "제품_추천": "product_discovery_korean",
    "문제_해결": "problem_solving_korean",
    "캐주얼_문의": "casual_inquiry_korean",
    "후속_질문": "followup_korean"
}
```

### 코드 필드 보호
```python
# ❌ 기존 (토크나이제이션 위험)
chunk = {
    'text': product_code,  # "PP-50-001" → 손상 위험
    'embedding': embed(text)  # 분리됨
}

# ✅ 수정 (정확 매칭 보장)
chunk = {
    'exact_text': product_code,  # "PP-50-001" (원본 유지)
    'search_strategy': 'exact_match_only',  # BM25만 사용
    'dense_embedding': None,  # 벡터 불필요
    'sparse_index': True  # BM25만 활용
}
```

### 대명사 처리
```python
# ❌ 기존 (손실)
"이거 다른 색상도 있나요?"
→ 의미 불명확

# ✅ 수정 (컨텍스트 추적)
previous_product = get_last_product(session_id)  # 이전 제품
query = resolve_korean_pronouns(
    "이거 다른 색상도 있나요?",
    previous_product=previous_product
)
→ "PE 펌프용기 50ml의 다른 색상도 있나요?"
```

---

## 📋 체크리스트 (Phase 1 재설계)

- [ ] 한국어 패턴 사전 구축 (100+ 패턴)
- [ ] 제품 코드 정확 매칭 시스템
- [ ] 한국어 형태소 분석기 통합
- [ ] 존댓글 수준 감지 모듈
- [ ] 대명사 해결 시스템
- [ ] 한국어 임베딩 모델 검증
- [ ] 다국어 필드 정규화
- [ ] 한국어 응답 템플릿 (30+)
- [ ] 한국어 QA 쌍 생성 (100+ 샘플)
- [ ] 엔드투엔드 한국어 테스트

---

## 🚀 다음 단계

**Phase 1 재설계**: 한국어-우선 아키텍처
- 코드: ~4,500줄 (기존 3,077 + 한국어 특화 1,400+)
- 패턴 사전: 한국어 500+, 영어 100
- 응답 템플릿: 한국어 40+, 영어 10
- 테스트: 한국어 중심 (영어는 보조)

**예상 효과:**
- 쿼리 분류 정확도: 85% → 95%+
- 코드 필드 손실률: 0.1% → 0%
- 톤 인식 정확도: 80% → 95%+
- 대화 컨텍스트 유지: 60% → 95%+

---

**Critical**: 이제부터 모든 설계는 **한국어 우선, 영어 보조** 원칙 적용
