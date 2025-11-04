#!/usr/bin/env python3
"""
List all products missing material specification
Generate detailed report
"""

import json
from pathlib import Path
from typing import List, Dict


def find_products_missing_material(base_dir: str = "data/crawled_products_final") -> List[Dict]:
    """Find all products without material specification"""

    base_path = Path(base_dir)
    categories = ["Bottle", "CapPump", "Jar", "특별폴더"]
    materials = ["PE", "PET", "PETG", "PP", "Other"]

    missing_material_products = []

    for category in categories:
        for material in materials:
            products_dir = base_path / category / material / "products"

            if not products_dir.exists():
                continue

            for json_file in products_dir.glob("idx_*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Check for material spec
                    specs = data.get("specifications", {})
                    has_material = False

                    for key in specs.keys():
                        if any(kw in key for kw in ["재질", "Material", "원료"]):
                            has_material = True
                            break

                    if not has_material:
                        idx = json_file.stem.replace("idx_", "")

                        missing_material_products.append({
                            "idx": idx,
                            "category": category,
                            "material_folder": material,
                            "product_name": data.get("product_name", "Unknown"),
                            "category_label": data.get("category_label", "N/A"),
                            "specifications": specs,
                            "spec_count": len(specs),
                            "image_count": len(data.get("images", [])),
                            "has_print_area": bool(data.get("print_area_url")),
                            "url": data.get("url", "")
                        })

                except Exception as e:
                    print(f"Error reading {json_file}: {e}")

    # Sort by idx
    missing_material_products.sort(key=lambda x: int(x["idx"]))

    return missing_material_products


def print_detailed_report(products: List[Dict]):
    """Print detailed report"""

    print("=" * 100)
    print("COMPLETE LIST OF PRODUCTS MISSING MATERIAL SPECIFICATION")
    print("=" * 100)
    print(f"\nTotal: {len(products)} products\n")

    # Group by category
    by_category = {}
    for p in products:
        cat = p["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)

    print("Summary by Category:")
    for cat, items in sorted(by_category.items()):
        print(f"  {cat}: {len(items)} products")

    print("\n" + "=" * 100)
    print("DETAILED PRODUCT LIST")
    print("=" * 100)

    for idx, product in enumerate(products, 1):
        print(f"\n{idx}. idx_{product['idx']}")
        print(f"   Product Name: {product['product_name']}")
        print(f"   Category: {product['category']} (Label: {product['category_label']})")
        print(f"   Material Folder: {product['material_folder']}")
        print(f"   URL: {product['url']}")
        print(f"   Specifications: {product['spec_count']} items")

        if product['specifications']:
            for key, value in product['specifications'].items():
                print(f"      - {key}: {value}")
        else:
            print(f"      (No specifications)")

        print(f"   Images: {product['image_count']}")
        print(f"   Print Area: {'Yes' if product['has_print_area'] else 'No'}")
        print(f"   Location: {product['category']}/{product['material_folder']}/products/idx_{product['idx']}.json")


def save_json_report(products: List[Dict], output_file: str = "data/products_missing_material.json"):
    """Save report as JSON"""

    report = {
        "generated_at": "2025-10-21",
        "total_count": len(products),
        "by_category": {},
        "products": products
    }

    # Count by category
    for p in products:
        cat = p["category"]
        if cat not in report["by_category"]:
            report["by_category"][cat] = 0
        report["by_category"][cat] += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ JSON report saved to: {output_file}")


def main():
    products = find_products_missing_material()
    print_detailed_report(products)
    save_json_report(products)

    print("\n" + "=" * 100)
    print("ACTION ITEMS:")
    print("=" * 100)
    print("\n1. Review each product URL to verify if material info is truly missing")
    print("2. For CapPump products (caps/pumps), material may not be relevant")
    print("3. Consider adding 'material': 'Not Specified' for clarity")
    print("4. Manual data entry may be needed for critical products")
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
