# 불완전한 데이터 분석 및 보완 방안

## 요약
- 총 제품: 846개
- 불완전한 제품: 191개 (22.6%)
- 완전한 제품: 655개 (77.4%)

---

## 1. Cappump 제품 (135개) - capacity 없음

### 문제
- **누락 필드**: `capacity` (용량)
- **제품 예시**: 
  - idx_659: 24파이 일반펌프
  - idx_675: 32파이 일반펌프
  - idx_726: 20파이 프레스캡

### 원인
펌프와 캡 제품은 **용량(ml/g) 개념이 없습니다**. 대신 **규격(파이)**으로 표시됩니다.
- 예: "24파이 일반펌프" → capacity 개념 없음

### 보완 방법
**Option 1: 규격을 capacity로 매핑 (권장)**
```python
# specifications에 다음 추가
if '파이' in product_name:
    size = extract_number(product_name)  # "24파이" → 24
    specs['capacity'] = f"{size}파이"
```

**Option 2: capacity를 선택적 필드로 변경**
```python
# 검증 로직 수정
if category in ['bottle', 'jar']:
    required_fields.append('capacity')
# cappump는 capacity 불필요
```

**추천**: Option 2 (capacity는 Bottle/Jar만 필수)

---

## 2. Jar 제품 (29개) - pricing 없음

### 문제
- **누락 필드**: `pricing` (가격 정보)
- **제품 예시**:
  - idx_884: 600g 크림용기
  - idx_904: 400g 크림용기
  - idx_788: 500g 크림사출용기

### 원인
가격 엑셀에 **Jar 제품 가격 데이터가 없었을 가능성**

### 보완 방법
**Option 1: 엑셀에서 가격 추가 후 재파싱**
```bash
# 1. 엑셀에 Jar 제품 가격 추가
# 2. 가격 파싱 스크립트 재실행
python scripts/parse_pricing.py
```

**Option 2: 웹사이트에서 직접 크롤링**
```python
# Jar 제품 페이지에서 가격 정보 크롤링
for idx in missing_pricing_jar:
    crawl_price_from_web(idx)
```

**Option 3: 기본 가격 설정**
```python
# Jar 제품에 임시 가격 설정
if not pricing and category == 'jar':
    pricing = {'regular_price': 0, 'note': '가격 문의'}
```

**추천**: Option 1 (정확한 가격 데이터 확보)

---

## 3. Bottle 제품 (25개) - neck_size 없음

### 문제
- **누락 필드**: `neck_size` (입구 크기)
- **제품 예시**:
  - idx_455: 320ml 튜브브로우용기
  - idx_456: 400ml 튜브브로우용기
  - idx_956: 7g 마스카라용기

### 원인
특정 제품은 **웹사이트에 neck_size 정보가 없음**
- 튜브 제품: 입구 크기 미표시
- 마스카라: 특수 제품으로 neck_size 개념 없음

### 보완 방법
**Option 1: 사양(dimensions)에서 추출**
```python
# "38x155(mm)/Ø24" → neck_size: "24파이"
if 'Ø' in dimensions:
    neck_size = extract_diameter(dimensions)
```

**Option 2: neck_size를 선택적 필드로 변경**
```python
# 검증 로직 수정
if product_type not in ['튜브', '마스카라']:
    required_fields.append('neck_size')
```

**Option 3: 기본값 설정**
```python
if not neck_size and category == 'bottle':
    specs['neck_size'] = 'N/A'  # 명시적으로 없음 표시
```

**추천**: Option 1 (dimensions에서 자동 추출)

---

## 4. Material 없음 (95개)

### 문제
- **누락 필드**: `재질(원료)`
- 주로 Cappump 제품에서 발생

### 원인
웹사이트에 재질 정보가 없거나 크롤링 시 누락

### 보완 방법
**Option 1: 웹페이지 재크롤링**
```python
# 재질 정보 다시 크롤링
for idx in missing_material:
    recrawl_material(idx)
```

**Option 2: 카테고리별 기본값**
```python
# 재질이 없으면 카테고리별 기본값
material_defaults = {
    'cappump': 'PP',  # 대부분의 캡/펌프는 PP
    'bottle': 'PET',
    'jar': 'PP'
}
```

**추천**: Option 1 (정확한 재질 데이터)

---

## 보완 우선순위

### 🔴 우선순위 1: 검증 로직 수정 (즉시 가능)
```python
# 카테고리별 필수 필드 구분
required_fields = {
    'bottle': ['capacity', 'material', 'pricing', 'images', 'neck_size'],
    'jar': ['capacity', 'material', 'pricing', 'images'],
    'cappump': ['material', 'pricing', 'images'],  # capacity, neck_size 불필요
}
```
**효과**: Cappump 135개 → 완전한 데이터로 전환

### 🟡 우선순위 2: Dimensions에서 neck_size 자동 추출
```python
# "38x155(mm)/Ø24" → neck_size: "24파이"
def extract_neck_size_from_dimensions(dimensions):
    import re
    match = re.search(r'Ø(\d+)', dimensions)
    if match:
        return f"{match.group(1)}파이"
    return None
```
**효과**: Bottle 20개 추가 완성

### 🟢 우선순위 3: Jar 가격 데이터 추가
- 엑셀에서 가격 추가 후 재파싱
- 또는 웹사이트에서 직접 크롤링

**효과**: Jar 29개 추가 완성

---

## 실행 계획

### Step 1: 검증 로직 수정 (10분)
```bash
# app/api/main.py 수정
# 카테고리별 필수 필드 구분
```

### Step 2: Neck_size 자동 추출 (20분)
```bash
python scripts/extract_neck_from_dimensions.py
```

### Step 3: 재질/가격 데이터 보완 (1시간)
```bash
# Jar 가격 크롤링
python scripts/crawl_jar_pricing.py

# 재질 재크롤링
python scripts/recrawl_materials.py
```

### 예상 결과
- **현재**: 655/846 (77.4%)
- **Step 1 후**: 790/846 (93.4%)
- **Step 2 후**: 810/846 (95.7%)
- **Step 3 후**: 840/846 (99.3%)

---

## 결론

대부분의 "불완전한 데이터"는 **제품 특성상 정상**입니다:
- Cappump는 capacity가 없는 게 정상
- 일부 Bottle은 neck_size가 없는 게 정상

**검증 로직만 수정하면 93.4% 완성도 달성 가능!**
