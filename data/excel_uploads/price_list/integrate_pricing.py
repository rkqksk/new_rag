#!/usr/bin/env python3
"""
용기 제품 가격 통합 스크립트

크롤링된 제품 데이터에 가격 정보를 자동으로 추가합니다.
"""

import json
import re
import os
from pathlib import Path

# [위의 함수들을 여기에 포함]
# - parse_capacity_range()
# - find_best_price_range()
# - extract_capacity_from_product()
# - add_pricing_to_product()

def integrate_pricing_for_directory(base_dir, pricing_lookup):
    """디렉토리의 모든 제품에 가격 통합"""
    updated_count = 0
    failed_count = 0
    
    for material_dir in Path(base_dir).iterdir():
        if not material_dir.is_dir():
            continue
            
        material = material_dir.name
        products_dir = material_dir / 'products'
        
        if not products_dir.exists():
            continue
        
        print(f"Processing {material} products...")
        
        for product_file in products_dir.glob('*.json'):
            try:
                with open(product_file, 'r', encoding='utf-8') as f:
                    product = json.load(f)
                
                # Add pricing
                pricing = add_pricing_to_product(product, material_override=material)
                
                if pricing:
                    product['pricing'] = pricing
                    
                    # Save updated product
                    with open(product_file, 'w', encoding='utf-8') as f:
                        json.dump(product, f, indent=2, ensure_ascii=False)
                    
                    updated_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error processing {product_file}: {e}")
                failed_count += 1
    
    return updated_count, failed_count

if __name__ == "__main__":
    # Load pricing data
    with open('container_complete.json', 'r', encoding='utf-8') as f:
        pricing_data = json.load(f)
    
    # Build lookup
    pricing_lookup = build_pricing_lookup(pricing_data)
    
    # Integrate for Bottle directory
    base_dir = '/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle'
    updated, failed = integrate_pricing_for_directory(base_dir, pricing_lookup)
    
    print(f"\nIntegration complete:")
    print(f"  Updated: {updated} products")
    print(f"  Failed: {failed} products")
