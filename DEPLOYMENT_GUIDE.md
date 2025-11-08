# RAG Enterprise - Complete Deployment Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-07

---

## 🎯 Deployment Options

### 1️⃣ **Local Development** (localhost)
### 2️⃣ **Self-Hosted Production** (Docker + Kubernetes)
### 3️⃣ **Serverless Edge** (Cloudflare Workers + Pages)
### 4️⃣ **Hybrid** (Edge + Origin)

---

## 1️⃣ Local Development

### Quick Start (5 minutes)

```bash
# One command start
./scripts/start-nexa.sh development

# Access services
# - API: http://localhost:8001
# - Frontend: http://localhost:3000
# - Admin: http://localhost:3000/admin
```

### Manual Setup

```bash
# 1. Install NexaAI CLI
curl -fsSL https://github.com/NexaAI/nexa-sdk/releases/latest/download/nexa-cli_linux_x86_64.sh -o install.sh
chmod +x install.sh && ./install.sh

# 2. Pull models
nexa pull NexaAI/Qwen3-1.7B-GGUF
nexa pull NexaAI/Qwen3-VL-4B-Instruct-GGUF
nexa pull NexaAI/EmbeddingGemma-GGUF

# 3. Start NexaAI server
nexa serve --host 0.0.0.0:8080 &

# 4. Configure environment
cp .env.nexa.example .env.nexa

# 5. Start Docker services
docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up -d

# 6. Start frontend
cd frontend-next
npm install && npm run dev
```

### Test

```bash
# Run comprehensive tests
./scripts/test-all.sh

# Test specific endpoint
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'
```

---

## 2️⃣ Self-Hosted Production

### Option A: Docker Compose

```bash
# Production deployment
./scripts/start-nexa.sh production

# Services will run on:
# - API: http://your-domain.com:8001
# - NexaAI: http://your-domain.com:8080
# - Qdrant: http://your-domain.com:6333
```

### Option B: Kubernetes

#### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3+

#### Deploy

```bash
# 1. Create namespace
kubectl create namespace rag-enterprise

# 2. Create secrets
kubectl create secret generic rag-secrets \
  --from-literal=postgres-password=your-password \
  --namespace=rag-enterprise

# 3. Deploy services
kubectl apply -f k8s/ --namespace=rag-enterprise

# 4. Check status
kubectl get pods -n rag-enterprise

# Expected output:
# NAME                        READY   STATUS    RESTARTS   AGE
# rag-api-xxxxx              1/1     Running   0          2m
# rag-qdrant-xxxxx           1/1     Running   0          2m
# rag-redis-xxxxx            1/1     Running   0          2m
# rag-postgres-xxxxx         1/1     Running   0          2m
```

#### Scale

```bash
# Horizontal scaling
kubectl scale deployment rag-api --replicas=5 -n rag-enterprise

# Auto-scaling
kubectl autoscale deployment rag-api \
  --min=3 --max=10 \
  --cpu-percent=70 \
  -n rag-enterprise
```

---

## 3️⃣ Serverless Edge (Cloudflare)

### Setup Cloudflare Workers

#### 1. Create Vectorize Index

```bash
npx wrangler vectorize create rag-products \
  --dimensions=384 \
  --metric=cosine
```

#### 2. Create D1 Database

```bash
# Create database
npx wrangler d1 create rag-metadata

# Execute schema
npx wrangler d1 execute rag-metadata \
  --file=./workers/schema.sql
```

#### 3. Create KV Namespace

```bash
npx wrangler kv:namespace create "rag-cache"
```

#### 4. Update wrangler.toml

```toml
# workers/api/wrangler.toml

account_id = "YOUR_ACCOUNT_ID"

[[vectorize]]
binding = "VECTORIZE"
index_name = "rag-products"

[[d1_databases]]
binding = "DB"
database_id = "YOUR_D1_ID"

[[kv_namespaces]]
binding = "KV"
id = "YOUR_KV_ID"
```

#### 5. Deploy Workers API

```bash
cd workers/api
npm install
npx wrangler deploy
```

### Setup Cloudflare Pages

#### 1. Build Frontend

```bash
cd frontend-next
npm install
npm run build
```

#### 2. Deploy to Pages

```bash
npx wrangler pages deploy ./out \
  --project-name=rag-enterprise
```

### Configure Custom Domain

```bash
# Add custom domain
npx wrangler pages domain add api.your-domain.com

# DNS will be configured automatically
```

---

## 4️⃣ Hybrid Deployment

### Edge + Origin Architecture

