# Data Collection Examples

**Purpose**: Real-world examples of data collection workflows.

---

## Example 1: Web Scraping E-commerce Products

### Scenario
Scrape product listings from an e-commerce website daily.

### Implementation

```python
from src.collectors.web_scraper import WebScraper
from src.collectors.data_pipeline import DataPipeline

# 1. Configure scraper
scraper = WebScraper(
    engine="playwright",  # Dynamic content
    headless=True,
    timeout_seconds=30
)

# 2. Scrape products
config = {
    "url": "https://example.com/products",
    "selectors": {
        "product_name": ".product-title",
        "price": ".product-price",
        "image": ".product-image img[src]"
    },
    "pagination": {
        "type": "infinite_scroll",
        "scroll_pause": 2
    }
}

products = await scraper.scrape(config)

# 3. Process data
pipeline = DataPipeline(
    validation_schema="product_schema.json",
    error_strategy="skip",
    enable_deduplication=True
)

processed_data = await pipeline.process(products)

# 4. Store in database
await db.bulk_insert("products", processed_data)
```

### Schedule Daily

```bash
schedule daily_products \
  web https://example.com/products \
  "0 2 * * *" \
  --engine playwright
```

---

## Example 2: API Polling with Pagination

### Scenario
Poll REST API every 6 hours, handle pagination, store in PostgreSQL + Qdrant.

### Implementation

```python
from src.collectors.api_poller import APIPoller

# 1. Configure API poller
poller = APIPoller(
    base_url="https://api.example.com/v1",
    auth_type="oauth2",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 2. Poll with pagination
products = await poller.poll(
    endpoint="/products",
    method="GET",
    params={"category": "packaging"},
    paginate=True,
    pagination_type="offset",  # offset | cursor | page
    page_size=100
)

# 3. Process and enrich
pipeline = DataPipeline()
processed = await pipeline.process(products)

# 4. Generate embeddings and store
from src.core.embeddings import generate_embeddings

for product in processed:
    # Store structured data in PostgreSQL
    await db.insert("products", product)

    # Generate embedding and store in Qdrant
    embedding = generate_embeddings(product["description"])
    await qdrant.insert(
        collection_name="products",
        id=product["id"],
        vector=embedding,
        payload=product
    )
```

### Schedule Every 6 Hours

```bash
schedule api_polling \
  api https://api.example.com/v1/products \
  "0 */6 * * *" \
  --max-instances 1
```

---

## Example 3: Bulk File Processing

### Scenario
Process Excel file with 10K+ product records.

### Implementation

```python
from src.collectors.file_parser import FileParser

# 1. Parse Excel file
parser = FileParser()
data = parser.parse("/data/products.xlsx", sheet_name="Products")

# Output: List[Dict] with all rows
# [
#   {"Product Code": "A001", "Name": "50ml Bottle", ...},
#   {"Product Code": "A002", "Name": "100ml Bottle", ...},
#   ...
# ]

# 2. Validate and transform
pipeline = DataPipeline(
    validation_schema={
        "product_code": {"type": "string", "required": True},
        "name": {"type": "string", "required": True},
        "capacity": {"type": "string", "pattern": r"^\d+ml$"}
    },
    field_mapping={
        "Product Code": "product_code",
        "Name": "name",
        "Capacity": "capacity"
    }
)

processed = await pipeline.process(data)

# 3. Batch insert (1000 records at a time)
batch_size = 1000
for i in range(0, len(processed), batch_size):
    batch = processed[i:i+batch_size]
    await db.bulk_insert("products", batch)
```

### One-time Processing

```bash
collect file /data/products.xlsx
process products.xlsx --skip-enrichment
```

---

## Example 4: Multi-Source Aggregation

### Scenario
Collect data from multiple sources (web + API + file), merge, and deduplicate.

### Implementation

