#!/usr/bin/env python3
"""
Consolidate Cap/Pump/Cappump folders into Cap and Pump
Removes duplicates and organizes products properly
"""
import json
import shutil
from pathlib import Path
from collections import defaultdict

def main():
    crawled_dir = Path('/Users/oypnus/Project/rag-enterprise/data/crawled_products_final')

    # Source directories
    cap_dir = crawled_dir / 'Cap'
    pump_dir = crawled_dir / 'Pump'
    cappump_dir = crawled_dir / 'Cappump'

    # Target directories (will be recreated)
    new_cap_dir = crawled_dir / 'Cap_consolidated'
    new_pump_dir = crawled_dir / 'Pump_consolidated'

    # Create new directories
    new_cap_dir.mkdir(exist_ok=True)
    new_pump_dir.mkdir(exist_ok=True)

    stats = {
        'cap': 0,
        'pump': 0,
        'duplicates_removed': 0
    }

    seen_products = set()  # Track product codes to avoid duplicates

    def process_product(json_file, target_category):
        """Process a single product file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            specs = product.get('specifications', {})
            product_code = specs.get('제품 코드', json_file.stem)

            # Skip if already processed
            if product_code in seen_products:
                stats['duplicates_removed'] += 1
                return False

            seen_products.add(product_code)

            # Determine material
            material = specs.get('재질(원료)', 'Other')

            # Determine target directory
            if target_category == 'Cap':
                target_dir = new_cap_dir
            else:
                target_dir = new_pump_dir

            # Create material subdirectory
            material_dir = target_dir / material / 'products'
            material_dir.mkdir(parents=True, exist_ok=True)

            # Copy product file
            target_file = material_dir / json_file.name
            shutil.copy2(json_file, target_file)

            stats[target_category.lower()] += 1
            return True

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            return False

    # Process Cappump -> Cap (all 118 products)
    print("Processing Cappump -> Cap...")
    if cappump_dir.exists():
        for material_dir in cappump_dir.iterdir():
            if not material_dir.is_dir() or material_dir.name.startswith('.'):
                continue

            products_dir = material_dir / 'products'
            if not products_dir.exists():
                continue

            for json_file in products_dir.glob('*.json'):
                process_product(json_file, 'Cap')

    # Process existing Pump directory
    print("Processing Pump...")
    if pump_dir.exists():
        for material_dir in pump_dir.iterdir():
            if not material_dir.is_dir() or material_dir.name.startswith('.'):
                continue

            products_dir = material_dir / 'products'
            if not products_dir.exists():
                continue

            for json_file in products_dir.glob('*.json'):
                process_product(json_file, 'Pump')

    # Process existing Cap directory (if has any files)
    print("Processing Cap...")
    if cap_dir.exists():
        for material_dir in cap_dir.iterdir():
            if not material_dir.is_dir() or material_dir.name.startswith('.'):
                continue

            products_dir = material_dir / 'products'
            if not products_dir.exists():
                continue

            for json_file in products_dir.glob('*.json'):
                process_product(json_file, 'Cap')

    # Print statistics
    print(f"\n=== Consolidation Complete ===")
    print(f"Cap products: {stats['cap']}")
    print(f"Pump products: {stats['pump']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"\nNew directories created:")
    print(f"  - {new_cap_dir}")
    print(f"  - {new_pump_dir}")
    print(f"\nPlease review and then:")
    print(f"  1. Backup old directories")
    print(f"  2. mv {new_cap_dir} {cap_dir.parent / 'Cap'}")
    print(f"  3. mv {new_pump_dir} {pump_dir.parent / 'Pump'}")
    print(f"  4. Remove Cappump directory")

if __name__ == '__main__':
    main()
