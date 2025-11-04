#!/usr/bin/env python3
"""
Phase 3: Restructure Data
- Source: crawled_products_updated (superior data content)
- Structure: crawled_products_organized (superior folder hierarchy)
- Destination: crawled_products_final (golden source)

Result: Best data + Best structure = Optimal RAG dataset
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime
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
FINAL_DIR = DATA_DIR / "crawled_products_final"
QUALITY_DIR = DATA_DIR / "quality"

# Ensure quality directory exists
QUALITY_DIR.mkdir(exist_ok=True)


class DataRestructurer:
    """Restructure data from updated into organized hierarchy"""

    def __init__(self):
        self.restructure_log = []
        self.stats = {
            "total_products": 0,
            "products_moved": 0,
            "images_copied": 0,
            "pdfs_copied": 0,
            "errors": 0
        }

    def load_product_json(self, filepath: Path) -> Dict:
        """Load product JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return {}

    def get_product_category(self, product_data: Dict) -> str:
        """Determine product category from specifications or metadata"""
        # Try to infer category from product info
        product_name = product_data.get("product_name", "").lower()
        specs = product_data.get("specifications", {})

        # Check product name for hints
        if "병" in product_name or "용기" in product_name or "bottle" in product_name:
            return "Bottle"
        elif "펌프" in product_name or "pump" in product_name or "cap" in product_name:
            return "CapPump"
        elif "jar" in product_name:
            return "Jar"

        # If not found, try to find from specs product code
        product_code = specs.get("제품 코드", "").upper() if isinstance(specs, dict) else ""
        if product_code:
            if product_code.startswith("BE"):
                return "Bottle"
            elif product_code.startswith("PO"):
                return "CapPump"
            elif product_code.startswith("JR"):
                return "Jar"

        # Default fallback - try to load from organized structure if exists
        # This is just a safety measure
        return "Unknown"

    def initialize_final_structure(self):
        """Create the final directory structure"""
        logger.info("📁 Initializing final directory structure...")

        categories = ["Bottle", "CapPump", "Jar"]

        for category in categories:
            category_dir = FINAL_DIR / category
            category_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (category_dir / "products").mkdir(exist_ok=True)
            (category_dir / "images").mkdir(exist_ok=True)
            (category_dir / "print_area").mkdir(exist_ok=True)

        logger.info(f"✅ Directory structure created at {FINAL_DIR}")

    def copy_product_to_category(self, product_id: str, category: str) -> bool:
        """Copy product JSON from updated to final category"""
        try:
            source_json = UPDATED_DIR / f"{product_id}.json"
            if not source_json.exists():
                logger.warning(f"Product JSON not found: {product_id}")
                return False

            # Load and verify product data
            product_data = self.load_product_json(source_json)
            if not product_data:
                return False

            # Determine actual category
            inferred_category = self.get_product_category(product_data)
            if inferred_category != category and inferred_category != "Unknown":
                logger.debug(f"Category mismatch: {product_id} - stored as {inferred_category}")
                category = inferred_category

            # Create target path
            target_json = FINAL_DIR / category / "products" / f"{product_id}.json"

            # Copy JSON
            with open(source_json, 'r', encoding='utf-8') as f:
                product_data = json.load(f)

            with open(target_json, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2, ensure_ascii=False)

            self.stats["products_moved"] += 1
            return True

        except Exception as e:
            logger.error(f"Error copying product {product_id}: {e}")
            self.stats["errors"] += 1
            return False

    def copy_images_to_category(self, product_id: str, category: str):
        """Copy all images for a product"""
        try:
            source_images_dir = UPDATED_DIR / "images"
            target_images_dir = FINAL_DIR / category / "images"

            if not source_images_dir.exists():
                return

            # Find all images for this product (pattern: idx_XXX_*.jpg)
            for image_file in source_images_dir.glob(f"{product_id}_*.jpg"):
                target_image = target_images_dir / image_file.name
                shutil.copy2(image_file, target_image)
                self.stats["images_copied"] += 1

        except Exception as e:
            logger.error(f"Error copying images for {product_id}: {e}")
            self.stats["errors"] += 1

    def copy_pdfs_to_category(self, product_id: str, category: str):
        """Copy all PDFs for a product"""
        try:
            source_pdf_dir = UPDATED_DIR / "print_area"
            target_pdf_dir = FINAL_DIR / category / "print_area"

            if not source_pdf_dir.exists():
                return

            # Find all PDFs for this product (pattern: idx_XXX_*.pdf)
            for pdf_file in source_pdf_dir.glob(f"{product_id}_*.pdf"):
                target_pdf = target_pdf_dir / pdf_file.name
                shutil.copy2(pdf_file, target_pdf)
                self.stats["pdfs_copied"] += 1

        except Exception as e:
            logger.error(f"Error copying PDFs for {product_id}: {e}")
            self.stats["errors"] += 1

    def organize_products_by_category(self) -> Dict[str, List[str]]:
        """Scan updated folder and organize products by category"""
        logger.info("🔍 Scanning products and determining categories...")

        category_map = defaultdict(list)
        product_files = list(UPDATED_DIR.glob("idx_*.json"))

        logger.info(f"📊 Processing {len(product_files)} products...")

        for idx, product_file in enumerate(product_files):
            product_id = product_file.stem
            product_data = self.load_product_json(product_file)

            if not product_data:
                continue

            category = self.get_product_category(product_data)
            category_map[category].append(product_id)

            if (idx + 1) % 50 == 0:
                logger.info(f"  Scanned {idx + 1}/{len(product_files)}...")

        logger.info(f"📈 Category distribution:")
        for category, products in sorted(category_map.items()):
            logger.info(f"  - {category}: {len(products)} products")

        return category_map

    def restructure_all_data(self):
        """Restructure all data from updated to final"""
        logger.info("🔄 Starting data restructuring...")

        # Initialize directory structure
        self.initialize_final_structure()

        # Organize by category
        category_map = self.organize_products_by_category()

        # Restructure each product
        total_products = sum(len(p) for p in category_map.values())
        processed = 0

        for category, product_ids in sorted(category_map.items()):
            logger.info(f"\n📦 Processing {category} ({len(product_ids)} products)...")

            for product_id in product_ids:
                # Copy product JSON
                if self.copy_product_to_category(product_id, category):
                    # Copy associated assets
                    self.copy_images_to_category(product_id, category)
                    self.copy_pdfs_to_category(product_id, category)

                processed += 1
                if processed % 50 == 0:
                    logger.info(f"  Progress: {processed}/{total_products}...")

        logger.info(f"\n✅ Restructuring complete!")
        self.print_statistics()

    def print_statistics(self):
        """Print restructuring statistics"""
        logger.info("📊 Restructuring Statistics:")
        logger.info(f"  Products moved:     {self.stats['products_moved']}")
        logger.info(f"  Images copied:      {self.stats['images_copied']}")
        logger.info(f"  PDFs copied:        {self.stats['pdfs_copied']}")
        logger.info(f"  Errors:             {self.stats['errors']}")

    def save_restructure_log(self):
        """Save restructuring operation log"""
        log_file = QUALITY_DIR / "restructure_log.json"

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "source": str(UPDATED_DIR),
            "destination": str(FINAL_DIR),
            "structure": "Bottle/CapPump/Jar with products/images/print_area subdirs",
            "statistics": self.stats
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Restructure log saved to {log_file}")

    def verify_structure(self):
        """Verify final structure integrity"""
        logger.info("✓ Verifying final structure...")

        categories = ["Bottle", "CapPump", "Jar"]
        for category in categories:
            category_dir = FINAL_DIR / category
            products_dir = category_dir / "products"
            images_dir = category_dir / "images"

            product_count = len(list(products_dir.glob("idx_*.json")))
            image_count = len(list(images_dir.glob("*.jpg")))

            logger.info(f"  {category}: {product_count} products, {image_count} images")

        logger.info("✅ Structure verification complete")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3: Restructure Data"
    )
    parser.add_argument(
        "--restructure",
        action="store_true",
        help="Execute data restructuring"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify final structure"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    restructurer = DataRestructurer()

    if args.restructure:
        restructurer.restructure_all_data()
        restructurer.save_restructure_log()
        restructurer.verify_structure()
    elif args.verify:
        restructurer.verify_structure()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
