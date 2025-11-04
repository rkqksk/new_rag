#!/usr/bin/env python3
"""
Fix coating_available for PET and PETG materials
These materials SHOULD support coating, but were incorrectly set to False
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle")

stats = {'total': 0, 'fixed': 0}

print("🔧 Fixing coating availability for PET/PETG materials...\n")

for material in ['PET', 'PETG']:
    material_dir = BASE_DIR / material
    if not material_dir.exists():
        continue

    print(f"📁 Processing {material}...")
    products_dir = material_dir / 'products'

    if not products_dir.exists():
        continue

    mat_fixed = 0

    for json_file in products_dir.glob('*.json'):
        stats['total'] += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            pricing = product.get('pricing', {})

            # Fix coating_available for PET/PETG
            if pricing.get('coating_available') == False:
                pricing['coating_available'] = True
                if 'coating_note' in pricing:
                    del pricing['coating_note']
                pricing['structure_updated_at'] = datetime.now().isoformat()

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(product, f, ensure_ascii=False, indent=2)

                stats['fixed'] += 1
                mat_fixed += 1

        except Exception as e:
            print(f"  ❌ Error in {json_file.name}: {e}")

    print(f"  ✅ Fixed {mat_fixed} products\n")

print("=" * 80)
print(f"Total: {stats['total']}, Fixed: {stats['fixed']}")
print("=" * 80)
