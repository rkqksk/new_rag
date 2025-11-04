#!/usr/bin/env python3
"""
Reorganize Existing Products by Material
Moves existing 398 products from Bottle/Jar/CapPump to PE/PET/PETG/PP/Other

Usage:
    python scripts/reorganize_by_material.py
    python scripts/reorganize_by_material.py --dry-run  # Preview changes only
"""

import json
import logging
import argparse
import shutil
from pathlib import Path
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MaterialReorganizer:
    """Reorganize products from category-based to material-based structure"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

        # Current structure
        self.old_categories = ["Bottle", "Jar", "CapPump"]

        # New material structure
        self.materials = ["PE", "PET", "PETG", "PP", "Other"]

        # Statistics
        self.stats = {
            "total_products": 0,
            "by_material": {material: 0 for material in self.materials},
            "moved": 0,
            "failed": 0,
            "errors": []
        }

    def _extract_material(self, product_data: dict) -> str:
        """Extract material from product specifications"""
        specs = product_data.get("specifications", {})

        # Check for material field
        material_value = None
        for key, value in specs.items():
            if '재질' in key or 'Material' in key.lower() or '원료' in key:
                material_value = str(value).upper()
                break

        if not material_value:
            return "Other"

        # Extract material type
        if 'PETG' in material_value:
            return "PETG"
        elif 'PET' in material_value:
            return "PET"
        elif 'PE' in material_value:
            return "PE"
        elif 'PP' in material_value:
            return "PP"
        else:
            return "Other"

    def analyze_current_structure(self):
        """Analyze current products and their materials"""
        logger.info("\n" + "="*80)
        logger.info("Analyzing Current Products...")
        logger.info("="*80)

        analysis = defaultdict(list)

        for category in self.old_categories:
            category_path = self.base_dir / category / "products"

            if not category_path.exists():
                logger.warning(f"Category not found: {category}")
                continue

            json_files = list(category_path.glob("*.json"))
            logger.info(f"\n{category}: {len(json_files)} products")

            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        product_data = json.load(f)

                    material = self._extract_material(product_data)
                    idx = product_data.get("idx", json_file.stem.replace("idx_", ""))

                    analysis[material].append({
                        "idx": idx,
                        "product_name": product_data.get("product_name", "Unknown"),
                        "current_category": category,
                        "json_path": json_file
                    })

                except Exception as e:
                    logger.error(f"Error reading {json_file}: {e}")

        # Print analysis
        logger.info("\n" + "-"*80)
        logger.info("Material Distribution:")
        logger.info("-"*80)
        for material in self.materials:
            count = len(analysis[material])
            logger.info(f"{material:6s}: {count:4d} products")
        logger.info(f"{'TOTAL':6s}: {sum(len(v) for v in analysis.values()):4d} products")
        logger.info("-"*80)

        return analysis

    def reorganize(self, dry_run: bool = False):
        """Reorganize products by material"""
        logger.info("\n" + "="*80)
        if dry_run:
            logger.info("DRY RUN MODE - No files will be moved")
        else:
            logger.info("REORGANIZING PRODUCTS BY MATERIAL")
        logger.info("="*80)

        # Analyze current structure
        analysis = self.analyze_current_structure()

        # Create material directories
        if not dry_run:
            for material in self.materials:
                (self.base_dir / material / "products").mkdir(parents=True, exist_ok=True)
                (self.base_dir / material / "images").mkdir(parents=True, exist_ok=True)
                (self.base_dir / material / "print_area").mkdir(parents=True, exist_ok=True)
                logger.info(f"✓ Created directory: {material}/")

        # Move products by material
        for material, products in analysis.items():
            if not products:
                continue

            logger.info(f"\n{'='*80}")
            logger.info(f"Moving {len(products)} products to {material}/")
            logger.info(f"{'='*80}")

            for product_info in products:
                try:
                    idx = product_info["idx"]
                    old_category = product_info["current_category"]
                    old_json_path = product_info["json_path"]

                    # Load product data
                    with open(old_json_path, 'r', encoding='utf-8') as f:
                        product_data = json.load(f)

                    # New paths
                    new_json_path = self.base_dir / material / "products" / f"idx_{idx}.json"

                    logger.info(f"  idx_{idx}: {product_info['product_name'][:40]:40s} | {old_category:10s} → {material}")

                    if not dry_run:
                        # Move JSON file
                        shutil.copy2(old_json_path, new_json_path)

                        # Move images
                        images_moved = self._move_images(product_data, idx, material, old_category)

                        # Move print area PDF
                        pdf_moved = self._move_print_area(product_data, idx, material, old_category)

                        # Update JSON with new paths
                        with open(new_json_path, 'w', encoding='utf-8') as f:
                            json.dump(product_data, f, ensure_ascii=False, indent=2)

                        self.stats["moved"] += 1

                    self.stats["total_products"] += 1
                    self.stats["by_material"][material] += 1

                except Exception as e:
                    logger.error(f"  ❌ Failed to move idx_{idx}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append({
                        "idx": idx,
                        "error": str(e)
                    })

        # Print final summary
        self._print_summary(dry_run)

        return self.stats

    def _move_images(self, product_data: dict, idx: str, material: str, old_category: str) -> int:
        """Move product images to material folder"""
        moved_count = 0

        for img_info in product_data.get("downloaded_images", []):
            if "local_path" in img_info:
                old_path = Path(img_info["local_path"])

                # Check in old category structure
                if not old_path.exists():
                    # Try alternate path
                    old_path = self.base_dir / old_category / "images" / old_path.name

                if old_path.exists():
                    # New path in material folder
                    new_filename = f"idx_{idx}_{img_info['type']}_{old_path.name}"
                    new_path = self.base_dir / material / "images" / new_filename

                    try:
                        shutil.copy2(old_path, new_path)
                        img_info["local_path"] = str(new_path)
                        moved_count += 1
                    except Exception as e:
                        logger.debug(f"Failed to move image: {e}")

        return moved_count

    def _move_print_area(self, product_data: dict, idx: str, material: str, old_category: str) -> bool:
        """Move print area PDF to material folder"""
        if not product_data.get("print_area_local_path"):
            return False

        old_path = Path(product_data["print_area_local_path"])

        # Check in old category structure
        if not old_path.exists():
            old_path = self.base_dir / old_category / "print_area" / old_path.name

        if old_path.exists():
            new_filename = f"idx_{idx}_print_area.pdf"
            new_path = self.base_dir / material / "print_area" / new_filename

            try:
                shutil.copy2(old_path, new_path)
                product_data["print_area_local_path"] = str(new_path)
                return True
            except Exception as e:
                logger.debug(f"Failed to move print area PDF: {e}")

        return False

    def _print_summary(self, dry_run: bool):
        """Print reorganization summary"""
        logger.info("\n" + "="*80)
        logger.info("REORGANIZATION SUMMARY")
        logger.info("="*80)

        if dry_run:
            logger.info("Mode: DRY RUN (no files moved)")
        else:
            logger.info("Mode: LIVE (files moved)")

        logger.info(f"\nTotal products processed: {self.stats['total_products']}")

        if not dry_run:
            logger.info(f"Successfully moved: {self.stats['moved']}")
            logger.info(f"Failed: {self.stats['failed']}")

        logger.info("\nProducts by Material:")
        for material in self.materials:
            count = self.stats["by_material"][material]
            if count > 0:
                logger.info(f"  {material:6s}: {count:4d} products")

        logger.info("\nNew Directory Structure:")
        for material in self.materials:
            count = self.stats["by_material"][material]
            if count > 0:
                logger.info(f"  {self.base_dir}/{material}/products/  ({count} files)")

        if self.stats["errors"]:
            logger.info(f"\n⚠️  {len(self.stats['errors'])} errors occurred:")
            for error in self.stats["errors"][:5]:
                logger.info(f"  - idx_{error['idx']}: {error['error']}")

        logger.info("="*80)

    def cleanup_old_structure(self):
        """Remove old category directories after successful reorganization"""
        logger.info("\n" + "="*80)
        logger.info("Cleaning up old category structure...")
        logger.info("="*80)

        for category in self.old_categories:
            category_path = self.base_dir / category

            if category_path.exists():
                try:
                    shutil.rmtree(category_path)
                    logger.info(f"✓ Removed: {category}/")
                except Exception as e:
                    logger.error(f"Failed to remove {category}/: {e}")

        logger.info("Cleanup complete!")


def main():
    """Main execution function"""

    parser = argparse.ArgumentParser(description="Reorganize products by material")
    parser.add_argument(
        "--base-dir",
        type=str,
        default="data/crawled_products_final",
        help="Base directory (default: data/crawled_products_final)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove old category directories after reorganization"
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("Product Reorganization by Material")
    print("="*80)
    print(f"Base directory: {args.base_dir}")
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE (will move files)'}")
    print(f"Cleanup old structure: {args.cleanup}")
    print("="*80)

    if not args.dry_run:
        response = input("\n⚠️  This will reorganize all existing products. Continue? (y/n): ")
        if response.lower() != 'y':
            print("Reorganization cancelled.")
            return

    # Execute reorganization
    reorganizer = MaterialReorganizer(base_dir=args.base_dir)

    try:
        stats = reorganizer.reorganize(dry_run=args.dry_run)

        if not args.dry_run and args.cleanup and stats["failed"] == 0:
            cleanup_response = input("\n🗑️  Remove old category directories? (y/n): ")
            if cleanup_response.lower() == 'y':
                reorganizer.cleanup_old_structure()

        print("\n✅ Reorganization complete!")

    except Exception as e:
        logger.error(f"Reorganization failed: {e}", exc_info=True)
        print(f"\n❌ Reorganization failed: {e}")


if __name__ == "__main__":
    main()
