# 🎯 Freemold 크롤링 - 최종 실행 계획

## 📊 현재 상황

### ✅ 수집 완료
- **21,201개 제품 URL** (4개 카테고리)
- 제품 인덱스 (pIdx), 카테고리, 회사 URL

### ❌ 문제점
- **강력한 IP 차단**: 모든 상세 페이지 접근 시 서버 에러
- **누락 데이터**: 제품명, 이미지, 가격, 스펙, 재질 등

---

## 🛡️ IP 차단 현황 분석

### 차단 증거
```
❌ Server error detected (모든 제품 페이지)
❌ "An error occurred on the server when processing the URL"
❌ 3-8초 지연 + User-Agent 로테이션에도 불구하고 차단
```

### 차단 원인 추정
1. **세션 기반 차단**: 짧은 시간에 많은 요청
2. **행동 패턴 분석**: 로봇 행동 탐지 (직접 URL 접근)
3. **IP 블랙리스트**: 반복 크롤링으로 인한 IP 차단

---

## 🚀 해결 방안

### 방법 1: **극단적 지연 + 분산 IP**
```python
delay_min = 30.0  # 30초
delay_max = 120.0  # 2분
```

#### 예상 소요 시간
- B001 (9,870개): **82-329시간** (3.4-13.7일)
- 전체 (21,201개): **177-708시간** (7.4-29.5일)

#### 장점
- 인간 행동 패턴 모방
- 서버 부하 최소화

#### 단점
- ⏰ **너무 오래 걸림**
- 💸 비효율적

---

### 방법 2: **프록시 로테이션** ⭐ 추천
```python
# 프록시 풀 사용
proxies = [
    "proxy1.example.com:8080",
    "proxy2.example.com:8080",
    "proxy3.example.com:8080"
]
```

#### 프록시 서비스 옵션

| 서비스 | 가격 | IP 수 | 로테이션 | 추천도 |
|--------|------|-------|---------|--------|
| **Bright Data** | $500/월 | 수십만 | 자동 | ⭐⭐⭐⭐⭐ |
| **Smartproxy** | $75/월 | 4만+ | 자동 | ⭐⭐⭐⭐ |
| **Oxylabs** | $300/월 | 10만+ | 자동 | ⭐⭐⭐⭐⭐ |
| **ProxyMesh** | $10/월 | 10+ | 자동 | ⭐⭐⭐ |
| **무료 프록시** | 무료 | 100+ | 수동 | ⭐⭐ |

#### 예상 소요 시간
- 3-8초 지연 유지
- B001: **8-22시간**
- 전체: **18-47시간**

#### 구현
```python
crawler = AntiBlockCrawler(
    delay_min=3.0,
    delay_max=8.0,
    use_proxy=True,
    proxy_url="http://user:pass@proxy.provider.com:8080"
)
```

---

### 방법 3: **클라우드 VM 분산 크롤링** ⭐⭐ 추천

#### AWS/GCP/Azure 활용
```bash
# 5개 VM 인스턴스 생성 (각각 다른 IP)
vm1: B001 (0-2000)
vm2: B001 (2000-4000)
vm3: B001 (4000-6000)
vm4: B002 + B003
vm5: B004
```

#### 예상 소요 시간
- **병렬 실행**: 전체 약 **4-10시간**

#### 예상 비용
- AWS EC2 t3.micro: $0.01/시간 × 5 VM × 10시간 = **$0.50**
- GCP e2-micro: 무료 티어 사용 가능

#### 구현
```bash
# VM1에서
ssh vm1
python3 crawl_freemold_complete.py B001_products.json 0 2000

# VM2에서
ssh vm2
python3 crawl_freemold_complete.py B001_products.json 2000 2000

# ... 반복
```

---

### 방법 4: **VPN + 수동 IP 변경**

#### 프로세스
1. VPN 연결 (NordVPN, ExpressVPN 등)
2. 100개 제품 크롤링
3. VPN 서버 변경
4. 다음 100개 크롤링
5. 반복

#### 예상 소요 시간
- 100개/IP 기준: **212회 IP 변경** 필요
- VPN 변경 시간: 2분/회
- 총 시간: **약 60-80시간**

---

### 방법 5: **Selenium Grid + Tor 네트워크**

#### Tor 기반 IP 로테이션
```bash
# Tor 설치
brew install tor
tor

# Tor 프록시 사용
proxy = "socks5://localhost:9050"
```

#### IP 갱신 주기
- 10개 제품마다 Tor circuit 재시작
- 완전히 다른 IP로 변경

#### 예상 소요 시간
- **30-50시간**

---

## 📋 최종 권장 방법

### 🥇 1순위: **클라우드 VM 분산** (빠름 + 저렴)
```bash
# AWS 5개 VM으로 병렬 실행
# 예상: 4-10시간, 비용: $0.50-1.00
```

### 🥈 2순위: **프록시 서비스** (안정적 + 자동화)
```bash
# Smartproxy ($75/월) 사용
# 예상: 18-47시간
```