```
User Request
    ↓
Cloudflare Workers (Edge - Fast queries)
    ├─→ Workers AI (Simple queries, < 0.3 complexity)
    └─→ Origin Server (Complex queries, > 0.3 complexity)
        ├─→ NexaAI (Medium, 0.3-0.7)
        └─→ Ollama (Complex, > 0.7)
```

### Configuration

```typescript
// workers/api/src/hybrid.ts

export async function route(request: Request, env: Env) {
  const { query } = await request.json()

  // Analyze complexity
  const complexity = analyzeComplexity(query)

  if (complexity < 0.3) {
    // Handle at edge with Workers AI
    return await handleEdge(query, env)
  } else {
    // Forward to origin
    return await fetch('https://origin.your-domain.com/api/v1/search/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    })
  }
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
# .env.production

# NexaAI
NEXA_ENABLED=true
NEXA_BASE_URL=http://nexa-server:8080/v1

# Ollama
OLLAMA_BASE_URL=http://ollama-server:11434

# Qdrant
QDRANT_HOST=qdrant-server
QDRANT_PORT=6333

# Redis
REDIS_HOST=redis-server
REDIS_PORT=6379

# PostgreSQL
POSTGRES_HOST=postgres-server
POSTGRES_PORT=5432
POSTGRES_DB=rag
POSTGRES_USER=rag
POSTGRES_PASSWORD=<from-secret>

# API
API_HOST=0.0.0.0
API_PORT=8001

# Router
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7
```

---

## 📊 Monitoring

### Prometheus Metrics

```yaml
# prometheus.yml

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rag-api'
    static_configs:
      - targets: ['rag-api:8001']

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
```

### Grafana Dashboards

```bash
# Import dashboard
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboard.json
```

### Key Metrics

- **Response Time**: p50, p95, p99
- **Request Rate**: requests/second
- **Error Rate**: errors/total requests
- **Model Usage**: NexaAI vs Ollama distribution
- **Cache Hit Rate**: Redis cache performance

---

## 🔒 Security

### SSL/TLS

```bash
# Let's Encrypt (certbot)
sudo certbot --nginx -d api.your-domain.com

# Or use Cloudflare SSL (automatic)
```

### API Keys

```bash
# Generate API key
openssl rand -hex 32

# Add to environment
export API_KEY=your-generated-key

# Use in requests
curl -H "Authorization: Bearer $API_KEY" \
  http://api.your-domain.com/api/v1/search/
```

---

## 🚀 CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy Workers
        run: |
          cd workers/api
          npx wrangler deploy

      - name: Deploy Pages
        run: |
          cd frontend-next
          npm run build
          npx wrangler pages deploy ./out

      - name: Deploy Kubernetes
        run: |
          kubectl apply -f k8s/
```

---

## 📈 Performance Optimization

### Caching Strategy

```python
# Multi-level caching
L1: Redis (hot data, < 1s TTL)
L2: Cloudflare KV (warm data, 1h TTL)
L3: Origin database (cold data)
```

### CDN Configuration

```javascript
// Cloudflare cache rules
{
  "cache": {
    "/api/v1/search/*": {
      "edge_ttl": 300,  // 5 minutes
      "browser_ttl": 60
    }
  }
}
```

---

## 🆘 Troubleshooting

### Common Issues

#### 1. NexaAI not responding

```bash
# Check process
ps aux | grep nexa

# Check logs
tail -f logs/nexa-server.log

# Restart
pkill nexa
nexa serve --host 0.0.0.0:8080
```

#### 2. Qdrant connection failed

```bash
# Check Docker container
docker ps | grep qdrant

# Check logs
docker logs rag-qdrant

# Restart
docker restart rag-qdrant
```

#### 3. High latency

```bash
# Check routing stats
curl http://localhost:8001/api/v1/admin/stats

# Adjust thresholds
curl -X POST http://localhost:8001/api/v1/admin/router/config \
  -d '{"simple_threshold":0.5}'
```

---

## 📝 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (`./scripts/test-all.sh`)
- [ ] Environment variables configured
- [ ] Secrets created (API keys, passwords)
- [ ] SSL certificates ready
- [ ] Monitoring configured

### Deployment

- [ ] Build Docker images
- [ ] Push to registry
- [ ] Deploy to target environment
- [ ] Run health checks
- [ ] Verify routing logic

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Check performance metrics
- [ ] Test all endpoints
- [ ] Verify auto-scaling
- [ ] Update documentation

---

**Deployment Guide** | **Version 1.0** | **Updated: 2025-11-07**
