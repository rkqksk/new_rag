#!/usr/bin/env python3
"""
Onehago Background Image Download Worker

Downloads images for category 2 (packaging) products in background.
Multiple workers can run in parallel to maximize download throughput.

Features:
- Parallel-safe: Each worker processes different products
- Resume capability: Skip already downloaded products
- Progress tracking: Individual worker statistics
- Rate limiting: Respectful download delays
- Graceful shutdown: Ctrl+C handling
"""
import json
import requests
import time
import signal
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import hashlib
from typing import Dict, List, Set

# Configuration
PHASE2_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
IMAGE_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2')
TARGET_CATEGORY = 2

# Download settings
MAX_RETRIES = 3
TIMEOUT = 30
DELAY_BETWEEN_DOWNLOADS = 0.1  # 100ms delay
DELAY_BETWEEN_PRODUCTS = 0.2  # 200ms delay between products

# Worker control
RUNNING = True


def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global RUNNING
    print("\n🛑 Received shutdown signal, stopping worker...")
    RUNNING = False


class ImageDownloadWorker:
    def __init__(self, worker_id: int, start_product: int = 0, end_product: int = None):
        self.worker_id = worker_id
        self.start_product = start_product
        self.end_product = end_product

        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Progress tracking
        self.log_file = Path(f'/tmp/onehago_image_worker_{worker_id:04d}.log')
        self.progress_file = IMAGE_OUTPUT_DIR / f'worker_{worker_id:04d}_progress.json'
        self.downloaded_products = self.load_progress()

        # Statistics
        self.stats = {
            'worker_id': worker_id,
            'products_processed': 0,
            'images_downloaded': 0,
            'images_failed': 0,
            'images_skipped': 0,
            'start_time': datetime.now().isoformat(),
            'start_product': start_product,
            'end_product': end_product
        }

        # Create output directory
        IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def load_progress(self) -> Set[str]:
        """Load worker progress"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('downloaded_products', []))
            except:
                return set()
        return set()

    def save_progress(self):
        """Save worker progress"""
        with open(self.progress_file, 'w') as f:
            json.dump({
                'downloaded_products': list(self.downloaded_products),
                'stats': self.stats,
                'last_update': datetime.now().isoformat()
            }, f, indent=2)

    def log(self, message: str):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [Worker-{self.worker_id:04d}] {message}"
        print(log_message)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')

    def get_image_filename(self, url: str, index: int) -> str:
        """Generate consistent filename from URL"""
        parsed = urlparse(url)
        original_name = Path(parsed.path).name

        # Create hash of URL for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        # Use original filename with hash prefix
        ext = Path(original_name).suffix or '.jpg'
        return f"img_{index:02d}_{url_hash}{ext}"

    def download_image(self, url: str, output_path: Path) -> bool:
        """Download single image with retries"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=TIMEOUT, stream=True)
                response.raise_for_status()

                # Save image
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return True

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                else:
                    self.log(f"   ❌ Failed after {MAX_RETRIES} attempts: {e}")
                    return False

        return False

    def download_product_images(self, product: Dict) -> tuple:
        """Download all images for a product"""
        product_id = product['product_id']
        image_urls = product.get('image_urls', [])

        if not image_urls:
            return 0, 0

        # Create product directory
        product_dir = IMAGE_OUTPUT_DIR / product_id
        product_dir.mkdir(parents=True, exist_ok=True)

        # Save product metadata
        metadata = {
            'product_id': product_id,
            'product_name': product.get('product_name', ''),
            'product_url': product.get('product_url', ''),
            'category_id': product.get('category_id'),
            'company_no': product.get('company_no'),
            'total_images': len(image_urls),
            'downloaded_at': datetime.now().isoformat(),
            'worker_id': self.worker_id
        }

        with open(product_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Download images
        success_count = 0
        fail_count = 0
        skip_count = 0

        for idx, url in enumerate(image_urls, 1):
            if not RUNNING:
                break

            filename = self.get_image_filename(url, idx)
            output_path = product_dir / filename

            # Skip if already downloaded
            if output_path.exists():
                success_count += 1
                skip_count += 1
                continue

            if self.download_image(url, output_path):
                success_count += 1
                time.sleep(DELAY_BETWEEN_DOWNLOADS)
            else:
                fail_count += 1

        return success_count, fail_count, skip_count

    def find_category2_products(self) -> List[Dict]:
        """Find all category 2 products from Phase 2 output"""
        category2_products = []
        product_counter = 0

        # Find all Phase 2 output files
        phase2_files = []
        phase2_files.extend(PHASE2_OUTPUT_DIR.glob('worker_*_output.jsonl'))
        phase2_files.extend(PHASE2_OUTPUT_DIR.glob('batch_*.jsonl'))
        phase2_files = sorted(phase2_files)

        self.log(f"📂 Scanning {len(phase2_files)} Phase 2 output files for category 2 products")

        for file_path in phase2_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue

                        try:
                            product = json.loads(line)

                            # Check if category 2
                            if product.get('category_id') == TARGET_CATEGORY:
                                # Check worker range
                                if self.start_product <= product_counter:
                                    if self.end_product is None or product_counter < self.end_product:
                                        category2_products.append(product)

                                product_counter += 1

                                # Stop if reached end
                                if self.end_product and product_counter >= self.end_product:
                                    break

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                self.log(f"⚠️ Error reading {file_path.name}: {e}")
                continue

            # Stop if reached end
            if self.end_product and product_counter >= self.end_product:
                break

        return category2_products

    def run(self):
        """Run image download worker"""
        self.log("=" * 80)
        self.log(f"🚀 ONEHAGO IMAGE DOWNLOAD WORKER {self.worker_id:04d} STARTED")
        self.log("=" * 80)
        self.log(f"Category: {TARGET_CATEGORY} (packaging)")
        self.log(f"Product range: {self.start_product} - {self.end_product or 'END'}")
        self.log(f"Output directory: {IMAGE_OUTPUT_DIR}")
        self.log(f"Log file: {self.log_file}")
        self.log("")

        # Resume info
        if self.downloaded_products:
            self.log(f"📊 Resuming: {len(self.downloaded_products)} products already downloaded")

        # Find category 2 products
        self.log("🔍 Finding category 2 products in worker range...")
        products = self.find_category2_products()

        if not products:
            self.log("❌ No category 2 products found in worker range!")
            return

        self.log(f"✅ Found {len(products)} category 2 products in worker range")
        self.log("")

        # Process each product
        start_time = time.time()

        for idx, product in enumerate(products, 1):
            if not RUNNING:
                self.log("⚠️ Worker interrupted by signal")
                break

            product_id = product['product_id']

            # Skip if already downloaded
            if product_id in self.downloaded_products:
                continue

            product_name = product.get('product_name', 'Unknown')
            image_count = product.get('image_count', 0)

            self.log(f"📦 [{idx}/{len(products)}] Product {product_id}: {product_name}")
            self.log(f"   Images: {image_count}")

            # Download images
            success, failed, skipped = self.download_product_images(product)

            # Update statistics
            self.downloaded_products.add(product_id)
            self.stats['products_processed'] += 1
            self.stats['images_downloaded'] += success
            self.stats['images_failed'] += failed
            self.stats['images_skipped'] += skipped

            self.log(f"   ✅ Downloaded: {success}/{image_count} images"
                    f"{f' (skipped {skipped} existing)' if skipped > 0 else ''}")

            if failed > 0:
                self.log(f"   ⚠️ Failed: {failed} images")

            # Save progress periodically
            if self.stats['products_processed'] % 10 == 0:
                self.save_progress()

            # Rate limiting between products
            time.sleep(DELAY_BETWEEN_PRODUCTS)

        # Final statistics
        elapsed_time = time.time() - start_time

        self.log("")
        self.log("=" * 80)
        self.log(f"📊 WORKER {self.worker_id:04d} SUMMARY")
        self.log("=" * 80)
        self.log(f"Products processed: {self.stats['products_processed']}")
        self.log(f"Images downloaded: {self.stats['images_downloaded']}")
        self.log(f"Images failed: {self.stats['images_failed']}")
        self.log(f"Images skipped (existing): {self.stats['images_skipped']}")
        self.log(f"Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")

        if self.stats['images_downloaded'] > 0:
            avg_time = elapsed_time / self.stats['images_downloaded']
            self.log(f"Average time per image: {avg_time:.2f} seconds")

        self.log("")
        self.log(f"💾 Images saved to: {IMAGE_OUTPUT_DIR}")
        self.log(f"📋 Progress saved to: {self.progress_file}")
        self.log("=" * 80)

        # Save final progress
        self.save_progress()


def main():
    global RUNNING

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if len(sys.argv) < 2:
        print("""
Onehago Background Image Download Worker

Downloads images for category 2 (packaging) products in background.
Multiple workers can run in parallel.

Usage:
    python3 onehago_image_worker.py <worker_id> [start_product] [end_product]

Arguments:
    worker_id       : Worker identifier (0-99)
    start_product   : Starting product index (default: 0)
    end_product     : Ending product index (default: None = all)

Examples:
    # Worker 0: Download all category 2 products
    python3 onehago_image_worker.py 0

    # Worker 0: Download products 0-5000
    python3 onehago_image_worker.py 0 0 5000

    # Worker 1: Download products 5000-10000
    python3 onehago_image_worker.py 1 5000 10000

    # Parallel workers (4 workers for 20,464 products)
    python3 onehago_image_worker.py 0 0 5116 &      # Worker 0: 0-5116
    python3 onehago_image_worker.py 1 5116 10232 &  # Worker 1: 5116-10232
    python3 onehago_image_worker.py 2 10232 15348 & # Worker 2: 10232-15348
    python3 onehago_image_worker.py 3 15348 20464 & # Worker 3: 15348-20464

Run in background:
    nohup python3 onehago_image_worker.py 0 0 5116 > /dev/null 2>&1 &

Monitor progress:
    tail -f /tmp/onehago_image_worker_0000.log

Output:
    Images: data/onehago/images/category_2/{product_id}/
    Progress: data/onehago/images/category_2/worker_XXXX_progress.json
    Log: /tmp/onehago_image_worker_XXXX.log
""")
        sys.exit(0)

    # Parse arguments
    worker_id = int(sys.argv[1])
    start_product = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end_product = int(sys.argv[3]) if len(sys.argv) > 3 else None

    # Create and run worker
    worker = ImageDownloadWorker(worker_id, start_product, end_product)
    worker.run()


if __name__ == '__main__':
    main()
