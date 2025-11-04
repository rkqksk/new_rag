# 사전 적용 상태 분석 보고서

**Date**: 2025-10-20
**Status**: 🔴 **현재 적용 안 됨** (사전 인프라 부재)
**진행 상황**: 방금 생성된 사전 프레임워크는 아직 RAG에 연결되지 않음

---

## 📊 현재 RAG 시스템 구조

### 현재 구현된 계층 (Phase 1)

```
사용자 질문
  ↓
[Classification Layer] ✅ 구현됨
├─ QueryClassifier (BERT-based, 7가지 타입)
├─ IntentDetector (멀티라벨, 6가지 타입)
├─ ToneAnalyzer (형식성, 긴급성, 전문성)
└─ LanguageDetector (언어 감지)
  ↓
[Context Layer] ✅ 구현됨
├─ ConversationManager
└─ ContextStore (Redis)
  ↓
[Retrieval Layer] ⚠️ 부분 구현
├─ QueryExpander (동의어 기반, 제한적)
└─ ❌ Qdrant 벡터 검색: 없음
  ↓
[Generation Layer] ✅ 구현됨
├─ PromptBuilder
├─ ResponseGenerator (Ollama localhost:11434)
└─ TemplateSystem (쿼리 타입별)
  ↓
응답 생성
```

---

## 🔴 현재 문제점

### 1. **Qdrant 검색 미연결** (치명적)
```
현재:
  - 398개 제품 벡터화 완료 ✅
  - 3개 Qdrant 컬렉션 준비됨 ✅
  - 하지만: 검색 쿼리에서 호출 안 함 ❌

결과:
  - 고객 질문 → 벡터 검색 X
  - Ollama가 컨텍스트 없이 응답 생성
  - 제품 데이터 활용 안 함
```

### 2. **산업용어 사전 미적용** (중요)
```
현재:
  - QueryExpander에 하드코딩된 동의어만 있음
  - 영어 중심 동의어 (error, fix, optimize 등)

문제:
  - 한국어 산업용어 미지원
  - PE, PP, PET 약자 매핑 없음
  - 제품 코드 정규화 없음
  - 다양한 변동 표현 처리 불가
```

### 3. **제품 추천 논리 없음** (핵심 부재)
```
현재:
  - 템플릿 시스템이 있지만
  - 제품 추천 사전의 규칙이 없음

결과:
  - "투명한 용기 필요해" → PE, PET 추천 불가
  - "뜨거운 음식 담을 용기" → PP 추천 불가
  - 단순 LLM 생성만 가능
```

### 4. **품질/재질 Q&A 미통합** (보조 부재)
```
현재:
  - TemplateSystem이 기본 템플릿만 제공

문제:
  - PE 특성 (85-90% 투명도) 미제공
  - 문제 해결 가이드 없음
  - MSDS 정보 연결 안 됨
```

---

## ✅ 준비된 것

### 1. **벡터 데이터** (준비 완료)
```
✅ 398개 제품 인덱싱
✅ 3개 Qdrant 컬렉션:
   - products_text: 796 벡터 (3584-dim)
   - products_images: 791 벡터 (1024-dim)
   - products_hybrid: BM25 + 벡터

✅ 벡터화 스크립트: scripts/qdrant_init_and_ingest.py
```

### 2. **사전 프레임워크** (방금 생성)
```
✅ RAG_COMPREHENSIVE_DICTIONARY_GUIDE.md
✅ 3가지 사전 구조 정의
✅ 260개 초기 항목 체크리스트
✅ 한국어 우선 아키텍처

준비 상태:
  - Part 1: 작성 가이드 ✅
  - Part 2: 제품 추천 템플릿 ✅
  - Part 3: 품질/재질 Q&A 템플릿 ✅
  - Part 4: 산업용어 템플릿 ✅
```

