# 엔터프라이즈 웹 크롤링 프레임워크 v1.0

## 개요

청진코리아 사이트 크롤링을 통해 개발한 재사용 가능한 크롤링 프레임워크.
**핵심 가치**: AJAX 페이지네이션, 멀티모달 데이터 수집, 에러 복구 로직을 일반화하여 다양한 사이트에 적용 가능

---

## 🎯 개발 과정에서 발견한 핵심 패턴

### Phase 1: 기본 크롤링 (8개 샘플 제품)
**목표**: 단일 제품 페이지 완벽 크롤링

**발견한 패턴**:
1. **멀티소스 이미지 추출**
   - `<img>` 태그 (명시적)
   - CSS `background-image` (암시적)
   - 중복 제거 및 우선순위 정렬 필요

2. **Definition List 스펙 파싱**
   - `<dl>/<dt>/<dd>` 구조가 제품 스펙의 표준
   - Key-Value 매핑으로 구조화

3. **파일명 기반 이미지 분류**
   - GOODS1 = 메인 이미지
   - ADD_GOODS1/2/3 = 추가 이미지
   - 파일명 패턴으로 타입 자동 감지

**성과**: 8/8 제품 100% 성공

---

### Phase 2: 기본 페이지네이션 (Jar 카테고리, 4페이지)
**목표**: 단순 페이지 번호 클릭 방식 페이지네이션 처리

**발견한 패턴**:
1. **AJAX 기반 페이지 전환**
   - URL 변경 없이 JavaScript `onclick`으로 페이지 전환
   - DOM 업데이트 대기 시간 필요 (3-5초)

2. **제품 URL 수집 후 크롤링 2단계 전략**
   - Stage 1: 모든 페이지에서 URL 수집
   - Stage 2: 수집된 URL로 제품 크롤링
   - 메모리 효율적이고 재시도 가능

**성과**: 37/37 제품 100% 성공

---

### Phase 3: 그룹 페이지네이션 (Cap&Pump, 14페이지)
**목표**: 5개씩 묶인 페이지 그룹 + paging-next 버튼 처리

**발견한 패턴**:
1. **그룹화된 페이지 번호 표시**
   - 페이지 1-5만 보임 → paging-next 클릭 → 6-10 보임
   - 14개 페이지를 3개 그룹으로 분할

2. **동적 페이지 범위 탐색**
   ```javascript
   // 현재 보이는 페이지 범위 확인
   const visible_pages = [1, 2, 3, 4, 5]
   const min_page = 1
   const max_page = 5

   // 목표 페이지(예: 11)가 범위 밖이면 paging-next 클릭
   if (target_page > max_page) {
       click_paging_next()
       await sleep(5s)  // AJAX 로딩 대기
   }
   ```

3. **에러 복구: AJAX 지연 대응**
   - 첫 번째 버그: `page < min_page` 시 즉시 실패
   - 해결: 2초 추가 대기 후 재시도 (AJAX 로딩 지연 대응)

**성과**: 137/137 제품 100% 성공

---

### Phase 4: 대규모 크롤링 (Bottle, 68페이지)
**목표**: 14개 그룹, 680개 제품의 안정적 크롤링

**발견한 패턴**:
1. **무한 루프 방지**
   - 최대 시도 횟수 제한 (max_attempts = 20)
   - 각 시도마다 페이지 범위 재확인

2. **점진적 에러 수정**
   - 페이지 11-15, 21-25에서 반복 실패 패턴 발견
   - 로그 분석 → 원인 파악 → 즉시 수정 → 재시작

3. **백그라운드 실행 + 모니터링**
   ```bash
   nohup python crawl.py > crawl.log 2>&1 &
   tail -f crawl.log  # 실시간 모니터링
   grep "페이지.*URL 발견" crawl.log | wc -l  # 진행률 확인
   ```

**예상 성과**: ~680개 제품 (진행 중)

---

## 🏗️ 일반화된 크롤링 아키텍처

### 핵심 컴포넌트

