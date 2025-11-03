-- 사용자 행동 분석 시스템 DB 스키마
-- Created: 2025-01-25
-- Purpose: 인기도 기반 추천을 위한 데이터 수집

-- ============================================================
-- 1. 샘플 신청 테이블 (가장 강력한 구매 의도 신호)
-- ============================================================
CREATE TABLE IF NOT EXISTS sample_requests (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 제품 정보
    product_idx VARCHAR(50) NOT NULL,
    product_code VARCHAR(100),
    product_name VARCHAR(500),
    category VARCHAR(100),        -- Bottle, Pump, Cap, Jar
    material VARCHAR(50),          -- PET, HDPE, PP, PETG, etc.
    capacity_ml FLOAT,
    neck_size VARCHAR(20),

    -- 사용자 입력 정보
    intended_use VARCHAR(200),     -- 로션, 크림, 세럼, 샴푸, etc.
    company_name VARCHAR(200),
    contact_info JSONB,            -- {name, phone, email, address}

    -- 메타 정보
    requested_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, shipped, cancelled
    notes TEXT,
    ip_address VARCHAR(45),

    -- 인덱스
    CONSTRAINT fk_product FOREIGN KEY (product_idx) REFERENCES products(idx) ON DELETE CASCADE
);

CREATE INDEX idx_sample_requests_product ON sample_requests(product_idx);
CREATE INDEX idx_sample_requests_material ON sample_requests(material);
CREATE INDEX idx_sample_requests_capacity ON sample_requests(capacity_ml);
CREATE INDEX idx_sample_requests_use ON sample_requests(intended_use);
CREATE INDEX idx_sample_requests_date ON sample_requests(requested_at DESC);
CREATE INDEX idx_sample_requests_user ON sample_requests(user_id);
CREATE INDEX idx_sample_requests_session ON sample_requests(session_id);


-- ============================================================
-- 2. 검색 로그 테이블 (사용자가 무엇을 찾는지)
-- ============================================================
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 검색 쿼리
    query TEXT NOT NULL,
    normalized_query TEXT,         -- 정규화된 쿼리

    -- 추출된 필터
    filters JSONB,                 -- {material, capacity, neck_size, product_type, etc.}

    -- 검색 결과
    result_count INTEGER DEFAULT 0,
    result_product_indices TEXT[], -- 검색된 제품 idx 배열 (최대 50개)

    -- 의도 분류
    intent VARCHAR(50),            -- search, filter, reference, compatibility, etc.
    product_type VARCHAR(50),      -- bottle, pump, cap, jar, etc.

    -- 메타 정보
    searched_at TIMESTAMP DEFAULT NOW(),
    response_time_ms INTEGER,
    ip_address VARCHAR(45),

    -- 인덱스
    INDEX idx_search_logs_user (user_id),
    INDEX idx_search_logs_session (session_id),
    INDEX idx_search_logs_query (query(255)),
    INDEX idx_search_logs_filters USING GIN (filters),
    INDEX idx_search_logs_date (searched_at DESC),
    INDEX idx_search_logs_intent (intent)
);


-- ============================================================
-- 3. 클릭 로그 테이블 (어떤 제품에 관심 있는지)
-- ============================================================
CREATE TABLE IF NOT EXISTS click_logs (
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
    neck_size VARCHAR(20),

    -- 클릭 컨텍스트
    click_position INTEGER,        -- 검색 결과에서 몇 번째 위치 (1-based)
    search_query TEXT,             -- 어떤 검색에서 클릭했는지
    referrer VARCHAR(50),          -- search_result, related_products, homepage, etc.

    -- 행동 패턴
    time_on_page_seconds INTEGER,  -- 상세 페이지에서 머문 시간
    viewed_images BOOLEAN DEFAULT FALSE,         -- 이미지 확대 여부
    checked_specs BOOLEAN DEFAULT FALSE,         -- 스펙 탭 클릭 여부
    checked_compatibility BOOLEAN DEFAULT FALSE, -- 호환성 확인 여부
    requested_sample BOOLEAN DEFAULT FALSE,      -- 샘플 신청 여부

    -- 메타 정보
    clicked_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),

    -- 인덱스
    INDEX idx_click_logs_product (product_idx),
    INDEX idx_click_logs_user (user_id),
    INDEX idx_click_logs_session (session_id),
    INDEX idx_click_logs_material (material),
    INDEX idx_click_logs_capacity (capacity_ml),
    INDEX idx_click_logs_date (clicked_at DESC),
    INDEX idx_click_logs_position (click_position)
);


-- ============================================================
-- 4. 대화 로그 테이블 (대화 패턴 및 의도)
-- ============================================================
CREATE TABLE IF NOT EXISTS conversation_logs (
    id SERIAL PRIMARY KEY,

    -- 사용자 정보
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,

    -- 대화 내용
    user_message TEXT NOT NULL,
    bot_response TEXT,

    -- 대화 분석
    intent VARCHAR(50),            -- search, filter, reference, compatibility, document, etc.
    reference_type VARCHAR(50),    -- number, demonstrative, document, implicit, etc.
    conversation_state VARCHAR(50), -- GREETING, SEARCHING, FILTERING, FOCUSED, etc.

    -- 컨텍스트
    focused_product VARCHAR(50),   -- 포커스된 제품 idx
    active_filters JSONB,          -- 활성 필터 상태

    -- 결과
    products_shown TEXT[],         -- 표시된 제품 idx 배열
    product_count INTEGER,         -- 표시된 제품 수
    action_taken VARCHAR(50),      -- search, apply_filter, show_detail, find_compatible, etc.

    -- 메타 정보
    created_at TIMESTAMP DEFAULT NOW(),
    response_time_ms INTEGER,
    ip_address VARCHAR(45),

    -- 인덱스
    INDEX idx_conversation_logs_user (user_id),
    INDEX idx_conversation_logs_session (session_id),
    INDEX idx_conversation_logs_intent (intent),
    INDEX idx_conversation_logs_focused (focused_product),
    INDEX idx_conversation_logs_date (created_at DESC),
    INDEX idx_conversation_logs_state (conversation_state)
);


