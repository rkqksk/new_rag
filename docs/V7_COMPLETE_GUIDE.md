# RAG Enterprise v7.0.0 - Complete Production Guide

**Status**: ✅ Production Ready | **Type**: Ultimate Open Source Edition | **Cost**: $0/month

---

## 🎯 Overview

v7.0.0 is the **ultimate open-source production platform** with enterprise-grade features:
- ✅ **100% Open Source** - Zero software costs
- ✅ **Production-Ready** - Battle-tested components
- ✅ **Enterprise Features** - SSO, Secrets, Tracing, Object Storage, ETL
- ✅ **Auto-Scaling** - Kubernetes HPA + KEDA
- ✅ **Observable** - OpenTelemetry + Jaeger + Prometheus + Grafana
- ✅ **Secure** - Keycloak OAuth2 + Vault Secrets + RBAC

---

## 📊 Complete Service Stack

### Core Infrastructure (v6.0.0)
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 15432 | Primary database |
| Redis | 16379 | Cache + Rate Limiting |
| Qdrant | 16333 | Vector database |
| API | 8001 | FastAPI application |

### Analytics Stack (v6.0.0)
| Service | Port | Purpose |
|---------|------|---------|
| ClickHouse | 8123, 9000 | OLAP analytics |
| Kafka | 9092 | Event streaming |
| Zookeeper | 2181 | Kafka coordination |

### Monitoring Stack (v6.0.0)
| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |

### Security Stack (v7.0.0) ⭐ NEW
| Service | Port | Purpose |
|---------|------|---------|
| Keycloak | 8080 | OAuth2/OIDC SSO |
| Vault | 8200 | Secret management |

### Observability Stack (v7.0.0) ⭐ NEW
| Service | Port | Purpose |
|---------|------|---------|
| Jaeger | 16686 | Distributed tracing |
| OpenTelemetry | - | Instrumentation |

### Data Platform (v7.0.0) ⭐ NEW
| Service | Port | Purpose |
|---------|------|---------|
| MinIO | 9001, 9002 | Object storage (S3) |
| Airflow | 8082 | ETL workflows |
| Metabase | 3001 | Business intelligence |

**Total Services**: 17 containers

---

## 🚀 Quick Start

### 1. Start All Services

```bash
# Clone repository
git clone https://github.com/rkqksk/new_rag.git
cd new_rag

# Start everything (17 services)
docker-compose up -d

# Wait for services (2-3 minutes)
docker-compose ps

# Check API health
curl http://localhost:8001/health/ready
```

### 2. Access Services

```bash
# Core Services
API Docs:      http://localhost:8001/api/v1/docs
GraphQL:       http://localhost:8001/api/v1/graphql
Frontend:      http://localhost:8080/chat.html

# Security
Keycloak:      http://localhost:8080 (admin/admin)
Vault:         http://localhost:8200 (token: root)

# Observability
Jaeger UI:     http://localhost:16686
Prometheus:    http://localhost:9090
Grafana:       http://localhost:3000 (admin/admin)

# Data Platform
MinIO Console: http://localhost:9002 (minioadmin/minioadmin)
Airflow:       http://localhost:8082 (admin/admin)
Metabase:      http://localhost:3001

# Analytics
ClickHouse:    http://localhost:8123
Analytics UI:  frontend/analytics-dashboard.html
```

### 3. Test Integration

```bash
# Test search with tracing
curl -X POST http://localhost:8001/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":5}'

# View trace in Jaeger
open http://localhost:16686

# Test object storage
curl -X POST http://localhost:8001/api/v1/upload \
  -F "file=@test.txt"

# View in MinIO
open http://localhost:9002
```

---

## 🔒 Security & Authentication

### Keycloak OAuth2 Setup

**1. Create Realm**
```bash
# Access Keycloak
open http://localhost:8080

# Login: admin/admin
# Create realm: "rag-enterprise"
```

**2. Create Client**
```
Client ID: rag-enterprise-api
Client Protocol: openid-connect
Access Type: confidential
Valid Redirect URIs: http://localhost:8001/*
```

**3. Use in API**
```python
from app.core.auth_keycloak import get_current_user, require_role
from fastapi import Depends

@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user": user["preferred_username"]}

@app.get("/admin")
async def admin_route(user: dict = Depends(require_role("admin"))):
    return {"message": "Admin access granted"}
```

### Vault Secret Management

**1. Initialize Vault**
```bash
# Already initialized in dev mode with token: root
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="root"
```

**2. Store Secrets**
```bash
# Via CLI
vault kv put secret/database/postgres \
  username=postgres \
  password=supersecret

# Via Python
from app.core.secrets_vault import get_vault_client

vault = get_vault_client()
vault.create_or_update_secret(
    "database/postgres",
    {"username": "postgres", "password": "supersecret"}
)
```

