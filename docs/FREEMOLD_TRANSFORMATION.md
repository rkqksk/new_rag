# Freemold 데이터 변환 가이드

## 개요

Freemold 크롤러는 **크롤링 중 실시간으로 데이터를 Onehago 표준 구조로 변환**하여 저장합니다.

---

## 표준 구조 (Onehago 기준)

### 18개 필수 필드

| 필드 | 타입 | 설명 | Freemold 매핑 |
|------|------|------|---------------|
| `product_id` | str | 제품 고유 ID | `pIdx` |
| `company_no` | str | 회사 번호 | `mIdx` |
| `category_id` | str | 카테고리 ID | `category_code` |
| `category_name` | str | 카테고리 명 | `category_name` |
| `product_name` | str | 제품명 | 테이블 추출 |
| `detailed_name` | str | 상세 제품명 | `product_name` 복사 |
| `moq` | str | 최소 주문량 | 테이블 추출 |
| `detail_url` | str | 상세 페이지 URL | `url` |
| `image_url` | str | 메인 이미지 URL | `main_image` |
| `full_image_url` | str | 전체 이미지 URL | `main_image` 복사 |
| `image_path` | str | 로컬 이미지 경로 | 추후 다운로드 시 설정 |
| `images` | list | 전체 이미지 리스트 | 상세 페이지 추출 |
| `specifications` | **dict** | **사양 정보 (중요!)** | 변환 로직 적용 |
| `manufacturer` | str | 제조사 | specifications에서 추출 |
| `phone` | str | 전화번호 | specifications에서 추출 |
| `fax` | str | 팩스번호 | specifications에서 추출 |
| `email` | str | 이메일 | specifications에서 추출 |
| `contact` | str | 담당자 | specifications에서 추출 |
| `crawled_at` | str | 수집 시각 (ISO 8601) | 자동 생성 |

---

## specifications 구조

### Freemold 원시 데이터 (플랫 구조)

```json
{
  "pIdx": "89037",
  "product_name": "티코스터",
  "specifications": "용량 : -     /     사이즈 : 90*90(mm)",  // ⚠️ String
  "material": "PU",
  "moq": "-",
  "origin": "대한민국",
  "manufacturer": "전화 : 070-7796-9988"
}
```

### 변환 후 (dict 구조)

```json
{
  "product_id": "89037",
  "product_name": "티코스터",
  "specifications": {                                       // ✅ Dict
    "사이즈": "용량 : -     /     사이즈 : 90*90(mm)",
    "재질": "PU",
    "MOQ": "-",
    "원산지": "대한민국",
    "제조사": "전화 : 070-7796-9988"
  },
  "manufacturer": "전화 : 070-7796-9988",
  // ... 나머지 표준 필드들
}
```

---

## 변환 로직

### 크롤러 내 변환 함수 (`transform_to_standard`)

**위치**: `scripts/crawl_freemold_manual.py` (89-127행)

```python
def transform_to_standard(self, raw_product):
    """원시 데이터를 Onehago 표준 구조로 즉시 변환"""
    # 1. specifications dict 생성
    specs_dict = {}

    if raw_product.get('specifications'):
        specs_dict['사이즈'] = raw_product['specifications']
    if raw_product.get('material'):
        specs_dict['재질'] = raw_product['material']
    if raw_product.get('moq'):
        specs_dict['MOQ'] = raw_product['moq']
    if raw_product.get('origin'):
        specs_dict['원산지'] = raw_product['origin']
    if raw_product.get('manufacturer'):
        specs_dict['제조사'] = raw_product['manufacturer']

    # 2. 표준 구조로 변환
    return {
        'product_id': raw_product.get('pIdx', ''),
        'company_no': raw_product.get('mIdx', ''),
        'category_id': raw_product.get('category_code', ''),
        'category_name': raw_product.get('category_name', ''),
        'product_name': raw_product.get('product_name', ''),
        'detailed_name': raw_product.get('product_name', ''),
        'moq': raw_product.get('moq', ''),
        'detail_url': raw_product.get('url', ''),
        'image_url': raw_product.get('main_image', ''),
        'full_image_url': raw_product.get('main_image', ''),
        'image_path': '',
        'images': raw_product.get('images', []),
        'specifications': specs_dict,  # ✅ dict 타입
        'manufacturer': specs_dict.get('제조사', ''),
        'phone': '',
        'fax': '',
        'email': '',
        'contact': '',
        'crawled_at': raw_product.get('crawled_at', datetime.now().isoformat())
    }
```

### 호출 시점

**위치**: `scripts/crawl_freemold_manual.py` (216행)

