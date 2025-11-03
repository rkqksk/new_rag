#!/usr/bin/env python3
"""
PHASE 2 PRODUCTION: Extract ALL Product Text Data (NO IMAGES)
Extracts: product_name, specifications, company info, contact details
Storage: ~2GB for 2M products (text only)
Images can be downloaded later selectively
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import time

# Setup logging
log_file = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs') / f'phase2_production_text_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago')
INPUT_FILE = BASE_PATH / 'crawled' / 'production' / 'all_product_urls.jsonl'
OUTPUT_DIR = BASE_PATH / 'crawled' / 'production' / 'products_text_only'
PROGRESS_FILE = OUTPUT_DIR / 'phase2_progress.json'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
BATCH_SIZE = 1000  # Products per batch file
WORKERS = 8  # Parallel workers (optimized to prevent server rate limiting)
REQUEST_DELAY = 0.03  # Seconds between requests (reduced for more workers)
CHECKPOINT_INTERVAL = 5000  # Save progress every 5000 products

class Phase2TextExtractor:
    def __init__(self):
        # Configure session with larger connection pool for 25 workers
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=30,
            pool_maxsize=30,
            max_retries=3
        )
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.products_processed = 0
        self.products_success = 0
        self.products_failed = 0
        self.start_time = datetime.now()

    def extract_product_details(self, product_info: Dict) -> Dict[str, Any]:
        """Extract comprehensive product text data (NO IMAGES)"""
        try:
            detail_url = product_info.get('product_url')
            product_id = product_info.get('product_id')

            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()

            time.sleep(REQUEST_DELAY)  # Rate limiting

            soup = BeautifulSoup(response.text, 'html.parser')

            details = {
                **product_info,
                'detail_crawled': True,
                'detail_crawled_at': datetime.now().isoformat(),
                'specifications': {},
                'company_info': {},
                'image_urls': []  # Store URLs only, don't download
            }

            # 1. Product Name
            pack_tit = soup.find('div', class_='pack_tit')
            if pack_tit:
                product_name = pack_tit.get_text(strip=True)
                product_name = re.sub(r'\d+$', '', product_name).strip()
                details['product_name'] = product_name

            # 2. Specifications from pack_txt_li
            pack_txt_li = soup.find('div', class_='pack_txt_li')
            if pack_txt_li:
                text = pack_txt_li.get_text(strip=True)

                spec_patterns = [
                    (r'코드([^용량사이즈MOQ재질원산지]+)', '코드'),
                    (r'용량([^사이즈MOQ재질원산지]+)', '용량'),
                    (r'사이즈([^MOQ재질원산지]+)', '사이즈'),
                    (r'MOQ([^재질원산지]+)', 'MOQ'),
                    (r'재질([^원산지]+)', '재질'),
                    (r'원산지(.+)', '원산지'),
                ]

                for pattern, key in spec_patterns:
                    match = re.search(pattern, text)
                    if match:
                        value = match.group(1).strip()
                        value = re.sub(r'\s+', ' ', value)
                        details['specifications'][key] = value

            # 3. Company info from pack_com_li
            pack_com_li = soup.find('div', class_='pack_com_li')
            if pack_com_li:
                text = pack_com_li.get_text(strip=True)

                # Extract manufacturer
                company_match = re.search(r'제조사([^P]+)PHONE', text)
                if company_match:
                    details['company_info']['제조사'] = company_match.group(1).strip()

                # Extract contact person
                contact_match = re.search(r'담당([^E]+)E MAIL', text)
                if contact_match:
                    details['company_info']['담당'] = contact_match.group(1).strip()

                # Extract phone
                phone_match = re.search(r'PHONE([^F]+)FAX', text)
                if phone_match:
                    details['phone'] = phone_match.group(1).strip()

                # Extract fax
                fax_match = re.search(r'FAX([^담]+)담당', text)
                if fax_match:
                    details['fax'] = fax_match.group(1).strip()

                # Extract email
                email_match = re.search(r'E MAIL([^\s]+)', text)
                if email_match:
                    details['email'] = email_match.group(1).strip()

            # 4. Collect image URLs ONLY (don't download)
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and '/productImages/' in src:
                    if src.startswith('/'):
                        src = f"https://www.onehago.com{src}"
                    image_urls.append(src)

            details['image_urls'] = image_urls
            details['image_count'] = len(image_urls)

            self.products_success += 1
            return details

        except Exception as e:
            logger.error(f"Failed to extract product {product_info.get('product_id')}: {e}")
            self.products_failed += 1
            return {
                **product_info,
                'detail_crawled': False,
                'detail_crawled_at': datetime.now().isoformat(),
                'error': str(e)
            }

    def save_batch(self, products: List[Dict], batch_num: int):
        """Save batch of products to file"""
        batch_file = OUTPUT_DIR / f'batch_{batch_num:05d}.jsonl'
        with open(batch_file, 'w', encoding='utf-8') as f:
            for product in products:
                f.write(json.dumps(product, ensure_ascii=False) + '\n')
        logger.info(f"💾 Saved batch {batch_num} ({len(products)} products) to {batch_file.name}")

    def save_progress(self, processed_count: int):
        """Save current progress"""
        progress = {
            'products_processed': processed_count,
            'products_success': self.products_success,
            'products_failed': self.products_failed,
            'last_update': datetime.now().isoformat(),
            'elapsed_time': str(datetime.now() - self.start_time)
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

def main():
    logger.info("="*80)
    logger.info("🚀 PHASE 2 PRODUCTION: Extract ALL Product Text Data (NO IMAGES)")
    logger.info("="*80)
    logger.info(f"📊 Configuration:")
    logger.info(f"  Input: {INPUT_FILE}")
    logger.info(f"  Output: {OUTPUT_DIR}")
    logger.info(f"  Batch size: {BATCH_SIZE} products")
    logger.info(f"  Workers: {WORKERS}")
    logger.info(f"  Storage: Text only (~1KB per product)")
    logger.info("="*80)

    # Load all product URLs
    logger.info(f"\n📥 Loading product URLs from {INPUT_FILE}")
    all_products = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            all_products.append(json.loads(line))

    total_products = len(all_products)
    logger.info(f"✅ Loaded {total_products:,} product URLs")

    # Check if resume needed
    start_index = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_index = progress.get('products_processed', 0)
            logger.info(f"📥 Resuming from product {start_index:,}")

    extractor = Phase2TextExtractor()
    current_batch = []
    batch_num = start_index // BATCH_SIZE

    # Process products with parallel workers
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {}

        for idx in range(start_index, total_products):
            product = all_products[idx]
            future = executor.submit(extractor.extract_product_details, product)
            futures[future] = idx

            # Process completed futures when queue is full
            while len(futures) >= WORKERS * 2:  # Keep queue filled but process results
                done, pending = concurrent.futures.wait(futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    result = future.result()
                    current_batch.append(result)
                    extractor.products_processed += 1
                    del futures[future]

                    # Save batch when full
                    if len(current_batch) >= BATCH_SIZE:
                        extractor.save_batch(current_batch, batch_num)
                        current_batch = []
                        batch_num += 1

                    # Checkpoint progress
                    if extractor.products_processed % CHECKPOINT_INTERVAL == 0:
                        extractor.save_progress(extractor.products_processed)
                        elapsed = datetime.now() - extractor.start_time
                        rate = extractor.products_processed / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                        logger.info(f"📊 Progress: {extractor.products_processed:,}/{total_products:,} "
                                  f"({extractor.products_processed/total_products*100:.1f}%), "
                                  f"{rate:.0f} products/min, "
                                  f"Success: {extractor.products_success:,}, "
                                  f"Failed: {extractor.products_failed:,}")

        # Wait for remaining futures
        for future in as_completed(futures.keys()):
            result = future.result()
            current_batch.append(result)
            extractor.products_processed += 1

    # Save final batch
    if current_batch:
        extractor.save_batch(current_batch, batch_num)

    # Final save
    extractor.save_progress(extractor.products_processed)

    # Summary
    elapsed = datetime.now() - extractor.start_time
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ PHASE 2 PRODUCTION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Total products: {total_products:,}")
    logger.info(f"  Successfully extracted: {extractor.products_success:,} ({extractor.products_success/total_products*100:.1f}%)")
    logger.info(f"  Failed: {extractor.products_failed:,} ({extractor.products_failed/total_products*100:.1f}%)")
    logger.info(f"  Time elapsed: {elapsed}")
    logger.info(f"  Average: {total_products/elapsed.total_seconds()*60:.0f} products/min")
    logger.info(f"  Output directory: {OUTPUT_DIR}")
    logger.info(f"  Batch files: {batch_num + 1}")
    logger.info(f"  Storage: Text only (images saved as URLs)")
    logger.info(f"{'='*80}")

    return extractor.products_success > 0

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
