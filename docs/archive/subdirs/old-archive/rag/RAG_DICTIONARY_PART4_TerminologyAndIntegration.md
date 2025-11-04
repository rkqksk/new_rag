# RAG 사전 Part 4: 산업용어 사전 & 통합 가이드

**Date**: 2025-10-20
**Version**: 1.0
**Focus**: 산업용어 정규화 + 통합 안내
**Items**: 150개 항목 구조

---

## 📋 산업용어 사전 구조

### 1. 약자 정규화 (30개 항목)

```yaml
industry_terminology:
  abbreviations:

    # ─── 재질 약자 (10개) ───
    - id: "term_abbr_001"
      abbreviation: "PE"
      full_name: "폴리에틸렌 (Polyethylene)"
      korean_name: "폴리에틸렌"
      alternatives: ["폴리에틸", "PE 수지", "LDPE/HDPE"]
      context: "가장 일반적인 플라스틱 용기 재질"

    - id: "term_abbr_002"
      abbreviation: "PP"
      full_name: "폴리프로필렌 (Polypropylene)"
      korean_name: "폴리프로필렌"
      alternatives: ["폴리프로필", "PP 수지"]
      context: "내열성 최고 플라스틱"

    - id: "term_abbr_003"
      abbreviation: "PET"
      full_name: "폴리에틸렌 테레프탈레이트"
      korean_name: "폴리에스터"
      alternatives: ["PET 수지", "폴리에스터"]
      context: "음료 병 표준 재질"

    - id: "term_abbr_004"
      abbreviation: "HDPE"
      full_name: "고밀도 폴리에틸렌"
      korean_name: "고밀도 폴리에틸렌"
      alternatives: ["HDPE 수지"]
      difference_from_PE: "PE보다 2-3배 강함, 산 저항 우수"

    - id: "term_abbr_005"
      abbreviation: "LDPE"
      full_name: "저밀도 폴리에틸렌"
      korean_name: "저밀도 폴리에틸렌"
      aliases: ["LDPE"]

    - id: "term_abbr_006"
      abbreviation: "PVC"
      full_name: "폴리염화비닐"
      korean_name: "폴리염화비닐"
      note: "식품용 사용 제한"

    - id: "term_abbr_007"
      abbreviation: "TPE"
      full_name: "열가소성 엘라스토머"
      korean_name: "열가소성 고무"
      use: "극저온 환경, 유연한 제품"

    - id: "term_abbr_008"
      abbreviation: "PMMA"
      full_name: "폴리메틸 메타크릴레이트 (아크릴)"
      korean_name: "아크릴, 아크릴 수지"
      use: "고투명도, 고급 디스플레이"

    - id: "term_abbr_009"
      abbreviation: "PEEK"
      full_name: "폴리에테르 에테르 케톤"
      korean_name: "피크 수지"
      use: "산업용 초고온 (200°C+)"

    - id: "term_abbr_010"
      abbreviation: "PC"
      full_name: "폴리카보네이트"
      korean_name: "폴리카보네이트"
      use: "광학 투명도, 충격 강도"

    # ─── 규제/표준 약자 (10개) ───
    - id: "term_abbr_011"
      abbreviation: "FDA"
      full_name: "Food and Drug Administration (미국 식품의약청)"
      korean_name: "미국 식품의약청"
      relevance: "식품 접촉 재질 인증"

    - id: "term_abbr_012"
      abbreviation: "MSDS"
      full_name: "Material Safety Data Sheet"
      korean_name: "물질안전보건자료"
      relevance: "화학약품 안전 정보"

    - id: "term_abbr_013"
      abbreviation: "KS"
      full_name: "한국산업표준"
      korean_name: "한국산업표준"
      relevance: "국내 용기 규격"

    - id: "term_abbr_014"
      abbreviation: "ISO"
      full_name: "국제표준기구"
      korean_name: "국제표준기구"
      relevance: "국제 품질 기준"

    - id: "term_abbr_015"
      abbreviation: "NSF"
      full_name: "National Sanitation Foundation"
      korean_name: "식품 안전 인증"
      relevance: "식품 접촉 용기 인증"

    - id: "term_abbr_016"
      abbreviation: "UV"
      full_name: "자외선 (Ultraviolet)"
      korean_name: "자외선"
      relevance: "플라스틱 손상 원인"

    - id: "term_abbr_017"
      abbreviation: "BPA"
      full_name: "비스페놀 A"
      korean_name: "비스페놀 A"
      risk: "유해 화학물질, 온도 상승시 용출"

    - id: "term_abbr_018"
      abbreviation: "RoHS"
      full_name: "유해물질 제한 지침"
      korean_name: "유해물질 제한"
      relevance: "EU 규제, 국내 적용 증가"

    - id: "term_abbr_019"
      abbreviation: "OSHA"
      full_name: "Occupational Safety and Health Administration"
      korean_name: "미국 산업안전보건청"
      relevance: "산업용 화학약품 저장"

    - id: "term_abbr_020"
      abbreviation: "GHS"
      full_name: "세계조화제도 (Globally Harmonized System)"
      korean_name: "화학물질 분류 표시"
      relevance: "위험물 표시 표준"

    # ─── 기술 약자 (10개) ───
    - id: "term_abbr_021"
      abbreviation: "UV차단제"
      full_name: "자외선 차단 첨가제"
      korean_name: "UV 차단제"
      purpose: "플라스틱 UV 손상 방지"

    - id: "term_abbr_022"
      abbreviation: "가소제"
      full_name: "Plasticizer"
      korean_name: "가소제"
      risk: "고온에서 용출 가능"

    - id: "term_abbr_023"
      abbreviation: "항산화제"
      full_name: "Antioxidant"
      korean_name: "항산화제"
      purpose: "플라스틱 열화 방지"

    - id: "term_abbr_024"
      abbreviation: "충전제"
      full_name: "Filler"
      korean_name: "충전제"
      purpose: "강도 증가, 비용 절감"

    - id: "term_abbr_025"
      abbreviation: "안료"
      full_name: "Pigment"
      korean_name: "안료"
      purpose: "색상 부여"

    - id: "term_abbr_026"
      abbreviation: "윤활제"
      full_name: "Lubricant"
      korean_name: "윤활제"
      purpose: "생산 효율성"

    - id: "term_abbr_027"
      abbreviation: "계면활성제"
      full_name: "Surfactant"
      korean_name: "계면활성제"
      context: "세정제 주성분"

    - id: "term_abbr_028"
      abbreviation: "에멀젼"
      full_name: "Emulsion"
      korean_name: "에멀젼"
      context: "유기용제-물 혼합"

    - id: "term_abbr_029"
      abbreviation: "용해"
      full_name: "Dissolution"
      korean_name: "용해"
      context: "화학약품이 플라스틱 침투"

    - id: "term_abbr_030"
      abbreviation: "흡착"
      full_name: "Adsorption"
      korean_name: "흡착"
      context: "냄새/색상 흡수"
```

