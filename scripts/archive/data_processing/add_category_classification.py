#!/usr/bin/env python3
"""
Post-process Phase 2 output to add category classification
Adds category_type, priority, and download_images fields
"""

import json
from pathlib import Path
from datetime import datetime
import logging
import sys

# Setup logging
log_file = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs') / f'category_classification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
INPUT_DIR = BASE_PATH / 'products_text_only'
OUTPUT_DIR = BASE_PATH / 'products_classified'
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_classification():
    """Load category classification rules"""
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_category(category_id: int, classification: dict) -> dict:
    """Classify a category ID"""
    for cat_type, config in classification['category_types'].items():
        if category_id in config['category_ids']:
            return {
                'category_type': cat_type,
                'category_description': config['description'],
                'priority': config['priority'],
                'download_images': config['download_images'],
                'remarks': config['remarks']
            }

    # Default to "other" if not found
    return {
        'category_type': 'other',
        'category_description': 'Uncategorized - needs review',
        'priority': 'low',
        'download_images': False,
        'remarks': f'Category {category_id} - manual review needed'
    }

def get_packaging_subcategory(category_id: int, classification: dict) -> str:
    """Get packaging subcategory name"""
    for subcat_name, cat_ids in classification['packaging_subcategories'].items():
        if category_id in cat_ids:
            return subcat_name
    return 'unknown'

def main():
    logger.info("="*80)
    logger.info("🏷️  CATEGORY CLASSIFICATION POST-PROCESSOR")
    logger.info("="*80)

    # Load classification rules
    logger.info(f"📥 Loading classification rules from {CLASSIFICATION_FILE}")
    classification = load_classification()

    # Find all batch files
    batch_files = sorted(INPUT_DIR.glob('batch_*.jsonl'))
    logger.info(f"📂 Found {len(batch_files)} batch files to process")

    if not batch_files:
        logger.warning("⚠️  No batch files found! Phase 2 may not be complete yet.")
        return False

    total_products = 0
    packaging_count = 0
    service_count = 0
    other_count = 0

    # Process each batch file
    for batch_file in batch_files:
        logger.info(f"🔄 Processing {batch_file.name}")

        output_file = OUTPUT_DIR / batch_file.name
        classified_products = []

        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                product = json.loads(line)
                category_id = product.get('category_id')

                if category_id:
                    # Add classification
                    classification_info = classify_category(category_id, classification)
                    product.update(classification_info)

                    # Add packaging subcategory if applicable
                    if classification_info['category_type'] == 'packaging':
                        product['packaging_subcategory'] = get_packaging_subcategory(category_id, classification)
                        packaging_count += 1
                    elif classification_info['category_type'] in ['oem_odm', 'design', 'marketing']:
                        service_count += 1
                    else:
                        other_count += 1

                classified_products.append(product)
                total_products += 1

        # Save classified batch
        with open(output_file, 'w', encoding='utf-8') as f:
            for product in classified_products:
                f.write(json.dumps(product, ensure_ascii=False) + '\n')

        logger.info(f"✅ Saved {len(classified_products)} classified products to {output_file.name}")

    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ CLASSIFICATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Total products: {total_products:,}")
    logger.info(f"  Packaging products: {packaging_count:,} ({packaging_count/total_products*100:.1f}%) - HIGH PRIORITY")
    logger.info(f"  Service products: {service_count:,} ({service_count/total_products*100:.1f}%) - SKIP IMAGES")
    logger.info(f"  Other products: {other_count:,} ({other_count/total_products*100:.1f}%) - NEEDS REVIEW")
    logger.info(f"  Output directory: {OUTPUT_DIR}")
    logger.info(f"  Batch files: {len(batch_files)}")
    logger.info(f"{'='*80}")

    # Create summary file
    summary_file = OUTPUT_DIR / 'classification_summary.json'
    summary = {
        'total_products': total_products,
        'packaging_count': packaging_count,
        'service_count': service_count,
        'other_count': other_count,
        'packaging_percentage': round(packaging_count/total_products*100, 2),
        'processed_at': datetime.now().isoformat(),
        'batch_count': len(batch_files)
    }

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"\n📄 Summary saved to: {summary_file}")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
