# 🤖 Freemold 완벽 크롤링 가이드

## 📋 개요

Freemold.net에서 **21,201개 제품**의 상세 정보와 이미지를 수집하는 프로덕션급 크롤러입니다.

### ✅ 이미 완료된 작업
- **제품 목록 크롤링**: 21,201개 제품 URL 수집 완료
  - B001 (다이렉트 블로우): 9,870개
  - B002: 5,013개
  - B003: 5,291개
  - B004: 1,027개

### ❌ 누락된 데이터
현재 데이터에는 **URL만** 있고 다음 정보가 없습니다:
- 제품명, 이미지, 가격, 스펙, 재질, 용량, 설명

---

## 🛡️ IP 차단 우회 전략

### 1️⃣ **랜덤 지연** (Random Delay)
```python
delay_min = 3.0  # 최소 3초
delay_max = 8.0  # 최대 8초
```
- 봇 탐지 회피
- 서버 부하 분산
- 인간 행동 패턴 모방

### 2️⃣ **User-Agent 로테이션**
```python
USER_AGENTS = [
    "Chrome/Windows 10",
    "Chrome/macOS",
    "Firefox/Windows",
    "Safari/macOS",
    "Chrome/Linux"
]
```
- 5개의 제품마다 User-Agent 변경
- 다양한 브라우저/OS 조합

### 3️⃣ **재시도 메커니즘**
```python
max_retries = 3  # 최대 3회 재시도
```
- 서버 에러 발생 시 10초 대기 후 재시도
- 네트워크 장애 자동 복구

### 4️⃣ **진행상황 저장**
```python
# 10개 제품마다 자동 저장
crawl_progress.json  # 완료/실패 목록
error_log.json       # 에러 상세 로그
```
- 중단 시 이어서 크롤링 가능
- 완료된 제품 자동 스킵

### 5️⃣ **프록시 지원** (옵션)
```python
use_proxy = True
proxy_url = "http://proxy-server:port"
```
- 필요시 프록시 서버 사용
- IP 로테이션 가능

---

## 🚀 사용 방법

### 1. 필수 패키지 설치
```bash
pip install playwright aiohttp
playwright install chromium
```

### 2. Chrome Remote Debugging 실행
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile &
```

### 3. 소규모 테스트 (처음 10개)
```bash
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B001/B001_products.json \
  0 \
  10
```

### 4. 카테고리별 크롤링

#### B001 (9,870개 - 약 13-22시간 소요)
```bash
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B001/B001_products.json \
  0 \
  100  # 처음 100개만
```

#### B002 (5,013개)
```bash
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B002/B002_products.json
```

#### B003 (5,291개)
```bash
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B003/B003_products.json
```

#### B004 (1,027개)
```bash
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B004/B004_products.json
```

### 5. 이어서 크롤링 (중단된 경우)
```bash
# 진행상황 확인
cat data/freemold/complete_crawl/crawl_progress.json

# 특정 인덱스부터 재시작
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B001/B001_products.json \
  500  # 500번째부터 시작
```

---

## 📊 수집되는 데이터

### 완전한 제품 정보
```json
{
  "product_id": "88939",
  "product_url": "https://www.freemold.net/Front/Product/?tp=vi&pIdx=88939",
  "product_name": "50ml PET 다이렉트 블로우 용기",
  "category_code": "B001",
  "category_name": "다이렉트 브로우 (Direct Blow)",

  "images": [
    "https://www.freemold.net/upload/product/88939_1.jpg",
    "https://www.freemold.net/upload/product/88939_2.jpg"
  ],

  "downloaded_images": [
    "data/freemold/images/88939_abc123def456.jpg",
    "data/freemold/images/88939_789ghi012jkl.jpg"
  ],

  "specifications": {
    "용량": "50ml",
    "재질": "PET",
    "넥사이즈": "24/410",
    "높이": "120mm",
    "직경": "45mm"
  },

  "capacities": [["50", "ml"]],
  "materials": ["PET"],
  "neck_sizes": ["24/410"],

  "price_info": "단가: 문의 / MOQ: 5,000개",
  "company_url": "https://www.freemold.net/Front/Company/?mIdx=1324",
  "crawled_at": "2025-10-27T02:00:00.000000"
}
```

---

## 📁 출력 파일 구조

```
data/freemold/
├── complete_crawl/                    # 완벽한 크롤링 결과
│   ├── B001_detailed_complete.json    # B001 상세 정보
│   ├── B002_detailed_complete.json
│   ├── B003_detailed_complete.json
│   ├── B004_detailed_complete.json
│   ├── crawl_progress.json            # 진행상황 추적
│   ├── error_log.json                 # 에러 로그
│   └── crawl_stats.json               # 통계
│
├── images/                            # 다운로드된 이미지
│   ├── 88939_abc123def456.jpg
│   ├── 88938_def456ghi789.jpg
│   └── ...
│
└── crawled_products/                  # 기존 목록 데이터
    ├── B001/B001_products.json
    ├── B002/B002_products.json
    ├── B003/B003_products.json
    └── B004/B004_products.json
