-- Analytics Database Schema
-- Stores all search events, product interactions, and analytics data

-- ============================================================================
-- Search Events Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS search_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    parsed_keywords JSONB,  -- Array of extracted keywords
    context JSONB,  -- Previous search context
    results_count INTEGER,
    INDEX idx_search_timestamp (timestamp),
    INDEX idx_search_session (session_id),
    INDEX idx_search_keywords USING GIN (parsed_keywords)
);

-- ============================================================================
-- Product Events Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'view', 'click', 'bookmark'
    product_category VARCHAR(100),
    product_name TEXT,
    search_context TEXT,  -- Query that led to this event
    INDEX idx_product_timestamp (timestamp),
    INDEX idx_product_session (session_id),
    INDEX idx_product_id (product_id),
    INDEX idx_product_event_type (event_type)
);

-- ============================================================================
-- Keyword Statistics Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS keyword_stats (
    keyword VARCHAR(255) PRIMARY KEY,
    search_count INTEGER DEFAULT 0,
    total_results INTEGER DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    related_products JSONB,  -- Array of product IDs
    co_occurring_keywords JSONB,  -- Dict of keyword -> count
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Product Statistics Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_stats (
    product_id VARCHAR(255) PRIMARY KEY,
    view_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    bookmark_count INTEGER DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    search_keywords JSONB,  -- Dict of keyword -> count
    category VARCHAR(100),
    name TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Search Context Patterns Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS search_context_patterns (
    pattern TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0,
    sessions JSONB,  -- Array of session IDs
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- User Focus Profiles Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_focus_profiles (
    session_id VARCHAR(255) PRIMARY KEY,
    supplier_focus FLOAT DEFAULT 0.0,
    compatibility_focus FLOAT DEFAULT 0.0,
    material_focus FLOAT DEFAULT 0.0,
    price_focus FLOAT DEFAULT 0.0,
    category_focus FLOAT DEFAULT 0.0,
    specification_focus FLOAT DEFAULT 0.0,
    frequent_suppliers JSONB,  -- Array
    frequent_materials JSONB,  -- Array
    frequent_categories JSONB,  -- Array
    total_searches INTEGER DEFAULT 0,
    searches_with_supplier INTEGER DEFAULT 0,
    searches_with_compatibility INTEGER DEFAULT 0,
    searches_with_material INTEGER DEFAULT 0,
    searches_with_price INTEGER DEFAULT 0,
    searches_with_category INTEGER DEFAULT 0,
    searches_with_spec INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Materialized Views for Fast Analytics
-- ============================================================================

-- Top keywords (last 7 days)
CREATE MATERIALIZED VIEW IF NOT EXISTS top_keywords_7d AS
SELECT
    keyword,
    search_count,
    last_seen
FROM keyword_stats
WHERE last_seen > NOW() - INTERVAL '7 days'
ORDER BY search_count DESC
LIMIT 100;

CREATE INDEX idx_top_keywords_7d ON top_keywords_7d(search_count DESC);

-- Top products (last 7 days)
CREATE MATERIALIZED VIEW IF NOT EXISTS top_products_7d AS
SELECT
    product_id,
    view_count,
    click_count,
    bookmark_count,
    category,
    name,
    last_seen
FROM product_stats
WHERE last_seen > NOW() - INTERVAL '7 days'
ORDER BY click_count DESC
LIMIT 100;

CREATE INDEX idx_top_products_7d ON top_products_7d(click_count DESC);

-- Trending queries (last 24 hours)
CREATE MATERIALIZED VIEW IF NOT EXISTS trending_queries_24h AS
SELECT
    query,
    COUNT(*) as search_count,
    MAX(timestamp) as last_seen
FROM search_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY query
ORDER BY search_count DESC, last_seen DESC
LIMIT 50;

-- ============================================================================
-- Functions for Analytics
-- ============================================================================

-- Refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY top_keywords_7d;
    REFRESH MATERIALIZED VIEW CONCURRENTLY top_products_7d;
    REFRESH MATERIALIZED VIEW CONCURRENTLY trending_queries_24h;
END;
$$ LANGUAGE plpgsql;

-- Aggregate search events to keyword stats (run periodically)
CREATE OR REPLACE FUNCTION aggregate_search_events()
RETURNS void AS $$
BEGIN
    -- Update keyword stats from recent search events
    INSERT INTO keyword_stats (keyword, search_count, unique_sessions, first_seen, last_seen)
    SELECT
        jsonb_array_elements_text(parsed_keywords) as keyword,
        COUNT(*) as search_count,
        COUNT(DISTINCT session_id) as unique_sessions,
        MIN(timestamp) as first_seen,
        MAX(timestamp) as last_seen
    FROM search_events
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY keyword
    ON CONFLICT (keyword) DO UPDATE
    SET
        search_count = keyword_stats.search_count + EXCLUDED.search_count,
        unique_sessions = GREATEST(keyword_stats.unique_sessions, EXCLUDED.unique_sessions),
        last_seen = EXCLUDED.last_seen,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Aggregate product events to product stats
CREATE OR REPLACE FUNCTION aggregate_product_events()
RETURNS void AS $$
BEGIN
    -- Update product stats from recent product events
    WITH event_counts AS (
        SELECT
            product_id,
            COUNT(*) FILTER (WHERE event_type = 'view') as views,
            COUNT(*) FILTER (WHERE event_type = 'click') as clicks,
            COUNT(*) FILTER (WHERE event_type = 'bookmark') as bookmarks,
            COUNT(DISTINCT session_id) as unique_sessions,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen,
            MAX(product_category) as category,
            MAX(product_name) as name
        FROM product_events
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY product_id
    )
    INSERT INTO product_stats (
        product_id, view_count, click_count, bookmark_count,
        unique_sessions, first_seen, last_seen, category, name
    )
    SELECT * FROM event_counts
    ON CONFLICT (product_id) DO UPDATE
    SET
        view_count = product_stats.view_count + EXCLUDED.view_count,
        click_count = product_stats.click_count + EXCLUDED.click_count,
        bookmark_count = product_stats.bookmark_count + EXCLUDED.bookmark_count,
        unique_sessions = GREATEST(product_stats.unique_sessions, EXCLUDED.unique_sessions),
        last_seen = EXCLUDED.last_seen,
        category = COALESCE(EXCLUDED.category, product_stats.category),
        name = COALESCE(EXCLUDED.name, product_stats.name),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Scheduled Jobs (use pg_cron or external scheduler)
-- ============================================================================

-- Every hour: aggregate events
-- SELECT cron.schedule('aggregate_events', '0 * * * *',
--     'SELECT aggregate_search_events(); SELECT aggregate_product_events();');

-- Every 5 minutes: refresh materialized views
-- SELECT cron.schedule('refresh_views', '*/5 * * * *',
--     'SELECT refresh_analytics_views();');

-- ============================================================================
-- Cleanup Old Data (optional, to manage storage)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_old_events(days_to_keep INTEGER DEFAULT 90)
RETURNS void AS $$
BEGIN
    -- Delete old search events
    DELETE FROM search_events
    WHERE timestamp < NOW() - INTERVAL '1 day' * days_to_keep;

    -- Delete old product events
    DELETE FROM product_events
    WHERE timestamp < NOW() - INTERVAL '1 day' * days_to_keep;

    -- Clean up keyword stats with no recent activity
    DELETE FROM keyword_stats
    WHERE last_seen < NOW() - INTERVAL '1 day' * days_to_keep;

    -- Clean up product stats with no recent activity
    DELETE FROM product_stats
    WHERE last_seen < NOW() - INTERVAL '1 day' * days_to_keep;
END;
$$ LANGUAGE plpgsql;

-- Run weekly cleanup
-- SELECT cron.schedule('cleanup_old_data', '0 0 * * 0',
--     'SELECT cleanup_old_events(90);');

-- ============================================================================
-- Sample Queries
-- ============================================================================

-- Top 20 keywords (all time)
-- SELECT keyword, search_count FROM keyword_stats ORDER BY search_count DESC LIMIT 20;

-- Top 20 products by clicks (last 7 days)
-- SELECT product_id, name, click_count FROM top_products_7d LIMIT 20;

-- Trending queries (last 24 hours)
-- SELECT * FROM trending_queries_24h;

-- Search volume by hour (last 7 days)
-- SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*) as searches
-- FROM search_events
-- WHERE timestamp > NOW() - INTERVAL '7 days'
-- GROUP BY hour
-- ORDER BY hour DESC;

-- Most common search patterns
-- SELECT pattern, count FROM search_context_patterns ORDER BY count DESC LIMIT 20;

-- User focus distribution
-- SELECT
--     CASE
--         WHEN supplier_focus > 0.5 THEN 'supplier'
--         WHEN compatibility_focus > 0.5 THEN 'compatibility'
--         WHEN material_focus > 0.5 THEN 'material'
--         WHEN price_focus > 0.5 THEN 'price'
--         ELSE 'general'
--     END as focus_type,
--     COUNT(*) as user_count
-- FROM user_focus_profiles
-- GROUP BY focus_type
-- ORDER BY user_count DESC;
