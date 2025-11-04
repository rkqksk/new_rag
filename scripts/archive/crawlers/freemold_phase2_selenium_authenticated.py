#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 2 - SELENIUM AUTHENTICATED EXTRACTION
============================================================

Keeps authenticated Selenium browser session alive
- User logs in manually
- Script maintains authenticated session
- Extracts: name, description, specs, manufacturer, supplier, contact, images, related products
- Serial extraction with checkpointing every 50 products
- Resume capability

"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.freemold.net"

# Output directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Files
URLS_FILE = OUTPUT_DIR / "product_urls.jsonl"
OUTPUT_FILE = OUTPUT_DIR / "products_text_complete.jsonl"
PROGRESS_FILE = OUTPUT_DIR / "freemold_phase2_progress.json"
SUMMARY_FILE = OUTPUT_DIR / "freemold_extraction_summary.json"

# Setup logging
log_file = LOG_DIR / f"freemold_phase2_selenium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# PROGRESS TRACKING
# ============================================

def load_progress():
    """Load progress from checkpoint file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'phase': 'extraction',
        'products_extracted': 0,
        'products_with_errors': 0,
        'last_product_id': None,
        'start_time': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save progress to checkpoint file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ============================================
# AUTHENTICATION & LOGIN
# ============================================

def setup_authenticated_browser():
    """Setup Chrome browser and wait for user login"""

    logger.info("=" * 80)
    logger.info("🔐 FREEMOLD AUTHENTICATION - MANUAL LOGIN")
    logger.info("=" * 80)

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # NOT headless - we want visible window for login!

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # Navigate to homepage
    logger.info("\n📱 Opening Freemold.net in Chrome...")
    driver.get(BASE_URL)
    time.sleep(2)

    logger.info("\n✅ Chrome browser opened with Freemold.net")
    logger.info("📌 Please log in to your account manually")
    logger.info("⏳ Waiting for login confirmation (checking every 2 seconds)...\n")

    # Wait for user to log in manually (simple file-based trigger)
    logger.info("\n📝 Once you've logged in successfully, you can tell me to proceed.")
    logger.info("   I will detect when you signal completion...\n")

    max_wait_seconds = 600  # 10 minutes
    start_time = time.time()
    logged_in = False

    while (time.time() - start_time) < max_wait_seconds:
        try:
            # Check for trigger file that indicates user is ready
            if Path('/tmp/freemold_login_ready.flag').exists():
                logger.info("\n✅ LOGIN SIGNAL RECEIVED!")
                logger.info("   Proceeding with extraction...")
                logged_in = True
                break

            # Also check page to see if still on login error
            page_source = driver.page_source
            if '비회원은' not in page_source and 'alert' not in page_source.lower():
                # Not on error page, maybe logged in - wait a bit more to be safe
                logger.info("✓ Not on login error page, waiting for your signal...")
            else:
                logger.info("⏳ Still on login page, waiting for you to log in...")

        except Exception as e:
            pass

        time.sleep(2)

    if not logged_in:
        logger.error("\n⚠️  Login signal not received within 10 minutes")
        logger.error("Please check the Chrome browser")
        driver.quit()
        return None

    logger.info("\n✅ Browser is now authenticated and ready for data extraction")
    logger.info("🔒 Keeping session alive for Phase 2 extraction...\n")

    return driver

# ============================================
# EXTRACT PRODUCT TEXT (WITH AUTHENTICATED DRIVER)
# ============================================

def extract_product_text_selenium(driver, product_url, product_id, category, category_name):
    """
    Extract text content using authenticated Selenium browser
    """

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
        # Navigate to product page using authenticated driver
        driver.get(product_url)

        # Wait for page to load
        time.sleep(2)

        # Check if we got login page
        if '비회원은' in driver.page_source or 'alert' in driver.page_source.lower():
            logger.warning(f"⚠️  Product {product_id}: Got login redirect - session may have expired")
            return product_data

        # Parse page
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract product name
        name_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'title' in x.lower() if x else False)
        if name_elem:
            product_data['name'] = name_elem.get_text(strip=True)[:500]

        # Extract all text content
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

        # Extract from table structure
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if '제품명' in label or 'product name' in label or '상품명' in label:
                        product_data['name'] = value[:500]
                    elif '규격' in label or 'specification' in label or '스펙' in label:
                        product_data['specs']['specification'] = value
                    elif '용량' in label or 'capacity' in label or '사이즈' in label or 'size' in label:
                        product_data['specs']['capacity'] = value
                    elif '재질' in label or 'material' in label:
                        product_data['specs']['material'] = value
                    elif '원산지' in label or 'origin' in label or '제조국' in label:
                        product_data['specs']['origin'] = value
                    elif '제조사' in label or '판매처' in label or '공급업체' in label or 'manufacturer' in label or 'supplier' in label:
                        if 'supplier' in label:
                            product_data['supplier'] = value
                        else:
                            product_data['manufacturer'] = value
                    elif '연락처' in label or 'contact' in label or '전화' in label or '이메일' in label or '핸드폰' in label:
                        product_data['contact'] = value
                    elif 'moq' in label or '최소' in label or '주문' in label:
                        product_data['specs']['moq'] = value
                    elif '색상' in label or 'color' in label or 'colour' in label:
                        product_data['specs']['color'] = value
                    elif '형태' in label or 'shape' in label or '형상' in label:
                        product_data['specs']['shape'] = value

        # Extract image URLs
        images = soup.find_all('img', src=lambda x: x and ('product' in x.lower() or 'image' in x.lower() or 'pic' in x.lower()) if x else False)
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
        logger.warning(f"⚠️  Error extracting {product_id}: {str(e)[:100]}")

    return product_data

# ============================================
# MAIN EXTRACTION LOOP
# ============================================

def main():
    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2 - SELENIUM AUTHENTICATED EXTRACTION")
    logger.info("=" * 80)

    # Setup authenticated browser
    driver = setup_authenticated_browser()
    if not driver:
        logger.error("❌ Failed to authenticate. Exiting.")
        return

    try:
        # Load progress
        progress = load_progress()
        start_index = progress['products_extracted']

        logger.info(f"\n📊 Starting extraction from product {start_index}")

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
            driver.quit()
            return

        logger.info(f"📦 Loaded {len(products)} products to extract\n")

        # Extract products
        with open(OUTPUT_FILE, 'a') as out_f:
            extracted_count = 0
            error_count = 0

            for i, product in enumerate(products):
                # Extract product data
                result = extract_product_text_selenium(
                    driver,
                    product['url'],
                    product['product_id'],
                    product['category'],
                    product['category_name']
                )

                # Write to output file
                out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                out_f.flush()

                extracted_count += 1

                if result['name']:
                    logger.info(f"✅ {product['product_id']}: {result['name'][:50]}")
                else:
                    logger.warning(f"⚠️  {product['product_id']}: No name extracted")
                    error_count += 1

                # Checkpoint every 50 products
                if extracted_count % 50 == 0:
                    progress['products_extracted'] = start_index + extracted_count
                    progress['products_with_errors'] = error_count
                    progress['last_product_id'] = product['product_id']
                    save_progress(progress)
                    pct = 100 * extracted_count // len(products)
                    logger.info(f"📊 Progress: {extracted_count}/{len(products)} ({pct}%)")
                    logger.info(f"✅ Checkpoint: {extracted_count} products saved")

        # Final summary
        logger.info(f"\n" + "=" * 80)
        logger.info(f"✅ EXTRACTION COMPLETE")
        logger.info(f"=" * 80)
        logger.info(f"📊 Total extracted: {extracted_count}")
        logger.info(f"⚠️  Errors: {error_count}")
        logger.info(f"📁 Output: {OUTPUT_FILE}")

        # Save final summary
        summary = {
            'total_processed': len(products),
            'successfully_extracted': extracted_count,
            'errors': error_count,
            'start_time': progress['start_time'],
            'end_time': datetime.now().isoformat(),
            'success_rate': f"{100*extracted_count/len(products):.1f}%" if products else "0%"
        }
        with open(SUMMARY_FILE, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Update final progress
        progress['products_extracted'] = start_index + extracted_count
        progress['products_with_errors'] = error_count
        progress['phase'] = 'extraction_complete'
        save_progress(progress)

        logger.info("\n✅ All data saved successfully!")

    finally:
        logger.info("\n🔒 Closing authenticated browser session...")
        driver.quit()
        logger.info("✅ Browser closed")

if __name__ == "__main__":
    main()
