#!/usr/bin/env python3
"""
Update legacy data with specialty material information:
1. Other → Multi-layer Blow (다층브로우)
2. PP Bottle (not Jar) → MB4A/Highpax (하이팍스)
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final")

stats = {
    'total': 0,
    'multi_layer_updated': 0,
    'mb4a_updated': 0,
    'errors': 0
}

print("🔧 Updating specialty material information...\n")

# 1. Update "Other" materials → Multi-layer Blow
print("📦 Processing Bottle/Other → Multi-layer Blow...")
other_dir = BASE_DIR / "Bottle" / "Other" / "products"
if other_dir.exists():
    for json_file in other_dir.glob('idx_*.json'):
        stats['total'] += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            # Add specialty material info
            if 'expert_enrichment' not in product:
                product['expert_enrichment'] = {}

            product['expert_enrichment']['specialty_material'] = {
                'type': 'multi_layer_blow',
                'korean_name': '다층브로우',
                'alternative_names': ['2중용기', 'Multi-layer Blow Molding'],
                'description': 'Dual-nozzle injection container using 2 materials or single material',
                'manufacturing': {
                    'nozzles': 2,
                    'materials_options': ['dual_material', 'single_material']
                },
                'properties': [
                    'excellent_transparency',
                    'no_coating_needed',
                    'dual_color_capable'
                ],
                'purpose': 'Alternative to matte coating with superior transparency',
                'coating_compatibility': False,
                'coating_note': 'Already dual-layer structure, coating not recommended',
                'updated_at': datetime.now().isoformat()
            }

            # Update pricing coating info
            if 'pricing' in product:
                product['pricing']['coating_available'] = False
                product['pricing']['coating_note'] = '다층브로우 용기는 코팅 불필요 (이미 2중 구조)'

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(product, f, ensure_ascii=False, indent=2)

            stats['multi_layer_updated'] += 1

            if stats['multi_layer_updated'] <= 3:
                print(f"  ✅ idx_{product.get('idx')}: {product.get('product_name', '')[:40]}")

        except Exception as e:
            print(f"  ❌ Error: {json_file.name} - {e}")
            stats['errors'] += 1

print(f"  📊 Multi-layer Blow: {stats['multi_layer_updated']} products updated\n")

# 2. Update PP Bottle (not Jar) → MB4A/Highpax
print("📦 Processing Bottle/PP → MB4A/Highpax...")
pp_dir = BASE_DIR / "Bottle" / "PP" / "products"
if pp_dir.exists():
    for json_file in pp_dir.glob('idx_*.json'):
        stats['total'] += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            # Add specialty material info
            if 'expert_enrichment' not in product:
                product['expert_enrichment'] = {}

            product['expert_enrichment']['specialty_material'] = {
                'type': 'mb4a_highpax',
                'korean_name': 'MB4A (하이팍스)',
                'alternative_names': ['Highpax', 'MB4A용기'],
                'description': 'PP-based premium container with matte soft-touch finish',
                'base_material': 'PP',
                'properties': [
                    'matte_finish',
                    'soft_touch_texture',
                    'premium_feel',
                    'lava_coating_like'
                ],
                'purpose': 'Premium container with luxurious tactile sensation',
                'coating_compatibility': False,
                'coating_note': 'Built-in soft-touch finish, coating not required',
                'updated_at': datetime.now().isoformat()
            }

            # Update pricing coating info
            if 'pricing' in product:
                product['pricing']['coating_available'] = False
                product['pricing']['coating_note'] = 'MB4A/하이팍스 용기는 코팅 불필요 (내장 소프트터치 마감)'

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(product, f, ensure_ascii=False, indent=2)

            stats['mb4a_updated'] += 1

            if stats['mb4a_updated'] <= 3:
                print(f"  ✅ idx_{product.get('idx')}: {product.get('product_name', '')[:40]}")

        except Exception as e:
            print(f"  ❌ Error: {json_file.name} - {e}")
            stats['errors'] += 1
else:
    print("  ⚠️  PP directory not found")

print(f"  📊 MB4A/Highpax: {stats['mb4a_updated']} products updated\n")

# Summary
print("=" * 80)
print("📊 Update Summary")
print("=" * 80)
print(f"Total products processed: {stats['total']}")
print(f"Multi-layer Blow updated: {stats['multi_layer_updated']}")
print(f"MB4A/Highpax updated: {stats['mb4a_updated']}")
print(f"Errors: {stats['errors']}")
print("=" * 80)
