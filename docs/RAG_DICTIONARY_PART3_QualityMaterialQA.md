# RAG 사전 Part 3: 품질/재질 Q&A 사전

**Date**: 2025-10-20
**Version**: 1.0
**Focus**: 품질/재질 기술 문답 (부가)
**Items**: 60개 항목 구조 (20-30% 초기 채움)

---

## 📋 품질/재질 Q&A 사전 구조

### 1. 재질 특성 상세 (20개 항목)

```yaml
quality_material_qa:
  material_properties:

    # ─── PE (폴리에틸렌) ───
    - id: "qa_m001"
      material: "PE (폴리에틸렌)"
      full_name: "Polyethylene"
      aliases: ["PE", "폴리에틸", "폴리에틸렌"]

      properties:
        transparency: "고투명성 (85-90%)"
        heat_resistance: "낮음 (50-70°C 권장)"
        max_temperature: "최대 90°C (단기)"
        cost: "저가형 (기준 100%)"
        weight: "경량"
        durability: "3-5년 (UV 노출시 단축)"

      chemical_resistance:
        acids: "강함"
        bases: "약함"
        solvents: "중간"

      qa_items:
        - q: "PE는 식품에 안전한가?"
          a: "네, FDA 승인 PE는 식품 직접 접촉 안전. 식품용 인증 제품 필수."

        - q: "PE가 햇빛에 노출되면?"
          a: "2-3개월 내 갈색 변색, 취약해짐. UV 차단 PE 제품 사용 권장."

        - q: "PE는 뜨거운 액체를 담을 수 있나?"
          a: "아니요. PE는 50-70°C에서 변형 시작. 80°C 이상 금지."

      standards: ["FDA CFR 177.1520", "ISO 1043-1"]
      msds: "MSDS_PE_v2.1.pdf"

    - id: "qa_m002"
      material: "PP (폴리프로필렌)"
      full_name: "Polypropylene"
      aliases: ["PP", "폴리프로필", "폴리프로필렌"]

      properties:
        transparency: "중투명성 (75-85%)"
        heat_resistance: "우수 (80-120°C)"
        max_temperature: "최대 140°C (단기)"
        cost: "중가형 (기준 120%)"
        strength: "PE보다 강함"

      qa_items:
        - q: "PP는 뜨거운 음식을 담을 수 있나?"
          a: "네, PP는 최대 100°C 안전. 가장 내열성 우수한 플라스틱."

        - q: "PP와 PE의 차이?"
          a: "PP는 더 강하고 내열성 우수. PE는 더 저렴하고 투명도 높음."

        - q: "PP는 냉동실에서 안전한가?"
          a: "네, PP는 -20°C 안전. PE보다 저온 취약성 낮음."

    - id: "qa_m003"
      material: "PET (폴리에틸렌 테레프탈레이트)"
      full_name: "Polyethylene Terephthalate"
      aliases: ["PET", "폴리에스터"]

      properties:
        transparency: "최고 투명성 (95-99%)"
        heat_resistance: "중간 (60-85°C)"
        strength: "매우 강함"
        cost: "중-고가형 (기준 150%)"
        barrier_properties: "산소/습기 차단 우수"

      qa_items:
        - q: "PET는 투명도 최고인가?"
          a: "네, PET가 가장 투명함 (95-99%). 음료 디스플레이 최적."

        - q: "PET 용기는 재사용 가능한가?"
          a: "1회용 권장. 반복 사용시 화학 용출 위험."

    - id: "qa_m004"
      material: "HDPE (고밀도 폴리에틸렌)"
      full_name: "High-Density Polyethylene"

      properties:
        strength: "PE보다 2-3배 강함"
        chemical_resistance: "산 저항 우수"
        cost: "PE보다 20-30% 비쌈"

      qa_items:
        - q: "HDPE는 화학약품 저장에 좋나?"
          a: "네, HDPE는 강산 저장에 우수. PP와 함께 권장."

    # ─── PEEK, TPE 등 특수 재질 (2개) ───
    - id: "qa_m005"
      material: "PEEK (폴리에테르 에테르 케톤)"
      properties:
        heat_resistance: "극고온 (200°C+)"
        cost: "매우 비쌈"
        use: "산업 초고온 환경"

      qa_items:
        - q: "PEEK는 언제 사용하나?"
          a: "극고온 산업용 (200°C+). 매우 고가이므로 필요할 때만 사용."
```

