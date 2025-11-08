# Web Scraping Expert Skill

**Version**: 1.0.0
**Status**: Production Ready ✅
**Purpose**: Advanced web scraping strategies for large-scale data collection

> **Expert web scraping system** for RAG Enterprise Platform - implements 3 scraping engines, anti-bot evasion, rate limiting, error recovery, and data extraction patterns.

---

## Quick Reference

### Commands

```bash
# Engine selection
scrape analyze <url>                    # Analyze site and recommend engine
scrape test <url> --all-engines        # Test all engines on URL

# Static scraping (BeautifulSoup)
scrape static <url>                    # Fast, simple sites
scrape static <url> --selector "div.product"  # CSS selector
scrape batch urls.txt --engine static  # Batch processing

# Dynamic scraping (Playwright)
scrape dynamic <url>                   # JavaScript-heavy sites
scrape dynamic <url> --wait-for "div.loaded"  # Wait for element
scrape dynamic <url> --screenshot      # Capture screenshot

# Complex scraping (Selenium)
scrape complex <url>                   # Complex interactions
scrape complex <url> --login user:pass # Authenticated scraping
scrape complex <url> --infinite-scroll # Scroll to load more

# Anti-bot evasion
scrape evade <url> --rotate-proxies    # Rotate IP addresses
scrape evade <url> --randomize-headers # Randomize user agents
scrape evade <url> --human-delays      # Human-like delays

# Data extraction
scrape extract <url> --schema product.json  # Structured extraction
scrape validate <data> --schema product.json # Validate extracted data

# Performance optimization
scrape parallel urls.txt --workers 10  # Parallel scraping
scrape optimize <url> --target speed   # Optimize for speed
scrape benchmark urls.txt              # Benchmark engines
```

---

## Scraping Engines

### 1. BeautifulSoup (Static Content)
**Use Case**: Static HTML sites, simple product catalogs
**Status**: ✅ Current production (chunjinkorea, onehago, freemold)

**Characteristics**:
- **Speed**: ⚡⚡⚡ Fastest (50-100 pages/min)
- **Resource usage**: Minimal (< 50 MB RAM)
- **JavaScript support**: ❌ No
- **Best for**: Static HTML, simple sites

**Implementation** (`scripts/crawlers/static_scraper.py`):
```python
import requests
from bs4 import BeautifulSoup

class StaticScraper:
    """Fast scraper for static HTML sites."""

    def __init__(self, rate_limit=2.0):
        self.session = requests.Session()
        self.rate_limit = rate_limit  # Seconds between requests

    def scrape(self, url: str) -> Dict:
        """
        Scrape static HTML page.

        Steps:
        1. HTTP GET request
        2. Parse HTML with BeautifulSoup
        3. Extract data with CSS selectors
        4. Rate limiting
        """
        # Fetch HTML
        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        # Parse
        soup = BeautifulSoup(response.content, 'lxml')

        # Extract product data
        product = {
            'name': soup.select_one('h1.product-name').text.strip(),
            'price': soup.select_one('span.price').text.strip(),
            'description': soup.select_one('div.description').text.strip(),
            'images': [img['src'] for img in soup.select('img.product-image')]
        }

        # Rate limiting
        time.sleep(self.rate_limit)

        return product
```

**Production Performance** (Current crawlers):
```
chunjinkorea.com:
- Pages crawled: 1,500+
- Success rate: 98.7%
- Speed: 75 pages/min
- Engine: BeautifulSoup + lxml

onehago.com:
- Pages crawled: 800+
- Success rate: 97.2%
- Speed: 62 pages/min
- Engine: BeautifulSoup + lxml

freemold.net:
- Pages crawled: 600+
- Success rate: 96.8%
- Speed: 55 pages/min
- Engine: BeautifulSoup + lxml
```

**Best For**:
- Product catalogs (current use case)
- News sites
- Blogs
- Simple e-commerce

**Pros**:
- Fastest scraping (50-100 pages/min)
- Minimal resources
- Simple implementation
- No browser overhead

