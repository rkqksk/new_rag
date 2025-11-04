#!/usr/bin/env python3
"""
Onehago Batch Validation and Repair Script
Processes already-crawled Phase 2 data, validates products, and repairs failures.
No real-time monitoring - batch processing of existing data.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Configuration
PHASE2_OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only")
REPAIRED_OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/repaired")
PROGRESS_FILE = Path("/tmp/onehago_batch_validation_progress.json")
LOG_FILE = Path("/tmp/onehago_batch_validation.log")

# Validation criteria
MIN_SPECIFICATIONS = 2
MIN_COMPANY_INFO = 1
MIN_IMAGES = 1

# Repair settings
REPAIR_TIMEOUT = 30  # 30 seconds (double the original 15s timeout)
MAX_RETRIES = 3

class BatchValidator:
    def __init__(self):
        self.stats = {
            'total_products': 0,
            'validated': 0,
            'passed': 0,
            'failed': 0,
            'repaired': 0,
            'repair_failed': 0,
            'skipped': 0
        }
        self.repaired_output_dir = REPAIRED_OUTPUT_DIR
        self.repaired_output_dir.mkdir(parents=True, exist_ok=True)

        # Load progress if exists
        self.progress = self.load_progress()

    def load_progress(self) -> Dict:
        """Load progress from previous run"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {'processed_files': set(), 'processed_products': set()}

    def save_progress(self):
        """Save progress for resume capability"""
        # Convert sets to lists for JSON serialization
        progress_data = {
            'processed_files': list(self.progress['processed_files']),
            'processed_products': list(self.progress['processed_products']),
            'stats': self.stats,
            'last_update': datetime.now().isoformat()
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress_data, f, indent=2)

    def log(self, message: str):
        """Log message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(LOG_FILE, 'a') as f:
            f.write(log_message + '\n')

    def validate_product(self, product: Dict) -> Tuple[bool, List[str]]:
        """Validate a single product against quality criteria"""
        issues = []

        # Check required fields
        required_fields = ['product_id', 'product_name', 'specifications', 'company_info', 'image_urls']
        for field in required_fields:
            if field not in product or not product[field]:
                issues.append(f"Missing or empty field: {field}")

        if issues:
            return False, issues

        # Check specifications count
        specs = product.get('specifications', {})
        if not isinstance(specs, dict) or len(specs) < MIN_SPECIFICATIONS:
            issues.append(f"Insufficient specifications: {len(specs) if isinstance(specs, dict) else 0} < {MIN_SPECIFICATIONS}")

        # Check company info count
        company = product.get('company_info', {})
        if not isinstance(company, dict) or len(company) < MIN_COMPANY_INFO:
            issues.append(f"Insufficient company info: {len(company) if isinstance(company, dict) else 0} < {MIN_COMPANY_INFO}")

        # Check image URLs
        image_urls = product.get('image_urls', [])
        if not isinstance(image_urls, list) or len(image_urls) < MIN_IMAGES:
            issues.append(f"Insufficient images: {len(image_urls) if isinstance(image_urls, list) else 0} < {MIN_IMAGES}")

        # Check image count consistency
        if isinstance(image_urls, list):
            image_count = product.get('image_count', 0)
            if image_count != len(image_urls):
                issues.append(f"Image count mismatch: {image_count} != {len(image_urls)}")

        # Check detail_crawled flag
        if not product.get('detail_crawled', True):
            issues.append("detail_crawled is false")

        return len(issues) == 0, issues

    def repair_product(self, product: Dict) -> Tuple[bool, Dict]:
        """Attempt to repair a failed product by re-crawling"""
        product_id = product.get('product_id')
        if not product_id:
            return False, product

        product_url = f"https://www.onehago.com/product/view.php?id={product_id}"

        for attempt in range(MAX_RETRIES):
            try:
                self.log(f"   Repair attempt {attempt + 1}/{MAX_RETRIES} for product {product_id}")

                response = requests.get(product_url, timeout=REPAIR_TIMEOUT)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                # Re-extract product details
                repaired = product.copy()

                # Extract specifications
                specs = {}
                spec_table = soup.find('table', class_='spec_table')
                if spec_table:
                    rows = spec_table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            if key and value:
                                specs[key] = value

                if specs:
                    repaired['specifications'] = specs

                # Extract company info
                company = {}
                company_section = soup.find('div', class_='company_info')
                if company_section:
                    company_rows = company_section.find_all('tr')
                    for row in company_rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            if key and value:
                                company[key] = value

                if company:
                    repaired['company_info'] = company

                # Extract image URLs
                image_urls = []
                image_container = soup.find('div', class_='product_images')
                if image_container:
                    images = image_container.find_all('img')
                    for img in images:
                        src = img.get('src')
                        if src and src.startswith('http'):
                            image_urls.append(src)

                if image_urls:
                    repaired['image_urls'] = image_urls
                    repaired['image_count'] = len(image_urls)

                repaired['detail_crawled'] = True
                repaired['repaired_at'] = datetime.now().isoformat()

                # Validate repaired product
                is_valid, _ = self.validate_product(repaired)
                if is_valid:
                    self.log(f"   ✅ Successfully repaired product {product_id}")
                    return True, repaired

            except Exception as e:
                self.log(f"   ⚠️  Repair attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        return False, product

    def process_file(self, file_path: Path):
        """Process a single JSONL file"""
        if str(file_path) in self.progress['processed_files']:
            self.log(f"⏭️  Skipping already processed file: {file_path.name}")
            return

        self.log(f"📄 Processing file: {file_path.name}")

        products_to_repair = []
        valid_products = []

        # Read and validate all products in file
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    product = json.loads(line)
                    product_id = product.get('product_id', f'unknown_{line_num}')

                    self.stats['total_products'] += 1

                    # Skip if already processed
                    if product_id in self.progress['processed_products']:
                        self.stats['skipped'] += 1
                        valid_products.append(product)
                        continue

                    # Validate
                    is_valid, issues = self.validate_product(product)
                    self.stats['validated'] += 1

                    if is_valid:
                        self.stats['passed'] += 1
                        valid_products.append(product)
                    else:
                        self.stats['failed'] += 1
                        self.log(f"   ❌ Product {product_id} failed: {'; '.join(issues)}")
                        products_to_repair.append(product)

                    self.progress['processed_products'].add(product_id)

                except json.JSONDecodeError as e:
                    self.log(f"   ⚠️  JSON decode error on line {line_num}: {e}")

        # Repair failed products
        if products_to_repair:
            self.log(f"🔧 Repairing {len(products_to_repair)} failed products...")

            repaired_batch = []
            for product in products_to_repair:
                success, repaired_product = self.repair_product(product)
                if success:
                    self.stats['repaired'] += 1
                    repaired_batch.append(repaired_product)
                else:
                    self.stats['repair_failed'] += 1

            # Save repaired products
            if repaired_batch:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.repaired_output_dir / f"repaired_{file_path.stem}_{timestamp}.jsonl"

                with open(output_file, 'w', encoding='utf-8') as f:
                    for product in repaired_batch:
                        f.write(json.dumps(product, ensure_ascii=False) + '\n')

                self.log(f"   💾 Saved {len(repaired_batch)} repaired products to {output_file.name}")

        # Mark file as processed
        self.progress['processed_files'].add(str(file_path))
        self.save_progress()

    def run(self):
        """Main batch validation process"""
        self.log("🚀 ONEHAGO BATCH VALIDATION AND REPAIR")
        self.log("=" * 50)
        self.log(f"Source: {PHASE2_OUTPUT_DIR}")
        self.log(f"Output: {self.repaired_output_dir}")
        self.log("")

        # Find all JSONL files
        worker_files = sorted(PHASE2_OUTPUT_DIR.glob("worker_*.jsonl"))
        batch_files = sorted(PHASE2_OUTPUT_DIR.glob("batch_*.jsonl"))
        all_files = worker_files + batch_files

        if not all_files:
            self.log("❌ No JSONL files found in Phase 2 output directory")
            return

        self.log(f"📊 Found {len(all_files)} files to process")
        self.log(f"   Worker files: {len(worker_files)}")
        self.log(f"   Batch files: {len(batch_files)}")
        self.log("")

        # Process each file
        start_time = time.time()

        for idx, file_path in enumerate(all_files, 1):
            self.log(f"[{idx}/{len(all_files)}] Processing {file_path.name}")
            self.process_file(file_path)

            # Progress update every 10 files
            if idx % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / idx
                remaining = (len(all_files) - idx) * avg_time

                self.log("")
                self.log(f"📈 Progress: {idx}/{len(all_files)} files ({idx/len(all_files)*100:.1f}%)")
                self.log(f"⏱️  Elapsed: {elapsed/60:.1f} min | Remaining: ~{remaining/60:.1f} min")
                self.log(f"📊 Stats: Total={self.stats['total_products']}, Passed={self.stats['passed']}, Failed={self.stats['failed']}, Repaired={self.stats['repaired']}")
                self.log("")

        # Final summary
        elapsed = time.time() - start_time

        self.log("")
        self.log("=" * 50)
        self.log("✅ BATCH VALIDATION COMPLETE")
        self.log("=" * 50)
        self.log(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        self.log("")
        self.log("📊 Final Statistics:")
        self.log(f"   Total products: {self.stats['total_products']}")
        self.log(f"   Validated: {self.stats['validated']}")
        self.log(f"   ✅ Passed: {self.stats['passed']} ({self.stats['passed']/max(self.stats['validated'],1)*100:.1f}%)")
        self.log(f"   ❌ Failed: {self.stats['failed']} ({self.stats['failed']/max(self.stats['validated'],1)*100:.1f}%)")
        self.log(f"   🔧 Repaired: {self.stats['repaired']} ({self.stats['repaired']/max(self.stats['failed'],1)*100:.1f}%)")
        self.log(f"   ⚠️  Repair failed: {self.stats['repair_failed']}")
        self.log(f"   ⏭️  Skipped: {self.stats['skipped']}")
        self.log("")
        self.log(f"📁 Repaired products saved to: {self.repaired_output_dir}")
        self.log("=" * 50)

if __name__ == "__main__":
    validator = BatchValidator()
    validator.run()
