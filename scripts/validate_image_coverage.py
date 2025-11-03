#!/usr/bin/env python3
"""
이미지 데이터 Coverage Validation Script

packaging_extracted.jsonl 파일의 모든 제품에 이미지가 포함되어 있는지 검증합니다.
"""

import json
from pathlib import Path
from collections import defaultdict

# Configuration
PACKAGING_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/packaging_extracted.jsonl')
IMAGES_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/images')

def validate_image_coverage():
    """모든 제품의 이미지 포함 여부 검증"""

    print("="*80)
    print("🔍 ONEHAGO PACKAGING IMAGE COVERAGE VALIDATION")
    print("="*80)
    print()

    # Statistics
    total_products = 0
    products_with_images = 0
    products_without_images = 0
    total_image_urls = 0

    # Detailed counts
    image_count_distribution = defaultdict(int)
    missing_image_products = []

    print("📊 Analyzing packaging_extracted.jsonl...")
    print()

    with open(PACKAGING_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                product = json.loads(line.strip())
                total_products += 1

                # Check image_urls field
                image_urls = product.get('image_urls', [])
                image_count = product.get('image_count', 0)

                if image_urls and len(image_urls) > 0:
                    products_with_images += 1
                    total_image_urls += len(image_urls)
                    image_count_distribution[len(image_urls)] += 1
                else:
                    products_without_images += 1
                    missing_image_products.append({
                        'product_id': product.get('product_id', 'unknown'),
                        'product_name': product.get('product_name', 'unknown'),
                        'line_number': line_num
                    })

            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_num}: JSON decode error: {e}")
                continue

    # Print results
    print("✅ VALIDATION RESULTS")
    print("="*80)
    print()

    print(f"📦 Total Products: {total_products:,}")
    print(f"✅ Products with Images: {products_with_images:,} ({products_with_images/total_products*100:.2f}%)")
    print(f"❌ Products without Images: {products_without_images:,} ({products_without_images/total_products*100:.2f}%)")
    print(f"🖼️  Total Image URLs: {total_image_urls:,}")
    print(f"📊 Average Images per Product: {total_image_urls/total_products:.2f}")
    print()

    # Image count distribution
    print("📈 IMAGE COUNT DISTRIBUTION")
    print("-"*80)
    sorted_counts = sorted(image_count_distribution.items())
    for count, num_products in sorted_counts:
        percentage = (num_products / total_products) * 100
        bar = '█' * int(percentage / 2)
        print(f"{count:3d} images: {num_products:8,} products ({percentage:5.2f}%) {bar}")
    print()

    # Missing images details
    if missing_image_products:
        print("❌ PRODUCTS WITHOUT IMAGES (First 20)")
        print("-"*80)
        for i, product in enumerate(missing_image_products[:20], 1):
            print(f"{i:3d}. Product ID: {product['product_id']}")
            print(f"     Name: {product['product_name'][:60]}...")
            print(f"     Line: {product['line_number']}")
            print()

        if len(missing_image_products) > 20:
            print(f"... and {len(missing_image_products) - 20:,} more products without images")
            print()

    # Check downloaded images
    if IMAGES_DIR.exists():
        image_files = list(IMAGES_DIR.glob('*.jpg')) + list(IMAGES_DIR.glob('*.png'))
        print(f"🖼️  Downloaded Image Files: {len(image_files):,}")
        print()

    # Final verdict
    print("="*80)
    if products_without_images == 0:
        print("✅ VALIDATION PASSED: All products have images!")
    elif products_without_images / total_products < 0.01:  # Less than 1%
        print(f"⚠️  VALIDATION WARNING: {products_without_images:,} products missing images ({products_without_images/total_products*100:.2f}%)")
    else:
        print(f"❌ VALIDATION FAILED: {products_without_images:,} products missing images ({products_without_images/total_products*100:.2f}%)")
    print("="*80)
    print()

    return {
        'total_products': total_products,
        'products_with_images': products_with_images,
        'products_without_images': products_without_images,
        'total_image_urls': total_image_urls,
        'missing_image_products': missing_image_products
    }

if __name__ == '__main__':
    try:
        results = validate_image_coverage()
    except FileNotFoundError as e:
        print(f"❌ Error: File not found: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