**3. Read Secrets**
```python
secret = vault.read_secret("database/postgres")
db_password = secret["password"]
```

---

## 📡 Distributed Tracing

### OpenTelemetry + Jaeger

**1. Auto-Instrumentation** (Already configured)
```python
# In app/main.py
from app.core.telemetry import setup_telemetry, instrument_app

# Setup on startup
setup_telemetry(service_name="rag-enterprise", jaeger_host="jaeger")
instrument_app(app)
```

**2. Custom Spans**
```python
from app.core.telemetry import TracingContext

async def my_function(query: str):
    with TracingContext("search_operation", {"query": query}) as ctx:
        # Search logic
        ctx.add_event("search_started")
        results = await search(query)
        ctx.add_event("search_completed", {"count": len(results)})
        return results
```

**3. View Traces**
```bash
# Access Jaeger UI
open http://localhost:16686

# Search for traces
Service: rag-enterprise
Operation: POST /api/v1/search
```

---

## 💾 Object Storage

### MinIO S3-Compatible Storage

**1. Create Bucket**
```python
from app.core.storage_minio import get_minio_client

minio = get_minio_client()
minio.create_bucket("rag-documents")
```

**2. Upload Files**
```python
# Upload file
minio.upload_file(
    bucket_name="rag-documents",
    object_name="user-docs/file.pdf",
    file_path="/path/to/file.pdf",
    content_type="application/pdf"
)

# Upload bytes
minio.upload_bytes(
    bucket_name="rag-documents",
    object_name="data/embeddings.npy",
    data=embedding_bytes
)
```

**3. Presigned URLs**
```python
# Generate download URL (expires in 1 hour)
url = minio.get_presigned_url("rag-documents", "file.pdf", expires=3600)

# Generate upload URL
upload_url = minio.get_presigned_upload_url("rag-documents", "upload.pdf")
```

---

## 🔄 ETL Workflows

### Apache Airflow

**1. Access Airflow**
```bash
open http://localhost:8082
# Login: admin/admin
```

**2. Example DAG** (already created)
```
Location: airflow/dags/rag_etl_pipeline.py
Schedule: Daily @ midnight
Tasks: health_check → extract → transform → [load_qdrant, update_analytics] → notify
```

**3. Create Custom DAG**
```python
# airflow/dags/my_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def my_task():
    print("Running custom task")

dag = DAG(
    'my_pipeline',
    start_date=datetime(2025, 1, 1),
    schedule_interval='@hourly'
)

task = PythonOperator(
    task_id='my_task',
    python_callable=my_task,
    dag=dag
)
```

**4. Trigger Manually**
```bash
# Via UI or CLI
docker exec airflow-webserver airflow dags trigger rag_etl_pipeline
```

---

## 📊 Business Intelligence

### Metabase

**1. Setup**
```bash
open http://localhost:3001
# First-time setup wizard
```

**2. Connect Data Sources**
- PostgreSQL: localhost:15432 / rag_enterprise
- ClickHouse: localhost:8123 / analytics

**3. Create Dashboards**
- Search Analytics (from ClickHouse)
- User Behavior (from PostgreSQL)
- Product Performance (from both)

---

## 🔍 CI/CD Pipeline

### GitHub Actions Workflows

**Automatic on Push**:
1. **CI Pipeline** (.github/workflows/ci.yml)
   - Linting (Black, Ruff, MyPy)
   - Testing (pytest + coverage)
   - Security (Bandit, Safety)
   - Docker build

2. **CD Pipeline** (.github/workflows/cd.yml)
   - Build & push images
   - Deploy to staging (auto)
   - Deploy to production (manual)

3. **Security** (.github/workflows/codeql.yml)
   - CodeQL analysis
   - Dependency scanning

**Manual Deployment**:
```bash
# Via GitHub UI: Actions → CD Pipeline → Run workflow
# Select environment: staging / production
```

---

## ☸️ Kubernetes Deployment

### Production Deployment

**1. Apply Manifests**
```bash
kubectl apply -f k8s/
```

**2. Verify Deployment**
```bash
kubectl get pods
kubectl get hpa  # Horizontal Pod Autoscaler
kubectl get ingress
```

**3. Auto-Scaling in Action**
```bash
# Watch HPA
kubectl get hpa rag-enterprise-api --watch

# Simulate load
kubectl run -it load-test --rm --image=busybox \
  -- /bin/sh -c "while true; do wget -q -O- http://rag-enterprise-api:8001/health/live; done"

# See pods scale up
kubectl get pods --watch
```

---

