#!/usr/bin/env python3
"""
Load Cap and Pump products from crawled data directories
Creates a unified accessory database for compatibility matching
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def load_crawled_products(base_dir: str, category_type: str) -> Dict[str, Any]:
    """Load all JSON files from crawled products directory

    Args:
        base_dir: Base directory path (e.g., "data/crawled_products_final/Cap")
        category_type: CAP or PUMP

    Returns:
        Dictionary of products {idx: product_data}
    """
    products = {}
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"⚠️  Directory not found: {base_dir}")
        return products

    # Find all JSON files recursively
    json_files = list(base_path.rglob("*.json"))

    print(f"📂 Found {len(json_files)} JSON files in {base_dir}")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product = json.load(f)

            # Get idx
            idx = product.get('idx')
            if not idx:
                print(f"  ⚠️  No idx in {json_file.name}")
                continue

            # Ensure category_type is set
            if 'category_type' not in product:
                product['category_type'] = category_type

            # Extract key fields for quick access
            product_id = f"idx_{idx}"

            # Get spec (사양) - contains neck size
            spec = product.get('specifications', {}).get('사양', '')
            if spec:
                product['spec'] = spec

            # Get product code
            product_code = product.get('product_code', '')
            if product_code:
                product['product_code'] = product_code

            # Get material
            material = product.get('specifications', {}).get('재질(원료)', '')
            if material:
                product['material'] = material

            # Get product name
            product_name = product.get('product_name', '')
            if product_name:
                product['product_name'] = product_name

            products[product_id] = product

        except Exception as e:
            print(f"  ❌ Error loading {json_file.name}: {e}")
            continue

    print(f"✅ Loaded {len(products)} {category_type} products")
    return products


def merge_with_product_dictionary(
    caps: Dict[str, Any],
    pumps: Dict[str, Any],
    output_path: str = "data/product_dictionary_with_accessories.json"
):
    """Merge Cap/Pump with existing product_dictionary.json

    Args:
        caps: Cap products
        pumps: Pump products
        output_path: Output file path
    """
    # Load existing product dictionary (bottles)
    try:
        with open('data/product_dictionary.json', 'r', encoding='utf-8') as f:
            bottles = json.load(f)
        print(f"📦 Loaded {len(bottles)} existing products (bottles)")
    except FileNotFoundError:
        bottles = {}
        print("⚠️  product_dictionary.json not found, starting fresh")

    # Merge all products
    all_products = {}
    all_products.update(bottles)
    all_products.update(caps)
    all_products.update(pumps)

    print(f"\n📊 Total products after merge: {len(all_products)}")
    print(f"  - Bottles: {len(bottles)}")
    print(f"  - Caps: {len(caps)}")
    print(f"  - Pumps: {len(pumps)}")

    # Save merged dictionary
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved merged dictionary to {output_path}")

    # Show sample products with neck sizes
    print("\n📋 Sample products with neck sizes:")
    count = 0
    for product_id, product in all_products.items():
        spec = product.get('spec', '')
        if 'Ø' in spec or 'ø' in spec or '내경' in spec:
            category = product.get('category_type', 'BOTTLE')
            name = product.get('product_name', 'N/A')
            print(f"  {category:6} | {product_id:10} | {name[:30]:30} | {spec}")
            count += 1
            if count >= 10:
                break


def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 Loading Crawled Accessories (Cap & Pump)")
    print("=" * 80)

    # Load Caps
    print("\n1️⃣  Loading Caps...")
    caps = load_crawled_products(
        "data/crawled_products_final/Cap",
        "CAP"
    )

    # Load Pumps
    print("\n2️⃣  Loading Pumps...")
    pumps = load_crawled_products(
        "data/crawled_products_final/Pump",
        "PUMP"
    )

    # Merge with existing dictionary
    print("\n3️⃣  Merging with existing product_dictionary.json...")
    merge_with_product_dictionary(caps, pumps)

    print("\n" + "=" * 80)
    print("✅ Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
