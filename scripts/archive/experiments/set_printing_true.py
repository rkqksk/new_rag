#!/usr/bin/env python3
"""
Simply set printing_option from null to true for Bottle and Jar products
"""

import json
from pathlib import Path

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final")
PRINTABLE_CATEGORIES = ['Bottle', 'Jar']

total = 0
updated = 0

for category in ['Bottle', 'Jar', 'Cap', 'Pump']:
    category_dir = BASE_DIR / category
    if not category_dir.exists():
        continue

    for material_dir in category_dir.iterdir():
        if not material_dir.is_dir() or material_dir.name.startswith('.'):
            continue

        products_dir = material_dir / 'products'
        if not products_dir.exists():
            continue

        for json_file in products_dir.glob('*.json'):
            total += 1

            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            pricing = product.get('pricing', {})

            # Only update Bottle and Jar
            if category in PRINTABLE_CATEGORIES and pricing.get('printing_option') is None:
                pricing['printing_option'] = True
                product['pricing'] = pricing

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(product, f, ensure_ascii=False, indent=2)

                updated += 1

print(f"Total: {total}, Updated: {updated}")
