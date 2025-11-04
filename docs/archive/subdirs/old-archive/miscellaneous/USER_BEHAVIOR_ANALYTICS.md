# 사용자 행동 분석 시스템 (User Behavior Analytics)

인기도 기반 추천을 위한 데이터 수집 및 분석 시스템

## 📋 개요

### 목표

사용자 행동 데이터를 수집하고 분석하여:
- ✅ **인기 제품 자동 상단 노출**: 조건과 무관하게 인기 제품 우선 표시
- ✅ **개인화 추천**: 사용자 패턴 기반 맞춤 추천
- ✅ **트렌드 분석**: 재질/용도/용량별 인기 제품 파악

### 수집 데이터

1. **샘플 신청 데이터**: 실제 구매 의도가 있는 제품
2. **검색 행동 데이터**: 어떤 키워드로 검색하는지
3. **클릭 행동 데이터**: 어떤 제품을 자주 클릭하는지
4. **대화 로그 데이터**: 사용자 대화 패턴 및 의도

---

## 🗄️ DB 스키마 설계

### 1. 샘플 신청 테이블 (sample_requests)

가장 강력한 신호: **실제 구매 의도**

```sql
CREATE TABLE sample_requests (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 제품 정보
    product_idx VARCHAR(50) NOT NULL,
    product_code VARCHAR(100),
    product_name VARCHAR(500),
    category VARCHAR(100),        -- Bottle, Pump, Cap, etc.
    material VARCHAR(50),          -- PET, HDPE, PP, etc.
    capacity_ml FLOAT,
    neck_size VARCHAR(20),

    -- 사용자 입력 정보
    intended_use VARCHAR(200),     -- 용도: 로션, 크림, 세럼, etc.
    company_name VARCHAR(200),
    contact_info JSONB,            -- {name, phone, email}

    -- 메타 정보
    requested_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, shipped, cancelled
    notes TEXT,

    -- 인덱스
    INDEX idx_product (product_idx),
    INDEX idx_material (material),
    INDEX idx_capacity (capacity_ml),
    INDEX idx_use (intended_use),
    INDEX idx_requested_at (requested_at)
);
```

**중요도 가중치**: 10.0 (실제 구매 의도)

---

### 2. 검색 로그 테이블 (search_logs)

사용자가 **무엇을 찾는지** 파악

```sql
CREATE TABLE search_logs (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 검색 쿼리
    query TEXT NOT NULL,
    normalized_query TEXT,         -- 정규화된 쿼리

    -- 추출된 필터
    filters JSONB,                 -- {material, capacity, neck_size, etc.}

    -- 검색 결과
    result_count INTEGER,
    result_product_indices TEXT[], -- 검색된 제품 idx 배열

    -- 의도 분류
    intent VARCHAR(50),            -- search, filter, reference, etc.
    product_type VARCHAR(50),      -- bottle, pump, cap, etc.

    -- 메타 정보
    searched_at TIMESTAMP DEFAULT NOW(),
    response_time_ms INTEGER,

    -- 인덱스
    INDEX idx_user (user_id),
    INDEX idx_session (session_id),
    INDEX idx_query (query),
    INDEX idx_filters (filters),
    INDEX idx_searched_at (searched_at)
);
```

**중요도 가중치**: 1.0 (관심 표시)

---

### 3. 클릭 로그 테이블 (click_logs)

사용자가 **어떤 제품에 관심 있는지** 파악

