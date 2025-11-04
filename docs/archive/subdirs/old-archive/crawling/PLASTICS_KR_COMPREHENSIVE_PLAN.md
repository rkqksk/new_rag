# 플라넷뉴스(Plastics.kr) 크롤링 전략 - 종합 계획

**작성일**: 2025-11-01
**목표**: 플라넷뉴스 웹사이트에서 모든 텍스트 기사를 체계적으로 크롤링

---

## 📋 1단계: 현황 분석

### 1.1 웹사이트 구조
- **도메인**: https://www.plastics.kr
- **기사 타입**: 텍스트 뉴스 (이미지 기사 제외)
- **HTML 구조**: DIV 기반 (모던 시맨틱 HTML)
- **인코딩**: UTF-8 (한글 완벽 지원)

### 1.2 카테고리별 페이지 수
| 카테고리 | 구분 코드 | 한글명 | 예상 페이지 수 |
|---------|---------|------|--------------|
| S1N1 | Latest News | 뉴스 | 50+ 페이지 |
| S1N2 | Insights | 인사이트 | ~2 페이지 |
| S1N3 | Opinion | 오피니언 | ~2 페이지 |
| S1N4 | TECH | TECH | ~5 페이지 |

### 1.3 현재 크롤러 상태
- ✅ 기사 목록 페이지 파싱 (listing pages)
- ✅ 페이지네이션 처리 (다음 페이지 감지)
- ⚠️ 기사 상세 페이지 추출 (detail page extraction) - 부분적

---

## 🎯 2단계: 데이터 정제 (Data Cleanup)

### 2.1 기존 데이터 삭제
```bash
# 불완전한 데이터 제거
rm -rf data/plastics_kr/plastic_news_articles.jsonl
rm -rf data/plastics_kr/progress.json
rm -rf data/plastics_kr/crawled_urls.json
rm -rf data/plastics_kr/index.json
rm -rf data/plastics_kr/logs/
```

### 2.2 디렉토리 초기화
```bash
# 깨끗한 상태에서 시작
mkdir -p data/plastics_kr/logs
```

---

## 🔧 3단계: HTML 구조 분석 및 추출 전략

### 3.1 기사 목록 페이지 (List Page)
**URL 패턴**:
```
https://www.plastics.kr/news/articleList.html?sc_section_code=S1N1&view_type=sm&page=1
```

**HTML 구조**:
```html
<div class="item">
  <a class="auto-section">카테고리명</a>
  <a class="auto-titles" href="/news/articleView.html?idxno=XXXX">기사제목</a>
</div>
```

**추출 전략**:
- 선택자: `div.item > a.auto-titles[href*="articleView"]`
- 추출 필드: `href` (기사 상세 URL)
- 필터: `articleView.html` 포함 확인

### 3.2 기사 상세 페이지 (Detail Page)
**URL 패턴**:
```
https://www.plastics.kr/news/articleView.html?idxno=1234
```

**주요 HTML 요소**:
```html
<!-- 제목 -->
<h1 class="title">기사 제목</h1>

<!-- 기사 본문 -->
<div class="content">본문 텍스트</div>

<!-- 작성자 -->
<span class="writer">저자명</span>

<!-- 작성일 -->
<span class="date">2025.01.15</span>
```

**추출 전략**:
1. **제목**: `h1.title` 또는 `h1` (우선순위 순)
2. **본문**: `div.content` 또는 `div#article-content`
3. **작성자**: `span.writer`, `span.author`, 또는 정규식으로 "기자명" 찾기
4. **날짜**: `span.date` 또는 HTML meta 태그에서 추출

---

## 🚀 4단계: 개선된 크롤러 구현

### 4.1 핵심 개선사항

#### 문제 1: 기사 링크 추출 오류
**원인**: 카테고리 링크와 기사 링크 혼동
```python
# 잘못된 방식
link = item.find('a')  # 첫 <a> 태그는 카테고리!

# 올바른 방식
link = item.find('a', class_='auto-titles')
if link and 'articleView' in link.get('href', ''):
    # 추출
```

#### 문제 2: 상세 페이지 파싱 실패
**원인**: HTML 선택자 부정확
```python
# 각 필드별 다중 선택자 시도
def extract_field(soup, selectors):
    for selector_type, selector_value in selectors:
        if selector_type == 'class':
            elem = soup.find(class_=selector_value)
        elif selector_type == 'id':
            elem = soup.find(id=selector_value)
        if elem:
            return elem.get_text(strip=True)
    return None
```

### 4.2 추천 라이브러리
- **BeautifulSoup4**: HTML 파싱
- **requests**: HTTP 요청
- **lxml**: 빠른 파싱
- **dateparser**: 날짜 추출 및 정규화

---

## 📊 5단계: 크롤링 실행 계획

