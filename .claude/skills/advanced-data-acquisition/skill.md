# Advanced Data Acquisition Skill

**Purpose**: Comprehensive data crawling and extraction with authentication, anti-bot evasion, and complex file processing

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Project**: rag-enterprise

---

## 📖 Overview

This skill provides enterprise-grade data acquisition capabilities including:
- Multi-strategy web crawling (static, dynamic, API)
- Authentication handling (Basic, OAuth, 2FA/TOTP)
- Anti-bot evasion techniques
- Advanced Excel/PDF/Document processing
- Session management and cookie handling

## ⚠️  Legal & Ethical Use Only

**This skill is for AUTHORIZED use only**:
- ✅ Your own systems and accounts
- ✅ Systems with explicit permission
- ✅ Automated testing of your applications
- ✅ Data you have legal right to access

**NEVER use for**:
- ❌ Unauthorized access
- ❌ Bypassing security without permission
- ❌ Accessing others' accounts
- ❌ Violating Terms of Service

---

## 📋 Commands

### `crawl`
Crawl websites with various strategies

**Usage**:
```
/advanced-data-acquisition crawl [--method=<method>] [--url=<url>] [--auth=<type>]
```

**Options**:
- `--method`: `static` | `dynamic` | `api` (default: `auto`)
- `--url`: Target URL
- `--auth`: `none` | `basic` | `oauth` | `session` | `2fa`

**Examples**:
```bash
# Static HTML crawling
/advanced-data-acquisition crawl --method=static --url=https://example.com

# Dynamic JavaScript site
/advanced-data-acquisition crawl --method=dynamic --url=https://react-app.com

# With authentication
/advanced-data-acquisition crawl --url=https://portal.com --auth=oauth
```

---

### `login`
Handle authentication and session management

**Usage**:
```
/advanced-data-acquisition login [--type=<type>] [--credentials=<path>]
```

**Options**:
- `--type`: `basic` | `form` | `oauth` | `2fa-totp` | `api-key`
- `--credentials`: Path to credentials file (JSON)

**Credentials File Format**:
```json
{
  "type": "oauth",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "redirect_uri": "http://localhost:8080/callback"
}
```

**Examples**:
```bash
# OAuth login
/advanced-data-acquisition login --type=oauth --credentials=oauth_creds.json

# 2FA/TOTP (for own accounts)
/advanced-data-acquisition login --type=2fa-totp --credentials=totp_config.json
```

---

### `process-excel`
Advanced Excel file processing

**Usage**:
```
/advanced-data-acquisition process-excel [--file=<path>] [--extract=<features>]
```

**Options**:
- `--file`: Excel file path
- `--extract`: `data` | `images` | `charts` | `styles` | `all` (default: `all`)

**Examples**:
```bash
# Extract everything
/advanced-data-acquisition process-excel --file=complex.xlsx --extract=all

# Only data and images
/advanced-data-acquisition process-excel --file=report.xlsx --extract=data,images
```

---

### `evade`
Configure anti-bot evasion strategies

**Usage**:
```
/advanced-data-acquisition evade [--strategies=<list>]
```

**Options**:
- `--strategies`: `user-agent` | `proxy` | `delay` | `stealth` | `all`

**Examples**:
```bash
# Enable all evasion techniques
/advanced-data-acquisition evade --strategies=all

# Specific techniques
/advanced-data-acquisition evade --strategies=user-agent,delay
```

---

### `session`
Manage crawling sessions

**Usage**:
```
/advanced-data-acquisition session [--action=<action>] [--name=<session>]
```

**Options**:
- `--action`: `save` | `load` | `list` | `delete`
- `--name`: Session identifier

**Examples**:
```bash
# Save current session
/advanced-data-acquisition session --action=save --name=my-portal

# Reuse saved session
/advanced-data-acquisition session --action=load --name=my-portal
```

---

## 🔧 Implementation Modules

### Module 1: Multi-Strategy Crawler