**Cons**:
- No JavaScript support
- Can't handle dynamic content
- Limited anti-bot evasion

---

### 2. Playwright (Dynamic Content)
**Use Case**: JavaScript-heavy sites, SPAs, dynamic loading

**Characteristics**:
- **Speed**: ⚡⚡ Medium (10-20 pages/min)
- **Resource usage**: Medium (~200 MB RAM/browser)
- **JavaScript support**: ✅ Full
- **Best for**: Dynamic sites, SPAs

**Implementation**:
```python
from playwright.async_api import async_playwright

class DynamicScraper:
    """Playwright-based scraper for dynamic sites."""

    async def scrape(self, url: str) -> Dict:
        """
        Scrape JavaScript-heavy site.

        Steps:
        1. Launch headless browser
        2. Navigate to URL
        3. Wait for JavaScript to load
        4. Extract data from rendered DOM
        """
        async with async_playwright() as p:
            # Launch browser (headless)
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate
            await page.goto(url, wait_until='networkidle')

            # Wait for specific element
            await page.wait_for_selector('div.products-loaded')

            # Extract data
            products = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('.product'))
                    .map(el => ({
                        name: el.querySelector('.name').textContent,
                        price: el.querySelector('.price').textContent,
                        image: el.querySelector('img').src
                    }))
            }''')

            await browser.close()
            return products
```

**Use Cases**:
- Single Page Applications (React, Vue, Angular)
- Infinite scroll pages
- AJAX-loaded content
- Real-time data updates

**Advanced Features**:
```python
# Wait for network idle (all resources loaded)
await page.goto(url, wait_until='networkidle')

# Wait for specific element
await page.wait_for_selector('div.loaded')

# Infinite scroll
for _ in range(10):
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await page.wait_for_timeout(1000)

# Screenshot
await page.screenshot(path='screenshot.png')

# Intercept requests
await page.route('**/*.jpg', lambda route: route.abort())  # Block images
```

**Performance**:
```
Speed: 10-20 pages/min
Resource usage: ~200 MB RAM per browser
Concurrency: 5-10 parallel browsers
Best for: Dynamic sites, SPAs
```

**Best For**:
- React/Vue/Angular sites
- Infinite scroll
- AJAX content
- Complex JavaScript

**Pros**:
- Full JavaScript support
- Network interception
- Screenshots
- Multiple browsers (Chromium, Firefox, WebKit)

**Cons**:
- Slower than BeautifulSoup (10-20x)
- Higher resource usage
- More complex

---

### 3. Selenium (Complex Interactions)
**Use Case**: Complex user interactions, authenticated sessions, CAPTCHAs

**Characteristics**:
- **Speed**: ⚡ Slow (5-15 pages/min)
- **Resource usage**: High (~300 MB RAM/browser)
- **JavaScript support**: ✅ Full
- **Best for**: Complex interactions, logins

**Implementation**:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ComplexScraper:
    """Selenium-based scraper for complex interactions."""

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(options=options)

    def scrape_with_login(self, url: str, username: str, password: str):
        """
        Scrape authenticated content.

        Steps:
        1. Navigate to login page
        2. Fill login form
        3. Submit and wait for redirect
        4. Navigate to target page
        5. Extract data
        """
        # Login
        self.driver.get('https://example.com/login')
        self.driver.find_element(By.ID, 'username').send_keys(username)
        self.driver.find_element(By.ID, 'password').send_keys(password)
        self.driver.find_element(By.ID, 'submit').click()

        # Wait for redirect
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/dashboard')
        )

        # Navigate to target
        self.driver.get(url)

        # Extract data
        products = self.driver.find_elements(By.CLASS_NAME, 'product')
        return [self._extract_product(p) for p in products]

    def infinite_scroll(self, url: str, scroll_count=10):
        """Scrape infinite scroll page."""
        self.driver.get(url)

        for i in range(scroll_count):
            # Scroll to bottom
            self.driver.execute_script(
                'window.scrollTo(0, document.body.scrollHeight)'
            )

            # Wait for new content
            time.sleep(2)

            # Check if loaded
            current_height = self.driver.execute_script(
                'return document.body.scrollHeight'
            )

        # Extract all products
        return self._extract_all_products()