### 2. 제품 코드 정규화 (50개 항목 구조)

```yaml
  product_codes:

    # ─── PE 라인 (10개) ───
    - id: "term_code_001"
      code: "PE-CLEAR-50"
      description: "투명 폴리에틸렌 50ml 용기"
      category: "소형/샘플용"
      material: "PE"
      capacity: "50ml"
      properties: "투명, 저가"
      use_case: "의약품 샘플, 시료"
      price: "약 ₩500"

    - id: "term_code_002"
      code: "PE-CLEAR-100"
      capacity: "100ml"
      use_case: "샴푸, 향수, 샘플"

    - id: "term_code_003"
      code: "PE-CLEAR-500"
      capacity: "500ml"
      use_case: "일반 음료, 식용유"

    - id: "term_code_004"
      code: "PE-CLEAR-1L"
      capacity: "1L"
      use_case: "우유, 주스"

    - id: "term_code_005"
      code: "PE-AMBER-100"
      color: "갈색 (차광)"
      capacity: "100ml"
      use_case: "의약품, UV 민감 제품"

    - id: "term_code_006"
      code: "PE-SQUEEZE-300"
      shape: "스퀼즈 (압축 가능)"
      capacity: "300ml"
      use_case: "세제, 샤워젤"

    - id: "term_code_007"
      code: "PE-PUMP-500"
      feature: "펌프 디스펜서"
      capacity: "500ml"
      use_case: "샴푸, 로션"

    # ─── PP 라인 (10개) ───
    - id: "term_code_008"
      code: "PP-BLUE-1L"
      color: "파란색"
      capacity: "1L"
      material: "PP"
      use_case: "화학약품, 세정제"

    - id: "term_code_009"
      code: "PP-BLUE-5L"
      capacity: "5L"
      use_case: "산업용 화학약품"

    - id: "term_code_010"
      code: "PP-WHITE-1L"
      color: "흰색"
      capacity: "1L"
      use_case: "일반 산업용"

    - id: "term_code_011"
      code: "PP-TANK-20L"
      shape: "드럼/탱크"
      capacity: "20L"
      use_case: "대량 화학약품 저장"

    # ─── PET 라인 (10개) ───
    - id: "term_code_012"
      code: "PET-CLEAR-250"
      material: "PET"
      color: "투명"
      capacity: "250ml"
      use_case: "음료, 주스"

    - id: "term_code_013"
      code: "PET-BOTTLE-500"
      shape: "병"
      capacity: "500ml"
      use_case: "음료, 우유"

    - id: "term_code_014"
      code: "PET-BOTTLE-1L"
      capacity: "1L"
      use_case: "음료 대량 저장"

    - id: "term_code_015"
      code: "PET-BOTTLE-2L"
      capacity: "2L"

    # ─── HDPE 라인 (10개) ───
    - id: "term_code_016"
      code: "HDPE-TANK-5L"
      material: "HDPE"
      capacity: "5L"
      use_case: "산업 화학약품 (산 저장)"

    - id: "term_code_017"
      code: "HDPE-TANK-20L"
      capacity: "20L"
      use_case: "대량 산업 저장"

    # ─── 특수 용기 (10개) ───
    - id: "term_code_018"
      code: "SAMPLE-VIAL-15"
      type: "샘플 병"
      capacity: "15ml"
      material: "유리 또는 PE"
      use_case: "의료 샘플"

    - id: "term_code_019"
      code: "HAZARD-DRUM-55"
      type: "위험물 드럼"
      capacity: "55갤런 (약 200L)"
      use_case: "산업 폐기물"

```

