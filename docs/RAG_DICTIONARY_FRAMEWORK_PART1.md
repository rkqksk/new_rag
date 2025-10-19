# RAG 사전 프레임워크 - Part 1: 작성 가이드 & 구조

**Date**: 2025-10-20
**Version**: 1.0
**Status**: 프로덕션 준비 단계
**언어**: 한국어 우선 (영어는 기술용어만)

---

## 📋 개요

이 문서는 RAG 시스템의 핵심을 이루는 **3가지 사전 (Dictionary)** 을 정의하고, 각 사전을 점진적으로 채워나가기 위한 완전한 프레임워크를 제공합니다.

### 3가지 핵심 사전

1. **제품 추천 사전 (Product Recommendation Dictionary)** - 핵심 🎯
   - 용도: 고객 질문 → 최적 제품 추천
   - 예: "투명한 용기 필요해" → PE, PET 추천
   - 데이터: 제품 특성 + 추천 규칙 + 가격 범위

2. **품질/재질 Q&A 사전 (Quality/Material QA Dictionary)** - 부가
   - 용도: 제품 특성 & 문제 해결
   - 예: "폴리에틸렌은 얼마나 내구적이야?" → 상세 답변
   - 데이터: 재질 특성 + 문제-해결 매핑

3. **산업용어 사전 (Industry Terminology Dictionary)** - 지원
   - 용도: 쿼리 정규화 & 변동 처리
   - 예: "PET" = "폴리에틸렌 테레프탈레이트"
   - 데이터: 약자 ↔ 전체명 매핑

---

## 🎯 작성 원칙 (5가지)

### 1. 한국어 우선 (Korean-First)
```
✅ 좋음: "폴리에틸렌 용기는 식품 보관에 적합하고..."
❌ 나쁨: "Polyethylene container is suitable for..."
```
- 모든 설명은 **한국어**로 작성
- 영어는 **기술 용어 (PE, PET, PP)** 와 **제품코드 (PP-50-001)** 에만 사용

### 2. 구체성 (Specificity)
```
✅ 좋음: "세제 희석액에도 견딜 수 있으며, 60°C까지 안전"
❌ 나쁨: "강하다" 또는 "좋다"
```
- 모호한 표현 금지
- 구체적인 조건, 온도, 용도명시
- 검증 가능한 사실 기반

### 3. 재사용성 (Reusability)
```
사전 항목은 여러 질문에서 재사용되어야 함:

Q1: "투명한 용기 필요해"
→ PE 추천 (투명성 특성 사용)

Q2: "PE로 만든 용기가 얼마나 투명해?"
→ 같은 투명성 항목 재사용
```

### 4. 확장성 (Extensibility)
```
초기 크기: 충분히 크게 시작
├─ 제품 추천: 50개 규칙
├─ 재질 Q&A: 60개 항목
└─ 산업용어: 150개 항목

주간 추가: 5-10개씩 점진적 확대
└─ 6주 후: 초기 3배 규모로 자동 성장
```

### 5. 검증 가능성 (Verifiability)
```
모든 정보는 다음 출처 중 하나에서 검증:
├─ 제품 스펙 시트
├─ MSDS (Material Safety Data Sheet)
├─ 산업 표준 (KS, ISO)
└─ 실제 고객 피드백
```

---

## 📝 기본 작성 형식

### YAML 형식 (모든 사전)

```yaml
# 파일명 규칙: dictionary_[이름]_[버전].yaml
# 예: dictionary_product_recommendation_v1.yaml

dictionaries:
  - id: "UNIQUE_ID"           # 고유 번호 (자동 생성됨)
    category: "카테고리명"      # 분류
    term: "검색 키워드"         # 사용자 검색어
    synonyms: ["동의어1", "동의어2"]  # 변동 처리

    # 핵심 콘텐츠
    content:
      korean: "한국어 설명"     # 필수
      specification: "스펙"     # 해당될 때만
      condition: "조건"         # 상한/하한 값 등

    # 추천 또는 답변
    recommendation: "구체적인 추천"
    confidence: 0.95           # 신뢰도 (0.0-1.0)

    # 메타데이터
    source: "출처"             # MSDS, 제품스펙 등
    created_date: "2025-10-20"
    last_updated: "2025-10-20"
    tags: ["tag1", "tag2"]

    # 예제
    examples:
      - context: "상황 설명"
        question: "고객 질문 예제"
        answer: "시스템 응답"
```

---

## 🎯 사전 1: 제품 추천 사전 (MAIN)

### 목적
고객의 구체적인 필요 조건 (용도, 크기, 특성) → 최적의 제품 추천