```python
# app/services/crawling/multi_strategy_crawler.py

from enum import Enum
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class CrawlMethod(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    API = "api"
    AUTO = "auto"

class BaseCrawler(ABC):
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> str:
        pass

class StaticCrawler(BaseCrawler):
    """BeautifulSoup for static HTML"""
    async def crawl(self, url: str, **kwargs) -> str:
        # Implementation from crawler_agent.py
        pass

class DynamicCrawler(BaseCrawler):
    """Playwright for JavaScript sites"""
    async def crawl(self, url: str, **kwargs) -> str:
        # Playwright implementation
        pass

class APICrawler(BaseCrawler):
    """Direct API calls"""
    async def crawl(self, url: str, **kwargs) -> str:
        # API implementation
        pass

class MultiStrategyCrawler:
    def __init__(self):
        self.crawlers = {
            CrawlMethod.STATIC: StaticCrawler(),
            CrawlMethod.DYNAMIC: DynamicCrawler(),
            CrawlMethod.API: APICrawler()
        }

    async def detect_method(self, url: str) -> CrawlMethod:
        """Auto-detect best crawling method"""
        # Try static first (fastest)
        # If JavaScript detected, switch to dynamic
        # If API endpoint, use API crawler
        pass

    async def crawl(self, url: str, method: CrawlMethod = CrawlMethod.AUTO) -> str:
        if method == CrawlMethod.AUTO:
            method = await self.detect_method(url)

        crawler = self.crawlers[method]
        return await crawler.crawl(url)
```

---

### Module 2: Authentication Manager

```python
# app/services/crawling/auth_manager.py

from enum import Enum
from typing import Optional, Dict
import pyotp
from requests_oauthlib import OAuth2Session

class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    FORM = "form"
    OAUTH = "oauth"
    TOTP = "2fa-totp"
    API_KEY = "api-key"

class AuthenticationManager:
    def __init__(self):
        self.sessions = {}

    async def authenticate(self, auth_type: AuthType, credentials: Dict) -> Any:
        """Authenticate and return session/token"""
        if auth_type == AuthType.BASIC:
            return self._basic_auth(credentials)
        elif auth_type == AuthType.OAUTH:
            return await self._oauth_flow(credentials)
        elif auth_type == AuthType.TOTP:
            return await self._totp_auth(credentials)
        elif auth_type == AuthType.API_KEY:
            return self._api_key_auth(credentials)

    def _basic_auth(self, creds: Dict):
        """HTTP Basic Authentication"""
        from requests.auth import HTTPBasicAuth
        return HTTPBasicAuth(creds['username'], creds['password'])

    async def _oauth_flow(self, creds: Dict):
        """OAuth 2.0 Flow"""
        oauth = OAuth2Session(
            creds['client_id'],
            redirect_uri=creds['redirect_uri']
        )

        # Get authorization URL
        auth_url, state = oauth.authorization_url(creds['auth_url'])

        # User must visit auth_url (return to user)
        # After user authorizes, exchange code for token
        # token = oauth.fetch_token(...)

        return oauth

    async def _totp_auth(self, creds: Dict):
        """TOTP/2FA Authentication (for own accounts)"""
        totp = pyotp.TOTP(creds['secret'])
        current_code = totp.now()

        return {
            'username': creds['username'],
            'password': creds['password'],
            'totp_code': current_code
        }

    def _api_key_auth(self, creds: Dict):
        """API Key Authentication"""
        return {
            'Authorization': f"Bearer {creds['api_key']}"
        }
```

---

### Module 3: Advanced Excel Processor

