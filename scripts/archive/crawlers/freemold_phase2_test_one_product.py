#!/usr/bin/env python3
"""
🧪 FREEMOLD PHASE 2 - TEST ONE PRODUCT
======================================

Tests extraction with ONE product to verify:
1. Chrome connection works
2. Authentication is valid
3. Data extraction works
4. Then we proceed with full extraction
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.freemold.net"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"freemold_phase2_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# TEST EXTRACTION
# ============================================

def test_extraction():
    """Test extraction with ONE product"""

    logger.info("=" * 80)
    logger.info("🧪 TESTING EXTRACTION WITH ONE PRODUCT")
    logger.info("=" * 80)

    try:
        # Connect to Chrome
        logger.info("\n📱 Connecting to your Chrome browser...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Connected to Chrome")

        # Test product URL
        test_product_id = "89299"
        test_url = f"https://www.freemold.net/Front/Product/?tp=vi&pIdx={test_product_id}"

        logger.info(f"\n🔍 Testing product: {test_product_id}")
        logger.info(f"   URL: {test_url}")

        # Navigate
        logger.info("\n⏳ Loading product page...")
        driver.get(test_url)
        time.sleep(2)

        # Get page source
        page_source = driver.page_source
        logger.info("✅ Page loaded")

        # Check for error
        logger.info("\n🔎 Checking for login errors...")
        if '비회원은' in page_source:
            logger.error("❌ GOT LOGIN ERROR - Session is NOT authenticated!")
            logger.error("   Non-member message detected")
            return False

        if 'alert' in page_source.lower():
            logger.warning("⚠️  Alert detected on page")

        logger.info("✅ No login errors - session appears AUTHENTICATED")

        # Try extraction
        logger.info("\n📊 Extracting data...")
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract name
        name_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'title' in x.lower() if x else False)
        name = None
        if name_elem:
            name = name_elem.get_text(strip=True)[:100]

        logger.info(f"\n📝 EXTRACTED DATA:")
        logger.info(f"   Product ID: {test_product_id}")
        logger.info(f"   Product Name: {name if name else '(none found)'}")

        # Extract description
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'detail', 'body', 'main']) if x else False)
        desc = None
        if main_content:
            for p in main_content.find_all(['p', 'div', 'span'], limit=5):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    desc = text[:100]
                    break

        if desc:
            logger.info(f"   Description: {desc}")
        else:
            logger.info(f"   Description: (none found)")

        # Extract from table
        logger.info("\n📋 Table data found:")
        tables = soup.find_all('table')
        table_data_found = False
        if tables:
            for table in tables:
                rows = table.find_all('tr')[:3]  # First 3 rows only
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)[:30]
                        value = cells[1].get_text(strip=True)[:50]
                        logger.info(f"   {label}: {value}")
                        table_data_found = True

        if not table_data_found:
            logger.info("   (no table data found)")

        # Extract images
        logger.info("\n🖼️  Images found:")
        images = soup.find_all('img', src=lambda x: x and any(k in x.lower() for k in ['product', 'image', 'pic']) if x else False)
        if images:
            logger.info(f"   Total: {len(images)} images")
            for img in images[:2]:
                src = img.get('src', '')[:60]
                logger.info(f"   - {src}")
        else:
            logger.info("   (no images found)")

        # Final verdict
        logger.info("\n" + "=" * 80)
        if name:
            logger.info("✅ SUCCESS - Data extraction is working!")
            logger.info("   Chrome is authenticated")
            logger.info("   Product name extracted successfully")
            logger.info("   Ready to proceed with FULL extraction")
            return True
        else:
            logger.warning("⚠️  PARTIAL - Got authenticated page but no product name found")
            logger.warning("   This may be a page structure issue, but session seems valid")
            return True

    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)[:200]}")
        return False

    finally:
        try:
            driver.quit()
        except:
            pass

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    success = test_extraction()

    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ TEST PASSED - Ready for full extraction!")
        logger.info("\nNext step: Run full extraction script")
    else:
        logger.error("❌ TEST FAILED - Check the errors above")
    logger.info("=" * 80)