```
┌─────────────────────────────────────────┐
│   BaseCrawler (Abstract Base Class)    │
│  - 브라우저 자동화 (Playwright)         │
│  - 에러 복구 로직                        │
│  - 진행 상태 추적                        │
└─────────────────────────────────────────┘
              ↓ 상속
┌─────────────────────────────────────────┐
│   SiteCrawler (Site-Specific)           │
│  - 페이지네이션 전략 구현                │
│  - 데이터 추출 로직 구현                 │
│  - 사이트별 특수 처리                    │
└─────────────────────────────────────────┘
```

### 추상화된 페이지네이션 전략

```python
class PaginationStrategy(ABC):
    """페이지네이션 전략 인터페이스"""

    @abstractmethod
    async def navigate_to_page(self, page_num: int) -> bool:
        """특정 페이지로 이동"""
        pass

    @abstractmethod
    async def get_total_pages(self) -> int:
        """전체 페이지 수 반환"""
        pass

    @abstractmethod
    async def extract_product_urls(self) -> List[str]:
        """현재 페이지에서 제품 URL 추출"""
        pass


class SimplePagination(PaginationStrategy):
    """기본 페이지 번호 클릭 방식"""
    async def navigate_to_page(self, page_num: int):
        # 페이지 번호 버튼 클릭
        pass


class GroupedPagination(PaginationStrategy):
    """그룹화된 페이지 + paging-next 방식"""
    async def navigate_to_page(self, page_num: int):
        # 1. 현재 보이는 페이지 범위 확인
        # 2. 목표 페이지가 범위 밖이면 paging-next 클릭
        # 3. 반복
        pass


class InfiniteScroll(PaginationStrategy):
    """무한 스크롤 방식"""
    async def navigate_to_page(self, page_num: int):
        # 스크롤 내려서 더 많은 제품 로드
        pass
```

### 추상화된 데이터 추출기

```python
class DataExtractor(ABC):
    """데이터 추출 전략 인터페이스"""

    @abstractmethod
    async def extract_product_name(self) -> str:
        pass

    @abstractmethod
    async def extract_images(self) -> List[Dict]:
        pass

    @abstractmethod
    async def extract_specifications(self) -> Dict[str, str]:
        pass


class ChungjinExtractor(DataExtractor):
    """청진코리아 특화 추출기"""

    async def extract_images(self):
        # img 태그 + CSS background-image
        # 파일명 기반 분류 및 정렬
        pass

    async def extract_specifications(self):
        # Definition List 파싱
        pass


class GenericExtractor(DataExtractor):
    """일반 사이트용 추출기"""

    async def extract_images(self):
        # 기본적인 img 태그만
        pass

    async def extract_specifications(self):
        # table 파싱
        pass
```

---

## 📋 사이트별 크롤링 체크리스트

### Step 1: 사이트 분석 (30분)
- [ ] 페이지네이션 방식 파악
  - [ ] URL 파라미터 방식 (`?page=2`)
  - [ ] AJAX 페이지 전환 (`onclick`)
  - [ ] 그룹화 여부 확인
  - [ ] 무한 스크롤 여부

- [ ] 제품 URL 패턴 파악
  - [ ] 제품 상세 페이지 URL 형식
  - [ ] 고유 ID 위치 (idx, product_id 등)

- [ ] 데이터 구조 분석
  - [ ] 이미지 위치 (img, background-image, data-src 등)
  - [ ] 제품명 위치 (h1, alt, title 등)
  - [ ] 스펙 정보 구조 (dl, table, div 등)

### Step 2: 샘플 크롤링 (1시간)
- [ ] 3-5개 제품 수동 크롤링
- [ ] 데이터 추출 로직 검증
- [ ] 파일 저장 구조 확인
- [ ] 성공률 100% 달성

### Step 3: 페이지네이션 구현 (2시간)
- [ ] 적절한 PaginationStrategy 선택/구현
- [ ] 첫 페이지 크롤링 테스트
- [ ] 전체 페이지 URL 수집 테스트
- [ ] 에러 처리 및 재시도 로직

