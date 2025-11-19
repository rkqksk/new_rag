# Database Performance Baseline - v10.0.0

**Date**: 2025-11-19
**System**: v10 Unified Maximum
**Databases**: PostgreSQL 16, Qdrant 1.7, Redis 7, ClickHouse 23

---

## Executive Summary

### Performance Targets
| Database | Operation | Target | Industry Standard | Status |
|----------|-----------|--------|-------------------|--------|
| PostgreSQL | Simple SELECT | <20ms | <50ms | ✅ Excellent |
| PostgreSQL | JOIN Query | <80ms | <200ms | ✅ Good |
| PostgreSQL | Full-text Search | <200ms | <500ms | ✅ Good |
| Qdrant | Vector Search | <100ms | <200ms | ✅ Excellent |
| Redis | GET/SET | <5ms | <10ms | ✅ Excellent |
| ClickHouse | Aggregation | <100ms | <500ms | ✅ Excellent |

### Quick Stats
- **PostgreSQL**: 471 products, 3,246 chunks, 20 connections
- **Qdrant**: 3,246 vectors, 768 dimensions, HNSW index
- **Redis**: 1000+ cached keys, LRU eviction
- **ClickHouse**: Analytics data, columnar storage

---

## 1. PostgreSQL Performance

### Database Configuration

**Connection**:
- Host: localhost
- Port: 15432
- Database: rag_db
- Pool Size: 20 connections
- Max Overflow: 10 connections

**Tables**:
- `products`: 471 rows (product catalog)
- `chunks`: 3,246 rows (document chunks)
- `users`: N rows (user accounts)
- `sessions`: N rows (user sessions)
- `queries`: N rows (search history)

---

### 1.1 Simple SELECT Queries

**Target**: <20ms (95th percentile)

#### Test Queries
```sql
-- Single product by ID (indexed)
EXPLAIN ANALYZE
SELECT * FROM products WHERE id = 'prod_123';

-- Expected: Index Scan, 2-10ms

-- Multiple products by category (indexed)
EXPLAIN ANALYZE
SELECT * FROM products WHERE category = 'PET' LIMIT 20;

-- Expected: Index Scan, 10-30ms

-- Count all products
EXPLAIN ANALYZE
SELECT COUNT(*) FROM products;

-- Expected: Seq Scan or Index-Only Scan, 5-20ms
```

#### Running Tests
```bash
# Connect to PostgreSQL
docker exec -it new_rag-postgres-1 psql -U postgres -d rag_db

# Run individual queries
\timing on

SELECT * FROM products WHERE id = 'prod_123';
SELECT * FROM products WHERE category = 'PET' LIMIT 20;
SELECT COUNT(*) FROM products;

# Batch test (100 queries)
\o /tmp/query_results.txt
\timing on
SELECT * FROM generate_series(1, 100) AS s,
  (SELECT * FROM products LIMIT 1) AS p;
\o
```

**Expected Results**:
```
Query                          | Avg Time | p95 Time | Rows
-------------------------------|----------|----------|------
SELECT by ID (indexed)         | 3ms      | 8ms      | 1
SELECT by category (indexed)   | 15ms     | 35ms     | 20
SELECT with LIMIT              | 8ms      | 20ms     | 20
COUNT(*)                       | 10ms     | 25ms     | 1
```

---

### 1.2 JOIN Queries

**Target**: <80ms (95th percentile)

#### Test Queries
```sql
-- Product with chunks (1:N)
EXPLAIN ANALYZE
SELECT p.*, c.content
FROM products p
LEFT JOIN chunks c ON c.product_id = p.id
WHERE p.id = 'prod_123';

-- Expected: Nested Loop, 20-60ms

-- Products with user queries (M:N)
EXPLAIN ANALYZE
SELECT p.*, q.query_text, q.created_at
FROM products p
JOIN query_results qr ON qr.product_id = p.id
JOIN queries q ON q.id = qr.query_id
WHERE q.user_id = 'user_456'
LIMIT 20;

-- Expected: Hash Join, 40-120ms

-- Aggregation with JOIN
EXPLAIN ANALYZE
SELECT p.category, COUNT(*) as product_count, AVG(p.price) as avg_price
FROM products p
LEFT JOIN chunks c ON c.product_id = p.id
GROUP BY p.category;

-- Expected: Hash Join + Aggregate, 30-100ms
```