```sql
CREATE TABLE click_logs (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 클릭된 제품
    product_idx VARCHAR(50) NOT NULL,
    product_code VARCHAR(100),
    product_name VARCHAR(500),
    category VARCHAR(100),
    material VARCHAR(50),
    capacity_ml FLOAT,

    -- 클릭 컨텍스트
    click_position INTEGER,        -- 검색 결과에서 몇 번째 위치
    search_query TEXT,             -- 어떤 검색에서 클릭했는지
    referrer VARCHAR(50),          -- search_result, related_products, etc.

    -- 행동 패턴
    time_on_page_seconds INTEGER,  -- 상세 페이지에서 머문 시간
    viewed_images BOOLEAN,         -- 이미지 확대 여부
    checked_specs BOOLEAN,         -- 스펙 탭 클릭 여부
    checked_compatibility BOOLEAN, -- 호환성 확인 여부

    -- 메타 정보
    clicked_at TIMESTAMP DEFAULT NOW(),

    -- 인덱스
    INDEX idx_product (product_idx),
    INDEX idx_user (user_id),
    INDEX idx_session (session_id),
    INDEX idx_material (material),
    INDEX idx_capacity (capacity_ml),
    INDEX idx_clicked_at (clicked_at)
);
```

**중요도 가중치**: 3.0 (높은 관심)

---

### 4. 대화 로그 테이블 (conversation_logs)

사용자 **대화 패턴 및 의도** 파악

```sql
CREATE TABLE conversation_logs (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 대화 내용
    user_message TEXT NOT NULL,
    bot_response TEXT,

    -- 대화 분석
    intent VARCHAR(50),            -- search, filter, reference, compatibility, etc.
    reference_type VARCHAR(50),    -- number, demonstrative, document, etc.
    state VARCHAR(50),             -- SEARCHING, FILTERING, FOCUSED, etc.

    -- 컨텍스트
    focused_product VARCHAR(50),   -- 포커스된 제품 idx
    active_filters JSONB,          -- 활성 필터

    -- 결과
    products_shown TEXT[],         -- 표시된 제품 idx 배열
    action_taken VARCHAR(50),      -- search, apply_filter, show_detail, etc.

    -- 메타 정보
    created_at TIMESTAMP DEFAULT NOW(),

    -- 인덱스
    INDEX idx_user (user_id),
    INDEX idx_session (session_id),
    INDEX idx_intent (intent),
    INDEX idx_focused_product (focused_product),
    INDEX idx_created_at (created_at)
);
```

**중요도 가중치**: 0.5 (대화 흐름 파악)

---

### 5. 제품 인기도 집계 테이블 (product_popularity)

**실시간 인기도 스코어 캐싱**

```sql
CREATE TABLE product_popularity (
    product_idx VARCHAR(50) PRIMARY KEY,

    -- 제품 메타데이터
    product_code VARCHAR(100),
    product_name VARCHAR(500),
    category VARCHAR(100),
    material VARCHAR(50),
    capacity_ml FLOAT,
    neck_size VARCHAR(20),

    -- 인기도 메트릭 (최근 30일)
    sample_request_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    search_appearance_count INTEGER DEFAULT 0,
    conversation_mention_count INTEGER DEFAULT 0,

    -- 가중치 적용 스코어
    total_score FLOAT DEFAULT 0,

    -- 카테고리별 스코어 (재질/용도/용량별)
    score_by_material JSONB,       -- {PET: 85.5, HDPE: 20.3, ...}
    score_by_use JSONB,            -- {로션: 90.2, 크림: 45.1, ...}
    score_by_capacity JSONB,       -- {50ml: 75.0, 100ml: 60.5, ...}

    -- 트렌드 (최근 7일 vs 이전 7일)
    trend_percentage FLOAT,        -- +15.5 (증가), -8.2 (감소)

    -- 메타 정보
    last_updated TIMESTAMP DEFAULT NOW(),

    -- 인덱스
    INDEX idx_total_score (total_score DESC),
    INDEX idx_material (material),
    INDEX idx_capacity (capacity_ml),
    INDEX idx_category (category)
);
```

---

## 📊 인기도 스코어 계산 알고리즘

### 기본 공식

```python
popularity_score = (
    sample_requests * 10.0 +      # 가장 강력한 신호
    clicks * 3.0 +                # 높은 관심
    searches * 1.0 +              # 관심 표시
    conversations * 0.5           # 대화 흐름
) * time_decay_factor * trend_boost
```