### 🥉 3순위: **Tor + 긴 지연** (무료 + 느림)
```bash
# Tor + 30-120초 지연
# 예상: 3-14일
```

---

## 🛠️ 실행 가이드

### Option A: 클라우드 VM 분산 크롤링

#### 1. AWS EC2 인스턴스 생성
```bash
# AWS CLI로 5개 인스턴스 생성
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type t3.micro \
  --count 5 \
  --key-name my-key \
  --security-group-ids sg-xxxxx
```

#### 2. 각 VM에 크롤러 배포
```bash
# 각 VM에서
git clone <repo>
cd rag-enterprise
pip install playwright aiohttp
playwright install chromium

# 할당된 범위 크롤링
python3 scripts/crawl_freemold_complete.py \
  data/freemold/crawled_products/B001/B001_products.json \
  0 \    # start_index
  2000   # max_products
```

#### 3. 결과 수집
```bash
# 모든 VM에서 결과 다운로드
scp vm1:~/rag-enterprise/data/freemold/complete_crawl/* ./results/
```

---

### Option B: 프록시 서비스 사용

#### 1. Smartproxy 가입
```bash
# https://smartproxy.com/ 가입
# Residential Proxy 선택
# 크레덴셜 획득: username:password@proxy.smartproxy.com:10001
```

#### 2. 크롤러 실행
```python
crawler = AntiBlockCrawler(
    delay_min=3.0,
    delay_max=8.0,
    use_proxy=True,
    proxy_url="http://username:password@proxy.smartproxy.com:10001"
)

await crawler.crawl_product_list(
    "data/freemold/crawled_products/B001/B001_products.json"
)
```

---

### Option C: Tor 네트워크 (무료)

#### 1. Tor 설치 및 실행
```bash
brew install tor
tor &  # Background 실행

# Tor SOCKS5 proxy: localhost:9050
```

#### 2. 크롤러 수정
```python
# playwright proxy 설정
context = await browser.new_context(
    proxy={"server": "socks5://localhost:9050"}
)

# 10개마다 Tor circuit 재시작
if idx % 10 == 0:
    subprocess.run(["killall", "-HUP", "tor"])
    await asyncio.sleep(10)
```

---

## ⏱️ 타임라인 예상

### 클라우드 VM 방식
| Day | 작업 | 소요시간 |
|-----|------|---------|
| D+0 | VM 셋업 + 배포 | 2시간 |
| D+0 | B004 크롤링 (테스트) | 1시간 |
| D+0~1 | B001-B003 병렬 크롤링 | 8시간 |
| D+1 | 데이터 수집 + 검증 | 2시간 |
| **총계** | | **~13시간** |

### 프록시 서비스 방식
| Day | 작업 | 소요시간 |
|-----|------|---------|
| D+0 | 프록시 가입 + 설정 | 1시간 |
| D+0~2 | 전체 크롤링 | 24시간 |
| D+2 | 검증 | 2시간 |
| **총계** | | **~27시간** |

---

## 💰 비용 분석

| 방법 | 초기 비용 | 운영 비용 | 시간 |
|------|----------|----------|------|
| **클라우드 VM** | $0 | $0.50-1 | 8-12시간 |
| **프록시 서비스** | $75 (월 구독) | $0 | 18-47시간 |
| **Tor (무료)** | $0 | $0 | 3-14일 |
| **VPN** | $10/월 | $0 | 60-80시간 |

---

## 🎯 다음 액션 아이템

### 즉시 실행 가능
1. ✅ **크롤러 코드 준비 완료**
2. ✅ **21,201개 제품 URL 수집 완료**
3. ⏳ **IP 우회 방법 선택** ← 현재 단계

### 선택 필요
- [ ] **Option A**: AWS VM 5개 생성 ($0.50, 8-12시간)
- [ ] **Option B**: Smartproxy 가입 ($75/월, 18-47시간)
- [ ] **Option C**: Tor 무료 사용 (0원, 3-14일)

### 실행 후
1. 데이터 정제 및 검증
2. 이미지 최적화
3. RAG 시스템 색인
4. Bottle Expert SKILL 통합

---

## 📞 의사결정 필요

**사용자님께 결정이 필요합니다**:

1. **예산**: 유료 서비스 사용 가능 여부?
   - ✅ 가능 → 프록시 서비스 ($75/월) 또는 AWS VM ($1)
   - ❌ 불가능 → Tor 무료 (3-14일)

2. **긴급도**: 언제까지 필요한가?
   - 🚨 급함 (1-2일) → AWS VM 병렬
   - ⏰ 여유 있음 (1-2주) → Tor 또는 VPN

3. **자동화 vs 수동**:
   - 🤖 자동화 선호 → AWS VM + 스크립트
   - 👨‍💻 수동 관리 가능 → VPN + 수동 변경

---

**다음 단계를 위해 선택해주세요!** 🚀
