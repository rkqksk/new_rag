# RAG Enterprise - Complete Symbol Reference Map

**Version**: v5.0.0
**Last Updated**: 2025-11-08

> **Purpose**: Lightweight symbol-based navigation system for efficient documentation access.
> **Usage**: Reference symbols like `§rag.core`, `§saas.auth`, or `§collector.pipeline` to access detailed information.

---

## 📖 Symbol System Overview

The symbol system uses hierarchical notation: `§{domain}.{component}.{detail}`

**Benefits**:
- ⚡ **Fast navigation**: Jump directly to relevant content
- 📉 **Reduced duplication**: Reference instead of repeating
- 🎯 **Context-aware**: Load only what you need
- 💾 **Token-efficient**: Minimize context window usage

---

## 🗺️ Complete Symbol Map

### §rag - RAG System

#### §rag.status
**Current State**: Phase 0-4 Complete ✅
**Location**: `CLAUDE.md`, `docs/COMPLETION_REPORT.md`

```
Phase 0: Initial Setup ✅
Phase 1: Atomic Chunking (471 products → 3,246 chunks) ✅
Phase 2: Enhanced Field Extraction ✅
Phase 3: Search Optimization (0.79-0.82 quality) ✅
Phase 4: OCR Pipeline (7 modules, ~1,850 lines) ✅
```

**Quick Access**:
- Data: 471 products → 3,246 atomic chunks
- Search quality: 0.79-0.82 similarity
- Vector DB: Qdrant (3,246 vectors, 384-dim)
- Model: sentence-transformers/all-MiniLM-L6-v2

#### §rag.core
**Core Modules**: Completed production modules
**Location**: `src/core/`

```
✅ product_classifier.py     - Product categorization (Bottle/Jar/Cap/Pump)
✅ chunk_templates.py         - 20+ field type templates
✅ category_templates.py      - Category-specific templates
✅ advanced_chunk_generator.py - Unified chunking pipeline
✅ enhanced_field_extractor.py - Enhanced field extraction
✅ query_parser.py            - Natural language entity extraction
✅ search_engine.py           - Hybrid search engine
✅ natural_language_response.py - Response generation
```

#### §rag.pipeline
**Complete Pipeline**: End-to-end RAG flow
**Location**: `src/core/rag_pipeline.py`, `docs/RAG_ACTIVATION_STRATEGY.md`

```
Data Ingestion → Chunking → Embedding → Vector Store → Search → Response
```

**Key Features**:
- Atomic chunking (6.9 chunks/product)
- Multi-field extraction (8 entity types)
- Hybrid search (semantic + keyword)
- Cross-encoder re-ranking
- Personalization integration

#### §rag.roadmap
**Future Phases**: Phase 5-9 plans
**Location**: `docs/ROADMAP.md`

```
Phase 5: Advanced RAG Integration (unified vector store)
Phase 6: Shape Embedding & Image Matching (tri-modal)
Phase 7: Cloud Data Integration (multi-source)
Phase 8: Real-Time Streaming (SSE)
Phase 9: Enterprise Deployment (K8s + CI/CD)
```

---

### §ocr - OCR & Document Processing

#### §ocr.status
**Current State**: Phase 4 Complete ✅
**Implementation**: 7 production modules (~1,850 lines)
**Location**: `src/core/ocr/`, `docs/OCR_PARSING_STRATEGY.md`

#### §ocr.pipeline
**Multi-Engine OCR Architecture**: Confidence-based fallback
**Location**: `src/core/ocr/`

```
Input (PDF/Image/Excel)
  ↓
Image Preprocessing (deskew, denoise, CLAHE, binarization)
  ↓
Multi-Engine OCR (PaddleOCR → EasyOCR → Tesseract)
  ↓
Entity Recognition (8 field types, confidence scoring)
  ↓
Structured Output (RAG-ready format)
```

**Modules**:
1. `image_preprocessor.py` (310 lines) - Image optimization
2. `ocr_engine.py` (450 lines) - Multi-engine with fallback
3. `pdf_extractor.py` (140 lines) - PDF processing
4. `excel_parser.py` (220 lines) - Excel/CSV parsing
5. `entity_recognizer.py` (190 lines) - Entity extraction
6. `document_processor.py` (350 lines) - Unified processor
7. `__init__.py` - Module exports

