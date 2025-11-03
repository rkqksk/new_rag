#!/usr/bin/env python3
"""
Phase 1: Recover Missing Products
Copies 102 missing CapPump products from organized to updated folder
"""

import json
import shutil
import logging
from pathlib import Path
from typing import List
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path("/Users/oypnus/Project/rag-enterprise/data")
ORGANIZED_DIR = DATA_DIR / "crawled_products_organized"
UPDATED_DIR = DATA_DIR / "crawled_products_updated"
QUALITY_DIR = DATA_DIR / "quality"
RECONCILIATION_DIR = QUALITY_DIR / "reconciliation"


class MissingProductRecovery:
    """Recover missing products from organized folder"""

    def __init__(self):
        self.recovered_count = 0
        self.recovery_log = []

    def load_missing_products_report(self) -> List[dict]:
        """Load missing products from reconciliation report"""
        report_file = RECONCILIATION_DIR / "missing_products.json"

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            return report["missing_products"]
        except Exception as e:
            logger.error(f"Error loading report: {e}")
            return []

    def recover_product_files(self, product_id: str, source_category: str) -> bool:
        """Recover all files for a product (JSON + images + PDFs)"""
        try:
            # Source paths
            source_product_dir = ORGANIZED_DIR / source_category / "products"
            source_product_json = source_product_dir / f"{product_id}.json"

            if not source_product_json.exists():
                logger.warning(f"Product JSON not found: {source_product_json}")
                return False

            # Load product JSON to normalize it
            with open(source_product_json, 'r', encoding='utf-8') as f:
                product_data = json.load(f)

            # Create/update product JSON in updated folder
            target_product_json = UPDATED_DIR / f"{product_id}.json"

            # Add category info if not present
            if "category" not in product_data:
                product_data["category"] = source_category

            # Save to updated folder
            with open(target_product_json, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2, ensure_ascii=False)

            # Copy associated images
            source_images_dir = ORGANIZED_DIR / source_category / "images"
            if source_images_dir.exists():
                # Find all images for this product (pattern: idx_XXX_*.jpg)
                for image_file in source_images_dir.glob(f"{product_id}_*.jpg"):
                    target_image = UPDATED_DIR / "images" / image_file.name
                    UPDATED_DIR.joinpath("images").mkdir(exist_ok=True)
                    shutil.copy2(image_file, target_image)

            # Copy associated PDFs
            source_pdf_dir = ORGANIZED_DIR / source_category / "print_area"
            if source_pdf_dir.exists():
                for pdf_file in source_pdf_dir.glob(f"{product_id}_*.pdf"):
                    target_pdf = UPDATED_DIR / "print_area" / pdf_file.name
                    UPDATED_DIR.joinpath("print_area").mkdir(exist_ok=True)
                    shutil.copy2(pdf_file, target_pdf)

            self.recovery_log.append({
                "product_id": product_id,
                "category": source_category,
                "status": "recovered",
                "json": str(target_product_json),
                "images": len(list(ORGANIZED_DIR.joinpath(source_category, "images").glob(f"{product_id}_*.jpg")))
            })

            self.recovered_count += 1
            return True

        except Exception as e:
            logger.error(f"Error recovering {product_id}: {e}")
            self.recovery_log.append({
                "product_id": product_id,
                "status": "failed",
                "error": str(e)
            })
            return False

    def save_recovery_log(self):
        """Save recovery operation log"""
        log_file = RECONCILIATION_DIR / "recovery_log.json"

        log_data = {
            "total_attempted": len(self.recovery_log),
            "total_recovered": self.recovered_count,
            "operations": self.recovery_log
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Recovery log saved to {log_file}")

    def run_recovery(self):
        """Run recovery process"""
        logger.info("🔄 Starting missing product recovery...")

        missing_products = self.load_missing_products_report()

        if not missing_products:
            logger.error("No missing products found in report")
            return

        logger.info(f"📦 Recovering {len(missing_products)} products...")

        for product in missing_products:
            product_id = product["product_id"]
            category = product["category"]

            logger.info(f"  Recovering {product_id} ({category})...")
            self.recover_product_files(product_id, category)

        logger.info(f"✅ Recovery complete! Recovered {self.recovered_count}/{len(missing_products)}")
        self.save_recovery_log()


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Recover Missing Products"
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Execute recovery"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be recovered without copying"
    )

    args = parser.parse_args()

    if args.recover:
        recovery = MissingProductRecovery()
        recovery.run_recovery()
    elif args.dry_run:
        recovery = MissingProductRecovery()
        missing = recovery.load_missing_products_report()
        print(f"Would recover {len(missing)} products:")
        for product in missing[:10]:
            print(f"  - {product['product_id']}: {product['product_name']}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
