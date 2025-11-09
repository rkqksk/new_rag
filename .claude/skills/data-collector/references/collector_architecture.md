# Data Collector Architecture Reference

**Purpose**: Detailed architecture and implementation guide for data collection system.

**See Also**: `docs/DATA_COLLECTOR_ARCHITECTURE.md` for complete documentation.

---

## System Architecture

```
┌─────────────────────┐
│  Collection Layer   │ (Web Scraper, API Poller, File Parser)
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Processing Layer   │ (Validation → Cleaning → Transformation → Enrichment)
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Storage Layer      │ (PostgreSQL + Qdrant + MinIO)
└─────────────────────┘
```

---

## Collection Engines

### Web Scraper

**BeautifulSoup** (Static HTML):
- Fast parsing (50-100 pages/min)
- Low resource usage (~50MB RAM)
- Best for: Static content, simple structure

**Playwright** (Dynamic JS):
- JavaScript rendering (10-20 pages/min)
- Moderate resource usage (~200MB RAM)
- Best for: SPAs, dynamic content

**Selenium** (Complex Interactions):
- Full browser automation (5-10 pages/min)
- High resource usage (~500MB RAM)
- Best for: Form submission, complex navigation

### API Poller

**Features**:
- OAuth2, API key, Basic auth
- Automatic pagination (offset, cursor, page-based)
- Rate limit detection (429 retry with exponential backoff)
- Response caching

**Performance**: 100-500 req/min

### File Parser

**Supported Formats**:
- CSV (pandas): 10K-50K rows/sec
- Excel (openpyxl): 5K-10K rows/sec
- PDF (PyPDF2): 5-10 pages/sec
- JSON (json): 50K-100K records/sec
- XML (lxml): 10K-20K nodes/sec

---

## Processing Pipeline

### 1. Validation
- Schema validation (Pydantic models)
- Required field checks
- Data type validation
- Custom validation rules

### 2. Cleaning
- Remove duplicates (based on unique keys)
- Trim whitespace
- Normalize text (lowercase, unicode normalization)
- Remove null/empty values

### 3. Transformation
- Field mapping (source → target schema)
- Format conversion (date, number, string)
- Unit standardization

### 4. Entity Extraction
- Product codes (regex patterns)
- Capacities (number + unit)
- Materials (NER or lookup)
- Prices (number + currency)

### 5. Enrichment
- Add metadata (timestamp, source, version)
- External API lookups
- Classification (product category)
- Generate embeddings (for Qdrant)

---

## Database Integration

### PostgreSQL
**Purpose**: Structured data storage
**Schema**: `raw_data`, `processed_data`, `collection_jobs`

### Qdrant
**Purpose**: Vector embeddings for RAG
**Process**: Text → Embeddings (all-MiniLM-L6-v2) → Qdrant

### MinIO
**Purpose**: Object storage for files
**Use Cases**: PDF files, images, large JSON dumps

---

## Job Scheduling

### APScheduler

**Trigger Types**:
- **Cron**: "0 2 * * *" (daily at 2 AM)
- **Interval**: IntervalTrigger(hours=6)
- **Date**: Specific datetime

**Job Management**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    collect_data,
    trigger='cron',
    hour=2,
    minute=0,
    id='daily_collection',
    max_instances=1
)
scheduler.start()
```

---

## Error Handling

### Strategies

**Skip**: Continue processing, log error
**Stop**: Halt pipeline on first error
**Retry**: Exponential backoff (3 attempts)

### Retry Logic
```python
async def retry_with_backoff(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = 2 ** attempt  # 2s, 4s, 8s
            await asyncio.sleep(delay)
```

---

## Performance Optimization

### Parallel Processing
- Use `asyncio.gather()` for concurrent requests
- Thread pool for CPU-bound tasks (file parsing)

### Caching
- Cache API responses (Redis, 1-hour TTL)
- Cache parsed files (avoid re-parsing)

### Batch Processing
- Insert to PostgreSQL in batches (1000 records)
- Bulk upload to Qdrant (100 vectors)

---

**Full Documentation**: `docs/DATA_COLLECTOR_ARCHITECTURE.md`