### 2. 일반 품질 문제 해결 (25개 항목)

```yaml
  quality_issues:

    # ─── 변색 문제 (5개) ───
    - id: "qa_q001"
      issue: "용기 갈색/황색 변색"
      synonyms: ["색이 변했어", "누렇다", "색상 변화"]

      causes:
        - cause: "UV 노출"
          symptom: "갈색 또는 황색"
          duration: "2-3개월 내"
          affected_materials: ["PE", "PP"]
          solution: "어두운 곳 보관 또는 검은색/파란색 용기 사용"

        - cause: "화학 반응"
          symptom: "국부적 변색"
          material_affected: ["PE", "PP"]
          solution: "해당 화학물질 저항성 재질 확인"

      prevention: "UV 차단 처리된 용기 사용 (BLUE/BLACK 라인)"

    - id: "qa_q002"
      issue: "용기에서 냄새 발생"
      synonyms: ["이상 냄새", "화학 냄새", "플라스틱 냄새"]

      causes:
        - cause: "화학 용출"
          symptom: "강한 화학 냄새"
          risk: "식품 오염"
          solution: "용기 교체 필수"

        - cause: "보관 제품 냄새"
          symptom: "약한 냄새"
          solution: "실온 보관, 통풍"

      qa_items:
        - q: "새 용기에서 냄새나면?"
          a: "정상. 며칠 통풍하면 사라짐. 강한 화학 냄새면 교체."

    - id: "qa_q003"
      issue: "용기 투명도 저하"
      synonyms: ["흐려졌다", "투명도 감소", "뿌였다"]

      causes:
        - cause: "미세 스크래치"
          symptom: "표면이 뿌였다"
          solution: "사용에 무해. 외형상 문제만 있음"

        - cause: "미세 균열"
          symptom: "자주색 줄무늬"
          risk: "누수 위험"
          solution: "용기 교체"

      qa_items:
        - q: "용기가 뿌옇게 변했는데?"
          a: "표면 스크래치일 가능성 높음. 기능상 무해. 교체 필수 아님."

    # ─── 취약성/강도 문제 (5개) ───
    - id: "qa_q004"
      issue: "용기 깨지거나 부러짐"
      synonyms: ["깨진다", "부러진다", "자꾸 깨진다"]

      causes:
        - cause: "저온 노출"
          temp_range: "-10°C 이하"
          explanation: "저온에서 플라스틱 분자 이동성 감소, 취약"
          solution: "15-25°C 상온 보관"
          materials_affected: ["PE (심함)", "PET"]

        - cause: "UV 손상"
          symptom: "외부 깨짐"
          solution: "어두운 곳 보관"

        - cause: "충격"
          solution: "충격 방지, PP 용기로 업그레이드"

      qa_items:
        - q: "겨울에 용기가 자주 깨진다?"
          a: "저온 취약성. 실내 보관 또는 PP 용기 사용 추천."

    - id: "qa_q005"
      issue: "용기 변형/수축"
      synonyms: ["모양이 변했다", "찌그러졌다"]

      causes:
        - cause: "고온 노출"
          materials: ["PE (심함)", "PET"]
          solution: "상온 보관 또는 내열성 재질 (PP) 사용"

        - cause: "압력"
          solution: "외부 압력 제거"

      qa_items:
        - q: "뜨거운 물을 담으면 용기 변형된다?"
          a: "PE는 50-70°C에서 변형 시작. PP 용기 권장."

    # ─── 누수 문제 (4개) ───
    - id: "qa_q006"
      issue: "용기에서 누수"
      synonyms: ["새는데", "샜다", "물이 새온다"]

      causes:
        - cause: "뚜껑 밀폐 불충분"
          solution: "뚜껑 교체 또는 올바른 조임"

        - cause: "미세 균열"
          symptom: "아주 천천히 누수"
          solution: "용기 교체 필수"

        - cause: "고온 변형"
          solution: "적절한 온도 저장, 내열 용기 사용"

      qa_items:
        - q: "뚜껑은 닫혔는데 계속 새는데?"
          a: "뚜껑 교체 시도. 계속 새면 몸체 균열 가능 → 용기 교체."

    # ─── 강도/파손 문제 (3개) ───
    - id: "qa_q007"
      issue: "용기 강도 부족"
      synonyms: ["약하다", "약해졌다", "쉽게 깨진다"]

      materials_comparison:
        strongest: "PP, HDPE"
        medium: "PET"
        weakest: "PE"

      qa_items:
        - q: "가장 강한 용기는?"
          a: "PP와 HDPE가 가장 강함. PE는 약한 편."

    # ─── 화학 저항성 문제 (3개) ───
    - id: "qa_q008"
      issue: "화학 저항성 / 용해"
      synonyms: ["녹았다", "손상됐다", "화학에 약하다"]

      compatibility_matrix:
        PE:
          safe: ["산", "약알칼리"]
          unsafe: ["강알칼리", "유기용제"]

        PP:
          safe: ["산", "알칼리"]
          unsafe: ["강산", "일부 유기용제"]

        PET:
          safe: ["산", "알칼리 (약)"]
          unsafe: ["유기용제 대부분"]

      qa_items:
        - q: "아세톤을 담을 수 있는 용기?"
          a: "아니요. 아세톤은 PE/PP/PET 모두 손상. 특수 코팅 용기만 가능."

    - id: "qa_q009"
      issue: "산/알칼리 손상"
      acids: ["황산", "염산", "질산"]
      bases: ["수산화나트륨", "암모니아"]

      qa_items:
        - q: "황산(진한)을 담을 수 있는 용기?"
          a: "HDPE 또는 특수 코팅 필수. 일반 PE/PP는 손상."
```

