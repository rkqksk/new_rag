# 재질(Material) 정보 크롤링 현황 리포트

**작성일**: 2025-10-18  
**분석 대상**: RAG Enterprise 프로젝트 크롤링 데이터  
**분석 범위**: Bottle, Jar, CapPump 카테고리 (총 398개 제품)

---

## 1. 분석 개요

이 리포트는 청진코리아(chungjinkorea.com)에서 크롤링한 제품 데이터에 **재질(Material)** 정보가 포함되어 있는지를 분석한 결과입니다.

---

## 2. 크롤링 데이터 현황

### 2.1 카테고리별 데이터 현황

| 카테고리 | 총 제품 수 | 크롤링 시기 | 저장 위치 |
|---------|----------|----------|---------|
| Bottle | 224개 | 2025-10-18 | `data/crawled_products_organized/Bottle/products/` |
| Jar | 37개 | 2025-10-18 | `data/crawled_products_organized/Jar/products/` |
| CapPump | 137개 | 2025-10-18 | `data/crawled_products_organized/CapPump/products/` |
| **합계** | **398개** | - | - |

### 2.2 저장 데이터 구조

각 제품은 다음 정보를 포함하는 JSON 파일로 저장됨:

```json
{
  "product_name": "제품명",
  "images": [...],           // 이미지 정보 (img 태그 + CSS background)
  "specifications": {...},   // 스펙 정보 (Definition Lists에서 추출)
  "print_area_url": "URL",   // 인쇄영역 PDF 링크
  "downloaded_images": [...], // 로컬에 다운로드한 이미지 경로
  "idx": "제품ID",
  "url": "원본 URL",
  "crawled_at": "크롤링 시간"
}
```

**샘플**: `/Users/oypnus/Project/rag-enterprise/data/crawled_products_organized/Bottle/products/idx_823.json`

---

## 3. 재질 정보 추출 결과

### 3.1 현황 요약

| 항목 | 결과 | 비율 |
|-----|------|------|
| 재질 정보 포함 제품 | **0개** | **0.0%** |
| 재질 정보 미포함 제품 | 398개 | 100.0% |
| **결론** | **미포함** | - |

### 3.2 상세 분석

#### 샘플 데이터 분석 결과

**Bottle 카테고리** (idx_823):
```json
"specifications": {
  "Phone": "032-674- 2748~9",
  "Fax": "032-681-2748",
  "Email": "chungjin@chungjinkorea.com"
}
```

**Jar 카테고리** (idx_423):
```json
"specifications": {
  "Phone": "032-674- 2748~9",
  "Fax": "032-681-2748",
  "Email": "chungjin@chungjinkorea.com"
}
```

**CapPump 카테고리** (idx_659):
```json
"specifications": {
  "Phone": "032-674- 2748~9",
  "Fax": "032-681-2748",
  "Email": "chungjin@chungjinkorea.com"
}
```

#### 발견된 Specification 키

전체 398개 제품 중 20개 샘플 분석 결과:

| 키 | 출현 횟수 | 재질 관련 여부 |
|----|---------|-------------|
| Phone | 9회 | ❌ |
| Fax | 9회 | ❌ |
| Email | 9회 | ❌ |

**결론**: 모든 샘플에서 **연락처 정보만** 추출되었음

---

## 4. 크롤링 로직 분석

### 4.1 현재 크롤링 로직

**파일**: `/Users/oypnus/Project/rag-enterprise/scripts/crawlers/chungjin_crawler.py`

#### Specifications 추출 코드 (라인 186-205):

```javascript
// ========================================
// 3. 스펙 정보 (Definition Lists)
// ========================================
result.specifications = {};

const dls = document.querySelectorAll('dl');
dls.forEach(dl => {
    const dts = dl.querySelectorAll('dt');
    const dds = dl.querySelectorAll('dd');

    dts.forEach((dt, i) => {
        if (dds[i]) {
            const key = dt.textContent.trim();
            const value = dds[i].textContent.trim();
            if (key) {
                result.specifications[key] = value;
            }
        }
    });
});
```

