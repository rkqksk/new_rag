# 🌐 Freemold Tor 크롤링 가이드

## ✅ 완료된 작업

### 1. Tor 설치 및 설정 완료
```bash
✅ Tor 0.4.8.19 installed
✅ Tor running on localhost:9050 (SOCKS5)
✅ Tor circuit 100% bootstrapped
✅ Test IP via Tor: 45.66.35.22 (confirmed working)
```

### 2. 완성된 크롤러
- **파일**: `/Users/oypnus/Project/rag-enterprise/scripts/crawl_freemold_tor.py`
- **특징**:
  - 무료 Tor 네트워크 활용
  - 10개 제품마다 자동 IP 변경
  - 30-120초 긴 지연 (봇 탐지 회피)
  - 진행상황 자동 저장 및 재개 기능
  - 이미지 다운로드 (제품당 1개)
  - IP 히스토리 추적

---

## 🚀 사용 방법

### 1단계: Tor 실행 확인
```bash
# Tor 실행 중인지 확인
lsof -i :9050 | grep LISTEN

# 실행 중이 아니면 시작
/opt/homebrew/opt/tor/bin/tor &

# Tor 부트스트랩 대기 (10-30초)
tail -f /tmp/tor.log  # Bootstrapped 100% 확인
```

### 2단계: 소규모 테스트 (권장)
```bash
# B004 카테고리에서 3개만 테스트
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B004/B004_products.json \
  0 \
  3

# 예상 시간: 3-6분 (3개 × 30-120초)
```

### 3단계: 전체 크롤링

#### Option A: 순차적 실행
```bash
# B004부터 시작 (가장 작음: 1,027개)
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B004/B004_products.json

# 예상: 8.5-34시간

# B002 (5,013개)
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B002/B002_products.json

# B003 (5,291개)
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B003/B003_products.json

# B001 (9,870개) - 마지막
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B001/B001_products.json
```

#### Option B: 배치 분할 (추천)
```bash
# B001을 3개 배치로 분할 (3,290개씩)

# Batch 1: 0-3290
nohup python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B001/B001_products.json \
  0 3290 > /tmp/tor_b001_batch1.log 2>&1 &

# 완료 후 Batch 2: 3290-6580
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B001/B001_products.json \
  3290 3290

# 완료 후 Batch 3: 6580-9870
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B001/B001_products.json \
  6580 3290
```

---

## ⏱️ 예상 소요 시간

| 카테고리 | 제품 수 | 최소 (30초/개) | 최대 (120초/개) | 평균 |
|---------|--------|---------------|----------------|------|
| **B004** | 1,027 | 8.5시간 | 34시간 | 21시간 |
| **B002** | 5,013 | 42시간 | 167시간 | 104시간 |
| **B003** | 5,291 | 44시간 | 176시간 | 110시간 |
| **B001** | 9,870 | 82시간 | 329시간 | 206시간 |
| **전체** | 21,201 | 177시간 (7.4일) | 706시간 (29.4일) | **441시간 (18.4일)** |

### 💡 현실적 예상
- **하루 8시간 크롤링**: ~55일
- **하루 24시간 크롤링**: ~18일
- **배치 분할 (3개 세션)**: ~6-7일

---

## 📊 진행상황 모니터링

### 실시간 로그 확인
```bash
# 실행 로그 (실시간)
tail -f /tmp/tor_crawl.log

# 의미있는 메시지만 필터링
tail -f /tmp/tor_crawl.log | grep -E "Crawling|Success|Failed|Renewing|IP:"
```

### 진행상황 파일
```bash
# 완료/실패 제품 수 확인
cat data/freemold/tor_crawl/crawl_progress.json

# 통계 확인
cat data/freemold/tor_crawl/crawl_stats.json

# IP 변경 히스토리
cat data/freemold/tor_crawl/ip_history.json
```

### 수식으로 계산
```bash
# 완료율 계산
python3 << 'EOF'
import json
with open("data/freemold/tor_crawl/crawl_progress.json") as f:
    data = json.load(f)
completed = len(data["completed"])
failed = len(data["failed"])
total = 21201  # or specific category total
progress = (completed / total) * 100
print(f"✅ Completed: {completed} ({progress:.1f}%)")
print(f"❌ Failed: {failed}")
print(f"⏳ Remaining: {total - completed - failed}")
EOF
```

---

## 🔧 트러블슈팅

### 1. Tor가 응답하지 않음
```bash
# Tor 재시작
killall tor
/opt/homebrew/opt/tor/bin/tor > /tmp/tor.log 2>&1 &

# 부트스트랩 확인
tail -f /tmp/tor.log  # "Bootstrapped 100%" 대기
```