#### §ocr.engines
**Engine Selection Strategy**: Confidence-based routing
**Location**: `src/core/ocr/ocr_engine.py`

```
Primary:   PaddleOCR (Korean, 85-90% accuracy, GPU)
Fallback:  EasyOCR (complex fonts, 80-85% accuracy)
Last Resort: Tesseract (basic text, 70-75% accuracy)
Threshold: 0.75 confidence for automatic switching
```

#### §ocr.entities
**Entity Types**: 8 fields with confidence scoring
**Location**: `src/core/ocr/entity_recognizer.py`

```
1. product_code   (confidence: 0.9-0.95)
2. product_name   (confidence: 0.85-0.90)
3. capacity       (confidence: 0.90-0.95)
4. neck           (confidence: 0.90-0.95)
5. material       (confidence: 0.85-0.90)
6. moq            (confidence: 0.85-0.90)
7. price          (confidence: 0.80-0.85)
8. supplier       (confidence: 0.75-0.80)
```

#### §ocr.usage
**Quick Start**: Basic usage examples
**Location**: `docs/OCR_QUICKSTART.md`

```python
from src.core.ocr import DocumentProcessor

processor = DocumentProcessor()
result = processor.process_file("product_catalog.pdf")
# Returns: {text, entities, confidence, metadata}
```

---

### §debug - Debug & Observability System

#### §debug.status
**Current State**: Complete (10 components) ✅
**Location**: `app/core/`, `app/middleware/`, `docs/DEBUG_SYSTEM.md`

#### §debug.architecture
**Complete Debug System**: Production observability
**Location**: `app/`

```
Request → Tracing Middleware → Performance Timing → Logging
            ↓                      ↓                    ↓
      Correlation ID         Duration Tracking     Structured Logs
            ↓                      ↓                    ↓
      Query Logger            Profiler            Exception Context
            ↓                      ↓                    ↓
      Debug API (8 endpoints)  Performance Summary  Error Reports
```

**Components**:
1. `core/config.py` - DebugConfig with feature flags
2. `core/logging.py` - ContextVar-based correlation IDs
3. `core/exceptions.py` - Context-aware exceptions
4. `core/profiler.py` - Checkpoint-based profiler
5. `core/query_logger.py` - In-memory query log
6. `middleware/request_tracing.py` - Correlation ID injection
7. `middleware/performance_timing.py` - Duration tracking
8. `middleware/request_logging.py` - Structured logging
9. `api/v1/debug.py` - 8 debug endpoints
10. `main.py` - Full integration

#### §debug.features
**Key Capabilities**: Production debugging tools
**Location**: `app/core/`, `app/middleware/`

```
✓ Request Tracing: UUID-based correlation IDs
✓ Performance Profiling: Checkpoint-based with bottleneck detection
✓ Query Logging: In-memory log with slow query detection (>100ms)
✓ Structured Logging: JSON format with context propagation
✓ Exception Context: Full traceback + context dict
✓ Debug Endpoints: 8 endpoints for real-time inspection
```

#### §debug.endpoints
**Debug API**: 8 production endpoints
**Location**: `app/api/v1/debug.py`, `docs/API_DOCUMENTATION.md`

```
POST   /api/v1/debug/search/explain      - Search result explanation
GET    /api/v1/debug/profile/{session}   - User profile inspector
GET    /api/v1/debug/cache/stats          - Cache statistics
GET    /api/v1/debug/qdrant/stats         - Vector DB statistics
GET    /api/v1/debug/queries/recent       - Recent query log
GET    /api/v1/debug/performance/summary  - Performance metrics
GET    /api/v1/debug/health/detailed      - Detailed health check
POST   /api/v1/debug/cache/clear          - Clear cache
```

#### §debug.usage
**Quick Start**: Using debug features
**Location**: `docs/DEBUG_SYSTEM.md`