### 구조

```yaml
product_recommendation:

  # ─── 카테고리 1: 용도 기반 추천 ───
  use_case:
    - id: "rec_001_food_storage"
      term: "식품 보관"
      synonyms: ["음식 보관", "식용 용기", "급식용"]
      products: ["PE-CLEAR-500", "PET-CLEAR-250"]
      explanation: "식품과의 직접 접촉으로 FDA 규격 충족 필수"

    - id: "rec_002_industrial_chemical"
      term: "화학물질 보관"
      synonyms: ["화학약품", "산업용 저장", "세정제 보관"]
      products: ["PP-BLUE-1L", "HDPE-TANK-20L"]
      restriction: "알칼리 용액은 PE 사용 금지"

  # ─── 카테고리 2: 특성 기반 추천 ───
  characteristic:
    - id: "rec_101_transparent"
      term: "투명성"
      synonyms: ["투명한", "안이 보이는", "clear"]
      products: ["PE-CLEAR", "PET-CLEAR"]
      details: "PET > PE 순서로 투명도 높음"

    - id: "rec_102_heat_resistant"
      term: "내열성"
      synonyms: ["고온 견딤", "열에 강한"]
      products: ["PP-WHITE", "PEEK-BLACK"]
      temperature_range: "80-120°C"

  # ─── 카테고리 3: 크기/용량 기반 ───
  size:
    - id: "rec_201_small"
      capacity: "50-250ml"
      products: ["PE-SMALL-100", "PET-SQUARE-150"]
      use_case: "소량 샘플, 시료 보관"

    - id: "rec_202_medium"
      capacity: "250-1000ml"
      products: ["PE-MEDIUM-500", "PET-BOTTLE-800"]
      use_case: "일반 보관, 가정용"

    - id: "rec_203_large"
      capacity: "1L-20L"
      products: ["PP-TANK-5L", "HDPE-CONTAINER-20L"]
      use_case: "대량 보관, 산업용"
```

### 초기 작성 체크리스트

```
제품 추천 사전 (초기 50개 항목)
├─ 용도 기반 (15개)
│  ├─ 식품 보관 (3개)
│  ├─ 화학물질 (3개)
│  ├─ 의약품 (2개)
│  ├─ 세정제 (2개)
│  ├─ 화장품 (2개)
│  └─ 기타 산업용 (3개)
│
├─ 특성 기반 (20개)
│  ├─ 투명성 (4개)
│  ├─ 내열성 (4개)
│  ├─ 내산성/알칼리성 (4개)
│  ├─ 경량성 (4개)
│  └─ 강도 (4개)
│
└─ 크기/용량 (15개)
   ├─ 소형 (5개: 50ml-250ml 범위)
   ├─ 중형 (5개: 250ml-1L 범위)
   └─ 대형 (5개: 1L-20L 범위)
```

---

## ❓ 사전 2: 품질/재질 Q&A 사전 (SECONDARY)

### 목적
"왜?", "얼마나?", "언제?" 형태의 기술적 질문에 대한 상세 답변 제공

### 구조

