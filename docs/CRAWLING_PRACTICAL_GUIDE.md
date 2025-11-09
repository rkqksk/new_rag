# 크롤링 실전 가이드

**목적**: 실제로 사용 가능한 모든 크롤링 방법 총정리

---

## 📋 목차

1. [2FA/로그인 처리 방법](#1-2fa로그인-처리-방법)
2. [robots.txt 처리 방법](#2-robotstxt-처리-방법)
3. [완전한 예제](#3-완전한-예제)
4. [문제 해결](#4-문제-해결)

---

## 1. 2FA/로그인 처리 방법

### 방법 1: 수동 로그인 (가장 간단) ⭐ 추천

**사용 시점**: 2FA, CAPTCHA 등 자동화 어려울 때

```python
from app.services.crawling.manual_auth import auto_or_manual_login

# 첫 실행: 브라우저가 뜨고 직접 로그인
# 이후 실행: 저장된 쿠키로 자동 로그인
auth = await auto_or_manual_login(
    url='https://portal.com/login',
    session_name='my-portal',
    verify_url='https://portal.com/dashboard'
)

# 쿠키 사용해서 데이터 수집
cookies = auth['cookies']
```

**장점**:
- ✅ 모든 인증 방식 지원 (2FA, CAPTCHA, 생체인증 등)
- ✅ 법적 문제 없음 (본인이 직접 로그인)
- ✅ 한 번만 로그인하면 쿠키 재사용
- ✅ 복잡한 플로우도 OK

**단점**:
- ❌ 처음 한 번은 수동 작업 필요
- ❌ 완전 자동화 불가

### 방법 2: TOTP 자동 로그인 (자동화)

**사용 시점**: 본인 계정이고 TOTP 시크릿을 알 때

```python
from app.services.crawling.auth_manager import (
    AuthenticationManager, AuthType, AuthCredentials
)

auth = AuthenticationManager()

# TOTP 시크릿 준비 (본인 QR 코드에서 추출)
creds = AuthCredentials(
    username='your@email.com',
    password='your_password',
    totp_secret='JBSWY3DPEHPK3PXP'  # 본인 시크릿
)

# 자동 로그인
client = await auth.authenticate(
    AuthType.TOTP,
    creds,
    login_url='https://portal.com/login'
)

# 사용
response = await client.get('https://portal.com/data')
```

**TOTP 시크릿 얻는 방법**:

1. **새로 2FA 설정할 때**:
   ```python
   from app.services.crawling.auth_manager import AuthenticationManager

   # 시크릿 생성
   secret = AuthenticationManager.generate_totp_secret()
   print(f"시크릿: {secret}")

   # QR 코드 URI 생성
   uri = AuthenticationManager.get_totp_provisioning_uri(
       secret=secret,
       name='your@email.com',
       issuer='Portal'
   )
   print(f"QR URI: {uri}")

   # 이 시크릿을 Google Authenticator에 입력
   # 동시에 코드에도 저장
   ```

2. **이미 2FA 설정되어 있을 때**:
   - QR 코드 다시 보기 → 시크릿 추출
   - 또는 2FA 재설정

**장점**:
- ✅ 완전 자동화
- ✅ 빠름
- ✅ 본인 계정이면 합법

**단점**:
- ❌ 본인 계정만 가능
- ❌ TOTP 시크릿 필요
- ❌ 다른 사람 계정은 불법

### 방법 3: API Key (가장 좋음) ⭐⭐⭐

**사용 시점**: 웹사이트가 API 제공할 때

```python
from app.services.crawling.auth_manager import authenticate_api_key

# API Key로 인증 (가장 간단)
client = await authenticate_api_key('your-api-key')

# 사용
response = await client.get('https://api.example.com/data')
data = response.json()
```

**장점**:
- ✅ 가장 간단
- ✅ 공식 지원
- ✅ 차단 없음
- ✅ 안정적

**단점**:
- ❌ API 제공하는 사이트만 가능

### 방법 4: 기본 인증 (가장 단순)

**사용 시점**: 간단한 HTTP Basic Auth

```python
from app.services.crawling.auth_manager import authenticate_basic

client = await authenticate_basic('username', 'password')
response = await client.get('https://protected-site.com/data')
```

### 비교표

| 방법 | 자동화 | 난이도 | 법적 리스크 | 추천도 |
|------|-------|-------|-----------|--------|
| **수동 로그인** | 반자동 | ⭐ 쉬움 | 없음 | ⭐⭐⭐ |
| **TOTP 자동** | 완전 | ⭐⭐ 보통 | 없음 (본인만) | ⭐⭐ |
| **API Key** | 완전 | ⭐ 쉬움 | 없음 | ⭐⭐⭐⭐⭐ |
| **Basic Auth** | 완전 | ⭐ 쉬움 | 없음 | ⭐⭐⭐ |

---

## 2. robots.txt 처리 방법

### 방법 1: 준수 (기본)

```python
from app.services.crawling.robots_handler import RobotsHandler, RobotsPolicy

# robots.txt 준수
handler = RobotsHandler(policy=RobotsPolicy.RESPECT)

can_fetch = await handler.can_fetch('https://example.com/data')

if can_fetch:
    # 크롤링 진행
    pass
else:
    print("robots.txt에서 차단됨")
```

### 방법 2: 무시 (자기 책임)

```python
from app.services.crawling.robots_handler import RobotsHandler, RobotsPolicy

# robots.txt 무시
handler = RobotsHandler(policy=RobotsPolicy.IGNORE)

can_fetch = await handler.can_fetch('https://example.com/data')
# 항상 True 반환

# 크롤링 진행
```

### 방법 3: 우회 (Googlebot으로 위장)

```python
from app.services.crawling.robots_handler import RobotsHandler, RobotsPolicy

# Googlebot으로 위장
handler = RobotsHandler(policy=RobotsPolicy.BYPASS)

can_fetch = await handler.can_fetch('https://example.com/data')
# Googlebot은 허용되므로 True
```

### 간편 함수

```python
from app.services.crawling.robots_handler import check_robots, bypass_robots

# 준수
allowed = await check_robots('https://example.com/data', respect=True)

# 무시
allowed = await check_robots('https://example.com/data', respect=False)

# 우회
allowed = await bypass_robots('https://example.com/data')
```

### 크롤러에 통합

```python
from app.services.crawling.multi_strategy_crawler import MultiStrategyCrawler
from app.services.crawling.robots_handler import (
    add_robots_check_to_crawler,
    RobotsPolicy
)

crawler = MultiStrategyCrawler()

# robots.txt 체크 추가
add_robots_check_to_crawler(
    crawler,
    policy=RobotsPolicy.IGNORE  # 또는 RESPECT, BYPASS
)

# 크롤링
result = await crawler.crawl('https://example.com/data')
```

### 비교표

| 정책 | 동작 | 법적 | 추천도 |
|------|------|------|--------|
| **RESPECT** | robots.txt 준수 | 안전 | ⭐⭐⭐⭐⭐ |
| **IGNORE** | robots.txt 무시 | 그레이존 | ⭐⭐ |
| **BYPASS** | Googlebot 위장 | 그레이존 | ⭐⭐⭐ |

---

## 3. 완전한 예제

### 예제 1: 2FA 사이트 크롤링 (수동 로그인)

```python
from app.services.crawling.manual_auth import auto_or_manual_login
from app.services.crawling.multi_strategy_crawler import MultiStrategyCrawler
from app.services.crawling.robots_handler import RobotsPolicy
import httpx

async def crawl_with_2fa():
    """2FA 사이트 크롤링"""

    # 1. 로그인 (첫 실행만 브라우저 뜸)
    auth = await auto_or_manual_login(
        url='https://portal.com/login',
        session_name='my-portal',
        verify_url='https://portal.com/dashboard'
    )

    # 2. 쿠키로 HTTP 클라이언트 생성
    cookies = {c['name']: c['value'] for c in auth['cookies']}

    async with httpx.AsyncClient(cookies=cookies) as client:
        # 3. 데이터 크롤링
        response = await client.get('https://portal.com/api/data')
        data = response.json()

        print(f"수집된 데이터: {len(data)}건")

        return data

# 실행
data = await crawl_with_2fa()
```

### 예제 2: robots.txt 무시하고 크롤링

```python
from app.services.crawling.multi_strategy_crawler import (
    MultiStrategyCrawler,
    CrawlConfig
)
from app.services.crawling.evasion import EvasionConfig
from app.services.crawling.robots_handler import RobotsPolicy

async def crawl_ignore_robots():
    """robots.txt 무시"""

    # 크롤러 설정
    config = CrawlConfig(
        use_evasion=True,
        evasion_config=EvasionConfig(
            rotate_user_agent=True,
            min_delay=2.0,
            max_delay=5.0
        )
    )

    crawler = MultiStrategyCrawler(config)

    # robots.txt 무시 설정
    from app.services.crawling.robots_handler import add_robots_check_to_crawler
    add_robots_check_to_crawler(crawler, policy=RobotsPolicy.IGNORE)

    # 크롤링
    result = await crawler.crawl('https://example.com/data')

    return result

# 실행
result = await crawl_ignore_robots()
```

### 예제 3: 완전 자동화 (TOTP + robots.txt 무시)

```python
from app.services.crawling.auth_manager import (
    AuthenticationManager, AuthType, AuthCredentials
)
from app.services.crawling.session_manager import SessionManager
from app.services.crawling.robots_handler import RobotsPolicy
import httpx

async def fully_automated_crawl():
    """완전 자동화 크롤링"""

    # 1. 세션 관리자
    session_mgr = SessionManager()

    # 2. 로그인 함수 정의
    async def login():
        auth_mgr = AuthenticationManager()

        creds = AuthCredentials(
            username='your@email.com',
            password='your_password',
            totp_secret='YOUR_TOTP_SECRET'  # 본인 시크릿
        )

        return await auth_mgr.authenticate(
            AuthType.TOTP,
            creds,
            login_url='https://portal.com/login'
        )

    # 3. 세션 가져오기 (자동으로 로그인/재사용)
    client = await session_mgr.get_or_create_session(
        name='my-portal',
        validation_url='https://portal.com/dashboard',
        login_func=login,
        max_age_hours=24
    )

    # 4. 크롤링 (robots.txt 무시)
    response = await client.get('https://portal.com/api/data')
    data = response.json()

    return data

# 실행
data = await fully_automated_crawl()
```

### 예제 4: API 사용 (최고)

```python
from app.services.crawling.auth_manager import authenticate_api_key

async def crawl_with_api():
    """API로 데이터 수집 (가장 좋음)"""

    # API Key로 인증
    client = await authenticate_api_key('your-api-key')

    # 데이터 수집
    response = await client.get('https://api.example.com/v1/products')
    data = response.json()

    return data['results']

# 실행
products = await crawl_with_api()
```

---

## 4. 문제 해결

### Q1: "브라우저가 안 뜨는데요?"

**A**: Playwright 설치 필요

```bash
pip install playwright
playwright install chromium
```

### Q2: "TOTP 코드가 안 맞아요"

**A**: 시간 동기화 확인

```python
import pyotp
import time

totp = pyotp.TOTP('YOUR_SECRET')

# 현재 코드
print(f"현재 코드: {totp.now()}")

# 시간 확인
print(f"시스템 시간: {time.time()}")

# 남은 시간
print(f"남은 시간: {totp.interval - time.time() % totp.interval}초")
```

### Q3: "쿠키가 만료됐어요"

**A**: 강제 재로그인

```python
from app.services.crawling.manual_auth import auto_or_manual_login

# force_manual=True로 강제 재로그인
auth = await auto_or_manual_login(
    url='https://portal.com/login',
    session_name='my-portal',
    force_manual=True  # 기존 쿠키 무시하고 재로그인
)
```

### Q4: "봇으로 감지됐어요"

**A**: 안티 감지 강화

```python
from app.services.crawling.multi_strategy_crawler import (
    MultiStrategyCrawler, CrawlConfig
)
from app.services.crawling.evasion import EvasionConfig

config = CrawlConfig(
    use_evasion=True,
    evasion_config=EvasionConfig(
        rotate_user_agent=True,
        randomize_headers=True,
        spoof_referrer=True,
        min_delay=3.0,  # 딜레이 늘리기
        max_delay=7.0,
        use_proxies=True,  # 프록시 사용
        proxy_list=['http://proxy1.com:8080', 'http://proxy2.com:8080']
    )
)

crawler = MultiStrategyCrawler(config)
```

### Q5: "CAPTCHA가 나와요"

**A**: 수동 로그인 사용

```python
from app.services.crawling.manual_auth import manual_login_once

# 브라우저 띄워서 CAPTCHA 직접 풀기
await manual_login_once(
    url='https://site.com/login',
    session_name='my-site'
)
```

---

## 🎯 추천 워크플로우

### 단계 1: API 확인
```python
# 1. API 문서 찾기
# 2. API Key 발급
# 3. API 사용

client = await authenticate_api_key('api-key')
data = await client.get('https://api.example.com/data')
```

### 단계 2: API 없으면 수동 로그인
```python
# 브라우저 띄워서 로그인 (CAPTCHA, 2FA 등 해결)
auth = await auto_or_manual_login(
    url='https://site.com/login',
    session_name='my-site'
)
```

### 단계 3: 자동화 필요하면 TOTP
```python
# 본인 계정이고 반복 실행 필요하면
creds = AuthCredentials(
    username='your@email.com',
    password='password',
    totp_secret='YOUR_SECRET'
)

client = await auth_manager.authenticate(AuthType.TOTP, creds)
```

---

## 📋 체크리스트

### 크롤링 시작 전

- [ ] API 확인했는가?
- [ ] 이용약관 확인했는가?
- [ ] robots.txt 확인했는가?
- [ ] Rate limiting 설정했는가?
- [ ] 본인 계정인가? (타인 계정은 불법)

### 2FA 처리

- [ ] 수동 로그인 시도 (가장 간단)
- [ ] TOTP 시크릿 확보 (자동화 필요시)
- [ ] 쿠키 저장 설정 (재사용)

### 안티 감지

- [ ] User-Agent 랜덤화
- [ ] 딜레이 설정 (2-5초)
- [ ] Rate limiting (10건/분)
- [ ] Referrer 설정

---

## 🚀 빠른 시작 템플릿

### 템플릿 1: 간단한 크롤링
```python
from app.services.crawling.multi_strategy_crawler import MultiStrategyCrawler

async def simple_crawl(url):
    async with MultiStrategyCrawler() as crawler:
        result = await crawler.crawl(url)
        return result['content']
```

### 템플릿 2: 2FA 사이트
```python
from app.services.crawling.manual_auth import auto_or_manual_login

async def crawl_2fa_site(login_url, data_url, session_name):
    # 로그인
    auth = await auto_or_manual_login(
        url=login_url,
        session_name=session_name
    )

    # 크롤링
    cookies = {c['name']: c['value'] for c in auth['cookies']}
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(data_url)
        return response.json()
```

### 템플릿 3: API 사용
```python
from app.services.crawling.auth_manager import authenticate_api_key

async def fetch_from_api(api_key, endpoint):
    client = await authenticate_api_key(api_key)
    response = await client.get(endpoint)
    return response.json()
```

---

## 📚 참고 자료

- [API vs Scraping 비교](./API_VS_SCRAPING.md)
- [고급 크롤링 전략](./ADVANCED_CRAWLING_STRATEGY.md)
- [크롤링 능력 요약](./CRAWLING_CAPABILITIES_SUMMARY.md)

---

**결론**:
1. **API가 있으면 무조건 API 사용**
2. **2FA/CAPTCHA 있으면 수동 로그인**
3. **자동화 필요하면 TOTP (본인 계정만)**
4. **robots.txt는 상황에 따라 (기본은 준수)**
5. **Rate limiting은 무조건 적용**
