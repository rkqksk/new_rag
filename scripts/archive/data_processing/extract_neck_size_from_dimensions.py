#!/usr/bin/env python3
"""
dimensions 필드에서 Ø 패턴을 찾아 neck_size로 추출
예: "94x154(mm)/Ø32" → neck_size: "32파이"
"""
import json
import re
from pathlib import Path

base_dir = Path('/Users/oypnus/Project/rag-enterprise/data/crawled_products_final')

updated_count = 0
skipped_count = 0
error_count = 0

for category_dir in base_dir.iterdir():
    if not category_dir.is_dir():
        continue

    for material_dir in category_dir.iterdir():
        if not material_dir.is_dir():
            continue

        products_dir = material_dir / 'products'
        if not products_dir.exists():
            continue

        for json_file in products_dir.glob('idx_*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    product = json.load(f)

                specs = product.get('specifications', {})

                # 이미 neck_size가 있으면 스킵
                if specs.get('neck_size'):
                    skipped_count += 1
                    continue

                # dimensions에서 Ø 패턴 찾기
                dimensions = specs.get('dimensions', '')
                if not dimensions:
                    # dimensions가 없으면 사양 필드에서도 찾기
                    dimensions = specs.get('사양', '')

                if dimensions and 'Ø' in dimensions:
                    # "Ø32" 또는 "Ø24" 같은 패턴 추출
                    match = re.search(r'Ø(\d+)', dimensions)
                    if match:
                        neck_number = match.group(1)
                        specs['neck_size'] = f"{neck_number}파이"

                        # JSON 업데이트
                        product['specifications'] = specs
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(product, f, ensure_ascii=False, indent=2)

                        updated_count += 1

                        if updated_count % 50 == 0:
                            print(f"Progress: {updated_count} products updated")

            except Exception as e:
                error_count += 1
                print(f"❌ Error processing {json_file.name}: {str(e)[:50]}")

print(f"\n{'='*80}")
print(f"✅ Updated: {updated_count} products")
print(f"⏭️  Skipped (already has neck_size): {skipped_count} products")
print(f"❌ Errors: {error_count} products")
print(f"{'='*80}")