### 3. **LLM 연결** (작동)
```
✅ Ollama: localhost:11434
✅ 모델: qwen2.5:7b-instruct-q4_K_M
✅ ResponseGenerator 클래스 구현
```

---

## 🎯 필요한 작업 (적용을 위해)

### Phase 2: 사전 적용 (1-2주)

#### 1. **사전 로더 구현** (필수)
```python
# app/services/dictionary_loader.py

class DictionaryLoader:
    """YAML 사전 파일 로드"""

    def load_product_recommendations():
        """제품 추천 사전 로드"""
        # YAML 파싱
        # 메모리 캐싱
        # 신뢰도 검증

    def load_quality_qa():
        """품질/재질 Q&A 로드"""

    def load_terminology():
        """산업용어 정규화 로드"""
```

**소요 시간**: 4-6시간

#### 2. **Qdrant 검색 통합** (필수)
```python
# app/services/qdrant_search.py (신규)

class QdrantSearchService:
    """Qdrant에서 제품 검색"""

    async def search_products(query: str, top_k: int = 5):
        """
        1. 쿼리를 벡터로 변환
        2. Qdrant에서 검색
        3. 상위 K개 반환
        """

    async def hybrid_search(query: str):
        """텍스트 + 이미지 + BM25 하이브리드"""
```

**소요 시간**: 6-8시간

#### 3. **QueryExpander 개선** (필수)
```python
# app/rag_consultation/retrieval/query_expander.py (수정)

class QueryExpander:
    """
    현재: 하드코딩 동의어만 있음

    개선:
    1. DictionaryLoader 사용
    2. 산업용어 정규화 적용
    3. 한국어 동의어 확장
    4. 제품 코드 매핑
    """

    async def expand(query: str):
        # 산업용어 사전으로 정규화
        # 쿼리 확장
        # Qdrant 검색 쿼리 생성
```

**소요 시간**: 4-6시간

#### 4. **PromptBuilder 개선** (필수)
```python
# app/rag_consultation/generation/prompt_builder.py (수정)

class PromptBuilder:
    """
    현재: 기본 구조만 있음

    개선:
    1. Qdrant 검색 결과 포함
    2. 제품 추천 사전 활용
    3. 품질/재질 정보 포함
    4. 문맥 기반 생성
    """

    async def build(query, search_results):
        # Qdrant 결과 + 사전 정보 통합
        # 문맥에 맞는 프롬프트 생성
```

**소요 시간**: 6-8시간

#### 5. **API 수정** (필수)
```python
# app/api/consultation.py (수정)

@router.post("/query")
async def consultation_query(request):
    """
    1. 쿼리 분류 ✅
    2. 의도 감지 ✅
    3. 톤 분석 ✅
    4. [NEW] 산업용어 정규화
    5. [NEW] Qdrant 검색
    6. [NEW] 사전 정보 매칭
    7. 프롬프트 생성
    8. LLM 응답
    """
```

**소요 시간**: 2-3시간

#### 6. **YAML 파일 작성** (사용자 책임)
```
app/data/dictionaries/
├─ dictionary_product_recommendation_v1.yaml (채우기)
├─ dictionary_quality_qa_v1.yaml (채우기)
└─ dictionary_terminology_v1.yaml (채우기)

초기 260개 항목 채우기
```

**소요 시간**: 1-2일 (사용자)

---

## 🔄 적용 흐름도 (목표)