```python
# app/services/data_processing/excel_processor.py

import openpyxl
from openpyxl.utils import get_column_letter
from PIL import Image
import io
import json
from typing import Dict, List, Any

class AdvancedExcelProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.wb = openpyxl.load_workbook(file_path, data_only=False)

    def extract_all(self) -> Dict[str, Any]:
        """Extract everything from Excel"""
        result = {
            'metadata': self._get_metadata(),
            'sheets': {}
        }

        for sheet_name in self.wb.sheetnames:
            sheet = self.wb[sheet_name]
            result['sheets'][sheet_name] = {
                'data': self._extract_data(sheet),
                'merged_cells': self._extract_merged(sheet),
                'images': self._extract_images(sheet),
                'styles': self._extract_styles(sheet)
            }

        return result

    def _extract_merged(self, sheet) -> List[Dict]:
        """Handle merged cells"""
        merged = []
        for merged_range in sheet.merged_cells.ranges:
            min_row, min_col = merged_range.min_row, merged_range.min_col
            cell = sheet.cell(min_row, min_col)

            merged.append({
                'range': str(merged_range),
                'value': cell.value,
                'spans': {
                    'rows': merged_range.max_row - merged_range.min_row + 1,
                    'cols': merged_range.max_col - merged_range.min_col + 1
                }
            })

        return merged

    def _extract_images(self, sheet) -> List[Dict]:
        """Extract embedded images"""
        images = []
        for idx, image in enumerate(sheet._images):
            img_data = image._data()
            pil_img = Image.open(io.BytesIO(img_data))

            # Save image
            img_path = f"extracted_images/sheet_{sheet.title}_img_{idx}.{pil_img.format.lower()}"
            pil_img.save(img_path)

            images.append({
                'path': img_path,
                'width': pil_img.width,
                'height': pil_img.height,
                'format': pil_img.format
            })

        return images

    def _extract_styles(self, sheet) -> Dict:
        """Extract cell formatting"""
        # Implementation as shown in ADVANCED_CRAWLING_STRATEGY.md
        pass

    def _extract_data(self, sheet) -> List[List]:
        """Extract data with merged cell handling"""
        data = []
        merged_map = {}  # Map of cells to their merged value

        # Build merged cell map
        for merged_range in sheet.merged_cells.ranges:
            value = sheet.cell(merged_range.min_row, merged_range.min_col).value
            for row in range(merged_range.min_row, merged_range.max_row + 1):
                for col in range(merged_range.min_col, merged_range.max_col + 1):
                    merged_map[(row, col)] = value

        # Extract data
        for row_idx, row in enumerate(sheet.iter_rows(), start=1):
            row_data = []
            for col_idx, cell in enumerate(row, start=1):
                if (row_idx, col_idx) in merged_map:
                    row_data.append(merged_map[(row_idx, col_idx)])
                else:
                    row_data.append(cell.value)
            data.append(row_data)

        return data

    def _get_metadata(self) -> Dict:
        """Extract workbook metadata"""
        props = self.wb.properties
        return {
            'creator': props.creator,
            'created': props.created.isoformat() if props.created else None,
            'modified': props.modified.isoformat() if props.modified else None,
            'sheets': self.wb.sheetnames
        }
```

---

### Module 4: Anti-Bot Evasion

```python
# app/services/crawling/evasion.py

import random
import time
from fake_useragent import UserAgent
from typing import List, Optional

class AntiDetectionManager:
    def __init__(self):
        self.ua = UserAgent()
        self.proxies = []

    def get_random_headers(self) -> Dict[str, str]:
        """Generate random but realistic headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def human_delay(self, min_sec: float = 1, max_sec: float = 3):
        """Random delay to mimic human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))

    def get_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    async def apply_stealth(self, page):
        """Apply stealth techniques to Playwright page"""
        # Remove webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Add plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # Add languages
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
```

---

### Module 5: Session Manager

```python
# app/services/crawling/session_manager.py

import pickle
from pathlib import Path
from typing import Optional
import requests

class SessionManager:
    def __init__(self, storage_dir: str = ".sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_session(self, name: str, session: requests.Session):
        """Save session cookies to disk"""
        session_path = self.storage_dir / f"{name}.pkl"
        with open(session_path, 'wb') as f:
            pickle.dump(session.cookies, f)

    def load_session(self, name: str) -> Optional[requests.Session]:
        """Load session from disk"""
        session_path = self.storage_dir / f"{name}.pkl"
        if not session_path.exists():
            return None

        session = requests.Session()
        with open(session_path, 'rb') as f:
            session.cookies.update(pickle.load(f))

        return session

    def verify_session(self, session: requests.Session, check_url: str) -> bool:
        """Verify session is still valid"""
        response = session.get(check_url, allow_redirects=False)
        # If redirected to login, session is invalid
        return response.status_code == 200 and 'login' not in response.url.lower()

    async def get_or_create_session(
        self,
        name: str,
        check_url: str,
        login_func
    ) -> requests.Session:
        """Get existing session or create new one"""
        session = self.load_session(name)

        if session and self.verify_session(session, check_url):
            print(f"✅ Reusing session: {name}")
            return session

        print(f"🔐 Creating new session: {name}")
        session = requests.Session()
        await login_func(session)
        self.save_session(name, session)

        return session
```

