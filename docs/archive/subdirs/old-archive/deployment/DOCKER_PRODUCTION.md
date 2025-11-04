# Docker Production Deployment Guide

**RAG Enterprise v2.4.0**
**Last Updated**: 2025-10-19

Complete guide for deploying RAG Enterprise using Docker in development, staging, and production environments with security hardening, performance optimization, and operational best practices.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Multi-Stage Build Strategy](#multi-stage-build-strategy)
3. [Configuration Management](#configuration-management)
4. [Environment-Specific Deployment](#environment-specific-deployment)
5. [Security Hardening](#security-hardening)
6. [Performance Tuning](#performance-tuning)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Troubleshooting](#troubleshooting)
9. [Operational Procedures](#operational-procedures)
10. [Appendix](#appendix)

---

## Architecture Overview

### System Components

RAG Enterprise consists of five core services orchestrated through Docker Compose:

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Enterprise Stack                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ FastAPI  │  │PostgreSQL│  │  Redis   │  │  Qdrant  │   │
│  │   API    │  │    DB    │  │  Cache   │  │ VectorDB │   │
│  │  (8000)  │  │  (5432)  │  │  (6379)  │  │  (6333)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
│       └─────────────┴─────────────┴─────────────┘          │
│                        │                                    │
│                  ┌────┴─────┐                              │
│                  │Prometheus│                               │
│                  │  (9090)  │                               │
│                  └──────────┘                               │
└─────────────────────────────────────────────────────────────┘
          Network: 172.28.0.0/16 (rag_network)
```

**Service Details**:

| Service | IP Address | Port | Purpose | Resource Limits |
|---------|-----------|------|---------|----------------|
| FastAPI | 172.28.0.7 | 8000 | Application API | 2GB-4GB, 2-4 CPUs |
| PostgreSQL | 172.28.0.4 | 5432 | Relational Database | 2GB-4GB, 2-4 CPUs |
| Redis | 172.28.0.3 | 6379 | Cache Layer | 1GB-4GB, 1-2 CPUs |
| Qdrant | 172.28.0.2 | 6333 | Vector Database | 2GB-6GB, 2-4 CPUs |
| Prometheus | 172.28.0.8 | 9090 | Metrics Collection | 1GB-2GB, 1-2 CPUs |

### Network Architecture

All services communicate over a dedicated bridge network (`rag_network`) with static IP assignments:

- **Subnet**: 172.28.0.0/16
- **Isolation**: Services isolated from host network by default
- **Service Discovery**: DNS-based within Docker network
- **External Access**: Only API (8000) exposed to host by default

---

## Multi-Stage Build Strategy

### Dockerfile Architecture

The production Dockerfile uses a three-stage build process optimized for size (<500MB target) and security:

```dockerfile
# Stage 1: Base Image
python:3.11-slim-bookworm
├── Runtime dependencies only (libpq5, curl, ca-certificates)
├── Non-root user creation (appuser, UID 1000)
└── Minimal system footprint

# Stage 2: Builder
Base + Build tools
├── Compile dependencies (gcc, g++, libpq-dev)
├── Virtual environment creation
├── Python package installation
└── Artifact cleanup

# Stage 3: Runtime
Base + Compiled dependencies
├── Virtual environment copy from builder
├── Application code with proper ownership
├── Non-root user enforcement
└── Health check configuration
```

### Build Optimization Techniques

**Layer Caching Strategy**:
```bash
# Efficient build order (most stable → most volatile)
1. Base system packages (changes rarely)
2. Requirements file (changes occasionally)
3. Dependency installation (changes occasionally)
4. Application code (changes frequently)
```

**Size Reduction**:
- Multi-stage build eliminates build tools (~200MB saved)
- Virtual environment isolation (~50MB saved)
- `__pycache__` and `.pyc` cleanup (~10MB saved)
- No development dependencies (~100MB saved)
- **Total savings**: ~360MB from single-stage build

**Build Performance**:
- Cold build: <3 minutes
- Cached build: <5 seconds (code changes only)
- Image size: <500MB (target achieved)

### Building Images

**Development Build**:
```bash
# Build with development target
docker-compose build

# Build with specific target
docker build --target runtime -t rag-enterprise-api:dev .

# Build with cache optimization
docker build --cache-from rag-enterprise-api:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t rag-enterprise-api:latest .
```

**Production Build**:
```bash
# Build for production
docker build --target runtime \
  --tag rag-enterprise-api:2.4.0 \
  --tag rag-enterprise-api:latest \
  --file Dockerfile .

# Verify image size
docker images rag-enterprise-api:latest

# Expected output:
# REPOSITORY            TAG       SIZE
# rag-enterprise-api    latest    <500MB
```

**Multi-Platform Build** (for deployment to different architectures):
```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 \
  --tag rag-enterprise-api:2.4.0 \
  --push .
```

---

## Configuration Management

### Environment Variable Hierarchy

Configuration is loaded with the following precedence (highest to lowest):

1. **Environment variables** (set in shell or Docker Compose)
2. **`.env` file** (in project root)
3. **Default values** (in `app/core/config.py`)

### Pydantic Validation

The configuration system uses Pydantic for comprehensive validation:

```python
from app.core.config import get_settings, Environment

settings = get_settings()

# Automatic type conversion
assert isinstance(settings.api_port, int)
assert isinstance(settings.debug, bool)

# Environment-specific validation
if settings.environment == Environment.PRODUCTION:
    assert len(settings.jwt_secret_key) >= 64
    assert settings.sentry_dsn is not None
    assert settings.debug is False
```

**Validation Rules Summary**:

| Environment | JWT Secret | Sentry DSN | Debug Mode | Log Level |
|------------|-----------|------------|------------|-----------|
| Development | ≥32 chars | Optional | Allowed | Any |
| Staging | ≥64 chars | Recommended | Allowed | INFO+ |
| Production | ≥64 chars | **Required** | **Forbidden** | WARNING+ |

### Creating Environment Files

**Development (`.env`)**:
```bash
# Copy template
cp .env.example .env

# Edit with your values
vim .env

# Minimal required variables
ENVIRONMENT=development
POSTGRES_PASSWORD=dev_password_min_16_chars
JWT_SECRET_KEY=$(openssl rand -base64 32)
```

**Staging (`.env.staging`)**:
```bash
# Required variables for staging
ENVIRONMENT=staging
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 64)
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
SENTRY_TRACES_SAMPLE_RATE=0.3
```

**Production (`.env.production`)**:
```bash
# CRITICAL: Use secret management system (Vault, AWS Secrets Manager)
# Never store production secrets in plain text files

ENVIRONMENT=production
POSTGRES_PASSWORD=${VAULT_POSTGRES_PASSWORD}
JWT_SECRET_KEY=${VAULT_JWT_SECRET}
SENTRY_DSN=${VAULT_SENTRY_DSN}
ALLOWED_ORIGINS=https://app.example.com,https://api.example.com
LOG_LEVEL=WARNING
DEBUG=false
```

### Secrets Management Best Practices

**Development**:
- `.env` file acceptable
- Commit `.env.example` with placeholders
- Add `.env` to `.gitignore`

**Staging/Production**:
1. **Use Secret Management Systems**:
   - HashiCorp Vault
   - AWS Secrets Manager
   - Google Secret Manager
   - Azure Key Vault

2. **Inject Secrets at Runtime**:
   ```bash
   # Using environment variables
   export POSTGRES_PASSWORD=$(vault kv get -field=password secret/postgres)
   docker-compose up -d

   # Using Docker secrets (Swarm mode)
   echo "secret_value" | docker secret create postgres_password -
   ```

3. **Rotate Regularly**:
   - JWT secrets: Every 90 days
   - Database passwords: Every 60 days
   - API keys: Per provider recommendations

---

## Environment-Specific Deployment

### Development Environment

**Purpose**: Local development with hot-reload and debug tools

**Features**:
- Source code volume mounts for hot-reload
- Debug logging enabled
- Swagger UI available
- Single worker process
- Moderate resource limits

**Deployment**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Access services
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Prometheus: http://localhost:9090

# Rebuild after code changes
docker-compose up -d --build api

# Stop all services
docker-compose down
```

**Resource Usage** (typical):
- Total memory: 2.5GB-8GB
- Total CPU: 2-8 cores
- Disk I/O: Low

### Staging Environment

**Purpose**: Production-like testing environment

**Features**:
- Image-based deployment (no hot-reload)
- INFO-level logging
- Sentry integration enabled
- 2 worker processes
- Production-like resource limits

**Deployment**:
```bash
# Build staging image
docker-compose -f docker-compose.yml \
  -f docker-compose.staging.yml \
  build

# Start staging stack
docker-compose -f docker-compose.yml \
  -f docker-compose.staging.yml \
  up -d

# Health check
docker-compose -f docker-compose.yml \
  -f docker-compose.staging.yml \
  ps

# View metrics
curl http://localhost:9090/metrics
```

**Resource Usage** (typical):
- Total memory: 4GB-12.5GB
- Total CPU: 4-8.5 cores
- Disk I/O: Moderate

### Production Environment

**Purpose**: Live production deployment

**Features**:
- Optimized image build
- WARNING-level logging
- Full Sentry traces
- 4 workers × 3 replicas = 12 total
- Maximum resource allocation
- Strict security enforcement

**Deployment**:
```bash
# Build production image with versioning
docker build -t rag-enterprise-api:2.4.0 .
docker tag rag-enterprise-api:2.4.0 rag-enterprise-api:production

# Start production stack
docker-compose -f docker-compose.yml \
  -f docker-compose.production.yml \
  up -d

# Scale API service
docker-compose -f docker-compose.yml \
  -f docker-compose.production.yml \
  up -d --scale api=3

# Zero-downtime rolling update
docker-compose -f docker-compose.yml \
  -f docker-compose.production.yml \
  up -d --no-deps --build api

# Health verification
for i in {1..10}; do
  curl -f http://localhost:8000/health || echo "Health check failed"
  sleep 2
done
```

**Resource Usage** (typical with 3 API replicas):
- Total memory: 14GB-28GB
- Total CPU: 14-28 cores
- Disk I/O: High

---

## Security Hardening

### Container Security

**Non-Root User Enforcement**:
```dockerfile
# Dockerfile enforces non-root execution
USER appuser  # UID 1000, GID 1000

# Verify in running container
docker exec rag-api whoami  # Output: appuser
docker exec rag-api id      # Output: uid=1000(appuser) gid=1000(appuser)
```

**Read-Only Filesystem** (optional, advanced):
```yaml
# docker-compose.production.yml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
      - /app/temp
    volumes:
      - ./logs:/app/logs:rw  # Only logs writable
```

**Capability Dropping**:
```yaml
services:
  api:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to ports <1024
```

### Network Security

**Service Isolation**:
```yaml
# Only expose necessary ports to host
ports:
  - "8000:8000"  # API only, other services internal

# Internal service communication
networks:
  rag_network:
    internal: false  # Set to true for complete isolation
```

**TLS/SSL Configuration** (production):
```yaml
# Use reverse proxy (Nginx, Traefik) for TLS termination
# Example Nginx configuration:
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    location / {
        proxy_pass http://172.28.0.7:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Secrets Management

**Never Store Secrets in Images**:
```bash
# Bad practice
ENV JWT_SECRET_KEY=secret_value  # NEVER DO THIS

# Good practice
# Use environment variables injected at runtime
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}
```

**Docker Secrets** (Swarm mode):
```yaml
services:
  api:
    secrets:
      - postgres_password
      - jwt_secret

secrets:
  postgres_password:
    external: true
  jwt_secret:
    external: true
```

### Vulnerability Scanning

**Scan Images Before Deployment**:
```bash
# Using Trivy
trivy image rag-enterprise-api:latest

# Using Snyk
snyk container test rag-enterprise-api:latest

# Using Docker Scout
docker scout cves rag-enterprise-api:latest

# Fail CI/CD on critical vulnerabilities
trivy image --exit-code 1 --severity CRITICAL rag-enterprise-api:latest
```

---

## Performance Tuning

### PostgreSQL Optimization

**Connection Pooling**:
```python
# app/core/config.py
postgres_pool_size: int = 50          # Base connections
postgres_max_overflow: int = 20       # Burst capacity
postgres_pool_timeout: int = 30       # Wait timeout
postgres_pool_recycle: int = 3600     # Recycle after 1 hour
```

**Database Parameters** (production):
```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 512MB         # 25% of system RAM
  POSTGRES_EFFECTIVE_CACHE_SIZE: 2GB     # 50-75% of system RAM
  POSTGRES_WORK_MEM: 16MB                # Per-operation memory
  POSTGRES_MAINTENANCE_WORK_MEM: 256MB   # Vacuum/index operations
  POSTGRES_MAX_CONNECTIONS: 500          # Total connections
  POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
  POSTGRES_WAL_BUFFERS: 16MB
  POSTGRES_RANDOM_PAGE_COST: 1.1        # For SSD storage
```

### Redis Optimization

**Memory Management**:
```yaml
command: >
  redis-server
  --maxmemory 4gb
  --maxmemory-policy allkeys-lru
  --save 900 1
  --save 300 10
  --save 60 10000
  --tcp-keepalive 300
  --timeout 300
  --maxclients 10000
```

**Connection Pooling**:
```python
# app/core/config.py
redis_pool_max_connections: int = 100   # Production
redis_pool_min_idle: int = 10           # Minimum idle
```

### Qdrant Optimization

**Search Performance**:
```yaml
environment:
  QDRANT__SERVICE__MAX_REQUEST_SIZE_MB: 128
  QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS: 4
```

**Index Configuration**:
```python
# When creating collections
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE,
        hnsw_config=HnswConfigDiff(
            m=16,                # Connections per node
            ef_construct=100,    # Construction time quality
        )
    )
)
```

### API Server Tuning

**Uvicorn Workers**:
```python
# Formula: (2 * CPU_CORES) + 1
# Development: 1 worker
# Staging: 2 workers
# Production: 4-8 workers

uvicorn_workers: int = 4
uvicorn_timeout_keep_alive: int = 120
uvicorn_backlog: int = 4096
uvicorn_limit_concurrency: int = 1000
```

**Resource Limits**:
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
    reservations:
      cpus: '2.0'
      memory: 2G
```

### Monitoring Performance

**Key Metrics to Track**:
- Request latency (p50, p95, p99)
- Throughput (requests/second)
- Error rate
- Database connection pool utilization
- Cache hit rate
- Memory usage per service
- CPU utilization

**Prometheus Queries**:
```promql
# Request latency P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Cache hit rate
rate(rag_cache_hits_total[5m]) / (rate(rag_cache_hits_total[5m]) + rate(rag_cache_misses_total[5m]))

# Database connection pool usage
postgres_pool_size / postgres_pool_max_connections
```

---

## Monitoring and Observability

### Health Checks

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1697741234.567,
  "duration_ms": 123.45,
  "components": [
    {
      "component": "postgresql",
      "status": "healthy",
      "latency_ms": 12.34,
      "message": "Database is operational"
    },
    {
      "component": "redis",
      "status": "healthy",
      "latency_ms": 3.21,
      "message": "Cache is operational"
    },
    {
      "component": "qdrant",
      "status": "healthy",
      "latency_ms": 45.67,
      "message": "Vector database is operational"
    }
  ],
  "summary": {
    "healthy": 3,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

**Health Check Integration**:
```bash
# Docker Compose health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s

# Manual health check
curl -f http://localhost:8000/health || echo "Service unhealthy"

# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 30
```

### Metrics Collection

**Prometheus Integration**:
- API metrics exposed at `/metrics`
- Scrape interval: 10-15 seconds
- Retention: 7 days (dev), 15 days (staging), 30 days (production)

**Available Metrics**:
```
# HTTP metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}
http_requests_in_progress

# Business metrics
rag_embeddings_generated_total
rag_search_queries_total
rag_search_latency_seconds
rag_cache_hits_total
rag_cache_misses_total

# System metrics
process_cpu_seconds_total
process_resident_memory_bytes
process_open_fds
```

### Log Aggregation

**Structured Logging**:
```python
# All logs are JSON-formatted
{
  "timestamp": "2025-10-19T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.api.main",
  "message": "Request processed",
  "request_id": "req-abc123",
  "user_id": "user-456",
  "duration_ms": 123.45,
  "status_code": 200
}
```

**Log Collection**:
```bash
# View logs
docker-compose logs -f api

# Export logs to file
docker-compose logs api > api.log

# Centralized logging (production)
# Use ELK Stack, Loki, or CloudWatch
```

### Error Tracking

**Sentry Integration**:
```python
# Automatically enabled when SENTRY_DSN is configured
# Captures:
# - Exceptions and stack traces
# - Performance transactions
# - User context
# - Request context
# - Breadcrumbs

# Production configuration
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% transaction sampling
```

---

## Troubleshooting

### Common Issues

**1. Container Won't Start**

**Symptom**: Container exits immediately after starting

**Diagnosis**:
```bash
# Check container logs
docker-compose logs api

# Check container exit code
docker-compose ps api

# Inspect container
docker inspect rag-api
```

**Common Causes**:
- Missing required environment variables
- Configuration validation failure
- Port already in use
- Insufficient resources

**Solution**:
```bash
# Validate environment variables
docker-compose config

# Check port conflicts
lsof -i :8000

# Increase resource limits
# Edit docker-compose.yml deploy.resources section
```

**2. Database Connection Failures**

**Symptom**: "could not connect to server" errors

**Diagnosis**:
```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready

# Test connection from API container
docker-compose exec api python -c "
from app.core.config import get_settings
import psycopg
settings = get_settings()
conn = psycopg.connect(settings.postgres_dsn)
print('Connection successful')
"

# Check network connectivity
docker-compose exec api ping postgres
```

**Solution**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Verify credentials
# Check .env file POSTGRES_PASSWORD

# Wait for PostgreSQL to be ready
docker-compose up -d postgres
sleep 10
docker-compose up -d api
```

**3. High Memory Usage**

**Symptom**: Containers consuming excessive memory

**Diagnosis**:
```bash
# Monitor resource usage
docker stats

# Check memory limits
docker inspect rag-api | grep -i memory

# Profile application memory
docker-compose exec api python -m memory_profiler app/api/main.py
```

**Solution**:
```bash
# Adjust memory limits
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 4G

# Optimize application code
# Reduce batch sizes
# Enable garbage collection tuning
```

**4. Slow API Responses**

**Diagnosis**:
```bash
# Check API latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# curl-format.txt:
# time_namelookup: %{time_namelookup}
# time_connect: %{time_connect}
# time_starttransfer: %{time_starttransfer}
# time_total: %{time_total}

# Check database query performance
docker-compose exec postgres psql -U postgres -d rag_enterprise -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check Redis latency
docker-compose exec redis redis-cli --latency
```

**Solution**:
```bash
# Add database indexes
# Optimize slow queries
# Increase worker count
# Enable caching
# Scale horizontally
```

### Debugging Tools

**Access Container Shell**:
```bash
# API container
docker-compose exec api bash

# PostgreSQL container
docker-compose exec postgres bash

# Redis container
docker-compose exec redis sh
```

**Live Debugging**:
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Attach to running container
docker attach rag-api
```

**Network Debugging**:
```bash
# Test inter-service connectivity
docker-compose exec api curl http://172.28.0.4:5432
docker-compose exec api nc -zv postgres 5432

# Inspect network
docker network inspect rag_network

# Packet capture
docker run --rm --net=container:rag-api \
  nicolaka/netshoot tcpdump -i any -w /tmp/capture.pcap
```

---

## Operational Procedures

### Backup and Restore

**Database Backup**:
```bash
# Create backup
docker-compose exec -T postgres pg_dump \
  -U postgres rag_enterprise | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore from backup
gunzip < backup_20251019_103045.sql.gz | \
  docker-compose exec -T postgres psql -U postgres rag_enterprise
```

**Volume Backup**:
```bash
# Backup all volumes
docker run --rm \
  -v rag-enterprise_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data_backup.tar.gz /data

# Restore volume
docker run --rm \
  -v rag-enterprise_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_data_backup.tar.gz -C /
```

### Rolling Updates

**Zero-Downtime Deployment**:
```bash
# 1. Build new image
docker build -t rag-enterprise-api:2.4.1 .

# 2. Update with rolling restart
docker-compose -f docker-compose.yml \
  -f docker-compose.production.yml \
  up -d --no-deps --scale api=6 api

# 3. Wait for new containers to be healthy
sleep 30

# 4. Remove old containers
docker-compose -f docker-compose.yml \
  -f docker-compose.production.yml \
  up -d --no-deps --scale api=3 api

# 5. Verify deployment
curl http://localhost:8000/health
```

### Scaling

**Horizontal Scaling**:
```bash
# Scale API service
docker-compose up -d --scale api=5

# Verify scaling
docker-compose ps api

# Load balancing handled by Docker
```

**Vertical Scaling**:
```yaml
# Edit docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 8G

# Restart with new limits
docker-compose up -d --force-recreate api
```

### Maintenance Mode

**Enable Maintenance**:
```bash
# Stop API service
docker-compose stop api

# Deploy maintenance page
# Configure reverse proxy to show maintenance page

# Perform maintenance
docker-compose exec postgres vacuumdb -U postgres --all --analyze
```

**Disable Maintenance**:
```bash
# Restart API service
docker-compose start api

# Remove maintenance page configuration
```

---

## Appendix

### Quick Reference Commands

**Build and Deploy**:
```bash
# Development
docker-compose up -d --build

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d --scale api=3
```

**Logs and Monitoring**:
```bash
# View logs
docker-compose logs -f api

# Check status
docker-compose ps

# Resource usage
docker stats

# Health check
curl http://localhost:8000/health
```

**Maintenance**:
```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: destroys data)
docker-compose down -v

# Prune unused resources
docker system prune -a --volumes
```

### Performance Benchmarks

**Expected Performance** (single API instance, 4 workers):
- Throughput: 500-1000 req/s
- Latency (P95): <100ms
- Embedding generation: ~100 docs/s
- Vector search: <50ms (1M vectors)

**Stress Testing**:
```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/api/v1/search?query=test

# Using Locust
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Resource Sizing Guide

**Development Environment**:
- RAM: 8GB minimum
- CPU: 4 cores minimum
- Disk: 20GB minimum

**Production Environment (per instance)**:
- RAM: 32GB recommended (16GB minimum)
- CPU: 8 cores recommended (4 cores minimum)
- Disk: 100GB+ SSD storage
- Network: 1Gbps+

### Additional Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
- [Redis Best Practices](https://redis.io/docs/manual/config/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-19
**Maintained By**: RAG Enterprise Team
