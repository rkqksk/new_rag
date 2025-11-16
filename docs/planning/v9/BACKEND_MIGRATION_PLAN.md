# Backend Migration Plan: app/ + src/ → backend/

**Version**: v1.0.0
**Date**: 2025-11-15
**Status**: Planning Phase
**Estimated Duration**: 4-6 hours

---

## Executive Summary

### Current State
- **app/** (142 files): v7.x infrastructure, core RAG, realtime backend
- **src/** (174 files): v8-v9 features (advanced RAG, SaaS, manufacturing, middleware)
- **backend/** (142 files): Copy of app/ directory (currently duplicate)

### Target State
- **backend/** (unified): Single source of truth with organized v1 (stable) and v2 (experimental) APIs
- Clean import paths: `backend.*` everywhere
- No duplicate code between app/, src/, backend/
- All tests passing with new imports

### Migration Strategy
- **Incremental**: Feature-by-feature migration
- **Safe**: Full test suite after each phase
- **Reversible**: Git branches for easy rollback
- **Zero-downtime**: Docker compose unaffected during migration

---

## Phase 1: Pre-Migration Analysis ✅

### 1.1 Current Structure Analysis

**app/ (v7.x base - 142 files)**
```
app/
├── api/
│   ├── v1/                    # 11 files - Core v1 API
│   │   ├── search.py
│   │   ├── analytics.py
│   │   ├── admin.py
│   │   ├── debug.py
│   │   └── ...
│   └── routes/                # 5 files - Legacy routes
│       ├── health.py
│       ├── excel.py
│       └── ...
├── core/                      # 15 files - Infrastructure
│   ├── config.py
│   ├── logging.py
│   ├── exceptions.py
│   ├── health.py
│   └── routing/               # 4 files - Intent routing
├── services/                  # 50+ files - Business logic
├── middleware/                # 5 files - Basic middleware
├── realtime/                  # 3 files - Socket.IO, PostgreSQL LISTEN/NOTIFY
├── rag_consultation/          # 16 files - RAG consultation system
├── repositories/              # 5 files - Data access
└── models/                    # 3 files - Pydantic models
```

**src/ (v8-v9 features - 174 files)**
```
src/
├── api/
│   ├── routes/                # 23 files - v8-v9 routes
│   │   ├── auth.py           # ⭐ JWT authentication
│   │   ├── manufacturing.py   # ⭐ LORA + UR10e
│   │   ├── metrics.py         # ⭐ Phase 9 metrics
│   │   ├── recommendations.py # ⭐ Phase 9 recommendations
│   │   ├── search_ranking.py  # ⭐ Phase 9 ranking
│   │   ├── websocket.py       # ⭐ Phase 9 notifications
│   │   ├── ultimate_*.py      # ⭐ Ultimate services
│   │   └── ...
│   └── v1/
│       └── saas.py           # ⭐ SaaS platform
├── middleware/                # 2 files - Advanced middleware
│   ├── rate_limiting.py      # ⭐ Phase 9 rate limiting
│   └── error_tracking.py     # ⭐ Phase 9 error tracking
├── services/                  # 50+ files - Advanced services
│   ├── ultimate_*.py         # Ultimate automation services
│   ├── rate_limiter_service.py
│   ├── analytics_service.py
│   └── ...
├── core/                      # 27 files - Advanced core
│   ├── advanced_rag/         # 7 files
│   ├── multimodal/           # 8 files
│   ├── ocr/                  # 8 files
│   ├── recommendation/       # 8 files
│   └── ...
├── auth/                      # 3 files - JWT auth
└── models/                    # 2 files - SaaS models
```

**backend/ (duplicate of app/ - 142 files)**
```
backend/
├── api/
│   ├── v1/                   # ✅ Already exists (from app/)
│   └── v2/                   # 🆕 To be created for v8-v9 features
├── core/                     # ✅ Already exists
├── middleware/
│   ├── (basic from app/)     # ✅ Already exists
│   └── advanced/             # 🆕 To be created for src/ middleware
├── services/                 # ✅ Already exists
└── ...
```

### 1.2 Import Dependencies Analysis

**Files importing from app/***
- Total: 142 files in app/, backend/, and external
- Top imports:
  - `app.core.config` (8 occurrences)
  - `app.core.logging` (8 occurrences)
  - `app.core.dependencies` (6 occurrences)

**Files importing from src/***
- Total: 174 files in src/
- Top imports:
  - `src.db.session` (22 occurrences)
  - `src.models.saas_models` (6 occurrences)
  - `src.core.chunk_templates` (6 occurrences)

**Mixed imports (app + src):**
- `backend/main.py` - Main entry point (CRITICAL)
- Other files minimal

### 1.3 Key Conflicts to Resolve

| File | app/ | src/ | Resolution |
|------|------|------|------------|
| `middleware/rate_limiting.py` | Basic v6.0 | Advanced v8.5 | Use src/ version (more features) |
| `core/config.py` | v7.x | Minimal | Merge, keep app/ as base |
| `models/saas_models.py` | None | Exists | Copy to backend/ |
| `services/embedding_service.py` | Basic | Advanced | Merge features |

---

## Phase 2: Directory Structure Design

### 2.1 Target Backend Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py                    # Main FastAPI app (merged from app/main.py)
│   ├── v1/                        # Stable v7.x APIs
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── analytics.py
│   │   ├── admin.py
│   │   ├── debug.py
│   │   ├── hybrid.py
│   │   ├── multi_agent.py
│   │   ├── personalization.py
│   │   ├── rag_advanced.py
│   │   ├── streaming.py
│   │   └── analytics_realtime.py
│   ├── v2/                        # Experimental v8-v9 APIs ⭐ NEW
│   │   ├── __init__.py
│   │   ├── auth.py               # From src/api/routes/auth.py
│   │   ├── manufacturing.py      # From src/api/routes/manufacturing.py
│   │   ├── metrics.py            # From src/api/routes/metrics.py
│   │   ├── recommendations.py    # From src/api/routes/recommendations.py
│   │   ├── search_ranking.py     # From src/api/routes/search_ranking.py
│   │   ├── websocket.py          # From src/api/routes/websocket.py
│   │   ├── saas.py               # From src/api/v1/saas.py
│   │   ├── ultimate_rag.py       # From src/api/routes/ultimate_rag.py
│   │   ├── ultimate_crawler.py   # From src/api/routes/ultimate_crawler.py
│   │   ├── ultimate_saas.py      # From src/api/routes/ultimate_saas.py
│   │   └── ...                   # Other ultimate_* routes
│   └── routes/                    # Legacy compatibility
│       ├── health.py
│       ├── excel.py
│       ├── image.py
│       └── async_qa.py
│
├── core/                          # Core infrastructure
│   ├── __init__.py
│   ├── config.py                  # Merged app/src configs
│   ├── logging.py
│   ├── exceptions.py
│   ├── health.py
│   ├── telemetry.py
│   ├── metrics.py
│   ├── auth_keycloak.py
│   ├── secrets_vault.py
│   ├── storage_minio.py
│   ├── routing/                   # From app/core/routing/
│   ├── advanced_rag/             # From src/core/advanced_rag/ ⭐ NEW
│   ├── multimodal/               # From src/core/multimodal/ ⭐ NEW
│   ├── ocr/                      # From src/core/ocr/ ⭐ NEW
│   ├── recommendation/           # From src/core/recommendation/ ⭐ NEW
│   └── auth/                     # From src/core/auth/ ⭐ NEW
│
├── middleware/
│   ├── __init__.py
│   ├── request_logging.py        # From app/
│   ├── request_tracing.py        # From app/
│   ├── performance_timing.py     # From app/
│   └── advanced/                 # ⭐ NEW from src/middleware/
│       ├── __init__.py
│       ├── rate_limiting.py      # Advanced rate limiting (v8.5)
│       └── error_tracking.py     # Error tracking (v8.5)
│
├── services/                      # Business logic
│   ├── (all from app/services/)
│   ├── (all from src/services/)  # ⭐ NEW
│   └── ...
│
├── models/
│   ├── __init__.py
│   ├── schemas.py                # From app/
│   └── saas_models.py           # From src/ ⭐ NEW
│
├── auth/                         # ⭐ NEW from src/auth/
│   ├── __init__.py
│   ├── models.py
│   ├── jwt_utils.py
│   └── dependencies.py
│
├── db/                           # ⭐ NEW from src/db/
│   ├── __init__.py
│   └── session.py
│
├── integrations/                 # ⭐ NEW from src/integrations/
│   ├── __init__.py
│   ├── s3_integration.py
│   ├── google_drive_integration.py
│   └── automated_pipeline.py
│
├── streaming/                    # ⭐ NEW from src/streaming/
│   ├── __init__.py
│   ├── sse_manager.py
│   ├── sse_endpoints.py
│   └── analytics_dashboard.py
│
├── analytics/                    # ⭐ NEW from src/analytics/
│   ├── __init__.py
│   ├── behavior_tracker.py
│   └── popularity_calculator.py
│
├── utils/                        # ⭐ NEW from src/utils/
│   ├── __init__.py
│   ├── coordinate_transform.py
│   └── robot_safety.py
│
├── realtime/                     # From app/ (Socket.IO)
│   ├── socketio_server.py
│   ├── postgres_notify.py
│   └── redis_pubsub.py
│
├── rag_consultation/             # From app/
│   └── ...
│
├── repositories/                 # From app/
│   └── ...
│
├── routes/                       # From app/ (legacy)
│   └── ...
│
├── conversation/                 # From app/
│   └── ...
│
├── dependencies/                 # From app/
│   └── ...
│
├── graphql/                      # From app/
│   └── ...
│
└── main.py                       # Main entry point (merged)
```

### 2.2 API Version Strategy

**v1 APIs (Stable - Production Ready)**
- All current app/api/v1/ endpoints
- Well-tested, documented
- No breaking changes

**v2 APIs (Experimental - Feature Preview)**
- All src/api/routes/ endpoints
- v8-v9 features (auth, manufacturing, metrics, etc.)
- May have breaking changes
- Gradual promotion to v1 after validation

**Migration Path**: v2 → v1
- After 6 months stability and >80% test coverage
- Breaking changes stabilized
- Full documentation
- User feedback incorporated

---

## Phase 3: Step-by-Step Migration Plan

### 3.1 Phase 3A: Preparation (30 min)

**Step 1: Create Migration Branch**
```bash
git checkout -b backend-migration
git branch backup-before-migration  # Safety backup
```

**Step 2: Verify Current State**
```bash
# Ensure all tests pass before migration
pytest tests/ -v
docker-compose down
docker-compose up -d postgres redis qdrant
sleep 10
python3 -m pytest tests/test_api_quick.py -v
```

**Step 3: Create Migration Scripts**
```bash
mkdir -p scripts/migration/
touch scripts/migration/01_copy_src_to_backend.sh
touch scripts/migration/02_update_imports.sh
touch scripts/migration/03_validate_structure.sh
chmod +x scripts/migration/*.sh
```

**Step 4: Document Current Import Map**
```bash
# Create import mapping file for reference
cat > scripts/migration/import_map.json << 'EOF'
{
  "app.core.config": "backend.core.config",
  "app.core.logging": "backend.core.logging",
  "app.services": "backend.services",
  "src.api.routes.auth": "backend.api.v2.auth",
  "src.api.routes.manufacturing": "backend.api.v2.manufacturing",
  "src.api.routes.metrics": "backend.api.v2.metrics",
  "src.api.routes.recommendations": "backend.api.v2.recommendations",
  "src.api.routes.search_ranking": "backend.api.v2.search_ranking",
  "src.api.routes.websocket": "backend.api.v2.websocket",
  "src.api.v1.saas": "backend.api.v2.saas",
  "src.middleware.rate_limiting": "backend.middleware.advanced.rate_limiting",
  "src.middleware.error_tracking": "backend.middleware.advanced.error_tracking",
  "src.services": "backend.services",
  "src.models.saas_models": "backend.models.saas_models",
  "src.auth": "backend.auth",
  "src.db": "backend.db",
  "src.core": "backend.core"
}
EOF
```

### 3.2 Phase 3B: Copy src/ Features to backend/ (45 min)

**Step 5: Create backend/api/v2/ Structure**
```bash
# Create v2 API directory
mkdir -p backend/api/v2/

# Create __init__.py
cat > backend/api/v2/__init__.py << 'EOF'
"""
API v2 - Experimental Features
Version: v8-v9
Status: Preview

Experimental APIs from v8-v9:
- JWT Authentication
- Advanced Manufacturing (LORA + UR10e)
- Metrics & Analytics
- Recommendations
- Search Ranking
- WebSocket Notifications
- SaaS Platform
- Ultimate Services
"""

__version__ = "2.0.0"
__all__ = [
    "auth",
    "manufacturing",
    "metrics",
    "recommendations",
    "search_ranking",
    "websocket",
    "saas",
]
EOF
```

**Step 6: Copy src/api/routes/ to backend/api/v2/**
```bash
# Copy v8-v9 route files
cp src/api/routes/auth.py backend/api/v2/auth.py
cp src/api/routes/manufacturing.py backend/api/v2/manufacturing.py
cp src/api/routes/metrics.py backend/api/v2/metrics.py
cp src/api/routes/recommendations.py backend/api/v2/recommendations.py
cp src/api/routes/search_ranking.py backend/api/v2/search_ranking.py
cp src/api/routes/websocket.py backend/api/v2/websocket.py
cp src/api/v1/saas.py backend/api/v2/saas.py

# Copy ultimate services routes
cp src/api/routes/ultimate_rag.py backend/api/v2/ultimate_rag.py
cp src/api/routes/ultimate_crawler.py backend/api/v2/ultimate_crawler.py
cp src/api/routes/ultimate_saas.py backend/api/v2/ultimate_saas.py
cp src/api/routes/ultimate_sales.py backend/api/v2/ultimate_sales.py
cp src/api/routes/ultimate_management.py backend/api/v2/ultimate_management.py
cp src/api/routes/ultimate_preprocessing.py backend/api/v2/ultimate_preprocessing.py
cp src/api/routes/ultimate_manufacturing_ai.py backend/api/v2/ultimate_manufacturing_ai.py
```

**Step 7: Copy src/middleware/ to backend/middleware/advanced/**
```bash
mkdir -p backend/middleware/advanced/

# Copy advanced middleware
cp src/middleware/rate_limiting.py backend/middleware/advanced/rate_limiting.py
cp src/middleware/error_tracking.py backend/middleware/advanced/error_tracking.py

# Create __init__.py
cat > backend/middleware/advanced/__init__.py << 'EOF'
"""
Advanced Middleware (v8.5+)
- Rate limiting with multiple algorithms
- Error tracking and analytics
"""

from .rate_limiting import RateLimitMiddleware, RateLimitTier, RateLimitAlgorithm
from .error_tracking import (
    ErrorTrackingMiddleware,
    RequestContextMiddleware,
    AnalyticsMiddleware
)

__all__ = [
    "RateLimitMiddleware",
    "RateLimitTier",
    "RateLimitAlgorithm",
    "ErrorTrackingMiddleware",
    "RequestContextMiddleware",
    "AnalyticsMiddleware",
]
EOF
```

**Step 8: Copy src/services/ to backend/services/**
```bash
# Copy all src services (174 files total, ~50 in services/)
# Avoid overwriting existing app/services
for file in src/services/*.py; do
    filename=$(basename "$file")
    if [ ! -f "backend/services/$filename" ]; then
        cp "$file" "backend/services/$filename"
    else
        echo "⚠️  Conflict: backend/services/$filename exists"
        cp "$file" "backend/services/${filename%.py}_v2.py"
    fi
done
```

**Step 9: Copy src/core/ subdirectories to backend/core/**
```bash
# Copy advanced core modules
cp -r src/core/advanced_rag backend/core/
cp -r src/core/multimodal backend/core/
cp -r src/core/ocr backend/core/
cp -r src/core/recommendation backend/core/
cp -r src/core/auth backend/core/
cp -r src/core/caching backend/core/
cp -r src/core/enhancements backend/core/
cp -r src/core/image_matching backend/core/
cp -r src/core/shape_processors backend/core/
cp -r src/core/structured_processors backend/core/

# Copy individual core files (only if not conflicting)
for file in src/core/*.py; do
    filename=$(basename "$file")
    if [ ! -f "backend/core/$filename" ]; then
        cp "$file" "backend/core/$filename"
    fi
done
```

**Step 10: Copy src/ top-level modules to backend/**
```bash
# Copy auth module
cp -r src/auth backend/

# Copy db module
cp -r src/db backend/

# Copy models (merge with existing)
cp src/models/saas_models.py backend/models/

# Copy integrations
cp -r src/integrations backend/

# Copy streaming
cp -r src/streaming backend/

# Copy analytics
cp -r src/analytics backend/

# Copy utils
cp -r src/utils backend/
```

### 3.3 Phase 3C: Update Imports (60 min)

**Step 11: Create Import Update Script**
```bash
cat > scripts/migration/02_update_imports.sh << 'EOF'
#!/bin/bash
# Update all imports from app.* and src.* to backend.*

set -e

echo "🔄 Updating imports in backend/..."

# Function to update imports in a file
update_imports() {
    local file="$1"

    # Skip __pycache__ and non-Python files
    if [[ "$file" == *"__pycache__"* ]] || [[ "$file" != *.py ]]; then
        return
    fi

    echo "  Processing: $file"

    # Create temporary file
    temp_file="${file}.tmp"

    # Update imports (careful with regex to avoid partial matches)
    sed -E 's/from app\.([a-zA-Z0-9_.]+) import/from backend.\1 import/g' "$file" > "$temp_file"
    sed -E -i 's/import app\.([a-zA-Z0-9_.]+)/import backend.\1/g' "$temp_file"

    # Update src imports to backend
    sed -E -i 's/from src\.api\.routes\.([a-zA-Z0-9_]+) import/from backend.api.v2.\1 import/g' "$temp_file"
    sed -E -i 's/from src\.api\.v1\.([a-zA-Z0-9_]+) import/from backend.api.v2.\1 import/g' "$temp_file"
    sed -E -i 's/from src\.middleware\.([a-zA-Z0-9_]+) import/from backend.middleware.advanced.\1 import/g' "$temp_file"
    sed -E -i 's/from src\.([a-zA-Z0-9_.]+) import/from backend.\1 import/g' "$temp_file"
    sed -E -i 's/import src\.([a-zA-Z0-9_.]+)/import backend.\1/g' "$temp_file"

    # Replace original file
    mv "$temp_file" "$file"
}

# Update all Python files in backend/
export -f update_imports
find backend/ -type f -name "*.py" -exec bash -c 'update_imports "$0"' {} \;

echo "✅ Import updates complete"
EOF

chmod +x scripts/migration/02_update_imports.sh
```

**Step 12: Run Import Update Script**
```bash
./scripts/migration/02_update_imports.sh
```

**Step 13: Update backend/main.py (CRITICAL)**

Manually update `backend/main.py` to:
1. Remove all `from app.*` imports → `from backend.*`
2. Remove all `from src.*` imports → `from backend.*`
3. Add v2 API routes

```python
# Before (lines 10-21):
from app.api.routes import image_processing, excel, health, async_qa
from app.api.v1 import admin, analytics, analytics_realtime, debug, hybrid, multi_agent, personalization, rag_advanced, search, streaming
from app.api import workflow_routes, consultation, dashboard_routes, ingestion_routes, query_routes
from app.routes import products, qa, inquiries, tracking
from src.api.v1 import saas
from src.api.routes import manufacturing
from src.api.routes import metrics, recommendations, search_ranking, websocket
from src.middleware.rate_limiting import RateLimitMiddleware, RateLimitTier, RateLimitAlgorithm
from src.middleware.error_tracking import ErrorTrackingMiddleware, RequestContextMiddleware, AnalyticsMiddleware

# After:
from backend.api.routes import image_processing, excel, health, async_qa
from backend.api.v1 import admin, analytics, analytics_realtime, debug, hybrid, multi_agent, personalization, rag_advanced, search, streaming
from backend.api import workflow_routes, consultation, dashboard_routes, ingestion_routes, query_routes
from backend.routes import products, qa, inquiries, tracking
from backend.api.v2 import saas, manufacturing, metrics, recommendations, search_ranking, websocket
from backend.middleware.advanced.rate_limiting import RateLimitMiddleware, RateLimitTier, RateLimitAlgorithm
from backend.middleware.advanced.error_tracking import ErrorTrackingMiddleware, RequestContextMiddleware, AnalyticsMiddleware
```

**Step 14: Update pytest.ini**
```bash
# Update pytest.ini to test backend instead of app
sed -i 's/source = app/source = backend/g' pytest.ini
```

**Step 15: Update alembic/env.py**
```bash
# Update database migrations to use backend
sed -i 's/from app\./from backend./g' alembic/env.py
```

### 3.4 Phase 3D: Update Docker & Configuration (30 min)

**Step 16: Update docker-compose.yml**

Update the API service to use backend:

```yaml
# Before:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# After:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

**Step 17: Update Dockerfile**
```dockerfile
# Update PYTHONPATH and entry point

# Before:
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

# After:
ENV PYTHONPATH=/app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Step 18: Update Scripts**
```bash
# Update all deployment scripts
sed -i 's/app\.main/backend.main/g' scripts/*.sh
sed -i 's/app\.main/backend.main/g' scripts/*.py 2>/dev/null || true
```

### 3.5 Phase 3E: Testing & Validation (60 min)

**Step 19: Run Static Analysis**
```bash
# Check for remaining app.* or src.* imports in backend/
echo "🔍 Checking for old imports in backend/..."
grep -r "from app\." backend/ || echo "✅ No app.* imports found"
grep -r "import app\." backend/ || echo "✅ No app.* imports found"
grep -r "from src\." backend/ || echo "✅ No src.* imports found"
grep -r "import src\." backend/ || echo "✅ No src.* imports found"
```

**Step 20: Run Import Validation**
```bash
# Test that all modules can be imported
python3 << 'EOF'
import sys
import importlib

modules = [
    "backend.core.config",
    "backend.core.logging",
    "backend.api.v1.search",
    "backend.api.v2.auth",
    "backend.api.v2.manufacturing",
    "backend.middleware.advanced.rate_limiting",
    "backend.middleware.advanced.error_tracking",
    "backend.services.rate_limiter_service",
    "backend.models.saas_models",
    "backend.auth.jwt_utils",
    "backend.db.session",
]

failed = []
for module in modules:
    try:
        importlib.import_module(module)
        print(f"✅ {module}")
    except Exception as e:
        print(f"❌ {module}: {e}")
        failed.append(module)

if failed:
    print(f"\n❌ Failed to import {len(failed)} modules")
    sys.exit(1)
else:
    print(f"\n✅ All {len(modules)} modules imported successfully")
EOF
```

**Step 21: Run Unit Tests**
```bash
# Run full test suite
pytest tests/ -v --tb=short

# Run specific test categories
pytest tests/test_api_quick.py -v
pytest tests/integration/ -v
pytest tests/services/ -v
```

**Step 22: Start Services and Test APIs**
```bash
# Rebuild Docker images
docker-compose build api

# Start all services
docker-compose up -d

# Wait for services
sleep 30

# Test health endpoints
curl http://localhost:8001/health/ready
curl http://localhost:8001/health/live

# Test v1 API
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":5}'

# Test v2 API (if auth available)
# curl http://localhost:8001/api/v2/metrics/system

# Check logs
docker-compose logs -f api | head -50
```

**Step 23: Validate No Import Errors in Logs**
```bash
# Check for import errors
docker-compose logs api 2>&1 | grep -i "importerror\|modulenotfounderror" && \
  echo "❌ Import errors found" || \
  echo "✅ No import errors"
```

---

## Phase 4: Cleanup & Documentation (30 min)

### 4.1 Remove Duplicate Directories

**Step 24: Archive app/ and src/**
```bash
# Create archives directory
mkdir -p archive/pre-migration/

# Move old directories
mv app/ archive/pre-migration/app_$(date +%Y%m%d)/
mv src/ archive/pre-migration/src_$(date +%Y%m%d)/

# Update .gitignore
echo "archive/pre-migration/" >> .gitignore
```

**Step 25: Update External References**
```bash
# Update any external scripts still referencing app/ or src/
# Check common locations:
grep -r "from app\." scripts/ tests/ || echo "✅ No app imports in scripts/tests"
grep -r "from src\." scripts/ tests/ || echo "✅ No src imports in scripts/tests"

# Update if found
find scripts/ tests/ -type f -name "*.py" -exec sed -i 's/from app\./from backend./g' {} \;
find scripts/ tests/ -type f -name "*.py" -exec sed -i 's/from src\./from backend./g' {} \;
```

### 4.2 Update Documentation

**Step 26: Update README.md**
```bash
# Update project structure section
sed -i 's/app\//backend\//g' README.md
sed -i 's/src\//backend\//g' README.md
```

**Step 27: Update CLAUDE.md**
```bash
# Update quick reference paths
sed -i 's/app\//backend\//g' CLAUDE.md
```

**Step 28: Create Migration Summary**
```bash
cat > BACKEND_MIGRATION_SUMMARY.md << 'EOF'
# Backend Migration Summary

**Date**: $(date +%Y-%m-%d)
**Status**: ✅ Complete

## Changes Made

### Directory Structure
- ✅ Unified app/ and src/ into backend/
- ✅ Created backend/api/v2/ for v8-v9 features
- ✅ Created backend/middleware/advanced/ for Phase 9 middleware
- ✅ Merged all services, models, core modules

### Import Updates
- ✅ Updated 316+ Python files
- ✅ Changed app.* → backend.*
- ✅ Changed src.* → backend.*
- ✅ Updated pytest.ini, alembic, Docker configs

### Testing
- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ API health checks passing
- ✅ No import errors in logs

### Files Migrated
- app/: 142 files → backend/
- src/: 174 files → backend/
- Total: 316 files unified

### API Structure
- v1/: Stable production APIs (v7.x)
- v2/: Experimental APIs (v8-v9)

## Rollback Plan

If issues occur:
```bash
git checkout backup-before-migration
docker-compose down
docker-compose up -d
```

## Next Steps

1. Monitor production for 48 hours
2. Archive app/ and src/ permanently after 1 week
3. Update all external documentation
4. Train team on new import paths
EOF
```

### 4.3 Git Commit Strategy

**Step 29: Commit Migration**
```bash
# Add all changes
git add backend/
git add pytest.ini alembic/env.py docker-compose.yml Dockerfile
git add scripts/

# Commit
git commit -m "feat: Unify app/ and src/ into backend/

- Create backend/api/v2/ for v8-v9 experimental features
- Create backend/middleware/advanced/ for Phase 9 middleware
- Update all imports: app.* → backend.*, src.* → backend.*
- Update Docker, pytest, alembic configs
- All tests passing
- Zero downtime migration

BREAKING CHANGE: Import paths changed from app.*/src.* to backend.*