### 3. MSDS/규제 정보 (15개 항목)

```yaml
  msds_compliance:

    # ─── 식품 저장 규제 ───
    - id: "qa_s001"
      question: "뜨거운 음식을 용기에 담아도 되나?"
      answer: "재질별 다름. PE: 70°C까지 안전, PP: 100°C까지 안전, PET: 85°C까지"
      regulation: "FDA CFR 177"
      risk: "80°C+ 시 BPA 등 유해 물질 용출 가능"

    - id: "qa_s002"
      question: "용기를 전자레인지 사용 가능?"
      answer: "대부분의 플라스틱은 불가. PP만 제한적 가능. 확인 표시 필수"
      risk: "고온에서 화학 용출, 용기 변형"

    - id: "qa_s003"
      question: "식품용 용기의 안전 조건?"
      answer: "FDA 승인 / NSF 인증 / 식품용 표시 필수"
      standards: ["FDA CFR 177", "NSF/ANSI 51"]

    # ─── 화학약품 저장 규제 ───
    - id: "qa_s004"
      question: "산을 저장할 때 안전한 용기?"
      answer: "HDPE 최우선, PP 차선. PE는 부식 위험"
      regulation: "OSHA 1910.106"

    - id: "qa_s005"
      question: "유독성 물질 저장 용기 규정?"
      answer: "밀폐 용기 필수, 위험 표시 필수, 정기 검사 필수"
      standard: "OSHA 규정"

    # ─── 의약품 저장 ───
    - id: "qa_s006"
      question: "의약품을 담을 수 있는 용기?"
      answer: "의약품 인증 PE 또는 PET. 갈색/자주색 차광 처리"
      regulation: "식약처 기준"

    - id: "qa_s007"
      question: "어린이 안전 용기?"
      answer: "아이-안전 뚜껑, 유해 화학물질 무함유 필수"
      standards: ["Consumer Product Safety Commission"]

    # ─── 재활용/환경 ───
    - id: "qa_s008"
      question: "플라스틱 용기 재활용 가능한가?"
      answer: "재질별로 다름. PE/PP/PET는 대부분 재활용 가능"
      recycling_codes:
        PE: "2 또는 4"
        PP: "5"
        PET: "1"

```

**상태**: 품질/재질 Q&A 사전 ~7000토큰 완료
**다음**: Part 4에서 산업용어 사전 + 통합 안내

