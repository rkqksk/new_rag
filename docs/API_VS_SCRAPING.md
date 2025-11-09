# API vs Web Scraping 비교

**질문**: "API Keys recommended over scraping" 무슨말이야?

**답변**: 데이터를 가져오는 2가지 방법 비교입니다.

---

## 📊 두 가지 방법

### 1️⃣ **Web Scraping** (웹 스크래핑)
웹사이트 HTML을 다운로드해서 파싱하는 방법

```python
# 예시: 제품 정보 스크래핑
from bs4 import BeautifulSoup
import requests

response = requests.get('https://shop.com/products/12345')
soup = BeautifulSoup(response.text, 'html.parser')

# HTML에서 정보 추출
product_name = soup.find('h1', class_='product-title').text
price = soup.find('span', class_='price').text
```

**문제점**:
- ❌ 웹사이트 디자인 바뀌면 코드 다시 작성
- ❌ 봇 감지/차단 가능
- ❌ CAPTCHA, 로그인 등 복잡
- ❌ 느림 (HTML 전체 다운로드)
- ❌ 불안정 (언제든 막힐 수 있음)

### 2️⃣ **API** (Application Programming Interface)
웹사이트가 공식적으로 제공하는 데이터 접근 방법

```python
# 예시: 같은 제품 정보를 API로
import requests

response = requests.get(
    'https://api.shop.com/v1/products/12345',
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)

data = response.json()
product_name = data['name']
price = data['price']
```

**장점**:
- ✅ 안정적 (공식 지원)
- ✅ 빠름 (JSON 데이터만)
- ✅ 차단 없음 (정식 사용)
- ✅ 문서화되어 있음
- ✅ 유지보수 쉬움

---

## 🔑 API Key란?

**API Key** = 신분증

웹사이트가 "당신이 누구인지" 확인하고 데이터 접근을 허용하는 비밀번호입니다.

### 예시:

```python
# API Key 사용
API_KEY = "sk_live_1234567890abcdef"  # 웹사이트에서 발급

response = requests.get(
    'https://api.example.com/data',
    headers={'X-API-Key': API_KEY}
)
```

### API Key 발급 받는 방법:

1. 웹사이트 회원가입
2. 개발자 페이지로 이동
3. "API Key 발급" 버튼 클릭
4. 발급된 키를 코드에 사용

**예시 사이트**:
- Google Maps API: https://developers.google.com/maps
- GitHub API: https://github.com/settings/tokens
- OpenAI API: https://platform.openai.com/api-keys

---

## 📋 상세 비교

| 항목 | Web Scraping | API |
|------|-------------|-----|
| **속도** | 느림 (HTML 파싱) | 빠름 (JSON) |
| **안정성** | 낮음 (HTML 구조 변경) | 높음 (버전 관리) |
| **차단 위험** | 높음 (봇 감지) | 없음 (공식) |
| **로그인/2FA** | 복잡 | 간단 (API Key) |
| **CAPTCHA** | 막힘 | 없음 |
| **유지보수** | 어려움 | 쉬움 |
| **법적 문제** | 가능 (ToS 위반) | 없음 (공식) |
| **비용** | 무료 | 유료인 경우 많음 |
| **데이터 구조** | 비정형 (HTML) | 정형 (JSON) |
| **문서화** | 없음 | 있음 |

---

## 🎯 언제 무엇을 사용할까?

### ✅ API 사용 (권장)

**다음 경우에는 무조건 API 사용**:
- ✅ API가 제공되는 경우
- ✅ 대량 데이터 수집
- ✅ 장기 운영
- ✅ 안정성 중요
- ✅ 법적 문제 피하고 싶은 경우

**예시**:
- 날씨 데이터 → OpenWeatherMap API
- 주식 데이터 → Alpha Vantage API
- 뉴스 데이터 → NewsAPI
- SNS 데이터 → Twitter/Facebook/Instagram API

### ⚠️ Web Scraping 사용 (최후의 수단)

**다음 경우에만 사용**:
- ❌ API가 없는 경우
- ❌ API가 너무 비싼 경우
- ❌ API가 필요한 데이터를 제공하지 않는 경우
- ❌ 소규모/일회성 데이터 수집

**주의사항**:
- robots.txt 확인
- 이용약관 확인
- Rate limiting 적용
- 서버 부하 최소화

---

## 🔍 실제 사례

### 사례 1: 날씨 데이터

#### ❌ 스크래핑 (비권장)
```python
# 네이버 날씨 페이지 스크래핑
response = requests.get('https://weather.naver.com/today/09140101')
soup = BeautifulSoup(response.text, 'html.parser')
temp = soup.find('div', class_='temperature_text').text
# → HTML 구조 바뀌면 안됨
# → 봇 감지 가능
```

#### ✅ API (권장)
```python
# OpenWeatherMap API 사용
response = requests.get(
    'https://api.openweathermap.org/data/2.5/weather',
    params={
        'q': 'Seoul',
        'appid': 'YOUR_API_KEY'
    }
)
data = response.json()
temp = data['main']['temp']
# → 안정적
# → 빠름
# → 공식 지원
```

### 사례 2: 제품 정보

#### ❌ 스크래핑 (비권장)
```python
# 쿠팡 제품 페이지 스크래핑
response = requests.get('https://www.coupang.com/vp/products/12345')
# → CAPTCHA 막힘
# → 로그인 필요
# → 봇 감지
```