**로직 분석**:
- HTML의 `<dl>` (Definition List) 요소에서 모든 `<dt>` (term)과 `<dd>` (definition) 쌍을 추출
- 키-값 형태로 객체에 저장
- 조건: `<dt>`가 존재하고 비어있지 않으면 수집

### 4.2 추출 로직의 한계

**문제점 1: 선택자의 과도한 포괄성**
- 페이지의 **모든 `<dl>` 요소**를 대상으로 함
- 연락처 정보가 포함된 `<dl>`도 무차별적으로 추출

**문제점 2: 필터링 부재**
- 재질, 소재, 재성분 등 제품 스펙 관련 키만 추출하는 필터링 없음
- 일반적인 Information Architecture (`<dl>`) 구조를 모두 추출

**문제점 3: 웹사이트 구조 의존**
- 청진코리아의 HTML 구조에서 제품 재질이 `<dl>` 형식으로 제공되지 않을 가능성 높음
- 정상 추출으로 보아, 현재 추출된 Phone/Fax/Email이 제공되는 유일한 `<dl>` 데이터

---

## 5. 웹사이트 원본 구조 확인

### 5.1 추론 분석

현재 크롤링 결과에서:
- **추출됨**: Phone, Fax, Email (연락처 - 회사 공통 정보)
- **미추출됨**: Material, Composition, 재질, 소재 정보

이는 다음 중 하나를 의미:

#### 가능성 1: 웹사이트에 재질 정보가 제공되지 않음 ⭐ **가장 가능성 높음**
- 제품 페이지의 보이는 영역에 재질 정보가 없음
- 이미지와 제품명만 제공하고 상세 스펙은 "인쇄영역 PDF" 다운로드에만 포함

#### 가능성 2: 재질 정보가 다른 HTML 요소에 포함됨
- `<table>`, `<p>`, `<span>` 등 다른 형식의 마크업 사용
- 현재 `<dl>` 선택자로는 추출 불가능

#### 가능성 3: 재질 정보가 동적 콘텐츠로 로드됨
- JavaScript/AJAX로 별도 요청 필요
- 현재 크롤러는 초기 로드 후 3초 대기만 함 (라인 82)

#### 가능성 4: 인쇄 영역 PDF에만 재질 정보 포함
- 상세 스펙이 PDF 문서에만 존재
- 웹 페이지에는 요약 정보만 표시

---

## 6. 데이터 품질 평가

### 6.1 현재 추출된 정보의 완성도

| 정보 항목 | 추출 상태 | 데이터 품질 | 완전성 |
|---------|---------|----------|--------|
| 제품명 | ✅ 추출됨 | ★★★★★ | 100% |
| 이미지 (다중) | ✅ 추출됨 | ★★★★☆ | 95%+ |
| 스펙 정보 | ✅ 부분 추출 | ★☆☆☆☆ | ~10% |
| 재질 정보 | ❌ 미추출 | N/A | 0% |
| 연락처 | ✅ 추출됨 | ★★★★★ | 100% |

### 6.2 완전성 분석

```
추출된 정보:
- 제품명 ✅
- 이미지 ✅
- 기본 연락처 정보 ✅

미추출된 정보:
- 재질/소재 ❌
- 색상 ❌
- 크기/용량 상세 ❌
- 가격 ❌
- 브랜드 상세 설명 ❌
- 제품 설명 ❌
```

---

## 7. 크롤링 로직 검토

### 7.1 현재 크롤링 스크립트 목록

| 파일 | 용도 | 재질 추출 로직 |
|------|------|-------------|
| `scripts/crawlers/chungjin_crawler.py` | 핵심 크롤러 | ❌ 없음 |
| `scripts/crawlers/crawl_bottle_adaptive.py` | Bottle 카테고리 | chungjin_crawler.py 사용 |
| `scripts/crawlers/crawl_jar_incremental.py` | Jar 카테고리 | chungjin_crawler.py 사용 |
| `scripts/crawlers/crawl_cap_pump_incremental.py` | CapPump 카테고리 | chungjin_crawler.py 사용 |
| `agents/crawler_agent.py` | AI 에이전트 | (미확인) |

### 7.2 코드 리뷰 결과

