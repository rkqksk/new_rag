# 인기도 스코어 계산 시스템 설정 가이드

## 개요

사용자 행동 데이터를 기반으로 제품 인기도를 계산하고 `product_popularity` 테이블을 업데이트하는 시스템입니다.

---

## 시스템 구성

### 1. 핵심 컴포넌트

| 컴포넌트 | 파일 | 역할 |
|---------|------|------|
| **계산 엔진** | `src/analytics/popularity_calculator.py` | 인기도 스코어 계산 로직 |
| **실행 스크립트** | `scripts/calculate_popularity.py` | 주기적 실행 스크립트 |
| **테스트** | `scripts/test_popularity_calculator.py` | 로직 검증 |

### 2. 계산 알고리즘

#### 가중치 기반 스코어
```
총 스코어 = (샘플 신청 × 10.0) + (클릭 × 3.0) + (검색 × 1.0) + (대화 × 0.5)
```

- **샘플 신청** (10.0): 가장 강력한 구매 의도 신호
- **클릭** (3.0): 중간 수준의 관심도
- **검색 출현** (1.0): 기본 노출
- **대화 언급** (0.5): 약한 관심도

#### 시간 감쇠
```
감쇠 계수 = 0.5 ^ (days_ago / 7)
```

- **오늘**: 1.0
- **7일 전**: 0.5 (반감기)
- **14일 전**: 0.25
- **30일 전**: 0.051

최근 데이터에 더 높은 가중치를 부여하여 트렌드 반영

#### 트렌드 부스트
```
트렌드 부스트 = f(최근 7일 스코어 / 이전 7-14일 스코어)
```

- **2배 이상 증가**: 1.5x (최대 부스트)
- **증가세 (0~100%)**: 1.0x ~ 1.5x
- **동일**: 1.0x
- **감소세**: 0.8x ~ 1.0x (최소 패널티)

상승세 제품에 가산점을 부여하여 트렌드 반영

#### 정규화
```
정규화 스코어 = (원본 스코어 / 최대 스코어) × 100
```

0-100 스케일로 변환하여 직관적인 비교 가능

---

## 설치 및 설정

### 1. 의존성 설치

```bash
cd /Users/oypnus/Project/rag-enterprise
pip install -r requirements.txt
```

### 2. 테스트 실행

```bash
# 계산 로직 검증
python3 scripts/test_popularity_calculator.py
```

**기대 출력**:
```
=== 시간 감쇠 테스트 ===
0일 전: 1.000 (기대: 1.000) ✅
7일 전: 0.500 (기대: 0.500) ✅
...

=== 트렌드 부스트 테스트 ===
3배 증가 (최대 부스트): 1.50x ✅
...

✅ 모든 테스트 완료
```

### 3. 수동 실행

```bash
# 인기도 스코어 계산 (1회)
python3 scripts/calculate_popularity.py
```

**기대 출력**:
```
[2025-01-25 14:30:00] 인기도 스코어 계산 시작
제품 메타데이터 로드 중...
총 1234개 제품
인기도 스코어 계산 중...
총 567개 제품 스코어 계산 완료
카테고리별 스코어 계산 중...
카테고리별 스코어 계산 완료
product_popularity 테이블 업데이트 중...
DB 업데이트 완료

=== 계산 결과 요약 ===
총 제품 수: 567

상위 10개 제품:
1. idx_123 (50ml PET 브로우용기)
   스코어: 100.00
   샘플신청: 5, 클릭: 12
   트렌드: +45.2% (부스트: 1.23x)
...

[2025-01-25 14:30:15] 인기도 스코어 계산 완료
```

---

## 자동 실행 설정 (Cron Job)

### 1. Cron 설정

```bash
# Cron 편집
crontab -e
```

### 2. Cron 작업 추가

```cron
# 인기도 스코어 계산 (6시간마다)
0 */6 * * * cd /Users/oypnus/Project/rag-enterprise && /usr/bin/python3 scripts/calculate_popularity.py >> logs/popularity_calculation.log 2>&1

# 대안: 매일 오전 2시 실행
0 2 * * * cd /Users/oypnus/Project/rag-enterprise && /usr/bin/python3 scripts/calculate_popularity.py >> logs/popularity_calculation.log 2>&1
```

**설명**:
- `0 */6 * * *`: 6시간마다 (0시, 6시, 12시, 18시)
- `0 2 * * *`: 매일 오전 2시
- `>> logs/popularity_calculation.log`: 로그 파일에 출력 저장
- `2>&1`: 에러도 로그 파일에 저장

### 3. 로그 디렉토리 생성

```bash
mkdir -p /Users/oypnus/Project/rag-enterprise/logs
```

### 4. Cron 작업 확인

```bash
# 등록된 cron 작업 확인
crontab -l

# Cron 로그 확인
tail -f logs/popularity_calculation.log
```

---

## 시스템워크 설정 (macOS 대안)

Cron 대신 launchd를 사용할 수도 있습니다.

### 1. plist 파일 생성

```bash
nano ~/Library/LaunchAgents/com.ragenterprise.popularity.plist
```

### 2. plist 내용

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ragenterprise.popularity</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/oypnus/Project/rag-enterprise/scripts/calculate_popularity.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/oypnus/Project/rag-enterprise</string>

    <key>StartInterval</key>
    <integer>21600</integer> <!-- 6시간 (초 단위) -->

    <key>StandardOutPath</key>
    <string>/Users/oypnus/Project/rag-enterprise/logs/popularity_calculation.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/oypnus/Project/rag-enterprise/logs/popularity_calculation_error.log</string>

    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