```
사용자: "투명한 500ml 용기 추천해줄래?"
  ↓
[1] Classification ✅
  └─ 쿼리 타입: RECOMMENDATION
  └─ 의도: product_recommendation
  └─ 톤: neutral, medium
  ↓
[2] 산업용어 정규화 (사전 로더 사용) 🆕
  └─ "용기" → "container", "vessel"
  └─ 동의어 확장: 용기, 컨테이너, 보관용기
  ↓
[3] Qdrant 검색 (벡터 + 하이브리드) 🆕
  └─ 쿼리 벡터화
  └─ "투명" + "500ml" 조건 검색
  └─ 상위 5개 제품 반환
    - PE-CLEAR-500 (점수 0.92)
    - PET-CLEAR-500 (점수 0.89)
    - 등등
  ↓
[4] 제품 추천 사전 매칭 (사전 로더 사용) 🆕
  └─ 투명성: PE (85-90%), PET (95-99%)
  └─ 용량: 500ml → 중형 카테고리
  └─ 추천: PE (경제적), PET (최고 투명)
  ↓
[5] 품질/재질 정보 추가 (사전 로더 사용) 🆕
  └─ PE 특성: 50-70°C 권장
  └─ PET 특성: 60-85°C 권장
  └─ 비교 정보 제공
  ↓
[6] 프롬프트 생성 (개선된 PromptBuilder) 🆕
  "사용자가 투명한 500ml 용기를 찾습니다.
   Qdrant 검색 결과: PE-CLEAR-500, PET-CLEAR-500
   제품 추천 사전 정보:
   - PE: 85-90% 투명, 저가형, 50-70°C
   - PET: 95-99% 투명, 고강도, 60-85°C

   추천 이유: ..."
  ↓
[7] LLM 응답 (Ollama) ✅
  "투명한 500ml 용기로는 두 가지를 추천합니다:

   1. PE-CLEAR-500 (경제적 추천)
      - 투명도: 85-90%
      - 가격: ₩1,500-₩2,000
      - 안전 온도: 50-70°C

   2. PET-CLEAR-500 (최고 품질)
      - 투명도: 95-99%
      - 가격: ₩2,000-₩3,000
      - 안전 온도: 60-85°C
      - 강도: PE보다 우수

   뜨거운 액체를 담을 예정이면 PP 고려..."
  ↓
사용자 응답
```

---

## 📈 현재 vs 목표

| 단계 | 현재 상태 | 목표 상태 | 진행도 |
|------|---------|---------|-------|
| 벡터 데이터 | ✅ 완료 | ✅ 유지 | 100% |
| 사전 프레임워크 | 🆕 방금 생성 | ✅ 완료 | 20% |
| 사전 로더 | ❌ 없음 | ✅ 필수 | 0% |
| Qdrant 검색 | ❌ 없음 | ✅ 필수 | 0% |
| 산업용어 정규화 | ⚠️ 기본만 | ✅ 고급 | 20% |
| 제품 추천 논리 | ❌ 없음 | ✅ 필수 | 0% |
| 품질 정보 통합 | ❌ 없음 | ✅ 필수 | 0% |
| LLM 프롬프트 | ✅ 기본 | ✅ 고급 | 50% |

---

## 🚀 권장 일정

### Week 1-2: 사전 적용 (Phase 2)
- Day 1-2: 사전 로더 구현 (6h)
- Day 2-3: Qdrant 검색 통합 (8h)
- Day 3: QueryExpander 개선 (6h)
- Day 4: PromptBuilder 개선 (8h)
- Day 4: API 수정 (3h)
- **총**: 31시간 (개발팀)

### Week 1: 데이터 준비 (사용자)
- 260개 항목 초기 채우기 (산업용어 사전부터)
- YAML 파일 구조 검증

### Week 3: 통합 테스트
- 실제 쿼리 테스트
- 신뢰도 검증
- 성능 측정

---

## 결론

**현재**: 사전 프레임워크가 **종이 위에만** 존재
**필요**: 실제 **RAG 파이프라인에 연결하는 코드**

**적용 시 기대 효과**:
- ✅ 정확한 제품 추천 (신뢰도 0.85+)
- ✅ 산업 용어 자동 인식
- ✅ 한국어 자연스러운 응답
- ✅ Qdrant 벡터 데이터 활용
- ✅ 다양한 쿼리 표현 처리

**Timeline**: 2-3주 (개발 + 초기 데이터)