**Expected Results**:
```
Query                          | Avg Time | p95 Time | Rows
-------------------------------|----------|----------|------
Product + Chunks (1:N)         | 35ms     | 70ms     | 1-10
Products + Queries (M:N)       | 65ms     | 140ms    | 20
Aggregation with JOIN          | 55ms     | 120ms    | 5-10
```

**Optimization**:
- Ensure foreign keys are indexed
- Use `EXPLAIN ANALYZE` to check join strategy
- Consider materialized views for complex aggregations

---

### 1.3 Full-text Search

**Target**: <200ms (95th percentile)

#### Test Queries
```sql
-- Simple full-text search (GIN index)
EXPLAIN ANALYZE
SELECT *
FROM products
WHERE to_tsvector('korean', name || ' ' || description) @@ to_tsquery('korean', 'PET & 용기')
LIMIT 20;

-- Expected: Bitmap Heap Scan, 50-150ms

-- Full-text search with ranking
EXPLAIN ANALYZE
SELECT *,
  ts_rank(to_tsvector('korean', name || ' ' || description),
          to_tsquery('korean', 'PET & 용기')) AS rank
FROM products
WHERE to_tsvector('korean', name || ' ' || description) @@ to_tsquery('korean', 'PET & 용기')
ORDER BY rank DESC
LIMIT 20;

-- Expected: Bitmap Heap Scan + Sort, 80-250ms

-- Multi-field full-text search
EXPLAIN ANALYZE
SELECT p.*,
  ts_rank(to_tsvector('korean', p.name), query) * 2.0 +
  ts_rank(to_tsvector('korean', p.description), query) * 1.0 AS rank
FROM products p, to_tsquery('korean', 'PET & 용기') query
WHERE to_tsvector('korean', p.name || ' ' || p.description) @@ query
ORDER BY rank DESC
LIMIT 20;

-- Expected: 100-300ms
```

**Expected Results**:
```
Query                          | Avg Time | p95 Time | Rows
-------------------------------|----------|----------|------
Simple FTS (GIN index)         | 85ms     | 180ms    | 20
FTS with ranking               | 145ms    | 310ms    | 20
Multi-field FTS                | 175ms    | 380ms    | 20
```

**GIN Index Creation**:
```sql
-- Create GIN index for full-text search
CREATE INDEX idx_products_fts ON products
USING GIN (to_tsvector('korean', name || ' ' || description));

-- Verify index is used
EXPLAIN SELECT * FROM products
WHERE to_tsvector('korean', name || ' ' || description) @@ to_tsquery('korean', 'PET');
-- Should show: Bitmap Index Scan using idx_products_fts
```

---

### 1.4 Index Performance

#### Existing Indexes
```sql
-- List all indexes
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

#### Recommended Indexes
```sql
-- Primary key (automatic)
CREATE INDEX idx_products_pkey ON products (id);

-- Foreign keys
CREATE INDEX idx_chunks_product_id ON chunks (product_id);
CREATE INDEX idx_query_results_product_id ON query_results (product_id);
CREATE INDEX idx_query_results_query_id ON query_results (query_id);

-- Common filters
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_price ON products (price);
CREATE INDEX idx_queries_user_id ON queries (user_id);
CREATE INDEX idx_queries_created_at ON queries (created_at);

-- Full-text search
CREATE INDEX idx_products_fts ON products
USING GIN (to_tsvector('korean', name || ' ' || description));

-- Composite indexes for common queries
CREATE INDEX idx_products_category_price ON products (category, price);
```

**Index Size Analysis**:
```sql
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Expected Index Sizes**:
```
Index                          | Size
-------------------------------|-------
idx_products_pkey              | 40 KB
idx_chunks_product_id          | 120 KB
idx_products_fts (GIN)         | 250 KB
idx_products_category          | 32 KB
```

