#!/usr/bin/env python3
"""
Phase 2: Metadata Normalization
Transforms heterogeneous metadata into normalized schema with quality scoring

Normalization Steps:
1. Field mapping from organized/updated formats to normalized schema
2. Specification field correction (contact info vs product specs)
3. Quality scoring based on completeness
4. Asset validation and hashing
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path("/Users/oypnus/Project/rag-enterprise/data")
UPDATED_DIR = DATA_DIR / "crawled_products_updated"
SOURCE_DIR = DATA_DIR / "source"
QUALITY_DIR = DATA_DIR / "quality"
VALIDATION_DIR = QUALITY_DIR / "validation"

# Ensure directories exist
QUALITY_DIR.mkdir(exist_ok=True)
VALIDATION_DIR.mkdir(exist_ok=True)


@dataclass
class NormalizedProduct:
    """Normalized product schema"""
    product_id: str
    product_name: str
    category: Dict
    description: Dict
    specifications: Dict
    assets: Dict
    contact_info: Dict
    quality_metadata: Dict

    def to_dict(self):
        return asdict(self)


class MetadataNormalizer:
    """Normalize metadata to standard schema"""

    def __init__(self):
        self.normalized_count = 0
        self.quality_scores = []
        self.schema_errors = []

    def load_product_json(self, filepath: Path) -> Dict:
        """Load product JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return {}

    def correct_specifications_field(self, product_data: Dict, source: str) -> Dict:
        """Correct misplaced specifications/contact_info fields"""
        if source == "updated":
            # In updated version, specifications may contain contact info or be a dict
            spec_content = product_data.get("specifications", "")

            # Handle both dict and string specifications
            spec_str = ""
            if isinstance(spec_content, str):
                spec_str = spec_content
            elif isinstance(spec_content, dict):
                # If it's already a dict, keep it as specs
                return product_data
            else:
                spec_str = str(spec_content)

            # Try to extract contact info from string
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', spec_str)
            phone_match = re.search(
                r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                spec_str
            )

            # Initialize contact_info if not present
            if "contact_info" not in product_data:
                product_data["contact_info"] = {}

            # Extract to contact_info
            if email_match:
                product_data["contact_info"]["email"] = email_match.group(0)
            if phone_match:
                product_data["contact_info"]["phone"] = phone_match.group(0)

            # Clear misplaced specifications if it was a contact string
            if isinstance(spec_content, str) and (email_match or phone_match):
                product_data["specifications"] = {}

        return product_data

    def normalize_product(self, product_data: Dict) -> NormalizedProduct:
        """Normalize product to standard schema"""
        product_id = product_data.get("product_id", "UNKNOWN")

        # Correct specification field if needed
        product_data = self.correct_specifications_field(product_data, "updated")

        # Build normalized product
        normalized = NormalizedProduct(
            product_id=product_id,
            product_name=product_data.get("product_name", ""),
            category={
                "primary": product_data.get("category", "UNKNOWN"),
                "subcategory": product_data.get("subcategory", ""),
                "tags": product_data.get("tags", [])
            },
            description={
                "short": (product_data.get("description", "")[:150])
                if isinstance(product_data.get("description", ""), str)
                else "",
                "long": product_data.get("description", "")
                if isinstance(product_data.get("description", ""), str)
                else ""
            },
            specifications=product_data.get("specifications", {}),
            assets={
                "images": product_data.get("images", []),
                "documents": product_data.get("documents", [])
            },
            contact_info=product_data.get("contact_info", {}),
            quality_metadata={
                "completeness_score": 0,  # Will be calculated
                "last_validated": datetime.now().isoformat(),
                "validation_status": "pending",
                "data_source": "updated",
                "last_modified": product_data.get("last_modified", datetime.now().isoformat())
            }
        )

        return normalized

    def calculate_quality_score(self, product: NormalizedProduct) -> float:
        """Calculate product quality score (0-100)"""
        score = 0.0

        # Metadata completeness (30%)
        required_fields = ["product_name", "category"]
        optional_fields = ["description", "specifications"]

        required_present = sum(1 for f in required_fields if f and getattr(product, f, None))
        metadata_score = (required_present / len(required_fields)) * 0.7
        optional_present = sum(1 for f in optional_fields if getattr(product, f, None))
        metadata_score += (optional_present / len(optional_fields)) * 0.3
        score += metadata_score * 0.30

        # Asset quality (40%)
        image_count = len(product.assets.get("images", []))
        image_score = min(image_count / 3, 1.0)  # 3 images is target
        doc_score = 0.1 if len(product.assets.get("documents", [])) > 0 else 0
        asset_score = image_score * 0.6 + doc_score * 0.4
        score += asset_score * 0.40

        # Metadata richness (30%)
        desc_length = len(product.description.get("long", ""))
        desc_score = min(desc_length / 200, 1.0)  # 200 chars is target
        spec_count = len(product.specifications) if isinstance(product.specifications, dict) else 0
        spec_score = min(spec_count / 8, 1.0)  # 8 specs is target
        contact_score = (1 if product.contact_info.get("email") else 0 +
                        1 if product.contact_info.get("phone") else 0) / 2
        richness_score = desc_score * 0.4 + spec_score * 0.4 + contact_score * 0.2
        score += richness_score * 0.30

        return score * 100

    def classify_quality_status(self, score: float) -> str:
        """Classify product quality based on score"""
        if score >= 85:
            return "premium"
        elif score >= 70:
            return "production_ready"
        elif score >= 50:
            return "mvp"
        else:
            return "incomplete"

    def normalize_all_products(self, limit: Optional[int] = None):
        """Normalize all products in updated folder"""
        logger.info("📝 Starting metadata normalization...")

        product_files = list(UPDATED_DIR.glob("idx_*.json"))
        if limit:
            product_files = product_files[:limit]

        logger.info(f"📊 Processing {len(product_files)} products...")

        for idx, product_file in enumerate(product_files):
            try:
                product_data = self.load_product_json(product_file)
                if not product_data:
                    continue

                # Normalize product
                normalized = self.normalize_product(product_data)

                # Calculate quality score
                quality_score = self.calculate_quality_score(normalized)
                normalized.quality_metadata["completeness_score"] = quality_score
                normalized.quality_metadata["validation_status"] = self.classify_quality_status(quality_score)

                self.quality_scores.append({
                    "product_id": normalized.product_id,
                    "score": quality_score,
                    "status": normalized.quality_metadata["validation_status"]
                })

                self.normalized_count += 1

                if (idx + 1) % 50 == 0:
                    logger.info(f"  Processed {idx + 1}/{len(product_files)} products...")

            except Exception as e:
                logger.error(f"Error normalizing {product_file}: {e}")
                self.schema_errors.append(str(product_file))

        logger.info(f"✅ Normalization complete! Processed {self.normalized_count} products")

    def save_quality_scores(self):
        """Save quality scores report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(self.quality_scores),
            "average_score": sum(s["score"] for s in self.quality_scores) / len(self.quality_scores)
            if self.quality_scores else 0,
            "distribution": {
                "premium": len([s for s in self.quality_scores if s["status"] == "premium"]),
                "production_ready": len([s for s in self.quality_scores if s["status"] == "production_ready"]),
                "mvp": len([s for s in self.quality_scores if s["status"] == "mvp"]),
                "incomplete": len([s for s in self.quality_scores if s["status"] == "incomplete"])
            },
            "scores": self.quality_scores
        }

        output_file = VALIDATION_DIR / "completeness_scores.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Quality scores saved to {output_file}")
        return report

    def print_quality_summary(self):
        """Print quality summary statistics"""
        if not self.quality_scores:
            logger.warning("No quality scores to summarize")
            return

        scores = [s["score"] for s in self.quality_scores]
        avg = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        logger.info("📊 Quality Score Summary:")
        logger.info(f"  Average:          {avg:.1f}")
        logger.info(f"  Min:              {min_score:.1f}")
        logger.info(f"  Max:              {max_score:.1f}")
        logger.info(f"  Production Ready: {len([s for s in self.quality_scores if s['score'] >= 70])} products")
        logger.info(f"  Below Threshold:  {len([s for s in self.quality_scores if s['score'] < 50])} products")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: Metadata Normalization"
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Run metadata normalization"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of products to process"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    normalizer = MetadataNormalizer()

    if args.normalize:
        normalizer.normalize_all_products(limit=args.limit)
        report = normalizer.save_quality_scores()
        normalizer.print_quality_summary()
        print(json.dumps(report, indent=2, ensure_ascii=False)[:2000])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