```python
# Auto-injection via middleware
from app.core.logging import correlation_id_var

correlation_id = correlation_id_var.get()  # Current request ID

# Performance profiling
from app.core.profiler import RequestProfiler

with RequestProfiler("operation") as profiler:
    profiler.checkpoint("step1")
    # ... work ...
    profiler.checkpoint("step2")
    summary = profiler.get_summary()  # Get bottlenecks
```

#### §debug.config
**Configuration**: Environment variables
**Location**: `.env.example`

```bash
DEBUG_ENABLED=true
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=true
DEBUG_LOG_SQL=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=300
```

---

### §deploy - Deployment & Infrastructure

#### §deploy.status
**Current State**: Production-ready ✅
**Infrastructure**: Docker + K8s manifests
**Location**: `scripts/`, `docs/DEPLOYMENT_GUIDE.md`

#### §deploy.quick
**Quick Start**: One-command deployment
**Location**: `scripts/deploy-optimized.sh`

```bash
# Development
./scripts/deploy-optimized.sh development

# Production
./scripts/deploy-optimized.sh production
```

#### §deploy.docker
**Docker Deployment**: Multi-environment support
**Location**: `docker-compose.yml`, `docker-compose.prod.yml`

```
Development:  docker-compose.yml (no resource limits)
Production:   docker-compose.prod.yml (resource limits, replicas)
```

**Services**:
- API (FastAPI) - ports: 8001
- Qdrant (vector DB) - ports: 6333
- Redis (cache) - ports: 6379
- PostgreSQL (database) - ports: 5432

#### §deploy.k8s
**Kubernetes Deployment**: Production orchestration
**Location**: `k8s/deployment.yaml`

```
API Deployment: 3 replicas, auto-scaling
ConfigMap: Environment variables
Secrets: Sensitive data
Services: LoadBalancer for API
Ingress: (optional) Domain routing
```

#### §deploy.cloud
**Cloud Platforms**: AWS, GCP, on-premises
**Location**: `docs/DEPLOYMENT_GUIDE.md`

```
AWS:    ECS/Fargate + RDS + ElastiCache + EC2 (Qdrant)
GCP:    GKE + Cloud SQL + Memorystore + GCE (Qdrant)
On-Prem: Docker Swarm/K8s + PostgreSQL + Redis + Qdrant cluster
```

#### §deploy.scripts
**Modular Scripts**: Reusable library functions
**Location**: `scripts/lib/`

```
scripts/lib/colors.sh  - Color output utilities
scripts/lib/health.sh  - Health check functions
scripts/lib/docker.sh  - Docker management
scripts/lib/test.sh    - Testing utilities
```

**Usage**:
```bash
source scripts/lib/colors.sh
print_success "Deployment complete"
```

---

### §test - Testing & Quality Assurance

#### §test.status
**Current State**: 122 test cases, 95%+ target ✅
**Location**: `tests/`, `scripts/test-optimized.sh`

#### §test.coverage
**Test Suite**: Comprehensive testing
**Location**: `tests/`

```
Unit Tests (77):
  - Repositories: 39 tests (Qdrant, Redis, PostgreSQL)
  - Services: 38 tests (Search, Personalization, Analytics)

Integration Tests (45):
  - API endpoints: 45 tests (Search, Personalization, Analytics, Debug)

Total: 122 test cases
Coverage Target: 95%+
```

#### §test.quick
**Quick Start**: One-command testing
**Location**: `scripts/test-optimized.sh`

```bash
./scripts/test-optimized.sh
```

**Test Phases**:
1. Infrastructure Health (Qdrant, Redis, PostgreSQL, API)
2. API Endpoints (health, docs)
3. Search API (text, image, hybrid)
4. Personalization API (profile, tracking)
5. Analytics API (keywords, trending)
6. Debug Endpoints (if enabled)
7. Python Test Suite (pytest)
8. OCR Pipeline (module validation)

#### §test.pytest
**Python Tests**: pytest with coverage
**Location**: `tests/`, `conftest.py`

```bash
pytest tests/ -v --cov=src --cov=app --cov-report=term-missing --cov-fail-under=95
```

