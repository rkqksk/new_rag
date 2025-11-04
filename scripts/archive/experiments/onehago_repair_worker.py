#!/usr/bin/env python3
"""
Onehago Phase 2 Data Repair Worker
Validates extracted data and re-crawls failed/incomplete products
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import time
import sys
from typing import Dict, List, Set

# Configuration
PHASE2_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
REPAIR_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/repaired')
REPAIR_LOG = Path('/tmp/onehago_repair_worker.log')
REPAIR_PROGRESS = REPAIR_OUTPUT_DIR / 'repair_progress.json'

# Validation criteria
REQUIRED_FIELDS = ['product_id', 'product_name', 'specifications', 'company_info', 'image_urls', 'image_count']
MIN_IMAGE_COUNT = 1
MIN_SPEC_FIELDS = 2  # At least 2 specification fields
MIN_COMPANY_FIELDS = 1  # At least 1 company field

# Crawler settings
TIMEOUT = 30
RETRY_ATTEMPTS = 3
DELAY_BETWEEN_REQUESTS = 0.5

class RepairWorker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Statistics
        self.stats = {
            'total_products': 0,
            'validated': 0,
            'failed_validation': 0,
            'repair_attempts': 0,
            'repair_success': 0,
            'repair_failed': 0,
            'start_time': datetime.now().isoformat()
        }

        # Create output directory
        REPAIR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Load progress
        self.repaired_products = self.load_progress()

    def load_progress(self) -> Set[str]:
        """Load previously repaired product IDs"""
        if REPAIR_PROGRESS.exists():
            try:
                with open(REPAIR_PROGRESS, 'r') as f:
                    data = json.load(f)
                    return set(data.get('repaired_products', []))
            except:
                return set()
        return set()

    def save_progress(self):
        """Save repair progress"""
        with open(REPAIR_PROGRESS, 'w') as f:
            json.dump({
                'repaired_products': list(self.repaired_products),
                'stats': self.stats,
                'last_update': datetime.now().isoformat()
            }, f, indent=2)

    def log(self, message: str):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        with open(REPAIR_LOG, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')

    def validate_product(self, product: Dict) -> tuple[bool, List[str]]:
        """
        Validate product data quality
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        product_id = product.get('product_id', 'UNKNOWN')

        # Check required fields exist
        for field in REQUIRED_FIELDS:
            if field not in product:
                issues.append(f"Missing field: {field}")

        # Validate product name
        product_name = product.get('product_name', '')
        if not product_name or len(product_name) < 5:
            issues.append("Invalid or too short product name")

        # Validate specifications
        specs = product.get('specifications', {})
        if not isinstance(specs, dict):
            issues.append("specifications is not a dict")
        elif len(specs) < MIN_SPEC_FIELDS:
            issues.append(f"Only {len(specs)} specification fields (minimum {MIN_SPEC_FIELDS})")

        # Validate company info
        company = product.get('company_info', {})
        if not isinstance(company, dict):
            issues.append("company_info is not a dict")
        elif len(company) < MIN_COMPANY_FIELDS:
            issues.append(f"Only {len(company)} company fields (minimum {MIN_COMPANY_FIELDS})")

        # Validate images
        image_urls = product.get('image_urls', [])
        image_count = product.get('image_count', 0)

        if not isinstance(image_urls, list):
            issues.append("image_urls is not a list")
        elif len(image_urls) < MIN_IMAGE_COUNT:
            issues.append(f"Only {len(image_urls)} images (minimum {MIN_IMAGE_COUNT})")

        if len(image_urls) != image_count:
            issues.append(f"image_count mismatch: {image_count} vs {len(image_urls)}")

        # Validate image URLs
        for url in image_urls:
            if not url.startswith('http'):
                issues.append(f"Invalid image URL: {url}")
                break

        is_valid = len(issues) == 0
        return is_valid, issues

    def extract_product_details(self, product_url: str, product_id: str) -> Dict:
        """
        Re-crawl product page and extract complete data
        Same logic as corrected onehago_worker.py
        """
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = self.session.get(product_url, timeout=TIMEOUT)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract product name
                pack_tit = soup.find('div', class_='pack_tit')
                product_name = pack_tit.get_text(strip=True) if pack_tit else ""

                # Extract specifications and company info
                pack_info = soup.find('div', class_='pack_info')

                specifications = {}
                company_info = {}
                phone = ""
                fax = ""
                email = ""

                if pack_info:
                    dt_elements = pack_info.find_all('dt')
                    for dt in dt_elements:
                        label = dt.get_text(strip=True)
                        dd = dt.find_next_sibling('dd')
                        value = dd.get_text(strip=True) if dd else ""

                        # Map Korean labels to nested structures
                        if '코드' in label:
                            specifications['코드'] = value
                        elif '용량' in label:
                            specifications['용량'] = value
                        elif '사이즈' in label:
                            specifications['사이즈'] = value
                        elif 'MOQ' in label or '수량' in label:
                            specifications['MOQ'] = value
                        elif '재질' in label:
                            specifications['재질'] = value
                        elif '원산지' in label:
                            specifications['원산지'] = value
                        elif '제조사' in label:
                            company_info['제조사'] = value
                        elif '담당' in label:
                            company_info['담당'] = value
                        elif 'PHONE' in label or '전화' in label:
                            phone = value
                        elif 'FAX' in label:
                            fax = value
                        elif 'E MAIL' in label or 'EMAIL' in label or '이메일' in label:
                            email = value

                # Extract all image URLs
                image_urls = []
                img_tags = soup.find_all('img')
                for img in img_tags:
                    src = img.get('src', '')
                    if src and 'productImages' in src:
                        if src.startswith('http'):
                            image_urls.append(src)
                        else:
                            image_urls.append(f"https://www.onehago.com{src}")

                # Remove duplicates while preserving order
                seen = set()
                unique_images = []
                for url in image_urls:
                    if url not in seen:
                        seen.add(url)
                        unique_images.append(url)

                # Build result
                result = {
                    'detail_crawled': True,
                    'detail_crawled_at': datetime.now().isoformat(),
                    'specifications': specifications,
                    'company_info': company_info,
                    'image_urls': unique_images,
                    'product_name': product_name,
                    'phone': phone,
                    'fax': fax,
                    'email': email,
                    'image_count': len(unique_images),
                    'repaired': True,
                    'repaired_at': datetime.now().isoformat()
                }

                return result

            except Exception as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    self.log(f"   Retry {attempt + 1}/{RETRY_ATTEMPTS} for product {product_id}: {e}")
                    time.sleep(2 * (attempt + 1))
                else:
                    self.log(f"   Failed to re-crawl product {product_id} after {RETRY_ATTEMPTS} attempts: {e}")
                    return None

        return None

    def repair_product(self, product: Dict, issues: List[str]) -> Dict:
        """Repair a failed product by re-crawling"""
        product_id = product.get('product_id', 'UNKNOWN')
        product_url = product.get('product_url', '')

        if not product_url:
            self.log(f"   ❌ No URL for product {product_id}")
            return None

        self.log(f"   🔧 Repairing product {product_id}")
        self.log(f"      Issues: {', '.join(issues)}")

        # Re-crawl product
        repaired_data = self.extract_product_details(product_url, product_id)

        if repaired_data:
            # Merge with original data
            repaired_product = {
                **product,
                **repaired_data
            }

            # Validate repaired data
            is_valid, new_issues = self.validate_product(repaired_product)

            if is_valid:
                self.log(f"   ✅ Successfully repaired product {product_id}")
                self.stats['repair_success'] += 1
                return repaired_product
            else:
                self.log(f"   ⚠️  Repair incomplete for product {product_id}: {', '.join(new_issues)}")
                self.stats['repair_failed'] += 1
                return repaired_product  # Return even if not perfect
        else:
            self.log(f"   ❌ Failed to repair product {product_id}")
            self.stats['repair_failed'] += 1
            return None

    def process_file(self, file_path: Path):
        """Process a single Phase 2 output file"""
        self.log(f"\n📂 Processing: {file_path.name}")

        # Output file for repaired products
        output_file = REPAIR_OUTPUT_DIR / f"repaired_{file_path.name}"

        products_in_file = 0
        repaired_in_file = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as infile:
                with open(output_file, 'a', encoding='utf-8') as outfile:
                    for line in infile:
                        if not line.strip():
                            continue

                        try:
                            product = json.loads(line)
                            self.stats['total_products'] += 1
                            products_in_file += 1

                            product_id = product.get('product_id', 'UNKNOWN')

                            # Skip if already repaired
                            if product_id in self.repaired_products:
                                continue

                            # Validate product
                            is_valid, issues = self.validate_product(product)

                            if is_valid:
                                self.stats['validated'] += 1
                                # Write valid product as-is
                                outfile.write(json.dumps(product, ensure_ascii=False) + '\n')
                                self.repaired_products.add(product_id)
                            else:
                                self.stats['failed_validation'] += 1
                                self.stats['repair_attempts'] += 1

                                # Attempt repair
                                repaired_product = self.repair_product(product, issues)

                                if repaired_product:
                                    outfile.write(json.dumps(repaired_product, ensure_ascii=False) + '\n')
                                    self.repaired_products.add(product_id)
                                    repaired_in_file += 1

                                # Rate limiting
                                time.sleep(DELAY_BETWEEN_REQUESTS)

                            # Save progress periodically
                            if self.stats['total_products'] % 100 == 0:
                                self.save_progress()

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.log(f"❌ Error processing {file_path.name}: {e}")

        self.log(f"   Processed: {products_in_file} products, Repaired: {repaired_in_file}")

    def run(self):
        """Run repair worker on all Phase 2 output files"""
        self.log("🔧 ONEHAGO DATA REPAIR WORKER STARTED")
        self.log("=" * 80)
        self.log(f"Output directory: {REPAIR_OUTPUT_DIR}")
        self.log("")

        # Find all Phase 2 output files
        phase2_files = []
        phase2_files.extend(PHASE2_OUTPUT_DIR.glob('worker_*_output.jsonl'))
        phase2_files.extend(PHASE2_OUTPUT_DIR.glob('batch_*.jsonl'))
        phase2_files = sorted(phase2_files)

        if not phase2_files:
            self.log("❌ No Phase 2 output files found!")
            return

        self.log(f"📋 Found {len(phase2_files)} Phase 2 output files")
        self.log("")

        # Process each file
        for idx, file_path in enumerate(phase2_files, 1):
            self.log(f"\n{'=' * 80}")
            self.log(f"File {idx}/{len(phase2_files)}")
            self.process_file(file_path)

            # Save progress after each file
            self.save_progress()

        # Final statistics
        self.log("\n" + "=" * 80)
        self.log("📊 REPAIR WORKER SUMMARY")
        self.log("=" * 80)
        self.log(f"Total products processed: {self.stats['total_products']:,}")
        self.log(f"Already valid: {self.stats['validated']:,} ({self.stats['validated']/max(self.stats['total_products'],1)*100:.1f}%)")
        self.log(f"Failed validation: {self.stats['failed_validation']:,} ({self.stats['failed_validation']/max(self.stats['total_products'],1)*100:.1f}%)")
        self.log(f"Repair attempts: {self.stats['repair_attempts']:,}")
        self.log(f"Repair successful: {self.stats['repair_success']:,}")
        self.log(f"Repair failed: {self.stats['repair_failed']:,}")
        self.log(f"")
        self.log(f"Success rate: {self.stats['repair_success']/max(self.stats['repair_attempts'],1)*100:.1f}%")
        self.log(f"")
        self.log(f"💾 Repaired data saved to: {REPAIR_OUTPUT_DIR}")
        self.log(f"📋 Progress saved to: {REPAIR_PROGRESS}")
        self.log("=" * 80)

        # Save final progress
        self.save_progress()

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("""
Onehago Phase 2 Data Repair Worker

Validates all Phase 2 extracted data and automatically re-crawls
failed or incomplete products to ensure data quality.

Usage:
    python3 onehago_repair_worker.py

The worker will:
1. Scan all Phase 2 output files (worker_*.jsonl, batch_*.jsonl)
2. Validate each product against quality criteria
3. Re-crawl products that fail validation
4. Save repaired data to: data/onehago/crawled/production/repaired/

Validation criteria:
- Required fields present
- Product name valid (>5 chars)
- At least 2 specification fields
- At least 1 company info field
- At least 1 image URL
- Image URLs valid (start with http)
- Image count matches actual images

Output:
- Repaired files: repaired_worker_*.jsonl, repaired_batch_*.jsonl
- Progress file: repair_progress.json (for resume capability)
- Log file: /tmp/onehago_repair_worker.log
""")
            return

    worker = RepairWorker()
    worker.run()

if __name__ == '__main__':
    main()
