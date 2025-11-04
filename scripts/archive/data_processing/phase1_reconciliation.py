#!/usr/bin/env python3
"""
Phase 1: Data Reconciliation & Cleanup
Analyzes 72 missing products, finds duplicates, and resolves conflicts

Usage:
    python scripts/phase1_reconciliation.py --analyze
    python scripts/phase1_reconciliation.py --deduplicate
    python scripts/phase1_reconciliation.py --merge
"""

import json
import hashlib
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
import difflib
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
QUALITY_DIR = DATA_DIR / "quality"
RECONCILIATION_DIR = QUALITY_DIR / "reconciliation"

# Ensure directories exist
QUALITY_DIR.mkdir(exist_ok=True)
RECONCILIATION_DIR.mkdir(exist_ok=True)


@dataclass
class ProductMetadata:
    """Product metadata for comparison"""
    product_id: str
    product_name: str
    category: str
    source: str  # "organized" or "updated"
    file_path: str
    hash_md5: str = ""

    def to_dict(self):
        return asdict(self)


class DataReconciliation:
    """Main reconciliation class"""

    def __init__(self):
        self.organized_products: Dict[str, ProductMetadata] = {}
        self.updated_products: Dict[str, ProductMetadata] = {}
        self.missing_products: List[ProductMetadata] = []
        self.duplicate_candidates: List[Tuple[ProductMetadata, ProductMetadata]] = []
        self.conflicts: List[Dict] = []

    def extract_product_id(self, filename: str) -> str:
        """Extract product ID from filename"""
        # Handles both "idx_123.json" and other naming patterns
        import re
        match = re.search(r'idx_(\d+)', filename)
        if match:
            return f"idx_{match.group(1)}"
        # Fallback to filename without extension
        return Path(filename).stem

    def compute_file_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of file"""
        try:
            md5 = hashlib.md5()
            with open(filepath, 'rb') as f:
                md5.update(f.read())
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {filepath}: {e}")
            return ""

    def load_product_json(self, filepath: Path) -> Dict:
        """Load and parse product JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return {}

    def scan_organized_products(self):
        """Scan organized products folder"""
        logger.info("📂 Scanning organized products...")

        categories = ["Bottle", "CapPump", "Jar"]
        for category in categories:
            products_dir = ORGANIZED_DIR / category / "products"
            if not products_dir.exists():
                logger.warning(f"Category {category} not found")
                continue

            for json_file in products_dir.glob("*.json"):
                try:
                    product_id = self.extract_product_id(json_file.name)
                    product_data = self.load_product_json(json_file)

                    if not product_data:
                        continue

                    metadata = ProductMetadata(
                        product_id=product_id,
                        product_name=product_data.get("product_name", "UNKNOWN"),
                        category=category,
                        source="organized",
                        file_path=str(json_file),
                        hash_md5=self.compute_file_hash(json_file)
                    )
                    self.organized_products[product_id] = metadata
                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")

        logger.info(f"✅ Found {len(self.organized_products)} products in organized")

    def scan_updated_products(self):
        """Scan updated products folder"""
        logger.info("📂 Scanning updated products...")

        # Updated has flat structure with idx_*.json at root
        for json_file in UPDATED_DIR.glob("idx_*.json"):
            try:
                product_id = self.extract_product_id(json_file.name)
                product_data = self.load_product_json(json_file)

                if not product_data:
                    continue

                metadata = ProductMetadata(
                    product_id=product_id,
                    product_name=product_data.get("product_name", "UNKNOWN"),
                    category=product_data.get("category", "UNKNOWN"),
                    source="updated",
                    file_path=str(json_file),
                    hash_md5=self.compute_file_hash(json_file)
                )
                self.updated_products[product_id] = metadata
            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")

        logger.info(f"✅ Found {len(self.updated_products)} products in updated")

    def analyze_missing_products(self):
        """Analyze 72 missing products"""
        logger.info("🔍 Analyzing missing products...")

        organized_ids = set(self.organized_products.keys())
        updated_ids = set(self.updated_products.keys())

        missing_ids = organized_ids - updated_ids
        logger.info(f"📊 Missing: {len(missing_ids)} products")

        for product_id in missing_ids:
            self.missing_products.append(self.organized_products[product_id])

        # Analyze by category
        missing_by_category = defaultdict(int)
        for product in self.missing_products:
            missing_by_category[product.category] += 1

        logger.info(f"📈 Missing by category:")
        for category, count in sorted(missing_by_category.items()):
            logger.info(f"  - {category}: {count}")

        return missing_ids

    def find_fuzzy_duplicates(self, threshold: float = 0.85) -> List[Tuple[str, str, float]]:
        """Find fuzzy duplicates by name similarity"""
        logger.info(f"🔎 Finding fuzzy duplicates (threshold: {threshold})...")

        all_products = list(self.organized_products.values())
        duplicates = []

        for i, prod1 in enumerate(all_products):
            for prod2 in all_products[i+1:]:
                # Compare product names
                similarity = difflib.SequenceMatcher(
                    None,
                    prod1.product_name.lower(),
                    prod2.product_name.lower()
                ).ratio()

                if similarity >= threshold and prod1.product_id != prod2.product_id:
                    duplicates.append((prod1.product_id, prod2.product_id, similarity))

        logger.info(f"✅ Found {len(duplicates)} fuzzy duplicate candidates")
        return duplicates

    def save_reconciliation_report(self):
        """Save reconciliation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_organized": len(self.organized_products),
                "total_updated": len(self.updated_products),
                "missing_count": len(self.missing_products),
                "duplicate_count": len(self.duplicate_candidates)
            },
            "missing_products": [p.to_dict() for p in self.missing_products],
            "analysis": {
                "missing_by_category": {
                    "Bottle": sum(1 for p in self.missing_products if p.category == "Bottle"),
                    "CapPump": sum(1 for p in self.missing_products if p.category == "CapPump"),
                    "Jar": sum(1 for p in self.missing_products if p.category == "Jar")
                }
            }
        }

        output_file = RECONCILIATION_DIR / "missing_products.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Reconciliation report saved to {output_file}")
        return report

    def run_analysis(self):
        """Run complete analysis"""
        logger.info("🚀 Starting Phase 1 Data Reconciliation Analysis...")

        self.scan_organized_products()
        self.scan_updated_products()
        self.analyze_missing_products()
        self.find_fuzzy_duplicates()
        report = self.save_reconciliation_report()

        logger.info("✅ Phase 1 Analysis Complete!")
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Data Reconciliation & Cleanup"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run reconciliation analysis"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    reconciliation = DataReconciliation()

    if args.analyze:
        report = reconciliation.run_analysis()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
