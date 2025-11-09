# Data Collector - Universal Data Ingestion System

**Version**: v5.0.0
**Symbol Domain**: §collector.*
**Modular, scalable data collection pipeline for any source**

---

## 📍 Symbol Navigation

**Quick Access**: Use these symbols for efficient documentation navigation

| Symbol | Description | Location |
|--------|-------------|----------|
| §collector.status | System status & capabilities | SYMBOLS.md |
| §collector.pipeline | Complete data pipeline | This document, SYMBOLS.md |
| §collector.sources | Collection sources (web/API/file) | This document, SYMBOLS.md |
| §collector.scheduling | Job scheduling (APScheduler) | This document, SYMBOLS.md |
| §api.endpoints | All Collector API endpoints | API_DOCUMENTATION.md |
| §rag.core | RAG integration | RAG_ACTIVATION_STRATEGY.md |

**See Also**:
- **CLAUDE.md**: Quick reference with all symbols
- **SYMBOLS.md**: Complete symbol map (§collector.* section)
- **Skills**: `.claude/skills/data-collector/SKILL.md`

---

## ⚡ Quick Reference (Token-Optimized)

```
Data Collector v5.0.0
├─ Web: BeautifulSoup (50-100 p/min) | Playwright (10-20 p/min) → §collector.sources
├─ API: REST/GraphQL, OAuth2, pagination (100-500 req/min) → §collector.sources
├─ Files: CSV/Excel/PDF/JSON/XML (10K-50K rows/sec) → §collector.sources
├─ Pipeline: Validate → Clean → Transform → Enrich → §collector.pipeline
├─ Storage: PostgreSQL + Qdrant + MinIO → §collector.pipeline
└─ Schedule: APScheduler (cron, interval) → §collector.scheduling

Performance:
• BeautifulSoup: 50MB RAM, fast static pages
• Playwright: 200MB RAM, JS rendering
• Selenium: 500MB RAM, complex interactions
```