**Fixtures**:
- Mock repositories (Qdrant, Redis, PostgreSQL)
- Mock services (Search, Personalization, Analytics)
- Sample data (products, users, queries)

#### §test.integration
**Integration Tests**: End-to-end API testing
**Location**: `tests/integration/`

```
test_search_api.py         - 14 tests
test_personalization_api.py - 12 tests
test_analytics_api.py       - 11 tests
test_debug_api.py           - 8 tests
```

---

### §arch - System Architecture

#### §arch.overview
**System Architecture**: Layered design
**Location**: `docs/ARCHITECTURE.md`, `docs/COMPLETION_REPORT.md`

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│              chat.html (v2.0.0 - ChatGPT-style)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  /search, /personalization, /analytics, /debug              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  SearchService, PersonalizationService, AnalyticsService    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                           │
│  QdrantRepository, RedisRepository, PostgresRepository      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│    Qdrant (vectors) + Redis (cache) + PostgreSQL (DB)      │
└─────────────────────────────────────────────────────────────┘
```

#### §arch.layers
**Layered Architecture**: Separation of concerns
**Location**: `docs/ARCHITECTURE.md`

```
1. Frontend: UI components (chat.html)
2. API: FastAPI endpoints (app/api/)
3. Service: Business logic (app/services/)
4. Repository: Data access (app/repositories/)
5. Data: Storage layer (Qdrant, Redis, PostgreSQL)
```

#### §arch.skills
**SKILL-Based Architecture**: Modular capabilities
**Location**: `.claude/skills/`

```
rag-pipeline           - Complete RAG workflow
manufacturing-expert   - Manufacturing domain
packaging-expert       - Packaging domain
web-crawler-pipeline   - Web data ingestion
```

---

### §api - API Reference

#### §api.endpoints
**Complete API**: 35+ production endpoints
**Location**: `docs/reference/API_DOCUMENTATION.md`

**Health** (2):
- GET `/health/live` - Liveness probe
- GET `/health/ready` - Readiness probe

**RAG Search** (3):
- POST `/api/v1/search/` - Text search
- POST `/api/v1/search/image` - Image search
- POST `/api/v1/search/hybrid` - Hybrid search

**Personalization** (2):
- POST `/api/v1/personalization/track` - Track interaction
- GET `/api/v1/personalization/profile/{session_id}` - Get profile

**Analytics** (3):
- GET `/api/v1/analytics/keywords` - Top keywords
- GET `/api/v1/analytics/trending` - Trending queries
- GET `/api/v1/analytics/summary` - Analytics summary

**SaaS Platform** (10+):
- POST `/api/v1/saas/auth/register` - Tenant registration
- POST `/api/v1/saas/auth/login` - User login
- POST `/api/v1/saas/api-keys` - Create API key
- GET `/api/v1/saas/api-keys` - List API keys
- DELETE `/api/v1/saas/api-keys/{key_id}` - Revoke API key
- GET `/api/v1/saas/billing/subscription` - Get subscription
- POST `/api/v1/saas/billing/upgrade` - Upgrade plan
- POST `/api/v1/saas/billing/cancel` - Cancel subscription
- GET `/api/v1/saas/usage/quota` - Check quota
- GET `/api/v1/saas/usage/stats` - Usage statistics
- GET `/api/v1/saas/tenants` - List tenants (admin)

**Manufacturing** (5+):
- POST `/api/v1/manufacturing/vision/inspect` - Vision inspection
- GET `/api/v1/manufacturing/defects` - Defect history
- GET `/api/v1/manufacturing/quality/spc` - SPC analysis
- POST `/api/v1/manufacturing/devices/register` - Register device
- GET `/api/v1/manufacturing/devices` - List devices

**Data Collector** (5+):
- POST `/api/v1/collector/collect` - Start collection
- GET `/api/v1/collector/jobs` - List jobs
- GET `/api/v1/collector/jobs/{job_id}` - Job status
- POST `/api/v1/collector/schedule` - Schedule job
- GET `/api/v1/collector/sources` - List sources

**Debug** (8):
- POST `/api/v1/debug/search/explain` - Search explanation
- GET `/api/v1/debug/profile/{session_id}` - Profile inspector
- GET `/api/v1/debug/cache/stats` - Cache statistics
- GET `/api/v1/debug/qdrant/stats` - Vector DB stats
- GET `/api/v1/debug/queries/recent` - Query log
- GET `/api/v1/debug/performance/summary` - Performance metrics
- GET `/api/v1/debug/health/detailed` - Detailed health
- POST `/api/v1/debug/cache/clear` - Clear cache

#### §api.docs
**Interactive Documentation**: Swagger UI + ReDoc
**Location**: Auto-generated from FastAPI

```
Swagger UI: http://localhost:8001/api/v1/docs
ReDoc:      http://localhost:8001/api/v1/redoc
```

---

### §ui - Frontend UI/UX

#### §ui.design
**Design System**: ChatGPT-style gray tones
**Location**: `frontend/chat.html`, `docs/FRONTEND_UI_POLICY.md`

**Colors**:
```
Background: #ffffff
Text:       #2d333a (primary), #6e6e80 (secondary)
Border:     #d1d5db
Hover:      #ececf1
```

**Layout**:
```
Max width: 768px
Full page chat
Input at bottom
Card grid: auto-fill 240px
```

#### §ui.version
**Current Version**: v2.0.0
**Status**: Production-ready ✅
**Location**: `frontend/chat.html`

---

### §ollama - Model Management

#### §ollama.production
**Production Models**: Fixed configuration
**Location**: `config/ollama_models.yaml`, `docs/OLLAMA_MODEL_POLICY.md`

```
qwen2.5:7b-instruct (4.7GB) - Main generation model
nomic-embed-text (274MB)    - Embeddings model
```

**Policy**: No changes without approval ⚠️

---

### §multimodal - Multi-Modal RAG

#### §multimodal.status
**Current State**: Strategy designed (Phase 6 준비 완료)
**Location**: `docs/MULTIMODAL_RAG_STRATEGY.md`

#### §multimodal.architecture
**Three-Modal Pipeline**: Text + Image + Shape
**Location**: `docs/MULTIMODAL_RAG_STRATEGY.md`

```
Text Embedding:  sentence-transformers/all-MiniLM-L6-v2 (384-dim)
Image Embedding: OpenCLIP ViT-H-14 (1024-dim)
Shape Embedding: Hu Moments + Fourier Descriptors (128-dim)
```

**Search Strategies**:
- Text-only: >85% accuracy @ Top-10
- Image-only: >80% accuracy @ Top-10
- Hybrid: >90% accuracy @ Top-10
- Tri-modal: Best accuracy (Phase 6)

---

### §saas - SaaS Platform (NEW v5.0.0)

#### §saas.status
**Current State**: Production-ready ✅
**Location**: `docs/SAAS_ARCHITECTURE.md`

```
✅ Multi-Tenancy: Row-Level Security (PostgreSQL)
✅ Authentication: JWT (24h expiration) + API keys (SHA-256 hashed)
✅ Billing: Stripe integration (webhooks, subscriptions, invoices)
✅ Usage Tracking: Redis (counters) + PostgreSQL (analytics)
✅ Plans: Free ($0), Pro ($49/mo), Enterprise ($499/mo)
```

#### §saas.auth
**Authentication System**: JWT + API Key dual auth
**Location**: `src/core/auth/`, `src/api/v1/saas.py`

**Components**:
```
JWT Handler:
  - Token generation (24h expiration)
  - Signature verification (HS256)
  - Claims validation (exp, iat, sub, tenant_id)

