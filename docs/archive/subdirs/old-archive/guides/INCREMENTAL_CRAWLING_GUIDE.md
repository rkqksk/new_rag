# 증분 업데이트 크롤링 시스템 가이드

## 📋 개요

청진코리아 사이트의 카테고리별 독립 크롤러 시스템으로, 기존 데이터는 SKIP하고 새 제품만 수집하는 효율적인 증분 업데이트를 지원합니다.

## 🎯 주요 특징

### 1. 카테고리별 분리
```
crawl_jar_incremental.py       → Jar (4페이지, 단순 페이지네이션)
crawl_cap_pump_incremental.py  → Cap&Pump (14페이지, 그룹 페이지네이션)
crawl_bottle_adaptive.py        → Bottle (동적 페이지 탐색)
```

**장점**:
- 각 카테고리의 페이지네이션 패턴에 최적화된 로직
- Python 오류 최소화 (단일 목적 스크립트)
- 독립 실행으로 한 카테고리 업데이트만 필요할 때 효율적

### 2. 증분 업데이트 로직
```python
# 1. 기존 제품 ID 확인
existing_ids = load_existing_product_ids()

# 2. 전체 URL 수집
all_urls = collect_all_urls()

# 3. 새 제품 필터링
new_urls = [url for url in all_urls
            if extract_id(url) not in existing_ids]

# 4. 새 제품만 크롤링
for url in new_urls:
    crawl_product(url)
```

**효율성**:
- 1차 스캔: 빠른 URL 수집 (페이지 로딩만)
- 2차 스캔: 새 제품만 상세 크롤링
- 기존 제품 SKIP으로 작업 시간 단축

### 3. 적응형 페이지 탐색 (Bottle)
```
기존 방식 (실패):
페이지 1 → 2 → 3 → ... → 68 (순차 접근)
문제: 페이지 11-15, 21-35 등이 존재하지 않음

새 방식 (성공):
현재 그룹 확인 → 모든 페이지 크롤링 → paging-next → 반복
결과: 실제 존재하는 페이지만 접근
```

**Bottle 페이지 패턴**:
- 그룹 1: 1-5
- 그룹 2: 6-10
- 그룹 3: 16-20 (11-15 건너뜀)
- 그룹 4: 36-40 (21-35 건너뜀)
- 그룹 5: 66-68 (41-65 건너뜀)

## 🔄 사용 방법

### 수동 실행

#### Jar 카테고리만 업데이트
```bash
python crawl_jar_incremental.py

# 로그: crawl_jar_incremental.log
# 결과: data/crawled_products/category_Jar_YYYYMMDD_HHMMSS.json
```

#### Cap&Pump 카테고리만 업데이트
```bash
python crawl_cap_pump_incremental.py

# 로그: crawl_cap_pump_incremental.log
# 결과: data/crawled_products/category_Cap_Pump_YYYYMMDD_HHMMSS.json
```

#### Bottle 카테고리만 업데이트 (적응형)
```bash
python crawl_bottle_adaptive.py

# 로그: crawl_bottle_adaptive.log
# 결과: data/crawled_products/category_Bottle_YYYYMMDD_HHMMSS.json
```

### 자동 스케줄 실행

#### 스케줄러 시작
```bash
python crawl_scheduler.py

# 백그라운드 실행
nohup python crawl_scheduler.py > scheduler.log 2>&1 &
```

#### 스케줄 설정 (`config/crawl_schedule.yaml`)
```yaml
schedules:
  jar:
    enabled: true
    cron: "0 2 1 * *"  # 매월 1일 새벽 2시

  cap_pump:
    enabled: true
    cron: "0 3 1 * *"  # 매월 1일 새벽 3시

  bottle:
    enabled: true
    cron: "0 4 1 * *"  # 매월 1일 새벽 4시
```

**Cron 표현식 예시**:
- `"0 2 1 * *"` - 매월 1일 새벽 2시
- `"0 2 * * 1"` - 매주 월요일 새벽 2시
- `"0 2 */7 * *"` - 7일마다 새벽 2시
- `"0 */6 * * *"` - 6시간마다

## 📊 실행 결과 확인

### 로그 확인
```bash
# 최신 Bottle 크롤링 로그
tail -f crawl_bottle_adaptive.log

# 스케줄러 로그
tail -f logs/crawl_scheduler.log
```

### 요약 JSON 확인
```bash
# 최신 Bottle 요약
ls -lt data/crawled_products/category_Bottle_*.json | head -1

# 요약 내용 확인
cat data/crawled_products/category_Bottle_20251018_120000.json | jq
```