Migrated files:
- app/: 142 files
- src/: 174 files
- Total: 316 files

API structure:
- backend/api/v1/: Stable v7.x APIs
- backend/api/v2/: Experimental v8-v9 APIs

Co-authored-by: Claude <noreply@anthropic.com>"

# Tag the migration
git tag -a v10.0.0-migration -m "Backend unification migration"
```

---

## Phase 5: Post-Migration Validation (30 min)

### 5.1 Comprehensive Testing Checklist

**Step 30: Full System Test**
```bash
# Create validation script
cat > scripts/migration/03_validate_structure.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Post-Migration Validation"
echo "=============================="

# 1. Check directory structure
echo "1. Checking directory structure..."
test -d backend/api/v1 && echo "  ✅ backend/api/v1 exists"
test -d backend/api/v2 && echo "  ✅ backend/api/v2 exists"
test -d backend/middleware/advanced && echo "  ✅ backend/middleware/advanced exists"

# 2. Count files
echo "2. Counting migrated files..."
v1_count=$(find backend/api/v1 -name "*.py" | wc -l)
v2_count=$(find backend/api/v2 -name "*.py" | wc -l)
echo "  ✅ v1 APIs: $v1_count files"
echo "  ✅ v2 APIs: $v2_count files"

# 3. Check for old imports
echo "3. Checking for old import paths..."
old_imports=$(grep -r "from app\." backend/ 2>/dev/null | wc -l)
if [ "$old_imports" -eq 0 ]; then
    echo "  ✅ No app.* imports found"