```python
def extract_detail(self, driver, product):
    # ... 데이터 추출 로직

    result = {
        'pIdx': pIdx,
        'product_name': '...',
        'specifications': '...',  # String
        # ... 원시 데이터
    }

    # ✅ 즉시 변환하여 반환
    return self.transform_to_standard(result)
```

---

## 검증 방법

### 1. 구조 검증 스크립트

```bash
python3 << 'EOF'
import json
from pathlib import Path

# Onehago 표준
onehago_file = Path('data/onehago/test_clean/all_products_clean.json')
with open(onehago_file, 'r', encoding='utf-8') as f:
    onehago_data = json.load(f)
onehago_fields = set(onehago_data[0].keys())

# Freemold 변환 데이터
freemold_file = Path('data/freemold/crawled_v2/products_batch_50.json')
with open(freemold_file, 'r', encoding='utf-8') as f:
    freemold_data = json.load(f)
freemold_fields = set(freemold_data[0].keys())

# 비교
missing = onehago_fields - freemold_fields
extra = freemold_fields - onehago_fields

print(f"✅ Onehago 필드: {len(onehago_fields)}")
print(f"✅ Freemold 필드: {len(freemold_fields)}")
print(f"⚠️  누락: {missing if missing else 'None'}")
print(f"💡 추가: {extra if extra else 'None'}")

# specifications 타입 확인
print(f"\nspecifications 타입:")
print(f"  Onehago: {type(onehago_data[0]['specifications']).__name__}")
print(f"  Freemold: {type(freemold_data[0]['specifications']).__name__}")

if isinstance(freemold_data[0]['specifications'], dict):
    print("  ✅ dict 타입 일치!")
else:
    print("  ❌ dict 타입 불일치!")
EOF
```

### 2. 예상 출력

```
✅ Onehago 필드: 18
✅ Freemold 필드: 19
⚠️  누락: None
💡 추가: {'images'}

specifications 타입:
  Onehago: dict
  Freemold: dict
  ✅ dict 타입 일치!
```

---

## 크롤러 실행

### 수동 로그인 크롤러

```bash
python3 scripts/crawl_freemold_manual.py
```

**특징**:
- 브라우저 창이 열림 → 수동 로그인 필요
- 로그인 후 ENTER 키 입력 → 자동 크롤링 시작
- **크롤링 중 실시간 변환** → 표준 구조로 저장
- 50개마다 배치 저장 → `data/freemold/crawled_v2/products_batch_*.json`
- 진행 상황 추적 → `data/freemold/crawled_v2/crawl_progress_manual.json`

---

## 출력 파일

### 배치 파일 (50개 단위)

```
data/freemold/crawled_v2/products_batch_50.json
data/freemold/crawled_v2/products_batch_100.json
data/freemold/crawled_v2/products_batch_150.json
...
```

### 최종 파일

```
data/freemold/crawled_v2/all_products_detailed.json
```

**포맷**: 모든 제품이 **Onehago 표준 구조**로 변환된 상태로 저장됨

---

## 주요 차이점 (이전 vs 현재)

### ❌ 이전 방식 (2단계 파이프라인)

```
1. 크롤링 → 원시 데이터 저장
2. 변환 스크립트 실행 → 표준 구조 변환
```

**문제점**:
- 2단계 파이프라인 복잡도
- 원시 데이터 관리 오버헤드
- 변환 누락 가능성

### ✅ 현재 방식 (실시간 변환)

```
크롤링 + 변환 → 표준 구조 저장
```

**장점**:
- 백엔드에서 모두 실행 (사용자 요구사항)
- 단일 파이프라인으로 단순화
- 즉시 표준 구조 확보
- 변환 누락 불가능

---

## FAQ

### Q1. Onehago 크롤러도 같은 구조를 사용하나요?

**A**: 네, Onehago 크롤러도 동일한 18개 필드의 표준 구조를 사용합니다.

### Q2. specifications가 dict가 아니면?

**A**: 백엔드 API가 오류를 반환합니다. specifications는 반드시 dict 타입이어야 합니다.

### Q3. 이미지 다운로드는?

**A**: 현재는 URL만 저장합니다. 이미지 다운로드는 별도 스크립트에서 수행합니다.

### Q4. 변환 스크립트(`transform_freemold_to_standard.py`)는?

**A**: 더 이상 필요 없습니다. 크롤러가 실시간으로 변환합니다.

---

## 참고 문서

- [Onehago 표준 데이터 샘플](../data/onehago/test_clean/all_products_clean.json)
- [Freemold 크롤러 코드](../scripts/crawl_freemold_manual.py)
- [변환 검증 샘플](../data/freemold/transformed/products_batch_50_transformed.json)

---

**작성일**: 2025-10-28
**버전**: 1.0 (실시간 변환 방식)
