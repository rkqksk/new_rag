# RAG 사전 Part 2: 제품 추천 사전 (Product Recommendation Dictionary)

**Date**: 2025-10-20
**Version**: 1.0
**Focus**: 제품 추천 (핵심)
**Items**: 50개 항목 구조 (20-30% 초기 채움)

---

## 📋 제품 추천 사전 구조

### 1. 용도 기반 추천 (15개 항목)

```yaml
product_recommendation:
  use_case_recommendations:

    # ─── 1-1. 식품 저장용 (3개) ───
    - id: "rec_001"
      category: "용도"
      term: "식품 보관용"
      synonyms: ["음식 보관", "식용 용기", "음료 저장", "급식용"]

      recommended_materials:
        - material: "PE (폴리에틸렌)"
          confidence: 0.95
          reason: "FDA 승인, 투명하고 식품 안전"
          code: "PE-CLEAR-500, PE-CLEAR-1L"
          price_range: "₩1,000-₩3,000"

        - material: "PET (폴리에틸렌 테레프탈레이트)"
          confidence: 0.92
          reason: "고투명도, 강도 우수, 음료 권장"
          code: "PET-CLEAR-250, PET-BOTTLE-500"
          price_range: "₩1,500-₩4,000"

      key_requirements:
        - "FDA CFR 177 규정 준수"
        - "식품용 인증 필수"
        - "냄새/색 없음"
        - "화학 용출 없음"

      restrictions:
        - "화학물질 혼용 금지"
        - "고온 음식 (80°C 이상) - PE 사용 금지"

      example_questions:
        - q: "과일을 담을 수 있는 투명한 용기 추천해줄래?"
          a: "PE-CLEAR-1L이나 PET-CLEAR-250을 추천합니다. PE는 더 저렴하고, PET는 더 투명하고 강합니다."

        - q: "뜨거운 국을 담아도 되나?"
          a: "PE는 50-70°C 이상에서 사용 불가능합니다. PP(폴리프로필렌)나 특수 내열 용기를 사용해주세요."

    - id: "rec_002"
      category: "용도"
      term: "음료 저장용"
      synonyms: ["음료 보관", "음료 용기", "물 저장", "주스 보관"]

      recommended_materials:
        - material: "PET"
          confidence: 0.96
          reason: "맑은 투명도, 강도, 음료 산성 견딤"
          code: "PET-BOTTLE-500, PET-BOTTLE-1L, PET-BOTTLE-2L"
          price_range: "₩1,500-₩5,000"

        - material: "PE"
          confidence: 0.85
          reason: "경제적, 충분한 투명도"
          code: "PE-CLEAR-1L, PE-CLEAR-2L"
          price_range: "₩1,000-₩3,000"

      key_requirements:
        - "높은 투명도 (90% 이상)"
        - "산성 음료 (과즙) 견딤"
        - "탄산음료 시 고강도 필요"

      temperature_range: "0-50°C"

      example_questions:
        - q: "과일 주스를 담을 수 있는 용기?"
          a: "PET-BOTTLE-500 또는 PE-CLEAR-1L 추천. PET가 더 강하고 오래 보관에 유리합니다."

    - id: "rec_003"
      category: "용도"
      term: "냉동 식품용"
      synonyms: ["얼린 음식", "냉동 보관", "냉장 용기"]

      recommended_materials:
        - material: "PP (폴리프로필렌)"
          confidence: 0.94
          reason: "저온 강도, 식품 안전, -20°C 견딤"
          code: "PP-CLEAR-500, PP-CLEAR-1L"
          price_range: "₩1,200-₩3,500"

      key_requirements:
        - "저온 취약성 낮음"
        - "-20°C 이하 안전"
        - "밀폐 용기 필수"

      example_questions:
        - q: "냉동실에 넣을 용기는?"
          a: "PP 용기 권장. PE는 -10°C 이하에서 취약해질 수 있습니다."

    # ─── 1-2. 화학물질 보관용 (3개) ───
    - id: "rec_004"
      category: "용도"
      term: "화학 약품 저장용"
      synonyms: ["화학물질 보관", "약품 저장", "산업용 저장", "세정제 보관"]

      recommended_materials:
        - material: "PP (폴리프로필렌)"
          confidence: 0.90
          reason: "산/알칼리 저항성, 내구성"
          code: "PP-BLUE-1L, PP-BLUE-5L, PP-TANK-20L"
          price_range: "₩2,000-₩20,000"

        - material: "HDPE"
          confidence: 0.88
          reason: "강한 산 저장용"
          code: "HDPE-TANK-5L, HDPE-TANK-20L"
          price_range: "₩3,000-₩25,000"

      restrictions:
        - "PE 절대 금지 (산 노출 시 손상)"
        - "PET 제한적 (약산만 가능)"
        - "유기용제 저장시 특수 재질 필수"

      chemical_compatibility:
        safe_acids: ["황산 (약액)", "염산 (약액)"]
        safe_bases: ["수산화나트륨 (약액)", "암모니아 수"]
        unsafe: ["강산", "아세톤", "에탄올 (고농도)"]

      example_questions:
        - q: "세정제를 담을 수 있는 용기?"
          a: "PP-BLUE-1L이 최적입니다. PE는 알칼리 세정제에 약합니다."

    - id: "rec_005"
      category: "용도"
      term: "의약품/의료용품 보관"
      synonyms: ["약 보관", "의료용", "약품 저장", "알약 용기"]

      recommended_materials:
        - material: "PE (또는 PET)"
          confidence: 0.96
          reason: "약사법 승인, 화학적 안정성"
          code: "PE-AMBER-100, PE-AMBER-250"
          price_range: "₩2,000-₩5,000"

      key_requirements:
        - "의약품 허가 획득"
        - "아이-안전 뚜껑 권장"
        - "차광 처리 필수 (자주색/갈색)"

      example_questions:
        - q: "비타민 보충제를 담을 용기?"
          a: "PE-AMBER-250 권장. 갈색 처리로 빛 차단됩니다."

    - id: "rec_006"
      category: "용도"
      term: "화장품/샴푸 보관"
      synonyms: ["샴푸 용기", "로션 용기", "화장품"]

      recommended_materials:
        - material: "PE"
          confidence: 0.92
          reason: "유분 저항, 경제성"
          code: "PE-PUMP-500, PE-SQUEEZE-300"
          price_range: "₩1,500-₩4,000"

        - material: "PP"
          confidence: 0.88
          reason: "강도, 고급스러운 외관"
          code: "PP-DISPENSER-500"
          price_range: "₩2,500-₩6,000"

      example_questions:
        - q: "손거울 세제용 용기?"
          a: "PE-SQUEEZE 추천. 유분 저항 우수합니다."

    # ─── 1-3. 기타 산업용 (3개) ───
    - id: "rec_007"
      category: "용도"
      term: "샘플/시료 보관용"
      synonyms: ["샘플 병", "시험 용기", "시료 채취"]

      recommended_materials:
        - material: "PE 또는 PP"
          confidence: 0.93
          reason: "가격, 공급 용이, 무균 처리 가능"
          code: "PE-SAMPLE-15, PE-SAMPLE-50"
          price_range: "₩500-₩2,000"

      example_questions:
        - q: "물 수질 검사 샘플 보관용?"
          a: "PE-SAMPLE-50 추천. 무균 처리되고 경제적입니다."

    - id: "rec_008"
      category: "용도"
      term: "산업 폐기물 보관"
      synonyms: ["폐기물 저장", "산업 쓰레기", "유독성 폐기물"]

      recommended_materials:
        - material: "PP"
          confidence: 0.91
          reason: "내구성, 다양한 폐기물 대응"
          code: "PP-HAZARD-5L, PP-HAZARD-20L"
          price_range: "₩5,000-₩25,000"

      key_requirements:
        - "위험 물질 표시 필수"
        - "밀폐성 우수"
        - "정기 검사 필수"

      example_questions:
        - q: "염료 폐기물 담을 용기?"
          a: "PP-HAZARD-20L 권장. 산업용 폐기물 저장 규정 준수합니다."
```