```

**Advanced Features**:
```python
# Handle alerts
alert = self.driver.switch_to.alert
alert.accept()

# Switch frames
self.driver.switch_to.frame('iframe-name')

# Handle file uploads
file_input = self.driver.find_element(By.ID, 'file-upload')
file_input.send_keys('/path/to/file.csv')

# Execute JavaScript
result = self.driver.execute_script('return document.title')

# Cookies management
self.driver.add_cookie({'name': 'session', 'value': 'abc123'})
```

**Best For**:
- Authenticated scraping (login required)
- Complex forms
- File uploads/downloads
- CAPTCHA handling (with external services)
- Multi-step workflows

**Pros**:
- Full browser automation
- Complex interactions
- Cookie/session management
- Multiple browser support

**Cons**:
- Slowest (5-15 pages/min)
- Highest resource usage
- Most complex code
- Maintenance overhead

---

## Engine Selection Guide

### Decision Matrix

| Site Type | Recommended Engine | Reason |
|-----------|-------------------|---------|
| Static HTML | **BeautifulSoup** | Fastest, simplest |
| JavaScript SPA | **Playwright** | Full JS support |
| Infinite scroll | **Playwright** | Scroll automation |
| Login required | **Selenium** | Session management |
| Complex forms | **Selenium** | Form automation |
| AJAX-heavy | **Playwright** | Network interception |
| Simple catalog | **BeautifulSoup** | Production-proven |

### Auto-Selection Algorithm

```python
def select_scraping_engine(url: str) -> str:
    """
    Automatically select optimal scraping engine.

    Decision factors:
    1. JavaScript detection
    2. Login requirements
    3. Infinite scroll detection
    4. Site complexity
    """
    # Fetch page
    response = requests.get(url, timeout=10)
    html = response.text

    # Detect JavaScript
    has_js = 'react' in html.lower() or 'vue' in html.lower() or 'angular' in html.lower()

    # Detect login
    requires_login = 'login' in html.lower() or 'signin' in html.lower()

    # Detect infinite scroll
    has_infinite_scroll = 'infinite-scroll' in html or 'lazy-load' in html

    # Selection logic
    if requires_login:
        return "selenium"
    elif has_infinite_scroll or has_js:
        return "playwright"
    else:
        return "beautifulsoup"
```

---

## Anti-Bot Evasion Strategies

### 1. User Agent Rotation

```python
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
```

### 2. Rate Limiting (Human-Like Delays)

```python
import random
import time

class RateLimiter:
    """Human-like rate limiting."""

    def __init__(self, min_delay=1.0, max_delay=3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    def wait(self):
        """Random delay between min and max."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def smart_wait(self, error_count=0):
        """Adaptive delay based on errors."""
        if error_count > 0:
            # Exponential backoff
            delay = min(2 ** error_count, 60)
        else:
            # Normal random delay
            delay = random.uniform(self.min_delay, self.max_delay)

        time.sleep(delay)
```

### 3. Proxy Rotation

```python
class ProxyRotator:
    """Rotate proxies to avoid IP blocking."""

    def __init__(self, proxy_list):
        self.proxies = proxy_list
        self.current = 0

    def get_next_proxy(self):
        proxy = self.proxies[self.current]
        self.current = (self.current + 1) % len(self.proxies)
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }

# Usage
proxies = ['proxy1.com:8080', 'proxy2.com:8080']
rotator = ProxyRotator(proxies)

response = requests.get(url, proxies=rotator.get_next_proxy())
```

### 4. Browser Fingerprint Randomization (Playwright)

```python
async def scrape_with_stealth(url: str):
    """Scrape with anti-detection."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 ...',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060}
        )

        page = await context.new_page()

        # Hide webdriver flag
        await page.add_init_script('''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        ''')

        await page.goto(url)
        # ... scrape data