else
    echo "  ❌ Found $old_imports app.* imports"
    exit 1
fi

# 4. Test imports
echo "4. Testing Python imports..."
python3 -c "import backend.core.config; print('  ✅ backend.core.config')"
python3 -c "import backend.api.v1.search; print('  ✅ backend.api.v1.search')"
python3 -c "import backend.api.v2.auth; print('  ✅ backend.api.v2.auth')"

# 5. Run tests
echo "5. Running test suite..."
pytest tests/test_api_quick.py -v -q

echo ""
echo "✅ Post-migration validation complete"
EOF

chmod +x scripts/migration/03_validate_structure.sh
./scripts/migration/03_validate_structure.sh
```

### 5.2 Performance Benchmarks

**Step 31: Compare Performance**
```bash
# Test API response times before/after
echo "Testing API performance..."

# v1 search endpoint
time curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"packaging","top_k":5}' \
  -s -o /dev/null

# v2 metrics endpoint (if available)
time curl http://localhost:8001/api/v2/metrics/system -s -o /dev/null || true
```

### 5.3 Monitor Services

**Step 32: Monitor for 24 Hours**
```bash
# Set up monitoring alerts
docker-compose logs -f api | grep -i "error\|warning\|exception" &

# Check memory usage
docker stats api --no-stream