API Key Handler:
  - SHA-256 hashing (one-way)
  - Tenant-scoped keys
  - Automatic key rotation support
```

**Usage**:
```python
# JWT authentication
from src.core.auth.jwt_handler import create_access_token, verify_token

token = create_access_token(user_id="user-123", tenant_id="tenant-456")
payload = verify_token(token)  # Returns: {user_id, tenant_id, exp, iat}

# API key authentication
from src.core.auth.api_key_handler import generate_api_key, verify_api_key

key = generate_api_key(tenant_id="tenant-456")  # Returns: plain key (show once!)
is_valid = verify_api_key(key, tenant_id="tenant-456")  # Returns: True/False
```

#### §saas.billing
**Billing System**: Stripe integration
**Location**: `src/services/billing_service.py`

**Features**:
```
Subscription Management:
  - Create subscription (Free → Pro/Enterprise)
  - Upgrade/downgrade plans
  - Cancel subscription (end of billing period)
  - Billing period: monthly/yearly

Webhook Handling:
  - subscription.created
  - subscription.updated
  - invoice.payment_succeeded
  - invoice.payment_failed

Invoice Generation:
  - Automatic invoicing
  - Payment status tracking
  - Stripe dashboard integration
```

**Plans**:
```
Free:       $0/mo    - 1,000 API calls/month, 1GB storage, 1 user
Pro:        $49/mo   - 100K API calls/month, 50GB storage, 10 users
Enterprise: $499/mo  - Unlimited calls, 500GB storage, unlimited users
```

#### §saas.usage
**Usage Tracking System**: Dual-storage architecture
**Location**: `src/services/usage_tracker.py`

**Architecture**:
```
Redis (Fast Counters):
  - usage:{tenant_id}:{date}:api_calls
  - usage:{tenant_id}:{date}:storage_bytes
  - rate_limit:{tenant_id}:{window}

