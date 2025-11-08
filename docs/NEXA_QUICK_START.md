# NexaAI SDK - Quick Start Guide

완벽한 RAG 시스템을 5분 안에 시작하세요!

## 📋 Prerequisites

- **OS**: Linux (x86_64) or macOS
- **Docker**: v24.0+
- **Python**: 3.11+
- **Disk Space**: ~10GB (for models)
- **RAM**: 8GB+ recommended (16GB ideal)

## 🚀 Quick Start (5 minutes)

### Option 1: One-Command Start

```bash
# Clone and start
git clone <your-repo-url>
cd rag-enterprise

# Start everything
./scripts/start-nexa.sh development
```

That's it! 🎉

### Option 2: Manual Setup

#### Step 1: Install NexaAI CLI

```bash
# Linux
curl -fsSL https://github.com/NexaAI/nexa-sdk/releases/latest/download/nexa-cli_linux_x86_64.sh -o install.sh
chmod +x install.sh
./install.sh

# Verify
nexa --version
```

#### Step 2: Pull Models

```bash
# Text generation (fast)
nexa pull NexaAI/Qwen3-1.7B-GGUF

# Vision-language (image analysis)
nexa pull NexaAI/Qwen3-VL-4B-Instruct-GGUF

# Embeddings
nexa pull NexaAI/EmbeddingGemma-GGUF

# Verify
nexa list
```

#### Step 3: Start NexaAI Server

```bash
# Start server
nexa serve --host 0.0.0.0:8080

# Server will be available at http://localhost:8080
```

#### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.nexa.example .env.nexa

# Edit if needed (defaults should work)
nano .env.nexa
```

#### Step 5: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
pip install -r requirements-nexa.txt
```

#### Step 6: Start Services

```bash
# Start Docker services
docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up -d

# Wait for services to start (~30s)
sleep 30
```

#### Step 7: Verify

```bash
# Check all services
curl http://localhost:8080/health       # NexaAI
curl http://localhost:8001/health/ready # API
curl http://localhost:6333/dashboard    # Qdrant
```

## 🎯 Quick Test

### Test 1: Simple Search

```bash
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"50ml PET 용기","top_k":5}'
```

**Expected**: NexaAI's Qwen3-1.7B (fast model) handles this simple query

### Test 2: Complex Query

```bash
curl -X POST http://localhost:8001/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "100ml 투명 PET 용기와 PP 용기의 차이점을 분석하고 각각의 장단점을 비교해줘",
    "session_id": "test-123"
  }'
```

**Expected**: Ollama's qwen2.5:7b (quality model) handles this complex query

### Test 3: Image Analysis

```bash
# Prepare an image
wget https://example.com/product.jpg -O /tmp/product.jpg

# Analyze image (requires NexaAI Vision model)
curl -X POST http://localhost:8001/api/v1/image/analyze \
  -F "file=@/tmp/product.jpg" \
  -F "prompt=Describe this product in detail"
```

**Expected**: NexaAI's Qwen3-VL-4B-Instruct (vision model) analyzes the image

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **NexaAI Server** | http://localhost:8080 | OpenAI-compatible API |
| **API** | http://localhost:8001 | FastAPI backend |
| **API Docs** | http://localhost:8001/api/v1/docs | Swagger UI |
| **Qdrant UI** | http://localhost:6333/dashboard | Vector database |
| **Frontend** | http://localhost:8000 | Chat interface |

## 📊 Service Status

```bash
# Check NexaAI
curl http://localhost:8080/health

# Check API health
curl http://localhost:8001/health/ready

# Check engine status
curl http://localhost:8001/api/v1/debug/llm/status

# Response example:
{
  "unified": true,
  "engines": {
    "nexa": {"healthy": true},
    "ollama": {"healthy": true}
  },
  "stats": {
    "nexa_requests": 42,
    "ollama_requests": 15,
    "errors": 0
  }
}
```

## 🔧 Configuration

### Key Environment Variables

```bash
# .env.nexa

# NexaAI Settings
NEXA_ENABLED=true
NEXA_BASE_URL=http://localhost:8080/v1
NEXA_DEFAULT_MODEL=Qwen3-1.7B
NEXA_VISION_MODEL=Qwen3-VL-4B-Instruct

# Model Router
MODEL_ROUTER_ENABLED=true
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3    # Below → simple model
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7   # Above → complex model

# Engine Availability
ENABLE_NEXA=true
ENABLE_OLLAMA=true
```

### Routing Logic

| Query Type | Complexity Score | Engine | Model |
|------------|------------------|--------|-------|
| Simple search | < 0.3 | NexaAI | Qwen3-1.7B |
| Medium complexity | 0.3 - 0.7 | NexaAI | Qwen3-VL-4B |
| Complex reasoning | > 0.7 | Ollama | qwen2.5:7b |
| Image analysis | Any | NexaAI | Qwen3-VL-4B |

## 🐛 Troubleshooting

### NexaAI server not starting

```bash
# Check if port is in use
lsof -i :8080

# Check logs
tail -f logs/nexa-server.log

# Restart server
pkill nexa
nexa serve --host 0.0.0.0:8080
```

### Models not found

```bash
# List cached models
nexa list

# Re-download if missing
nexa pull NexaAI/Qwen3-1.7B-GGUF
```

### Docker services not healthy

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f api
docker-compose logs -f qdrant

# Restart services
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up -d
```

### API errors

```bash
# Check API logs
docker-compose logs -f api

# Check debug endpoints
curl http://localhost:8001/api/v1/debug/performance/summary

# Check LLM engine status
curl http://localhost:8001/api/v1/debug/llm/status
```

## 📈 Performance Tuning

### Fast Responses (< 500ms)

```bash
# In .env.nexa
MODEL_ROUTER_SIMPLE_THRESHOLD=0.5  # Route more queries to fast model
ENABLE_NEXA=true
ENABLE_OLLAMA=false                # Disable slow model
```

### High Quality

```bash
# In .env.nexa
MODEL_ROUTER_COMPLEX_THRESHOLD=0.3  # Route more queries to quality model
ENABLE_NEXA=true
ENABLE_OLLAMA=true
```

### Vision-Only

```bash
# In .env.nexa
NEXA_DEFAULT_MODEL=Qwen3-VL-4B-Instruct  # Use vision model by default
```

## 🛑 Stop Services

```bash
# Stop all services
./scripts/stop-nexa.sh

# Or manually
docker-compose down
pkill nexa
```

## 📚 Next Steps

1. **Explore API**: http://localhost:8001/api/v1/docs
2. **Read Integration Plan**: `docs/NEXA_SDK_INTEGRATION_PLAN.md`
3. **Deploy to Cloudflare**: See deployment section in integration plan
4. **Set up CI/CD**: GitHub Actions workflows included

## 🆘 Getting Help

- **Documentation**: `docs/NEXA_SDK_INTEGRATION_PLAN.md`
- **API Reference**: http://localhost:8001/api/v1/docs
- **Logs**: `logs/nexa-server.log`, `docker-compose logs`
- **Issues**: Create an issue on GitHub

---

**Quick Start Guide** | **Version 1.0** | **Last Updated: 2025-11-07**
