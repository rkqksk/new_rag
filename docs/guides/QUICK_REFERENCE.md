# RAG Enterprise - Quick Reference Card

**Version**: v4.0.0 | **Status**: Phase 0-4 Complete ✅

> **Fast access to common operations and commands**

---

## ⚡ Quick Commands

### Start System
```bash
# Development (all services)
./scripts/deploy-optimized.sh development

# Production
./scripts/deploy-optimized.sh production

# Frontend only
cd frontend && python3 -m http.server 8080
```

### Test System
```bash
# All tests
./scripts/test-optimized.sh

# Python tests only
pytest tests/ -v --cov=src --cov=app

# Specific test
pytest tests/unit/services/test_search_service.py -v
```

### Docker Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart api

# Check status
docker-compose ps
```

---

## 🔍 Common Operations

### Search Products
```python
import requests

response = requests.post(
    "http://localhost:8001/api/v1/search/",
    json={"query": "50ml PET 용기", "top_k": 10}
)
print(response.json())
```

### Process OCR Document
```python
from src.core.ocr import DocumentProcessor

processor = DocumentProcessor()
result = processor.process_file("product_catalog.pdf")
print(f"Extracted: {result['text'][:100]}...")
```

### Check System Health
```bash
curl http://localhost:8001/health/ready
```

### Debug Performance
```bash
curl http://localhost:8001/api/v1/debug/performance/summary
```

---

## 📊 System Status

### Current Data
- **Products**: 471
- **Chunks**: 3,246 (6.9/product)
- **Search Quality**: 0.79-0.82
- **Vector DB**: Qdrant (3,246 vectors, 384-dim)

### Services
- **API**: http://localhost:8001
- **Docs**: http://localhost:8001/api/v1/docs
- **Qdrant**: http://localhost:6333/dashboard
- **Frontend**: http://localhost:8080

### Ports
- API: 8001
- Qdrant: 6333
- Redis: 6379
- PostgreSQL: 5432
- Frontend: 8080

---

## 🎯 Symbol Quick Access

### Most Used Symbols
```
§rag.status         - RAG system status
§rag.core           - Core modules
§ocr.pipeline       - OCR workflow
§debug.endpoints    - Debug API
§deploy.quick       - Quick deployment
§test.coverage      - Test details
§api.endpoints      - API reference
```

### Load Full Details
- **§rag.*** → `docs/RAG_ACTIVATION_STRATEGY.md`
- **§ocr.*** → `docs/OCR_PARSING_STRATEGY.md`
- **§debug.*** → `docs/DEBUG_SYSTEM.md`
- **§deploy.*** → `docs/DEPLOYMENT_GUIDE.md`
- **§api.*** → `docs/API_DOCUMENTATION.md`

**Complete Map**: `docs/reference/SYMBOLS.md`

---

## 🔧 Troubleshooting

### Service Won't Start
```bash
# Check Docker
docker info

# Check ports
lsof -i :8001  # API
lsof -i :6333  # Qdrant

# Reset everything
docker-compose down -v
docker-compose up -d
```

### Search Not Working
```bash
# Check Qdrant collections
curl http://localhost:6333/collections

# Check vector count
curl http://localhost:6333/collections/products_atomic

# Check API health
curl http://localhost:8001/health/ready
```

### Debug Performance Issues
```bash
# Enable debug mode
echo "DEBUG_ENABLED=true" >> .env
docker-compose restart api

# Check slow queries
curl http://localhost:8001/api/v1/debug/queries/recent?slow_only=true

# Check performance summary
curl http://localhost:8001/api/v1/debug/performance/summary
```

---

## 📝 Environment Variables

### Essential Variables
```bash
# API Configuration
API_PORT=8001
API_HOST=0.0.0.0

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Cache
REDIS_HOST=redis
REDIS_PORT=6379

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your_password
```

### Debug Configuration
```bash
DEBUG_ENABLED=true
DEBUG_LOG_REQUESTS=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=300
```

**Full List**: `.env.example`

---

## 🧪 Testing Checklist

### Pre-Deployment
- [ ] All tests passing (`./scripts/test-optimized.sh`)
- [ ] Coverage ≥ 95% (`pytest --cov`)
- [ ] No errors in logs (`docker-compose logs`)
- [ ] All services healthy (`health/ready`)

### Post-Deployment
- [ ] API responding (`curl /health/ready`)
- [ ] Search working (test query)
- [ ] Frontend accessible (`http://localhost:8080`)
- [ ] Qdrant UI accessible (`http://localhost:6333/dashboard`)

---

## 🚀 Development Workflow

### 1. Start Development
```bash
git checkout -b feature/my-feature
./scripts/deploy-optimized.sh development
```

### 2. Make Changes
```bash
# Edit code
vim src/core/my_module.py

# Run tests
pytest tests/unit/ -v
```

### 3. Test & Commit
```bash
./scripts/test-optimized.sh
git add .
git commit -m "feat: Add my feature"
```

### 4. Push & Deploy
```bash
git push origin feature/my-feature
# Create PR
# After approval: deploy to production
./scripts/deploy-optimized.sh production
```

---

## 📖 Documentation Index

### Quick Access
- **This File**: Quick reference
- **Complete Symbols**: `docs/reference/SYMBOLS.md`
- **API Docs**: `docs/API_DOCUMENTATION.md`
- **Deployment**: `docs/DEPLOYMENT_GUIDE.md`

### Full Documentation
```bash
docs/
├── guides/
│   ├── QUICK_REFERENCE.md (this file)
│   ├── DEPLOYMENT.md
│   └── TESTING.md
├── reference/
│   ├── SYMBOLS.md (complete map)
│   ├── API.md
│   └── ARCHITECTURE.md
└── strategies/
    ├── OCR_STRATEGY.md
    ├── MULTIMODAL_STRATEGY.md
    └── RAG_STRATEGY.md
```

---

## 🆘 Getting Help

### Resources
- **Documentation**: `docs/` directory
- **API Docs**: http://localhost:8001/api/v1/docs
- **Symbol Map**: `docs/reference/SYMBOLS.md`

### Common Commands
```bash
# View API documentation
open http://localhost:8001/api/v1/docs

# Check logs
docker-compose logs -f api

# Debug specific service
docker-compose logs qdrant --tail=100

# Shell into container
docker-compose exec api bash
```

---

**Last Updated**: 2025-11-06
**Version**: v4.0.0
**Quick Start**: `./scripts/deploy-optimized.sh development`