PostgreSQL (Long-term Analytics):
  - api_usage table (tenant_id, endpoint, timestamp, status, response_time)
  - storage_usage table (tenant_id, date, bytes_used)
  - Monthly aggregation for billing
```

**Features**:
```
API Call Tracking:
  - Per-endpoint metrics
  - Response time tracking
  - Status code distribution

Quota Enforcement:
  - Free: 1K calls/month
  - Pro: 100K calls/month
  - Enterprise: Unlimited

Rate Limiting (sliding window):
  - Free: 10 req/min
  - Pro: 100 req/min
  - Enterprise: 1000 req/min
```

#### §saas.tenants
**Multi-Tenancy System**: PostgreSQL Row-Level Security
**Location**: `docs/SAAS_ARCHITECTURE.md`

**Database Schema**:
```sql
tenants:
  - id (UUID), name, domain, plan_tier, stripe_customer_id

users:
  - id (UUID), tenant_id (FK), email, hashed_password, role

api_keys:
  - id (UUID), tenant_id (FK), key_hash (SHA-256), name, created_at

subscriptions:
  - id (UUID), tenant_id (FK), stripe_subscription_id, status, plan_tier
```

**Row-Level Security**:
```sql
CREATE POLICY tenant_isolation ON users
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

---

### §collector - Data Collector (NEW v5.0.0)

#### §collector.status
**Current State**: Architecture complete ✅
**Location**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`

```
✅ Web Scraping: BeautifulSoup + Playwright + Selenium
✅ API Polling: OAuth2, retry logic, pagination
✅ File Parsing: 6 formats (CSV, Excel, PDF, JSON, XML, HTML)
✅ Processing Pipeline: Validation → Cleaning → Transformation → Enrichment
✅ Database Integration: PostgreSQL + Qdrant + MinIO
✅ Scheduling: APScheduler (cron triggers, daily jobs)
```

#### §collector.pipeline
**Complete Data Pipeline**: Collection → Processing → DB
**Location**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`

```
┌─────────────┐
│  Collection │ (Web Scraper, API Poller, File Parser)
└──────┬──────┘
       ↓
┌─────────────┐
│  Processing │ (Validation → Cleaning → Transformation → Enrichment)
└──────┬──────┘
       ↓
┌─────────────┐
│  Database   │ (PostgreSQL + Qdrant + MinIO)
└─────────────┘
```

**Processing Steps**:
1. **Validation**: Schema validation, required fields, data types
2. **Cleaning**: Remove duplicates, trim whitespace, normalize text
3. **Transformation**: Format conversion, field mapping, standardization
4. **Entity Extraction**: NER (product codes, capacities, materials)
5. **Enrichment**: Add metadata, external lookups, classification

