# 🛠️ Google DevTools MCP 서버 구축

## ✨ 완성 요약

**Google DevTools MCP 서버**가 구축되었습니다!

### 📁 생성된 파일

```
mcp_servers/google_devtools/
├── __init__.py              → 패키지 초기화
├── server.py                → MCP 서버 메인 (10개 도구)
└── rag_crawler.py           → RAG 사이트 크롤러
```

---

## 🔧 구현된 도구 (Tools)

### 기본 브라우저 제어
```python
1. launch_browser()      # 브라우저 시작
2. navigate(url)         # URL 이동
3. close_browser()       # 브라우저 종료
```

### 페이지 상호작용
```python
4. screenshot()          # 스크린샷 캡처
5. click_element()       # 요소 클릭
6. fill_form()           # 폼 입력
7. evaluate_js()         # JavaScript 실행
```

### 데이터 수집
```python
8. get_page_content()    # HTML 콘텐츠
9. crawl_page()          # 페이지 크롤링 (링크, 제목, 텍스트)
10. get_metrics()        # 성능 메트릭
```

---

## 📊 RAG 크롤러 기능

```python
RAGSiteCrawler
├─ crawl_dashboard()           # 전체 대시보드 크롤링
├─ test_api_endpoints()        # API 테스트
├─ monitor_performance()       # 성능 모니터링
├─ test_form_submission()      # 검색 폼 테스트
└─ take_full_report()          # 전체 리포트 생성
```

---

## 🚀 사용 방법 (다음 세션)

### 1. 의존성 설치
```bash
pip install playwright mcp
playwright install chromium
```

### 2. MCP 서버 등록
`.mcp.json` 수정:
```json
{
  "mcpServers": {
    "google-devtools": {
      "command": "python",
      "args": ["/path/to/mcp_servers/google_devtools/server.py"]
    }
  }
}
```

### 3. 사용 예시 (Claude에서)
```
"우리 RAG 대시보드 성능을 모니터링해줄 수 있어?"

Claude는 google_devtools MCP를 사용해서:
1. 브라우저 시작
2. http://localhost:8000/dashboard 접방
3. 모든 탭 크롤링
4. 성능 메트릭 수집
5. 리포트 생성
```

---

## 💡 활용 시나리오

### ✅ 자동 테스트
- 대시보드 전체 기능 테스트
- API 엔드포인트 검증
- 성능 회귀 테스트

### ✅ 데이터 수집
- 렌더링된 페이지 내용 추출
- 동적 콘텐츠 크롤링
- 실시간 메트릭 모니터링

### ✅ 디버깅
- 브라우저에서 보이는 내용 확인
- JavaScript 실행 및 결과 확인
- 폼 제출 등 사용자 행동 자동화

---

## 🔄 다음 단계

### Phase 2 (다음 세션에서):
- [ ] .mcp.json 등록
- [ ] Claude에서 MCP 연동 테스트
- [ ] 자동 크롤링 스크립트
- [ ] 성능 리포트 생성 자동화

### Phase 3:
- [ ] 정기적 모니터링 (Cron)
- [ ] 결과 저장 (DB/파일)
- [ ] 알림 시스템
- [ ] 시각화 대시보드

---

## 📝 기술 스택

- **Protocol**: Model Context Protocol (MCP)
- **Browser**: Playwright (Chromium)
- **Python**: 3.11+
- **Server**: MCP Server SDK

---

## 🎯 전체 구조

```
Claude Code
    ↓
MCP Server (Google DevTools)
    ↓
Playwright Browser
    ↓
RAG Dashboard (localhost:8000)
    ↓
Crawl/Test/Monitor
    ↓
Report/Data Collection
```

---

**Status**: ✅ **구축 완료 - 테스트 준비 됨**
**Version**: 1.0
**Last Updated**: 2025-10-17
