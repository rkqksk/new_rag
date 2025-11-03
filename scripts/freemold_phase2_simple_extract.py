#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 2 - SIMPLE EXTRACTION FROM AUTHENTICATED BROWSER
========================================================================

CRITICAL RULES:
1. NO repeated login attempts - you login once manually, we use that session
2. Connect to the SAME Chrome that is already open with your login
3. Use Selenium to read HTML directly from the authenticated session
4. No aggressive automation - just simple page reads

This script will:
1. Wait for user to confirm Chrome is ready (you're logged in)
2. Connect to that Chrome instance
3. Start extracting product pages one at a time
4. Report status after each page
5. Wait for your OK before continuing
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.freemold.net"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

URLS_FILE = OUTPUT_DIR / "product_urls.jsonl"
OUTPUT_FILE = OUTPUT_DIR / "products_text_complete.jsonl"
PROGRESS_FILE = OUTPUT_DIR / "freemold_phase2_progress.json"

# Setup logging
log_file = LOG_DIR / f"freemold_phase2_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# CONNECT TO CHROME (REUSE EXISTING INSTANCE)
# ============================================

def connect_to_chrome():
    """
    Connect to the Chrome browser that's already open with your login.
    Do NOT create a new browser.
    """
    logger.info("\n" + "=" * 80)
    logger.info("📱 CONNECTING TO YOUR AUTHENTICATED CHROME BROWSER")
    logger.info("=" * 80)

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Connected to Chrome browser")
        return driver
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error("\n⚠️  Make sure:")
        logger.error("   - Chrome browser is still open from freemold_manual_browser_login.py")
        logger.error("   - You are logged in")
        logger.error("   - Do not close Chrome during extraction")
        return None

# ============================================
# PROGRESS TRACKING
# ============================================

def load_progress():
    """Load progress from checkpoint"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'products_extracted': 0,
        'start_time': datetime.now().isoformat()
    }

def save_progress(count):
    """Save progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'products_extracted': count, 'start_time': datetime.now().isoformat()}, f)

# ============================================
# EXTRACT ONE PRODUCT
# ============================================

def extract_product(driver, product_url, product_id, category, category_name):
    """Extract one product page using Selenium to read HTML"""

    product_data = {
        'product_id': product_id,
        'url': product_url,
        'category': category,
        'category_name': category_name,
        'crawled_at': datetime.now().isoformat(),
        'name': None,
        'description': None,
        'specs': {},
        'manufacturer': None,
        'supplier': None,
        'contact': None,
        'tags': [],
        'images': [],
        'related_products': []
    }

    try:
        # Navigate to product page
        driver.get(product_url)

        # Wait briefly for page to load
        time.sleep(1)

        # Get page HTML using Selenium
        page_source = driver.page_source

        # Check if we got login error
        if '비회원은' in page_source:
            logger.warning(f"⚠️  {product_id}: Got non-member error - session may have expired")
            return product_data

        # Parse HTML
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract product name
        name_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'title' in x.lower() if x else False)
        if name_elem:
            product_data['name'] = name_elem.get_text(strip=True)[:500]

        # Extract description
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'detail', 'body', 'main']) if x else False)
        if not main_content:
            main_content = soup.find('div', {'id': lambda x: x and 'content' in x.lower() if x else False})

        if main_content:
            for p in main_content.find_all(['p', 'div', 'span'], limit=20):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    if not product_data['description']:
                        product_data['description'] = text[:2000]
                    elif len(product_data['description']) < 3000:
                        product_data['description'] += '\n' + text[:500]

        # Extract from tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if '제품명' in label or 'product name' in label:
                        product_data['name'] = value[:500]
                    elif '규격' in label or 'specification' in label:
                        product_data['specs']['specification'] = value
                    elif '용량' in label or 'capacity' in label or 'size' in label:
                        product_data['specs']['capacity'] = value
                    elif '재질' in label or 'material' in label:
                        product_data['specs']['material'] = value
                    elif '원산지' in label or 'origin' in label:
                        product_data['specs']['origin'] = value
                    elif '제조사' in label or 'manufacturer' in label:
                        product_data['manufacturer'] = value
                    elif '공급업체' in label or 'supplier' in label:
                        product_data['supplier'] = value
                    elif '연락처' in label or 'contact' in label or '전화' in label:
                        product_data['contact'] = value
                    elif 'moq' in label or '최소' in label:
                        product_data['specs']['moq'] = value
                    elif '색상' in label or 'color' in label:
                        product_data['specs']['color'] = value
                    elif '형태' in label or 'shape' in label:
                        product_data['specs']['shape'] = value

        # Extract images
        images = soup.find_all('img', src=lambda x: x and any(k in x.lower() for k in ['product', 'image', 'pic']) if x else False)
        for img in images[:10]:
            img_url = img.get('src', '')
            if img_url and not img_url.startswith('data:'):
                if not img_url.startswith('http'):
                    img_url = urljoin(BASE_URL, img_url)
                product_data['images'].append(img_url)

        # Extract tags
        keywords = soup.find_all('meta', attrs={'name': 'keywords'})
        for keyword in keywords:
            content = keyword.get('content', '')
            if content:
                product_data['tags'] = [k.strip() for k in content.split(',')][:10]

        # Extract related products
        related = soup.find_all('a', href=lambda x: x and 'pIdx=' in x if x else False)
        for link in related[:5]:
            href = link.get('href', '')
            if href and href != product_url:
                product_data['related_products'].append(href)

    except Exception as e:
        logger.error(f"❌ Error extracting {product_id}: {str(e)[:100]}")

    return product_data

# ============================================
# MAIN
# ============================================

def main():
    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2 - SIMPLE EXTRACTION")
    logger.info("=" * 80)

    # Connect to Chrome
    driver = connect_to_chrome()
    if not driver:
        return

    try:
        # Load progress
        progress = load_progress()
        start_index = progress['products_extracted']

        logger.info(f"\n📊 Starting from product {start_index}")

        # Load product URLs
        products = []
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r') as f:
                for i, line in enumerate(f):
                    if i >= start_index:
                        data = json.loads(line)
                        products.append(data)
        else:
            logger.error(f"❌ {URLS_FILE} not found!")
            return

        logger.info(f"📦 Loaded {len(products)} products to extract\n")

        # Extract products
        with open(OUTPUT_FILE, 'a') as out_f:
            extracted_count = 0

            for i, product in enumerate(products):
                # Extract
                result = extract_product(
                    driver,
                    product['url'],
                    product['product_id'],
                    product['category'],
                    product['category_name']
                )

                # Write result
                out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                out_f.flush()

                extracted_count += 1

                # Report
                if result['name']:
                    logger.info(f"✅ [{extracted_count}] {product['product_id']}: {result['name'][:40]}")
                else:
                    logger.warning(f"⚠️  [{extracted_count}] {product['product_id']}: No data")

                # Checkpoint every 100 products
                if extracted_count % 100 == 0:
                    save_progress(start_index + extracted_count)
                    pct = 100 * extracted_count // len(products) if products else 0
                    logger.info(f"\n📊 Progress: {extracted_count}/{len(products)} ({pct}%)")
                    logger.info(f"✅ Saved checkpoint\n")

                # Brief pause
                time.sleep(0.5)

        logger.info(f"\n✅ EXTRACTION COMPLETE: {extracted_count} products")

    finally:
        logger.info("\n🔒 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()