# Monitor error rate
docker-compose logs api --tail=1000 | grep -c "ERROR" || echo "0 errors"
```

---

## Phase 6: Rollback Plan

### 6.1 Immediate Rollback (< 1 hour after migration)

```bash
# If critical issues found immediately:

# 1. Checkout backup branch
git checkout backup-before-migration

# 2. Rebuild containers
docker-compose down
docker-compose build api
docker-compose up -d

# 3. Verify services
curl http://localhost:8001/health/ready
```

### 6.2 Partial Rollback (1-7 days after migration)

```bash
# If specific features broken:

# 1. Restore specific files from backup
git checkout backup-before-migration -- backend/api/v2/problematic_feature.py

# 2. Fix imports in restored file
sed -i 's/from src\./from backend./g' backend/api/v2/problematic_feature.py

# 3. Restart service
docker-compose restart api
```

---

## Risk Assessment

### High Risk Areas

| Area | Risk Level | Mitigation |
|------|------------|------------|
| Import path changes | 🔴 High | Automated script + manual verification |
| backend/main.py | 🔴 High | Manual review + extensive testing |
| Docker build | 🟡 Medium | Test build before deployment |
| Database migrations | 🟡 Medium | Alembic update + backup before run |
| External dependencies | 🟢 Low | No external code imports app/src directly |

### Rollback Triggers

**Immediate Rollback** if:
- API returns 500 errors on >10% of requests
- Import errors in logs
- Tests fail after migration
- Services won't start

**Investigate but Don't Rollback** if:
- Performance degradation <10%
- Non-critical features broken
- Documentation out of date

---

## Success Metrics

### Technical Metrics
- ✅ 0 import errors in logs
- ✅ 100% tests passing (same as before migration)
- ✅ API response time <5% slower than baseline
- ✅ All 17 services healthy
- ✅ 0 breaking changes to v1 APIs

### Code Quality Metrics
- ✅ Single source of truth (backend/)
- ✅ Clear API versioning (v1/ vs v2/)
- ✅ Organized middleware (basic vs advanced/)
- ✅ No duplicate code
- ✅ Clean import paths

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| 3A: Preparation | 30 min | Branch, scripts, verification |
| 3B: Copy Files | 45 min | Copy src/ to backend/ |
| 3C: Update Imports | 60 min | Import script + manual fixes |
| 3D: Docker Config | 30 min | Update compose, Dockerfile, scripts |
| 3E: Testing | 60 min | Unit, integration, API tests |
| Phase 4: Cleanup | 30 min | Archive, docs, commit |
| Phase 5: Validation | 30 min | Full system test |
| **Total** | **~4.5 hours** | |

**Buffer**: +1.5 hours for unexpected issues
**Total Estimate**: 6 hours

---

## Dependencies

### Required Before Migration
- ✅ All tests passing
- ✅ Git branch up to date
- ✅ Docker services healthy
- ✅ Backup created
- ✅ Team notified

### Required Tools
- ✅ Python 3.11+
- ✅ Docker & Docker Compose
- ✅ sed (GNU sed)
- ✅ bash 4.0+
- ✅ pytest

---

## Notes

### Why v2 for src/ features?

**Rationale**:
1. **Maturity**: src/ features are v8-v9 experimental
2. **Stability**: app/ v7.x is production-tested
3. **Breaking Changes**: v2 allows evolution without breaking v1
4. **Gradual Migration**: Features graduate from v2 → v1 after validation

### Import Update Strategy

**Automated** (90%):
- Regex replacement in `02_update_imports.sh`
- Covers 99% of cases

**Manual** (10%):
- backend/main.py (complex imports)
- Circular dependency fixes
- Dynamic imports

### Testing Strategy

**Pre-Migration**:
- Full test suite baseline
- Performance benchmarks
- API response samples

**During Migration**:
- Import validation after each phase
- Incremental testing

**Post-Migration**:
- Full test suite (must match baseline)
- 24-hour monitoring
- Load testing

---

## Appendix A: File Mapping

### API Routes Mapping

| Source | Destination | Status |
|--------|-------------|--------|
| app/api/v1/*.py | backend/api/v1/*.py | ✅ Already done |
| src/api/routes/auth.py | backend/api/v2/auth.py | 🆕 New |
| src/api/routes/manufacturing.py | backend/api/v2/manufacturing.py | 🆕 New |
| src/api/routes/metrics.py | backend/api/v2/metrics.py | 🆕 New |
| src/api/routes/recommendations.py | backend/api/v2/recommendations.py | 🆕 New |
| src/api/routes/search_ranking.py | backend/api/v2/search_ranking.py | 🆕 New |
| src/api/routes/websocket.py | backend/api/v2/websocket.py | 🆕 New |
| src/api/v1/saas.py | backend/api/v2/saas.py | 🆕 New |

### Middleware Mapping

| Source | Destination | Status |
|--------|-------------|--------|
| app/middleware/*.py | backend/middleware/*.py | ✅ Already done |
| src/middleware/rate_limiting.py | backend/middleware/advanced/rate_limiting.py | 🆕 New |
| src/middleware/error_tracking.py | backend/middleware/advanced/error_tracking.py | 🆕 New |

### Core Modules Mapping

| Source | Destination | Status |
|--------|-------------|--------|
| app/core/*.py | backend/core/*.py | ✅ Already done |
| src/core/advanced_rag/ | backend/core/advanced_rag/ | 🆕 New |
| src/core/multimodal/ | backend/core/multimodal/ | 🆕 New |
| src/core/ocr/ | backend/core/ocr/ | 🆕 New |
| src/core/recommendation/ | backend/core/recommendation/ | 🆕 New |
| src/core/auth/ | backend/core/auth/ | 🆕 New |

---

## Appendix B: Testing Checklist

### Unit Tests
- [ ] backend.core.config
- [ ] backend.core.logging
- [ ] backend.api.v1.search
- [ ] backend.api.v2.auth
- [ ] backend.middleware.advanced.rate_limiting
- [ ] backend.services.*

### Integration Tests
- [ ] Database connections
- [ ] Redis connections
- [ ] Qdrant connections
- [ ] API endpoint responses
- [ ] WebSocket connections

### API Tests
- [ ] v1 search endpoint
- [ ] v1 analytics endpoint
- [ ] v2 auth endpoint
- [ ] v2 metrics endpoint
- [ ] Health endpoints

### Performance Tests
- [ ] Response time baseline
- [ ] Memory usage baseline
- [ ] Concurrent requests handling

---

**End of Migration Plan**

**Next Steps After Completion**:
1. Monitor production for 48 hours
2. Update team documentation
3. Remove app/ and src/ after 1 week validation
4. Promote stable v2 features to v1 after 3 months
