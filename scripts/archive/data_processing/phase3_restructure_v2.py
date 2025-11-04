#!/usr/bin/env python3
"""
Phase 3 v2: Restructure Data - Using organized folder as category reference
- Source: crawled_products_organized (category truth) + crawled_products_updated (data truth)
- Destination: crawled_products_final (golden dataset)
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path("/Users/oypnus/Project/rag-enterprise/data")
ORGANIZED_DIR = DATA_DIR / "crawled_products_organized"
UPDATED_DIR = DATA_DIR / "crawled_products_updated"
FINAL_DIR = DATA_DIR / "crawled_products_final"
QUALITY_DIR = DATA_DIR / "quality"


class DataRestructurerV2:
    """Restructure using organized as category source"""

    def __init__(self):
        self.category_map = {}
        self.stats = {
            "products_moved": 0,
            "images_copied": 0,
            "pdfs_copied": 0,
            "errors": 0
        }

    def load_category_mapping(self):
        """Load category mapping from organized folder"""
        logger.info("📚 Loading category mapping from organized folder...")

        categories = ["Bottle", "CapPump", "Jar"]
        for category in categories:
            products_dir = ORGANIZED_DIR / category / "products"
            for json_file in products_dir.glob("idx_*.json"):
                product_id = json_file.stem
                self.category_map[product_id] = category

        logger.info(f"✅ Loaded {len(self.category_map)} product categories")

    def initialize_final_structure(self):
        """Create final directory structure"""
        logger.info("📁 Initializing final directory structure...")

        # Clean up if exists
        if FINAL_DIR.exists():
            shutil.rmtree(FINAL_DIR)

        categories = ["Bottle", "CapPump", "Jar"]
        for category in categories:
            category_dir = FINAL_DIR / category
            (category_dir / "products").mkdir(parents=True, exist_ok=True)
            (category_dir / "images").mkdir(exist_ok=True)
            (category_dir / "print_area").mkdir(exist_ok=True)

        logger.info(f"✅ Structure created at {FINAL_DIR}")

    def restructure_all_data(self):
        """Restructure all products"""
        logger.info("🔄 Starting data restructuring with category mapping...")

        self.load_category_mapping()
        self.initialize_final_structure()

        # Process each product
        total = len(self.category_map)
        for idx, (product_id, category) in enumerate(sorted(self.category_map.items())):
            # Copy JSON from updated
            source_json = UPDATED_DIR / f"{product_id}.json"
            if not source_json.exists():
                self.stats["errors"] += 1
                continue

            try:
                target_json = FINAL_DIR / category / "products" / f"{product_id}.json"
                shutil.copy2(source_json, target_json)
                self.stats["products_moved"] += 1

                # Copy images
                source_images_dir = UPDATED_DIR / "images"
                target_images_dir = FINAL_DIR / category / "images"
                for image_file in source_images_dir.glob(f"{product_id}_*.jpg"):
                    target_image = target_images_dir / image_file.name
                    shutil.copy2(image_file, target_image)
                    self.stats["images_copied"] += 1

                # Copy PDFs
                source_pdf_dir = UPDATED_DIR / "print_area"
                target_pdf_dir = FINAL_DIR / category / "print_area"
                for pdf_file in source_pdf_dir.glob(f"{product_id}_*.pdf"):
                    target_pdf = target_pdf_dir / pdf_file.name
                    shutil.copy2(pdf_file, target_pdf)
                    self.stats["pdfs_copied"] += 1

                if (idx + 1) % 50 == 0:
                    logger.info(f"  Progress: {idx + 1}/{total}...")

            except Exception as e:
                logger.error(f"Error processing {product_id}: {e}")
                self.stats["errors"] += 1

        logger.info(f"\n✅ Restructuring complete!")
        self.print_statistics()

    def print_statistics(self):
        """Print statistics"""
        logger.info("📊 Statistics:")
        logger.info(f"  Products moved:  {self.stats['products_moved']}")
        logger.info(f"  Images copied:   {self.stats['images_copied']}")
        logger.info(f"  PDFs copied:     {self.stats['pdfs_copied']}")
        logger.info(f"  Errors:          {self.stats['errors']}")

    def verify_structure(self):
        """Verify final structure"""
        logger.info("✓ Verifying final structure...")

        categories = ["Bottle", "CapPump", "Jar"]
        total_products = 0
        total_images = 0

        for category in categories:
            category_dir = FINAL_DIR / category
            products = len(list((category_dir / "products").glob("idx_*.json")))
            images = len(list((category_dir / "images").glob("*.jpg")))
            total_products += products
            total_images += images

            logger.info(f"  {category}: {products} products, {images} images")

        logger.info(f"\n📊 Final structure summary:")
        logger.info(f"  Total products:  {total_products}")
        logger.info(f"  Total images:    {total_images}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 v2: Restructure Data"
    )
    parser.add_argument("--restructure", action="store_true", help="Execute restructuring")
    parser.add_argument("--verify", action="store_true", help="Verify structure")

    args = parser.parse_args()

    restructurer = DataRestructurerV2()

    if args.restructure:
        restructurer.restructure_all_data()
        restructurer.verify_structure()
    elif args.verify:
        restructurer.load_category_mapping()
        restructurer.verify_structure()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