```yaml
quality_material_qa:

  # ─── 카테고리 1: 재질 특성 ───
  material_properties:

    - id: "qa_m001_polyethylene"
      material: "폴리에틸렌 (PE)"
      full_name: "Polyethylene"
      aliases: ["PE", "폴리에틸렌"]

      characteristics:
        transparency: "고투명성 (85-90%)"
        heat_resistance: "낮음 (50-70°C 권장, 최대 90°C)"
        chemical_resistance:
          - "산: 강함"
          - "알칼리: 약함"
          - "유기용제: 중간"
        durability: "3-5년 (UV 노출 시 단축)"
        cost: "저가형 (기준 100%)"
        recycling: "HDPE/LDPE 분류"

      qa_examples:
        - q: "PE는 식품에 안전한가?"
          a: "예. FDA 승인 PE는 식품 직접 접촉에 안전합니다. 단, 식품용으로 별도 인증된 제품 사용 필수."

        - q: "PE는 얼마나 투명한가?"
          a: "PE는 85-90% 투명도를 가지며, PET(95%)보다는 약간 낮지만 충분히 투명합니다."

        - q: "PE가 햇빛에 노출되면 어떻게 되나?"
          a: "UV 차단제 없는 일반 PE는 2-3개월 내에 갈색으로 변색되고 취약해집니다. UV 차단 PE 제품 사용 추천."

      msds_reference: "MSDS_PE_v2.1.pdf"
      standards: ["FDA CFR 177.1520", "ISO 1043-1"]

    - id: "qa_m002_polypropylene"
      material: "폴리프로필렌 (PP)"
      full_name: "Polypropylene"
      # ... 유사 구조

    - id: "qa_m003_pet"
      material: "폴리에틸렌 테레프탈레이트 (PET)"
      full_name: "Polyethylene Terephthalate"
      # ... 유사 구조

  # ─── 카테고리 2: 일반 품질 문제 ───
  quality_issues:

    - id: "qa_q001_discoloration"
      issue: "용기 변색"
      synonyms: ["색이 변했어", "누렇게 변했다", "갈색 변색"]

      causes:
        - cause: "UV 노출"
          symptom: "갈색 또는 황색 변색, 취약해짐"
          duration: "2-3개월 내 발생"
          solution: "UV 차단 제품으로 교체 (BLACK/BLUE 라인)"

        - cause: "화학 반응"
          symptom: "국부적 변색, 냄새 발생"
          material_affected: ["PE", "PP"]
          solution: "해당 화학물질 저항 재질 확인 후 교체"

    - id: "qa_q002_brittleness"
      issue: "용기 취약성 / 깨짐"
      synonyms: ["깨지기 쉬워", "부러진다", "자꾸 깨진다"]

      causes:
        - cause: "저온 노출"
          temp_range: "-10°C 이하"
          explanation: "대부분의 플라스틱은 저온에서 취약해짐"
          solution: "상온 (15-25°C) 보관, 또는 내한성 재질 (TPE) 사용"

        - cause: "UV 손상"
          explanation: "자외선이 분자 결합을 파괴함"
          solution: "어두운 곳에 보관 또는 검은색 용기 사용"

  # ─── 카테고리 3: MSDS 관련 ───
  msds_information:

    - id: "qa_s001_food_contact"
      question: "이 용기로 뜨거운 음식을 담아도 되나?"
      answer: "재질에 따라 다릅니다. PE: 최대 70°C, PP: 최대 100°C, PET: 최대 85°C 권장. 더 높은 온도는 유해 물질 용출 가능."
      regulation: "FDA CFR 177"

    - id: "qa_s002_chemical_storage"
      question: "아세톤을 이 용기에 담을 수 있나?"
      answer: "아니요. 아세톤은 PE, PP를 용해시킵니다. HDPE 또는 특수 코팅 용기만 사용 가능."
      affected_materials: ["PE", "PP", "PET"]
      safe_materials: ["HDPE (제한적)", "특수 코팅 용기"]
```

### 초기 작성 체크리스트

```
품질/재질 Q&A 사전 (초기 60개 항목)
├─ 재질 특성 (20개)
│  ├─ PE 상세 (4개: 특성, 용도, 제한, 팁)
│  ├─ PP 상세 (4개)
│  ├─ PET 상세 (4개)
│  ├─ HDPE 상세 (4개)
│  └─ 기타 (4개)
│
├─ 품질 문제 해결 (25개)
│  ├─ 변색 (4개: 원인별)
│  ├─ 취약성 (4개)
│  ├─ 누수 (4개)
│  ├─ 냄새 (4개)
│  └─ 강도 부족 (5개)
│
└─ MSDS/규제 (15개)
   ├─ 식품 저장 (5개)
   ├─ 화학물질 (5개)
   └─ 규제 준수 (5개)
```

---

## 🔤 사전 3: 산업용어 사전 (SUPPORTING)

### 목적
다양한 표현 방식의 쿼리를 정규화하여 체계적으로 처리

### 구조

```yaml
industry_terminology:

  # ─── 약자 ↔ 전체명 ───
  abbreviations:
    - id: "term_abbr_001"
      abbreviation: "PE"
      full_name: "폴리에틸렌 (Polyethylene)"
      aliases: ["폴리에틸", "폴리에틸렌"]

    - id: "term_abbr_002"
      abbreviation: "PP"
      full_name: "폴리프로필렌 (Polypropylene)"

    - id: "term_abbr_003"
      abbreviation: "PET"
      full_name: "폴리에틸렌 테레프탈레이트"

  # ─── 제품 코드 ───
  product_codes:
    - id: "term_code_001"
      code: "PE-CLEAR-500"
      description: "투명 폴리에틸렌 500ml 용기"
      product_name: "PE 클리어 500"
      category: "소형 용기"

    - id: "term_code_002"
      code: "PP-BLUE-1L"
      description: "파란색 폴리프로필렌 1L 용기"
      product_name: "PP 블루 1L"
      category: "중형 용기"

  # ─── 기술용어 정규화 ───
  technical_terms:
    - id: "term_tech_001"
      term: "투명도"
      synonyms: ["명확성", "투명성", "clarity", "transparency"]
      definition: "빛이 통과하는 정도 (0-100%, 높을수록 투명함)"

    - id: "term_tech_002"
      term: "내열성"
      synonyms: ["내온도성", "내고온성", "heat_resistance"]
      definition: "높은 온도에서 재질 특성이 유지되는 능력"
```

