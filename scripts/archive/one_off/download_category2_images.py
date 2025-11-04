#!/usr/bin/env python3
"""
Download images for category 2 products from Phase 2 extraction results
"""
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import hashlib
from typing import List, Dict

# Configuration
PHASE2_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
IMAGE_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2')
PROGRESS_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/download_progress.json')
TARGET_CATEGORY = 2

# Download settings
MAX_RETRIES = 3
TIMEOUT = 30
DELAY_BETWEEN_DOWNLOADS = 0.1  # 100ms delay to be respectful
BATCH_SIZE = 100  # Save progress every 100 products

# Create output directory
IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_progress():
    """Load download progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'downloaded_products': [],
        'downloaded_images': 0,
        'failed_images': 0,
        'total_products': 0,
        'start_time': datetime.now().isoformat(),
        'last_update': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save download progress to file"""
    progress['last_update'] = datetime.now().isoformat()
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

def get_image_filename(url: str, index: int) -> str:
    """Generate consistent filename from URL"""
    # Extract original filename from URL
    parsed = urlparse(url)
    original_name = Path(parsed.path).name

    # Create hash of URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # Use original filename with hash prefix
    ext = Path(original_name).suffix or '.jpg'
    return f"img_{index:02d}_{url_hash}{ext}"

def download_image(url: str, output_path: Path, session: requests.Session) -> bool:
    """Download single image with retries"""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=TIMEOUT, stream=True)
            response.raise_for_status()

            # Save image
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            else:
                print(f"   ❌ Failed after {MAX_RETRIES} attempts: {e}")
                return False

    return False

def download_product_images(product: Dict, session: requests.Session, progress: Dict) -> tuple:
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
        'downloaded_at': datetime.now().isoformat()
    }

    with open(product_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Download images
    success_count = 0
    fail_count = 0

    for idx, url in enumerate(image_urls, 1):
        filename = get_image_filename(url, idx)
        output_path = product_dir / filename

        # Skip if already downloaded
        if output_path.exists():
            success_count += 1
            continue

        print(f"   📥 Downloading image {idx}/{len(image_urls)}: {filename}")

        if download_image(url, output_path, session):
            success_count += 1
            time.sleep(DELAY_BETWEEN_DOWNLOADS)
        else:
            fail_count += 1

    return success_count, fail_count

def find_phase2_files() -> List[Path]:
    """Find all Phase 2 output files (worker outputs and batches)"""
    files = []

    # Worker output files
    files.extend(PHASE2_OUTPUT_DIR.glob('worker_*_output.jsonl'))

    # Batch files
    files.extend(PHASE2_OUTPUT_DIR.glob('batch_*.jsonl'))

    return sorted(files)

def process_phase2_file(file_path: Path, session: requests.Session, progress: Dict):
    """Process a single Phase 2 output file"""
    print(f"\n📂 Processing: {file_path.name}")

    category2_products = []

    # Read file and filter category 2 products
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    product = json.loads(line)

                    # Filter for category 2
                    if product.get('category_id') == TARGET_CATEGORY:
                        category2_products.append(product)

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    if not category2_products:
        print(f"   ℹ️  No category 2 products found")
        return

    print(f"   ✅ Found {len(category2_products)} category 2 products")

    # Process each product
    for idx, product in enumerate(category2_products, 1):
        product_id = product['product_id']

        # Skip if already processed
        if product_id in progress['downloaded_products']:
            continue

        product_name = product.get('product_name', 'Unknown')
        image_count = product.get('image_count', 0)

        print(f"\n📦 Product {idx}/{len(category2_products)}: {product_id}")
        print(f"   Name: {product_name}")
        print(f"   Images: {image_count}")

        # Download images
        success, failed = download_product_images(product, session, progress)

        # Update progress
        progress['downloaded_products'].append(product_id)
        progress['downloaded_images'] += success
        progress['failed_images'] += failed
        progress['total_products'] += 1

        print(f"   ✅ Downloaded: {success}/{image_count} images")
        if failed > 0:
            print(f"   ⚠️  Failed: {failed} images")

        # Save progress periodically
        if progress['total_products'] % BATCH_SIZE == 0:
            save_progress(progress)
            print(f"\n💾 Progress saved: {progress['total_products']} products, {progress['downloaded_images']} images")

def main():
    print("🚀 Onehago Category 2 Image Downloader")
    print("=" * 60)
    print(f"Target category: {TARGET_CATEGORY}")
    print(f"Output directory: {IMAGE_OUTPUT_DIR}")
    print(f"Phase 2 data: {PHASE2_OUTPUT_DIR}")
    print()

    # Load progress
    progress = load_progress()

    if progress['total_products'] > 0:
        print(f"📊 Resuming previous session:")
        print(f"   Products processed: {progress['total_products']}")
        print(f"   Images downloaded: {progress['downloaded_images']}")
        print(f"   Images failed: {progress['failed_images']}")
        print()

    # Setup session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Find all Phase 2 output files
    phase2_files = find_phase2_files()

    if not phase2_files:
        print("❌ No Phase 2 output files found!")
        print("   Waiting for Phase 2 to generate output...")
        return

    print(f"📋 Found {len(phase2_files)} Phase 2 output files")
    print()

    # Process each file
    start_time = time.time()

    try:
        for file_idx, file_path in enumerate(phase2_files, 1):
            print(f"\n{'=' * 60}")
            print(f"File {file_idx}/{len(phase2_files)}")
            process_phase2_file(file_path, session, progress)

    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")

    finally:
        # Final progress save
        save_progress(progress)

        # Print summary
        elapsed_time = time.time() - start_time

        print("\n" + "=" * 60)
        print("📊 Download Summary")
        print("=" * 60)
        print(f"Total products processed: {progress['total_products']}")
        print(f"Total images downloaded: {progress['downloaded_images']}")
        print(f"Total images failed: {progress['failed_images']}")
        print(f"Time elapsed: {elapsed_time:.1f} seconds")

        if progress['downloaded_images'] > 0:
            avg_time = elapsed_time / progress['downloaded_images']
            print(f"Average time per image: {avg_time:.2f} seconds")

        print(f"\n💾 Images saved to: {IMAGE_OUTPUT_DIR}")
        print(f"📋 Progress saved to: {PROGRESS_FILE}")

if __name__ == '__main__':
    main()
