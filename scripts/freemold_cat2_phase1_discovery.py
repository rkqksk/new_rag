#!/usr/bin/env python3
"""
FREEMOLD CATEGORY 2 (A003) - PHASE 1 DISCOVERY
Extract all product URLs for Category 2 (패키징/포장재 - Packaging/Packing Materials)

Workflow:
  Input: Manual category selection (A003)
  Process: Crawl all 1,592 pages of category A003 pagination
  Output: product_urls_a003_complete.jsonl (all unique product URLs)

Features:
  - Remote Chrome Debugging (localhost:9222)
  - Pagination crawling (all 1,592 pages)
  - Product ID extraction from pagination links
  - Deduplication using Python sets
  - Progress tracking and resumable crawling
"""

import json
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://www.freemold.net"
CATEGORY = "A003"
CATEGORY_NAME = "패키징/포장재"
TOTAL_PAGES = 1592  # Based on site structure
OUTPUT_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/product_urls_{CATEGORY}_complete.jsonl")
PROGRESS_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/phase1_{CATEGORY}_progress.json")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/tmp/freemold_phase1_{CATEGORY}_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print(f"🔄 FREEMOLD CATEGORY {CATEGORY} ({CATEGORY_NAME}) - PHASE 1 DISCOVERY")
print("="*80)
print(f"Target: Extract ALL product URLs for category {CATEGORY}")
print(f"Pages: 1-{TOTAL_PAGES}")
print(f"Output: {OUTPUT_FILE}")
print("="*80 + "\n")

def connect_to_remote_chrome():
    """Connect to existing Chrome at localhost:9222"""
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        driver = webdriver.Chrome(options=options)
        logger.info("✅ Connected to existing Chrome instance (localhost:9222)")
        return driver
    except Exception as e:
        logger.error(f"❌ Failed to connect to remote Chrome: {e}")
        raise

def extract_product_ids(html):
    """Extract product IDs from pagination page"""
    soup = BeautifulSoup(html, 'html.parser')
    product_ids = []

    try:
        # Find all product links (typically in <a> tags with product IDs in href)
        # Freemold pattern: /Front/Product/?tp=vi&pIdx=XXXXX
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            # Extract product ID from URL pattern
            if 'pIdx=' in href:
                try:
                    product_id = href.split('pIdx=')[1].split('&')[0]
                    if product_id and product_id.isdigit():
                        product_ids.append(product_id)
                except:
                    continue

        logger.debug(f"Found {len(product_ids)} product IDs on page")
        return product_ids

    except Exception as e:
        logger.warning(f"Error extracting product IDs: {e}")
        return []

def load_progress():
    """Load discovery progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'category': CATEGORY,
        'total_pages': TOTAL_PAGES,
        'pages_processed': 0,
        'unique_products': 0,
        'current_page': 1,
        'last_updated': None
    }

def save_progress(progress):
    """Save discovery progress"""
    progress['last_updated'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    """Main discovery process"""

    # Load existing progress
    progress = load_progress()
    start_page = progress.get('current_page', 1)

    # Initialize output file
    if start_page == 1 and OUTPUT_FILE.exists():
        logger.info("Clearing existing output file...")
        OUTPUT_FILE.unlink()

    logger.info(f"Starting from page {start_page}/{TOTAL_PAGES}")

    # Connect to Chrome
    driver = connect_to_remote_chrome()

    # Track unique products
    unique_products = set()

    try:
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as outfile:

            for page_num in range(start_page, TOTAL_PAGES + 1):
                try:
                    # Build pagination URL
                    url = f"{BASE_URL}/Front/Product/?tp=ma&CatA={CATEGORY}&page={page_num}"

                    logger.info(f"[{page_num}/{TOTAL_PAGES}] Crawling page {page_num}...")

                    # Load page
                    driver.get(url)

                    # Wait for page load
                    time.sleep(1.5)

                    # Get page source
                    html = driver.page_source

                    # Extract product IDs
                    product_ids = extract_product_ids(html)

                    # Write unique products
                    for product_id in product_ids:
                        if product_id not in unique_products:
                            unique_products.add(product_id)

                            # Build product record
                            record = {
                                'product_id': product_id,
                                'category': CATEGORY,
                                'category_name': CATEGORY_NAME,
                                'url': f"{BASE_URL}/Front/Product/?tp=vi&pIdx={product_id}",
                                'discovered_at': datetime.now().isoformat(),
                                'page_source': page_num
                            }

                            # Write to output
                            outfile.write(json.dumps(record, ensure_ascii=False) + '\n')
                            outfile.flush()

                    # Update progress
                    progress['pages_processed'] = page_num
                    progress['unique_products'] = len(unique_products)
                    progress['current_page'] = page_num + 1

                    # Log progress every 50 pages
                    if page_num % 50 == 0:
                        logger.info(f"Progress: {page_num}/{TOTAL_PAGES} pages | {len(unique_products)} unique products found")
                        save_progress(progress)

                except Exception as e:
                    logger.error(f"Error on page {page_num}: {e}")
                    # Save progress and continue
                    progress['current_page'] = page_num + 1
                    save_progress(progress)
                    time.sleep(2)  # Brief delay before retry
                    continue

        # Final summary
        logger.info("\n" + "="*80)
        logger.info(f"✅ DISCOVERY COMPLETE FOR CATEGORY {CATEGORY}")
        logger.info("="*80)
        logger.info(f"Total pages crawled: {progress['pages_processed']}/{TOTAL_PAGES}")
        logger.info(f"Unique products discovered: {len(unique_products)}")
        logger.info(f"Output file: {OUTPUT_FILE}")
        logger.info(f"Progress file: {PROGRESS_FILE}")
        logger.info("="*80)

        # Final progress update
        progress['pages_processed'] = TOTAL_PAGES
        progress['unique_products'] = len(unique_products)
        progress['current_page'] = TOTAL_PAGES + 1
        save_progress(progress)

    finally:
        driver.quit()
        logger.info("✨ Browser closed, discovery finished")

if __name__ == '__main__':
    main()