### 2. IP가 변경되지 않음
```bash
# Tor circuit 수동 재시작
killall -HUP tor

# 새 IP 확인
curl --socks5 localhost:9050 -s https://check.torproject.org/api/ip
```

### 3. 크롤러가 멈춤
```bash
# 백그라운드 프로세스 확인
ps aux | grep crawl_freemold_tor

# 진행상황 파일로 이어서 시작
# (크롤러가 자동으로 완료된 제품 스킵)
python3 scripts/crawl_freemold_tor.py \
  data/freemold/crawled_products/B001/B001_products.json
```

### 4. 여전히 IP 차단 발생
```bash
# 지연 시간 증가 (코드 수정)
delay_min = 60.0   # 1분
delay_max = 300.0  # 5분

# IP 변경 빈도 증가
tor_renewal_interval = 5  # 5개마다
```

### 5. Chromium 크래시
```bash
# Headless 모드로 변경 (코드 수정)
browser = await p.chromium.launch(
    headless=True,  # False → True
    proxy={"server": self.tor_proxy}
)
```

---

## 📁 출력 파일 구조

```
data/freemold/
├── tor_crawl/                        # Tor 크롤링 결과
│   ├── B001_detailed_complete.json   # 완료된 제품 데이터
│   ├── B001_detailed_temp.json       # 중간 저장 (5개마다)
│   ├── crawl_progress.json           # 완료/실패 목록
│   ├── error_log.json                # 에러 로그
│   ├── ip_history.json               # IP 변경 히스토리
│   └── crawl_stats.json              # 통계
│
└── tor_images/                       # 다운로드된 이미지
    ├── 72566_abc123def456.jpg
    └── ...
```

---

## ✨ 주요 특징

### 1. 자동 IP 로테이션
```json
// ip_history.json
[
  {
    "ip": "45.66.35.22",
    "timestamp": "2025-10-27T01:52:00",
    "products_crawled": 0
  },
  {
    "ip": "185.220.101.42",
    "timestamp": "2025-10-27T02:10:00",
    "products_crawled": 10
  }
]
```

### 2. 진행상황 자동 저장
- **5개 제품마다** progress 파일 업데이트
- 중단 시 자동으로 이어서 크롤링 가능
- 완료된 제품 자동 스킵

### 3. 완전한 제품 데이터
```json
{
  "product_id": "72566",
  "product_name": "50ml PET 용기",
  "images": ["https://..."],
  "downloaded_images": ["data/freemold/tor_images/72566_abc.jpg"],
  "specifications": {
    "용량": "50ml",
    "재질": "PET",
    "넥사이즈": "24/410"
  },
  "capacities": [["50", "ml"]],
  "materials": ["PET"],
  "crawled_at": "2025-10-27T..."
}
```

---

## 🎯 다음 단계

### 크롤링 완료 후
1. **데이터 정제**
   ```bash
   python3 scripts/clean_tor_crawl_data.py
   ```

2. **이미지 최적화**
   ```bash
   python3 scripts/optimize_images.py data/freemold/tor_images
   ```

3. **RAG 시스템 색인**
   ```bash
   python3 scripts/index_to_qdrant.py data/freemold/tor_crawl/*.json
   ```

4. **품질 검증**
   ```bash
   python3 scripts/validate_crawl_quality.py
   ```

---

## 💡 팁

### 최적화 전략
1. **야간 실행**: 서버 부하가 적은 시간대 활용
2. **배치 실행**: 큰 카테고리는 3-4개 배치로 분할
3. **nohup 사용**: 터미널 종료해도 계속 실행
   ```bash
   nohup python3 scripts/crawl_freemold_tor.py ... > /tmp/tor.log 2>&1 &
   ```
4. **tmux/screen**: 세션 유지 도구 활용

### 비용 절감
- ✅ **완전 무료** (Tor 네트워크 활용)
- ⏳ 단, 시간이 오래 걸림 (18-55일)
- 💻 로컬 머신 리소스만 사용

---

## 📞 지원

### 문제 발생 시
1. `/tmp/tor.log` 확인 (Tor 로그)
2. `/tmp/tor_crawl.log` 확인 (크롤러 로그)
3. `data/freemold/tor_crawl/error_log.json` 확인

### 성공 사례
- B004 (1,027개): ~21시간
- 완료 시 통계 파일 생성
- IP 변경 ~100회 이상

---

**작성일**: 2025-10-27
**버전**: 1.0.0
**방법**: Tor 무료 크롤링
**예상**: 18-55일
