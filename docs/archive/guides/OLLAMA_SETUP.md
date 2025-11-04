# Ollama Setup Guide

Complete guide for installing and configuring Ollama for RAG Enterprise development and production.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Model Management](#model-management)
- [Configuration](#configuration)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

---

## Quick Start

**5-Minute Setup:**

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull recommended model (4.7GB download)
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Verify installation
curl http://localhost:11434/api/tags

# 4. Configure RAG Enterprise
echo "OLLAMA_URL=http://localhost:11434" >> .env
echo "OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M" >> .env

# 5. Start RAG Enterprise
docker-compose up -d
```

---

## Installation

### Development vs Production Configuration

RAG Enterprise supports two Ollama deployment strategies:

**Development: Local Ollama App (Recommended)**
- Faster iteration (no Docker overhead)
- Easier debugging (direct access to logs and models)
- Resource efficient (single Ollama instance)
- Simple model management (`ollama pull`, `ollama list`)

**Production: Docker Ollama**
- Consistent deployment (containerized environment)
- Resource isolation (dedicated container resources)
- Scalability (easy horizontal scaling)

---

## Local Ollama Setup (Development)

### 1. Installation

**macOS (Homebrew)**:
```bash
brew install ollama
```

**Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows**:
Download from https://ollama.ai/download

### 2. Start Ollama Service

**macOS/Linux**:
```bash
# Start service
ollama serve

# Verify running
curl http://localhost:11434/api/tags
```

**macOS (Background Service)**:
```bash
# Start with launchd
brew services start ollama

# Check status
brew services list | grep ollama
```

### 3. Pull Required Models

```bash
# Recommended model (balanced performance/quality)
ollama pull qwen2.5:7b-instruct-q4_K_M

# Fast model for simple queries
ollama pull qwen2.5:3b

# List installed models
ollama list
```

**Expected Output**:
```
NAME                          ID              SIZE    MODIFIED
qwen2.5:7b-instruct-q4_K_M    845dbda0ea48    4.7 GB  2 hours ago
qwen2.5:3b                    357c53fb659c    1.9 GB  3 hours ago
```

### 4. Configure RAG Enterprise

**Option A: Use Default Configuration (Recommended)**

No configuration needed. System defaults to `http://localhost:11434`.

**Option B: Explicit Configuration**

Create/update `.env`:
```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
```

### 5. Verify Setup

```bash
# Test Ollama API
curl http://localhost:11434/api/tags

# Test model inference
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b-instruct-q4_K_M",
  "prompt": "Hello",
  "stream": false
}'

# Test RAG Enterprise integration
python3 -c "
import os
os.environ['POSTGRES_PASSWORD'] = 'test'
from app.core.dependencies import get_config
config = get_config()
print(f'Ollama URL: {config.ollama_url}')
print(f'Ollama Model: {config.ollama_model}')
"
```

---

## Docker Ollama Setup (Production)

### 1. Enable Docker Ollama Service

**Option A: Use Default docker-compose.yml**

Uncomment Ollama service in `docker-compose.yml` (if disabled).

**Option B: Create Production Overlay**

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: rag-ollama
    restart: unless-stopped

    ports:
      - "11434:11434"

    volumes:
      - ollama_data:/root/.ollama

    networks:
      rag_network:
        ipv4_address: 172.28.0.6

    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

volumes:
  ollama_data:
```

### 2. Configure Environment

Update `.env`:
```bash
OLLAMA_URL=http://172.28.0.6:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
```

### 3. Pull Models in Container

```bash
# Start Ollama container
docker-compose up -d ollama

# Pull models inside container
docker exec -it rag-ollama ollama pull qwen2.5:7b-instruct-q4_K_M

# Verify models
docker exec -it rag-ollama ollama list
```

### 4. Verify Connectivity

```bash
# From host
curl http://172.28.0.6:11434/api/tags

# From FastAPI container
docker exec -it rag-api curl http://172.28.0.6:11434/api/tags
```

---

## Switching Between Configurations

### Development → Production

1. Update `.env`:
```bash
OLLAMA_URL=http://172.28.0.6:11434
```

2. Enable Docker Ollama:
```bash
docker-compose up -d ollama
```

3. Restart FastAPI:
```bash
docker-compose restart api
```

### Production → Development

1. Stop Docker Ollama:
```bash
docker-compose stop ollama
```

2. Update `.env`:
```bash
OLLAMA_URL=http://localhost:11434
```

3. Ensure local Ollama running:
```bash
brew services start ollama  # macOS
# or
ollama serve  # Manual start
```

4. Restart FastAPI:
```bash
uvicorn app.api.main:app --reload
```

---

## Troubleshooting

### Issue: "Connection refused" to localhost:11434

**Cause**: Local Ollama service not running

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
brew services start ollama  # macOS background
# or
ollama serve  # Manual start (foreground)
```

### Issue: Model not found

**Cause**: Model not pulled or incorrect model name

**Solution**:
```bash
# List available models
ollama list

# Pull missing model
ollama pull qwen2.5:7b-instruct-q4_K_M

# Verify in RAG Enterprise config
grep OLLAMA_MODEL .env
```

### Issue: Docker Ollama not accessible from FastAPI

**Cause**: Network configuration or service not started

**Solution**:
```bash
# Check Ollama container status
docker-compose ps ollama

# Check network connectivity
docker exec -it rag-api ping 172.28.0.6

# Verify Ollama service
docker exec -it rag-api curl http://172.28.0.6:11434/api/tags

# Check logs
docker-compose logs ollama
```

### Issue: Slow responses from Ollama

**Possible Causes**:
1. Model too large for available RAM
2. CPU-only inference (no GPU acceleration)
3. Concurrent request overload

**Solutions**:
```bash
# Use smaller model
ollama pull qwen2.5:3b

# Check resource usage
docker stats rag-ollama  # Docker
top -pid $(pgrep ollama)  # Local

# Reduce concurrent requests in .env
OLLAMA_NUM_PARALLEL=1
```

---

## Model Recommendations

### Development

**Fast Iteration**:
- Model: `qwen2.5:3b`
- Size: 1.9GB
- Speed: ~50 tokens/sec (CPU)
- Use Case: Testing, quick prototyping

**Balanced**:
- Model: `qwen2.5:7b-instruct-q4_K_M`
- Size: 4.7GB
- Speed: ~20 tokens/sec (CPU)
- Use Case: Standard development, realistic testing

### Production

**High Quality**:
- Model: `qwen2.5:14b-instruct-q4_K_M`
- Size: ~9GB
- Speed: ~10 tokens/sec (CPU)
- Use Case: Production workloads requiring high accuracy

**GPU-Accelerated**:
- Model: `qwen2.5:7b` (full precision)
- Size: ~15GB
- Speed: ~100+ tokens/sec (GPU)
- Use Case: High-throughput production with GPU

---

## Performance Tuning

### Local Ollama

**Optimize for Speed**:
```bash
# Set environment variables before starting Ollama
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_FLASH_ATTENTION=1

ollama serve
```

**Optimize for Memory**:
```bash
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1

ollama serve
```

### Docker Ollama

Update `docker-compose.yml`:
```yaml
services:
  ollama:
    environment:
      OLLAMA_NUM_PARALLEL: 4
      OLLAMA_MAX_LOADED_MODELS: 2
      OLLAMA_FLASH_ATTENTION: 1
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
```

---

## Resource Requirements

### Minimum (Development)
- **RAM**: 8GB (with qwen2.5:3b)
- **Disk**: 5GB
- **CPU**: 4 cores

### Recommended (Development)
- **RAM**: 16GB (with qwen2.5:7b)
- **Disk**: 20GB
- **CPU**: 8 cores

### Production
- **RAM**: 32GB+ (with qwen2.5:14b or multiple models)
- **Disk**: 50GB+
- **CPU**: 16+ cores OR GPU (NVIDIA RTX 3060+)

---

## Integration with RAG Enterprise

### Configuration Flow

1. **Environment Variables** → `app/core/dependencies.py` → `AppConfig`
2. **AppConfig** → `get_rag_qa_service()` → `RAGQAService`
3. **RAGQAService** → Ollama HTTP API → Model Inference

### Code Example

```python
from app.core.dependencies import get_config, get_rag_qa_service

# Get configuration
config = get_config()
print(f"Ollama URL: {config.ollama_url}")
print(f"Ollama Model: {config.ollama_model}")

# Get RAG service (auto-configured with Ollama)
rag_service = get_rag_qa_service()

# Use service for QA
response = await rag_service.answer_question(
    question="What is the product specification?",
    collection="products_all"
)
```

### Testing Integration

```bash
# Unit test with mocked Ollama
pytest tests/unit/test_rag_qa_service.py -v

# Integration test with real Ollama
pytest tests/integration/test_rag_qa_service.py -v

# E2E test with full pipeline
pytest tests/e2e/test_pipeline_e2e.py -v
```

---

## Best Practices

### Development
1. Use local Ollama app for faster iteration
2. Start with small models (qwen2.5:3b) for testing
3. Verify connectivity before running tests
4. Monitor resource usage during development

### Production
1. Use Docker Ollama for consistency
2. Pre-pull models during deployment
3. Configure health checks and monitoring
4. Set resource limits based on load testing
5. Use GPU if available for better throughput

### Model Management
1. Keep models updated: `ollama pull <model>`
2. Remove unused models: `ollama rm <model>`
3. Test new models in development before production
4. Document model changes in release notes

---

## Security Considerations

### Network Security

```bash
# Bind to localhost only (default - secure)
export OLLAMA_HOST=127.0.0.1:11434

# Bind to all interfaces (production with firewall)
export OLLAMA_HOST=0.0.0.0:11434
```

### API Access Control

Ollama does not have built-in authentication. For production:

1. Use reverse proxy (nginx/traefik) with authentication
2. Configure firewall rules to restrict access
3. Use VPN or private network for Ollama communication
4. Enable HTTPS with valid certificates

### Model Security

```bash
# Verify model signatures (when available)
ollama pull qwen2.5:7b-instruct-q4_K_M --verify

# List model hashes
ollama list

# Remove unauthorized models
ollama rm suspicious-model
```

---

## Migration Guide

For detailed migration steps from Docker Ollama to Local Ollama, see:
**[MIGRATION_OLLAMA_LOCAL.md](./MIGRATION_OLLAMA_LOCAL.md)**

---

## Additional Resources

- **Official Documentation:** https://github.com/ollama/ollama/blob/main/docs/README.md
- **Model Library:** https://ollama.com/library
- **API Reference:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Community Discord:** https://discord.gg/ollama
- **RAG Enterprise Docs:** [README.md](./README.md)

---

**Last Updated:** 2025-10-20
**Version:** 2.0.0
**Tested With:** Ollama 0.1.x+, macOS 14+, Ubuntu 22.04+, Docker 24.x+
