#!/usr/bin/env python3
"""
Fix printing_option for Bottle and Jar products
- Bottle/Jar: printing_option should have price data (not null)
- Cap/Pump: printing_option remains null
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final")

# Categories where printing is available
PRINTABLE_CATEGORIES = ['Bottle', 'Jar']

def fix_printing_option(product_data, category):
    """Fix printing_option for a product"""
    pricing = product_data.get('pricing', {})

    # Skip if not a printable category
    if category not in PRINTABLE_CATEGORIES:
        return product_data, False

    # Skip if printing_option already has data
    if pricing.get('printing_option') and pricing['printing_option'] != 'null':
        return product_data, False

    # Calculate printing price
    regular_price = pricing.get('regular_price')
    base_price = pricing.get('base_price', {}).get('regular')

    if not regular_price or not base_price:
        print(f"  ⚠️  Missing price data: regular={regular_price}, base={base_price}")
        return product_data, False

    printing_price = regular_price - base_price

    if printing_price <= 0:
        print(f"  ⚠️  Invalid printing price: {printing_price} (regular={regular_price}, base={base_price})")
        return product_data, False

    # Create printing_option structure
    pricing['printing_option'] = {
        'regular_price': printing_price,
        'discount_price': printing_price,
        'updated_at': datetime.now().isoformat(),
        'note': 'Calculated from regular_price - base_price'
    }

    product_data['pricing'] = pricing

    return product_data, True


def main():
    """Process all products"""
    stats = {
        'total': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
        'by_category': {}
    }

    print("🔧 Fixing printing_option for Bottle and Jar products...\n")

    for category in ['Bottle', 'Jar', 'Cap', 'Pump']:
        category_dir = BASE_DIR / category
        if not category_dir.exists():
            print(f"⚠️  Category directory not found: {category}")
            continue

        category_stats = {'total': 0, 'updated': 0, 'skipped': 0}

        print(f"📁 Processing {category}...")

        for material_dir in category_dir.iterdir():
            if not material_dir.is_dir() or material_dir.name.startswith('.'):
                continue

            products_dir = material_dir / 'products'
            if not products_dir.exists():
                continue

            for json_file in products_dir.glob('*.json'):
                stats['total'] += 1
                category_stats['total'] += 1

                try:
                    # Read product
                    with open(json_file, 'r', encoding='utf-8') as f:
                        product = json.load(f)

                    # Fix printing_option
                    updated_product, was_updated = fix_printing_option(product, category)

                    if was_updated:
                        # Write back
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(updated_product, f, ensure_ascii=False, indent=2)

                        stats['updated'] += 1
                        category_stats['updated'] += 1

                        # Show example
                        if category_stats['updated'] <= 3:
                            idx = product.get('idx', 'unknown')
                            pricing = updated_product['pricing']
                            print(f"  ✅ {idx}: printing_option = {pricing['printing_option']['regular_price']}원")
                    else:
                        stats['skipped'] += 1
                        category_stats['skipped'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    category_stats['errors'] = category_stats.get('errors', 0) + 1
                    print(f"  ❌ Error processing {json_file.name}: {e}")

        stats['by_category'][category] = category_stats
        print(f"  📊 {category}: {category_stats['updated']}/{category_stats['total']} updated\n")

    # Final summary
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print(f"Total products: {stats['total']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print("\nBy category:")
    for cat, cat_stats in stats['by_category'].items():
        print(f"  {cat}: {cat_stats['updated']}/{cat_stats['total']} updated")
    print("="*60)


if __name__ == '__main__':
    main()