```

### 5. CAPTCHA Handling (External Services)

```python
import requests

class CaptchaSolver:
    """Solve CAPTCHAs with 2captcha service."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://2captcha.com'

    def solve_recaptcha(self, site_key, page_url):
        """Solve reCAPTCHA v2."""
        # Submit CAPTCHA
        response = requests.post(f'{self.base_url}/in.php', data={
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url
        })

        captcha_id = response.text.split('|')[1]

        # Poll for solution (max 2 minutes)
        for _ in range(24):
            time.sleep(5)
            result = requests.get(f'{self.base_url}/res.php', params={
                'key': self.api_key,
                'action': 'get',
                'id': captcha_id
            })

            if 'OK|' in result.text:
                return result.text.split('|')[1]

        raise Exception('CAPTCHA solve timeout')
```

---

## Data Extraction Patterns

### 1. Schema-Based Extraction

```python
# Define extraction schema
PRODUCT_SCHEMA = {
    'name': {'selector': 'h1.product-name', 'attr': 'text'},
    'price': {'selector': 'span.price', 'attr': 'text', 'transform': parse_price},
    'images': {'selector': 'img.product-image', 'attr': 'src', 'multiple': True},
    'specs': {
        'material': {'selector': 'td.spec-material', 'attr': 'text'},
        'capacity': {'selector': 'td.spec-capacity', 'attr': 'text'},
    }
}

def extract_with_schema(soup, schema):
    """Extract data using schema."""
    result = {}

    for field, config in schema.items():
        if isinstance(config, dict) and 'selector' in config:
            # Simple field
            elements = soup.select(config['selector'])

            if config.get('multiple'):
                # Multiple elements
                result[field] = [el.get(config['attr']) if config['attr'] != 'text'
                                 else el.text.strip() for el in elements]
            else:
                # Single element
                el = elements[0] if elements else None
                if el:
                    value = el.get(config['attr']) if config['attr'] != 'text' else el.text.strip()
                    if 'transform' in config:
                        value = config['transform'](value)
                    result[field] = value
        else:
            # Nested schema
            result[field] = extract_with_schema(soup, config)

    return result
```

### 2. Pagination Handling

```python
class PaginationScraper:
    """Handle paginated results."""

    def scrape_all_pages(self, base_url, max_pages=None):
        """Scrape all pages until no next page."""
        page = 1
        all_products = []

        while True:
            # Scrape current page
            url = f"{base_url}?page={page}"
            products = self.scrape_page(url)

            if not products:
                break  # No more products

            all_products.extend(products)

            # Check max pages
            if max_pages and page >= max_pages:
                break

            page += 1

        return all_products

    def scrape_with_next_button(self, start_url):
        """Follow 'next' button links."""
        current_url = start_url
        all_products = []

        while current_url:
            # Scrape page
            soup = self.fetch_page(current_url)
            products = self.extract_products(soup)
            all_products.extend(products)

            # Find next page link
            next_button = soup.select_one('a.next-page')
            current_url = next_button['href'] if next_button else None

        return all_products
```

### 3. Error Recovery

```python
class RobustScraper:
    """Scraper with error recovery."""

    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def scrape_with_retry(self, url):
        """Retry on failure with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return self.scrape(url)
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise

                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def scrape_with_fallback(self, url):
        """Try multiple engines on failure."""
        engines = [self.beautifulsoup_scraper, self.playwright_scraper, self.selenium_scraper]

        for engine in engines:
            try:
                return engine.scrape(url)
            except Exception as e:
                logger.warning(f"{engine.__class__.__name__} failed: {e}")
                continue

        raise Exception("All engines failed")