### Step 4: 전체 크롤링 (N시간)
- [ ] 백그라운드 실행
- [ ] 로그 모니터링
- [ ] 에러 발생 시 즉시 수정
- [ ] CSV 리포트 생성 및 검증

---

## 🛠️ 재사용 가능한 유틸리티

### 1. AJAX 대기 헬퍼

```python
async def wait_for_ajax_complete(
    automation,
    timeout: int = 10,
    interval: float = 0.5
) -> bool:
    """
    AJAX 요청 완료 대기

    Args:
        automation: DevToolsAutomation 인스턴스
        timeout: 최대 대기 시간 (초)
        interval: 체크 간격 (초)

    Returns:
        AJAX 완료 여부
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # jQuery.active 확인 (jQuery 사용 사이트)
        result = await automation.evaluate_javascript("""
            () => {
                if (typeof jQuery !== 'undefined') {
                    return jQuery.active === 0;
                }
                return document.readyState === 'complete';
            }
        """)

        if result.get('status') == 'success' and result.get('result'):
            return True

        await asyncio.sleep(interval)

    return False
```

### 2. 페이지 범위 탐색기

```python
async def find_visible_page_range(automation) -> Dict[str, Any]:
    """
    현재 보이는 페이지 번호 범위 탐색

    Returns:
        {
            'visible_pages': [1, 2, 3, 4, 5],
            'min_page': 1,
            'max_page': 5,
            'has_next': True/False
        }
    """
    result = await automation.evaluate_javascript("""
        () => {
            const pageLinks = Array.from(
                document.querySelectorAll('.paging a, .pagination a')
            );

            const pageNumbers = pageLinks
                .map(a => a.textContent.trim())
                .filter(text => /^\d{1,3}$/.test(text))
                .map(Number)
                .sort((a, b) => a - b);

            const nextButton = document.querySelector(
                '.paging-next, .next, .pagination-next'
            );

            return {
                visible_pages: pageNumbers,
                min_page: Math.min(...pageNumbers),
                max_page: Math.max(...pageNumbers),
                has_next: nextButton && !nextButton.classList.contains('disabled')
            };
        }
    """)

    return result.get('result', {})
```

### 3. 이미지 완전 추출기

```python
async def extract_all_images(automation, filters: List[str] = None) -> List[Dict]:
    """
    모든 이미지 소스 추출 (img + CSS background)

    Args:
        automation: DevToolsAutomation 인스턴스
        filters: URL 필터 (예: ['goodsImages', 'product'])

    Returns:
        [{source, url, type, ...}, ...]
    """
    filter_str = json.dumps(filters or [])

    result = await automation.evaluate_javascript(f"""
        () => {{
            const filters = {filter_str};
            const images = [];

            // 1. img 태그
            document.querySelectorAll('img').forEach(img => {{
                const url = img.src;
                if (filters.length === 0 || filters.some(f => url.includes(f))) {{
                    images.push({{
                        source: 'img',
                        url: url,
                        alt: img.alt || '',
                        width: img.naturalWidth,
                        height: img.naturalHeight
                    }});
                }}
            }});

            // 2. CSS background-image
            document.querySelectorAll('*').forEach(elem => {{
                const bg = window.getComputedStyle(elem).backgroundImage;
                if (bg && bg !== 'none' && bg.includes('url(')) {{
                    const match = bg.match(/url\\(["']?([^"')]+)["']?\\)/);
                    if (match && match[1]) {{
                        const url = match[1];
                        if (filters.length === 0 || filters.some(f => url.includes(f))) {{
                            images.push({{
                                source: 'css',
                                url: url
                            }});
                        }}
                    }}
                }}
            }});

            // 중복 제거
            const seen = new Set();
            return images.filter(img => {{
                if (seen.has(img.url)) return false;
                seen.add(img.url);
                return true;
            }});
        }}
    """)

    return result.get('result', [])
```

---

## 📚 다른 사이트 적용 예시

### 예시 1: 쿠팡 제품 페이지

