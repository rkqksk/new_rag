# UI 테스트 가이드 - 인기도 기반 추천 시스템

**목적**: Phase 2 인기도 기반 추천 시스템이 UI에서 정상 작동하는지 확인

---

## 🚀 서버 시작

### 방법 1: 직접 실행
```bash
cd /Users/oypnus/Project/rag-enterprise

# 백엔드 서버 실행
python run_chat_server.py

# 서버 확인
curl http://localhost:8000/health
```

### 방법 2: Docker (권장)
```bash
cd /Users/oypnus/Project/rag-enterprise

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

**서버 주소**: `http://localhost:8000`

---

## 📋 테스트 시나리오

### 시나리오 1: 기본 검색 (인기도 랭킹 확인)

**목적**: 검색 결과가 인기도에 따라 재정렬되는지 확인

#### 1.1 새 세션 시작
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_1",
    "user_id": "test_user",
    "query": "50ml 용기 보여줘"
  }'
```

**확인 포인트**:
- ✅ `ranking_applied: "popularity"` 포함
- ✅ `products` 배열에 제품 리스트
- ✅ 인기도 높은 제품이 상위에 위치

**예상 응답**:
```json
{
  "products": [
    {
      "idx": "idx_123",
      "product_name": "50ml PET 브로우용기",
      "popularity_score": 85.5,
      "relevance_score": 90.0,
      "final_score": 87.15
    },
    ...
  ],
  "response": "32개 제품을 찾았습니다.",
  "ranking_applied": "popularity",
  "filters_applied": {"capacity_ml": 50}
}
```

---

### 시나리오 2: 필터 적용 (컨텍스트 인기도 확인)

**목적**: 필터 적용 시 해당 카테고리 내 인기도가 반영되는지 확인

#### 2.1 초기 검색
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_2",
    "user_id": "test_user",
    "query": "100ml 용기"
  }'
```

#### 2.2 재질 필터 추가
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_2",
    "user_id": "test_user",
    "query": "PET만 보여줘"
  }'
```

**확인 포인트**:
- ✅ `ranking_applied: "popularity_with_context"` 포함
- ✅ `filters_applied: {"capacity_ml": 100, "material": "PET"}`
- ✅ PET 카테고리 내 인기 제품이 상위에 위치

**예상 응답**:
```json
{
  "products": [
    {
      "idx": "idx_456",
      "product_name": "100ml PET 브로우용기",
      "specifications": {
        "material": "PET",
        "capacity_ml": 100
      },
      "popularity_score": 90.0,  // PET 카테고리 내 인기도
      "context_boost": 1.2
    },
    ...
  ],
  "ranking_applied": "popularity_with_context",
  "filters_applied": {
    "capacity_ml": 100,
    "material": "PET"
  }
}
```

---

### 시나리오 3: 샘플 신청 (행동 추적 확인)

**목적**: 샘플 신청이 정상적으로 추적되는지 확인

#### 3.1 샘플 신청 제출
```bash
curl -X POST http://localhost:8000/analytics/sample-request \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session_3",
    "product_idx": "idx_123",
    "intended_use": "로션",
    "company_name": "테스트 회사",
    "contact_name": "홍길동",
    "contact_phone": "010-1234-5678",
    "contact_email": "test@example.com",
    "notes": "테스트 샘플 신청"
  }'
```

**확인 포인트**:
- ✅ `status: "success"`
- ✅ `request_id` 반환
- ✅ DB에 저장 확인

**예상 응답**:
```json
{
  "status": "success",
  "message": "샘플 신청이 접수되었습니다.",
  "request_id": "test_user_20250125143000"
}
```

#### 3.2 추적기 상태 확인
```bash
curl http://localhost:8000/analytics/status
```

**예상 응답**:
```json
{
  "status": "active",
  "queue_size": 1,
  "batch_size": 100,
  "flush_interval_seconds": 60
}
```

---

### 시나리오 4: 클릭 추적

**목적**: 클릭 이벤트가 정상적으로 추적되는지 확인

#### 4.1 클릭 이벤트 전송
```bash
curl -X POST http://localhost:8000/analytics/track/click \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session_4",
    "product_idx": "idx_789",
    "product_code": "BOTTLE-PET-50",
    "product_name": "50ml PET 브로우용기",
    "category": "Bottle",
    "material": "PET",
    "capacity_ml": 50,
    "neck_size": "24/410",
    "click_position": 1,
    "search_query": "50ml 용기",
    "referrer": "search_result"
  }'
```

**확인 포인트**:
- ✅ `status: "success"`
- ✅ 에러 없이 처리

**예상 응답**:
```json
{
  "status": "success",
  "message": "Click event tracked"
}
```

---

### 시나리오 5: 대화 흐름 (누적 필터 + 인기도)

**목적**: 대화식 검색에서 인기도가 지속적으로 반영되는지 확인

#### 5.1 초기 검색
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_5",
    "user_id": "test_user",
    "query": "로션 용기 찾아줘"
  }'
```

#### 5.2 용량 필터
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_5",
    "user_id": "test_user",
    "query": "50ml만 보여줘"
  }'