**💡 Use symbols above to jump to detailed sections in SYMBOLS.md**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Collection Modules](#collection-modules)
4. [Processing Pipeline](#processing-pipeline)
5. [Database Integration](#database-integration)
6. [Scheduling & Orchestration](#scheduling--orchestration)
7. [Error Handling](#error-handling)
8. [Implementation](#implementation)

---

## Overview

### Data Collector Stack

```
Universal Data Collection System
├── Collection Modules
│   ├── Web Scraper (BeautifulSoup, Playwright, Selenium)
│   ├── API Poller (REST, GraphQL, SOAP)
│   ├── File Parser (Excel, CSV, PDF, JSON, XML)
│   ├── Database Connector (PostgreSQL, MySQL, MongoDB)
│   └── FTP/SFTP Client (Remote file systems)
├── Processing Pipeline
│   ├── Data Validation (Schema validation)
│   ├── Data Cleaning (Deduplication, normalization)
│   ├── Data Transformation (Field mapping, type conversion)
│   ├── Entity Extraction (Regex, NER)
│   └── Data Enrichment (External APIs)
├── Storage Layer
│   ├── Raw Data Storage (MinIO/S3)
│   ├── Processed Data (PostgreSQL)
│   ├── Vector Storage (Qdrant - for RAG)
│   └── Cache (Redis)
├── Orchestration
│   ├── Task Scheduler (APScheduler, Celery)
│   ├── Workflow Engine (Prefect, Airflow-lite)
│   ├── Monitoring (Prometheus + Grafana)
│   └── Alerts (Email, Slack, Webhook)
└── API Layer
    ├── REST API (FastAPI)
    ├── GraphQL (Optional)
    └── WebSocket (Real-time updates)
```

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                            │
├─────────────────────────────────────────────────────────────┤
│  Web    │  APIs   │  Files  │  Databases  │  FTP/SFTP      │
└────┬─────────┬─────────┬──────────┬──────────────┬──────────┘
     │         │         │          │              │
     ↓         ↓         ↓          ↓              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Collection Layer                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Scraper │  │  Poller  │  │  Parser  │  │Connector │   │
│  │  Module  │  │  Module  │  │  Module  │  │  Module  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   Processing Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│  [1] Validation → [2] Cleaning → [3] Transformation →       │
│  [4] Extraction → [5] Enrichment                            │
└────┬────────────────────────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  MinIO   │  │PostgreSQL│  │  Qdrant  │  │  Redis   │   │
│  │  (Raw)   │  │(Processed)│  │ (Vector) │  │ (Cache)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer                          │
├─────────────────────────────────────────────────────────────┤
│  → RAG Enterprise (Vector Indexing)                         │
│  → Manufacturing Surveillance (Quality Monitoring)           │
│  → External APIs (Third-party integrations)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Collection Modules

### 1. Web Scraper Module

**Purpose**: Extract data from websites

**Technologies**: BeautifulSoup, Playwright, Selenium

**Features**:
- JavaScript rendering support
- Dynamic content handling
- Anti-bot detection evasion
- Rate limiting & politeness
- Proxy rotation

**Implementation**:
```python
# src/collectors/web_scraper.py

from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
from dataclasses import dataclass

@dataclass
class ScrapeConfig:
    """Scraper configuration"""
    url: str
    method: str = "GET"  # GET, POST
    headers: Dict = None
    cookies: Dict = None
    render_js: bool = False  # Use Playwright if True
    wait_selector: str = None  # Wait for element before scraping
    pagination: bool = False
    max_pages: int = 10
    rate_limit: float = 1.0  # Seconds between requests

class WebScraper:
    """
    Universal web scraper

    Supports:
    - Static HTML (httpx + BeautifulSoup)
    - Dynamic content (Playwright)
    - Pagination
    - Rate limiting
    """

    def __init__(self):
        self.session = httpx.AsyncClient(timeout=30.0)

    async def scrape(self, config: ScrapeConfig) -> List[Dict]:
        """
        Scrape data from URL

        Args:
            config: Scrape configuration

        Returns:
            List of extracted data
        """
        if config.render_js:
            return await self._scrape_dynamic(config)
        else:
            return await self._scrape_static(config)

    async def _scrape_static(self, config: ScrapeConfig) -> List[Dict]:
        """Scrape static HTML pages"""
        results = []

        try:
            # Make request
            response = await self.session.request(
                method=config.method,
                url=config.url,
                headers=config.headers or {},
                cookies=config.cookies or {}
            )

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract data (override in subclass)
            data = self._extract_data(soup)
            results.extend(data)

            # Handle pagination
            if config.pagination:
                next_url = self._find_next_page(soup)
                page_count = 1

                while next_url and page_count < config.max_pages:
                    await asyncio.sleep(config.rate_limit)

                    response = await self.session.get(next_url)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    data = self._extract_data(soup)
                    results.extend(data)

                    next_url = self._find_next_page(soup)
                    page_count += 1

            return results

        except Exception as e:
            raise ScrapeError(f"Failed to scrape {config.url}: {e}")

    async def _scrape_dynamic(self, config: ScrapeConfig) -> List[Dict]:
        """Scrape dynamic JavaScript-rendered pages"""
        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Navigate to URL
                await page.goto(config.url, wait_until='networkidle')

                # Wait for specific element if specified
                if config.wait_selector:
                    await page.wait_for_selector(config.wait_selector)

                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Extract data
                data = self._extract_data(soup)
                results.extend(data)

                # Handle pagination
                if config.pagination:
                    page_count = 1

                    while page_count < config.max_pages:
                        # Try to find and click "next" button
                        next_button = await page.query_selector('a.next, button.next, [aria-label="Next"]')

                        if not next_button:
                            break

                        await next_button.click()
                        await asyncio.sleep(config.rate_limit)
                        await page.wait_for_load_state('networkidle')

                        content = await page.content()
                        soup = BeautifulSoup(content, 'html.parser')

                        data = self._extract_data(soup)
                        results.extend(data)

                        page_count += 1

                return results

            finally:
                await browser.close()

    def _extract_data(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract data from parsed HTML

        Override this method in subclasses for specific sites
        """
        raise NotImplementedError("Subclass must implement _extract_data()")

    def _find_next_page(self, soup: BeautifulSoup) -> Optional[str]:
        """Find next page URL"""
        # Look for common pagination patterns
        next_link = soup.find('a', {'class': 'next'}) or \
                   soup.find('a', {'rel': 'next'}) or \
                   soup.find('a', text='Next')

        if next_link and next_link.get('href'):
            return next_link['href']

        return None

class ScrapeError(Exception):
    """Scraping error"""
    pass


# Example: Product scraper
class ProductScraper(WebScraper):
    """Scrape product listings"""

    def _extract_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract product data"""
        products = []

        # Find all product containers
        for item in soup.find_all('div', class_='product-item'):
            try:
                product = {
                    'product_code': item.find('span', class_='code').text.strip(),
                    'product_name': item.find('h3', class_='name').text.strip(),
                    'price': self._parse_price(item.find('span', class_='price').text),
                    'url': item.find('a')['href'],
                    'image_url': item.find('img')['src']
                }
                products.append(product)
            except Exception as e:
                # Skip malformed items
                continue

        return products

    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        import re
        # Extract numbers
        numbers = re.findall(r'\d+', price_text.replace(',', ''))
        if numbers:
            return float(''.join(numbers))
        return 0.0
```

---

### 2. API Poller Module

**Purpose**: Poll REST/GraphQL APIs for data

**Features**:
- OAuth2, API key authentication
- Rate limiting (respect API limits)
- Retry with exponential backoff
- Pagination handling
- Webhook support

**Implementation**:
```python
# src/collectors/api_poller.py

from typing import Dict, List, Optional, Any
import httpx
import asyncio
from datetime import datetime, timedelta
import hashlib
import hmac

class APIPoller:
    """
    Universal API poller

    Supports:
    - REST APIs
    - GraphQL APIs
    - OAuth2 authentication
    - API key authentication
    - Rate limiting
    - Pagination
    """

    def __init__(
        self,
        base_url: str,
        auth_type: str = "api_key",  # api_key, oauth2, bearer, basic
        api_key: str = None,
        oauth_token: str = None,
        rate_limit: float = 1.0
    ):
        self.base_url = base_url
        self.auth_type = auth_type
        self.api_key = api_key
        self.oauth_token = oauth_token
        self.rate_limit = rate_limit
        self.session = httpx.AsyncClient(timeout=30.0)

    async def poll(
        self,
        endpoint: str,
        method: str = "GET",
        params: Dict = None,
        data: Dict = None,
        paginate: bool = False,
        max_pages: int = 100
    ) -> List[Dict]:
        """
        Poll API endpoint

        Args:
            endpoint: API endpoint path
            method: HTTP method
            params: Query parameters
            data: Request body
            paginate: Enable pagination
            max_pages: Maximum pages to fetch

        Returns:
            List of API responses
        """
        results = []
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Prepare headers
        headers = self._get_auth_headers()

        # Make request
        try:
            response = await self._make_request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )

            # Parse response
            response_data = response.json()

            # Handle different response formats
            if isinstance(response_data, list):
                results.extend(response_data)
            elif isinstance(response_data, dict):
                # Check common data keys
                if 'data' in response_data:
                    results.extend(response_data['data'])
                elif 'results' in response_data:
                    results.extend(response_data['results'])
                elif 'items' in response_data:
                    results.extend(response_data['items'])
                else:
                    results.append(response_data)

            # Handle pagination
            if paginate:
                next_page = self._get_next_page(response_data)
                page_count = 1

                while next_page and page_count < max_pages:
                    await asyncio.sleep(self.rate_limit)

                    response = await self._make_request(
                        method=method,
                        url=next_page if next_page.startswith('http') else f"{self.base_url}/{next_page}",
                        headers=headers
                    )

                    response_data = response.json()

                    if isinstance(response_data, list):
                        results.extend(response_data)
                    elif 'data' in response_data:
                        results.extend(response_data['data'])

                    next_page = self._get_next_page(response_data)
                    page_count += 1

            return results

        except httpx.HTTPStatusError as e:
            raise APIError(f"API request failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise APIError(f"API polling failed: {e}")

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict,
        params: Dict = None,
        json: Any = None,
        retry: int = 3
    ) -> httpx.Response:
        """Make HTTP request with retry"""
        for attempt in range(retry):
            try:
                response = await self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json
                )
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except httpx.RequestError as e:
                if attempt == retry - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    def _get_auth_headers(self) -> Dict:
        """Get authentication headers"""
        headers = {'Content-Type': 'application/json'}

        if self.auth_type == "api_key":
            headers['X-API-Key'] = self.api_key
        elif self.auth_type == "bearer":
            headers['Authorization'] = f'Bearer {self.oauth_token}'
        elif self.auth_type == "oauth2":
            headers['Authorization'] = f'Bearer {self.oauth_token}'

        return headers

    def _get_next_page(self, response_data: Dict) -> Optional[str]:
        """Extract next page URL/token from response"""
        # Check common pagination patterns
        if isinstance(response_data, dict):
            # Cursor-based
            if 'next_cursor' in response_data:
                return response_data['next_cursor']

            # Link-based
            if 'next' in response_data:
                return response_data['next']

            # Page-based
            if 'pagination' in response_data:
                pagination = response_data['pagination']
                if pagination.get('has_more') or pagination.get('next_page'):
                    return pagination.get('next_page') or pagination.get('next_url')

        return None

class APIError(Exception):
    """API polling error"""
    pass
```

---

### 3. File Parser Module

**Purpose**: Parse various file formats

**Supported Formats**: Excel, CSV, PDF, JSON, XML

**Implementation**:
```python
# src/collectors/file_parser.py

from typing import List, Dict, Any
import pandas as pd
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from openpyxl import load_workbook
import PyPDF2

class FileParser:
    """Universal file parser"""

    @staticmethod
    def parse(file_path: str) -> List[Dict]:
        """
        Parse file based on extension

        Args:
            file_path: Path to file

        Returns:
            List of parsed records
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        parsers = {
            '.csv': FileParser._parse_csv,
            '.xlsx': FileParser._parse_excel,
            '.xls': FileParser._parse_excel,
            '.json': FileParser._parse_json,
            '.xml': FileParser._parse_xml,
            '.pdf': FileParser._parse_pdf
        }

        parser = parsers.get(extension)
        if not parser:
            raise ValueError(f"Unsupported file format: {extension}")

        return parser(file_path)

    @staticmethod
    def _parse_csv(file_path: str) -> List[Dict]:
        """Parse CSV file"""
        df = pd.read_csv(file_path)
        return df.to_dict('records')

    @staticmethod
    def _parse_excel(file_path: str) -> List[Dict]:
        """Parse Excel file"""
        # Try pandas first (faster)
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            return df.to_dict('records')
        except:
            # Fallback to openpyxl for complex files
            wb = load_workbook(file_path, data_only=True)
            ws = wb.active

            # Get headers from first row
            headers = [cell.value for cell in ws[1]]

            # Parse data rows
            records = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                record = {headers[i]: row[i] for i in range(len(headers))}
                records.append(record)

            return records

    @staticmethod
    def _parse_json(file_path: str) -> List[Dict]:
        """Parse JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Look for common data keys
            for key in ['data', 'results', 'items', 'records']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Single record
            return [data]

        return []

    @staticmethod
    def _parse_xml(file_path: str) -> List[Dict]:
        """Parse XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        records = []

        # Assume each child of root is a record
        for child in root:
            record = {}
            for elem in child:
                record[elem.tag] = elem.text
            records.append(record)

        return records

    @staticmethod
    def _parse_pdf(file_path: str) -> List[Dict]:
        """Parse PDF file (text extraction)"""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            text_pages = []
            for page in reader.pages:
                text = page.extract_text()
                text_pages.append({'page_text': text})

            return text_pages
```

---

## Processing Pipeline

### Data Processing Flow

```python
# src/processors/data_pipeline.py

from typing import List, Dict, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStep:
    """Processing step configuration"""
    name: str
    function: Callable
    enabled: bool = True
    on_error: str = "skip"  # skip, stop, retry

class DataPipeline:
    """
    Modular data processing pipeline

    Steps:
    1. Validation
    2. Cleaning
    3. Transformation
    4. Extraction
    5. Enrichment
    """

    def __init__(self):
        self.steps: List[ProcessingStep] = []

    def add_step(self, step: ProcessingStep):
        """Add processing step"""
        self.steps.append(step)

    async def process(self, data: List[Dict]) -> List[Dict]:
        """
        Process data through pipeline

        Args:
            data: Raw data records

        Returns:
            Processed data records
        """
        processed_data = data

        for step in self.steps:
            if not step.enabled:
                continue

            logger.info(f"Running step: {step.name}")

            try:
                processed_data = await self._run_step(step, processed_data)
                logger.info(f"Step {step.name} completed: {len(processed_data)} records")

            except Exception as e:
                logger.error(f"Step {step.name} failed: {e}")

                if step.on_error == "stop":
                    raise
                elif step.on_error == "skip":
                    logger.warning(f"Skipping step {step.name}")
                    continue
                elif step.on_error == "retry":
                    # Retry once
                    try:
                        processed_data = await self._run_step(step, processed_data)
                    except:
                        logger.error(f"Retry failed for {step.name}")
                        if step.on_error == "stop":
                            raise

        return processed_data

    async def _run_step(self, step: ProcessingStep, data: List[Dict]) -> List[Dict]:
        """Run processing step"""
        if asyncio.iscoroutinefunction(step.function):
            return await step.function(data)
        else:
            return step.function(data)


# Example processing functions

def validate_schema(data: List[Dict]) -> List[Dict]:
    """Validate data against schema"""
    valid_data = []

    for record in data:
        # Check required fields
        if 'product_code' in record and 'product_name' in record:
            valid_data.append(record)

    return valid_data

def deduplicate(data: List[Dict]) -> List[Dict]:
    """Remove duplicates"""
    seen = set()
    unique_data = []

    for record in data:
        # Use product_code as unique key
        key = record.get('product_code')
        if key and key not in seen:
            seen.add(key)
            unique_data.append(record)

    return unique_data

def normalize_fields(data: List[Dict]) -> List[Dict]:
    """Normalize field values"""
    for record in data:
        # Normalize strings
        if 'product_name' in record:
            record['product_name'] = record['product_name'].strip()

        # Normalize numbers
        if 'capacity_ml' in record and isinstance(record['capacity_ml'], str):
            try:
                record['capacity_ml'] = float(record['capacity_ml'].replace(',', ''))
            except:
                record['capacity_ml'] = None

    return data

async def extract_entities(data: List[Dict]) -> List[Dict]:
    """Extract entities from text"""
    from src.core.ocr_processors.entity_extractor import EntityExtractor

    extractor = EntityExtractor()

    for record in data:
        if 'product_name' in record:
            entities = extractor.extract(record['product_name'])
            record.update(entities)

    return data

# Usage example
async def process_collected_data(raw_data: List[Dict]) -> List[Dict]:
    """Process collected data"""
    pipeline = DataPipeline()

    # Add steps
    pipeline.add_step(ProcessingStep(
        name="Validation",
        function=validate_schema,
        on_error="skip"
    ))

    pipeline.add_step(ProcessingStep(
        name="Deduplication",
        function=deduplicate,
        on_error="skip"
    ))

    pipeline.add_step(ProcessingStep(
        name="Normalization",
        function=normalize_fields,
        on_error="skip"
    ))

    pipeline.add_step(ProcessingStep(
        name="Entity Extraction",
        function=extract_entities,
        on_error="skip"
    ))

    # Process
    processed_data = await pipeline.process(raw_data)

    return processed_data
```

---

## Database Integration

**Multi-database support**:
```python
# src/collectors/db_integrator.py

from typing import List, Dict
from sqlalchemy import create_engine, Table, MetaData, insert
from qdrant_client import QdrantClient, models
import asyncio

class DatabaseIntegrator:
    """Integrate processed data into databases"""

    def __init__(
        self,
        postgres_url: str,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333
    ):
        self.pg_engine = create_engine(postgres_url)
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)

    async def store(
        self,
        data: List[Dict],
        tenant_id: str,
        store_postgres: bool = True,
        store_qdrant: bool = True
    ):
        """
        Store data in multiple databases

        Args:
            data: Processed data
            tenant_id: Tenant ID for multi-tenancy
            store_postgres: Store in PostgreSQL
            store_qdrant: Store in Qdrant (for RAG)
        """
        if store_postgres:
            await self._store_postgres(data, tenant_id)

        if store_qdrant:
            await self._store_qdrant(data, tenant_id)

    async def _store_postgres(self, data: List[Dict], tenant_id: str):
        """Store in PostgreSQL"""
        # Insert into collected_products table
        with self.pg_engine.connect() as conn:
            for record in data:
                record['tenant_id'] = tenant_id

            # Batch insert
            # (Assuming table schema matches record structure)
            conn.execute(
                insert(collected_products_table),
                data
            )
            conn.commit()

    async def _store_qdrant(self, data: List[Dict], tenant_id: str):
        """Store in Qdrant for RAG"""
        from src.core.embedding_service import EmbeddingService

        embeddings_service = EmbeddingService()

        # Generate embeddings
        texts = [f"{r.get('product_name', '')} {r.get('product_code', '')}" for r in data]
        embeddings = await embeddings_service.embed_batch(texts)

        # Prepare points
        points = []
        for i, record in enumerate(data):
            point = models.PointStruct(
                id=hash(f"{tenant_id}_{record['product_code']}") & 0xFFFFFFFF,
                vector=embeddings[i],
                payload={
                    **record,
                    "tenant_id": tenant_id
                }
            )
            points.append(point)

        # Upsert to Qdrant
        collection_name = f"tenant_{tenant_id}_products"

        # Ensure collection exists
        try:
            self.qdrant.get_collection(collection_name)
        except:
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )

        # Batch upsert
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points
        )
```

---

## Scheduling & Orchestration

```python
# src/collectors/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class CollectorScheduler:
    """Schedule data collection jobs"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def add_job(
        self,
        func: Callable,
        trigger: str = "cron",
        **trigger_args
    ):
        """
        Add scheduled job

        Args:
            func: Job function
            trigger: Trigger type (cron, interval, date)
            **trigger_args: Trigger arguments

        Example:
            scheduler.add_job(
                collect_products,
                trigger="cron",
                hour=2,  # Run at 2 AM daily
                minute=0
            )
        """
        self.scheduler.add_job(
            func,
            trigger=trigger,
            **trigger_args
        )

    def start(self):
        """Start scheduler"""
        self.scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


# Example usage
async def daily_collection_job():
    """Daily data collection job"""
    from src.collectors.web_scraper import ProductScraper
    from src.processors.data_pipeline import process_collected_data
    from src.collectors.db_integrator import DatabaseIntegrator

    logger.info("Starting daily collection job")

    # 1. Collect data
    scraper = ProductScraper()
    raw_data = await scraper.scrape(ScrapeConfig(
        url="https://example.com/products",
        pagination=True,
        max_pages=10
    ))

    # 2. Process data
    processed_data = await process_collected_data(raw_data)

    # 3. Store data
    integrator = DatabaseIntegrator(
        postgres_url="postgresql://user:pass@localhost/db"
    )
    await integrator.store(
        data=processed_data,
        tenant_id="system"
    )

    logger.info(f"Collection job completed: {len(processed_data)} products")

# Setup scheduler
scheduler = CollectorScheduler()

# Run daily at 2 AM
scheduler.add_job(
    daily_collection_job,
    trigger="cron",
    hour=2,
    minute=0
)

scheduler.start()
```

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