```

---

## ⏱️ 예상 소요 시간

### 지연 시간: 3-8초 (평균 5.5초)

| 카테고리 | 제품 수 | 최소 시간 | 최대 시간 | 평균 시간 |
|---------|--------|---------|---------|---------|
| **B001** | 9,870 | 8.2시간 | 21.9시간 | 15.1시간 |
| **B002** | 5,013 | 4.2시간 | 11.1시간 | 7.7시간 |
| **B003** | 5,291 | 4.4시간 | 11.7시간 | 8.1시간 |
| **B004** | 1,027 | 0.9시간 | 2.3시간 | 1.6시간 |
| **전체** | 21,201 | 17.7시간 | 47.0시간 | 32.4시간 |

### 💡 최적화 전략
1. **소규모 테스트**: 처음 10-50개로 테스트
2. **배치 실행**: 카테고리별로 분산 실행
3. **야간 실행**: 긴 크롤링은 야간에 실행
4. **중간 저장**: 10개마다 자동 저장 (중단 가능)

---

## 🔧 트러블슈팅

### 1. IP 차단 발생 시
```python
# 지연 시간 증가
delay_min = 5.0
delay_max = 15.0

# 또는 프록시 사용
use_proxy = True
proxy_url = "http://your-proxy:port"
```

### 2. 서버 에러 지속 시
```bash
# 재시도 횟수 증가
max_retries = 5

# 서버 에러 시 대기 시간 증가 (코드 수정)
await asyncio.sleep(30)  # 10초 → 30초
```

### 3. 메모리 부족 시
```python
# 배치 크기 축소
max_products = 100  # 한 번에 100개씩만
```

### 4. 진행상황 확인
```bash
# 완료된 제품 수
cat data/freemold/complete_crawl/crawl_progress.json | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Completed: {len(d[\"completed\"])}, Failed: {len(d[\"failed\"])}')"

# 통계 확인
cat data/freemold/complete_crawl/crawl_stats.json
```

---

## 📈 실행 예시

### 단계별 실행 계획

#### Phase 1: 테스트 (10분)
```bash
# B004 전체 크롤링 (1,027개, 약 1.6시간)
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B004/B004_products.json
```

#### Phase 2: 중규모 (15-20시간)
```bash
# B002 + B003 크롤링 (10,304개)
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B002/B002_products.json &

python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B003/B003_products.json &
```

#### Phase 3: 대규모 (15시간)
```bash
# B001 크롤링 (9,870개)
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B001/B001_products.json
```

---

## 🎯 다음 단계

### 1. 데이터 정제
```bash
python3 scripts/clean_crawled_data.py
```

### 2. RAG 시스템에 색인
```bash
python3 scripts/index_to_qdrant.py
```

### 3. 이미지 최적화
```bash
# 이미지 리사이즈/압축
python3 scripts/optimize_images.py
```

### 4. 데이터 분석
```bash
# 통계 및 품질 분석
python3 scripts/analyze_crawl_quality.py
```

---

## 📝 라이선스 및 주의사항

### ⚠️ 법적 주의사항
- **로봇 배제 표준** (robots.txt) 확인
- **이용 약관** 준수
- **적절한 크롤링 속도** 유지 (3-8초 지연)
- **서버 부하** 최소화

### 🤝 윤리적 크롤링
- 개인정보 수집 금지
- 저작권 존중
- 상업적 이용 시 허가 필요
- 서버 과부하 방지

---

## 📞 문의

문제 발생 시:
1. `error_log.json` 확인
2. GitHub Issues 등록
3. 크롤링 속도 조정

---

**작성일**: 2025-10-27
**버전**: 1.0.0
**작성자**: RAG Enterprise Team