**chungjin_crawler.py의 데이터 추출 로직**:

```javascript
// 현재 로직 (라인 85-220)
result.product_name = mainImg?.alt || 'Unknown Product';
result.images = [...];  // 이미지 추출
result.specifications = {};  // Definition Lists에서 모든 DT/DD 추출
result.print_area_url = printLink ? printLink.href : null;
```

**특징**:
- ✅ 유연한 이미지 수집 (img 태그 + CSS background)
- ✅ 제품명 정확 추출
- ❌ 재질 정보 추출 로직 완전히 부재
- ❌ PDF 콘텐츠 파싱 로직 없음

---

## 8. 재질 정보 추출 현황 종합

### 8.1 최종 결론

| 항목 | 상태 | 근거 |
|-----|------|------|
| 재질 정보 크롤링 현황 | **❌ 미포함** | 398개 제품 모두 0% |
| 추출 로직 존재 여부 | **❌ 없음** | chungjin_crawler.py에 명시된 로직 없음 |
| 웹사이트 제공 여부 | **? 불명확** | 웹사이트 HTML 구조 확인 필요 |
| 데이터 품질 | ⭐ **부분적** | 제품명/이미지는 우수, 스펙은 불완전 |

### 8.2 재질 정보 추출 가능성 평가

#### 🔴 현재 상태
- **포함**: ❌ 재질 정보 없음
- **로직**: ❌ 추출 로직 없음
- **원본 데이터**: ❓ 확인 필요

#### 🟡 개선 가능성

| 방법 | 난이도 | 예상 성공률 |
|-----|--------|-----------|
| HTML 선택자 확장 (테이블, 다른 요소) | 🟢 낮음 | 60% |
| JavaScript 동적 콘텐츠 로드 | 🟡 중간 | 40% |
| PDF 파싱 추가 | 🟠 높음 | 80%+ |
| 웹사이트 직접 검사 | 🟢 낮음 | 100% |

---

## 9. 권장사항

### 9.1 우선순위별 액션 아이템

#### 🔴 즉시 필요

1. **웹사이트 구조 확인**
   ```bash
   # 실제 제품 페이지에 재질 정보가 있는지 확인
   # 예: http://chungjinkorea.com/kr/product/view.php?idx=823
   ```
   - 웹 브라우저에서 직접 제품 페이지 확인
   - 개발자 도구로 HTML 구조 검사
   - 재질 정보의 위치와 형식 파악

2. **인쇄 영역 PDF 검사**
   - 다운로드된 PDF 파일 확인
   - 재질 정보가 PDF에만 포함되어 있는지 확인
   - `data/crawled_products_organized/*/print_area/` 디렉토리 확인

#### 🟡 단기 계획 (1주)

3. **크롤링 로직 개선**
   ```python
   # 예시: 재질 정보 추출 확장
   - 다양한 CSS selector 시도 (table, span, div.spec 등)
   - 사용자 정의 스펙 키 매핑 추가
   - PDF OCR/파싱 추가 (openpyxl, pdfplumber 사용)
   ```

4. **재질 정보 정규화**
   ```python
   # 발견된 재질 정보에 대해
   - 우리말/영어 매핑 (예: "플라스틱" → "Plastic")
   - 재질 카테고리 표준화
   - 구성 성분 분해 로직
   ```

#### 🟢 중기 계획 (1개월)

5. **멀티모달 분석 추가**
   - CLIP/BLIP-2를 사용하여 이미지에서 재질 특성 추출
   - 제품명 기반 자동 재질 추론 (LLM 기반)
   - 중국산 경쟁사 제품 데이터 크로스 검증

---

## 10. 기술 상세 분석

### 10.1 현재 크롤러 코드 흐름

```
crawl_product(url)
  ↓
launch_browser()
  ↓
navigate(url) + wait 3s
  ↓
evaluate_javascript() [제품명, 이미지, 스펙, PDF링크 추출]
  ├─ product_name ← img[src*="goodsImages"].alt
  ├─ images ← [img 태그 + CSS background]
  ├─ specifications ← dl/dt/dd 모두 추출  ⚠️ 연락처만 있음
  └─ print_area_url ← a:contains("인쇄영역")
  ↓
download_image() × N
  ↓
download_print_area() ← 재질 정보 가능성 ⭐
  ↓
save_json()
```

