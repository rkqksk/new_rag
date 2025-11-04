#!/usr/bin/env python3
"""
Apply printing and label prices based on capacity and material
User-specified pricing structure
"""

import json
from pathlib import Path
from datetime import datetime
import re

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle")

def extract_capacity_ml(capacity_str: str) -> float:
    """Extract numeric capacity value in ml"""
    if not capacity_str:
        return 0
    match = re.search(r'(\d+(?:\.\d+)?)', capacity_str)
    if match:
        return float(match.group(1))
    return 0

def get_printing_price(material: str, capacity_ml: float) -> dict:
    """
    Get printing price based on material and capacity

    PET:
    - 10~400ml: 매출 80원, 매입 70원
    - 500~749ml: 매출 90원, 매입 80원
    - 750~999ml: 매출 120원, 매입 100원
    - 1000ml+: 매출 130원, 매입 110원

    PE/PP/Other:
    - 10~400ml: 매출 80원, 매입 80원
    - 500~749ml: 매출 90원, 매입 80원
    - 750~999ml: 매출 120원, 매입 100원
    - 1000ml+: 매출 130원, 매입 110원
    - 열처리 30원 별도 (note)
    """
    if capacity_ml == 0:
        return None

    # Determine price based on capacity
    if capacity_ml < 500:
        if material == 'PET':
            regular, discount = 80, 70
        else:  # PE, PP, PETG, Other
            regular, discount = 80, 80
    elif capacity_ml < 750:
        if material == 'PET':
            regular, discount = 90, 80
        else:
            regular, discount = 90, 80
    elif capacity_ml < 1000:
        if material == 'PET':
            regular, discount = 120, 100
        else:
            regular, discount = 120, 100
    else:  # 1000ml+
        if material == 'PET':
            regular, discount = 130, 110
        else:
            regular, discount = 130, 110

    result = {
        'regular_price': regular,
        'discount_price': discount
    }

    # Add heat treatment note for PE/PP/Other
    if material in ['PE', 'PP', 'Other']:
        result['heat_treatment'] = {
            'price': 30,
            'note': '열처리 별도'
        }

    return result

def get_label_price(capacity_ml: float) -> dict:
    """
    Get label price based on capacity (same for all materials)

    - 10~400ml: 매출 60원, 매입 60원
    - 500~749ml: 매출 90원, 매입 90원
    - 750~999ml: 매출 120원, 매입 100원
    - 1000ml+: 매출 100원, 매입 90원
    """
    if capacity_ml == 0:
        return None

    if capacity_ml < 500:
        regular, discount = 60, 60
    elif capacity_ml < 750:
        regular, discount = 90, 90
    elif capacity_ml < 1000:
        regular, discount = 120, 100
    else:  # 1000ml+
        regular, discount = 100, 90

    return {
        'regular_price': regular,
        'discount_price': discount
    }

stats = {
    'total': 0,
    'printing_updated': 0,
    'label_updated': 0,
    'by_material': {}
}

print("💰 Applying printing and label prices...\n")

for material_dir in BASE_DIR.iterdir():
    if not material_dir.is_dir() or material_dir.name.startswith('.'):
        continue

    material = material_dir.name
    print(f"📁 Processing {material}...")

    mat_stats = {'total': 0, 'printing': 0, 'label': 0}
    products_dir = material_dir / 'products'

    if not products_dir.exists():
        continue

    for json_file in products_dir.glob('*.json'):
        stats['total'] += 1
        mat_stats['total'] += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            specs = product.get('specifications', {})
            capacity_str = specs.get('capacity', '')
            capacity_ml = extract_capacity_ml(capacity_str)

            if capacity_ml == 0:
                continue

            pricing = product.get('pricing', {})
            changed = False

            # Apply printing price
            printing_price = get_printing_price(material, capacity_ml)
            if printing_price:
                pricing['printing_option'] = printing_price
                changed = True
                stats['printing_updated'] += 1
                mat_stats['printing'] += 1

            # Apply label price
            label_price = get_label_price(capacity_ml)
            if label_price:
                pricing['label_option'] = label_price
                changed = True
                stats['label_updated'] += 1
                mat_stats['label'] += 1

            if changed:
                pricing['pricing_updated_at'] = datetime.now().isoformat()
                product['pricing'] = pricing

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(product, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"  ❌ Error: {json_file.name} - {e}")

    stats['by_material'][material] = mat_stats
    print(f"  ✅ {material}: Printing {mat_stats['printing']}, Label {mat_stats['label']}\n")

print("=" * 80)
print("📊 Summary")
print("=" * 80)
print(f"Total products processed: {stats['total']}")
print(f"Printing prices updated: {stats['printing_updated']}")
print(f"Label prices updated: {stats['label_updated']}")
print("\nBy material:")
for mat, mat_stats in sorted(stats['by_material'].items()):
    print(f"  {mat}: {mat_stats['total']} products")
    print(f"    - Printing: {mat_stats['printing']}")
    print(f"    - Label: {mat_stats['label']}")
print("=" * 80)
