# 브라우저 통합 가이드

## 📋 개요

크로스 플랫폼 브라우저 자동화를 위한 통합 레이어로, Google DevTools MCP와 Playwright를 지원합니다.

## 🌐 지원하는 브라우저

### webkit
- **플랫폼**: macOS
- **엔진**: Safari WebKit
- **장점**:
  - 빠른 실행 속도
  - macOS 네이티브 통합
  - 낮은 리소스 사용
- **단점**: macOS 전용

### chromium
- **플랫폼**: macOS, Linux, Windows
- **엔진**: Chrome Chromium
- **장점**:
  - 크로스 플랫폼 호환성
  - 안정적인 자바스크립트 실행
  - 광범위한 테스트 지원
- **단점**: webkit보다 느림

## 🛠️ 지원하는 백엔드

### Google DevTools MCP (기본)
- **타입**: MCP Server
- **경로**: `mcp_servers.google_devtools.server`
- **특징**:
  - Claude Code 네이티브 통합
  - 낮은 지연시간
  - 안정적인 DevTools Protocol

### Playwright (선택)
- **타입**: Python 라이브러리
- **패키지**: `playwright==1.38.0`
- **특징**:
  - 스크린샷 지원
  - 풍부한 브라우저 제어
  - 크로스 브라우저 테스팅

## 🚀 사용 방법

### 기본 사용 (webkit + DevTools)
```python
from chungjin_crawler import ChungjinCrawler

# macOS 최적화 (기본값)
crawler = ChungjinCrawler(
    output_dir="data/crawled_products"
)
# 자동: browser_type="webkit", use_playwright=False
```

### Chromium 사용
```python
# 크로스 플랫폼 호환성
crawler = ChungjinCrawler(
    output_dir="data/crawled_products",
    browser_type="chromium"  # Linux/Windows에서 안정적
)
```

### Playwright 사용
```python
# Playwright로 전환 (추후 구현)
crawler = ChungjinCrawler(
    output_dir="data/crawled_products",
    browser_type="chromium",
    use_playwright=True
)
```

### 크롤링 에이전트에서 사용
```python
from agents.crawling_agent import CrawlingAgent, CrawlConfig, ChungjinCrawler

# 설정 생성
config = CrawlConfig(
    site_name="청진코리아",
    site_url="http://chungjinkorea.com",
    output_dir="data/crawled_products",
    browser_type="chromium",  # 크로스 플랫폼
    use_playwright=False      # DevTools 사용
)

# 크롤러 생성
crawler = ChungjinCrawler(config)

# 에이전트 등록
agent = CrawlingAgent()
agent.register_crawler("청진코리아", crawler)
```

## 📊 브라우저 선택 가이드

### macOS 사용자
```python
# 권장: webkit (가장 빠름)
browser_type="webkit"

# 대안: chromium (다른 환경과 동일)
browser_type="chromium"
```

### Linux/Windows 사용자
```python
# 필수: chromium
browser_type="chromium"
```

### CI/CD 환경
```python
# Docker 컨테이너
browser_type="chromium"
use_playwright=False  # DevTools로 충분
```

### 스크린샷 필요 시
```python
# Playwright 필요
browser_type="chromium"
use_playwright=True
```

## 🔧 고급 설정

### 증분 크롤러 설정
```python
# crawl_bottle_adaptive.py
from chungjin_crawler import ChungjinCrawler

# Linux 서버에서 실행
crawler = ChungjinCrawler(
    output_dir="data/crawled_products",
    browser_type="chromium"  # webkit 사용 불가
)
```

### 환경별 자동 선택
```python
from browser_automation import create_automation
import platform

# 플랫폼에 따라 자동 선택
automation = create_automation()
# macOS → webkit
# Linux/Windows → chromium
```

### 수동 브라우저 제어
```python
from browser_automation import BrowserAutomation

# 세밀한 제어
automation = BrowserAutomation(
    backend="devtools",     # 또는 "playwright"
    browser_type="chromium"
)

await automation.launch_browser(headless=True)
await automation.navigate("https://example.com")
result = await automation.evaluate_javascript("() => document.title")
await automation.close_browser()
```

## 🐛 문제 해결

### webkit이 Linux에서 실행 안됨
**문제**: "webkit is not supported on this platform"

**해결**:
```python
# chromium으로 변경
crawler = ChungjinCrawler(
    browser_type="chromium"
)
```

### Playwright 설치 에러
**문제**: "playwright is not installed"

**해결**:
```bash
# Playwright 설치
pip install playwright

# 브라우저 바이너리 설치
python -m playwright install chromium
```

### DevTools MCP 연결 실패
**문제**: "Cannot connect to DevTools"

**해결**:
1. `.mcp.json` 확인
2. Google DevTools MCP 서버 재시작
3. Playwright로 fallback

## 📈 성능 비교

| 브라우저 | 백엔드 | 속도 | 메모리 | 호환성 |
|---------|-------|------|--------|--------|
| webkit | DevTools | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | macOS 전용 |
| chromium | DevTools | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 크로스 플랫폼 |
| webkit | Playwright | ⭐⭐⭐⭐ | ⭐⭐⭐ | macOS 전용 |
| chromium | Playwright | ⭐⭐⭐ | ⭐⭐⭐ | 크로스 플랫폼 |

## 🔄 마이그레이션 가이드

### 기존 코드 (webkit 하드코딩)
```python
# OLD
await self.automation.launch_browser(
    headless=True,
    browser_type="webkit"  # 하드코딩
)
```

### 새 코드 (설정 가능)
```python
# NEW
crawler = ChungjinCrawler(
    output_dir="data/crawled_products",
    browser_type="webkit"  # 또는 "chromium"
)

await crawler.automation.launch_browser(
    headless=True,
    browser_type=crawler.browser_type  # 동적
)
```

## 📝 환경 변수

```bash
# .env 파일
BROWSER_TYPE=chromium         # webkit 또는 chromium
USE_PLAYWRIGHT=false          # true 또는 false
BROWSER_HEADLESS=true         # 헤드리스 모드
```

```python
# 환경 변수 사용
import os

crawler = ChungjinCrawler(
    output_dir="data/crawled_products",
    browser_type=os.getenv("BROWSER_TYPE", "webkit"),
    use_playwright=os.getenv("USE_PLAYWRIGHT", "false") == "true"
)
```

## 🚀 스케줄러 통합

```yaml
# config/crawl_schedule.yaml
schedules:
  bottle:
    enabled: true
    script: "crawl_bottle_adaptive.py"
    browser_type: "chromium"  # 서버 환경
    use_playwright: false
```

## ✅ 체크리스트

### macOS 개발 환경
- [x] webkit + DevTools (기본값)
- [x] chromium + DevTools (대체)
- [ ] Playwright 지원 (추후)

### Linux 프로덕션 환경
- [x] chromium + DevTools
- [ ] Playwright 지원 (추후)

### Windows 환경
- [x] chromium + DevTools
- [ ] Playwright 지원 (추후)

---

**작성자**: RAG Enterprise Team
**버전**: 1.0.0
**최종 업데이트**: 2025-10-18
