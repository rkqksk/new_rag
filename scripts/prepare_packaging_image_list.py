#!/usr/bin/env python3
"""
Prepare Packaging Product List for Image Download

Deduplicates packaging products by product_id and creates a clean list
with image URLs for the image download orchestrator.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
EXTRACTED_FILE = BASE_PATH / 'packaging_extracted.jsonl'
OUTPUT_FILE = BASE_PATH / 'packaging_unique_for_images.jsonl'

print("=" * 80)
print("🖼️  PREPARING PACKAGING PRODUCTS FOR IMAGE DOWNLOAD")
print("=" * 80)
print()

# Track unique products by product_id
unique_products = {}  # product_id -> product_data
duplicate_count = 0
total_count = 0

print(f"📥 Reading from: {EXTRACTED_FILE}")
print()

# Read and deduplicate
with open(EXTRACTED_FILE, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        total_count += 1
        data = json.loads(line)
        product_id = data['product_id']

        if product_id in unique_products:
            duplicate_count += 1
            # Keep the one with more image URLs
            existing = unique_products[product_id]
            existing_img_count = len(existing.get('image_urls', []))
            new_img_count = len(data.get('image_urls', []))

            if new_img_count > existing_img_count:
                unique_products[product_id] = data
        else:
            unique_products[product_id] = data

        if line_num % 50000 == 0:
            print(f"   Processed {line_num:,} lines... ({len(unique_products):,} unique)")

print(f"✅ Deduplication complete:")
print(f"   Total products read: {total_count:,}")
print(f"   Duplicate entries: {duplicate_count:,}")
print(f"   Unique products: {len(unique_products):,}")
print()

# Analyze image availability
products_with_images = 0
products_without_images = 0
total_images = 0

for product in unique_products.values():
    image_urls = product.get('image_urls', [])
    if image_urls:
        products_with_images += 1
        total_images += len(image_urls)
    else:
        products_without_images += 1

print(f"📊 Image Availability:")
print(f"   Products with images: {products_with_images:,} ({products_with_images/len(unique_products)*100:.2f}%)")
print(f"   Products without images: {products_without_images:,} ({products_without_images/len(unique_products)*100:.2f}%)")
print(f"   Total image URLs: {total_images:,}")
print(f"   Average images per product: {total_images/products_with_images:.2f}")
print()

# Save unique products for image download
print(f"💾 Saving unique products to: {OUTPUT_FILE}")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for product in unique_products.values():
        f.write(json.dumps(product, ensure_ascii=False) + '\n')

print(f"✅ Saved {len(unique_products):,} unique packaging products")
print()

# Storage estimation
print("=" * 80)
print("💾 IMAGE DOWNLOAD ESTIMATION")
print("=" * 80)
print()

avg_image_size_kb = 100  # Conservative estimate: 100 KB per image
total_storage_gb = (total_images * avg_image_size_kb) / (1024 * 1024)

print(f"📊 Download Statistics:")
print(f"   Products to process: {products_with_images:,}")
print(f"   Total images to download: {total_images:,}")
print(f"   Estimated storage: {total_storage_gb:.2f} GB")
print()

# Time estimation
download_time_per_image = 0.5  # seconds (with 0.1s delay + download time)
total_time_hours_10_workers = (total_images * download_time_per_image) / (10 * 3600)

print(f"⏱️  Time Estimation (10 workers):")
print(f"   Total time: {total_time_hours_10_workers:.1f} hours ({total_time_hours_10_workers/24:.1f} days)")
print(f"   Time per product: {total_images * download_time_per_image / products_with_images:.1f} seconds")
print()

print("=" * 80)
print("✅ PREPARATION COMPLETE")
print("=" * 80)
print()

print(f"📁 Output file: {OUTPUT_FILE}")
print(f"📊 Unique products: {len(unique_products):,}")
print(f"🖼️  Ready for image download orchestration")
print()

print("💡 Next steps:")
print("   1. Start image download orchestrator with 10 workers")
print("   2. Monitor at localhost:5555")
print("   3. Images will be saved to: data/onehago/images/packaging/")
print()
