# 제품 페이지 크롤러 사용 가이드

Google DevTools MCP 기반 구조화된 제품 데이터 추출 시스템

## 📋 개요

이 크롤러는 제품 페이지에서 다음 정보를 자동으로 추출하고 저장합니다:

- ✅ **제품 이미지** (자동 다운로드)
- ✅ **인쇄영역 PDF** (자동 다운로드)
- ✅ **제품 정보** (제품명, 코드, 재질, 사양)
- ✅ **구조화된 JSON 데이터**

## 🚀 빠른 시작

### 1. 기본 사용법

```python
from mcp_servers.google_devtools.product_crawler import ProductPageCrawler

# 크롤러 초기화
crawler = ProductPageCrawler(output_dir="data/crawled_products")

# 단일 제품 페이지 크롤링
result = await crawler.crawl_product_page(
    url="http://chungjinkorea.com/kr/product/view.php?idx=224"
)

print(result)
```

### 2. 여러 제품 일괄 크롤링

```python
urls = [
    "http://chungjinkorea.com/kr/product/view.php?idx=224",
    "http://chungjinkorea.com/kr/product/view.php?idx=777",
    # 추가 URL...
]

summary = await crawler.crawl_multiple_products(urls)
print(f"성공: {summary['success']}, 실패: {summary['error']}")
```

## 📁 출력 구조

```
data/crawled_products/
├── images/                      # 제품 이미지
│   └── product_logo.png
├── files/                       # 인쇄영역 PDF
│   ├── printarea_20251017_233401.pdf
│   └── printarea_20251017_233433.pdf
├── BT400-R005.json             # 제품 데이터 (제품 코드 기준)
├── JP450-GM01.json
└── crawl_summary_*.json        # 일괄 크롤링 요약
```

## 📊 JSON 데이터 형식

```json
{
  "product_name": "400ml 브로우용기",
  "image_url": "http://chungjinkorea.com/data/goodsImages/GOODS1_*.jpg",
  "image_alt": "400ml 브로우용기",
  "print_area_url": "http://chungjinkorea.com/bbs/goods_download.php?download=1&idx=224",
  "specifications": {
    "제품명": "400ml 브로우용기",
    "제품 코드": "BT400-R005",
    "재질(원료)": "PET",
    "사양": "61x177(mm)/Ø24"
  },
  "local_image_path": "data/crawled_products/images/product_BT400-R005.jpg",
  "local_printarea_path": "data/crawled_products/files/printarea_BT400-R005.pdf",
  "source_url": "http://chungjinkorea.com/kr/product/view.php?idx=224",
  "page_title": "제품소개 - 제품소개 - 청진",
  "crawled_at": "2025-10-17T23:34:34.113206"
}
```

## 🎯 다른 사이트 적용 방법

### 사이트별 설정 (site_config)

```python
# 예시: 다른 사이트를 위한 커스텀 설정
custom_config = {
    "name": "커스텀 사이트",
    "selectors": {
        "image": "img.product-image",              # 제품 이미지 셀렉터
        "download": "a.download-link",             # 다운로드 링크 셀렉터
        "features": ".specs-table tr",             # 제품 정보 셀렉터
        "product_name": "h1.product-title"         # 제품명 셀렉터
    }
}

# 커스텀 설정으로 크롤링
result = await crawler.crawl_product_page(
    url="https://example.com/product/123",
    site_config=custom_config
)
```

### CSS 셀렉터 찾는 방법

1. **브라우저 개발자 도구** (F12) 열기
2. **Elements** 탭에서 원하는 요소 선택
3. 우클릭 → **Copy** → **Copy selector**
4. 복사한 셀렉터를 `site_config`에 추가

## 🔧 고급 사용법

### 1. 헤드리스 모드 제어

```python
# DevToolsAutomation 클래스 수정
await automation.launch_browser(
    headless=True,          # True: 백그라운드, False: UI 표시
    browser_type="webkit"   # webkit (권장), chromium, firefox
)
```

### 2. 타임아웃 설정

