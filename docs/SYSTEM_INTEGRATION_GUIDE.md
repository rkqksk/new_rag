# System Integration Guide - Complete Enterprise Platform

**Unified platform: RAG + SaaS + Manufacturing Automation + Data Collection**

---

## Table of Contents

1. [Overview](#overview)
2. [Complete Architecture](#complete-architecture)
3. [Module Integration](#module-integration)
4. [Data Flow](#data-flow)
5. [Deployment Scenarios](#deployment-scenarios)
6. [API Reference](#api-reference)
7. [Use Cases](#use-cases)

---

## Overview

### Complete Platform Stack

```
Enterprise RAG Platform
├── Core RAG System
│   ├── Semantic Search (Qdrant, 384/1024/128-dim)
│   ├── LLM Engines (NexaAI + Ollama)
│   ├── OCR Pipeline (PaddleOCR + EasyOCR + Tesseract)
│   └── Multi-Modal RAG (Text + Image + Shape)
├── SaaS Platform
│   ├── Multi-Tenancy (Row-Level Security)
│   ├── Authentication (JWT + API Keys)
│   ├── Billing (Stripe Integration)
│   ├── Usage Tracking & Quotas
│   └── Admin Dashboard
├── Manufacturing Automation
│   ├── YOLO Vision Inspection (YOLOv8/v10)
│   ├── Edge AI (Jetson Orin Nano / Raspberry Pi)
│   ├── Quality Control (SPC, Defect Detection)
│   └── Real-time Monitoring (MQTT, WebSocket)
├── External Integrations
│   ├── Data Collector (Web Scraping, API Polling)
│   ├── Manufacturing Surveillance (Quality Monitoring)
│   └── Third-party APIs
└── Deployment
    ├── Free: Streamlit Cloud, HuggingFace Spaces
    ├── Mid-tier: Railway, Render, Fly.io
    └── Enterprise: AWS, GCP, DigitalOcean + Cloudflare
```

---

## Complete Architecture

### System Topology

```
┌───────────────────────────────────────────────────────────────────┐
│                        Client Layer                                │
├───────────────────────────────────────────────────────────────────┤
│  Web UI  │  Mobile App  │  External APIs  │  Edge Devices        │
└────┬──────────┬──────────────┬─────────────────┬──────────────────┘
     │          │              │                 │
     └──────────┴──────────────┴─────────────────┘
                       ↓
┌───────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                             │
├───────────────────────────────────────────────────────────────────┤
│  - Authentication (JWT/API Key)                                   │
│  - Rate Limiting (per plan tier)                                  │
│  - Tenant Detection (subdomain/header)                            │
│  - Request Logging                                                │
└────┬──────────────────────────────────────────────────────────────┘
     │
     ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Application Layer (FastAPI)                     │
├───────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐             │
│  │  RAG API    │  │  SaaS API   │  │  Mfg API     │             │
│  │  /search    │  │  /tenants   │  │  /inspection │             │
│  │  /ingest    │  │  /billing   │  │  /devices    │             │
│  └─────────────┘  └─────────────┘  └──────────────┘             │
└────┬──────────────────────┬──────────────────┬────────────────────┘
     │                      │                  │
     ↓                      ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  RAG Service │  │ Billing Svc  │  │  Vision Svc  │
│  - Search    │  │ - Stripe     │  │  - YOLO      │
│  - Ingest    │  │ - Quotas     │  │  - SPC       │
│  - OCR       │  │ - Usage      │  │  - Alerts    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       ↓                 ↓                  ↓
┌───────────────────────────────────────────────────────────────────┐
│                        Data Layer                                  │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │ PostgreSQL   │  │   Qdrant    │  │    Redis     │            │
│  │ (Tenants,    │  │  (Vectors)  │  │   (Cache,    │            │
│  │  Users,      │  │             │  │    Quotas)   │            │
│  │  Invoices)   │  │             │  │              │            │
│  └──────────────┘  └─────────────┘  └──────────────┘            │
│                                                                    │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │   MinIO      │  │   Ollama    │  │   MQTT       │            │
│  │  (Images)    │  │   (LLM)     │  │ (Edge Msgs)  │            │
│  └──────────────┘  └─────────────┘  └──────────────┘            │
└───────────────────────────────────────────────────────────────────┘
       ↑                                          ↑
       │                                          │
┌──────┴────────────┐                   ┌────────┴──────────┐
│  Data Collector   │                   │  Edge Devices     │
│  - Web Scraping   │                   │  - Jetson Orin    │
│  - API Polling    │                   │  - Raspberry Pi   │
│  - Excel Parsing  │                   │  - YOLO Vision    │
└───────────────────┘                   └───────────────────┘
```

---

## Module Integration

### 1. RAG + SaaS Integration

**Tenant-specific Search**:
```python
# src/api/v1/search.py

from fastapi import APIRouter, Depends
from src.core.auth.api_key_handler import get_current_tenant
from src.core.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("/")
async def search(
    query: str,
    top_k: int = 5,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Multi-tenant search with usage tracking

    Automatically:
    - Filters by tenant_id
    - Tracks API usage
    - Enforces quotas
    """

    # Check quota
    from src.services.usage_tracker import UsageTracker
    tracker = UsageTracker()

    quota_status = tracker.check_quota(tenant_id)
    if not quota_status["within_quota"]:
        raise HTTPException(
            status_code=429,
            detail=f"Quota exceeded ({quota_status['current_usage']}/{quota_status['quota_limit']} API calls this month)"
        )

    # Perform search (tenant-filtered)
    rag = RAGPipeline()
    results = await rag.search(
        query=query,
        top_k=top_k,
        tenant_id=tenant_id  # Filter by tenant
    )

    # Track usage
    tracker.track_api_call(
        tenant_id=tenant_id,
        endpoint="/search",
        response_time_ms=0  # Calculate actual time
    )

    return {"results": results}
```

**Tenant-isolated Vector Collections**:
```python
# src/core/rag_pipeline.py

from qdrant_client import QdrantClient, models

class RAGPipeline:
    def __init__(self):
        self.qdrant = QdrantClient(host="localhost", port=6333)

    async def search(
        self,
        query: str,
        top_k: int,
        tenant_id: str
    ):
        """Search with tenant isolation"""

        # Option 1: Separate collection per tenant
        collection_name = f"tenant_{tenant_id}_products"

        # Option 2: Shared collection with tenant filter
        collection_name = "products_all"
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=tenant_id)
                )
            ]
        )

        # Perform search
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=self.encode(query),
            query_filter=query_filter,  # Tenant isolation
            limit=top_k
        )

        return results
```

---

### 2. RAG + Manufacturing Integration

**Product Spec Lookup During Inspection**:
```python
# src/services/inspection_service.py

from src.core.rag_pipeline import RAGPipeline

class InspectionService:
    def __init__(self):
        self.rag = RAGPipeline()

    async def process_inspection_result(
        self,
        device_id: str,
        product_code: str,
        defect_type: str,
        confidence: float
    ):
        """
        Process vision inspection result with RAG lookup

        Flow:
        1. Receive inspection result from edge device
        2. Look up product specs using RAG
        3. Validate against quality requirements
        4. Determine pass/fail
        5. Send alert if needed
        """

        # 1. Look up product specs
        spec_results = await self.rag.search(
            query=f"Product {product_code} specifications quality requirements",
            top_k=3
        )

        if not spec_results:
            # No spec found - default to fail
            return {
                "pass": False,
                "reason": "No product specification found",
                "action": "manual_review"
            }

        spec = spec_results[0].payload

        # 2. Get quality requirements
        requirements = spec.get("quality_requirements", {})
        max_defect_size = requirements.get(f"max_{defect_type}_size_mm", 0)

        # 3. Determine pass/fail
        pass_inspection = confidence < 0.8 or max_defect_size > 0

        # 4. Return result
        return {
            "pass": pass_inspection,
            "product_code": product_code,
            "product_name": spec.get("product_name"),
            "defect_type": defect_type,
            "confidence": confidence,
            "max_allowed": max_defect_size,
            "severity": "minor" if pass_inspection else "major",
            "action": "proceed" if pass_inspection else "reject"
        }
```

---

### 3. Data Collector + RAG Integration

**Automated Data Ingestion Pipeline**:
```python
# src/integrations/data_collector_pipeline.py

from src.integrations.data_collector_client import DataCollectorClient
from src.core.rag_pipeline import RAGPipeline

class DataCollectorPipeline:
    """
    Automated pipeline: Data Collection → RAG Ingestion

    Workflow:
    1. Data Collector scrapes product data
    2. Publishes to message queue (Redis Pub/Sub)
    3. RAG subscribes and ingests
    4. Vectors indexed in Qdrant
    """

    def __init__(self):
        self.collector = DataCollectorClient()
        self.rag = RAGPipeline()
        self.redis = redis.Redis()

    async def collect_and_ingest(
        self,
        source: str,
        tenant_id: str
    ):
        """
        Collect data from source and ingest into RAG

        Args:
            source: Data source (e.g., "chunjinkorea", "onehago")
            tenant_id: Tenant ID for multi-tenancy
        """

        # 1. Trigger data collection
        products = await self.collector.collect_products(source)

        # 2. Ingest into RAG (batch)
        await self.rag.ingest_batch(
            documents=products,
            tenant_id=tenant_id  # Tenant isolation
        )

        # 3. Publish event
        self.redis.publish('data.ingested', json.dumps({
            "source": source,
            "tenant_id": tenant_id,
            "count": len(products),
            "timestamp": datetime.utcnow().isoformat()
        }))

        return {
            "status": "success",
            "ingested": len(products)
        }

# Background job (APScheduler)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=24)
async def daily_data_collection():
    """Run data collection daily"""
    pipeline = DataCollectorPipeline()

    sources = ["chunjinkorea", "onehago", "freemold"]

    for source in sources:
        await pipeline.collect_and_ingest(
            source=source,
            tenant_id="system"  # Or per-tenant
        )

scheduler.start()
```

---

### 4. Manufacturing Surveillance + RAG

**Quality Trend Analysis**:
```python
# src/services/surveillance_service.py

from src.core.rag_pipeline import RAGPipeline

class SurveillanceService:
    """
    Manufacturing surveillance with RAG integration

    Features:
    - Defect trend analysis
    - Historical data lookup
    - Anomaly detection
    - Alert management
    """

    def __init__(self):
        self.rag = RAGPipeline()

    async def analyze_defect_trend(
        self,
        product_code: str,
        time_range_days: int = 7
    ):
        """
        Analyze defect trends and compare with historical data

        Uses RAG to:
        - Look up historical defect rates
        - Compare current trends
        - Identify anomalies
        """

        # 1. Get current defect rate
        current_rate = self.get_current_defect_rate(product_code, days=1)

        # 2. Look up historical data via RAG
        history_results = await self.rag.search(
            query=f"Product {product_code} defect rate history quality trends",
            top_k=10
        )

        historical_rates = [r.payload.get("defect_rate") for r in history_results]
        avg_historical_rate = sum(historical_rates) / len(historical_rates)

        # 3. Detect anomaly
        is_anomaly = current_rate > avg_historical_rate * 1.5

        return {
            "product_code": product_code,
            "current_rate": current_rate,
            "historical_avg": avg_historical_rate,
            "is_anomaly": is_anomaly,
            "severity": "high" if is_anomaly else "normal",
            "recommendation": "Investigate process changes" if is_anomaly else "Continue monitoring"
        }
```

---

## Data Flow

### End-to-End Data Pipeline

```
[Data Collection]
    │
    ├→ Web Scraping (data_collector)
    ├→ API Polling (data_collector)
    ├→ Manual Upload (Admin UI)
    │
    ↓
[Data Normalization]
    │
    ├→ Field Extraction
    ├→ Entity Recognition
    ├→ Deduplication
    │
    ↓
[RAG Ingestion]
    │
    ├→ Text Chunking (Atomic + Field-based)
    ├→ OCR Processing (PaddleOCR)
    ├→ Entity Extraction (8 types)
    │
    ↓
[Embedding Generation]
    │
    ├→ Text Embeddings (384-dim, all-MiniLM-L6-v2)
    ├→ Image Embeddings (1024-dim, CLIP)
    ├→ Shape Embeddings (128-dim, Custom)
    │
    ↓
[Vector Storage]
    │
    ├→ Qdrant Collections (tenant-isolated)
    ├→ PostgreSQL Metadata
    ├→ MinIO Images
    │
    ↓
[Search & Retrieval]
    │
    ├→ Semantic Search
    ├→ Filtered Search
    ├→ Hybrid Search (Text + Image + Shape)
    │
    ↓
[Application Integration]
    │
    ├→ Manufacturing Inspection (Product Spec Lookup)
    ├→ Quality Control (Historical Comparison)
    ├→ Customer Search (Web UI)
    ├→ API Access (External Apps)
    │
    ↓
[Analytics & Monitoring]
    │
    ├→ Usage Tracking (API calls, storage)
    ├→ SPC Analysis (Defect trends)
    ├→ Billing (Stripe)
    └→ Dashboard (Grafana/Custom)
```

---

## Deployment Scenarios

### Scenario 1: Small Business (Free/Low-Cost)

**Requirements**:
- 1-10 users
- Basic search functionality
- Limited manufacturing automation

**Deployment**:
```
Frontend: Streamlit Cloud (Free)
Backend API: Railway ($13/mo)
Vector DB: Qdrant Cloud Free Tier (1GB)
Database: Railway PostgreSQL (included)
LLM: Ollama (local, self-hosted)
Edge Devices: 0-2 Raspberry Pi 4
Total Cost: $13/mo
```

---

### Scenario 2: Growing Company (Mid-Tier)

**Requirements**:
- 10-50 users
- Full RAG capabilities
- 5-10 inspection stations
- Basic SaaS features

**Deployment**:
```
Frontend: Cloudflare Pages (Free)
Backend API: DigitalOcean Droplet 4GB ($24/mo)
Vector DB: Self-hosted Qdrant (on same droplet)
Database: DigitalOcean Managed PostgreSQL ($15/mo)
Redis: DigitalOcean Managed Redis ($15/mo)
LLM: Ollama + NexaAI (local GPU)
Edge Devices: 5-10 Jetson Orin Nano
Total Cost: $54/mo + hardware
```

---

### Scenario 3: Enterprise (High Scale)

**Requirements**:
- 100+ users
- Multi-tenancy
- 20+ inspection stations
- Full SaaS platform

**Deployment**:
```
Frontend: Cloudflare Workers ($5/mo) + CDN
Backend API: AWS ECS Fargate ($150/mo)
Vector DB: Qdrant Cloud Pro ($100/mo)
Database: AWS RDS PostgreSQL ($100/mo)
Redis: AWS ElastiCache ($50/mo)
Storage: AWS S3 ($20/mo)
LLM: NexaAI Cloud + Ollama (GPU instances)
Edge Devices: 20+ Jetson Orin Nano/Xavier
Load Balancer: AWS ALB ($18/mo)
Monitoring: Datadog ($30/mo)
Total Cost: $473/mo + hardware + GPU costs
```

---

## API Reference

### Unified API Structure

```
/api/v1/
├── auth/
│   ├── POST /login              # JWT login
│   ├── POST /register           # User registration
│   └── POST /refresh            # Refresh token
├── tenants/
│   ├── GET  /                   # List tenants (admin)
│   ├── POST /                   # Create tenant
│   ├── GET  /{id}              # Get tenant
│   └── PUT  /{id}              # Update tenant
├── search/
│   ├── POST /                   # Semantic search
│   ├── POST /hybrid             # Hybrid search
│   └── POST /image              # Image similarity search
├── ingest/
│   ├── POST /document           # Ingest single document
│   ├── POST /batch              # Batch ingest
│   └── POST /ocr                # OCR + ingest
├── manufacturing/
│   ├── GET  /devices            # List edge devices
│   ├── POST /inspection         # Record inspection result
│   ├── GET  /defects            # Get defect statistics
│   └── GET  /spc                # SPC analysis
├── billing/
│   ├── GET  /subscription       # Current subscription
│   ├── POST /upgrade            # Upgrade plan
│   ├── GET  /invoices           # List invoices
│   └── GET  /usage              # Usage statistics
└── admin/
    ├── GET  /stats              # System statistics
    ├── GET  /health             # Health check
    └── POST /maintenance        # Maintenance mode
```

---

## Use Cases

### Use Case 1: Automated Quality Control

**Scenario**: Packaging factory with 10 inspection stations

**Workflow**:
1. Product arrives at inspection station
2. Camera captures image
3. Jetson Orin Nano runs YOLO inference
4. Defect detected → Look up product spec via RAG
5. Compare against quality requirements
6. Pass/Fail decision
7. Log result to PostgreSQL
8. Update dashboard in real-time
9. If high defect rate detected → Alert supervisor

**Technologies Used**:
- Edge: Jetson Orin Nano + YOLOv8
- Communication: MQTT
- Spec Lookup: RAG (Qdrant)
- Analytics: SPC Service
- Monitoring: Grafana Dashboard

---

### Use Case 2: Multi-Tenant Product Search SaaS

**Scenario**: B2B SaaS platform for packaging suppliers

**Workflow**:
1. Customer (Tenant A) logs in
2. Searches for "50ml PET bottle"
3. API authenticates via JWT
4. Checks usage quota
5. RAG performs semantic search (tenant-filtered)
6. Returns top 5 results
7. Tracks API usage
8. Updates billing metrics
9. Customer downloads product specs

**Technologies Used**:
- Auth: JWT + API Keys
- Search: RAG Pipeline
- Multi-tenancy: RLS in PostgreSQL
- Billing: Stripe
- Usage Tracking: Redis + PostgreSQL

---

### Use Case 3: Data Collection + RAG Pipeline

**Scenario**: Daily product catalog updates

**Workflow**:
1. Scheduler triggers at 2:00 AM
2. Data Collector scrapes 5 websites
3. Normalizes and deduplicates data
4. Publishes to Redis Pub/Sub
5. RAG subscriber processes batch
6. OCR extracts text from Excel screenshots
7. Chunks documents atomically
8. Generates embeddings
9. Indexes in Qdrant (tenant-specific collections)
10. Sends completion notification

**Technologies Used**:
- Scheduler: APScheduler
- Scraping: Data Collector module
- OCR: PaddleOCR
- Messaging: Redis Pub/Sub
- Indexing: RAG Pipeline + Qdrant

---

## Best Practices

### 1. Security

- ✅ Use Row-Level Security (RLS) for multi-tenancy
- ✅ Hash API keys before storage
- ✅ Rotate JWT secrets regularly
- ✅ Implement rate limiting per tenant
- ✅ Use HTTPS everywhere
- ✅ Sanitize all user inputs

### 2. Performance

- ✅ Cache frequent queries (Redis)
- ✅ Use connection pooling
- ✅ Batch database operations
- ✅ Enable Qdrant quantization
- ✅ Use TensorRT for YOLO on Jetson
- ✅ Implement pagination

### 3. Monitoring

- ✅ Track API latency (P50, P95, P99)
- ✅ Monitor defect rates (SPC)
- ✅ Set up alerts for quota overages
- ✅ Log all authentication attempts
- ✅ Monitor edge device health
- ✅ Track billing metrics

### 4. Scalability

- ✅ Design for horizontal scaling
- ✅ Use message queues for async operations
- ✅ Implement caching layers
- ✅ Partition large databases
- ✅ Use CDN for static assets
- ✅ Load balance API requests

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
