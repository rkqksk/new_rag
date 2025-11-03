#!/usr/bin/env python3
"""
Analyze category 2 products to estimate image download requirements
"""
import json
from pathlib import Path
from collections import Counter

# Configuration
PHASE2_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
TARGET_CATEGORY = 2

def find_phase2_files():
    """Find all Phase 2 output files"""
    files = []
    files.extend(PHASE2_OUTPUT_DIR.glob('worker_*_output.jsonl'))
    files.extend(PHASE2_OUTPUT_DIR.glob('batch_*.jsonl'))
    return sorted(files)

def analyze_category2():
    """Analyze category 2 products and their images"""
    print("🔍 Analyzing Category 2 Products from Phase 2 Output")
    print("=" * 60)
    print(f"Target category: {TARGET_CATEGORY}")
    print()

    # Find all output files
    phase2_files = find_phase2_files()

    if not phase2_files:
        print("❌ No Phase 2 output files found yet!")
        print("   Waiting for Phase 2 extraction to generate output...")
        return

    print(f"📂 Found {len(phase2_files)} Phase 2 output files")
    print()

    # Statistics
    total_products = 0
    category2_products = 0
    total_images = 0
    image_counts = []
    products_without_images = 0
    sample_products = []

    # Process all files
    for file_path in phase2_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        product = json.loads(line)
                        total_products += 1

                        # Check if category 2
                        if product.get('category_id') == TARGET_CATEGORY:
                            category2_products += 1

                            # Count images
                            image_urls = product.get('image_urls', [])
                            image_count = len(image_urls)

                            if image_count > 0:
                                total_images += image_count
                                image_counts.append(image_count)
                            else:
                                products_without_images += 1

                            # Collect samples
                            if len(sample_products) < 5:
                                sample_products.append({
                                    'product_id': product.get('product_id'),
                                    'product_name': product.get('product_name', ''),
                                    'image_count': image_count,
                                    'sample_url': image_urls[0] if image_urls else None
                                })

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"⚠️  Error reading {file_path.name}: {e}")
            continue

    # Print results
    print("📊 Analysis Results")
    print("=" * 60)
    print(f"Total products processed: {total_products:,}")
    print(f"Category 2 products: {category2_products:,} ({category2_products/max(total_products,1)*100:.1f}%)")
    print()

    if category2_products > 0:
        print(f"📸 Image Statistics:")
        print(f"   Total images: {total_images:,}")
        print(f"   Products with images: {category2_products - products_without_images:,}")
        print(f"   Products without images: {products_without_images:,}")
        print()

        if image_counts:
            avg_images = sum(image_counts) / len(image_counts)
            max_images = max(image_counts)
            min_images = min(image_counts)

            print(f"   Average images per product: {avg_images:.1f}")
            print(f"   Max images per product: {max_images}")
            print(f"   Min images per product: {min_images}")
            print()

            # Image count distribution
            count_dist = Counter(image_counts)
            print(f"   Image count distribution:")
            for count, freq in sorted(count_dist.items())[:10]:
                print(f"      {count} images: {freq:,} products")
            print()

        # Estimate download size (assuming ~100KB per image)
        estimated_size_mb = total_images * 0.1  # MB
        estimated_size_gb = estimated_size_mb / 1024

        print(f"💾 Estimated Download Size:")
        print(f"   Total images: {total_images:,}")
        print(f"   Estimated size (100KB/image): {estimated_size_gb:.2f} GB")
        print(f"   Estimated time (1 image/sec): {total_images/3600:.1f} hours")
        print()

        # Show samples
        if sample_products:
            print(f"📋 Sample Category 2 Products:")
            for i, product in enumerate(sample_products, 1):
                print(f"\n   {i}. Product ID: {product['product_id']}")
                print(f"      Name: {product['product_name']}")
                print(f"      Images: {product['image_count']}")
                if product['sample_url']:
                    print(f"      Sample URL: {product['sample_url']}")

    else:
        print("ℹ️  No category 2 products found yet")
        print("   Phase 2 extraction may still be processing...")

    print()
    print("=" * 60)
    print("✅ Analysis complete!")
    print()
    print("💡 Next Steps:")
    print("   1. Wait for Phase 2 extraction to complete")
    print("   2. Run: python3 scripts/download_category2_images.py")
    print(f"   3. Images will be saved to: data/onehago/images/category_2/")

if __name__ == '__main__':
    analyze_category2()