---

## 📚 Integration Examples

### Example 1: Crawl Dynamic Site with OAuth

```python
from app.services.crawling.multi_strategy_crawler import MultiStrategyCrawler, CrawlMethod
from app.services.crawling.auth_manager import AuthenticationManager, AuthType

async def crawl_protected_site():
    # Step 1: Authenticate
    auth_manager = AuthenticationManager()
    oauth_session = await auth_manager.authenticate(
        AuthType.OAUTH,
        {
            'client_id': 'your-id',
            'client_secret': 'your-secret',
            'redirect_uri': 'http://localhost:8080/callback',
            'auth_url': 'https://provider.com/oauth/authorize'
        }
    )

    # Step 2: Crawl with authenticated session
    crawler = MultiStrategyCrawler()
    content = await crawler.crawl(
        'https://protected-site.com/data',
        method=CrawlMethod.DYNAMIC,
        session=oauth_session
    )

    return content
```

### Example 2: Process Complex Excel

```python
from app.services.data_processing.excel_processor import AdvancedExcelProcessor

def process_complex_excel(file_path):
    processor = AdvancedExcelProcessor(file_path)

    # Extract everything
    data = processor.extract_all()

    # Access specific sheets
    sheet1_data = data['sheets']['Sheet1']['data']
    merged_cells = data['sheets']['Sheet1']['merged_cells']
    images = data['sheets']['Sheet1']['images']

    # Save to JSON
    with open('output.json', 'w') as f:
        json.dump(data, f, indent=2)

    return data
```

### Example 3: Crawl with Anti-Detection

```python
from app.services.crawling.evasion import AntiDetectionManager
from playwright.async_api import async_playwright

async def crawl_with_evasion(url):
    evasion = AntiDetectionManager()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={'server': evasion.get_proxy()} if evasion.proxies else None
        )

        context = await browser.new_context(
            user_agent=evasion.get_random_headers()['User-Agent']
        )

        page = await context.new_page()

        # Apply stealth
        await evasion.apply_stealth(page)

        # Navigate
        await page.goto(url)

        # Human-like delay
        evasion.human_delay(2, 5)

        content = await page.content()
        await browser.close()

        return content
```

---

## 🎓 Best Practices

### 1. Always Get Permission
```python
# Before crawling, check:
# 1. Terms of Service
# 2. robots.txt
# 3. Get explicit permission if needed

import requests

def check_robots_txt(base_url, path):
    robots_url = f"{base_url}/robots.txt"
    response = requests.get(robots_url)

    if response.status_code == 200:
        # Parse robots.txt
        for line in response.text.split('\n'):
            if 'Disallow' in line and path in line:
                return False  # Not allowed

    return True  # Allowed
```

### 2. Implement Rate Limiting
```python
from ratelimit import limits, sleep_and_retry

class RateLimitedCrawler:
    @sleep_and_retry
    @limits(calls=10, period=60)  # 10 requests per minute
    async def crawl(self, url):
        # Crawling logic
        pass
```

### 3. Handle Errors Gracefully
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustCrawler:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def crawl(self, url):
        try:
            # Crawling logic
            pass
        except Exception as e:
            logger.error(f"Crawl failed: {url} - {e}")
            raise
```

---

## 📖 Related Documentation

- [Advanced Crawling Strategy](../../../docs/ADVANCED_CRAWLING_STRATEGY.md)
- [Data Collector Architecture](../../../docs/DATA_COLLECTOR_ARCHITECTURE.md)
- [Web Crawler Pipeline Skill](../web-crawler-pipeline/skill.md)

---

**Skill Version**: 1.0.0
**Last Updated**: 2025-11-08
**Maintainer**: RAG Enterprise Team