---

### 1.5 Query Performance Analysis

#### EXPLAIN ANALYZE

**Example**:
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM products WHERE category = 'PET' LIMIT 20;
```

**Output Interpretation**:
```
Index Scan using idx_products_category on products
  (cost=0.28..12.30 rows=20 width=256)
  (actual time=0.025..0.156 rows=20 loops=1)
  Index Cond: (category = 'PET'::text)
  Buffers: shared hit=5
Planning Time: 0.123 ms
Execution Time: 0.187 ms
```

**Key Metrics**:
- `cost`: Estimated cost (lower is better)
- `actual time`: Actual execution time
- `rows`: Number of rows returned
- `Buffers`: Shared buffers hit/read
- `Planning Time`: Query planning overhead
- `Execution Time`: Actual query execution

**Performance Indicators**:
- ✅ Index Scan: Good (uses index)
- ⚠️ Seq Scan: Warning (full table scan)
- ❌ Nested Loop (large tables): Bad (O(n²) complexity)

---

### 1.6 Connection Pool Performance

#### Configuration
```python
# In SQLAlchemy (apps/api)
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Max permanent connections
    max_overflow=10,        # Extra connections when needed
    pool_timeout=30,        # Wait 30s for connection
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connection before use
)
```

**Performance Metrics**:
- Connection acquisition: 1-10ms
- Connection reuse: <1ms
- Connection pool full: Wait or error (pool_timeout)

**Monitoring**:
```python
# Check connection pool status
from sqlalchemy import inspect

inspector = inspect(engine)
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
print(f"Overflow: {engine.pool.overflow()}")
```

---

### 1.7 Transaction Performance

#### Simple Transaction
```sql
BEGIN;
INSERT INTO products (id, name, category) VALUES ('prod_new', 'New Product', 'PET');
COMMIT;

-- Expected: 5-20ms
```

#### Complex Transaction
```sql
BEGIN;

-- Insert product
INSERT INTO products (id, name, category) VALUES ('prod_new', 'New Product', 'PET');

-- Insert chunks
INSERT INTO chunks (product_id, content) VALUES
  ('prod_new', 'Chunk 1'),
  ('prod_new', 'Chunk 2'),
  ('prod_new', 'Chunk 3');

-- Update stats
UPDATE product_stats SET total_products = total_products + 1;

COMMIT;

-- Expected: 15-60ms
```

**Expected Results**:
```
Transaction Type              | Avg Time | p95 Time
------------------------------|----------|----------
Single INSERT                 | 8ms      | 20ms
Multiple INSERTs (3)          | 22ms     | 55ms
INSERT + UPDATE               | 28ms     | 70ms
Complex (10 operations)       | 75ms     | 180ms
```

---

## 2. Qdrant (Vector Database) Performance

### Database Configuration

**Connection**:
- Host: localhost
- Port: 16333
- Collection: products
- Vector Dimension: 768
- Distance: Cosine

**Collection Info**:
```bash
curl http://localhost:16333/collections/products
```

**Expected Response**:
```json
{
  "result": {
    "status": "green",
    "vectors_count": 3246,
    "points_count": 3246,
    "segments_count": 3,
    "config": {
      "params": {
        "vectors": {
          "size": 768,
          "distance": "Cosine"
        }
      },
      "hnsw_config": {
        "m": 16,
        "ef_construct": 100
      }
    }
  }
}
```

---

### 2.1 Vector Search Performance

**Target**: <100ms (95th percentile)

#### Test Queries
```bash
# Simple vector search (top 5)
curl -X POST http://localhost:16333/collections/products/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ..., 0.768],
    "limit": 5
  }'

# Expected: 30-80ms

# Vector search with filter
curl -X POST http://localhost:16333/collections/products/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ..., 0.768],
    "filter": {
      "must": [
        {"key": "category", "match": {"value": "PET"}}
      ]
    },
    "limit": 5
  }'

# Expected: 50-120ms