**Error Handling**:
- Skip: Continue processing (log error)
- Stop: Halt pipeline (critical failure)
- Retry: Exponential backoff (3 attempts)

#### §collector.sources
**Collection Sources**: Multi-source support
**Location**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`

**Web Scraping**:
```
BeautifulSoup:  Static HTML parsing (fast, low resource)
Playwright:     Dynamic JS rendering (async, headless Chrome)
Selenium:       Complex interactions (form submission, navigation)

Features:
  - User-agent rotation
  - Rate limiting (respectful crawling)
  - Retry with exponential backoff
  - Proxy support (optional)
```

**API Polling**:
```
Protocols: REST, GraphQL
Auth: OAuth2, API keys, Basic auth
Features:
  - Pagination handling (offset, cursor, page-based)
  - Rate limit respect (429 retry)
  - Response caching
  - Webhook support (optional)
```

**File Parsing**:
```
Formats: CSV, Excel (.xlsx), PDF, JSON, XML, HTML
Libraries:
  - pandas (CSV, Excel)
  - openpyxl (Excel advanced)
  - PyPDF2 (PDF text extraction)
  - lxml (XML parsing)
```

#### §collector.scheduling
**Job Scheduling**: APScheduler
**Location**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`

**Schedule Types**:
```
Cron Triggers:
  - Daily: "0 2 * * *" (2 AM daily)
  - Weekly: "0 2 * * 0" (2 AM Sunday)
  - Monthly: "0 2 1 * *" (2 AM 1st of month)

Interval Triggers:
  - Every N hours: IntervalTrigger(hours=6)
  - Every N minutes: IntervalTrigger(minutes=30)
```

**Job Management**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    collect_data,
    trigger='cron',
    hour=2,
    minute=0,
    id='daily_collection'
)
scheduler.start()
```

---

### §manufacturing - Manufacturing Automation (NEW v5.0.0)

#### §manufacturing.status
**Current State**: Architecture complete ✅
**Location**: `docs/MANUFACTURING_AUTOMATION.md`

```
✅ Vision Inspection: YOLOv8/v10 defect detection (7 types)
✅ Edge Devices: Jetson Orin Nano (120 FPS), Raspberry Pi 4 (15 FPS)
✅ Quality Control: SPC, defect trends, alert system
✅ Communication: MQTT (edge → server), REST API
✅ Models: TensorRT (Jetson), ONNX (Pi)
```

#### §manufacturing.vision
**Vision Inspection System**: AI-powered defect detection
**Location**: `docs/MANUFACTURING_AUTOMATION.md`

**Defect Types** (7):
```
1. Scratch     - Surface scratches, abrasions
2. Crack       - Cracks, fissures
3. Deformation - Shape defects, warping
4. Discolor    - Color variations, stains
5. Contamination - Foreign particles, dirt
6. Bubble      - Air bubbles, voids
7. Incomplete  - Missing parts, incomplete molding
```

**Models**:
```
YOLOv8:  Fast detection (80-120 FPS)
YOLOv10: Higher accuracy (60-100 FPS)
Training: 10K+ labeled images, data augmentation
Metrics: >95% precision, >92% recall
```

#### §manufacturing.devices
**Edge Devices**: Hardware deployment options
**Location**: `docs/MANUFACTURING_AUTOMATION.md`

**Jetson Orin Nano** ($499):
```
Performance: 120 FPS (TensorRT INT8)
GPU: 1024-core NVIDIA Ampere
RAM: 8GB LPDDR5
Power: 15W
Inference: TensorRT optimized models
```

**Raspberry Pi 4** ($55):
```
Performance: 15 FPS (ONNX)
CPU: Quad-core Cortex-A72
RAM: 4GB/8GB
Power: 5W
Inference: ONNX Runtime (CPU)
```

#### §manufacturing.quality
**Quality Control System**: Statistical Process Control
**Location**: `docs/MANUFACTURING_AUTOMATION.md`

**SPC Metrics**:
```
Control Charts:
  - X-bar (mean defect rate)
  - R-chart (range, variance)
  - p-chart (proportion defective)

