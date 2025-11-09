# Deployment Options - From Free to Enterprise

**Complete deployment guide: Streamlit (free) → Cloudflare Workers (paid)**

---

## Table of Contents

1. [Overview](#overview)
2. [Free Options](#free-options)
3. [Mid-Tier Options](#mid-tier-options)
4. [Enterprise Options](#enterprise-options)
5. [Comparison Matrix](#comparison-matrix)
6. [Migration Paths](#migration-paths)

---

## Overview

### Deployment Strategy Matrix

| Tier | Services | Cost | Use Case | Complexity |
|------|---------|------|----------|------------|
| **Free** | Streamlit Cloud, Hugging Face Spaces | $0 | Demo, MVP, Learning | ⭐ Easy |
| **Low-Cost** | Railway, Render, Fly.io | $5-20/mo | Small teams, Prototypes | ⭐⭐ Medium |
| **Mid-Tier** | DigitalOcean, Linode, AWS Lightsail | $20-100/mo | Production, SMB | ⭐⭐⭐ Medium-Hard |
| **Enterprise** | AWS, GCP, Azure, Cloudflare | $100-1000+/mo | Scale, High availability | ⭐⭐⭐⭐ Hard |

---

## Free Options

### 1. Streamlit Cloud (Recommended for Free Tier)

**Best For**: Quick demos, MVPs, non-critical apps

**Specifications**:
- **CPU**: 1 vCPU
- **RAM**: 1GB
- **Storage**: 50GB
- **Bandwidth**: Unlimited
- **Uptime**: Community support (no SLA)
- **Cost**: $0 (Free tier)

**Pros**:
- ✅ Zero configuration
- ✅ Auto-deploy from GitHub
- ✅ Built-in secrets management
- ✅ HTTPS included
- ✅ Perfect for Streamlit apps

**Cons**:
- ❌ Limited resources (1GB RAM)
- ❌ No custom domain on free tier
- ❌ Apps sleep after inactivity
- ❌ Streamlit-only (no FastAPI support directly)

**Setup**:

1. **Create Streamlit App** (`streamlit_app.py`):
```python
import streamlit as st
import requests

st.title("RAG Enterprise Search")

# Use FastAPI backend (deployed elsewhere or local)
API_URL = st.secrets.get("API_URL", "http://localhost:8001")

query = st.text_input("Search products:")

if st.button("Search"):
    response = requests.post(
        f"{API_URL}/api/v1/search/",
        json={"query": query, "top_k": 5}
    )
    results = response.json()

    for result in results:
        st.write(f"**{result['product_name']}**")
        st.write(f"Score: {result['score']:.2f}")
        st.write(f"Material: {result['material']}")
        st.divider()
```

2. **Deploy**:
```bash
# 1. Push to GitHub
git add streamlit_app.py
git commit -m "Add Streamlit app"
git push

# 2. Go to https://share.streamlit.io
# 3. Connect GitHub repo
# 4. Select streamlit_app.py
# 5. Deploy!
```

3. **Add Secrets** (for API URL):
```toml
# .streamlit/secrets.toml (local)
API_URL = "http://localhost:8001"

# In Streamlit Cloud dashboard:
# Settings → Secrets
API_URL = "https://your-api.example.com"
```

**Limitations**:
- Cannot run FastAPI backend directly
- Need separate backend deployment (see below)
- 1GB RAM limit (not enough for Qdrant + Ollama)

---

### 2. Hugging Face Spaces

**Best For**: ML/AI demos, community showcase

**Specifications**:
- **CPU**: 2 vCPU
- **RAM**: 16GB (free tier)
- **Storage**: 50GB
- **GPU**: Available on paid tier
- **Cost**: $0 (Free tier), $0.60/hr (GPU)

**Pros**:
- ✅ More resources than Streamlit (16GB RAM!)
- ✅ Docker support
- ✅ Can run full stack (FastAPI + Qdrant)
- ✅ GPU available
- ✅ Great for AI/ML community

**Cons**:
- ❌ Apps sleep after inactivity
- ❌ Slower cold starts
- ❌ Community support only

**Setup**:

1. **Create Space** on https://huggingface.co/spaces

2. **Add Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 7860

# Run (Hugging Face uses port 7860)
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "7860"]
```

3. **Create `README.md`**:
```yaml
---
title: RAG Enterprise
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# RAG Enterprise Search

Semantic search for packaging products.
```

4. **Push**:
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/rag-enterprise
git push hf main
```

**Limitations**:
- No persistent storage (use external Qdrant Cloud)
- Community tier has lower priority

---

### 3. GitHub Pages (Frontend Only)

**Best For**: Static frontend for API-based apps

**Cost**: $0

**Setup**:
```bash
# Build frontend
cd frontend
# Deploy to gh-pages branch
git subtree push --prefix frontend origin gh-pages
```

**Access**: `https://YOUR_USERNAME.github.io/rag-enterprise/`

---

## Mid-Tier Options

### 4. Railway ($5-20/mo)

**Best For**: Small production apps, startups

**Specifications**:
- **CPU**: Shared vCPU
- **RAM**: 512MB - 8GB
- **Storage**: 100GB
- **Cost**: $5/mo (starter), $0.000231/GB-second

**Pros**:
- ✅ Simple deployment (like Heroku)
- ✅ PostgreSQL, Redis included
- ✅ Auto-scaling
- ✅ Custom domains
- ✅ Good free tier ($5 credit/month)

**Cons**:
- ❌ Can get expensive at scale
- ❌ Limited to certain regions

**Setup**:

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
railway login
```

2. **Deploy**:
```bash
railway init
railway up
```

3. **Add Services**:
```bash
# Add PostgreSQL
railway add --service postgres

# Add Redis
railway add --service redis
```

4. **Environment Variables**:
```bash
railway variables set QDRANT_HOST=qdrant-cloud.example.com
railway variables set OLLAMA_BASE_URL=http://localhost:11434
```

**Estimated Cost**:
- API (512MB RAM): ~$5/mo
- PostgreSQL: $5/mo
- Redis: $3/mo
- **Total**: ~$13/mo

---

### 5. Render ($7-25/mo)

**Best For**: Web apps, APIs, static sites

**Specifications**:
- **CPU**: Shared / 0.5-4 vCPU
- **RAM**: 512MB - 16GB
- **Cost**: $7/mo (starter), $25/mo (standard)

**Pros**:
- ✅ Simple Git-based deployment
- ✅ Free PostgreSQL, Redis
- ✅ Auto-scaling
- ✅ Managed services

**Cons**:
- ❌ Free tier has spin-down (15 min inactivity)
- ❌ Limited customization

**Setup**:

1. **Create `render.yaml`**:
```yaml
services:
  - type: web
    name: rag-enterprise-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.api.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: QDRANT_HOST
        value: qdrant-cloud.example.com

databases:
  - name: postgres
    plan: starter  # Free

  - name: redis
    plan: starter  # Free
```

2. **Deploy**:
- Connect GitHub repo on https://render.com
- Auto-deploys on push

**Estimated Cost**:
- Web service: $7/mo
- PostgreSQL: $0 (free)
- Redis: $0 (free)
- **Total**: $7/mo

---

### 6. Fly.io ($5-30/mo)

**Best For**: Edge computing, global deployment

**Specifications**:
- **CPU**: Shared vCPU
- **RAM**: 256MB - 8GB
- **Regions**: 30+ global regions
- **Cost**: $1.94/mo per 256MB instance

**Pros**:
- ✅ Global edge deployment
- ✅ Low latency worldwide
- ✅ Dockerfile support
- ✅ Good free tier (3 VMs)

**Cons**:
- ❌ More complex than Railway/Render
- ❌ Requires Dockerfile

**Setup**:

1. **Install Fly CLI**:
```bash
curl -L https://fly.io/install.sh | sh
fly auth signup
```

2. **Deploy**:
```bash
fly launch
# Follow prompts
fly deploy
```

3. **Scale**:
```bash
# Add more regions
fly regions add sin syd nrt  # Asia

# Scale RAM
fly scale memory 512
```

**Estimated Cost**:
- 2 instances × 512MB: ~$8/mo
- Postgres: $0 (free tier)
- **Total**: ~$8/mo

---

## Enterprise Options

### 7. DigitalOcean ($20-100/mo)

**Best For**: Production apps, full control

**Specifications**:
- **Droplets**: 1 vCPU, 1GB RAM → 32 vCPU, 192GB RAM
- **Kubernetes**: Managed K8s clusters
- **Databases**: Managed PostgreSQL, Redis
- **Cost**: $6/mo (basic droplet) → $960/mo (high-end)

**Setup**:

1. **Create Droplet**:
```bash
# Install doctl
brew install doctl
doctl auth init

# Create droplet
doctl compute droplet create rag-enterprise \
    --size s-2vcpu-4gb \
    --image ubuntu-22-04-x64 \
    --region sfo3
```

2. **Deploy with Docker Compose**:
```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Clone repo
git clone https://github.com/rkqksk/rag-enterprise.git
cd rag-enterprise

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

3. **Setup Nginx + SSL**:
```bash
# Install Nginx
apt-get install nginx certbot python3-certbot-nginx

# Get SSL cert
certbot --nginx -d api.example.com

# Nginx config
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Estimated Cost**:
- Droplet (2 vCPU, 4GB): $24/mo
- Managed PostgreSQL: $15/mo
- Managed Redis: $15/mo
- Backups: $5/mo
- **Total**: ~$60/mo

---

### 8. AWS (Elastic Beanstalk / ECS) ($50-500+/mo)

**Best For**: Enterprise scale, high availability

**Services**:
- **Elastic Beanstalk**: PaaS (easy)
- **ECS/Fargate**: Container orchestration
- **Lambda**: Serverless functions
- **RDS**: Managed databases
- **ElastiCache**: Managed Redis

**Setup (Elastic Beanstalk)**:

1. **Install EB CLI**:
```bash
pip install awsebcli
eb init
```

2. **Create `Dockerfile`**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Deploy**:
```bash
eb create rag-enterprise-prod
eb deploy
```

**Estimated Cost (Moderate)**:
- EC2 (t3.medium): $30/mo
- RDS PostgreSQL (db.t3.small): $25/mo
- ElastiCache Redis (cache.t3.micro): $12/mo
- Load Balancer: $18/mo
- Data transfer: ~$10/mo
- **Total**: ~$95/mo

**Estimated Cost (High Scale)**:
- EC2 (3× t3.large): $150/mo
- RDS (db.r6g.large): $180/mo
- ElastiCache (cache.r6g.large): $100/mo
- Load Balancer: $18/mo
- Data transfer: ~$50/mo
- **Total**: ~$500/mo

---

### 9. Google Cloud Platform ($50-300/mo)

**Best For**: ML workloads, global scale

**Services**:
- **Cloud Run**: Serverless containers
- **GKE**: Kubernetes
- **Cloud SQL**: PostgreSQL
- **Memorystore**: Redis
- **Vertex AI**: ML platform

**Setup (Cloud Run)**:

1. **Build Docker image**:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/rag-enterprise
```

2. **Deploy**:
```bash
gcloud run deploy rag-enterprise \
    --image gcr.io/PROJECT_ID/rag-enterprise \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2
```

**Estimated Cost**:
- Cloud Run: $20/mo (2 GB RAM, moderate traffic)
- Cloud SQL: $25/mo
- Memorystore: $20/mo
- Storage: $5/mo
- **Total**: ~$70/mo

---

### 10. Cloudflare Workers ($5-30/mo)

**Best For**: Edge computing, API gateway, low-latency

**Specifications**:
- **Workers**: Serverless JavaScript/Wasm
- **KV**: Edge key-value storage
- **D1**: SQLite at edge
- **Cost**: $5/mo (10M requests)

**Note**: Cannot run full FastAPI, but perfect for:
- API gateway / routing
- Caching layer
- Authentication
- Static frontend

**Setup**:

1. **Create Worker** (`worker.js`):
```javascript
// API gateway
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Cache layer
    const cache = caches.default;
    let response = await cache.match(request);

    if (!response) {
      // Forward to actual API (on DigitalOcean, AWS, etc.)
      response = await fetch(
        `https://api-backend.example.com${url.pathname}`,
        {
          method: request.method,
          headers: request.headers,
          body: request.body
        }
      );

      // Cache for 1 hour
      response = new Response(response.body, response);
      response.headers.set("Cache-Control", "s-maxage=3600");
      await cache.put(request, response.clone());
    }

    return response;
  }
};
```

2. **Deploy**:
```bash
npm install -g wrangler
wrangler login
wrangler publish
```

**Use Case**: Cloudflare Workers + Backend (AWS/DO)
- Workers: API gateway, caching, edge logic
- Backend: FastAPI + Qdrant + Ollama (DigitalOcean)

**Estimated Cost**:
- Cloudflare Workers: $5/mo
- Backend (DigitalOcean): $60/mo
- **Total**: $65/mo (with global edge caching!)

---

## Comparison Matrix

### Feature Comparison

| Feature | Streamlit Cloud | Railway | Render | Fly.io | DigitalOcean | AWS | Cloudflare |
|---------|----------------|---------|--------|--------|--------------|-----|------------|
| **Cost** | $0 | $5-20 | $7-25 | $5-30 | $20-100 | $50-500+ | $5-30 |
| **RAM** | 1GB | 512MB-8GB | 512MB-16GB | 256MB-8GB | 1GB-192GB | Unlimited | N/A (edge) |
| **GPU** | ❌ | ❌ | ❌ | ❌ | ✅ (extra $) | ✅ | ❌ |
| **Docker** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ (Wasm) |
| **Auto-Scale** | ❌ | ✅ | ✅ | ✅ | ❌ (manual) | ✅ | ✅ |
| **Global CDN** | ❌ | ❌ | ✅ | ✅ | ✅ (extra $) | ✅ | ✅ |
| **Uptime SLA** | None | 99.9% | 99.95% | 99.95% | 99.99% | 99.99% | 100% |
| **Setup Time** | 5 min | 10 min | 10 min | 20 min | 30 min | 60 min | 30 min |

---

## Migration Paths

### Path 1: Free → Low-Cost → Enterprise

```
Phase 1: MVP (Free)
  - Frontend: Streamlit Cloud
  - Backend API: Hugging Face Spaces
  - Vector DB: Qdrant Cloud (free tier)
  - LLM: Ollama (local dev only)
  → Cost: $0

Phase 2: Beta (Low-Cost)
  - Frontend: Render static site ($0)
  - Backend: Railway ($13/mo)
  - Vector DB: Qdrant Cloud (1GB, $25/mo)
  - LLM: Ollama on Railway
  → Cost: $38/mo

Phase 3: Production (Enterprise)
  - Frontend: Cloudflare Pages ($0)
  - Backend: DigitalOcean ($60/mo)
  - Vector DB: Self-hosted Qdrant
  - LLM: Ollama + GPU ($20/mo)
  → Cost: $80/mo

Phase 4: Scale (Enterprise+)
  - Frontend: Cloudflare Workers ($5/mo)
  - Backend: AWS ECS ($150/mo)
  - Vector DB: Managed Qdrant
  - LLM: NexaAI + Ollama (GPU)
  → Cost: $300+/mo
```

---

## Recommended Deployment

### For This Project (RAG Enterprise)

**Recommended**: Railway (Beta) → DigitalOcean (Production)

**Why**:
1. **Not Streamlit-compatible**: FastAPI backend needs separate deployment
2. **Resource needs**: Qdrant + Ollama need 4GB+ RAM
3. **Cost-effective**: Railway $13/mo is perfect for beta testing
4. **Easy migration**: Railway → DigitalOcean is straightforward

**Step-by-Step**:

```bash
# 1. Deploy to Railway (Beta)
railway login
railway init
railway up

# 2. Add Qdrant (external)
# → Use Qdrant Cloud free tier

# 3. Test with users
# → Get feedback, iterate

# 4. When ready for production:
# → Migrate to DigitalOcean droplet
# → Self-host Qdrant
# → Setup CI/CD with GitHub Actions

# 5. Add Cloudflare in front
# → For caching and DDoS protection
```

---

## Quick Start Templates

### 1. Railway Deployment

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Create project
railway init

# 4. Deploy
railway up

# 5. Set environment variables
railway variables set QDRANT_HOST=your-qdrant.cloud
railway variables set OLLAMA_BASE_URL=http://localhost:11434

# 6. Done!
railway open
```

### 2. DigitalOcean Deployment

```bash
# 1. Create droplet
doctl compute droplet create rag-enterprise \
    --size s-2vcpu-4gb \
    --image ubuntu-22-04-x64 \
    --region sfo3

# 2. SSH and setup
ssh root@DROPLET_IP
git clone https://github.com/rkqksk/rag-enterprise.git
cd rag-enterprise
./scripts/deploy-production.sh

# 3. Setup domain + SSL
certbot --nginx -d api.example.com

# 4. Done!
curl https://api.example.com/health
```

---

## Best Practices

1. **Start Small**: Free tier → paid tier → enterprise
2. **Separate Services**: Frontend (static) + Backend (API) + DB
3. **Use Managed Services**: PostgreSQL, Redis (saves time)
4. **Monitor Costs**: Set billing alerts
5. **Plan for Scale**: Design for horizontal scaling from day 1

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
