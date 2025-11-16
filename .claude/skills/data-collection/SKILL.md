---
name: data-collection
description: Web scraping crawling spider API collect parse 크롤링 수집 파싱 BeautifulSoup requests Airflow DAG scheduler OneHago FreeWorld ChunJin Excel PDF JSON HTML XML CSV file processing 데이터 수집 자동화
---

# Data Collection Pipeline

## When to Use
- 웹 크롤링, web scraping, crawling
- API 데이터 수집, API polling
- 파일 파싱, file parsing (Excel, PDF, JSON, HTML, XML, CSV)
- 스케줄링, scheduling, Airflow DAG
- 데이터 자동화, data automation
- OneHago, FreeWorld, ChunJin 사이트 크롤링

## Core Capabilities
1. **Web Crawling** - BeautifulSoup, requests, anti-blocking
2. **API Integration** - REST API polling, pagination
3. **File Parsing** - 6 formats (Excel, PDF, JSON, HTML, XML, CSV)
4. **Scheduling** - Airflow DAGs, cron jobs
5. **Data Validation** - Quality checks, deduplication

## Quick Actions

### Crawl Website
```python
# Create crawler
python scripts/create_crawler.py \
  --site onehago \
  --targets products,specifications \
  --output data/crawled/
```

### Parse Files
```python
# Batch parsing
python scripts/parse_documents.py \
  --input data/raw/*.pdf \
  --format pdf \
  --output data/parsed/
```

### Schedule Collection
```python
# Create Airflow DAG
python scripts/create_airflow_dag.py \
  --name daily_crawl \
  --schedule "0 2 * * *" \
  --tasks crawl,parse,index
```

### Validate Data
```python
# Quality check
python scripts/validate_data.py \
  --input data/parsed/ \
  --checks duplicates,missing,format
```

## Supported Sites
- **OneHago** (원하고) - 제조 자재 플랫폼
- **FreeWorld** (프리월드) - 산업 용품
- **ChunJinKorea** (천진코리아) - 포장 자재

## File Formats
- **Excel** (.xlsx, .xls, .csv) - Tabular data
- **PDF** (.pdf) - Documents with OCR
- **JSON** (.json) - Structured data
- **HTML** (.html) - Web pages
- **XML** (.xml) - Structured documents
- **CSV** (.csv) - Comma-separated values

## Integration
- **excel-processing**: Parse Excel files
- **pdf-processing**: Extract PDF content
- **rag-optimization**: Index collected data
- **testing-suite**: Generate crawler tests

## Key Files
- `scripts/crawlers/` - Site-specific crawlers
- `scripts/parsers/` - File format parsers
- `src/services/data_collector.py` - Collection service

## Anti-Blocking Strategies
- User-agent rotation
- Request delays (1-3 seconds)
- Proxy support
- Session management
- Retry logic with exponential backoff
