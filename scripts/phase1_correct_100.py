#!/usr/bin/env python3
"""
PHASE 1 (CORRECT): Collect 100 Product URLs from Category Listing Pages
Extracts product URLs in format: ?cate_mode=view&pid=X&no=Y
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f'/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase1_correct_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
OUTPUT_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/test_phase1_correct_urls.jsonl')
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

class Phase1Collector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def extract_products_from_page(self, category_id: int, page_num: int = 1):
        """Extract product URLs from a single category page"""
        try:
            # Try both URL formats
            if page_num == 1:
                url = f"https://www.onehago.com/mall/?cate={category_id}"
            else:
                url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all product links with cate_mode=view
            product_links = soup.find_all('a', href=re.compile(r'cate_mode=view.*pid='))

            products = []
            for link in product_links:
                href = link.get('href')

                # Extract pid and no
                pid_match = re.search(r'pid=(\d+)', href)
                no_match = re.search(r'no=(\d+)', href)

                if pid_match and no_match:
                    pid = pid_match.group(1)
                    no = no_match.group(1)

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
            logger.error(f"Error extracting from category {category_id} page {page_num}: {e}")
            return []

def main():
    logger.info("="*70)
    logger.info("🧪 PHASE 1 (CORRECT): Collect 100 Product URLs")
    logger.info("="*70)

    collector = Phase1Collector()
    all_products = []

    # Start with category 2 (has 200+ products per first page test)
    logger.info("\n📂 Collecting from category 2...")

    page = 1
    while len(all_products) < 100:
        logger.info(f"  📄 Page {page}...")

        products = collector.extract_products_from_page(category_id=2, page_num=page)

        if not products:
            logger.info(f"  ⚠️  No products found on page {page}, stopping")
            break

        all_products.extend(products)
        logger.info(f"  ✅ Found {len(products)} products (total: {len(all_products)})")

        if len(all_products) >= 100:
            break

        page += 1

    # Keep only first 100
    all_products = all_products[:100]

    # Save to file
    logger.info(f"\n💾 Saving {len(all_products)} products to {OUTPUT_FILE}")

    with open(OUTPUT_FILE, 'w') as f:
        for product in all_products:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ PHASE 1 COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"📊 Results:")
    logger.info(f"  Total products: {len(all_products)}")
    logger.info(f"  Output file: {OUTPUT_FILE}")
    logger.info(f"  URL format: cate_mode=view&pid=X&no=Y")

    # Show sample
    if all_products:
        logger.info(f"\n📋 Sample URLs (first 3):")
        for p in all_products[:3]:
            logger.info(f"  {p['product_url']}")

    logger.info(f"{'='*70}")

    return len(all_products) == 100

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
