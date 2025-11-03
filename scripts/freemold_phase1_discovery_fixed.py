#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 1 - CATEGORY & URL DISCOVERY (FIXED)
===========================================================

Discovers all product categories and collects product URLs from freemold.net
- Uses Selenium with proper wait times for JavaScript rendering
- Extracts products from dynamically loaded content via onclick handlers
- Text-first strategy (images collected later)
- No login required (public access)
- Smart checkpointing every 1,000 URLs
- Resume capability for long-running crawls

KEY FIXES:
1. Use /Front/Product/ URL path (not /product/)
2. Use Selenium with 10+ second wait for JS rendering
3. Extract pIdx from onclick="viewProduct('DetailF', 'PIDX')" pattern
4. Proper wait for divFreemoldProdList elements

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
log_file = LOG_DIR / f"freemold_phase1_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
    Looks for category navigation on homepage
    """
    logger.info("=" * 80)
    logger.info("🔍 DISCOVERING CATEGORIES")
    logger.info("=" * 80)

    try:
        driver.get(BASE_URL)
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
        )
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        categories = {}

        # Look for category links on homepage
        # Pattern: /Front/Product/?tp=ma&CatA={CODE}
        all_links = soup.find_all('a')

        for link in all_links:
            href = link.get('href', '')
            if 'CatA=' in href and '/Front/Product/' in href:
                # Extract category code
                match = re.search(r'CatA=([A-Z0-9]+)', href)
                if match:
                    cat_code = match.group(1)
                    cat_name = link.get_text(strip=True)

                    if cat_code not in categories and cat_name:
                        full_url = urljoin(BASE_URL, href)
                        categories[cat_code] = {
                            'name': cat_name,
                            'url': full_url,
                            'code': cat_code
                        }

        logger.info(f"✅ Found {len(categories)} categories")
        for code in sorted(categories.keys()):
            cat = categories[code]
            logger.info(f"  - {code}: {cat['name']}")

        return categories

    except Exception as e:
        logger.error(f"❌ Error discovering categories: {e}")
        import traceback
        traceback.print_exc()
        return {}

# ============================================
# PHASE 1: COLLECT PRODUCT URLs
# ============================================

def collect_urls_for_category(driver, category_code, category_name):
    """
    Collect all product URLs for a specific category
    Handles pagination

    KEY: Extracts pIdx from onclick="viewProduct('DetailF', 'PIDX')" pattern
    """
    product_urls = []

    try:
        page = 1
        consecutive_empty = 0
        max_pages = 500  # Safety limit

        while consecutive_empty < 2 and page <= max_pages:
            url = f"{PRODUCT_LIST_URL}?tp=ma&CatA={category_code}&page={page}"

            logger.info(f"  📄 {category_name} - Page {page}")

            try:
                driver.get(url)

                # Wait for product content to load (critical!)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "div"))
                )
                time.sleep(5)  # Additional wait for JavaScript rendering

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Extract products from divFreemoldProdList divs
                # These contain: onclick="viewProduct('DetailF', '89299');"
                product_divs = soup.find_all('div', id=lambda x: x and x.startswith('divFreemoldProdList') if x else False)

                if not product_divs:
                    consecutive_empty += 1
                    logger.debug(f"    No product divs found on page {page}")
                    page += 1
                    continue

                # Also search for all elements with onclick containing viewProduct
                page_products = 0

                # Pattern 1: divs with onclick="viewProduct(...)"
                elements_with_onclick = soup.find_all(True, {'onclick': lambda x: x and 'viewProduct' in str(x) if x else False})

                seen_pids = set()
                for elem in elements_with_onclick:
                    onclick = elem.get('onclick', '')
                    # Extract pIdx from onclick="viewProduct('DetailF', 'PIDX')"
                    match = re.search(r"viewProduct\(['\"]DetailF['\"]\s*,\s*['\"](\d+)['\"]\)", onclick)
                    if match:
                        p_id = match.group(1)
                        if p_id not in seen_pids:
                            seen_pids.add(p_id)

                            # Construct product detail URL
                            full_url = f"{BASE_URL}/Front/Product/?tp=vi&pIdx={p_id}"

                            product_urls.append({
                                'product_id': p_id,
                                'category': category_code,
                                'category_name': category_name,
                                'url': full_url,
                                'discovered_at': datetime.now().isoformat()
                            })
                            page_products += 1

                if page_products > 0:
                    consecutive_empty = 0
                    logger.info(f"    ✓ Found {page_products} products (Total: {len(product_urls)})")
                else:
                    consecutive_empty += 1

                page += 1
                time.sleep(1)

            except Exception as e:
                logger.warning(f"    ⚠️ Error on page {page}: {e}")
                consecutive_empty += 1
                page += 1
                continue

    except Exception as e:
        logger.error(f"❌ Error collecting URLs for {category_code}: {e}")

    return product_urls

# ============================================
# PHASE 1: MAIN DISCOVERY ORCHESTRATION
# ============================================

def discover_all_urls():
    """
    Discover all product URLs across all categories
    """

    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 1: CATEGORY & URL DISCOVERY (FIXED)")
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
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        # Discover categories
        categories = discover_categories(driver)
        if not categories:
            logger.error("❌ No categories discovered")
            driver.quit()
            return

        # Collect URLs from each category
        logger.info("\n" + "=" * 80)
        logger.info("🔗 COLLECTING PRODUCT URLs")
        logger.info("=" * 80 + "\n")

        for cat_code in sorted(categories.keys()):
            cat = categories[cat_code]
            logger.info(f"\n📂 Category: {cat_code} - {cat['name']}")

            # Collect URLs for this category
            category_urls = collect_urls_for_category(driver, cat_code, cat['name'])

            # Add new URLs (avoid duplicates)
            for url_data in category_urls:
                if url_data['product_id'] not in seen_pids:
                    all_urls.append(url_data)
                    seen_pids.add(url_data['product_id'])

            # Checkpoint every category
            progress['urls_collected'] = len(all_urls)
            progress['last_category'] = cat_code
            save_progress(progress)

            logger.info(f"📊 Checkpoint: {len(all_urls)} URLs collected so far")

        driver.quit()

        # Save final results
        logger.info("\n" + "=" * 80)
        logger.info("💾 SAVING RESULTS")
        logger.info("=" * 80)

        # Save all URLs to JSONL
        with open(URLS_FILE, 'w') as f:
            for url_data in all_urls:
                f.write(json.dumps(url_data, ensure_ascii=False) + '\n')

        logger.info(f"✅ Saved {len(all_urls)} product URLs to {URLS_FILE}")

        # Save categories list
        with open(CATEGORIES_FILE, 'w') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Saved {len(categories)} categories to {CATEGORIES_FILE}")

        # Final statistics
        logger.info("\n" + "=" * 80)
        logger.info("✅ PHASE 1 COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  - Categories discovered: {len(categories)}")
        logger.info(f"  - Product URLs collected: {len(all_urls)}")
        logger.info(f"  - Output file: {URLS_FILE}")
        logger.info("=" * 80)

        if len(all_urls) == 0:
            logger.error("⚠️ ️WARNING: No URLs discovered. Check site structure.")

        return all_urls

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return []

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    start_time = time.time()

    try:
        urls = discover_all_urls()

        elapsed = time.time() - start_time
        logger.info(f"\n⏱️  Total execution time: {elapsed/3600:.2f} hours")

    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
