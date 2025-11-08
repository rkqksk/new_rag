---
name: data-collector
description: Data Collector Skill
---

# Data Collector Skill

**Purpose**: Universal data collection, processing, and database integration for RAG Enterprise Platform.

**Version**: 1.0.0 (v5.0.0 Platform)
**Status**: Production-ready ✅

---

## 🎯 Skill Overview

This skill provides comprehensive data collection capabilities across multiple sources:
- **Web Scraping**: Static HTML (BeautifulSoup), dynamic JS (Playwright), complex interactions (Selenium)
- **API Polling**: REST/GraphQL with OAuth2, retry logic, pagination
- **File Parsing**: CSV, Excel, PDF, JSON, XML, HTML
- **Processing Pipeline**: Validation → Cleaning → Transformation → Enrichment
- **Database Integration**: PostgreSQL + Qdrant + MinIO

**Use this skill when:**
- Setting up data ingestion pipelines
- Scraping product data from websites
- Polling external APIs for updates
- Processing bulk data files
- Scheduling automated data collection jobs

**Architecture Reference**: §collector.* symbols → `docs/DATA_COLLECTOR_ARCHITECTURE.md`

---

## 📋 Available Commands

### 1. `collect`
**Description**: Start a data collection job from specified source

**Usage**:
```bash
collect <source_type> <source_config> [options]
```

**Source Types**:
- `web` - Web scraping (URL required)
- `api` - API polling (endpoint required)
- `file` - File parsing (file path required)

**Options**:
- `--engine <engine>` - Collection engine (beautifulsoup | playwright | selenium)
- `--schedule <cron>` - Schedule recurring job (cron expression)
- `--retry <n>` - Number of retry attempts (default: 3)

**Example**:
```bash
# Web scraping with Playwright
collect web https://example.com/products --engine playwright

# API polling with scheduling
collect api https://api.example.com/v1/products --schedule "0 2 * * *"

# File parsing
collect file /data/products.xlsx
```

---

### 2. `process`
**Description**: Process collected data through the pipeline

**Usage**:
```bash
process <data_source> [options]
```

**Options**:
- `--validate-only` - Only run validation step
- `--skip-enrichment` - Skip enrichment step
- `--error-strategy <strategy>` - Error handling (skip | stop | retry)

**Example**:
```bash
# Full pipeline processing
process collected_data.json

# Validation only
process collected_data.json --validate-only

# Skip enrichment (faster)
process collected_data.json --skip-enrichment
```

**Pipeline Steps**:
1. **Validation**: Schema validation, required fields, data types
2. **Cleaning**: Deduplication, normalization, whitespace trimming
3. **Transformation**: Field mapping, format conversion
4. **Entity Extraction**: Product codes, capacities, materials
5. **Enrichment**: Metadata, external lookups, classification

---

### 3. `schedule`
**Description**: Schedule recurring data collection jobs

**Usage**:
```bash
schedule <job_name> <source> <cron_expression> [options]
```

**Cron Examples**:
- `"0 2 * * *"` - Daily at 2 AM
- `"0 2 * * 0"` - Weekly (Sunday at 2 AM)
- `"0 2 1 * *"` - Monthly (1st at 2 AM)

**Options**:
- `--timezone <tz>` - Timezone (default: UTC)
- `--max-instances <n>` - Max concurrent instances (default: 1)

**Example**:
```bash
# Daily collection at 2 AM UTC
schedule daily_products web https://example.com/products "0 2 * * *"

# Weekly API polling
schedule weekly_api api https://api.example.com/products "0 2 * * 0"
```

---

### 4. `monitor`
**Description**: Monitor collection jobs and view status

**Usage**:
```bash
monitor [job_id]
```

**Options**:
- `--active` - Show only active jobs
- `--failed` - Show only failed jobs
- `--stats` - Show collection statistics

**Example**:
```bash
# Monitor specific job
monitor job-123

# View all active jobs
monitor --active

# Collection statistics
monitor --stats
```

**Output**:
```
Job ID: job-123
Status: running
Source: https://example.com/products
Started: 2025-11-08 02:00:00 UTC
Progress: 150/500 items (30%)
Errors: 2 (retry in progress)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Web Scraping
WEB_SCRAPER_ENGINE=playwright          # beautifulsoup | playwright | selenium
WEB_SCRAPER_HEADLESS=true              # Headless browser
WEB_SCRAPER_TIMEOUT_SECONDS=30         # Request timeout
WEB_SCRAPER_RETRY_ATTEMPTS=3           # Retry attempts
WEB_SCRAPER_RETRY_DELAY_SECONDS=2      # Delay between retries

# API Polling
API_POLLER_TIMEOUT_SECONDS=30
API_POLLER_RETRY_ATTEMPTS=3
API_POLLER_RATE_LIMIT_DELAY=1

# Job Scheduling
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=UTC
SCHEDULER_MAX_INSTANCES=3

# Storage
MINIO_ENABLED=false
MINIO_ENDPOINT=localhost:9000
```