---

## 2. 특성 기반 추천 (20개 항목 구조)

```yaml
  characteristic_recommendations:

    # ─── 투명도 기반 (4개) ───
    - id: "rec_101"
      characteristic: "투명도"
      level: "고투명도 (95% 이상)"
      synonyms: ["투명한", "명확한", "안이 보이는"]

      ranking:
        1st: "PET (95-99%)"
        2nd: "PE (85-90%)"
        3rd: "PMMA (92-96%)"

      use_cases:
        - "음료 디스플레이"
        - "고급 식품 패키징"
        - "의약품 시각 확인"

      price_vs_transparency:
        "가장 투명: PET"
        "가성비 최고: PE"
        "프리미엄: PMMA (단, 비쌈)"

      example_questions:
        - q: "가장 투명한 용기는?"
          a: "PET가 최고입니다 (95-99% 투명도). PE도 충분히 투명 (85-90%)합니다."

    - id: "rec_102"
      characteristic: "중간 투명도"
      level: "중간 투명도 (70-85%)"

      materials:
        - "반투명 PE"
        - "반투명 PP"

      use_cases:
        - "일반 가정용"
        - "식품 시각 확인 필요 없을 때"

      price_advantage: "투명도 낮을수록 저가"

    - id: "rec_103"
      characteristic: "불투명"
      level: "차광 처리 (0-10% 투명도)"

      colors: ["검은색", "파란색", "자주색", "갈색"]

      use_cases:
        - "자외선 차단 필요 (화학, 의약)"
        - "빛에 민감한 제품"
        - "산업용 저장"

      example_questions:
        - q: "햇빛을 피해야 하는 제품은?"
          a: "PP-BLUE나 갈색 용기 추천. UV 차단됩니다."

    - id: "rec_104"
      characteristic: "색상 옵션"
      colors: ["투명", "반투명", "검은색", "파란색", "흰색", "자주색", "갈색"]

      color_meanings:
        transparent: "일반 식품, 음료"
        blue: "화학약품, 세정제"
        brown: "의약품, 빛 민감 제품"
        white: "일반 산업용"
        black: "UV 완전 차단"

    # ─── 내열성 기반 (4개) ───
    - id: "rec_201"
      characteristic: "내열성"
      level: "극저온 (-40°C 이하)"

      recommended_materials:
        - material: "TPE"
          max_temp: "-40°C"
          confidence: 0.95

      use_cases:
        - "냉동 초저온"
        - "극지방 사용"

      cost: "매우 비쌈"

    - id: "rec_202"
      characteristic: "내열성"
      level: "저온 (-20~0°C)"

      recommended_materials:
        - material: "PP"
          max_temp: "-20°C"
          confidence: 0.95
        - material: "PE"
          max_temp: "-10°C"
          confidence: 0.85

      use_cases:
        - "냉동실 보관"
        - "일반 냉장"

      example_questions:
        - q: "냉동실 안전한 용기?"
          a: "PP 추천 (-20°C 안전). PE는 -10°C 권장입니다."

    - id: "rec_203"
      characteristic: "내열성"
      level: "상온 (0~70°C)"

      recommended_materials:
        - material: "PE"
          max_temp: "50-70°C"
        - material: "PET"
          max_temp: "60-85°C"
        - material: "PP"
          max_temp: "70-100°C"

      use_cases:
        - "일반 실내 보관"
        - "온수 보관 (제한적)"

    - id: "rec_204"
      characteristic: "내열성"
      level: "고온 (80°C 이상)"

      recommended_materials:
        - material: "PP"
          max_temp: "100-120°C"
          confidence: 0.95
        - material: "특수 PEEK"
          max_temp: "200°C+"
          confidence: 0.98

      use_cases:
        - "뜨거운 음식/음료"
        - "산업 열처리"

      cost: "PP는 중가, PEEK는 고가"

      example_questions:
        - q: "뜨거운 국을 담을 수 있는 용기?"
          a: "PP (폴리프로필렌) 권장 (최대 100°C). 일반 PE는 사용 불가능합니다."

    # ─── 화학 저항성 기반 (4개) ───
    - id: "rec_301"
      characteristic: "산 저항성"
      level: "강산 저항"

      recommended_materials:
        - material: "HDPE"
          confidence: 0.96
        - material: "PP"
          confidence: 0.90

      unsafe_materials: ["PE", "PET"]

      example_questions:
        - q: "황산을 담을 수 있는 용기?"
          a: "HDPE 또는 PP (강산용) 필수. PE/PET는 손상됩니다."

    - id: "rec_302"
      characteristic: "알칼리 저항성"
      level: "강알칼리 저항"

      recommended_materials:
        - material: "PP"
          confidence: 0.95
        - material: "PE"
          confidence: 0.85

      unsafe_materials: ["HDPE (제한적)"]

    - id: "rec_303"
      characteristic: "유기용제 저항성"
      level: "유기용제 저항"

      safe: ["PP (알코올 제한적)"]
      unsafe: ["PE", "PET (대부분 유기용제)"]

      special_note: "아세톤/벤젠/톨루엔 저장 시 특수 코팅 필수"

    - id: "rec_304"
      characteristic: "내구성"
      level: "일반/우수/극우수"

      ranking:
        excellent: "PP, HDPE"
        good: "PET"
        fair: "PE"

      durability_factors:
        - "자외선 노출: 차단 필수"
        - "충격: PP > PET > PE"
        - "마모: PP > PE"

    # ─── 경량성 기반 (2개) ───
    - id: "rec_401"
      characteristic: "경량성"
      level: "극경량 (50g 이하/500ml)"

      recommended_materials:
        - material: "PE"
          weight: "20-30g (500ml 기준)"
          confidence: 0.98
        - material: "PET"
          weight: "15-25g"

      use_cases:
        - "휴대용 음료"
        - "일회용"
        - "배송 최소화"

    - id: "rec_402"
      characteristic: "강도 vs 경량성"
      level: "균형형"

      recommended_materials:
        - material: "PP"
          weight: "25-35g (500ml)"
          strength: "우수"
```