## 📈 Monitoring & Observability

### Prometheus Metrics

**Custom Metrics**:
```python
from prometheus_client import Counter, Histogram

search_counter = Counter('search_total', 'Total searches')
search_duration = Histogram('search_duration_seconds', 'Search duration')

@search_duration.time()
async def search(query: str):
    search_counter.inc()
    # search logic
```

**Query Metrics**:
```
# Prometheus UI: http://localhost:9090
rate(search_total[5m])  # Searches per second
histogram_quantile(0.95, search_duration_seconds)  # P95 latency
```

### Grafana Dashboards

**Pre-configured**:
- System metrics (CPU, Memory, Disk)
- Application metrics (API requests, errors)
- Database metrics (connections, queries)

**Create Custom**:
```
1. Open http://localhost:3000
2. Create → Dashboard
3. Add panel → Select Prometheus
4. Query: rate(search_total[5m])
5. Save dashboard
```

---

## 🛠️ Development Workflow

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (without Docker)
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v --cov=app

# Format code
black app/ src/
ruff check app/ src/
```

### Pre-commit Checks

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 📚 Documentation

### MkDocs Site

**Build Documentation**:
```bash
cd mkdocs
pip install mkdocs-material
mkdocs serve
# Open http://localhost:8000
```

**Deploy to GitHub Pages**:
```bash
mkdocs gh-deploy
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Services Not Starting**
```bash
# Check logs
docker-compose logs [service-name]

# Restart all
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

**2. Port Conflicts**
```bash
# Check ports in use
lsof -i :8001

# Kill process
kill -9 <PID>
```

**3. Memory Issues**
```bash
# Increase Docker memory
# Docker Desktop → Settings → Resources → Memory: 8GB+

# Check resource usage
docker stats
```

### Health Checks

```bash
# API
curl http://localhost:8001/health/ready

# ClickHouse
curl http://localhost:8123/ping

# Jaeger
curl http://localhost:16686/api/services

# MinIO
curl http://localhost:9002/minio/health/live
```

---

## 📋 Feature Comparison

| Feature | v6.0.0 | v7.0.0 |
|---------|--------|--------|
| Services | 10 | 17 ⭐ |
| OAuth2/SSO | ❌ | ✅ Keycloak ⭐ |
| Secret Management | ❌ | ✅ Vault ⭐ |
| Distributed Tracing | ❌ | ✅ Jaeger ⭐ |
| Object Storage | ❌ | ✅ MinIO ⭐ |
| ETL Workflows | ❌ | ✅ Airflow ⭐ |
| Business Intelligence | ❌ | ✅ Metabase ⭐ |
| CI/CD Pipeline | Basic | Complete ⭐ |
| Documentation | Markdown | MkDocs Site ⭐ |
| Auto-Scaling | K8s HPA | HPA + KEDA ⭐ |
| Total LOC | ~12,000 | ~15,000 ⭐ |

---

## 💰 Total Cost

### Software Costs: **$0/month** ✅

All services are 100% open source:
- Keycloak (Apache 2.0)
- Vault (MPL 2.0)
- Jaeger (Apache 2.0)
- MinIO (AGPL 3.0)
- Airflow (Apache 2.0)
- Metabase (AGPL 3.0)
- All others (various OSS licenses)

### Infrastructure Costs (Examples)

**Self-Hosted**:
- Bare metal: $0 (use existing servers)
- VPS (Hetzner): ~$50/month (8 cores, 32GB RAM)

**Cloud (AWS/GCP/Azure)**:
- 3x t3.large instances: ~$250/month
- Load balancer: ~$20/month
- Storage: ~$50/month
- **Total**: ~$320/month

**Kubernetes (EKS/GKE/AKS)**:
- Control plane: ~$75/month
- 3x worker nodes: ~$250/month
- Load balancer: ~$20/month
- **Total**: ~$345/month

---

## 🎯 Production Checklist

### Before Going Live

- [ ] Set strong passwords (Keycloak, Grafana, MinIO, etc.)
- [ ] Configure Vault with real backend (not dev mode)
- [ ] Set up SSL/TLS (ingress + cert-manager)
- [ ] Configure backup strategy (database, volumes)
- [ ] Set up monitoring alerts (PagerDuty, Slack)
- [ ] Load test system (k6, Locust)
- [ ] Security audit (penetration testing)
- [ ] Disaster recovery plan
- [ ] Documentation review
- [ ] Team training

---

**Version**: v7.0.0
**Status**: Production Ready
**License**: MIT
**Last Updated**: 2025-11-09

**Quick Start**: `docker-compose up -d`
**Full Docs**: [MkDocs Site](http://localhost:8000)
**Support**: GitHub Issues
