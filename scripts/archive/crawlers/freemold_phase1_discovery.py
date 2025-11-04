#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 1 - CATEGORY & URL DISCOVERY
===================================================

Discovers all categories and extracts product URLs from freemold.net
- Text-first strategy (images collected later)
- No login required (public access)
- Smart checkpointing every 1,000 URLs
- Resume capability for long-running crawls

"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.freemold.net"
PRODUCT_LIST_URL = f"{BASE_URL}/Front/Product/"

# Output directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Checkpoint files
PROGRESS_FILE = OUTPUT_DIR / "freemold_phase1_progress.json"
URLS_FILE = OUTPUT_DIR / "product_urls.jsonl"
CATEGORIES_FILE = OUTPUT_DIR / "categories_discovered.json"

# Setup logging
log_file = LOG_DIR / f"freemold_phase1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
        'phase': 'discovery',
        'categories_discovered': 0,
        'urls_collected': 0,
        'last_category': None,
        'start_time': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save progress to checkpoint file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ============================================
# PHASE 1: DISCOVER CATEGORIES
# ============================================

def discover_categories(driver):
    """
    Discover all product categories from the site
    """
    logger.info("=" * 80)
    logger.info("🔍 DISCOVERING CATEGORIES")
    logger.info("=" * 80)

    try:
        driver.get(BASE_URL)
        time.sleep(2)

        # Look for category navigation elements
        # Freemold typically has category menu with links like:
        # /Front/Product/?tp=ma&CatA={code}

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        categories = {}

        # Try multiple selectors for category links
        selectors = [
            'a[href*="tp=ma&CatA="]',
            'a[href*="/Front/Product/"]',
            '.category_link',
            '.menu_item'
        ]

        found_links = set()
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if 'tp=ma&CatA=' in href or 'CatA=' in href:
                    # Extract category code
                    match = re.search(r'CatA=([A-Z0-9]+)', href)
                    if match:
                        cat_code = match.group(1)
                        cat_name = link.get_text(strip=True)
                        full_url = urljoin(BASE_URL, href)
                        categories[cat_code] = {
                            'name': cat_name,
                            'url': full_url,
                            'code': cat_code
                        }
                        found_links.add(cat_code)

        logger.info(f"✅ Found {len(categories)} categories")
        for code, cat in sorted(categories.items()):
            logger.info(f"  - {code}: {cat['name']}")

        return categories

    except Exception as e:
        logger.error(f"❌ Error discovering categories: {e}")
        return {}

# ============================================
# PHASE 1: COLLECT PRODUCT URLs
# ============================================

def collect_urls_for_category(driver, category_code, category_name):
    """
    Collect all product URLs for a specific category
    Handles pagination
    """
    product_urls = []

    try:
        page = 1
        consecutive_empty = 0

        while consecutive_empty < 2:  # Stop if 2 consecutive pages have no products
            url = f"{PRODUCT_LIST_URL}?tp=ma&CatA={category_code}&page={page}"

            logger.info(f"  📄 {category_name} - Page {page}")

            try:
                driver.get(url)
                time.sleep(1)

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Look for product detail links
                # Typically: /Front/Product/?tp=vi&pIdx={product_id}
                product_links = soup.find_all('a', href=lambda x: x and 'tp=vi&pIdx=' in str(x))

                if not product_links:
                    consecutive_empty += 1
                    logger.debug(f"    No products on page {page}")
                    page += 1
                    continue

                consecutive_empty = 0
                page_products = 0

                for link in product_links:
                    href = link.get('href', '')
                    if 'tp=vi&pIdx=' in href:
                        # Extract product ID
                        match = re.search(r'pIdx=(\d+)', href)
                        if match:
                            p_id = match.group(1)
                            full_url = urljoin(BASE_URL, href)

                            product_urls.append({
                                'product_id': p_id,
                                'category': category_code,
                                'category_name': category_name,
                                'url': full_url,
                                'discovered_at': datetime.now().isoformat()
                            })
                            page_products += 1

                if page_products > 0:
                    logger.info(f"    ✓ Found {page_products} products (Total: {len(product_urls)})")

                page += 1
                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"    ⚠️ Error on page {page}: {e}")
                consecutive_empty += 1
                page += 1
                continue

    except Exception as e:
        logger.error(f"❌ Error collecting URLs for {category_code}: {e}")

    return product_urls

def discover_all_urls():
    """
    Discover all product URLs across all categories
    """

    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 1: CATEGORY & URL DISCOVERY")
    logger.info("=" * 80)

    progress = load_progress()
    all_urls = []
    seen_pids = set()

    # Load existing URLs if resuming
    if URLS_FILE.exists():
        with open(URLS_FILE, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    all_urls.append(data)
                    seen_pids.add(data['product_id'])
                except:
                    pass
        logger.info(f"📥 Loaded {len(all_urls)} existing URLs from checkpoint")

    try:
        # Setup Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2  # Disable images for speed
        })

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        # Step 1: Discover categories
        categories = discover_categories(driver)

        if not categories:
            logger.error("❌ No categories found")
            driver.quit()
            return

        # Save discovered categories
        with open(CATEGORIES_FILE, 'w') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

        # Step 2: Collect URLs for each category
        logger.info("\n" + "=" * 80)
        logger.info("🔗 COLLECTING PRODUCT URLs")
        logger.info("=" * 80)

        for cat_code, cat_info in sorted(categories.items()):
            logger.info(f"\n📂 Category: {cat_code} - {cat_info['name']}")

            category_urls = collect_urls_for_category(
                driver,
                cat_code,
                cat_info['name']
            )

            # Add new URLs (deduplication)
            for url_data in category_urls:
                pid = url_data['product_id']
                if pid not in seen_pids:
                    all_urls.append(url_data)
                    seen_pids.add(pid)

            # Checkpoint every category
            with open(URLS_FILE, 'w') as f:
                for url_data in all_urls:
                    f.write(json.dumps(url_data, ensure_ascii=False) + '\n')

            progress['categories_discovered'] = len(categories)
            progress['urls_collected'] = len(all_urls)
            progress['last_category'] = cat_code
            save_progress(progress)

            logger.info(f"📊 Checkpoint: {len(all_urls)} URLs collected so far")

        driver.quit()

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

    # Final save
    with open(URLS_FILE, 'w') as f:
        for url_data in all_urls:
            f.write(json.dumps(url_data, ensure_ascii=False) + '\n')

    progress['phase'] = 'url_collection_complete'
    progress['urls_collected'] = len(all_urls)
    save_progress(progress)

    logger.info("\n" + "=" * 80)
    logger.info("✅ PHASE 1 COMPLETE")
    logger.info("=" * 80)
    logger.info(f"  - Categories discovered: {len(categories)}")
    logger.info(f"  - Product URLs collected: {len(all_urls)}")
    logger.info(f"  - Output file: {URLS_FILE}")
    logger.info("=" * 80)

    return all_urls

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    start_time = time.time()

    try:
        urls = discover_all_urls()

        if not urls:
            logger.error("❌ No URLs discovered")
            return

        elapsed = time.time() - start_time

        logger.info(f"\n⏱️  Execution time: {elapsed/3600:.1f} hours")
        logger.info(f"✅ Ready for Phase 2: Text extraction")

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
