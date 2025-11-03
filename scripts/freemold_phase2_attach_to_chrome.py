#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 2 - ATTACH TO YOUR CHROME BROWSER
=========================================================

This script CONNECTS to your already-running Chrome browser.
It does NOT create a new Chrome - it reuses YOUR Chrome with YOUR login.

How it works:
1. Find your Chrome process that's already running
2. Get its debug port
3. Connect Selenium to THAT Chrome instance
4. Extract using your authenticated session
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
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

log_file = LOG_DIR / f"freemold_phase2_attach_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# FIND YOUR CHROME PROCESS
# ============================================

def find_chrome_port():
    """
    Find your running Chrome process and get its debug port.
    Chrome must be started with --remote-debugging-port flag.
    """
    logger.info("\n" + "=" * 80)
    logger.info("🔍 LOOKING FOR YOUR CHROME BROWSER")
    logger.info("=" * 80)

    try:
        # Find Chrome processes
        result = subprocess.run(
            "ps aux | grep -i 'Google Chrome' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        if not result.stdout:
            logger.error("❌ No Chrome process found!")
            logger.info("\n⚠️  Please open Chrome manually and login first")
            return None

        logger.info(f"✅ Found Chrome process(es):")
        for line in result.stdout.split('\n')[:3]:
            if line.strip():
                logger.info(f"   {line[:100]}")

        # Try to find debug port if Chrome was started with --remote-debugging-port
        if 'remote-debugging-port' in result.stdout:
            match = re.search(r'remote-debugging-port=(\d+)', result.stdout)
            if match:
                port = int(match.group(1))
                logger.info(f"✅ Found debug port: {port}")
                return port

        logger.info("⚠️  Chrome is running but no explicit debug port found")
        logger.info("   We'll try to connect with default options...")
        return None

    except Exception as e:
        logger.error(f"Error finding Chrome: {e}")
        return None

def connect_to_running_chrome(debug_port=None):
    """
    Connect to YOUR running Chrome instance.
    """
    logger.info("\n" + "=" * 80)
    logger.info("📱 CONNECTING TO YOUR CHROME BROWSER")
    logger.info("=" * 80)

    try:
        chrome_options = Options()

        # IMPORTANT: Point to the running Chrome, not create a new one
        if debug_port:
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            logger.info(f"Connecting to debug port {debug_port}...")
        else:
            # If no explicit debug port, use default options to connect
            logger.info("Connecting with default options...")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Create driver that connects to existing Chrome
        driver = webdriver.Chrome(options=chrome_options)

        logger.info("✅ SUCCESSFULLY CONNECTED TO YOUR CHROME BROWSER!")
        logger.info(f"   Current URL: {driver.current_url}")

        return driver

    except Exception as e:
        logger.error(f"❌ Error connecting to Chrome: {e}")
        logger.error("\n⚠️  Solutions:")
        logger.error("   1. Make sure Chrome is still running")
        logger.error("   2. Make sure you're still logged in")
        logger.error("   3. Try restarting Chrome if needed")
        return None

# ============================================
# HANDLE ALERTS
# ============================================

def dismiss_alert(driver):
    """Try to dismiss any alerts"""
    try:
        alert = WebDriverWait(driver, 2).until(
            lambda d: d.switch_to.alert
        )
        logger.warning("   Alert detected, dismissing...")
        alert.dismiss()
        time.sleep(1)
    except:
        pass

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
    """Extract one product using your authenticated Chrome session"""

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
        # Dismiss any existing alerts first
        dismiss_alert(driver)

        # Navigate to product
        driver.get(product_url)
        time.sleep(1)

        # Dismiss any alerts from page load
        dismiss_alert(driver)

        # Get page HTML
        page_source = driver.page_source

        # Check for non-member error
        if '비회원은' in page_source:
            logger.warning(f"⚠️  {product_id}: Non-member error - session expired?")
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
    logger.info("🚀 FREEMOLD PHASE 2 - ATTACH TO YOUR CHROME")
    logger.info("=" * 80)

    # Step 1: Find your Chrome
    debug_port = find_chrome_port()

    # Step 2: Connect to your Chrome
    driver = connect_to_running_chrome(debug_port)
    if not driver:
        logger.error("\n❌ Could not connect to your Chrome browser")
        logger.error("Please make sure Chrome is open and you're logged in")
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
        logger.info("\n⚠️  Extraction interrupted by user")

    finally:
        logger.info("\n🔒 Closing connection to Chrome...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