### 시간 감쇠 (Time Decay)

최근 데이터에 더 높은 가중치:

```python
def time_decay_factor(days_ago):
    """
    0일 전: 1.0
    7일 전: 0.8
    14일 전: 0.6
    30일 전: 0.3
    """
    return max(0.3, 1.0 - (days_ago / 30) * 0.7)
```

### 트렌드 부스트 (Trend Boost)

상승세 제품 우대:

```python
def trend_boost(recent_score, previous_score):
    """
    상승률 +50% 이상: 1.2배
    상승률 +20~50%: 1.1배
    변화 없음: 1.0배
    하락: 0.9배
    """
    if previous_score == 0:
        return 1.0

    change_percent = ((recent_score - previous_score) / previous_score) * 100

    if change_percent >= 50:
        return 1.2
    elif change_percent >= 20:
        return 1.1
    elif change_percent <= -20:
        return 0.9
    else:
        return 1.0
```

### 카테고리별 스코어

재질/용도/용량별로 인기도 계산:

```python
# 예시: PET 재질 제품 중 인기도
score_by_material['PET'] = sum(
    score for product in products
    if product.material == 'PET'
)

# 예시: 로션용 제품 중 인기도
score_by_use['로션'] = sum(
    score for product in products
    if '로션' in product.intended_use
)

# 예시: 50ml 용량 제품 중 인기도
score_by_capacity['50ml'] = sum(
    score for product in products
    if product.capacity_ml == 50
)
```

---

## 🔄 데이터 수집 흐름

```
사용자 행동
    │
    ├─ 검색 → search_logs
    │   └─ 필터 추출 → filters JSONB
    │
    ├─ 클릭 → click_logs
    │   └─ 클릭 위치, 체류 시간 기록
    │
    ├─ 대화 → conversation_logs
    │   └─ 의도, 상태, 제품 기록
    │
    └─ 샘플 신청 → sample_requests
        └─ 구매 의도, 용도 기록

       ↓

매시간 집계 작업 (Cron)
    │
    └─ product_popularity 테이블 업데이트
        ├─ 최근 30일 데이터 집계
        ├─ 가중치 적용 스코어 계산
        ├─ 트렌드 분석 (최근 7일 vs 이전 7일)
        └─ 카테고리별 스코어 계산

       ↓

검색 결과 정렬
    │
    └─ 기본 점수 + 인기도 스코어 혼합
        ├─ 관련성 점수: 70%
        └─ 인기도 점수: 30%
```

---

## 🚀 검색 결과 정렬 로직

### 기존 방식 (관련성만)

```python
# 관련성 점수로만 정렬
results.sort(key=lambda x: x.relevance_score, reverse=True)
```

### 개선 방식 (관련성 + 인기도)

```python
def calculate_final_score(product, query, popularity_data):
    """
    최종 스코어 = 관련성 70% + 인기도 30%
    """
    # 1. 관련성 점수 (0-100)
    relevance_score = calculate_relevance(product, query)

    # 2. 인기도 점수 (0-100, 정규화)
    popularity_score = normalize_popularity_score(
        popularity_data.get(product.idx, {}).get('total_score', 0)
    )

    # 3. 혼합 스코어
    final_score = (
        relevance_score * 0.7 +
        popularity_score * 0.3
    )

    return final_score

# 최종 스코어로 정렬
results.sort(key=lambda x: calculate_final_score(x, query, popularity_data), reverse=True)
```

### 카테고리별 부스트

특정 조건에서 카테고리별 인기도 추가 적용:

```python
if query_has_material_filter(query):
    # "PET 병" 검색 시 PET 제품 중 인기 제품 부스트
    material = extract_material(query)
    popularity_score += popularity_data.score_by_material.get(material, 0) * 0.1

if query_has_use_filter(query):
    # "로션 펌프" 검색 시 로션용 중 인기 제품 부스트
    use = extract_use(query)
    popularity_score += popularity_data.score_by_use.get(use, 0) * 0.1
```