```

---

## Performance Optimization

### 1. Parallel Scraping

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def scrape_parallel(urls, max_workers=10):
    """Scrape multiple URLs in parallel."""
    async def scrape_one(url):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            data = await page.content()
            await browser.close()
            return data

    # Semaphore to limit concurrency
    sem = asyncio.Semaphore(max_workers)

    async def bounded_scrape(url):
        async with sem:
            return await scrape_one(url)

    results = await asyncio.gather(*[bounded_scrape(url) for url in urls])
    return results
```

**Performance**:
```
Sequential (100 URLs, 2s each): 200 seconds
Parallel (10 workers): 20 seconds (10x faster)
Parallel (20 workers): 10 seconds (20x faster)
```

### 2. Caching

```python
import hashlib
import pickle
from pathlib import Path

class CachedScraper:
    """Cache scraped pages to avoid re-scraping."""

    def __init__(self, cache_dir='cache', cache_ttl=86400):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = cache_ttl  # Seconds

    def get_cache_key(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def scrape_with_cache(self, url):
        """Scrape with file-based caching."""
        cache_key = self.get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        # Check cache
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < self.cache_ttl:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

        # Scrape
        data = self.scrape(url)

        # Save to cache
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

        return data
```

### 3. Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OptimizedScraper:
    """Scraper with connection pooling."""

    def __init__(self):
        self.session = requests.Session()

        # Retry strategy
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )

        # Connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry
        )

        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def scrape(self, url):
        # Reuses connections from pool
        response = self.session.get(url, timeout=10)
        return response.text
```

---

## Integration with RAG Pipeline

### Production Architecture (Current)

```
Web Scraping (BeautifulSoup)
  ↓
Data Extraction (CSS selectors)
  ↓
Data Cleaning & Validation
  ↓
Chunking (Atomic)
  ↓
Embedding (MiniLM-L6-v2)
  ↓
Vector Store (Qdrant)
```

### Multi-Engine Architecture (Enhanced)

```python
# app/api/v1/scraping.py
from src.scrapers import ScraperFactory

@router.post("/api/v1/scrape")
async def scrape_url(
    url: str,
    engine: str = "auto"  # auto, static, dynamic, complex
):
    """Scrape URL with auto-engine selection."""

    # Auto-select engine
    if engine == "auto":
        engine = select_scraping_engine(url)

    # Get scraper
    scraper = ScraperFactory.create(engine)

    # Scrape
    data = await scraper.scrape(url)

    # Process through RAG pipeline
    chunks = await chunking_service.chunk(data)
    embeddings = await embedding_service.embed(chunks)
    await vector_store.upsert(chunks, embeddings)

    return {
        "engine": engine,
        "products_extracted": len(data),
        "chunks_created": len(chunks)
    }
```

---

## Best Practices

### 1. Respect robots.txt
```python
from urllib.robotparser import RobotFileParser

def can_scrape(url):
    """Check if scraping is allowed."""
    rp = RobotFileParser()
    rp.set_url(f"{url}/robots.txt")
    rp.read()
    return rp.can_fetch("*", url)
```

### 2. Rate Limiting
- **Recommended**: 1-3 seconds between requests
- **Aggressive**: 0.5-1 second (risk of blocking)
- **Safe**: 3-5 seconds (production default)

### 3. Error Handling
- Retry on network errors (3 attempts max)
- Log failed URLs for later retry
- Use exponential backoff
- Implement circuit breaker for persistent failures

### 4. Data Validation
```python
from pydantic import BaseModel, validator

class Product(BaseModel):
    name: str
    price: float
    url: str

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
```

---

## References

### Implementation Files
- `scripts/crawlers/chunjinkorea_crawler.py` - Production BeautifulSoup crawler
- `scripts/crawlers/onehago_crawler.py` - Production static scraper
- `scripts/crawlers/freemold_crawler.py` - Production catalog scraper

### Related Skills
- **web-crawler-pipeline**: Complete crawling pipeline (§crawler.*)
- **data-collector**: Universal data collection (§collector.*)
- **chunking-expert**: Data chunking strategies (§chunk.*)

---

**Version**: 1.0.0 | **Status**: Production Ready | **License**: MIT