**Full Config**: `.env.example`

---

## 📚 References

### Progressive Disclosure
- **Quick Start**: This file (SKILL.md) - ~300 lines
- **Architecture**: `references/collector_architecture.md` - Complete system design
- **Examples**: `examples/collection_examples.md` - Real-world use cases

### Symbol Navigation
- `§collector.status` - System status and capabilities
- `§collector.pipeline` - Processing pipeline details
- `§collector.sources` - Collection source types
- `§collector.scheduling` - APScheduler integration

### Full Documentation
- **Architecture**: `docs/DATA_COLLECTOR_ARCHITECTURE.md` (~30KB)
- **System Integration**: `docs/SYSTEM_INTEGRATION_GUIDE.md`
- **CLAUDE.md**: Quick reference with symbols

---

## 💡 Best Practices

### Web Scraping
```python
# ✅ Good: Use BeautifulSoup for static content
from src.collectors.web_scraper import WebScraper

scraper = WebScraper(engine="beautifulsoup")
data = scraper.scrape("https://example.com/static-page")

# ✅ Good: Use Playwright for JavaScript rendering
scraper = WebScraper(engine="playwright")
data = scraper.scrape("https://example.com/dynamic-page")

# ❌ Avoid: Using Selenium for simple static pages (too slow)
```

### Error Handling
```python
# ✅ Good: Use appropriate error strategy
pipeline = DataPipeline(error_strategy="skip")  # Skip bad records
pipeline = DataPipeline(error_strategy="retry")  # Retry failed operations

# ❌ Avoid: Using "stop" in production (halts entire pipeline)
pipeline = DataPipeline(error_strategy="stop")  # Only for debugging
```

### Scheduling
```python
# ✅ Good: Schedule during low-traffic hours
schedule daily_job "0 2 * * *"  # 2 AM

# ✅ Good: Limit concurrent instances
schedule job_name source "0 * * * *" --max-instances 1

# ❌ Avoid: High-frequency scheduling without rate limiting
schedule bad_job source "* * * * *"  # Every minute = too frequent!
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue**: "Timeout error" during web scraping
**Solution**: Increase `WEB_SCRAPER_TIMEOUT_SECONDS` or switch to `playwright` engine

**Issue**: "Rate limit exceeded" from API
**Solution**: Increase `API_POLLER_RATE_LIMIT_DELAY` or implement exponential backoff

**Issue**: "Duplicate records" in database
**Solution**: Enable deduplication in processing pipeline:
```python
pipeline = DataPipeline(enable_deduplication=True)
```

**Issue**: "Job not starting" in scheduler
**Solution**: Check `SCHEDULER_MAX_INSTANCES` limit and active job count

---

## 📊 Performance Metrics

### Collection Speeds

| Source Type | Engine | Speed | Use Case |
|-------------|--------|-------|----------|
| Web (static) | BeautifulSoup | 50-100 pages/min | Simple HTML |
| Web (dynamic) | Playwright | 10-20 pages/min | JavaScript rendering |
| Web (complex) | Selenium | 5-10 pages/min | Form submission, navigation |
| API | httpx | 100-500 req/min | REST/GraphQL APIs |
| File (CSV) | pandas | 10K-50K rows/sec | Structured data |
| File (PDF) | PyPDF2 | 5-10 pages/sec | PDF text extraction |

### Resource Usage

- **BeautifulSoup**: ~50MB RAM, minimal CPU
- **Playwright**: ~200MB RAM, moderate CPU
- **Selenium**: ~500MB RAM, high CPU
- **API Poller**: ~100MB RAM, minimal CPU

---

## 🚀 Quick Start

### 1. One-Time Collection
```bash
# Collect data from website
collect web https://example.com/products --engine playwright

# Process collected data
process collected_data.json

# View results
monitor --stats
```

### 2. Scheduled Collection
```bash
# Schedule daily collection
schedule daily_products web https://example.com/products "0 2 * * *"

# Monitor scheduled job
monitor --active
```

### 3. Bulk File Processing
```bash
# Process Excel file
collect file /data/products.xlsx

# Process with custom pipeline
process products.xlsx --skip-enrichment
```

---

## 📖 See Also

- **SaaS Platform Skill**: Multi-tenancy, billing, usage tracking
- **RAG Pipeline Skill**: Vector search, embeddings, RAG orchestration
- **Manufacturing Expert Skill**: Document processing, classification

---

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Maintainer**: RAG Enterprise Platform Team