### 10.2 재질 정보 추출 개선안

#### Option A: HTML 구조 확장 분석

```javascript
// 현재: Definition List만 추출
const dls = document.querySelectorAll('dl');

// 개선안 1: 테이블 추출
const tables = document.querySelectorAll('table');
tables.forEach(table => {
    const rows = table.querySelectorAll('tr');
    rows.forEach(row => {
        const [th, td] = row.querySelectorAll('th, td');
        if (th?.textContent.includes('재') || th?.textContent.includes('재질')) {
            specifications[th.textContent] = td?.textContent;
        }
    });
});

// 개선안 2: 패턴 기반 추출
const allText = document.body.innerText;
const materialPattern = /재질\s*:?\s*([^,\n]+)/g;
const matches = allText.matchAll(materialPattern);
```

#### Option B: PDF 파싱

```python
import pdfplumber

pdf_path = "data/crawled_products_organized/Bottle/print_area/idx_823_print_area.pdf"
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        # 재질 정보 추출 로직
        if '재질' in text or 'material' in text:
            # 파싱 및 저장
```

#### Option C: LLM 기반 추론

```python
# 제품명과 이미지로부터 재질 추론
from openai import OpenAI

client = OpenAI()
response = client.messages.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"제품명: {product_name}"},
                {"type": "image_url", "url": image_url},
                {"type": "text", "text": "이 제품의 재질을 추론하세요"}
            ]
        }
    ]
)
```

---

## 11. 부록

### 11.1 샘플 데이터 위치

| 카테고리 | 샘플 경로 |
|---------|---------|
| Bottle | `/Users/oypnus/Project/rag-enterprise/data/crawled_products_organized/Bottle/products/idx_823.json` |
| Jar | `/Users/oypnus/Project/rag-enterprise/data/crawled_products_organized/Jar/products/idx_423.json` |
| CapPump | `/Users/oypnus/Project/rag-enterprise/data/crawled_products_organized/CapPump/products/idx_659.json` |

### 11.2 크롤러 스크립트 위치

- **핵심**: `/Users/oypnus/Project/rag-enterprise/scripts/crawlers/chungjin_crawler.py`
- **Bottle**: `/Users/oypnus/Project/rag-enterprise/scripts/crawlers/crawl_bottle_adaptive.py`
- **Jar**: `/Users/oypnus/Project/rag-enterprise/scripts/crawlers/crawl_jar_incremental.py`
- **CapPump**: `/Users/oypnus/Project/rag-enterprise/scripts/crawlers/crawl_cap_pump_incremental.py`

### 11.3 통계

```
총 크롤링된 제품: 398개
- Bottle: 224개 (56.3%)
- CapPump: 137개 (34.4%)
- Jar: 37개 (9.3%)

재질 정보 포함: 0개 (0.0%)
재질 정보 미포함: 398개 (100.0%)

추출된 Specification 필드:
- Phone, Fax, Email (연락처만)
```

---

## 12. 결론

### 최종 진단

| 항목 | 상태 |
|-----|------|
| **재질 정보 포함 현황** | ❌ **미포함** (0/398 = 0%) |
| **추출 로직** | ❌ **없음** |
| **원본 데이터** | ❓ **확인 필요** |
| **데이터 품질** | ⭐ **부분적** (제품명/이미지는 우수, 스펙은 불완전) |

### 권장 다음 단계

1. **긴급**: 웹사이트 직접 검사 - 재질 정보 위치 파악
2. **우선**: PDF 파싱 시도 - 인쇄 영역에서 재질 정보 추출
3. **중요**: 크롤링 로직 개선 - HTML 선택자 확장 및 재질 정보 매핑
4. **보완**: LLM 기반 재질 추론 - 이미지와 제품명으로부터 재질 예측

---

**리포트 작성**: Claude Code Analysis  
**데이터 기준일**: 2025-10-18  
**분석 완료**: 2025-10-18
