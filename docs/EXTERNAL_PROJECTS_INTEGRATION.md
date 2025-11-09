# External Projects Integration Framework

**Modular integration guide for data_collector and manufacturing-surveillance projects**

---

## Table of Contents

1. [Overview](#overview)
2. [Integration Patterns](#integration-patterns)
3. [Data Collector Integration](#data-collector-integration)
4. [Manufacturing Surveillance Integration](#manufacturing-surveillance-integration)
5. [Pipeline Architecture](#pipeline-architecture)
6. [Implementation Guide](#implementation-guide)
7. [API Contracts](#api-contracts)

---

## Overview

### Integration Strategy

This document provides a framework for integrating external projects into RAG Enterprise using **modular, loosely-coupled architecture**.

**Target Projects**:
- **data_collector**: https://github.com/rkqksk/data_collector
- **manufacturing-surveillance**: https://github.com/rkqksk/manufacturing-surveillance

**Integration Approaches**:
1. **Pipeline Integration**: Chained data flow (collector → RAG → surveillance)
2. **Modular Integration**: Embedded as packages/services
3. **API Integration**: RESTful communication
4. **Event-Driven**: Message queue (RabbitMQ, Redis Pub/Sub)

---

## Integration Patterns

### Pattern 1: Pipeline Integration (Recommended)

```
[Data Collector] → [RAG Enterprise] → [Manufacturing Surveillance]
      ↓                   ↓                      ↓
  Web Scraping        Semantic Search      Quality Monitoring
  Excel Parsing       Vector Indexing      Anomaly Detection
  API Polling         Entity Extraction    Alert System
```

**Flow**:
1. **Data Collector** scrapes/polls data → sends to RAG Enterprise
2. **RAG Enterprise** processes, indexes, searches → sends results to Surveillance
3. **Manufacturing Surveillance** monitors quality, detects anomalies

**Pros**:
- ✅ Clear separation of concerns
- ✅ Easy to test each stage
- ✅ Can swap implementations

**Cons**:
- ❌ More network overhead
- ❌ Need to manage 3 services

---

### Pattern 2: Modular Integration

```
RAG Enterprise
├── src/
│   ├── modules/
│   │   ├── data_collector/  ← Embedded as module
│   │   │   ├── scrapers/
│   │   │   ├── parsers/
│   │   │   └── api.py
│   │   └── surveillance/    ← Embedded as module
│   │       ├── monitors/
│   │       ├── alerts/
│   │       └── api.py
│   ├── core/
│   └── api/
```

**Pros**:
- ✅ Single deployment
- ✅ Shared resources (DB, cache)
- ✅ Lower latency

**Cons**:
- ❌ Tighter coupling
- ❌ Harder to scale independently

---

### Pattern 3: API Integration

```
┌─────────────────┐      HTTP/REST      ┌─────────────────┐
│ Data Collector  │ ──────────────────→ │  RAG Enterprise │
└─────────────────┘                      └─────────────────┘
                                                   │
                                                   │ HTTP/REST
                                                   ↓
                                         ┌─────────────────────────┐
                                         │ Manufacturing Surveillance│
                                         └─────────────────────────┘
```

**API Contracts**:
- `POST /api/v1/ingest` - Data Collector → RAG
- `POST /api/v1/analyze` - RAG → Surveillance
- `GET /api/v1/status` - Health checks

**Pros**:
- ✅ Language-agnostic
- ✅ Independent deployment
- ✅ Easy monitoring

**Cons**:
- ❌ Network latency
- ❌ Need API versioning

---

### Pattern 4: Event-Driven

```
[Data Collector] → [Redis Pub/Sub] → [RAG Enterprise]
                                             ↓
                          [Redis Pub/Sub] → [Surveillance]
```

**Message Queue Topics**:
- `data.collected` - New data available
- `data.indexed` - RAG indexing complete
- `alert.quality` - Quality issue detected

**Pros**:
- ✅ Async, non-blocking
- ✅ Decoupled
- ✅ Scalable

**Cons**:
- ❌ More complex
- ❌ Need message broker

---

## Data Collector Integration

### Assumed Capabilities (Typical Data Collector)

Based on common patterns, data_collector likely provides:

1. **Web Scraping**:
   - Product catalog scraping
   - Price monitoring
   - Inventory tracking

2. **Data Parsing**:
   - Excel/CSV parsing
   - PDF extraction
   - API polling

3. **Data Normalization**:
   - Field mapping
   - Data cleaning
   - Duplicate detection

### Integration Points

#### 1. Direct API Integration

**Data Collector** exposes API:
```python
# Data Collector API (assumed)
POST /api/collect
{
    "source": "chunjinkorea",
    "type": "products",
    "filters": {"category": "PET bottles"}
}

Response:
{
    "job_id": "abc123",
    "status": "processing",
    "estimated_time": 120  # seconds
}

GET /api/jobs/{job_id}
Response:
{
    "status": "completed",
    "data": [
        {
            "product_code": "A-100",
            "product_name": "50ml PET 용기",
            "capacity_ml": 50.0,
            ...
        }
    ]
}
```

**RAG Enterprise** consumes data:
```python
# src/integrations/data_collector_client.py

import httpx
from typing import List, Dict

class DataCollectorClient:
    """Client for data_collector API"""

    def __init__(self, base_url: str = "http://data-collector:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def collect_products(
        self,
        source: str,
        filters: Dict = None
    ) -> List[Dict]:
        """Trigger data collection"""

        # 1. Start collection job
        response = await self.client.post(
            f"{self.base_url}/api/collect",
            json={
                "source": source,
                "type": "products",
                "filters": filters or {}
            }
        )
        job = response.json()
        job_id = job["job_id"]

        # 2. Poll for completion
        while True:
            response = await self.client.get(
                f"{self.base_url}/api/jobs/{job_id}"
            )
            status = response.json()

            if status["status"] == "completed":
                return status["data"]
            elif status["status"] == "failed":
                raise Exception(status.get("error"))

            await asyncio.sleep(5)  # Wait 5 seconds

    async def ingest_to_rag(self, source: str):
        """Collect and ingest into RAG pipeline"""
        from src.core.rag_pipeline import RAGPipeline

        # 1. Collect data
        products = await self.collect_products(source)

        # 2. Ingest into RAG
        rag = RAGPipeline()
        for product in products:
            await rag.ingest_document(product)

        return len(products)
```

#### 2. Shared Database Integration

**Data Collector** writes to PostgreSQL:
```sql
-- Shared table: collected_products
CREATE TABLE collected_products (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    product_code VARCHAR(50),
    product_name TEXT,
    capacity_ml FLOAT,
    material VARCHAR(20),
    collected_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);
```

**RAG Enterprise** reads and processes:
```python
# src/integrations/data_collector_poller.py

from sqlalchemy import select
from src.db.models import CollectedProduct
from src.core.rag_pipeline import RAGPipeline

async def poll_new_products():
    """Poll for unprocessed products"""
    async with get_db_session() as session:
        # Get unprocessed products
        result = await session.execute(
            select(CollectedProduct).where(
                CollectedProduct.processed == False
            ).limit(100)
        )
        products = result.scalars().all()

        if not products:
            return 0

        # Ingest into RAG
        rag = RAGPipeline()
        for product in products:
            await rag.ingest_document({
                "product_code": product.product_code,
                "product_name": product.product_name,
                "capacity_ml": product.capacity_ml,
                "material": product.material
            })

            # Mark as processed
            product.processed = True

        await session.commit()

        return len(products)

# Schedule with APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(poll_new_products, 'interval', minutes=5)
scheduler.start()
```

#### 3. Message Queue Integration

**Data Collector** publishes to Redis:
```python
# data_collector/publisher.py

import redis
import json

r = redis.Redis(host='localhost', port=6379)

def publish_collected_data(products: List[Dict]):
    """Publish collected products"""
    r.publish('data.collected', json.dumps({
        "event": "products_collected",
        "count": len(products),
        "products": products
    }))
```

**RAG Enterprise** subscribes:
```python
# src/integrations/data_collector_subscriber.py

import redis
import json
from src.core.rag_pipeline import RAGPipeline

r = redis.Redis(host='localhost', port=6379)
pubsub = r.pubsub()
pubsub.subscribe('data.collected')

async def listen_for_data():
    """Listen for new data from collector"""
    rag = RAGPipeline()

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            products = data['products']

            # Ingest into RAG
            for product in products:
                await rag.ingest_document(product)

            logger.info(f"Ingested {len(products)} products")
```

---

## Manufacturing Surveillance Integration

### Assumed Capabilities

Based on typical manufacturing surveillance systems:

1. **Quality Monitoring**:
   - Defect detection
   - Measurement validation
   - Specification compliance

2. **Anomaly Detection**:
   - Statistical outliers
   - Pattern recognition
   - Trend analysis

3. **Alerting**:
   - Real-time notifications
   - Escalation rules
   - Dashboard visualization

### Integration Points

#### 1. RAG → Surveillance API

**Use Case**: Send search results for quality analysis

```python
# src/integrations/surveillance_client.py

import httpx

class SurveillanceClient:
    """Client for manufacturing-surveillance API"""

    def __init__(self, base_url: str = "http://surveillance:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def analyze_product_quality(
        self,
        products: List[Dict]
    ) -> Dict:
        """Send products for quality analysis"""

        response = await self.client.post(
            f"{self.base_url}/api/analyze/quality",
            json={"products": products}
        )

        return response.json()
        # {
        #     "anomalies": [...],
        #     "warnings": [...],
        #     "recommendations": [...]
        # }

    async def search_with_surveillance(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict:
        """Search + quality check"""
        from src.core.rag_pipeline import RAGPipeline

        # 1. Semantic search
        rag = RAGPipeline()
        results = await rag.search(query, top_k=top_k)

        # 2. Quality analysis
        analysis = await self.analyze_product_quality(results)

        return {
            "results": results,
            "quality_analysis": analysis
        }
```

#### 2. Event-Driven Monitoring

**RAG** publishes indexing events:
```python
# src/core/rag_pipeline.py

import redis

class RAGPipeline:
    def __init__(self):
        self.redis = redis.Redis()

    async def ingest_document(self, doc: Dict):
        # ... ingest logic ...

        # Publish event
        self.redis.publish('rag.indexed', json.dumps({
            "event": "document_indexed",
            "product_code": doc["product_code"],
            "timestamp": datetime.now().isoformat()
        }))
```

**Surveillance** monitors:
```python
# surveillance/monitor.py

import redis

r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe('rag.indexed')

for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])

        # Check quality
        product_code = data['product_code']
        quality_score = check_quality(product_code)

        if quality_score < 0.8:
            send_alert(f"Low quality detected: {product_code}")
```

---

## Pipeline Architecture

### End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  Complete Data Pipeline                      │
└─────────────────────────────────────────────────────────────┘

[1. Data Collection]
    │
    ├→ Web Scraping (data_collector)
    ├→ Excel Parsing (data_collector)
    ├→ API Polling (data_collector)
    │
    ↓
[2. Normalization] (data_collector)
    │
    ↓
[3. Ingestion] (RAG Enterprise)
    │
    ├→ OCR Processing (PaddleOCR)
    ├→ Entity Extraction (regex + NER)
    ├→ Chunking (atomic + field-based)
    │
    ↓
[4. Indexing] (RAG Enterprise)
    │
    ├→ Text Embeddings (384-dim)
    ├→ Image Embeddings (1024-dim)
    ├→ Shape Embeddings (128-dim)
    ├→ Vector Storage (Qdrant)
    │
    ↓
[5. Search & Retrieval] (RAG Enterprise)
    │
    ├→ Semantic Search
    ├→ Filtered Search
    ├→ Hybrid Search
    │
    ↓
[6. Quality Monitoring] (surveillance)
    │
    ├→ Defect Detection
    ├→ Anomaly Detection
    ├→ Compliance Check
    │
    ↓
[7. Alerting] (surveillance)
    │
    ├→ Real-time Notifications
    ├→ Dashboard Updates
    └→ Escalation
```

---

## Implementation Guide

### Step 1: Setup Integration Layer

```bash
# Create integration modules
mkdir -p src/integrations
touch src/integrations/__init__.py
touch src/integrations/data_collector_client.py
touch src/integrations/surveillance_client.py
```

### Step 2: Install Dependencies

```bash
# Add to requirements.txt
httpx>=0.25.0        # HTTP client
redis>=5.0.0         # Message queue
pydantic>=2.0.0      # Data validation
```

### Step 3: Configure Environment

```bash
# .env
DATA_COLLECTOR_URL=http://data-collector:8000
SURVEILLANCE_URL=http://surveillance:8000
REDIS_URL=redis://localhost:6379
```

### Step 4: Create API Endpoints

```python
# src/api/v1/integrations.py

from fastapi import APIRouter, BackgroundTasks
from src.integrations.data_collector_client import DataCollectorClient
from src.integrations.surveillance_client import SurveillanceClient

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post("/collect-and-ingest")
async def collect_and_ingest(
    source: str,
    background_tasks: BackgroundTasks
):
    """Trigger data collection and ingestion"""
    client = DataCollectorClient()

    # Run in background
    background_tasks.add_task(
        client.ingest_to_rag,
        source=source
    )

    return {"status": "started", "source": source}

@router.post("/search-with-analysis")
async def search_with_analysis(query: str, top_k: int = 5):
    """Search + quality analysis"""
    surveillance = SurveillanceClient()

    results = await surveillance.search_with_surveillance(
        query=query,
        top_k=top_k
    )

    return results
```

### Step 5: Add to Main App

```python
# src/api/app.py

from src.api.v1 import integrations

app.include_router(
    integrations.router,
    prefix="/api/v1"
)
```

---

## API Contracts

### Data Collector → RAG Enterprise

**Endpoint**: `POST /api/v1/ingest/bulk`

**Request**:
```json
{
  "source": "data_collector",
  "products": [
    {
      "product_code": "A-100",
      "product_name": "50ml PET 용기",
      "capacity_ml": 50.0,
      "material": "PET",
      "unit_price": 120.0
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "ingested": 100,
  "failed": 0,
  "errors": []
}
```

---

### RAG Enterprise → Manufacturing Surveillance

**Endpoint**: `POST /api/v1/monitor/products`

**Request**:
```json
{
  "products": [
    {
      "product_code": "A-100",
      "search_score": 0.89,
      "metadata": {...}
    }
  ]
}
```

**Response**:
```json
{
  "status": "analyzed",
  "anomalies": [
    {
      "product_code": "A-100",
      "issue": "Price deviation",
      "severity": "medium",
      "recommendation": "Review pricing"
    }
  ]
}
```

---

## Next Steps

1. **Wait for Projects**: Once data_collector and manufacturing-surveillance are available, review actual APIs
2. **Choose Pattern**: Select integration pattern based on requirements
3. **Implement Client**: Create integration clients
4. **Test**: Integration tests with mock data
5. **Deploy**: Deploy all services together
6. **Monitor**: Track pipeline performance

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