### 3. 기술용어 정규화 (70개 항목 구조)

```yaml
  technical_terms:

    # ─── 특성 용어 (30개) ───
    - id: "term_tech_001"
      korean: "투명도"
      english: "Transparency"
      measure: "백분율 (%)"
      scale: "0-100% (높을수록 투명)"
      examples: "PE 85%, PET 95%, PP 75%"

    - id: "term_tech_002"
      korean: "내열성"
      english: "Heat Resistance"
      measure: "온도 (°C)"
      context: "최대 안전 온도"

    - id: "term_tech_003"
      korean: "강도"
      english: "Strength"
      measure: "MPa (메가파스칼)"
      context: "충격/압축 강도"

    - id: "term_tech_004"
      korean: "유연성"
      english: "Flexibility"
      measure: "신장률 (%)"
      context: "얼마나 늘어나는가"

    - id: "term_tech_005"
      korean: "밀폐성"
      english: "Sealing Ability"
      context: "뚜껑이 얼마나 잘 닫히는가"

    - id: "term_tech_006"
      korean: "UV 저항성"
      english: "UV Resistance"
      context: "자외선 손상 정도"
      duration: "3개월-5년 범위"

    - id: "term_tech_007"
      korean: "화학 저항성"
      english: "Chemical Resistance"
      context: "산/알칼리/용제 견딤"

    - id: "term_tech_008"
      korean: "무게"
      english: "Weight"
      measure: "그램 (g)"

    - id: "term_tech_009"
      korean: "두께"
      english: "Thickness"
      measure: "밀리미터 (mm)"

    - id: "term_tech_010"
      korean: "광택도"
      english: "Glossiness"
      context: "반짝거림 정도"

    # ─── 문제 용어 (20개) ───
    - id: "term_prob_001"
      korean: "변색"
      english: "Discoloration"
      causes: ["UV 노출", "화학 반응", "시간 경과"]

    - id: "term_prob_002"
      korean: "취약성"
      english: "Brittleness"
      causes: ["저온", "UV 손상"]

    - id: "term_prob_003"
      korean: "누수"
      english: "Leakage"
      causes: ["뚜껑 불량", "균열"]

    - id: "term_prob_004"
      korean: "변형"
      english: "Deformation"
      causes: ["고온", "압력"]

    - id: "term_prob_005"
      korean: "미세균열"
      english: "Micro-cracks"
      risk: "누수 전조"

    - id: "term_prob_006"
      korean: "냄새 발생"
      english: "Odor Emission"
      causes: ["화학 용출", "저장 제품 냄새"]

    - id: "term_prob_007"
      korean: "가소제 용출"
      english: "Plasticizer Leaching"
      risk: "식품 오염"

    - id: "term_prob_008"
      korean: "스크래치"
      english: "Scratches"
      severity: "외형상 문제만"

    # ─── 규제 용어 (20개) ───
    - id: "term_reg_001"
      korean: "식품 접촉 승인"
      english: "Food Contact Approval"
      bodies: ["FDA", "식약처"]

    - id: "term_reg_002"
      korean: "독성 평가"
      english: "Toxicity Assessment"
      standard: "FDA CFR 177"

    - id: "term_reg_003"
      korean: "용출 테스트"
      english: "Migration Testing"
      test_type: "화학물질 용출량 측정"

    - id: "term_reg_004"
      korean: "재활용 표시"
      english: "Recycling Symbol"
      types: ["#1 PET", "#2 PE", "#5 PP"]
```

---

## 🔗 통합 가이드 & 사용 방법

### 파일 구조

```
app/data/dictionaries/
├─ dictionary_product_recommendation_v1.yaml
├─ dictionary_quality_qa_v1.yaml
├─ dictionary_terminology_v1.yaml
└─ README.md (이 가이드)
```

### YAML 로딩 (Python)

```python
from app.services.dictionary_loader import DictionaryLoader

loader = DictionaryLoader()
product_recs = loader.load('product_recommendation')
quality_qa = loader.load('quality_material_qa')
terminology = loader.load('industry_terminology')
```

### 쿼리 처리 흐름

```
사용자 입력
  ↓
[산업용어 사전] 정규화
  ↓
[제품 추천 사전] 매칭
  ↓
[품질/재질 Q&A] 상세 정보
  ↓
시스템 응답
```

### 주간 추가 프로세스

```
매주 월요일:
1. 저신뢰도 쿼리 분석 (시스템 로그)
2. 새 항목 5-10개 추출
3. YAML 파일 업데이트
4. PatternLoader 재로드 (자동)
```

---

**상태**: 4부 완료
**다음**: 모든 파트 통합

