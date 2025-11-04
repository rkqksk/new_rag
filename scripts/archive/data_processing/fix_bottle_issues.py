#!/usr/bin/env python3
"""
Fix three issues in Bottle products:
1. Dimensions format: Move neck_size from "사양" to separate field
2. MOQ standardization: 10-50ml → 20,000개, 50ml+ → 10,000개
3. Pricing structure: Ensure all pricing fields are present
"""

import json
from pathlib import Path
import re
from datetime import datetime

BASE_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle")

stats = {
    'total': 0,
    'dimensions_fixed': 0,
    'moq_fixed': 0,
    'pricing_fixed': 0,
    'errors': []
}

def extract_capacity_value(capacity_str: str) -> float:
    """Extract numeric capacity value from string like '80ml' or '80g'"""
    if not capacity_str:
        return 0
    match = re.search(r'(\d+(?:\.\d+)?)', capacity_str)
    if match:
        return float(match.group(1))
    return 0

def fix_dimensions(specs: dict) -> bool:
    """
    Fix dimensions format: separate neck_size from dimensions
    Before: "37x37x139(mm)/Ø20"
    After: "37x37x139(mm)" in dimensions, "Ø20" in neck_size
    """
    changed = False

    # Check "사양" field
    if '사양' in specs:
        spec_value = specs['사양']

        # Pattern: dimensions/neck_size or dimensions / neck_size
        if '/' in spec_value:
            parts = spec_value.split('/')
            if len(parts) == 2:
                dimensions_part = parts[0].strip()
                neck_part = parts[1].strip()

                # Update 사양 to only have dimensions
                specs['사양'] = dimensions_part
                changed = True

                # Update dimensions field
                if 'dimensions' not in specs or specs['dimensions'] == neck_part:
                    specs['dimensions'] = dimensions_part
                    changed = True

    return changed

def fix_moq(specs: dict, capacity: str) -> bool:
    """
    Standardize MOQ based on capacity:
    - 10-50ml: 20,000개
    - 50ml+: 10,000개
    """
    capacity_val = extract_capacity_value(capacity)

    if capacity_val == 0:
        return False

    # Determine correct MOQ
    if capacity_val < 50:
        correct_moq = "20,000개"
    else:
        correct_moq = "10,000개"

    # Update if different or missing
    current_moq = specs.get('moq', '')
    if current_moq != correct_moq:
        specs['moq'] = correct_moq
        return True

    return False

def fix_pricing(product: dict) -> bool:
    """
    Ensure pricing structure is complete:
    - base_price with regular/discount
    - printing_option (boolean or object)
    - label_option (object with prices or None)
    - coating_price (object with prices or None) - check material compatibility
    """
    changed = False

    if 'pricing' not in product:
        product['pricing'] = {}
        changed = True

    pricing = product['pricing']

    # 1. Ensure base_price structure
    if 'base_price' not in pricing:
        # Try to extract from old fields
        regular = pricing.get('regular_price') or pricing.get('container_price')
        discount = pricing.get('discount_price')

        if regular:
            pricing['base_price'] = {
                'regular': regular,
                'discount': discount
            }
            changed = True

    # 2. Ensure printing_option exists (should be True for Bottle)
    if 'printing_option' not in pricing or pricing['printing_option'] is None:
        pricing['printing_option'] = True
        changed = True

    # 3. Ensure label_option structure
    if 'label_option' not in pricing:
        pricing['label_option'] = None
        changed = True

    # 4. Check coating compatibility and set coating_available
    material = product.get('specifications', {}).get('재질(원료)', '')
    no_coating_materials = ['PE', 'Other', 'PP', 'MB4C', '다층', '혼합']

    if material in no_coating_materials:
        if pricing.get('coating_available') != False:
            pricing['coating_available'] = False
            pricing['coating_price'] = None
            pricing['coating_note'] = f"{material} material does not support coating"
            changed = True
    else:
        # Materials that support coating (PET, PETG, etc.)
        if 'coating_available' not in pricing:
            pricing['coating_available'] = pricing.get('coating_price') is not None
            changed = True

    if changed:
        pricing['structure_updated_at'] = datetime.now().isoformat()

    return changed

print("🔧 Fixing Bottle product issues...\n")

# Process all Bottle products
for material_dir in BASE_DIR.iterdir():
    if not material_dir.is_dir() or material_dir.name.startswith('.'):
        continue

    material = material_dir.name
    print(f"📁 Processing {material}...")

    products_dir = material_dir / 'products'
    if not products_dir.exists():
        continue

    mat_stats = {'total': 0, 'dimensions': 0, 'moq': 0, 'pricing': 0}

    for json_file in products_dir.glob('*.json'):
        stats['total'] += 1
        mat_stats['total'] += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            specs = product.get('specifications', {})
            capacity = specs.get('capacity', '')

            changed = False

            # Fix 1: Dimensions format
            if fix_dimensions(specs):
                stats['dimensions_fixed'] += 1
                mat_stats['dimensions'] += 1
                changed = True

            # Fix 2: MOQ standardization
            if fix_moq(specs, capacity):
                stats['moq_fixed'] += 1
                mat_stats['moq'] += 1
                changed = True

            # Fix 3: Pricing structure
            if fix_pricing(product):
                stats['pricing_fixed'] += 1
                mat_stats['pricing'] += 1
                changed = True

            # Save if changed
            if changed:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(product, f, ensure_ascii=False, indent=2)

        except Exception as e:
            error_msg = f"Error in {json_file.name}: {e}"
            print(f"  ❌ {error_msg}")
            stats['errors'].append(error_msg)

    print(f"  ✅ {material}: {mat_stats['dimensions']} dimensions, {mat_stats['moq']} MOQ, {mat_stats['pricing']} pricing fixed\n")

# Summary
print("=" * 80)
print("📊 Summary")
print("=" * 80)
print(f"Total products processed: {stats['total']}")
print(f"Dimensions format fixed: {stats['dimensions_fixed']}")
print(f"MOQ standardized: {stats['moq_fixed']}")
print(f"Pricing structure fixed: {stats['pricing_fixed']}")
print(f"Errors: {len(stats['errors'])}")
if stats['errors']:
    print("\nErrors:")
    for err in stats['errors'][:10]:
        print(f"  - {err}")
print("=" * 80)