-- ============================================================
-- 5. 제품 인기도 집계 테이블 (실시간 캐싱)
-- ============================================================
CREATE TABLE IF NOT EXISTS product_popularity (
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
    normalized_score FLOAT DEFAULT 0,  -- 0-100 정규화

    -- 카테고리별 스코어 (재질/용도/용량별)
    score_by_material JSONB,       -- {PET: 85.5, HDPE: 20.3, ...}
    score_by_use JSONB,            -- {로션: 90.2, 크림: 45.1, ...}
    score_by_capacity JSONB,       -- {50: 75.0, 100: 60.5, ...}
    score_by_category JSONB,       -- {Bottle: 80.0, Pump: 70.0, ...}

    -- 트렌드 (최근 7일 vs 이전 7-14일)
    recent_7d_score FLOAT DEFAULT 0,
    previous_7d_score FLOAT DEFAULT 0,
    trend_percentage FLOAT DEFAULT 0,  -- +15.5 (증가), -8.2 (감소)

    -- 랭킹
    overall_rank INTEGER,
    rank_by_material INTEGER,
    rank_by_category INTEGER,

    -- 메타 정보
    last_updated TIMESTAMP DEFAULT NOW(),
    data_window_start TIMESTAMP,   -- 집계 데이터 시작일
    data_window_end TIMESTAMP,     -- 집계 데이터 종료일

    -- 인덱스
    INDEX idx_popularity_score (total_score DESC),
    INDEX idx_popularity_normalized (normalized_score DESC),
    INDEX idx_popularity_material (material),
    INDEX idx_popularity_capacity (capacity_ml),
    INDEX idx_popularity_category (category),
    INDEX idx_popularity_trend (trend_percentage DESC),
    INDEX idx_popularity_updated (last_updated DESC)
);


-- ============================================================
-- 6. 사용자 선호도 프로필 테이블 (개인화)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR(255) PRIMARY KEY,

    -- 선호 재질
    preferred_materials JSONB,     -- {PET: 0.6, HDPE: 0.3, PP: 0.1}

    -- 선호 용량
    preferred_capacities JSONB,    -- {50: 0.5, 100: 0.3, 200: 0.2}

    -- 선호 카테고리
    preferred_categories JSONB,    -- {Bottle: 0.7, Pump: 0.2, Cap: 0.1}

    -- 주요 용도
    main_uses TEXT[],              -- [로션, 크림, 세럼]

    -- 최근 검색 키워드 (최근 20개)
    recent_searches TEXT[],

    -- 자주 본 제품 (최근 30개)
    frequently_viewed TEXT[],      -- product_idx 배열

    -- 메타 정보
    first_visit TIMESTAMP,
    last_visit TIMESTAMP DEFAULT NOW(),
    total_searches INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_sample_requests INTEGER DEFAULT 0,

    -- 인덱스
    INDEX idx_user_pref_last_visit (last_visit DESC)
);


-- ============================================================
-- 집계 작업을 위한 Helper Views
-- ============================================================

-- 최근 30일 샘플 신청 집계
CREATE OR REPLACE VIEW v_sample_requests_30d AS
SELECT
    product_idx,
    COUNT(*) as request_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(EXTRACT(EPOCH FROM (NOW() - requested_at)) / 86400) as avg_days_ago
FROM sample_requests
WHERE requested_at >= NOW() - INTERVAL '30 days'
GROUP BY product_idx;


-- 최근 30일 클릭 집계
CREATE OR REPLACE VIEW v_clicks_30d AS
SELECT
    product_idx,
    COUNT(*) as click_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(click_position) as avg_position,
    AVG(time_on_page_seconds) as avg_time_on_page
FROM click_logs
WHERE clicked_at >= NOW() - INTERVAL '30 days'
GROUP BY product_idx;


-- 최근 30일 검색 출현 집계
CREATE OR REPLACE VIEW v_search_appearances_30d AS
SELECT
    UNNEST(result_product_indices) as product_idx,
    COUNT(*) as appearance_count
FROM search_logs
WHERE searched_at >= NOW() - INTERVAL '30 days'
  AND result_product_indices IS NOT NULL
GROUP BY product_idx;


-- 최근 30일 대화 언급 집계
CREATE OR REPLACE VIEW v_conversation_mentions_30d AS
SELECT
    UNNEST(products_shown) as product_idx,
    COUNT(*) as mention_count
FROM conversation_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND products_shown IS NOT NULL
GROUP BY product_idx;


-- ============================================================
-- 코멘트 추가
-- ============================================================
COMMENT ON TABLE sample_requests IS '샘플 신청 데이터 - 가장 강력한 구매 의도 신호 (가중치 10.0)';
COMMENT ON TABLE search_logs IS '검색 로그 - 사용자가 무엇을 찾는지 (가중치 1.0)';
COMMENT ON TABLE click_logs IS '클릭 로그 - 어떤 제품에 관심 있는지 (가중치 3.0)';
COMMENT ON TABLE conversation_logs IS '대화 로그 - 대화 패턴 및 의도 (가중치 0.5)';
COMMENT ON TABLE product_popularity IS '제품 인기도 집계 - 실시간 인기도 스코어 캐싱';
COMMENT ON TABLE user_preferences IS '사용자 선호도 프로필 - 개인화 추천을 위한 데이터';