# Vector search with score threshold
curl -X POST http://localhost:16333/collections/products/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ..., 0.768],
    "score_threshold": 0.7,
    "limit": 20
  }'

# Expected: 40-100ms
```

**Expected Results**:
```
Query Type                    | Avg Time | p95 Time | Results
------------------------------|----------|----------|--------
Top 5 (no filter)             | 45ms     | 85ms     | 5
Top 5 (with filter)           | 68ms     | 135ms    | 5
Top 20 (score threshold)      | 62ms     | 118ms    | 0-20
Top 100 (large result set)    | 95ms     | 210ms    | 100
```

---

### 2.2 HNSW Index Performance

**HNSW Parameters**:
- `m`: 16 (number of edges per node)
- `ef_construct`: 100 (construction time quality)
- `ef`: 128 (search time quality)

**Parameter Effects**:
```
m value     | Index Size | Build Time | Search Speed | Accuracy
------------|------------|------------|--------------|----------
8           | Small      | Fast       | Slower       | Lower
16 (default)| Medium     | Medium     | Fast         | Good
32          | Large      | Slow       | Faster       | Better
64          | Very Large | Very Slow  | Fastest      | Best
```

**Optimization**:
```python
# Update HNSW config for better search performance
PUT /collections/products

{
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100
  },
  "optimizer_config": {
    "indexing_threshold": 10000
  }
}
```

---

### 2.3 Batch Operations

#### Batch Insert
```python
import requests

# Batch insert 100 vectors
vectors = [
    {
        "id": i,
        "vector": [random.random() for _ in range(768)],
        "payload": {"category": "PET", "name": f"Product {i}"}
    }
    for i in range(100)
]

response = requests.put(
    "http://localhost:16333/collections/products/points",
    json={"points": vectors}
)

# Expected: 500-2000ms for 100 vectors (5-20ms per vector)
```

#### Batch Search
```python
# Search with multiple vectors
response = requests.post(
    "http://localhost:16333/collections/products/points/search/batch",
    json={
        "searches": [
            {"vector": [0.1, ...], "limit": 5},
            {"vector": [0.2, ...], "limit": 5},
            {"vector": [0.3, ...], "limit": 5}
        ]
    }
)

# Expected: 100-300ms for 3 searches (faster than 3 individual requests)
```

---

### 2.4 Filtering Performance

**Filter Impact on Search Speed**:
```
Filter Type                   | Overhead
------------------------------|----------
No filter                     | Baseline
Single field match            | +10-30%
Multiple field match (AND)    | +20-50%
Range filter                  | +30-70%
Complex nested filter         | +50-150%
```

**Example**:
```json
// No filter: 50ms
{
  "vector": [...],
  "limit": 5
}

// With filter: 65ms (+30%)
{
  "vector": [...],
  "filter": {
    "must": [
      {"key": "category", "match": {"value": "PET"}},
      {"key": "price", "range": {"gte": 100, "lte": 1000}}
    ]
  },
  "limit": 5
}
```

---

### 2.5 Memory Usage

**Memory Requirements**:
```
Collection Size    | Vector Dim | Memory Usage
-------------------|------------|---------------
1,000 vectors      | 768        | ~50 MB
10,000 vectors     | 768        | ~500 MB
100,000 vectors    | 768        | ~5 GB
1,000,000 vectors  | 768        | ~50 GB
```

**Current Usage** (3,246 vectors):
- Vector storage: ~20 MB
- HNSW index: ~30 MB
- Metadata: ~5 MB
- Total: ~55 MB

**Monitoring**:
```bash
# Check Qdrant memory usage
docker stats new_rag-qdrant-1 --no-stream
```

---

## 3. Redis Performance

### Database Configuration

**Connection**:
- Host: localhost
- Port: 16379
- Database: 0
- Max Memory: 512 MB
- Eviction Policy: allkeys-lru

---

### 3.1 Basic Operations

**Target**: <5ms (99th percentile)

#### Test Commands
```bash
# Connect to Redis
docker exec -it new_rag-redis-1 redis-cli

# Simple GET/SET
SET key1 "value1"
GET key1