```python
from src.collectors.web_scraper import WebScraper
from src.collectors.api_poller import APIPoller
from src.collectors.file_parser import FileParser
from src.collectors.data_pipeline import DataPipeline

# 1. Collect from web
scraper = WebScraper(engine="playwright")
web_data = await scraper.scrape("https://supplier1.com/products")

# 2. Collect from API
poller = APIPoller(base_url="https://api.supplier2.com")
api_data = await poller.poll("/products")

# 3. Collect from file
parser = FileParser()
file_data = parser.parse("/data/supplier3.xlsx")

# 4. Merge all sources
all_data = web_data + api_data + file_data

# 5. Process with deduplication
pipeline = DataPipeline(
    enable_deduplication=True,
    dedup_key="product_code"  # Deduplicate by product code
)

processed = await pipeline.process(all_data)

# 6. Store
await db.bulk_insert("products", processed)
```

---

## Example 5: Error Handling and Retry

### Scenario
Handle errors gracefully, retry failed operations.

### Implementation

```python
from src.collectors.web_scraper import WebScraper
from src.collectors.data_pipeline import DataPipeline

# 1. Configure scraper with retry
scraper = WebScraper(
    engine="playwright",
    retry_attempts=3,
    retry_delay_seconds=2  # 2s, 4s, 8s (exponential backoff)
)

# 2. Scrape with error handling
try:
    products = await scraper.scrape("https://example.com/products")
except TimeoutError:
    # Fallback to BeautifulSoup (faster, no JS rendering)
    scraper = WebScraper(engine="beautifulsoup")
    products = await scraper.scrape("https://example.com/products")

# 3. Process with "skip" error strategy
pipeline = DataPipeline(
    error_strategy="skip",  # Skip invalid records, continue processing
    log_errors=True
)

processed = await pipeline.process(products)

# 4. Log skipped records
if pipeline.error_count > 0:
    logger.warning(f"Skipped {pipeline.error_count} invalid records")
    logger.error(f"Errors: {pipeline.errors}")
```

---

## Example 6: Real-time Monitoring

### Scenario
Monitor collection jobs in real-time.

### Implementation

```python
from src.collectors.job_monitor import JobMonitor

# 1. Create monitor
monitor = JobMonitor()

# 2. Start collection job (async)
job_id = await monitor.start_job(
    job_type="web_scraping",
    source="https://example.com/products",
    config={"engine": "playwright"}
)

# 3. Monitor progress
while True:
    status = await monitor.get_status(job_id)

    print(f"Status: {status['status']}")
    print(f"Progress: {status['items_collected']}/{status['total_items']}")
    print(f"Errors: {status['error_count']}")

    if status['status'] in ['completed', 'failed']:
        break

    await asyncio.sleep(5)

# 4. Get final results
results = await monitor.get_results(job_id)
```

### CLI Monitoring

```bash
# Start job
job_id=$(collect web https://example.com/products --async)

# Monitor progress
monitor $job_id

# View statistics
monitor --stats
```

---

## Best Practices Summary

### ✅ DO

1. **Use appropriate engine**:
   - BeautifulSoup for static HTML
   - Playwright for dynamic JS
   - Selenium only for complex interactions

2. **Handle errors gracefully**:
   - Use "skip" strategy in production
   - Log errors for debugging
   - Implement retry with exponential backoff

3. **Respect rate limits**:
   - Add delays between requests
   - Implement backoff on 429 errors
   - Use caching to reduce requests

4. **Batch processing**:
   - Insert to database in batches (1000 records)
   - Process large files in chunks
   - Use parallel processing for independent tasks

### ❌ DON'T

1. **Don't use "stop" error strategy in production** - It halts the entire pipeline
2. **Don't scrape without rate limiting** - You'll get blocked
3. **Don't process entire 100K+ file at once** - Use batch processing
4. **Don't forget to deduplicate** - Especially when merging sources

---

**See Also**:
- `references/collector_architecture.md` - System architecture
- `docs/DATA_COLLECTOR_ARCHITECTURE.md` - Complete documentation
