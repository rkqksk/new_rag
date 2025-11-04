#!/usr/bin/env python3
"""
Phase 2 Benchmark Crawler - 15 Workers (Text-Only)

Validates existing packaging extraction by re-crawling all 22,901 unique products.
Uses cleaned/deduplicated data for maximum efficiency.

Configuration:
    - 15 concurrent workers for optimal performance
    - Text-only extraction (no images)
    - Real-time progress tracking
    - Quality metrics for validation
    - Monitored via localhost:5555 dashboard

Output:
    - benchmark/worker_{worker_id:04d}_output.jsonl (per worker)
    - benchmark/worker_{worker_id:04d}_progress.json (per worker)
    - benchmark/overall_progress.json (aggregated stats)
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import time
import sys
import logging
from collections import defaultdict

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
INPUT_FILE = BASE_PATH / 'cleaned' / 'all_products_clean.jsonl'
OUTPUT_DIR = BASE_PATH / 'benchmark'
PROGRESS_DIR = OUTPUT_DIR / 'progress'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

# Overall progress file
OVERALL_PROGRESS_FILE = OUTPUT_DIR / 'overall_progress.json'

# Configuration
TOTAL_WORKERS = 15
REQUEST_DELAY = 0.05  # 50ms between requests per worker
TIMEOUT = 30  # 30 second timeout

class BenchmarkWorker:
    def __init__(self, worker_id: int, products: List[Dict], start_product: int):
        self.worker_id = worker_id
        self.products = products
        self.start_product = start_product
        self.total_products = len(products)

        # Setup logging
        self.log_file = Path(f'/tmp/benchmark_worker_{worker_id:04d}.log')
        logging.basicConfig(
            level=logging.INFO,
            format=f'Worker-{worker_id:04d} - %(asctime)s: %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(f'worker_{worker_id}')

        # Output files
        self.output_file = OUTPUT_DIR / f'worker_{worker_id:04d}_output.jsonl'
        self.progress_file = PROGRESS_DIR / f'worker_{worker_id:04d}_progress.json'

        # Configure session
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Statistics
        self.stats = {
            'worker_id': worker_id,
            'start_product': start_product,
            'total_products': self.total_products,
            'products_processed': 0,
            'products_success': 0,
            'products_failed': 0,
            'fields_extracted': defaultdict(int),
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }

    def extract_product_details(self, product_info: Dict) -> Dict[str, Any]:
        """Extract comprehensive product text data"""
        try:
            detail_url = product_info.get('product_url')
            product_id = product_info.get('product_id')

            response = self.session.get(detail_url, timeout=TIMEOUT)
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)

            soup = BeautifulSoup(response.text, 'html.parser')

            details = {
                **product_info,
                'detail_crawled': True,
                'detail_crawled_at': datetime.now().isoformat(),
                'specifications': {},
                'company_info': {},
                'image_urls': []
            }

            # 1. Product Name
            pack_tit = soup.find('div', class_='pack_tit')
            if pack_tit:
                product_name = pack_tit.get_text(strip=True)
                product_name = re.sub(r'\d+$', '', product_name).strip()
                details['product_name'] = product_name
                self.stats['fields_extracted']['product_name'] += 1

            # 2. Specifications
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
                        self.stats['fields_extracted'][f'spec_{key}'] += 1

            # 3. Company info
            pack_com_li = soup.find('div', class_='pack_com_li')
            if pack_com_li:
                text = pack_com_li.get_text(strip=True)

                company_match = re.search(r'제조사([^P]+)PHONE', text)
                if company_match:
                    details['company_info']['제조사'] = company_match.group(1).strip()
                    self.stats['fields_extracted']['company_manufacturer'] += 1

                contact_match = re.search(r'담당([^E]+)E MAIL', text)
                if contact_match:
                    details['company_info']['담당'] = contact_match.group(1).strip()
                    self.stats['fields_extracted']['company_contact'] += 1

                phone_match = re.search(r'PHONE([^F]+)FAX', text)
                if phone_match:
                    details['phone'] = phone_match.group(1).strip()
                    self.stats['fields_extracted']['phone'] += 1

                fax_match = re.search(r'FAX([^담]+)담당', text)
                if fax_match:
                    details['fax'] = fax_match.group(1).strip()
                    self.stats['fields_extracted']['fax'] += 1

                email_match = re.search(r'E MAIL([^\s]+)', text)
                if email_match:
                    details['email'] = email_match.group(1).strip()
                    self.stats['fields_extracted']['email'] += 1

            # 4. Image URLs
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and '/productImages/' in src:
                    if src.startswith('/'):
                        src = f"https://www.onehago.com{src}"
                    image_urls.append(src)

            details['image_urls'] = image_urls
            details['image_count'] = len(image_urls)
            if image_urls:
                self.stats['fields_extracted']['images'] += len(image_urls)

            self.stats['products_success'] += 1
            return details

        except Exception as e:
            self.logger.error(f"Failed to extract product {product_info.get('product_id')}: {e}")
            self.stats['products_failed'] += 1
            return {
                **product_info,
                'detail_crawled': False,
                'detail_crawled_at': datetime.now().isoformat(),
                'error': str(e)
            }

    def save_progress(self):
        """Save current progress"""
        self.stats['last_update'] = datetime.now().isoformat()
        self.stats['products_processed'] = self.stats['products_success'] + self.stats['products_failed']

        # Convert defaultdict to regular dict for JSON
        progress = {
            **self.stats,
            'fields_extracted': dict(self.stats['fields_extracted'])
        }

        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def run(self):
        """Main worker execution"""
        self.logger.info(f"Starting benchmark worker {self.worker_id}")
        self.logger.info(f"Processing {self.total_products} products (range: {self.start_product}-{self.start_product + self.total_products})")

        start_time = datetime.now()

        with open(self.output_file, 'w', encoding='utf-8') as f:
            for idx, product in enumerate(self.products):
                # Extract details
                result = self.extract_product_details(product)

                # Save to output
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
                f.flush()

                # Update progress every 50 products
                if (idx + 1) % 50 == 0:
                    self.save_progress()
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = (idx + 1) / elapsed * 60 if elapsed > 0 else 0
                    self.logger.info(
                        f"Progress: {idx + 1}/{self.total_products} "
                        f"({(idx + 1)/self.total_products*100:.1f}%), "
                        f"{rate:.1f} products/min, "
                        f"Success: {self.stats['products_success']}, "
                        f"Failed: {self.stats['products_failed']}"
                    )

        # Final save
        self.save_progress()

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Worker {self.worker_id} completed!")
        self.logger.info(f"  Total: {self.total_products} products")
        self.logger.info(f"  Success: {self.stats['products_success']}")
        self.logger.info(f"  Failed: {self.stats['products_failed']}")
        self.logger.info(f"  Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        self.logger.info(f"  Rate: {self.total_products/elapsed*60:.1f} products/min")


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 phase2_benchmark_crawler_15workers.py <worker_id> <start_index> <end_index>")
        sys.exit(1)

    worker_id = int(sys.argv[1])
    start_index = int(sys.argv[2])
    end_index = int(sys.argv[3])

    # Load all products
    all_products = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            all_products.append(json.loads(line))

    # Get products for this worker
    worker_products = all_products[start_index:end_index]

    # Create and run worker
    worker = BenchmarkWorker(worker_id, worker_products, start_index)
    worker.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Worker interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Worker failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
