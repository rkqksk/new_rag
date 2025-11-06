# RAG Enterprise - Production Deployment Guide

**Version**: 1.0  
**Last Updated**: 2025-11-06  
**Status**: Production-Ready

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Testing Deployment](#testing-deployment)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum** (Development):
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB
- OS: Linux (Ubuntu 20.04+), macOS, Windows (WSL2)

**Recommended** (Production):
- CPU: 8+ cores
- RAM: 16GB+
- Disk: 50GB+ SSD
- GPU: NVIDIA GPU with CUDA (optional, for OCR acceleration)

### Software Requirements

```bash
# Docker & Docker Compose
docker --version  # >= 20.10
docker-compose --version  # >= 2.0

# Python (for local development)
python --version  # >= 3.11

# PostgreSQL Client (for migrations)
psql --version  # >= 15

# Redis CLI (for cache management)
redis-cli --version  # >= 7.0
```

### Installation

**Ubuntu/Debian**:
```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose
sudo apt-get install docker-compose-plugin

# PostgreSQL Client
sudo apt-get install postgresql-client

# Redis CLI
sudo apt-get install redis-tools
```

**macOS**:
```bash
# Docker Desktop
brew install --cask docker

# PostgreSQL Client
brew install postgresql@15

# Redis CLI
brew install redis
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/rag-enterprise.git
cd rag-enterprise
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or vim, code, etc.
```

**Minimal `.env` for development**:
```bash
ENVIRONMENT=development
DEBUG_ENABLED=true

DB_HOST=postgres
DB_PASSWORD=your_secure_password

REDIS_HOST=redis

QDRANT_HOST=qdrant
```

### 3. Start Services

```bash
# Option A: Quick start (automated)
./deploy.sh development

# Option B: Manual start
docker-compose up -d
```

### 4. Verify Deployment

```bash
#Run test suite
./test_system.sh
```

**Expected Output**:
```
✓ Qdrant is running
✓ Redis is running
✓ PostgreSQL is running
✓ Backend is running
✓ All tests passed!
```

### 5. Access Services

```
Frontend:  http://localhost:8080
API:       http://localhost:8001
API Docs:  http://localhost:8001/api/v1/docs
Qdrant UI: http://localhost:6333/dashboard
```

---

## Environment Configuration

### Development Environment

**`.env` for development**:
```bash
# Application
ENVIRONMENT=development
DEBUG_ENABLED=true

# Debug Configuration
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=true
DEBUG_LOG_SQL=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=300

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=rag_enterprise
DB_USER=postgres
DB_PASSWORD=dev_password_change_me
DB_POOL_SIZE=20

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_PRODUCTS_COLLECTION=products_multimodal
```

### Staging Environment

**`.env` for staging**:
```bash
# Application
ENVIRONMENT=staging
DEBUG_ENABLED=true  # Enable for troubleshooting

# Debug Configuration (moderate)
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=false  # Too verbose
DEBUG_LOG_SQL=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=500

# Database (use staging database)
DB_HOST=staging-db.your-company.com
DB_PORT=5432
DB_NAME=rag_enterprise_staging
DB_USER=rag_staging_user
DB_PASSWORD=<from_secrets_manager>
DB_POOL_SIZE=20

# Redis (use staging Redis)
REDIS_HOST=staging-redis.your-company.com
REDIS_PORT=6379

# Qdrant (use staging Qdrant)
QDRANT_HOST=staging-qdrant.your-company.com
QDRANT_PORT=6333
```

### Production Environment

**`.env` for production**:
```bash
# Application
ENVIRONMENT=production
DEBUG_ENABLED=false  # ⚠️ MUST be false in production

# Database (use production database)
DB_HOST=prod-db.your-company.com
DB_PORT=5432
DB_NAME=rag_enterprise
DB_USER=rag_prod_user
DB_PASSWORD=<from_secrets_manager>
DB_POOL_SIZE=50  # Increase for production

# Redis (use production Redis cluster)
REDIS_HOST=prod-redis.your-company.com
REDIS_PORT=6379
REDIS_PASSWORD=<from_secrets_manager>

# Qdrant (use production Qdrant cluster)
QDRANT_HOST=prod-qdrant.your-company.com
QDRANT_PORT=6333
```

---

## Docker Deployment

### Development Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      DB_HOST: ${DB_HOST}
      DB_NAME: ${DB_NAME}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_HOST: ${REDIS_HOST}
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      QDRANT_HOST: ${QDRANT_HOST}
      ENVIRONMENT: production
      DEBUG_ENABLED: false
    depends_on:
      - postgres
      - redis
      - qdrant
    restart: unless-stopped
    deploy:
      replicas: 2  # Run 2 instances for HA
      resources:
        limits:
          cpus: '4'
          memory: 8G

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

**Deploy production**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Testing Deployment

### Automated Testing

```bash
# Full test suite
./test_system.sh

# API tests only
curl http://localhost:8001/health/live
curl http://localhost:8001/api/v1/search/ -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "50ml PET 용기", "top_k": 10}'

# Python test suite
pytest tests/ -v
```

### Manual Testing Checklist

- [ ] Health checks pass (`/health/live`, `/health/ready`)
- [ ] API documentation accessible (`/api/v1/docs`)
- [ ] Search endpoint works
- [ ] Personalization tracking works
- [ ] Analytics endpoints work
- [ ] Debug endpoints work (if enabled)
- [ ] OCR pipeline processes files
- [ ] Frontend connects to backend
- [ ] Database connections stable
- [ ] Redis caching works
- [ ] Qdrant vector search works

---

## Production Deployment

### Cloud Deployment Options

#### AWS Deployment

**Architecture**:
```
ELB (Load Balancer)
  ├─ ECS/Fargate (API containers)
  ├─ RDS PostgreSQL
  ├─ ElastiCache Redis
  └─ EC2 (Qdrant on dedicated instance)
```

**Steps**:
1. Create VPC and subnets
2. Deploy RDS PostgreSQL
3. Deploy ElastiCache Redis
4. Deploy Qdrant on EC2 (with EBS volume)
5. Create ECS cluster
6. Deploy API containers via ECS/Fargate
7. Configure ALB (Application Load Balancer)
8. Set up Route53 for DNS

#### Google Cloud Deployment

**Architecture**:
```
Cloud Load Balancer
  ├─ GKE (Kubernetes cluster)
  ├─ Cloud SQL (PostgreSQL)
  ├─ Memorystore (Redis)
  └─ GCE (Qdrant on VM)
```

#### On-Premises Deployment

**Architecture**:
```
Nginx/HAProxy (Load Balancer)
  ├─ Docker Swarm / Kubernetes
  ├─ PostgreSQL (Primary + Replica)
  ├─ Redis (Cluster mode)
  └─ Qdrant (Cluster mode)
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-enterprise-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: api
        image: your-registry/rag-enterprise:latest
        ports:
        - containerPort: 8001
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: rag-config
              key: db_host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: db_password
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

**Deploy**:
```bash
kubectl apply -f k8s/
```

---

## Monitoring & Maintenance

### Health Monitoring

**Endpoint**: `GET /health/ready`

**Response**:
```json
{
  "status": "ready",
  "debug_enabled": false,
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  }
}
```

### Performance Metrics

**Prometheus metrics** exposed at `/metrics`:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `cache_hits_total` - Cache hit count
- `cache_misses_total` - Cache miss count
- `vector_search_duration_seconds` - Vector search time

### Log Monitoring

**Structured JSON logs**:
```json
{
  "timestamp": "2025-11-06T12:34:56Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_path": "POST /api/v1/search/",
  "duration_ms": 145.32,
  "message": "Request completed"
}
```

**Aggregate logs**:
```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# Search for errors
docker-compose logs api | grep ERROR