### 5.1 실행 순서
1. **S1N1 (뉴스)**: 50 페이지 - 가장 콘텐츠 많음
2. **S1N4 (TECH)**: 5 페이지 - 기술 관련
3. **S1N2 (인사이트)**: 2 페이지 - 분석 기사
4. **S1N3 (오피니언)**: 2 페이지 - 의견/칼럼

### 5.2 크롤링 설정
```python
CRAWL_CONFIG = {
    'rate_limit': 0.5,           # 초당 요청 수 제한
    'retry_count': 3,            # 실패 재시도
    'timeout': 10,               # 타임아웃 (초)
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept-Language': 'ko-KR,ko;q=0.9'
    }
}
```

### 5.3 데이터 저장 포맷
```json
{
  "title": "기사 제목",
  "content": "기사 본문...",
  "author": "작성자명",
  "date": "2025-01-15T10:30:00",
  "url": "https://www.plastics.kr/news/articleView.html?idxno=1234",
  "category": "S1N1",
  "type": "news_article"
}
```

---

## ✅ 6단계: 검증 및 품질 관리

### 6.1 크롤링 후 검증
```bash
# 1. 파일 존재 여부
ls -lh data/plastics_kr/plastic_news_articles.jsonl

# 2. 라인 수 확인
wc -l data/plastics_kr/plastic_news_articles.jsonl

# 3. 첫 번째 항목 검증
head -1 data/plastics_kr/plastic_news_articles.jsonl | python3 -m json.tool

# 4. 최후 항목 검증
tail -1 data/plastics_kr/plastic_news_articles.jsonl | python3 -m json.tool
```

### 6.2 데이터 품질 지표
| 지표 | 목표 | 확인 방법 |
|-----|------|---------|
| 추출 성공률 | >80% | 추출된 기사 / 발견된 URL |
| 필드 완성도 | >90% | NULL이 아닌 필드 % |
| 중복 제거 | 100% | URL 해시 기반 중복 제거 |
| 인코딩 정확도 | 100% | 한글 텍스트 가독성 |

---

## 📈 7단계: 예상 결과

### 7.1 크롤링 완료 후 통계
```
총 기사 수: ~700-1000 개
총 페이지: 59 페이지
파일 크기: ~50-100 MB
예상 시간: 30-60 분 (rate limiting 포함)
```

### 7.2 생성될 파일
- `plastic_news_articles.jsonl` - 메인 기사 데이터
- `progress.json` - 크롤링 진행 상황
- `crawled_urls.json` - 처리된 URL 목록
- `index.json` - 카테고리별 통계
- `logs/` - 상세 실행 로그

---

## 🔄 8단계: RAG 통합 준비

### 8.1 Qdrant 벡터DB 색인화
```python
# 각 기사를 임베딩으로 변환
embeddings = generate_embeddings(articles)
qdrant.upsert(
    collection="plastics_kr_news",
    points=[Point(id=i, vector=vec, payload=article) for i, (vec, article) in enumerate(zip(embeddings, articles))]
)
```

### 8.2 검색 쿼리 예시
```python
# 의미 기반 검색
results = qdrant.search(
    collection="plastics_kr_news",
    query_vector=embed("환경 친화적 플라스틱"),
    limit=10
)
```

---

## 🛠️ 9단계: 문제 해결 가이드

### 문제: 기사 추출 성공률 낮음
**원인 분석**:
1. 상세 페이지 HTML 선택자 부정확
2. 동적 로딩 콘텐츠
3. 페이지 구조 변경

**해결책**:
```python
# 선택자 다중화
selectors = [
    ('class', 'content'),
    ('id', 'article-content'),
    ('tag', 'article'),
    ('class', 'main-content')
]
```

### 문제: 타임아웃 발생
**해결책**:
```python
# 재시도 로직
for attempt in range(3):
    try:
        response = requests.get(url, timeout=10)
        break
    except requests.Timeout:
        time.sleep(2 ** attempt)  # 지수 백오프
```

---

## 📝 10단계: 완료 체크리스트

- [ ] 기존 데이터 삭제 및 초기화
- [ ] 크롤러 HTML 선택자 검증
- [ ] 5개 샘플 기사로 테스트
- [ ] S1N1 전체 크롤링 (50 페이지)
- [ ] S1N2, S1N3, S1N4 크롤링
- [ ] 데이터 품질 검증
- [ ] 통계 리포트 생성
- [ ] Qdrant 색인화 준비

---

## 🎓 학습 포인트

**이 크롤러에서 배울 수 있는 기술**:
1. **웹 스크래핑**: BeautifulSoup과 requests 활용
2. **상태 관리**: 진행 상황 저장 및 재개
3. **에러 핸들링**: 재시도 및 로깅
4. **데이터 검증**: JSON 스키마 및 품질 검사
5. **성능 최적화**: 레이트 리미팅, 캐싱
6. **RAG 통합**: 벡터 DB와의 연동

---

**문의사항**: claude@anthropic.com
**마지막 업데이트**: 2025-11-01T22:30:00Z
