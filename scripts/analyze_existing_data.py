#!/usr/bin/env python3
"""
Analyze existing crawled data and identify what we have vs what we need
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    print("="*70)
    print("📊 Existing Data Analysis")
    print("="*70)

    # Load valid categories
    valid_file = Path('data/onehago/valid_categories.json')
    with open(valid_file) as f:
        valid_cats = json.load(f)

    expected = {cat['id']: cat for cat in valid_cats}

    # Collect actual data
    crawled_dir = Path('data/onehago/crawled')
    collected_products = {}

    # Check parent directory files
    for f in sorted(crawled_dir.glob('category_*.json')):
        cat_id = f.stem.split('_')[1]
        with open(f) as file:
            data = json.load(file)
            if cat_id not in collected_products:
                collected_products[cat_id] = []
            collected_products[cat_id].extend(data)

    # Check categories subdirectory
    cat_subdir = crawled_dir / 'categories'
    if cat_subdir.exists():
        for f in sorted(cat_subdir.glob('category_*.json')):
            cat_id = f.stem.split('_')[1]
            with open(f) as file:
                data = json.load(file)
                if cat_id not in collected_products:
                    collected_products[cat_id] = []
                else:
                    # Merge, avoiding duplicates
                    existing_ids = {p['product_id'] for p in collected_products[cat_id]}
                    new_products = [p for p in data if p['product_id'] not in existing_ids]
                    collected_products[cat_id].extend(new_products)

    # Analysis
    print(f"\n📋 Summary:")
    print(f"   Expected categories: {len(expected)}")
    print(f"   Collected categories: {len(collected_products)}")

    total_products = sum(len(products) for products in collected_products.values())
    print(f"   Total products collected: {total_products:,}")

    # Check image status
    print(f"\n🖼️  Image Status:")
    with_images = 0
    total_images = 0

    for cat_id, products in collected_products.items():
        for product in products:
            if product.get('image_path'):
                total_images += 1
            if product.get('full_image_url') or product.get('thumbnail_url'):
                with_images += 1

    print(f"   Products with image URLs: {with_images:,}")
    print(f"   Products with downloaded images: {total_images:,}")

    # Detail crawl status
    print(f"\n📝 Detail Status:")
    with_details = sum(1 for cat_id, products in collected_products.items()
                      for p in products if p.get('detail_crawled'))
    print(f"   Products with details crawled: {with_details:,}")

    # Missing categories
    collected_ids = set(collected_products.keys())
    expected_ids = set(expected.keys())
    missing_ids = expected_ids - collected_ids

    print(f"\n❌ Missing Categories: {len(missing_ids)}")
    if missing_ids and len(missing_ids) < 30:
        missing_with_info = [(cat_id, expected[cat_id]) for cat_id in sorted(missing_ids, key=int)]
        for cat_id, info in missing_with_info[:10]:
            print(f"   {cat_id:3s}: {info.get('products', 0):4d} products expected")
        if len(missing_with_info) > 10:
            print(f"   ... and {len(missing_with_info) - 10} more")

    # Category details
    print(f"\n✅ Collected Categories (with counts):")
    print(f"{'='*70}")
    print(f"{'Cat ID':>6s}  {'Expected':>8s}  {'Collected':>9s}  {'Status':>8s}  {'Details':>7s}")
    print(f"{'-'*70}")

    for cat_id in sorted(collected_ids, key=int):
        products = collected_products[cat_id]
        expected_count = expected.get(cat_id, {}).get('products', 0)
        actual_count = len(products)

        # Calculate percentages
        if expected_count > 0:
            pct = (actual_count / expected_count) * 100
            status = "✅" if pct >= 95 else "⚠️" if pct >= 50 else "❌"
        else:
            pct = 0
            status = "❓"

        # Check details
        with_detail = sum(1 for p in products if p.get('detail_crawled'))
        detail_pct = (with_detail / actual_count * 100) if actual_count > 0 else 0

        print(f"{cat_id:>6s}  {expected_count:>8d}  {actual_count:>9d}  {status} {pct:>5.1f}%  {detail_pct:>6.1f}%")

    print(f"{'='*70}")

    # Recommendations
    print(f"\n💡 Recommendations:")

    if total_images < with_images * 0.9:
        print(f"   1. Download missing images ({with_images - total_images:,} remaining)")

    if with_details < total_products:
        print(f"   2. Extract missing details ({total_products - with_details:,} products)")

    if missing_ids:
        missing_expected_products = sum(expected.get(cat_id, {}).get('products', 0)
                                       for cat_id in missing_ids)
        print(f"   3. Crawl missing categories ({len(missing_ids)} cats, ~{missing_expected_products:,} products)")

    print(f"\n🎯 Current Status: {(len(collected_ids) / len(expected_ids) * 100):.1f}% categories collected")
    print(f"                   {total_products:,} products ready to use")

if __name__ == "__main__":
    main()
