# 플라넷뉴스(plastics.kr) 텍스트 크롤링 - 단순 실행 계획

**작성일**: 2025-11-01
**목표**: 뉴스/인사이트/오피니언/TECH 모든 텍스트 기사 수집

---

## 1️⃣ 웹사이트 구조

### 기사 목록 페이지
```
URL: https://www.plastics.kr/news/articleList.html?sc_section_code={CODE}&view_type=sm&page={N}

카테고리:
- S1N1: 뉴스 (50+ 페이지)
- S1N2: 인사이트 (~2 페이지)
- S1N3: 오피니언 (~2 페이지)
- S1N4: TECH (~5 페이지)
```

### 기사 상세 페이지
```
URL: https://www.plastics.kr/news/articleView.html?idxno={ID}

추출 필드:
- 제목: <div class="article-title">
- 날짜: <div class="article-date">
- 본문: <div class="article-body">
- 작성자: <span class="writer"> 또는 본문에서 추출
```

---

## 2️⃣ HTML 구조 (현장 확인 필수)

### 기사 목록 리스트 페이지
```html
<ul class="article-list">
  <li>
    <a href="/news/articleView.html?idxno=1234">기사 제목</a>
    <div class="summary">요약 (생략될 수 있음)</div>
    <span class="date">YYYY.MM.DD</span>
  </li>
  ...
</ul>
```

### 기사 상세 페이지
```html
<div class="article-title">기사 제목</div>
<div class="article-date">YYYY.MM.DD</div>
<div class="article-body">기사 본문 텍스트</div>
```

---

## 3️⃣ 크롤링 알고리즘 (의사코드)

```
FOR EACH 카테고리 (S1N1, S1N2, S1N3, S1N4):
    page = 1
    WHILE 다음 페이지 존재:
        기사목록 URL 접속
        <ul.article-list> 내 모든 <li> 추출
        FOR EACH <li>:
            기사 ID 추출 (href에서)
            제목 추출
            날짜 추출

            상세 페이지 접속
            본문 추출

            JSON으로 저장:
            {
              "title": "...",
              "date": "YYYY-MM-DD",
              "body": "...",
              "url": "https://...",
              "category": "S1N1"
            }

        time.sleep(1)  # 서버 부하 방지
        page += 1
```

---

## 4️⃣ Python 구현 (최소 코드)

```python
import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://www.plastics.kr"
CODES = ["S1N1", "S1N2", "S1N3", "S1N4"]
MAX_PAGES = {"S1N1": 50, "S1N2": 2, "S1N3": 2, "S1N4": 5}

articles = []
seen_ids = set()

for code in CODES:
    for page in range(1, MAX_PAGES[code] + 1):
        # 기사 목록 페이지
        list_url = f"{BASE}/news/articleList.html?sc_section_code={code}&view_type=sm&page={page}"
        print(f"📄 {code} Page {page}...")

        try:
            soup = BeautifulSoup(requests.get(list_url, timeout=10).text, "html.parser")

            # 기사 링크 추출
            for li in soup.select("ul.article-list > li"):
                link_elem = li.select_one("a")
                if not link_elem:
                    continue

                href = link_elem.get("href", "")
                if "idxno=" not in href:
                    continue

                # 기사 ID 추출
                article_id = href.split("idxno=")[1].split("&")[0]
                if article_id in seen_ids:
                    continue

                seen_ids.add(article_id)

                # 기사 제목과 날짜
                title = link_elem.text.strip()
                date_elem = li.select_one("span.date")
                date = date_elem.text.strip() if date_elem else ""

                # 상세 페이지 방문
                detail_url = BASE + href if href.startswith("/") else href
                detail_soup = BeautifulSoup(requests.get(detail_url, timeout=10).text, "html.parser")

                # 본문 추출
                body_elem = detail_soup.select_one("div.article-body")
                body = body_elem.text.strip() if body_elem else ""

                # 저장
                articles.append({
                    "title": title,
                    "date": date,
                    "body": body,
                    "url": detail_url,
                    "category": code
                })

                print(f"  ✓ {title[:50]}...")
                time.sleep(1)

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

# JSONL 형식으로 저장
with open("/Users/oypnus/Project/rag-enterprise/data/plastics_kr/articles.jsonl", "w", encoding="utf-8") as f:
    for article in articles:
        f.write(json.dumps(article, ensure_ascii=False) + "\n")

print(f"\n✅ 완료: {len(articles)}개 기사 저장됨")
```

---

## 5️⃣ 실행 방법

```bash
# 1. 스크립트 파일 생성
cat > scripts/crawl_plastics_kr_simple.py << 'EOF'
# 위의 Python 코드 붙여넣기
EOF

# 2. 실행
python3 scripts/crawl_plastics_kr_simple.py

# 3. 결과 확인
wc -l data/plastics_kr/articles.jsonl
head -1 data/plastics_kr/articles.jsonl | python3 -m json.tool
```

---

## 6️⃣ 예상 결과

| 항목 | 예상값 |
|------|--------|
| 총 기사 수 | ~700-1000개 |
| 총 페이지 | 59 |
| 파일 크기 | ~50-100 MB |
| 실행 시간 | 1-2시간 (rate limiting 포함) |

---

## 7️⃣ 품질 검증

```bash
# 첫 번째 기사 확인
head -1 data/plastics_kr/articles.jsonl | python3 -m json.tool

# 마지막 기사 확인
tail -1 data/plastics_kr/articles.jsonl | python3 -m json.tool

# 기사 수 확인
wc -l data/plastics_kr/articles.jsonl

# 빈 본문 확인
cat data/plastics_kr/articles.jsonl | python3 -c "import sys, json; [print(x) for x in sys.stdin if not json.loads(x).get('body')]"
```

---

## ⚠️ 주의사항

1. **HTML 구조 확인**: 실제 웹사이트 방문 후 CSS 선택자 확인 필수
2. **율 제한**: 서버 과부하 방지를 위해 `time.sleep(1)` 필수
3. **에러 처리**: 일부 페이지가 접속 불가능할 수 있으니 try-except 사용
4. **인코딩**: UTF-8 인코딩으로 한글 완벽 지원

---

## 🎯 다음 단계

1. ✅ 크롤러 실행 → `articles.jsonl` 생성
2. ✅ 데이터 품질 검증 → 본문 추출 확인
3. 📊 Qdrant 벡터DB 색인화
4. 🤖 RAG 시스템에 통합

---

**마지막 업데이트**: 2025-11-01
**상태**: 준비 완료 ✅