# Follow slow requests
docker-compose logs api | grep "SLOW REQUEST"
```

### Database Maintenance

**Backups**:
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres rag_enterprise > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres rag_enterprise < backup.sql

# Backup Qdrant
curl -X POST http://localhost:6333/collections/products_multimodal/snapshots

# Backup Redis
docker-compose exec redis redis-cli SAVE
```

---

## Troubleshooting

### Common Issues

**Problem**: Services won't start

**Solution**:
```bash
# Check Docker daemon
systemctl status docker

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

**Problem**: Connection refused errors

**Solution**:
```bash
# Verify services are running
docker-compose ps

# Check ports
netstat -tulpn | grep -E '(6333|6379|5432|8001)'

# Check firewall
sudo ufw status
```

**Problem**: Slow API responses

**Solution**:
```bash
# Enable debug mode
DEBUG_ENABLED=true
DEBUG_PROFILE_REQUESTS=true

# Check performance summary
curl http://localhost:8001/api/v1/debug/performance/summary

# Check slow queries
curl http://localhost:8001/api/v1/debug/queries/recent?slow_only=true
```

**Problem**: Out of memory

**Solution**:
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Edit Docker Desktop settings or /etc/docker/daemon.json

# Reduce pool sizes in .env
DB_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=20
```

---

## Security Checklist

Production deployment security:

- [ ] Change all default passwords
- [ ] Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
- [ ] Enable HTTPS (TLS/SSL certificates)
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Disable debug mode (`DEBUG_ENABLED=false`)
- [ ] Review CORS settings
- [ ] Enable authentication/authorization
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Set up intrusion detection

---

## Support

**Documentation**:
- [API Documentation](./API_DOCUMENTATION.md)
- [Debug System](./DEBUG_SYSTEM.md)
- [OCR Strategy](./OCR_PARSING_STRATEGY.md)
- [Roadmap](./ROADMAP.md)

**Issues**: Report at GitHub Issues

---

**Last Updated**: 2025-11-06  
**Version**: 1.0  
**Status**: Production-Ready ✅
