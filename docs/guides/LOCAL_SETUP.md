# Local Setup Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Purpose**: Complete guide for cloning and setting up RAG Enterprise locally

---

## 🎯 Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux, macOS, Windows (WSL2) | Ubuntu 22.04+ |
| **RAM** | 8 GB | 16 GB+ |
| **Storage** | 20 GB free | 50 GB+ |
| **CPU** | 4 cores | 8 cores+ |
| **GPU** | None (optional) | NVIDIA with 4GB+ VRAM |

### Software Dependencies

- **Python**: 3.11+ (required)
- **Docker**: 20.10+ (required)
- **Docker Compose**: 2.0+ (required)
- **Git**: 2.30+ (required)
- **Node.js**: 18+ (optional, for MCP servers)

---

## 📦 Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url> rag-enterprise
cd rag-enterprise

# Verify branch
git branch
# Expected: claude/nex-sdk-rag-implementation-011CUuS3rxhmrLnmJGCFrM19
```

---

## 🔧 Step 2: Environment Setup

### Copy Environment Template

```bash
cp .env.example .env
```

### Configure Environment Variables

Edit `.env` and update the following:

```bash
# === Core Settings ===
API_PORT=8001
API_HOST=0.0.0.0

# === Database Settings ===
QDRANT_HOST=qdrant
QDRANT_PORT=6333
REDIS_HOST=redis
REDIS_PORT=6379
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your-secure-password-here  # CHANGE THIS

# === LLM Settings ===
# NexaAI (optional - leave disabled to use Ollama only)
NEXA_ENABLED=false
NEXA_BASE_URL=http://localhost:8080/v1

# Ollama (required)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b

# === Model Router ===
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7

# === JWT & Security ===
JWT_SECRET_KEY=your-random-secret-key-here  # CHANGE THIS (use: openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# === Stripe (optional - for billing features) ===
STRIPE_SECRET_KEY=sk_test_...  # Leave empty to disable billing
STRIPE_WEBHOOK_SECRET=whsec_...

# === Debug (optional) ===
DEBUG_ENABLED=true
DEBUG_PROFILE_REQUESTS=false
```

### Generate Secure Secrets

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate PostgreSQL password
openssl rand -base64 32
```

---

## 🐳 Step 3: Start Services

### Option A: Quick Start (Recommended)

```bash
# Deploy all services with one command
./scripts/deploy-optimized.sh development

# Wait for services to start (2-3 minutes)
```

### Option B: Manual Docker Start

```bash
# Start Docker services
docker-compose up -d

# Wait for services to be ready
docker-compose ps

# Expected services:
# - api
# - qdrant
# - redis
# - postgres
# - ollama
```

### Verify Services

```bash
# Check API health
curl http://localhost:8001/health/ready

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "qdrant": "connected",
#     "redis": "connected",
#     "postgres": "connected",
#     "ollama": "connected"
#   }
# }

# Check Qdrant
curl http://localhost:6333/health

# Check Redis
docker exec redis redis-cli ping
# Expected: PONG

# Check PostgreSQL
docker exec postgres pg_isready
# Expected: /var/run/postgresql:5432 - accepting connections
```

---

## 🧪 Step 4: Run Tests

```bash
# Install Python dependencies (if not using Docker)
pip install -r requirements.txt

# Run all tests
./scripts/test-optimized.sh

# Or manually:
pytest tests/ -v --cov=src --cov=app --cov-report=html

# Expected: 122+ tests passing
```

---

## 🌐 Step 5: Access Applications

### API Server

- **URL**: http://localhost:8001
- **Docs**: http://localhost:8001/api/v1/docs (Swagger UI)
- **Health**: http://localhost:8001/health/ready

### Vector Database (Qdrant)

- **Dashboard**: http://localhost:6333/dashboard
- **API**: http://localhost:6333

### Frontend (Chat Interface)

```bash
# Start simple HTTP server
cd frontend
python3 -m http.server 8080

# Access at: http://localhost:8080/chat.html
```

---

## 🔍 Step 6: Verify Installation

### Test Search API

```bash
curl -X POST http://localhost:8001/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "50ml PET 용기",
    "top_k": 5
  }'

# Expected: JSON response with search results
```

### Test Chat API

```bash
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "PET 용기의 특징을 알려줘",
    "user_id": "test-user"
  }'

# Expected: JSON response with LLM-generated answer
```

---

## 🛠️ Step 7: Development Setup (Optional)

### Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools
```

### IDE Setup

#### VS Code

```bash
# Recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
```

#### PyCharm

1. Open project directory
2. Set Python interpreter to `venv/bin/python`
3. Mark `src/` and `app/` as source roots

---

## 🚀 Step 8: Optional Features

### Enable NexaAI (Fast LLM)

```bash
# Install NexaAI SDK
pip install nexaai

# Start NexaAI server
nexa server start

# Update .env
NEXA_ENABLED=true
NEXA_BASE_URL=http://localhost:8080/v1

# Restart API
docker-compose restart api
```

### Enable Billing (Stripe)

```bash
# Get Stripe test keys at: https://dashboard.stripe.com/test/apikeys

# Update .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Restart API
docker-compose restart api
```

### Enable Monitoring (Prometheus + Grafana)

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana: http://localhost:3000
# Default login: admin / admin
```

---

## 📊 System Status Check

```bash
# Check all services
./scripts/health-check.sh

# Or manually:
docker-compose ps
docker-compose logs -f api

# Performance check
curl http://localhost:8001/api/v1/debug/performance/summary
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Full reset
docker-compose down -v
docker system prune -af
./scripts/deploy-optimized.sh development
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>

# Or change port in .env
API_PORT=8002
```

### Ollama Model Not Found

```bash
# Pull model manually
docker exec -it ollama ollama pull qwen2.5:7b

# Verify
docker exec -it ollama ollama list
```

### Tests Failing

```bash
# Check Python version
python --version
# Required: 3.11+

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear pytest cache
rm -rf .pytest_cache
pytest --cache-clear
```

---

## 🔄 Updating Project

```bash
# Pull latest changes
git pull origin <branch-name>

# Update dependencies
pip install -r requirements.txt

# Rebuild Docker images
docker-compose build

# Restart services
docker-compose down
docker-compose up -d
```

---

## 🧹 Cleanup

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Clean Docker Resources

```bash
# Remove unused images
docker image prune -a

# Remove all unused resources
docker system prune -af --volumes
```

---

## 📚 Next Steps

1. **Read Documentation**:
   - `CLAUDE.md` - Quick reference for Claude Code
   - `docs/DEPLOYMENT_GUIDE.md` - Production deployment
   - `docs/OPEN_SOURCE_ARCHITECTURE.md` - Architecture overview

2. **Explore Features**:
   - RAG search: `/api/v1/search`
   - Chat interface: `frontend/chat.html`
   - API docs: `http://localhost:8001/api/v1/docs`

3. **Development**:
   - Create sub-agents: `.claude/agents/`
   - Add skills: `.claude/skills/`
   - Run tests: `pytest tests/`

---

## 🆘 Getting Help

- **Documentation**: `docs/` folder
- **Issues**: Create GitHub issue
- **Debugging**: Enable `DEBUG_ENABLED=true` in `.env`
- **Logs**: `docker-compose logs -f api`

---

**Version**: v5.7.1
**Architecture**: 100% Open-Source
**Cost**: $0/month (software) + infrastructure costs
**Status**: ✅ Production-Ready

---

**Quick Commands**:

```bash
# Start
./scripts/deploy-optimized.sh development

# Test
./scripts/test-optimized.sh

# Restart
./scripts/restart-all.sh

# Stop
docker-compose down
```