---

## 📈 대시보드 및 분석

### 1. 실시간 인기 제품 대시보드

```
┌─────────────────────────────────────────────┐
│ 🔥 실시간 인기 제품 (최근 24시간)             │
├─────────────────────────────────────────────┤
│ 1. 50ml PET 로션펌프              ⬆ +25%   │
│    샘플신청: 15  클릭: 120  검색: 450       │
│                                             │
│ 2. 100ml HDPE 병                  ⬆ +18%   │
│    샘플신청: 12  클릭: 95   검색: 380       │
│                                             │
│ 3. 24파이 미스트펌프               ⬇ -5%    │
│    샘플신청: 8   클릭: 80   검색: 320       │
└─────────────────────────────────────────────┘
```

### 2. 재질별 인기 트렌드

```
┌─────────────────────────────────────────────┐
│ 📊 재질별 인기 트렌드 (최근 30일)             │
├─────────────────────────────────────────────┤
│ PET   ████████████████████████ 68%         │
│ HDPE  ████████████ 22%                     │
│ PP    ████ 7%                              │
│ 기타   █ 3%                                 │
└─────────────────────────────────────────────┘
```

### 3. 용량별 인기 분포

```
┌─────────────────────────────────────────────┐
│ 📏 용량별 검색 빈도 (최근 30일)               │
├─────────────────────────────────────────────┤
│ 50ml   ████████████████ 35%                │
│ 100ml  ████████████ 25%                    │
│ 30ml   ████████ 18%                        │
│ 200ml  ██████ 12%                          │
│ 기타    ████ 10%                            │
└─────────────────────────────────────────────┘
```

### 4. 검색 키워드 Top 20

```
┌─────────────────────────────────────────────┐
│ 🔍 인기 검색어 (최근 7일)                     │
├─────────────────────────────────────────────┤
│ 1. "로션 펌프"            1,250회           │
│ 2. "50ml 병"              980회            │
│ 3. "PET 용기"             850회            │
│ 4. "24파이 캡"            720회            │
│ 5. "투명 병"              680회            │
│ ...                                        │
└─────────────────────────────────────────────┘
```

---

## 🔧 구현 계획

### Phase 2.1: DB 스키마 설계 ✅

- [x] sample_requests 테이블
- [x] search_logs 테이블
- [x] click_logs 테이블
- [x] conversation_logs 테이블
- [x] product_popularity 테이블

### Phase 2.2: 데이터 수집 시스템

- [ ] 검색 로그 수집 미들웨어
- [ ] 클릭 이벤트 추적 API
- [ ] 대화 로그 자동 저장
- [ ] 샘플 신청 폼 및 저장

### Phase 2.3: 인기도 스코어 계산 엔진

- [ ] 집계 작업 스크립트 (Cron)
- [ ] 시간 감쇠 알고리즘
- [ ] 트렌드 분석 로직
- [ ] 카테고리별 스코어 계산

### Phase 2.4: 검색 결과 정렬 통합

- [ ] 관련성 + 인기도 혼합 스코어
- [ ] 카테고리별 부스트 로직
- [ ] A/B 테스팅 프레임워크

### Phase 2.5: 대시보드 및 분석 API

- [ ] 실시간 인기 제품 API
- [ ] 트렌드 분석 API
- [ ] 검색 키워드 분석
- [ ] 관리자 대시보드 UI

---

## 📚 참고 문서

- **대화 상태 머신**: `docs/CONVERSATION_STATE_MACHINE.md`
- **동의어 처리**: `docs/SYNONYM_HANDLING.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

**작성일**: 2025-01-25
**버전**: 1.0.0
**작성자**: Claude Code with Enhanced RAG Team
