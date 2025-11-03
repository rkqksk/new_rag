#!/usr/bin/env python3
"""
Packaging Image Download Worker

Downloads images for packaging products (category 2-113) in background.
OPTIMIZED: Only downloads first 3 images per product for 81% storage savings.

Features:
- Parallel-safe: Each worker processes different products
- Resume capability: Skip already downloaded products
- Progress tracking: Individual worker statistics
- Rate limiting: Respectful download delays
- Storage optimized: First 3 images only
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
PRODUCTS_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/packaging_unique_for_images.jsonl')
IMAGE_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/packaging')

# OPTIMIZATION: Only download first 3 images per product (saves 81% storage)
MAX_IMAGES_PER_PRODUCT = 3

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


class PackagingImageWorker:
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
        self.log_file = Path(f'/tmp/packaging_image_worker_{worker_id:04d}.log')
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
            'end_product': end_product,
            'max_images_per_product': MAX_IMAGES_PER_PRODUCT
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
        """Download first 3 images for a product (optimized)"""
        product_id = product['product_id']
        image_urls = product.get('image_urls', [])

        if not image_urls:
            return 0, 0, 0

        # OPTIMIZATION: Only download first 3 images
        image_urls = image_urls[:MAX_IMAGES_PER_PRODUCT]

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
            'total_images_available': len(product.get('image_urls', [])),
            'images_downloaded': len(image_urls),
            'max_images_limit': MAX_IMAGES_PER_PRODUCT,
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

    def load_packaging_products(self) -> List[Dict]:
        """Load packaging products from deduplicated JSONL file"""
        products = []
        product_counter = 0

        self.log(f"📂 Loading packaging products from: {PRODUCTS_FILE}")

        if not PRODUCTS_FILE.exists():
            self.log(f"❌ Products file not found: {PRODUCTS_FILE}")
            return []

        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    product = json.loads(line)

                    # Check if product has images
                    if not product.get('image_urls'):
                        continue

                    # Check worker range
                    if self.start_product <= product_counter:
                        if self.end_product is None or product_counter < self.end_product:
                            products.append(product)

                    product_counter += 1

                    # Stop if reached end
                    if self.end_product and product_counter >= self.end_product:
                        break

                except json.JSONDecodeError:
                    continue

        return products

    def run(self):
        """Run packaging image download worker"""
        self.log("=" * 80)
        self.log(f"📦 PACKAGING IMAGE DOWNLOAD WORKER {self.worker_id:04d} STARTED")
        self.log("=" * 80)
        self.log(f"Product range: {self.start_product} - {self.end_product or 'END'}")
        self.log(f"Image limit: First {MAX_IMAGES_PER_PRODUCT} images per product (81% storage savings)")
        self.log(f"Output directory: {IMAGE_OUTPUT_DIR}")
        self.log(f"Log file: {self.log_file}")
        self.log("")

        # Resume info
        if self.downloaded_products:
            self.log(f"📊 Resuming: {len(self.downloaded_products)} products already downloaded")

        # Load packaging products
        self.log("🔍 Loading packaging products in worker range...")
        products = self.load_packaging_products()

        if not products:
            self.log("❌ No packaging products found in worker range!")
            return

        self.log(f"✅ Found {len(products)} packaging products in worker range")
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
            total_available = len(product.get('image_urls', []))
            to_download = min(total_available, MAX_IMAGES_PER_PRODUCT)

            self.log(f"📦 [{idx}/{len(products)}] Product {product_id}: {product_name}")
            self.log(f"   Downloading: {to_download}/{total_available} images (first {MAX_IMAGES_PER_PRODUCT})")

            # Download images
            success, failed, skipped = self.download_product_images(product)

            # Update statistics
            self.downloaded_products.add(product_id)
            self.stats['products_processed'] += 1
            self.stats['images_downloaded'] += success
            self.stats['images_failed'] += failed
            self.stats['images_skipped'] += skipped

            self.log(f"   ✅ Downloaded: {success}/{to_download} images"
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
Packaging Image Download Worker

Downloads first 3 images for packaging products (category 2-113).
OPTIMIZED for 81% storage savings vs downloading all images.

Usage:
    python3 packaging_image_worker.py <worker_id> [start_product] [end_product]

Arguments:
    worker_id       : Worker identifier (0-13 for 14 workers)
    start_product   : Starting product index (default: 0)
    end_product     : Ending product index (default: None = all)

Examples:
    # Worker 0: Download all packaging products
    python3 packaging_image_worker.py 0

    # Worker 0: Download products 0-1604 (first worker of 14)
    python3 packaging_image_worker.py 0 0 1604

    # Worker 1: Download products 1604-3208 (second worker of 14)
    python3 packaging_image_worker.py 1 1604 3208

    # 14 workers for 22,457 products (~1,604 products each)
    python3 packaging_image_worker.py 0 0 1604 &
    python3 packaging_image_worker.py 1 1604 3208 &
    python3 packaging_image_worker.py 2 3208 4812 &
    ... (and so on for workers 3-13)

Run in background:
    nohup python3 packaging_image_worker.py 0 0 1604 > /dev/null 2>&1 &

Monitor progress:
    tail -f /tmp/packaging_image_worker_0000.log

Output:
    Images: data/onehago/images/packaging/{product_id}/
    Progress: data/onehago/images/packaging/worker_XXXX_progress.json
    Log: /tmp/packaging_image_worker_XXXX.log

Storage Optimization:
    First 3 images only = 67,371 images vs 345,803 = 81% storage savings
    Estimated storage: ~6.4 GB vs ~33 GB
""")
        sys.exit(0)

    # Parse arguments
    worker_id = int(sys.argv[1])
    start_product = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end_product = int(sys.argv[3]) if len(sys.argv) > 3 else None

    # Create and run worker
    worker = PackagingImageWorker(worker_id, start_product, end_product)
    worker.run()


if __name__ == '__main__':
    main()
