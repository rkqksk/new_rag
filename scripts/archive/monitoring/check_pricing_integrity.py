#!/usr/bin/env python3
"""
Check pricing data integrity across all Bottle products
Report missing pricing information
"""

import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle")

stats = {
    'total': 0,
    'missing_printing': [],
    'missing_label': [],
    'missing_coating': [],
    'complete': 0
}

by_material = defaultdict(lambda: {'total': 0, 'complete': 0, 'missing': []})

print("🔍 Checking pricing integrity for all Bottle products...\n")

for material_dir in BASE_DIR.iterdir():
    if not material_dir.is_dir() or material_dir.name.startswith('.'):
        continue

    material = material_dir.name
    products_dir = material_dir / 'products'

    if not products_dir.exists():
        continue

    for json_file in products_dir.glob('*.json'):
        stats['total'] += 1
        by_material[material]['total'] += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            idx = product.get('idx', json_file.stem)
            product_name = product.get('product_name', 'Unknown')
            specs = product.get('specifications', {})
            capacity = specs.get('capacity', 'N/A')
            pricing = product.get('pricing', {})

            missing = []

            # Check printing_option (should have price data)
            printing = pricing.get('printing_option')
            if printing is True:
                # printing_option=True but no price
                missing.append('printing_price')
                stats['missing_printing'].append(f"{idx}: {product_name} ({capacity})")
                by_material[material]['missing'].append(f"{idx}: no printing price")
            elif isinstance(printing, dict):
                if not printing.get('regular_price'):
                    missing.append('printing_price')
                    stats['missing_printing'].append(f"{idx}: {product_name} ({capacity})")

            # Check label_option
            label = pricing.get('label_option')
            if label is None:
                # No label data at all
                missing.append('label')
                stats['missing_label'].append(f"{idx}: {product_name} ({capacity})")
                by_material[material]['missing'].append(f"{idx}: no label data")
            elif isinstance(label, dict):
                if not label.get('regular_price'):
                    missing.append('label_price')
                    stats['missing_label'].append(f"{idx}: {product_name} ({capacity})")

            # Check coating (if coating_available=True, should have price)
            coating_available = pricing.get('coating_available')
            coating_price = pricing.get('coating_price')

            if coating_available is True and coating_price is None:
                missing.append('coating_price')
                stats['missing_coating'].append(f"{idx}: {product_name} ({capacity})")
                by_material[material]['missing'].append(f"{idx}: no coating price")

            if not missing:
                stats['complete'] += 1
                by_material[material]['complete'] += 1

        except Exception as e:
            print(f"  ❌ Error: {json_file.name} - {e}")

print("=" * 80)
print("📊 Pricing Integrity Report")
print("=" * 80)
print(f"Total products: {stats['total']}")
print(f"Complete pricing: {stats['complete']}")
print(f"Missing printing data: {len(stats['missing_printing'])}")
print(f"Missing label data: {len(stats['missing_label'])}")
print(f"Missing coating data: {len(stats['missing_coating'])}")
print()

print("By Material:")
for mat, mat_stats in sorted(by_material.items()):
    print(f"  {mat}: {mat_stats['complete']}/{mat_stats['total']} complete")
    if mat_stats['missing']:
        print(f"    Missing data in {len(mat_stats['missing'])} products")

print()
print("Sample products with missing data:")
if stats['missing_printing']:
    print(f"\n  Missing printing price ({len(stats['missing_printing'])} total):")
    for item in stats['missing_printing'][:5]:
        print(f"    - {item}")

if stats['missing_label']:
    print(f"\n  Missing label data ({len(stats['missing_label'])} total):")
    for item in stats['missing_label'][:5]:
        print(f"    - {item}")

if stats['missing_coating']:
    print(f"\n  Missing coating price ({len(stats['missing_coating'])} total):")
    for item in stats['missing_coating'][:5]:
        print(f"    - {item}")

print("=" * 80)