### 3. launchd 등록

```bash
# 등록
launchctl load ~/Library/LaunchAgents/com.ragenterprise.popularity.plist

# 시작
launchctl start com.ragenterprise.popularity

# 상태 확인
launchctl list | grep ragenterprise

# 해제 (필요시)
launchctl unload ~/Library/LaunchAgents/com.ragenterprise.popularity.plist
```

---

## Docker 환경 설정

### 1. docker-compose.yml 수정

```yaml
services:
  popularity-calculator:
    build: .
    container_name: rag_popularity_calculator
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=rag_enterprise
      - DB_USER=raguser
      - DB_PASSWORD=${DB_PASSWORD}
    volumes:
      - ./logs:/app/logs
    command: |
      sh -c "while true; do
        python3 scripts/calculate_popularity.py
        sleep 21600  # 6시간 대기
      done"
    depends_on:
      - postgres
    networks:
      - rag_network
```

### 2. Docker 실행

```bash
# 컨테이너 시작
docker-compose up -d popularity-calculator

# 로그 확인
docker-compose logs -f popularity-calculator

# 수동 실행
docker-compose exec popularity-calculator python3 scripts/calculate_popularity.py
```

---

## 모니터링

### 1. 로그 확인

```bash
# 최근 100줄
tail -100 logs/popularity_calculation.log

# 실시간 모니터링
tail -f logs/popularity_calculation.log

# 에러만 확인
grep ERROR logs/popularity_calculation.log
```

### 2. 계산 상태 확인

```bash
# 최근 계산 시간
ls -lh logs/analytics/popularity_scores_*.json | tail -5

# 계산 결과 확인
cat logs/analytics/popularity_scores_20250125_143000.json | python3 -m json.tool
```

### 3. DB 확인

```sql
-- 최근 업데이트 시간
SELECT MAX(last_updated) FROM product_popularity;

-- 상위 10개 제품
SELECT
    product_idx,
    product_name,
    normalized_score,
    trend_percentage,
    last_updated
FROM product_popularity
ORDER BY normalized_score DESC
LIMIT 10;

-- 급상승 제품
SELECT
    product_idx,
    product_name,
    trend_percentage,
    normalized_score
FROM product_popularity
WHERE trend_percentage > 50
ORDER BY trend_percentage DESC
LIMIT 10;
```

---

## 문제 해결

### 1. 계산 실패

**증상**: 스크립트가 에러로 종료

**해결**:
```bash
# 로그 확인
cat logs/popularity_calculation_error.log

# 수동 실행으로 디버깅
python3 scripts/calculate_popularity.py
```

### 2. DB 연결 실패

**증상**: "DB 저장 실패" 메시지

**해결**:
- DB 연결 정보 확인 (.env 파일)
- PostgreSQL 서비스 상태 확인
- 백업 파일 확인 (`logs/analytics/backup_*.jsonl`)

### 3. 메모리 부족

**증상**: Out of Memory 에러

**해결**:
- 배치 크기 조정 (`BehaviorTracker.batch_size`)
- 집계 기간 단축 (`window_days=30` → `window_days=14`)
- 메모리 증설

### 4. 계산 시간 초과

**증상**: 6시간 안에 완료되지 않음

**해결**:
- 인덱스 추가 확인 (DB 스키마)
- 병렬 처리 구현
- 계산 주기 조정 (6시간 → 12시간)

---

## 성능 최적화

### 1. DB 인덱스

```sql
-- 필수 인덱스 확인
SELECT indexname FROM pg_indexes
WHERE tablename IN ('sample_requests', 'click_logs', 'search_logs', 'conversation_logs');

-- 누락된 인덱스 추가
CREATE INDEX idx_sample_requests_date ON sample_requests(requested_at DESC);
CREATE INDEX idx_click_logs_date ON click_logs(clicked_at DESC);
CREATE INDEX idx_search_logs_date ON search_logs(searched_at DESC);
CREATE INDEX idx_conversation_logs_date ON conversation_logs(created_at DESC);
```

### 2. 계산 최적화

```python
# PopularityCalculator 초기화 시 설정
calculator = PopularityCalculator()
calculator.DECAY_HALFLIFE_DAYS = 5  # 더 빠른 감쇠 (기본: 7)
calculator.batch_size = 500  # 배치 크기 증가
```

### 3. 병렬 처리

```python
# calculate_popularity.py 수정
import asyncio

async def process_batch(products_batch):
    # 제품별 스코어 계산
    pass

async def main():
    # 제품을 배치로 나누어 병렬 처리
    batches = [products[i:i+100] for i in range(0, len(products), 100)]
    await asyncio.gather(*[process_batch(batch) for batch in batches])
```

---

## 백업 및 복구

### 1. 자동 백업

계산 실패 시 자동으로 `logs/analytics/backup_*.jsonl` 파일에 저장됩니다.

### 2. 수동 복구

```python
# backup_*.jsonl 파일에서 복구
python3 scripts/restore_from_backup.py logs/analytics/backup_20250125_143000.jsonl
```

---

## 다음 단계

Phase 2.3 완료 후:
- **Phase 2.4**: 검색 결과 정렬 로직에 인기도 스코어 통합
- **Phase 2.5**: 대시보드 및 분석 API 구현

---

**마지막 업데이트**: 2025-01-25
**작성자**: RAG Enterprise Team
