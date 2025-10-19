"""
Prometheus Metrics Collection

Defines all metrics for RAG Enterprise including:
- HTTP request metrics (latency, throughput, errors)
- Embedding generation metrics
- Vector search metrics
- Cache performance metrics
- Service-level metrics
"""
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
)

# Create registry for metrics
REGISTRY = CollectorRegistry()

# ============================================================
# HTTP Request Metrics
# ============================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=REGISTRY
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=REGISTRY
)

# ============================================================
# Embedding Metrics
# ============================================================

embedding_generation_total = Counter(
    'embedding_generation_total',
    'Total embeddings generated',
    ['model'],
    registry=REGISTRY
)

embedding_generation_duration_seconds = Histogram(
    'embedding_generation_duration_seconds',
    'Embedding generation latency in seconds',
    ['model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=REGISTRY
)

embedding_batch_size = Histogram(
    'embedding_batch_size',
    'Embedding batch size',
    ['model'],
    buckets=(1, 8, 16, 32, 64, 128),
    registry=REGISTRY
)

embedding_cache_hits = Counter(
    'embedding_cache_hits',
    'Embedding cache hits',
    ['cache_type'],
    registry=REGISTRY
)

embedding_cache_misses = Counter(
    'embedding_cache_misses',
    'Embedding cache misses',
    registry=REGISTRY
)

embedding_cache_hit_rate = Gauge(
    'embedding_cache_hit_rate',
    'Embedding cache hit rate (0-1)',
    registry=REGISTRY
)

# ============================================================
# Vector Search Metrics
# ============================================================

vector_search_total = Counter(
    'vector_search_total',
    'Total vector searches',
    ['collection'],
    registry=REGISTRY
)

vector_search_duration_seconds = Histogram(
    'vector_search_duration_seconds',
    'Vector search latency in seconds',
    ['collection'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=REGISTRY
)

vector_search_results_returned = Histogram(
    'vector_search_results_returned',
    'Number of results returned from vector search',
    ['collection'],
    buckets=(1, 5, 10, 20, 50, 100),
    registry=REGISTRY
)

vector_search_similarity_score = Histogram(
    'vector_search_similarity_score',
    'Similarity scores from vector search',
    ['collection'],
    buckets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
    registry=REGISTRY
)

# ============================================================
# Qdrant Database Metrics
# ============================================================

qdrant_upsert_total = Counter(
    'qdrant_upsert_total',
    'Total points upserted to Qdrant',
    ['collection'],
    registry=REGISTRY
)

qdrant_upsert_duration_seconds = Histogram(
    'qdrant_upsert_duration_seconds',
    'Qdrant upsert latency in seconds',
    ['collection'],
    buckets=(0.01, 0.1, 0.5, 1.0, 5.0, 10.0),
    registry=REGISTRY
)

qdrant_collection_size = Gauge(
    'qdrant_collection_size',
    'Number of points in Qdrant collection',
    ['collection'],
    registry=REGISTRY
)

# ============================================================
# Redis Cache Metrics
# ============================================================

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=REGISTRY
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation latency in seconds',
    ['operation'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=REGISTRY
)

redis_key_count = Gauge(
    'redis_key_count',
    'Number of keys in Redis',
    registry=REGISTRY
)

# ============================================================
# Document Processing Metrics
# ============================================================

document_ingestion_total = Counter(
    'document_ingestion_total',
    'Total documents ingested',
    ['format', 'status'],
    registry=REGISTRY
)

document_ingestion_duration_seconds = Histogram(
    'document_ingestion_duration_seconds',
    'Document ingestion latency in seconds',
    ['format'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY
)

document_chunk_count = Histogram(
    'document_chunk_count',
    'Number of chunks per document',
    buckets=(1, 10, 50, 100, 500, 1000),
    registry=REGISTRY
)

document_size_bytes = Histogram(
    'document_size_bytes',
    'Document size in bytes',
    ['format'],
    buckets=(1000, 10000, 100000, 1000000, 10000000),
    registry=REGISTRY
)

# ============================================================
# LLM Query Metrics
# ============================================================

llm_query_total = Counter(
    'llm_query_total',
    'Total LLM queries',
    ['model', 'status'],
    registry=REGISTRY
)

llm_query_duration_seconds = Histogram(
    'llm_query_duration_seconds',
    'LLM query latency in seconds',
    ['model'],
    buckets=(1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY
)

llm_tokens_generated = Histogram(
    'llm_tokens_generated',
    'Tokens generated by LLM',
    ['model'],
    buckets=(10, 50, 100, 500, 1000, 5000),
    registry=REGISTRY
)

llm_confidence_score = Histogram(
    'llm_confidence_score',
    'LLM response confidence score',
    buckets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
    registry=REGISTRY
)

# ============================================================
# System Health Metrics
# ============================================================

active_requests = Gauge(
    'active_requests',
    'Number of active requests',
    ['endpoint'],
    registry=REGISTRY
)

errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint'],
    registry=REGISTRY
)

exception_total = Counter(
    'exception_total',
    'Total exceptions',
    ['exception_type'],
    registry=REGISTRY
)

database_connection_errors = Counter(
    'database_connection_errors',
    'Database connection errors',
    ['database'],
    registry=REGISTRY
)

# ============================================================
# Cache Performance Metrics
# ============================================================

cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio (0-1)',
    ['cache_type'],
    registry=REGISTRY
)

cache_evictions_total = Counter(
    'cache_evictions_total',
    'Total cache evictions',
    ['cache_type'],
    registry=REGISTRY
)

cache_memory_bytes = Gauge(
    'cache_memory_bytes',
    'Cache memory usage in bytes',
    ['cache_type'],
    registry=REGISTRY
)

# ============================================================
# Performance Tracking
# ============================================================

p95_latency_seconds = Gauge(
    'p95_latency_seconds',
    'P95 latency in seconds',
    ['operation'],
    registry=REGISTRY
)

p99_latency_seconds = Gauge(
    'p99_latency_seconds',
    'P99 latency in seconds',
    ['operation'],
    registry=REGISTRY
)

throughput_requests_per_second = Gauge(
    'throughput_requests_per_second',
    'Throughput in requests per second',
    registry=REGISTRY
)
