-- TimescaleDB Initialization Script
-- v7.2.0 - Edge Computing Platform

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ========================================
-- IoT Sensor Data
-- ========================================

-- Sensor readings table (hypertable)
CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    sensor_id TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    value DOUBLE PRECISION,
    unit TEXT,
    metadata JSONB,
    PRIMARY KEY (time, sensor_id)
);

-- Convert to hypertable (time-series optimized)
SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sensor_id ON sensor_readings (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_type ON sensor_readings (sensor_type, time DESC);

-- Compression policy (after 7 days)
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_id, sensor_type'
);

SELECT add_compression_policy('sensor_readings', INTERVAL '7 days', if_not_exists => TRUE);

-- Retention policy (keep 1 year)
SELECT add_retention_policy('sensor_readings', INTERVAL '365 days', if_not_exists => TRUE);

-- ========================================
-- Equipment Health (Predictive Maintenance)
-- ========================================

CREATE TABLE IF NOT EXISTS equipment_health (
    time TIMESTAMPTZ NOT NULL,
    equipment_id TEXT NOT NULL,
    status TEXT NOT NULL,
    health_score DOUBLE PRECISION,
    rul_hours DOUBLE PRECISION,  -- Remaining Useful Life
    anomalies JSONB,
    recommendations JSONB,
    PRIMARY KEY (time, equipment_id)
);

SELECT create_hypertable('equipment_health', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_equipment_id ON equipment_health (equipment_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment_health (status, time DESC);

-- ========================================
-- Manufacturing Quality (LORA Vision)
-- ========================================

CREATE TABLE IF NOT EXISTS quality_inspections (
    time TIMESTAMPTZ NOT NULL,
    product_type TEXT NOT NULL,
    inspection_result TEXT NOT NULL,  -- 'pass', 'reject'
    defects JSONB,
    confidence DOUBLE PRECISION,
    cycle_time_ms DOUBLE PRECISION,
    PRIMARY KEY (time, product_type)
);

SELECT create_hypertable('quality_inspections', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_product_type ON quality_inspections (product_type, time DESC);
CREATE INDEX IF NOT EXISTS idx_inspection_result ON quality_inspections (inspection_result, time DESC);

-- ========================================
-- Robot Operations (UR10e)
-- ========================================

CREATE TABLE IF NOT EXISTS robot_operations (
    time TIMESTAMPTZ NOT NULL,
    robot_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,  -- 'pick', 'place', 'move'
    success BOOLEAN,
    cycle_time_ms DOUBLE PRECISION,
    position JSONB,
    error_message TEXT,
    PRIMARY KEY (time, robot_id)
);

SELECT create_hypertable('robot_operations', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_robot_id ON robot_operations (robot_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_operation_success ON robot_operations (success, time DESC);

-- ========================================
-- System Metrics
-- ========================================

CREATE TABLE IF NOT EXISTS system_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION,
    tags JSONB,
    PRIMARY KEY (time, metric_name)
);

SELECT create_hypertable('system_metrics', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_metric_name ON system_metrics (metric_name, time DESC);

-- ========================================
-- Continuous Aggregates (Materialized Views)
-- ========================================

-- Hourly sensor averages
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    sensor_id,
    sensor_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS std_value,
    COUNT(*) AS sample_count
FROM sensor_readings
GROUP BY bucket, sensor_id, sensor_type;

-- Refresh policy (every 1 hour)
SELECT add_continuous_aggregate_policy('sensor_readings_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Daily equipment health summary
CREATE MATERIALIZED VIEW IF NOT EXISTS equipment_health_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    equipment_id,
    AVG(health_score) AS avg_health_score,
    MIN(health_score) AS min_health_score,
    MAX(health_score) AS max_health_score,
    COUNT(CASE WHEN status = 'critical' THEN 1 END) AS critical_count,
    COUNT(CASE WHEN status = 'warning' THEN 1 END) AS warning_count
FROM equipment_health
GROUP BY bucket, equipment_id;

SELECT add_continuous_aggregate_policy('equipment_health_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Hourly quality metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS quality_metrics_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    product_type,
    COUNT(*) AS total_inspections,
    COUNT(CASE WHEN inspection_result = 'pass' THEN 1 END) AS pass_count,
    COUNT(CASE WHEN inspection_result = 'reject' THEN 1 END) AS reject_count,
    AVG(confidence) AS avg_confidence,
    AVG(cycle_time_ms) AS avg_cycle_time
FROM quality_inspections
GROUP BY bucket, product_type;

SELECT add_continuous_aggregate_policy('quality_metrics_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ========================================
-- Helper Functions
-- ========================================

-- Function to get sensor statistics
CREATE OR REPLACE FUNCTION get_sensor_stats(
    p_sensor_id TEXT,
    p_start_time TIMESTAMPTZ,
    p_end_time TIMESTAMPTZ
)
RETURNS TABLE (
    avg_value DOUBLE PRECISION,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    std_value DOUBLE PRECISION,
    sample_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        AVG(value),
        MIN(value),
        MAX(value),
        STDDEV(value),
        COUNT(*)
    FROM sensor_readings
    WHERE sensor_id = p_sensor_id
        AND time >= p_start_time
        AND time <= p_end_time;
END;
$$ LANGUAGE plpgsql;

-- Function to get equipment health trend
CREATE OR REPLACE FUNCTION get_equipment_health_trend(
    p_equipment_id TEXT,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    date DATE,
    avg_health_score DOUBLE PRECISION,
    critical_count BIGINT,
    warning_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        DATE(time),
        AVG(health_score),
        COUNT(CASE WHEN status = 'critical' THEN 1 END),
        COUNT(CASE WHEN status = 'warning' THEN 1 END)
    FROM equipment_health
    WHERE equipment_id = p_equipment_id
        AND time >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY DATE(time)
    ORDER BY DATE(time);
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- Grants
-- ========================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rag_user;

-- ========================================
-- Sample Data (for testing)
-- ========================================

-- Insert sample sensor readings
INSERT INTO sensor_readings (time, sensor_id, sensor_type, value, unit)
VALUES
    (NOW() - INTERVAL '1 hour', 'temp_01', 'temperature', 25.5, '°C'),
    (NOW() - INTERVAL '30 minutes', 'temp_01', 'temperature', 26.2, '°C'),
    (NOW(), 'temp_01', 'temperature', 25.8, '°C'),
    (NOW() - INTERVAL '1 hour', 'vibration_01', 'vibration', 0.5, 'm/s²'),
    (NOW(), 'vibration_01', 'vibration', 0.6, 'm/s²')
ON CONFLICT DO NOTHING;

VACUUM ANALYZE;

-- ========================================
-- Completion Message
-- ========================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'TimescaleDB initialized successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - sensor_readings (hypertable)';
    RAISE NOTICE '  - equipment_health (hypertable)';
    RAISE NOTICE '  - quality_inspections (hypertable)';
    RAISE NOTICE '  - robot_operations (hypertable)';
    RAISE NOTICE '  - system_metrics (hypertable)';
    RAISE NOTICE '';
    RAISE NOTICE 'Continuous aggregates:';
    RAISE NOTICE '  - sensor_readings_hourly';
    RAISE NOTICE '  - equipment_health_daily';
    RAISE NOTICE '  - quality_metrics_hourly';
    RAISE NOTICE '';
    RAISE NOTICE 'Policies enabled:';
    RAISE NOTICE '  - Compression: 7 days';
    RAISE NOTICE '  - Retention: 365 days';
    RAISE NOTICE '========================================';
END $$;
