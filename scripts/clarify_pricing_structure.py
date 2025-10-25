#!/usr/bin/env python3
"""
Clarify pricing structure in all product JSON files:
1. Ensure printing_option, label_option, coating_price are clearly defined
2. Set coating_available=false for materials that don't support coating
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final")

# Materials that DON'T support coating
NO_COATING_MATERIALS = ['PE', 'Other', 'PP', 'MB4C', '다층']

stats = {
    'total': 0,
    'updated': 0,
    'coating_disabled': 0,
    'by_category': {}
}

print("🔧 Clarifying pricing structure in all products...\n")

for category_dir in BASE_DIR.iterdir():
    if not category_dir.is_dir() or category_dir.name.startswith('.'):
        continue

    category = category_dir.name
    print(f"📁 Processing {category}...")

    cat_stats = {'total': 0, 'updated': 0, 'coating_disabled': 0}

    for material_dir in category_dir.iterdir():
        if not material_dir.is_dir() or material_dir.name.startswith('.'):
            continue

        material = material_dir.name
        products_dir = material_dir / 'products'

        if not products_dir.exists():
            continue

        for json_file in products_dir.glob('*.json'):
            stats['total'] += 1
            cat_stats['total'] += 1

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    product = json.load(f)

                pricing = product.get('pricing', {})
                updated = False

                # 1. Ensure printing_option is defined (Bottle/Jar only)
                if category in ['Bottle', 'Jar']:
                    if pricing.get('printing_option') is None:
                        pricing['printing_option'] = True
                        updated = True

                # 2. Ensure label_option structure
                if 'label_option' not in pricing:
                    pricing['label_option'] = None

                # 3. Handle coating based on material
                if material in NO_COATING_MATERIALS or (category == 'Jar' and material == 'PE'):
                    # Materials that don't support coating
                    if pricing.get('coating_available') != False:
                        pricing['coating_available'] = False
                        pricing['coating_price'] = None
                        pricing['coating_note'] = f"{material} material does not support coating"
                        updated = True
                        stats['coating_disabled'] += 1
                        cat_stats['coating_disabled'] += 1
                else:
                    # Materials that support coating
                    if 'coating_available' not in pricing:
                        pricing['coating_available'] = pricing.get('coating_price') is not None

                if updated:
                    pricing['structure_updated_at'] = datetime.now().isoformat()
                    product['pricing'] = pricing

                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(product, f, ensure_ascii=False, indent=2)

                    stats['updated'] += 1
                    cat_stats['updated'] += 1

            except Exception as e:
                print(f"  ❌ Error processing {json_file.name}: {e}")

    stats['by_category'][category] = cat_stats
    print(f"  ✅ {category}: {cat_stats['updated']}/{cat_stats['total']} updated, {cat_stats['coating_disabled']} coating disabled\n")

print("\n" + "="*80)
print("📊 Summary")
print("="*80)
print(f"Total products: {stats['total']}")
print(f"Updated: {stats['updated']}")
print(f"Coating disabled: {stats['coating_disabled']}")
print("\nBy category:")
for cat, cat_stats in stats['by_category'].items():
    print(f"  {cat}: {cat_stats['updated']}/{cat_stats['total']} updated, {cat_stats['coating_disabled']} coating disabled")
print("="*80)