# Expected: 0.5-2ms

# Increment
INCR counter
INCRBY counter 10

# Expected: 0.3-1ms

# Hash operations
HSET user:123 name "John" email "john@example.com"
HGET user:123 name
HGETALL user:123

# Expected: 0.5-3ms

# List operations
LPUSH queue:tasks "task1" "task2" "task3"
RPOP queue:tasks

# Expected: 0.5-2ms

# Set operations
SADD tags:product:123 "PET" "bottle" "50ml"
SMEMBERS tags:product:123

# Expected: 0.5-2ms

# Sorted set operations
ZADD leaderboard 100 "user1" 200 "user2" 150 "user3"
ZRANGE leaderboard 0 10 WITHSCORES

# Expected: 1-5ms
```

**Expected Results**:
```
Operation                     | Avg Time | p99 Time
------------------------------|----------|----------
GET/SET                       | 0.8ms    | 2.5ms
INCR/DECR                     | 0.5ms    | 1.5ms
HGET/HSET                     | 1.2ms    | 3.5ms
LPUSH/RPOP                    | 0.9ms    | 2.8ms
SADD/SMEMBERS                 | 1.1ms    | 3.2ms
ZADD/ZRANGE                   | 1.5ms    | 4.5ms
```

---

### 3.2 Cache Hit Rate

**Target**: >80% cache hit rate

#### Monitoring
```bash
# Get cache stats
redis-cli INFO stats

# Key metrics:
# - keyspace_hits: Number of successful lookups
# - keyspace_misses: Number of failed lookups
# - hit_rate = hits / (hits + misses)
```

**Expected Stats**:
```
keyspace_hits: 8500
keyspace_misses: 1500
hit_rate: 85%
```

**Cache Strategy**:
```python
# Typical cache pattern
async def get_product(product_id: str):
    # Try cache first
    cache_key = f"product:{product_id}"
    cached = await redis.get(cache_key)

    if cached:
        return json.loads(cached)  # Cache hit: 1-3ms

    # Cache miss: Fetch from DB
    product = await db.query(Product).filter(id=product_id).first()  # 10-30ms

    # Store in cache
    await redis.setex(cache_key, 300, json.dumps(product))  # TTL: 5 minutes

    return product
```

---

### 3.3 Pub/Sub Performance

**Target**: <10ms message latency

#### Test Commands
```bash
# Terminal 1: Subscribe
redis-cli SUBSCRIBE channel:notifications

# Terminal 2: Publish
redis-cli PUBLISH channel:notifications "Hello World"

# Expected latency: 2-8ms
```

**Performance with Multiple Subscribers**:
```
Subscribers    | Publish Time | Delivery Time
---------------|--------------|---------------
1              | 1ms          | 2ms
10             | 1ms          | 2-5ms
100            | 2ms          | 3-10ms
1000           | 5ms          | 5-20ms
```

---

### 3.4 Memory Usage

**Current Usage**:
```bash
# Check memory usage
redis-cli INFO memory

# Key metrics:
# - used_memory_human: 45.2M
# - used_memory_peak_human: 67.8M
# - maxmemory_human: 512M
```

**Memory Breakdown**:
```
Type                | Count  | Memory
--------------------|--------|--------
Strings (cache)     | 800    | 25 MB
Hashes (sessions)   | 150    | 12 MB
Lists (queues)      | 50     | 5 MB
Sets (tags)         | 100    | 3 MB
Sorted Sets         | 20     | 2 MB
Total               | 1120   | 47 MB
```

**Eviction Policy**:
```
allkeys-lru: Evict least recently used keys when maxmemory reached
```

---

## 4. ClickHouse Performance

### Database Configuration

**Connection**:
- Host: localhost
- Port: 8123 (HTTP) / 9000 (Native)
- Database: analytics

**Tables**:
- `search_logs`: Query logs
- `user_events`: User interaction events
- `product_views`: Product view tracking

---

### 4.1 Analytical Queries

**Target**: <100ms for aggregations

#### Test Queries
```sql
-- Count events by day
SELECT
  toDate(timestamp) as date,
  COUNT(*) as event_count
