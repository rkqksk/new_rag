#!/usr/bin/env python3
"""
PHASE 1 PRODUCTION: Collect ALL Product URLs from Categories 2-250
Extracts product URLs in format: ?cate_mode=view&pid=X&no=Y
Estimated: 100,000+ products from 248 categories
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import time

# Setup logging
log_file = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs') / f'phase1_production_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
OUTPUT_FILE = OUTPUT_DIR / 'all_product_urls.jsonl'
PROGRESS_FILE = OUTPUT_DIR / 'phase1_progress.json'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
CATEGORY_RANGE = range(2, 251)  # Categories 2-250
MAX_PAGES_PER_CATEGORY = 110  # Safety limit (category 2 has ~103 pages)
WORKERS = 8  # Parallel category crawlers
REQUEST_DELAY = 0.1  # Seconds between requests

class ProductionPhase1:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.total_products = 0
        self.total_pages = 0
        self.start_time = datetime.now()

    def extract_products_from_page(self, category_id: int, page_num: int = 1) -> List[Dict[str, Any]]:
        """Extract product URLs from a single category page"""
        try:
            # Build URL
            if page_num == 1:
                url = f"https://www.onehago.com/mall/?cate={category_id}"
            else:
                url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            time.sleep(REQUEST_DELAY)  # Rate limiting

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all product links with cate_mode=view
            product_links = soup.find_all('a', href=re.compile(r'cate_mode=view.*pid='))

            products = []
            seen_pids = set()

            for link in product_links:
                href = link.get('href')

                # Extract pid and no
                pid_match = re.search(r'pid=(\d+)', href)
                no_match = re.search(r'no=(\d+)', href)

                if pid_match and no_match:
                    pid = pid_match.group(1)
                    no = no_match.group(1)

                    # Skip duplicates on same page
                    if pid in seen_pids:
                        continue
                    seen_pids.add(pid)

                    # Build full URL
                    if href.startswith('/'):
                        full_url = f"https://www.onehago.com{href}"
                    elif not href.startswith('http'):
                        full_url = f"https://www.onehago.com/mall/{href}"
                    else:
                        full_url = href

                    products.append({
                        'product_id': pid,
                        'company_no': no,
                        'product_url': full_url,
                        'category_id': category_id,
                        'page': page_num,
                        'discovered_at': datetime.now().isoformat()
                    })

            return products

        except Exception as e:
            logger.error(f"Error extracting category {category_id} page {page_num}: {e}")
            return []

    def crawl_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Crawl all pages of a single category"""
        logger.info(f"📂 Starting category {category_id}")

        all_products = []
        page = 1
        consecutive_empty = 0

        while page <= MAX_PAGES_PER_CATEGORY:
            products = self.extract_products_from_page(category_id, page)

            if not products:
                consecutive_empty += 1
                if consecutive_empty >= 2:  # Stop after 2 consecutive empty pages
                    break
            else:
                consecutive_empty = 0
                all_products.extend(products)
                self.total_pages += 1

            page += 1

        self.total_products += len(all_products)

        if all_products:
            logger.info(f"✅ Category {category_id}: {len(all_products)} products from {page-1} pages")
        else:
            logger.info(f"⚠️  Category {category_id}: No products found (empty category)")

        return all_products

    def save_progress(self, completed_categories: List[int], all_products: List[Dict]):
        """Save current progress"""
        progress = {
            'completed_categories': completed_categories,
            'total_products': len(all_products),
            'total_pages': self.total_pages,
            'last_update': datetime.now().isoformat(),
            'elapsed_time': str(datetime.now() - self.start_time)
        }

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

        # Save products incrementally
        with open(OUTPUT_FILE, 'w') as f:
            for product in all_products:
                f.write(json.dumps(product, ensure_ascii=False) + '\n')

def main():
    logger.info("="*80)
    logger.info("🚀 PHASE 1 PRODUCTION: Collect ALL Product URLs")
    logger.info("="*80)
    logger.info(f"📊 Configuration:")
    logger.info(f"  Categories: {CATEGORY_RANGE.start}-{CATEGORY_RANGE.stop-1} ({len(CATEGORY_RANGE)} total)")
    logger.info(f"  Max pages per category: {MAX_PAGES_PER_CATEGORY}")
    logger.info(f"  Parallel workers: {WORKERS}")
    logger.info(f"  Output: {OUTPUT_FILE}")
    logger.info("="*80)

    crawler = ProductionPhase1()
    all_products = []
    completed_categories = []

    # Load progress if exists
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            completed_categories = progress.get('completed_categories', [])
            logger.info(f"📥 Resuming from progress: {len(completed_categories)} categories completed")

    # Filter remaining categories
    remaining_categories = [c for c in CATEGORY_RANGE if c not in completed_categories]
    logger.info(f"📋 Remaining categories: {len(remaining_categories)}")

    # Parallel crawl with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        # Submit all category crawl tasks
        future_to_category = {
            executor.submit(crawler.crawl_category, cat_id): cat_id
            for cat_id in remaining_categories
        }

        # Process completed tasks
        for future in as_completed(future_to_category):
            category_id = future_to_category[future]

            try:
                products = future.result()
                all_products.extend(products)
                completed_categories.append(category_id)

                # Save progress every 10 categories
                if len(completed_categories) % 10 == 0:
                    crawler.save_progress(completed_categories, all_products)

                    elapsed = datetime.now() - crawler.start_time
                    rate = len(all_products) / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                    logger.info(f"📊 Progress: {len(completed_categories)}/{len(CATEGORY_RANGE)} categories, "
                              f"{len(all_products):,} products, "
                              f"{rate:.1f} products/min")

            except Exception as e:
                logger.error(f"❌ Failed to process category {category_id}: {e}")

    # Final save
    crawler.save_progress(completed_categories, all_products)

    # Summary
    elapsed = datetime.now() - crawler.start_time
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ PHASE 1 PRODUCTION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Categories processed: {len(completed_categories)}/{len(CATEGORY_RANGE)}")
    logger.info(f"  Total products: {len(all_products):,}")
    logger.info(f"  Total pages crawled: {crawler.total_pages:,}")
    logger.info(f"  Time elapsed: {elapsed}")
    logger.info(f"  Average: {len(all_products)/elapsed.total_seconds()*60:.1f} products/min")
    logger.info(f"  Output file: {OUTPUT_FILE}")
    logger.info(f"  Progress file: {PROGRESS_FILE}")

    # Sample URLs
    if all_products:
        logger.info(f"\n📋 Sample URLs (first 5):")
        for p in all_products[:5]:
            logger.info(f"  Category {p['category_id']}: {p['product_url']}")

    logger.info(f"{'='*80}")

    return len(all_products) > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user. Progress has been saved.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