Control Limits:
  - UCL (Upper Control Limit) = mean + 3σ
  - LCL (Lower Control Limit) = mean - 3σ

Alerts:
  - Out-of-control condition (exceeds limits)
  - Trend detection (7+ consecutive points)
  - Run detection (pattern analysis)
```

**Defect Analysis**:
```
Pareto Analysis: 80/20 rule (top defect types)
Trend Analysis: Time-series forecasting
Root Cause: Correlation with process parameters
```

---

## 🎯 Symbol Usage Guide

### When to Load Full Documents

| Symbol | Load When | Document |
|--------|-----------|----------|
| §rag.* | RAG development, search optimization | RAG_ACTIVATION_STRATEGY.md |
| §saas.* | SaaS development, billing, multi-tenancy | SAAS_ARCHITECTURE.md |
| §collector.* | Data ingestion, pipeline setup | DATA_COLLECTOR_ARCHITECTURE.md |
| §manufacturing.* | Vision inspection, quality control | MANUFACTURING_AUTOMATION.md |
| §ocr.* | OCR implementation, document processing | OCR_PARSING_STRATEGY.md |
| §debug.* | Debugging, observability, monitoring | DEBUG_SYSTEM.md |
| §deploy.* | Deployment, infrastructure setup | DEPLOYMENT_GUIDE.md |
| §test.* | Testing, quality assurance | Test files, scripts |
| §api.* | API development, endpoint changes | API_DOCUMENTATION.md |
| §arch.* | Architecture design, system integration | ARCHITECTURE.md |
| §ui.* | Frontend development, design changes | FRONTEND_UI_POLICY.md |

### Quick Reference Pattern

```bash
# Pattern: §{domain}.{component}
§rag.core              # Core RAG modules
§saas.auth             # SaaS authentication
§collector.pipeline    # Data collection pipeline
§manufacturing.vision  # Vision inspection system
§ocr.pipeline          # OCR pipeline flow
§debug.endpoints       # Debug API endpoints
§deploy.quick          # Quick deployment
§test.coverage         # Test coverage details
```

---

## 📚 Document Index

| Document | Size | Symbols | Purpose |
|----------|------|---------|---------|
| CLAUDE.md | ~500 lines | All | Quick reference (v5.0.0) |
| SYMBOLS.md | ~1000 lines | All | Complete symbol map (v5.0.0) |
| **SAAS_ARCHITECTURE.md** | **35KB** | **§saas.*** | **SaaS platform (NEW)** |
| **DATA_COLLECTOR_ARCHITECTURE.md** | **30KB** | **§collector.*** | **Data collection (NEW)** |
| **MANUFACTURING_AUTOMATION.md** | **40KB** | **§manufacturing.*** | **Manufacturing (NEW)** |
| API_DOCUMENTATION.md | 30KB | §api.* | API reference (35+ endpoints) |
| DEPLOYMENT_GUIDE.md | 30KB | §deploy.* | Deployment guide |
| DEBUG_SYSTEM.md | 15KB | §debug.* | Debug system |
| OCR_PARSING_STRATEGY.md | 50KB | §ocr.* | OCR architecture |
| MULTIMODAL_RAG_STRATEGY.md | 80KB | §multimodal.* | Multi-modal RAG |
| NEXA_SDK_INTEGRATION_PLAN.md | 45KB | §rag.engines | NexaAI + Ollama routing |
| ARCHITECTURE.md | 31KB | §arch.* | System architecture |

---

## 🔄 Symbol Maintenance

**Update Frequency**:
- After major features: Update relevant § symbols
- After phase completion: Update §{phase}.status
- After API changes: Update §api.endpoints
- Monthly: Review and optimize symbol map

**Guidelines**:
1. Keep symbols concise (2-3 levels max)
2. Reference instead of duplicating
3. Update SYMBOLS.md when adding new domains
4. Test all symbol references before committing

---

**Last Updated**: 2025-11-08
**Version**: v5.0.0
**Status**: Enterprise Platform Complete ✅
**New Modules**: §saas, §collector, §manufacturing