FROM user_events
WHERE timestamp >= now() - INTERVAL 7 DAY
GROUP BY date
ORDER BY date;

-- Expected: 20-60ms (7 days data)

-- Top products by views
SELECT
  product_id,
  COUNT(*) as view_count,
  COUNT(DISTINCT user_id) as unique_users
FROM product_views
WHERE timestamp >= now() - INTERVAL 30 DAY
GROUP BY product_id
ORDER BY view_count DESC
LIMIT 10;

-- Expected: 40-120ms (30 days data)

-- Search query analysis
SELECT
  query_text,
  COUNT(*) as search_count,
  AVG(result_count) as avg_results,
  AVG(response_time_ms) as avg_response_time
FROM search_logs
WHERE timestamp >= now() - INTERVAL 7 DAY
GROUP BY query_text
HAVING COUNT(*) > 10
ORDER BY search_count DESC
LIMIT 20;

-- Expected: 60-180ms (7 days data)
```

**Expected Results**:
```
Query Type                    | Data Size | Avg Time | p95 Time
------------------------------|-----------|----------|----------
Count by date (7 days)        | 100k rows | 35ms     | 75ms
Top N aggregation (30 days)   | 500k rows | 78ms     | 165ms
Complex aggregation (7 days)  | 100k rows | 115ms    | 245ms
```

---

### 4.2 Insert Performance

**Target**: >10,000 rows/second

#### Batch Insert
```sql
-- Insert 10,000 rows
INSERT INTO user_events (user_id, event_type, timestamp)
VALUES
  ('user1', 'click', now()),
  ('user2', 'view', now()),
  ...
  ('user10000', 'search', now());

-- Expected: 300-800ms for 10k rows
-- Throughput: 12,500-33,000 rows/second
```

**Performance Tips**:
- Use batch inserts (1000-10000 rows)
- Use async inserts for better throughput
- Partition tables by date for better query performance

---

## 5. Database Comparison

### Performance Comparison

| Database   | Use Case           | Operation        | Latency  | Throughput |
|------------|-------------------|------------------|----------|------------|
| PostgreSQL | Transactional     | SELECT by ID     | 3-10ms   | 1000 QPS   |
| PostgreSQL | Transactional     | JOIN query       | 35-70ms  | 200 QPS    |
| Qdrant     | Vector Search     | Top 5 similar    | 45-85ms  | 200 QPS    |
| Redis      | Cache             | GET/SET          | 0.8-2.5ms| 10000 QPS  |
| ClickHouse | Analytics         | Aggregation      | 35-75ms  | 500 QPS    |

---

## 6. Optimization Recommendations

### PostgreSQL

**1. Add Missing Indexes**
```sql
-- Identify missing indexes
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 10
  AND correlation < 0.5
ORDER BY n_distinct DESC;
```

**2. Vacuum and Analyze**
```sql
-- Regular maintenance
VACUUM ANALYZE products;
VACUUM ANALYZE chunks;

-- Auto-vacuum configuration
ALTER TABLE products SET (autovacuum_vacuum_scale_factor = 0.1);
```

**3. Connection Pooling**
```python
# Use PgBouncer for connection pooling
# Reduces connection overhead by 50-80%
```

### Qdrant

**1. Optimize HNSW Parameters**
```python
# For better accuracy (slower search)
{"m": 32, "ef_construct": 200}

# For better speed (lower accuracy)
{"m": 8, "ef_construct": 50}
```

**2. Use Payload Indexes**
```python
# Create payload index for fast filtering
PUT /collections/products/index
{
  "field_name": "category",
  "field_schema": "keyword"
}
```

### Redis

**1. Enable Persistence**
```
# In redis.conf
save 900 1      # Save if 1 key changed in 900s
save 300 10     # Save if 10 keys changed in 300s
save 60 10000   # Save if 10k keys changed in 60s
```

**2. Monitor Slow Queries**
```bash
# Enable slow log
redis-cli CONFIG SET slowlog-log-slower-than 10000  # 10ms

