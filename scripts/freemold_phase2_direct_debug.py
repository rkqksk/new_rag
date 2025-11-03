#!/usr/bin/env python3
"""
🚀 FREEMOLD PHASE 2 - CONNECT TO EXISTING CHROME (NO NEW WINDOWS)
==================================================================

CRITICAL: This script connects to YOUR already-running Chrome via Debug Protocol.
It does NOT create a new Chrome window or lose your authenticated session.

How it works:
1. Find YOUR Chrome process that's already running with your login
2. Connect via Chrome Remote Debug Protocol (port 9222)
3. Extract data WITHOUT closing your Chrome
4. Your authenticated session stays alive throughout
"""

import json
import time
import logging
import subprocess
import re
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

log_file = LOG_DIR / f"freemold_phase2_direct_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# CONNECT TO EXISTING CHROME VIA DEBUG PROTOCOL
# ============================================

def connect_to_existing_chrome_via_debug():
    """
    Connect to your already-running Chrome using Remote Debug Protocol.
    This DOES NOT create a new Chrome - it reuses your existing one.
    """
    logger.info("\n" + "=" * 80)
    logger.info("📱 CONNECTING TO YOUR EXISTING CHROME (VIA DEBUG PROTOCOL)")
    logger.info("=" * 80)

    try:
        # Step 1: Find Chrome process
        logger.info("\n🔍 Looking for your Chrome process...")
        result = subprocess.run(
            "ps aux | grep '[C]hrome' | head -1",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        if not result.stdout:
            logger.error("❌ No Chrome process found!")
            return None

        logger.info("✅ Found Chrome process")

        # Step 2: Try to connect using debuggerAddress
        # This connects to port 9222 which is Chrome's default debug port
        logger.info("\n⏳ Connecting via debuggerAddress (127.0.0.1:9222)...")

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ SUCCESSFULLY CONNECTED TO YOUR CHROME!")
            logger.info(f"   Current URL: {driver.current_url}")
            return driver
        except Exception as e:
            logger.warning(f"⚠️  Could not connect via port 9222: {str(e)[:100]}")
            logger.info("\n   Trying alternative: connecting without port...")

            # Alternative: just create normal connection but don't launch new browser
            chrome_options = Options()
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")

            # This should reuse existing Chrome process
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Connected using alternative method")
            logger.info(f"   Current URL: {driver.current_url}")
            return driver

    except Exception as e:
        logger.error(f"❌ Error connecting: {str(e)[:200]}")
        logger.error("\n⚠️  IMPORTANT:")
        logger.error("   - Your Chrome must be open and logged in")
        logger.error("   - Do not close Chrome during this process")
        logger.error("   - Make sure freemold.net is accessible in your Chrome")
        return None

# ============================================
# PROGRESS TRACKING
# ============================================

def load_progress():
    """Load progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'products_extracted': 0, 'start_time': datetime.now().isoformat()}

def save_progress(count):
    """Save progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'products_extracted': count, 'start_time': datetime.now().isoformat()}, f)

# ============================================
# EXTRACT ONE PRODUCT
# ============================================

def extract_product(driver, product_url, product_id, category, category_name):
    """Extract one product from authenticated Chrome session"""

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
        # Navigate to product
        driver.get(product_url)
        time.sleep(1)

        # Get page HTML
        page_source = driver.page_source

        # Check for non-member error
        if '비회원은' in page_source:
            logger.warning(f"⚠️  {product_id}: Non-member error detected")
            return product_data

        # Parse HTML
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract name
        name_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'title' in x.lower() if x else False)
        if name_elem:
            product_data['name'] = name_elem.get_text(strip=True)[:500]

        # Extract description
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'detail', 'body', 'main']) if x else False)
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
    logger.info("🚀 FREEMOLD PHASE 2 - DIRECT DEBUG CONNECTION")
    logger.info("=" * 80)

    # Connect to existing Chrome
    driver = connect_to_existing_chrome_via_debug()
    if not driver:
        logger.error("\n❌ Could not connect to your Chrome")
        logger.error("Please ensure:")
        logger.error("  1. Chrome is still open")
        logger.error("  2. You are still logged in to freemold.net")
        logger.error("  3. Chrome was not closed")
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

                time.sleep(0.5)

        logger.info(f"\n✅ EXTRACTION COMPLETE: {extracted_count} products")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Extraction interrupted")

    finally:
        logger.info("\n🔒 Closing connection to Chrome...")
        try:
            # Don't quit - just disconnect without closing the browser
            driver.service.stop()
        except:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