#### ✅ API (권장)
```python
# 쿠팡 파트너스 API 사용
response = requests.get(
    'https://api-gateway.coupang.com/v2/providers/affiliate_open_api/apis/openapi/products/12345',
    headers={'Authorization': 'Bearer YOUR_ACCESS_KEY'}
)
# → 공식 지원
# → 차단 없음
```

---

## 💡 API가 없을 때 대안

### 1. **공식 문의**
웹사이트에 이메일로 API 제공 여부 문의

```
제목: API 제공 문의

안녕하세요,
귀사의 서비스를 활용한 프로젝트를 진행 중입니다.
데이터 접근을 위한 API를 제공하시는지 문의드립니다.

감사합니다.
```

### 2. **제휴 문의**
공식 데이터 제공 계약

### 3. **오픈 데이터 찾기**
- 공공데이터포털: https://www.data.go.kr/
- Kaggle: https://www.kaggle.com/datasets
- GitHub: 공개 데이터셋

### 4. **최후의 수단: 스크래핑**
API가 정말 없을 때만 사용하되:
- robots.txt 준수
- Rate limiting
- 이용약관 확인
- 서버 부하 최소화

---

## 🚀 실전 가이드

### Step 1: API 확인

1. 웹사이트 하단 "개발자" 또는 "API" 링크 찾기
2. Google 검색: "[사이트명] API"
3. 없으면 → 공식 문의

### Step 2: API Key 발급

```python
# 대부분의 API는 이런 식으로 사용
import requests

API_KEY = "your-api-key-here"  # 웹사이트에서 발급

response = requests.get(
    'https://api.example.com/data',
    headers={'Authorization': f'Bearer {API_KEY}'}
)

data = response.json()
```

### Step 3: 요금 확인

대부분의 API는:
- ✅ 무료 티어 제공 (일일 요청 제한)
- ✅ 초과 시 유료

**예시**:
- OpenWeatherMap: 무료 1,000건/일
- Google Maps: 무료 $200 크레딧/월
- NewsAPI: 무료 1,000건/일

---

## 📝 요약

### 🎯 핵심 정리

**API (권장)**:
```
웹사이트가 공식으로 제공하는 데이터 접근 방법
→ 안정적, 빠름, 차단 없음
→ API Key로 신분 확인
```

**Web Scraping (최후 수단)**:
```
HTML 파싱해서 데이터 추출
→ 불안정, 느림, 차단 위험
→ API 없을 때만 사용
```

### 🔑 실무 조언

1. **무조건 API부터 찾기**
   - 웹사이트 개발자 페이지 확인
   - Google 검색: "[사이트명] API"

2. **API 없으면 문의**
   - 공식 API 제공 여부 문의
   - 제휴 계약 가능성 확인

3. **정말 없으면 스크래핑**
   - robots.txt 확인
   - 이용약관 확인
   - Rate limiting 적용
   - 법적 책임 인지

---

## 🔗 유용한 API 목록

### 무료 공개 API

| 카테고리 | API | 링크 |
|---------|-----|------|
| 날씨 | OpenWeatherMap | https://openweathermap.org/api |
| 뉴스 | NewsAPI | https://newsapi.org/ |
| 주식 | Alpha Vantage | https://www.alphavantage.co/ |
| 환율 | ExchangeRate-API | https://www.exchangerate-api.com/ |
| 공공데이터 | 공공데이터포털 | https://www.data.go.kr/ |
| 지도 | Google Maps | https://developers.google.com/maps |
| 번역 | Papago API | https://developers.naver.com/docs/papago/ |
| 검색 | Naver Search API | https://developers.naver.com/products/search/ |

### API 검색 사이트

- **Public APIs**: https://github.com/public-apis/public-apis (1000+ 무료 API)
- **RapidAPI**: https://rapidapi.com/ (API 마켓플레이스)
- **API List**: https://apilist.fun/ (카테고리별 API)

---

## 💬 자주 묻는 질문

### Q1: API Key는 어디서 받나요?
**A**: 각 웹사이트의 개발자 페이지에서 발급
- 회원가입 → 개발자 페이지 → API Key 발급

### Q2: API는 무료인가요?
**A**: 대부분 무료 티어 제공
- 소규모: 무료
- 대규모: 유료
- 예: 하루 1,000건까지 무료, 이후 유료

### Q3: API가 없으면 어떻게 하나요?
**A**: 3단계 접근
1. 공식 문의 (API 제공 여부)
2. 오픈 데이터 찾기 (공공데이터포털, Kaggle 등)
3. 최후 수단: Web Scraping (법적 확인 필수)

### Q4: Web Scraping은 불법인가요?
**A**: 경우에 따라 다름
- ✅ 합법: 공개 데이터, robots.txt 준수, 개인 사용
- ❌ 불법: 이용약관 위반, 봇 차단 우회, 상업적 이용 (ToS 위반)
- ⚠️ 그레이존: 개인정보, 저작권 있는 콘텐츠

### Q5: API Key를 코드에 직접 쓰면 안되나요?
**A**: 절대 안됨!
```python
# ❌ 나쁜 예
API_KEY = "sk_live_1234567890"  # 코드에 하드코딩

# ✅ 좋은 예
import os
API_KEY = os.getenv('API_KEY')  # 환경변수 사용
```

---

**결론**: 가능하면 무조건 **API 사용**하세요!
- 더 빠름
- 더 안정적
- 법적 문제 없음
- 유지보수 쉬움

Web Scraping은 정말 API가 없을 때만 최후의 수단으로 사용하세요.