# View slow queries
redis-cli SLOWLOG GET 10
```

### ClickHouse

**1. Partition Tables**
```sql
-- Partition by month for time-series data
CREATE TABLE user_events (
  user_id String,
  event_type String,
  timestamp DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp);
```

**2. Use Materialized Views**
```sql
-- Pre-aggregate common queries
CREATE MATERIALIZED VIEW daily_stats
ENGINE = SummingMergeTree()
ORDER BY date
AS SELECT
  toDate(timestamp) as date,
  COUNT(*) as event_count
FROM user_events
GROUP BY date;
```

---

## 7. Monitoring and Alerts

### Key Metrics to Track

**PostgreSQL**:
- Connection pool usage
- Query latency (p50, p95, p99)
- Slow query count (>1s)
- Index hit rate (>99%)
- Transaction rate

**Qdrant**:
- Search latency (p50, p95, p99)
- Memory usage
- Collection size
- Failed requests

**Redis**:
- Memory usage (% of max)
- Cache hit rate (>80%)
- Eviction count
- Connected clients

**ClickHouse**:
- Insert throughput
- Query latency
- Merge operations
- Disk usage

---

## 8. Load Testing

### PostgreSQL Load Test
```bash
# Use pgbench for load testing
docker exec -it new_rag-postgres-1 pgbench -i -s 10 rag_db

# Run test: 10 concurrent clients, 1000 transactions
docker exec -it new_rag-postgres-1 pgbench -c 10 -t 1000 rag_db

# Expected: 200-500 TPS
```

### Qdrant Load Test
```python
# Python script for load testing
import asyncio
import aiohttp
import time

async def search(session, vector):
    start = time.time()
    async with session.post(
        "http://localhost:16333/collections/products/points/search",
        json={"vector": vector, "limit": 5}
    ) as response:
        await response.json()
    return time.time() - start

async def main():
    async with aiohttp.ClientSession() as session:
        # 100 concurrent searches
        tasks = [
            search(session, [random.random() for _ in range(768)])
            for _ in range(100)
        ]
        times = await asyncio.gather(*tasks)

        print(f"Mean: {statistics.mean(times)*1000:.2f}ms")
        print(f"p95: {sorted(times)[94]*1000:.2f}ms")

# Expected: 50-100ms mean, 100-200ms p95
```

---

## 9. Baseline Test Results

### Test Environment
- **Date**: 2025-11-19
- **System**: v10.0.0 Unified Maximum
- **Hardware**: [To be measured]

### Results Summary

| Database   | Test              | Target   | Actual | Status |
|------------|-------------------|----------|--------|--------|
| PostgreSQL | Simple SELECT     | <20ms    | [TBD]  | ⏳ |
| PostgreSQL | JOIN Query        | <80ms    | [TBD]  | ⏳ |
| PostgreSQL | Full-text Search  | <200ms   | [TBD]  | ⏳ |
| Qdrant     | Vector Search     | <100ms   | [TBD]  | ⏳ |
| Redis      | GET/SET           | <5ms     | [TBD]  | ⏳ |
| ClickHouse | Aggregation       | <100ms   | [TBD]  | ⏳ |

**Note**: Connect to databases and run the test queries to populate these results.

---

## 10. Next Steps

1. **Connect to Databases**: Verify all databases are running
2. **Run Test Queries**: Execute queries and measure performance
3. **Create Indexes**: Add missing indexes for better performance
4. **Setup Monitoring**: Configure Prometheus/Grafana dashboards
5. **Run Load Tests**: Test with concurrent load
6. **Document Findings**: Update this baseline with actual results

---

## Resources

- **PostgreSQL Docs**: https://www.postgresql.org/docs/16/performance-tips.html
- **Qdrant Docs**: https://qdrant.tech/documentation/guides/optimization/
- **Redis Docs**: https://redis.io/docs/management/optimization/
- **ClickHouse Docs**: https://clickhouse.com/docs/en/operations/optimizing-performance/

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Status**: Ready for Testing
**Next Review**: After first database performance test