```python
# server.py에서 navigate 메서드 타임아웃 조정
await automation.navigate(
    url=url,
    wait_until="networkidle",  # load, domcontentloaded, networkidle
    timeout=30000              # 밀리초 (기본: 30초)
)
```

### 3. 재시도 로직

`server.py`의 `retry_attempts` 변수 조정:
```python
class DevToolsAutomation:
    def __init__(self):
        self.retry_attempts = 3  # 실패 시 재시도 횟수
```

## 📝 실전 예시

### 청진코리아 전체 제품 크롤링

```python
import asyncio
from mcp_servers.google_devtools.product_crawler import ProductPageCrawler

async def crawl_all_chungjin_products():
    """청진코리아 전체 제품 크롤링"""

    # 제품 ID 범위 (실제 범위는 사이트 확인 필요)
    base_url = "http://chungjinkorea.com/kr/product/view.php?idx="
    product_ids = range(200, 800)  # 예시: 200~800

    urls = [f"{base_url}{idx}" for idx in product_ids]

    crawler = ProductPageCrawler(output_dir="data/chungjin_products")
    summary = await crawler.crawl_multiple_products(urls)

    print(f"✅ 총 {summary['success']}개 제품 크롤링 완료")
    print(f"❌ {summary['error']}개 실패")

    return summary

# 실행
asyncio.run(crawl_all_chungjin_products())
```

### RAG 시스템 연동

```python
async def crawl_and_index_to_rag(url: str):
    """크롤링 후 RAG 벡터 DB에 인덱싱"""

    # 1. 제품 데이터 크롤링
    crawler = ProductPageCrawler()
    result = await crawler.crawl_product_page(url)

    if result['status'] != 'success':
        return

    product_data = result['product_data']

    # 2. 벡터화용 텍스트 생성
    text_for_embedding = f"""
    제품명: {product_data['product_name']}
    제품 코드: {product_data['specifications'].get('제품 코드', 'N/A')}
    재질: {product_data['specifications'].get('재질(원료)', 'N/A')}
    사양: {product_data['specifications'].get('사양', 'N/A')}
    """

    # 3. Qdrant에 저장 (예시)
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer

    client = QdrantClient(url="http://localhost:6333")
    encoder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    vector = encoder.encode(text_for_embedding)

    client.upsert(
        collection_name="products",
        points=[{
            "id": product_data['specifications'].get('제품 코드'),
            "vector": vector.tolist(),
            "payload": product_data
        }]
    )

    print(f"✅ {product_data['product_name']} 인덱싱 완료")
```

## 🛠️ 트러블슈팅

### 문제 1: 브라우저 크래시 (macOS)

**증상**: `SIGTRAP` 에러로 Chromium 크래시

**해결책**: WebKit 사용
```python
await automation.launch_browser(browser_type="webkit")  # 기본값
```

### 문제 2: 이미지/파일 다운로드 실패

**원인**: URL이 잘못되었거나 접근 권한 없음

**해결책**:
1. 브라우저에서 직접 다운로드 가능한지 확인
2. 로그인 필요한 경우 쿠키 설정 추가

### 문제 3: CSS 셀렉터가 데이터를 못 찾음

**원인**: 사이트 구조가 다름

**해결책**:
1. F12 개발자 도구로 실제 HTML 구조 확인
2. `site_config`에서 정확한 셀렉터 지정

## 📚 참고 자료

- **Google DevTools MCP**: `mcp_servers/google_devtools/server.py`
- **Playwright 문서**: https://playwright.dev/python/
- **CSS 셀렉터 가이드**: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors

## 🔄 업데이트 로그

- **v1.0** (2025-10-17): 초기 버전 - 청진코리아 사이트 지원
  - 제품 이미지/파일 자동 다운로드
  - JSON 구조화 저장
  - 일괄 크롤링 지원
  - WebKit 브라우저 기본 적용 (macOS 호환)

---

**문의**: RAG Enterprise Team
**라이센스**: Internal Use Only