**요약 JSON 구조**:
```json
{
  "category": "Bottle",
  "total_urls_found": 680,
  "existing_products": 650,
  "new_products": 30,
  "success": 28,
  "error": 2,
  "timestamp": "2025-10-18T12:00:00"
}
```

### 크롤링 데이터 확인
```bash
# 총 제품 수
ls -1 data/crawled_products/idx_*.json | wc -l

# 최신 10개 제품
ls -lt data/crawled_products/idx_*.json | head -10

# 특정 제품 확인
cat data/crawled_products/idx_960.json | jq
```

## 🔧 문제 해결

### 페이지네이션 오류
**증상**: "버튼 찾기 실패" 경고 반복

**원인**: 페이지 그룹 변경이 예상과 다름

**해결**: Bottle은 `crawl_bottle_adaptive.py` 사용 (동적 탐색)

### 중복 제품
**증상**: 같은 제품이 여러 번 크롤링됨

**원인**: URL 중복 제거 실패

**해결**:
```python
# 스크립트 내부에서 자동 처리됨
unique_urls = list(set(all_urls))
```

### 크롤링 멈춤
**증상**: 특정 페이지에서 무한 대기

**원인**: AJAX 로딩 타임아웃

**해결**:
```python
# 대기 시간 조정
await asyncio.sleep(5)  # 기본 5초

# 필요시 늘리기
await asyncio.sleep(10)  # 느린 네트워크
```

## 📈 성능 최적화

### 1차 스캔 속도
```python
# URL 수집만 (빠름)
# 평균: 0.5초/페이지
# Bottle 68페이지 → 약 34초
```

### 2차 스캔 속도
```python
# 제품 상세 크롤링 (느림)
# 평균: 8초/제품 (이미지 다운로드 포함)
# 680개 제품 → 약 1.5시간
```

### 증분 업데이트 효과
```python
# 첫 크롤: 680개 제품 → 1.5시간
# 월간 업데이트: 30개 신제품 → 4분
# 시간 절약: 96%!
```

## 🗂️ 파일 구조

```
rag-enterprise/
├── crawl_jar_incremental.py        # Jar 증분 크롤러
├── crawl_cap_pump_incremental.py   # Cap&Pump 증분 크롤러
├── crawl_bottle_adaptive.py        # Bottle 적응형 크롤러
├── crawl_scheduler.py               # 스케줄러
├── config/
│   └── crawl_schedule.yaml         # 스케줄 설정
├── data/
│   └── crawled_products/           # 크롤링 결과
│       ├── idx_*.json              # 제품 데이터
│       ├── images/                 # 이미지
│       ├── print_area/             # 인쇄영역 PDF
│       └── category_*.json         # 카테고리별 요약
├── logs/
│   ├── crawl_jar_incremental.log
│   ├── crawl_cap_pump_incremental.log
│   ├── crawl_bottle_adaptive.log
│   └── crawl_scheduler.log
└── docs/
    └── INCREMENTAL_CRAWLING_GUIDE.md  # 이 문서
```

## 🚀 다음 단계

### 1. 첫 완전 크롤링
```bash
# 각 카테고리 순차 실행
python crawl_jar_incremental.py
python crawl_cap_pump_incremental.py
python crawl_bottle_adaptive.py
```

### 2. 데이터 검증
```bash
# CSV 리포트 생성
python scripts/generate_crawl_report.py

# 누락된 제품 확인
cat data/crawled_products/master_report.csv
```

### 3. 스케줄러 활성화
```bash
# 스케줄러 시작
python crawl_scheduler.py

# 또는 백그라운드 실행
nohup python crawl_scheduler.py > scheduler.log 2>&1 &
```

### 4. 모니터링 설정
```yaml
# config/crawl_schedule.yaml
notifications:
  slack:
    enabled: true
    webhook_url: "YOUR_WEBHOOK_URL"
    on_error: true
    on_success: true
```

## ⚠️ 주의사항

1. **서버 부하**: 제품 간 2초 딜레이 유지
2. **네트워크 안정성**: AJAX 대기 시간 충분히 설정
3. **데이터 백업**: 크롤링 전 기존 데이터 백업
4. **로그 모니터링**: 에러 발생 시 즉시 확인

## 📝 변경 이력

- **2025-10-18**: 초기 버전 작성
  - 카테고리별 분리 크롤러 구현
  - 증분 업데이트 로직 추가
  - Bottle 적응형 페이지 탐색 구현
  - 스케줄러 시스템 추가

---

**작성자**: RAG Enterprise Team
**버전**: 1.0.0
**최종 업데이트**: 2025-10-18
