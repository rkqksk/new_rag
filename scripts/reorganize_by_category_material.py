#!/usr/bin/env python3
"""
Reorganize products into hierarchical structure:
Category (Bottle/CapPump/Jar) → Material (PE/PET/PETG/PP/Other) → products/

Usage:
    python scripts/reorganize_by_category_material.py
    python scripts/reorganize_by_category_material.py --dry-run
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Tuple
import argparse


class CategoryMaterialOrganizer:
    """Reorganize products by Category → Material hierarchy"""

    def __init__(self, base_dir: str = "data/crawled_products_final"):
        self.base_dir = Path(base_dir)

        # Source: flat material folders
        self.source_materials = ["PE", "PET", "PETG", "PP", "Other"]

        # Target: Category/Material hierarchy
        self.categories = ["Bottle", "CapPump", "Jar"]
        self.materials = ["PE", "PET", "PETG", "PP", "Other"]

    def detect_category(self, product_data: dict) -> str:
        """
        Detect product category from product name

        Returns: "Bottle", "CapPump", "Jar", or None
        """
        product_name = product_data.get("product_name", "").lower()

        # CapPump keywords (most specific first)
        pump_keywords = ["펌프", "pump", "캡", "cap"]
        if any(kw in product_name for kw in pump_keywords):
            return "CapPump"

        # Jar keywords
        jar_keywords = ["크림", "jar", "cream"]
        if any(kw in product_name for kw in jar_keywords):
            return "Jar"

        # Bottle keywords (default for containers)
        bottle_keywords = ["용기", "병", "브로우", "bottle", "ml"]
        if any(kw in product_name for kw in bottle_keywords):
            return "Bottle"

        return None

    def get_material(self, product_data: dict) -> str:
        """Extract material from product specifications"""
        specs = product_data.get("specifications", {})

        # Check for material field
        for key, value in specs.items():
            if '재질' in key or 'Material' in key.lower() or '원료' in key:
                material_value = str(value).upper()

                # Extract material type
                if 'PETG' in material_value:
                    return "PETG"
                elif 'PET' in material_value:
                    return "PET"
                elif 'PE' in material_value:
                    return "PE"
                elif 'PP' in material_value:
                    return "PP"

        return "Other"

    def reorganize(self, dry_run: bool = False):
        """Reorganize all products into Category/Material/products/ structure"""

        print("=" * 80)
        print("Category → Material Reorganization")
        print("=" * 80)
        print(f"Base directory: {self.base_dir}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print("=" * 80)

        stats = {
            "total_processed": 0,
            "successful": 0,
            "skipped": 0,
            "by_category": {cat: 0 for cat in self.categories},
            "by_material": {mat: 0 for mat in self.materials},
            "category_material": {
                cat: {mat: 0 for mat in self.materials}
                for cat in self.categories
            }
        }

        # Create target directory structure
        if not dry_run:
            for category in self.categories:
                for material in self.materials:
                    target_dir = self.base_dir / category / material / "products"
                    target_dir.mkdir(parents=True, exist_ok=True)
                    print(f"✓ Created: {target_dir}")

        # Process each source material folder
        for material in self.source_materials:
            source_dir = self.base_dir / material / "products"

            if not source_dir.exists():
                print(f"⏭️  Skipping {material} (not found)")
                continue

            product_files = list(source_dir.glob("idx_*.json"))
            print(f"\n📂 Processing {material}: {len(product_files)} products")

            for json_file in product_files:
                stats["total_processed"] += 1
                idx = json_file.stem.replace("idx_", "")

                try:
                    # Read product data
                    with open(json_file, 'r', encoding='utf-8') as f:
                        product_data = json.load(f)

                    # Detect category
                    category = self.detect_category(product_data)
                    if not category:
                        print(f"⚠️  idx_{idx}: Could not detect category for '{product_data.get('product_name', 'Unknown')}'")
                        stats["skipped"] += 1
                        continue

                    # Verify material
                    detected_material = self.get_material(product_data)
                    if detected_material != material:
                        print(f"⚠️  idx_{idx}: Material mismatch (folder={material}, detected={detected_material})")

                    # Target path: Category/Material/products/
                    target_file = self.base_dir / category / material / "products" / f"idx_{idx}.json"

                    # Check if already exists
                    if target_file.exists():
                        print(f"⏭️  idx_{idx}: Already exists at {category}/{material}/")
                        stats["skipped"] += 1
                        continue

                    # Move file
                    if not dry_run:
                        shutil.copy2(json_file, target_file)

                    print(f"✅ idx_{idx}: {product_data.get('product_name', 'Unknown')[:30]} → {category}/{material}/")

                    stats["successful"] += 1
                    stats["by_category"][category] += 1
                    stats["by_material"][material] += 1
                    stats["category_material"][category][material] += 1

                except Exception as e:
                    print(f"❌ idx_{idx}: Error - {e}")
                    stats["skipped"] += 1

        # Print summary
        print("\n" + "=" * 80)
        print("REORGANIZATION SUMMARY")
        print("=" * 80)
        print(f"Total processed: {stats['total_processed']}")
        print(f"Successfully reorganized: {stats['successful']}")
        print(f"Skipped: {stats['skipped']}")

        print("\n📊 By Category:")
        for category in self.categories:
            print(f"  {category}: {stats['by_category'][category]} products")

        print("\n📊 By Material:")
        for material in self.materials:
            print(f"  {material}: {stats['by_material'][material]} products")

        print("\n📊 Category × Material Matrix:")
        print(f"{'Category':<12}", end="")
        for mat in self.materials:
            print(f"{mat:>8}", end="")
        print()
        print("-" * 60)

        for category in self.categories:
            print(f"{category:<12}", end="")
            for material in self.materials:
                count = stats["category_material"][category][material]
                print(f"{count:>8}", end="")
            print()

        print("=" * 80)

        if dry_run:
            print("\n⚠️  DRY RUN - No files were moved")
            print("Run without --dry-run to apply changes")
        else:
            print("\n✅ Reorganization complete!")


def main():
    parser = argparse.ArgumentParser(description="Reorganize products by Category → Material")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files"
    )
    parser.add_argument(
        "--base-dir",
        default="data/crawled_products_final",
        help="Base directory (default: data/crawled_products_final)"
    )

    args = parser.parse_args()

    organizer = CategoryMaterialOrganizer(base_dir=args.base_dir)
    organizer.reorganize(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
