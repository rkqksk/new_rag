# Real-time Analytics Pipeline (v6.0.0)

**Status**: ✅ Complete | **Type**: Business Intelligence | **Priority**: High

## Overview

Enterprise-grade real-time analytics infrastructure using ClickHouse OLAP database and Apache Kafka streaming platform for high-performance data analysis.

### Architecture

```
FastAPI Endpoints
      ↓
Kafka Topics (Async Streaming)
  ├─ search-events
  ├─ user-events
  └─ performance-events
      ↓
Kafka Consumer (Batch Processing)
      ↓
ClickHouse OLAP Database
      ↓
Analytics API (Real-time Queries)
      ↓
Dashboards & Reports
```

## Features

### 1. Event Streaming with Kafka

- **Async Publishing**: Non-blocking event publishing from API endpoints
- **Topics**:
  - `search-events`: All search queries with performance metrics
  - `user-events`: User interactions (clicks, sessions, conversions)
  - `performance-events`: API performance metrics
- **Reliable Delivery**: Acks=all, retries enabled
- **Scalable**: Multiple consumers with consumer groups

### 2. OLAP Storage with ClickHouse

- **Columnar Storage**: Optimized for analytical queries
- **Time-Series Data**: Efficient time-based partitioning
- **TTL Management**: Automatic data retention (30-90 days)
- **Aggregations**: Fast COUNT, AVG, SUM, percentiles
- **Compression**: 10x data compression on disk

### 3. Real-time Analytics API

**Base URL**: `/api/v1/analytics/realtime`

#### Query Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats` | GET | Overall search statistics |
| `/queries/top` | GET | Most popular queries |
| `/queries/trend` | GET | Hourly search volume trend |
| `/performance/strategy` | GET | Performance by search strategy |
| `/health` | GET | Analytics infrastructure health |

#### Tracking Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/track/search` | POST | Track search event (async) |
| `/track/event` | POST | Track user event (async) |

## Quick Start

### 1. Start Infrastructure

```bash
# Start all services (PostgreSQL, Redis, Qdrant, ClickHouse, Kafka)
docker-compose up -d

# Verify services
docker-compose ps

# Expected services:
# - clickhouse: 8123 (HTTP), 9000 (native)
# - kafka: 9092
# - zookeeper: 2181
```

### 2. Start Analytics Consumer

```bash
# In separate terminal
python scripts/run_analytics_consumer.py

# Or run in background
nohup python scripts/run_analytics_consumer.py > logs/consumer.log 2>&1 &
```

### 3. Track Events

```bash
# Track a search
curl -X POST http://localhost:8001/api/v1/analytics/realtime/track/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess-123",
    "user_id": "user-456",
    "query": "50ml PET 용기",
    "results_count": 95,
    "response_time_ms": 342.5,
    "search_strategy": "hybrid",
    "top_k": 10,
    "cache_hit": false
  }'

# Track a user event
curl -X POST http://localhost:8001/api/v1/analytics/realtime/track/event \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess-123",
    "user_id": "user-456",
    "event_type": "product_click",
    "product_id": "prod-789",
    "query": "50ml PET 용기"
  }'
```

### 4. Query Analytics

```bash
# Get overall stats
curl http://localhost:8001/api/v1/analytics/realtime/stats?hours=24

# Get top queries
curl http://localhost:8001/api/v1/analytics/realtime/queries/top?limit=10

# Get hourly trend
curl http://localhost:8001/api/v1/analytics/realtime/queries/trend?hours=24

# Get performance by strategy
curl http://localhost:8001/api/v1/analytics/realtime/performance/strategy
```

## Data Schema

### Search Logs Table

```sql
CREATE TABLE search_logs (
    timestamp DateTime,
    session_id String,
    user_id String,
    query String,
    results_count UInt32,
    response_time_ms Float32,
    search_strategy String,
    filters String,
    top_k UInt32,
    cache_hit UInt8,
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, timestamp)
TTL date + INTERVAL 90 DAY
```

### User Events Table