```python
class CoupangCrawler(BaseCrawler):
    """쿠팡 크롤러"""

    def __init__(self):
        super().__init__()
        self.pagination = InfiniteScroll()  # 무한 스크롤 방식
        self.extractor = CoupangExtractor()

    async def crawl_category(self, category_url: str):
        # 무한 스크롤로 모든 제품 로드
        await self.pagination.scroll_to_bottom()

        # 제품 URL 수집
        product_urls = await self.extractor.extract_product_urls()

        # 제품 크롤링
        for url in product_urls:
            await self.crawl_product(url)


class CoupangExtractor(DataExtractor):
    """쿠팡 데이터 추출기"""

    async def extract_images(self):
        # lazy loading 이미지 처리 (data-src)
        return await self.automation.evaluate_javascript("""
            () => {
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    url: img.dataset.src || img.src
                }));
            }
        """)
```

### 예시 2: 네이버 쇼핑

```python
class NaverShoppingCrawler(BaseCrawler):
    """네이버 쇼핑 크롤러"""

    def __init__(self):
        super().__init__()
        self.pagination = SimplePagination()  # URL 파라미터 방식
        self.extractor = NaverExtractor()

    async def get_category_pages(self, category_url: str):
        # URL 파라미터로 페이지 변경 (?page=N)
        base_url, params = category_url.split('?')

        for page in range(1, max_pages + 1):
            url = f"{base_url}?{params}&page={page}"
            await self.automation.navigate(url)
            await asyncio.sleep(2)

            product_urls = await self.extractor.extract_product_urls()
            yield product_urls
```

---

## 🎓 학습한 핵심 교훈

### 1. 점진적 개발이 핵심
- **작은 성공부터**: 8개 제품 → 37개 → 137개 → 680개
- **패턴 발견**: 각 단계에서 새로운 문제 발견 및 해결
- **즉시 적용**: 발견한 패턴을 즉시 코드에 반영

### 2. 로그와 모니터링의 중요성
```python
logger.info(f"페이지 {page}: {len(urls)}개 URL 발견")
logger.debug(f"현재 그룹: {min_page}-{max_page}")
logger.warning(f"페이지 {page} 버튼 찾기 실패")
```
- 상세한 로그가 문제 진단을 10배 빠르게 만듦
- 백그라운드 실행 시 로그 = 유일한 눈

### 3. 에러 복구 > 에러 방지
- 완벽한 첫 번째 시도는 불가능
- AJAX 지연, 네트워크 타임아웃 등 예상 못한 문제 발생
- **재시도 로직 필수**: `max_attempts`, `sleep`, `fallback`

### 4. 데이터 검증의 중요성
- CSV 리포트로 누락 확인
- 예상 개수 vs 실제 개수 비교
- 카테고리별 분리로 문제 격리

---

## 🚀 다음 단계 로드맵

### Short-term (1-2주)
- [ ] BaseCrawler 추상 클래스 구현
- [ ] 3가지 PaginationStrategy 구현
- [ ] 재사용 유틸리티 라이브러리 패키징

### Mid-term (1-2개월)
- [ ] 5개 이상 다른 사이트 크롤러 구축
- [ ] 크롤러 템플릿 생성기 (CLI 도구)
- [ ] 크롤링 스케줄러 (정기 실행)

### Long-term (3-6개월)
- [ ] 분산 크롤링 시스템 (Celery + Redis)
- [ ] 실시간 변경 감지 및 알림
- [ ] Anti-bot 우회 전략 라이브러리

---

## 📝 결론

청진코리아 크롤링을 통해 얻은 핵심 노하우:

1. **AJAX 페이지네이션 마스터**: 그룹화, 지연, 재시도
2. **멀티모달 추출**: 텍스트 + 이미지 + PDF
3. **점진적 개발**: 샘플 → 카테고리 → 전체
4. **데이터 체계화**: 카테고리별 구조화 + CSV 리포트

이 프레임워크를 기반으로 **어떤 사이트든 2-4시간 내에 크롤러 구축 가능**.

---
*Version: 1.0 | Created: 2025-10-18 | Author: RAG Enterprise Team*