```

#### 5.3 재질 필터
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_5",
    "user_id": "test_user",
    "query": "PET만"
  }'
```

**확인 포인트**:
- ✅ 각 단계마다 `ranking_applied` 포함
- ✅ 필터가 누적됨: `{"product_type": "bottle", "capacity_ml": 50, "material": "PET"}`
- ✅ 최종 결과에서 PET 50ml 로션 용기 중 인기 제품 상위 노출

---

## 🔍 검증 방법

### 1. API 응답 검증

#### 인기도 랭킹 적용 확인
```bash
# 검색 결과에서 ranking_applied 필드 확인
response=$(curl -s -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "user_id": "test", "query": "50ml"}')

echo $response | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('✅ Ranking applied:', data.get('ranking_applied', 'NOT FOUND'))
print('✅ Products count:', len(data.get('products', [])))
"
```

#### 필터 누적 확인
```bash
# 2단계 필터 적용 후 확인
# 1단계: 50ml
curl -s -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_filter", "user_id": "test", "query": "50ml 용기"}' > /dev/null

# 2단계: PET 추가
response=$(curl -s -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_filter", "user_id": "test", "query": "PET만"}')

echo $response | python3 -c "
import sys, json
data = json.load(sys.stdin)
filters = data.get('filters_applied', {})
print('✅ Filters:', filters)
print('✅ Has capacity?', 'capacity_ml' in filters or 'capacity' in filters)
print('✅ Has material?', 'material' in filters)
"
```

### 2. DB 확인

#### 행동 로그 확인
```bash
# PostgreSQL 연결 후
docker-compose exec postgres psql -U raguser -d rag_enterprise
```

```sql
-- 최근 검색 로그
SELECT
    user_id,
    query,
    result_count,
    searched_at
FROM search_logs
ORDER BY searched_at DESC
LIMIT 5;

-- 최근 클릭 로그
SELECT
    user_id,
    product_idx,
    product_name,
    click_position,
    clicked_at
FROM click_logs
ORDER BY clicked_at DESC
LIMIT 5;

-- 샘플 신청 확인
SELECT
    user_id,
    product_idx,
    company_name,
    intended_use,
    requested_at,
    status
FROM sample_requests
ORDER BY requested_at DESC
LIMIT 5;
```

### 3. 로그 파일 확인

#### 행동 추적 백업 로그
```bash
# 최신 백업 파일 확인
ls -lht logs/analytics/backup_*.jsonl | head -5

# 내용 확인
tail -20 logs/analytics/backup_*.jsonl | python3 -m json.tool
```

#### 인기도 계산 로그
```bash
# 계산 로그 확인
cat logs/popularity_calculation.log
```

---

## 🐛 문제 해결

### 문제 1: ranking_applied 필드가 없음

**원인**: PopularityRanker가 초기화되지 않음

**해결**:
```bash
# EnhancedContextualRAG 재시작
pkill -f run_chat_server
python run_chat_server.py
```

### 문제 2: 인기도 스코어가 모두 0

**원인**: product_popularity 테이블이 비어있음

**해결**:
```bash
# 인기도 계산 수동 실행
python3 scripts/calculate_popularity.py

# 또는 더미 데이터 생성
# TODO: 더미 데이터 스크립트 작성
```

### 문제 3: 샘플 신청이 저장되지 않음

**원인**: DB 연결 실패

**해결**:
```bash
# DB 연결 확인
docker-compose ps postgres

# 백업 파일 확인
ls logs/analytics/backup_*.jsonl
```

---

## 📊 기대 결과

### 성공 기준

✅ **검색 기능**
- 검색 시 `ranking_applied: "popularity"` 반환
- 제품 리스트가 인기도 순으로 정렬
- 응답 시간 < 200ms

✅ **필터 기능**
- 필터 적용 시 `ranking_applied: "popularity_with_context"` 반환
- 필터가 누적됨 (PET + 50ml = 둘 다 적용)
- 카테고리별 인기도 반영

✅ **행동 추적**
- 샘플 신청 즉시 저장 (status: success)
- 클릭 이벤트 추적 (에러 없음)
- DB 또는 백업 파일에 저장 확인

✅ **대화 흐름**
- 세션 유지 (동일 session_id)
- 컨텍스트 누적 (이전 검색 기억)
- 자연스러운 대화식 검색

---

## 🎯 다음 단계

### 1. 실제 데이터 확인
```bash
# 실제 제품 데이터로 테스트
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "real_test",
    "user_id": "real_user",
    "query": "브로우용기"
  }'
```

### 2. 인기도 계산 실행
```bash
# 인기도 스코어 생성
python3 scripts/calculate_popularity.py

# 결과 확인
cat logs/analytics/popularity_scores_*.json | python3 -m json.tool | head -50
```

### 3. 프론트엔드 통합
- UI에서 검색 기능 테스트
- 필터 적용 UI 테스트
- 샘플 신청 폼 테스트
- 클릭 이벤트 자동 전송

---

**작성일**: 2025-01-25
**작성자**: Claude Code
**버전**: 1.0.0