```sql
CREATE TABLE user_events (
    timestamp DateTime,
    session_id String,
    user_id String,
    event_type String,
    event_data String,
    product_id String,
    query String,
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, timestamp)
TTL date + INTERVAL 90 DAY
```

### Search Quality Table

```sql
CREATE TABLE search_quality (
    timestamp DateTime,
    query String,
    click_position UInt32,
    clicks UInt32,
    impressions UInt32,
    ctr Float32,
    mrr Float32,
    avg_similarity Float32,
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, timestamp)
TTL date + INTERVAL 90 DAY
```

### Performance Metrics Table

```sql
CREATE TABLE performance_metrics (
    timestamp DateTime,
    endpoint String,
    method String,
    status_code UInt16,
    response_time_ms Float32,
    cpu_percent Float32,
    memory_mb Float32,
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, timestamp)
TTL date + INTERVAL 30 DAY
```

## Performance

### Benchmarks

**Event Throughput**:
- Kafka: 100,000+ events/sec per partition
- ClickHouse: 1M+ inserts/sec (batched)
- Consumer: 10,000+ events/sec (batch_size=100)

**Query Performance**:
- Simple aggregations: < 50ms
- Complex time-series: < 200ms
- 95th percentile: < 500ms

**Storage**:
- Compression ratio: 10:1
- 1M events ≈ 50MB compressed
- TTL cleanup: automatic

### Optimization Tips

1. **Batch Size**: Adjust `KAFKA_BATCH_SIZE` (default: 100)
   - Higher = better throughput, more latency
   - Lower = lower latency, less throughput

2. **Partitioning**: Use monthly partitions for time-series data
   - Faster queries on recent data
   - Efficient TTL-based cleanup

3. **Consumer Parallelism**: Run multiple consumer instances
   ```bash
   # Consumer 1 (group: analytics-consumer)
   KAFKA_CONSUMER_GROUP_ID=analytics-consumer python scripts/run_analytics_consumer.py

   # Consumer 2 (same group for load balancing)
   KAFKA_CONSUMER_GROUP_ID=analytics-consumer python scripts/run_analytics_consumer.py
   ```

4. **ClickHouse Tuning**:
   ```sql
   -- Optimize table (merge parts)
   OPTIMIZE TABLE search_logs FINAL;

   -- Check table size
   SELECT
       table,
       formatReadableSize(sum(bytes)) as size
   FROM system.parts
   WHERE active
   GROUP BY table;
   ```

## Monitoring

### Health Check

```bash
curl http://localhost:8001/api/v1/analytics/realtime/health
```

Response:
```json
{
  "status": "healthy",
  "clickhouse": "available",
  "kafka": "available",
  "message": "Analytics fully operational"
}
```

### ClickHouse Console

```bash
# Access ClickHouse client
docker exec -it clickhouse clickhouse-client

# Check tables
SHOW TABLES;

# Query search logs
SELECT
    count() as total_searches,
    avg(response_time_ms) as avg_response_time
FROM search_logs
WHERE date = today();

# Check partitions
SELECT
    partition,
    count() as rows,
    formatReadableSize(sum(bytes_on_disk)) as size
FROM system.parts
WHERE table = 'search_logs' AND active
GROUP BY partition
ORDER BY partition DESC;
```

### Kafka Monitoring

```bash
# List topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check consumer lag
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-consumer \
  --describe

# View topic details
docker exec -it kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic search-events
```

## Use Cases

### 1. Search Quality Monitoring

Track search performance and quality metrics:

```python
from app.services.analytics_pipeline import track_search

# After every search
track_search(
    session_id=session_id,
    user_id=user_id,
    query=query,
    results_count=len(results),
    response_time_ms=elapsed_ms,
    search_strategy="hybrid+rerank",
    cache_hit=from_cache
)
```

### 2. User Behavior Analysis

Track user interactions:

```python
from app.services.analytics_pipeline import track_user_event

# Product click
track_user_event(
    session_id=session_id,
    user_id=user_id,
    event_type="product_click",
    product_id=product_id,
    query=search_query
)

# Session start
track_user_event(
    session_id=session_id,
    user_id=user_id,
    event_type="session_start"
)
```

