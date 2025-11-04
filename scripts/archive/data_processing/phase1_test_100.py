#!/usr/bin/env python3
"""
PHASE 1 TEST: Collect 100 Product URLs
Scan product IDs and validate accessibility
"""

import json
import requests
from pathlib import Path
from datetime import datetime
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f'/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase1_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
OUTPUT_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/test_phase1_urls.jsonl')
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def test_product_url(product_id: int) -> dict:
    """Test if a product URL is accessible"""
    url = f"https://www.onehago.com/mall/?mode=view&prod_cd={product_id}"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200 and len(response.text) > 10000:
            # Check if it's a real product page (has content)
            if 'box-info' in response.text or 'product' in response.text:
                return {
                    'product_id': str(product_id),
                    'product_url': url,
                    'status': 'valid',
                    'discovered_at': datetime.now().isoformat()
                }

        return None

    except Exception as e:
        return None

def main():
    logger.info("="*70)
    logger.info("🧪 PHASE 1 TEST: Collecting 100 Product URLs")
    logger.info("="*70)

    # Strategy: Start from known working IDs and expand
    # We know 36834, 54895, 54896, 59194-59207 work

    test_ranges = [
        (36800, 36900),   # Around known working ID 36834
        (54850, 54950),   # Around known working IDs 54895, 54896
        (59150, 59250),   # Around known working IDs 59194-59207
    ]

    valid_products = []
    tested = 0

    logger.info(f"\n📊 Test Strategy:")
    logger.info(f"  Testing {sum(end-start for start, end in test_ranges)} product IDs")
    logger.info(f"  Target: 100 valid products")
    logger.info(f"  Ranges: {test_ranges}\n")

    for start, end in test_ranges:
        logger.info(f"🔍 Scanning range {start}-{end}...")

        for product_id in range(start, end):
            tested += 1

            result = test_product_url(product_id)

            if result:
                valid_products.append(result)
                logger.info(f"  ✅ Found valid product: {product_id} ({len(valid_products)}/100)")

                # Write to file immediately
                with open(OUTPUT_FILE, 'a') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')

            if tested % 50 == 0:
                logger.info(f"  Progress: {tested} tested, {len(valid_products)} found")

            # Stop if we have 100
            if len(valid_products) >= 100:
                logger.info(f"\n🎉 Target reached: 100 valid products!")
                break

        if len(valid_products) >= 100:
            break

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ PHASE 1 TEST COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"📊 Results:")
    logger.info(f"  Total tested: {tested}")
    logger.info(f"  Valid products: {len(valid_products)}")
    logger.info(f"  Success rate: {len(valid_products)/tested*100:.1f}%")
    logger.info(f"  Output file: {OUTPUT_FILE}")
    logger.info(f"{'='*70}")

    return len(valid_products) >= 100

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