---

## 3. 크기/용량 기반 추천 (15개 항목 구조)

```yaml
  size_based_recommendations:

    # ─── 소형 (50-250ml) ───
    - id: "rec_501"
      size_category: "소형 (50-250ml)"
      typical_use: "샘플, 소량 제품, 시료"

      standard_sizes: ["50ml", "100ml", "150ml", "200ml", "250ml"]

      recommended_products:
        - code: "PE-SMALL-50"
          capacity: "50ml"
          price: "₩500-₩800"
          use: "의약품 샘플, 화장품"

        - code: "PE-SMALL-100"
          capacity: "100ml"
          price: "₩600-₩1,000"
          use: "일반 샘플, 향수"

        - code: "PET-SQUARE-150"
          capacity: "150ml"
          price: "₩800-₩1,200"
          use: "음료, 주스 (소량)"

    - id: "rec_502"
      size_category: "소형 (100-250ml)"
      use_case: "개인용, 휴대용"

      examples:
        - "여행용 샴푸"
        - "핸드크림"
        - "향수"
        - "와인/주류 (소량)"

    # ─── 중형 (250ml-1L) ───
    - id: "rec_601"
      size_category: "중형 (250ml-1L)"
      typical_use: "가정용, 일반 보관"

      standard_sizes: ["250ml", "500ml", "750ml", "1L"]

      recommended_products:
        - code: "PE-MEDIUM-500"
          capacity: "500ml"
          price: "₩800-₩1,500"
          use: "음료, 주스, 일반 보관"

        - code: "PET-BOTTLE-1L"
          capacity: "1L"
          price: "₩1,200-₩2,000"
          use: "음료 저장, 우유 대체"

    - id: "rec_602"
      size_category: "중형 (500ml-1L)"
      use_case: "가정용 음료, 식용유"

      best_for:
        - "우유/음료"
        - "식용유"
        - "세제 (소량)"
        - "기름"

    # ─── 대형 (1L-20L) ───
    - id: "rec_701"
      size_category: "대형 (1L-20L)"
      typical_use: "산업용, 대량 보관"

      standard_sizes: ["1L", "2L", "5L", "10L", "20L"]

      recommended_products:
        - code: "PP-TANK-5L"
          capacity: "5L"
          price: "₩2,000-₩3,500"
          use: "세제, 기름, 산업 화학"

        - code: "HDPE-CONTAINER-20L"
          capacity: "20L"
          price: "₩5,000-₩10,000"
          use: "화학약품, 대량 저장"

    - id: "rec_702"
      size_category: "대형 (5L-20L)"
      use_case: "산업용, 소매업체, 식당"

      best_for:
        - "대량 음료 저장"
        - "산업 화학"
        - "식용유 (20L 드럼)"
        - "세정제"
```

**상태**: 제품 추천 사전 ~8000토큰 구조 완료
**다음**: Part 3에서 품질/재질 Q&A 사전 계속