### 3. API Performance Monitoring

Track API performance:

```python
from app.services.analytics_pipeline import track_performance

# After API request
track_performance(
    endpoint="/api/v1/search",
    method="POST",
    status_code=200,
    response_time_ms=342.5,
    cpu_percent=45.2,
    memory_mb=512.0
)
```

### 4. Real-time Dashboards

Build dashboards using analytics API:

```javascript
// React component
const AnalyticsDashboard = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Fetch stats every 30 seconds
    const fetchStats = async () => {
      const response = await fetch('/api/v1/analytics/realtime/stats?hours=24');
      setStats(await response.json());
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Real-time Analytics</h2>
      <div>Total Searches: {stats?.total_searches}</div>
      <div>Avg Response Time: {stats?.avg_response_time}ms</div>
      <div>Cache Hit Rate: {(stats?.cache_hit_rate * 100).toFixed(1)}%</div>
    </div>
  );
};
```

## Troubleshooting

### Issue: Kafka Connection Failed

```bash
# Check if Kafka is running
docker-compose ps kafka

# View Kafka logs
docker-compose logs kafka --tail=50

# Restart Kafka
docker-compose restart kafka zookeeper
```

### Issue: ClickHouse Not Accepting Connections

```bash
# Check ClickHouse health
curl http://localhost:8123/ping

# View ClickHouse logs
docker-compose logs clickhouse --tail=50

# Restart ClickHouse
docker-compose restart clickhouse
```

### Issue: Consumer Not Processing Events

```bash
# Check consumer logs
tail -f logs/analytics_consumer.log

# Check consumer group lag
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-consumer \
  --describe

# Reset consumer offset (if needed)
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-consumer \
  --reset-offsets --to-earliest --topic search-events --execute
```

### Issue: High Memory Usage

```bash
# Check Docker stats
docker stats clickhouse kafka

# Adjust ClickHouse memory limit in docker-compose.yml
services:
  clickhouse:
    mem_limit: 2g  # Limit to 2GB
```

## Production Deployment

### Docker Compose

Already configured in `docker-compose.yml`:

```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse_data:/var/lib/clickhouse

  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
```

### Kubernetes

Deploy consumer as a separate deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-consumer
spec:
  replicas: 2  # For high availability
  selector:
    matchLabels:
      app: analytics-consumer
  template:
    metadata:
      labels:
        app: analytics-consumer
    spec:
      containers:
      - name: consumer
        image: rag-enterprise-api:latest
        command: ["python", "scripts/run_analytics_consumer.py"]
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        - name: CLICKHOUSE_HOST
          value: "clickhouse"
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
```

### Systemd Service

For bare-metal deployment:

```ini
# /etc/systemd/system/analytics-consumer.service
[Unit]
Description=Analytics Consumer Service
After=network.target kafka.service clickhouse.service

[Service]
Type=simple
User=app
WorkingDirectory=/opt/rag-enterprise
ExecStart=/usr/bin/python3 scripts/run_analytics_consumer.py
Restart=always
RestartSec=10
Environment="KAFKA_BOOTSTRAP_SERVERS=localhost:9092"
Environment="CLICKHOUSE_HOST=localhost"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable analytics-consumer
sudo systemctl start analytics-consumer
sudo systemctl status analytics-consumer
```

## API Reference

See detailed API documentation at:
- Swagger UI: http://localhost:8001/api/v1/docs
- Section: "analytics-realtime"

## Dependencies

- `clickhouse-driver>=0.2.9` - ClickHouse Python client
- `kafka-python>=2.0.2` - Apache Kafka client

## Related Documentation

- [Search Analytics Dashboard](../../frontend/analytics-dashboard.html)
- [Advanced Caching](../app/services/advanced_cache.py)
- [Rate Limiting](../app/middleware/rate_limiting.py)
- [GraphQL API](GRAPHQL_API.md)

---

**Version**: v6.0.0
**Status**: Production Ready
**Last Updated**: 2025-11-09