### 초기 작성 체크리스트

```
산업용어 사전 (초기 150개 항목)
├─ 약자 (30개)
│  ├─ 재질 약자 (PE, PP, PET 등)
│  ├─ 용어 약자 (MSDS, KS, FDA 등)
│  └─ 회사 약자
│
├─ 제품 코드 (50개)
│  ├─ 제품 라인별 (PE, PP, PET 각 라인)
│  └─ 용량별 코드
│
└─ 기술용어 (70개)
   ├─ 특성 용어 (30개: 투명성, 내열성 등)
   ├─ 문제 용어 (20개: 변색, 취약성 등)
   ├─ 규제 용어 (15개: FDA, MSDS 등)
   └─ 프로세스 용어 (5개)
```

---

## 📋 초기 사전 크기 요약

```
초기 3가지 사전 총 260개 항목:
├─ 제품 추천: 50개
├─ 품질/재질 Q&A: 60개
└─ 산업용어: 150개

주간 추가 계획 (6주):
├─ 1-2주: +30개 (사용자 피드백 기반)
├─ 3-4주: +40개 (실제 쿼리 분석)
├─ 5-6주: +50개 (LoRA 학습 데이터)
└─ 6주 후: 총 410개 항목 (58% 증가)
```

---

## 🔄 점진적 확장 방식

### 주간 프로세스

```
매주 월요일:
1. 이전주 사용자 질문 수집
   └─ 시스템에서 자동 로깅 (저신뢰도 응답 중심)

2. 새로운 항목 식별
   ├─ 새 용도 / 새 재질 / 새 문제 등
   └─ 5-10개 항목 우선순위 지정

3. 사전에 추가
   └─ YAML 파일 업데이트 (API 또는 수동)

4. 시스템 재로드
   └─ 자동 적용 (PatternLoader 활용)

결과: 주당 5-10개씩 유기적 성장
```

### 3개월 후 예상 규모

```
초기 (Week 1):        260개
+30 (Week 2):         290개
+40 (Week 4):         330개
+50 (Week 6):         380개
+60 (Month 2):        440개
+80 (Month 3):        520개

→ 3개월 후 초기 대비 2배 규모 달성
```

---

## 💾 파일 구조 및 저장소

### 디렉토리 구조

```
app/data/dictionaries/
├─ product_recommendation/
│  ├─ v1/
│  │  ├─ dictionary_product_recommendation_v1.yaml
│  │  ├─ examples_product_v1.yaml
│  │  └─ metadata_v1.json
│  └─ v2/ (향후)
│
├─ quality_material_qa/
│  ├─ v1/
│  │  ├─ dictionary_quality_qa_v1.yaml
│  │  ├─ msds_references.yaml
│  │  └─ metadata_v1.json
│  └─ v2/ (향후)
│
├─ industry_terminology/
│  ├─ v1/
│  │  ├─ dictionary_terminology_v1.yaml
│  │  ├─ abbreviations_v1.yaml
│  │  └─ product_codes_v1.yaml
│  └─ v2/ (향후)
│
├─ README.md (사전 작성 가이드)
└─ changelog.md (버전 변경사항)
```

---

## ✅ 다음 단계 (Part 2에서)

**Part 2에서 생성할 내용:**

1. **제품 추천 사전 (YAML 템플릿)** - 50개 항목 구조
   - 초기 틀: 20-30% 채워진 상태
   - 나머지: 사용자가 채울 수 있는 형식

2. **품질/재질 Q&A 사전 (YAML 템플릿)** - 60개 항목 구조
   - 초기 틀: 20-30% 채워진 상태
   - MSDS 참조 템플릿 포함

3. **산업용어 사전 (YAML 템플릿)** - 150개 항목 구조
   - 약자, 코드, 기술용어 각 섹션
   - 정규화 규칙 포함

4. **사전 작성 체크리스트**
   - 각 항목별 필수 필드
   - 품질 검증 기준
   - 예제 포함

---

## 📞 문의 사항

이 문서에서 불명확한 부분이 있으면:
- YAML 형식 문법 → 예제 섹션 참고
- 특정 용어 정의 → 산업용어 사전 참고
- 작성 방식 → 기본 작성 형식 섹션 참고

---

**Created**: 2025-10-20
**Status**: Part 1 완료, Part 2 진행 예정
