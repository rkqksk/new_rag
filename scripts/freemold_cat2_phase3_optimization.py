#!/usr/bin/env python3
"""
FREEMOLD CATEGORY 2 (A003) - PHASE 3 OPTIMIZATION & FILTERING
Filter and optimize Category 2 extracted products for RAG system

Workflow:
  Input: products_text_a003_complete.jsonl (all extracted A003 products)
  Process:
    1. Filter by category (A003 only)
    2. Validate and select best images
    3. Optimize data for RAG/search
  Output:
    - A003.jsonl (optimized category 2 dataset)
    - a003_summary.json (statistics)

Features:
  - Category-based filtering
  - Image quality validation
  - Data optimization for search
  - Category statistics
  - Batch processing
"""

import json
from pathlib import Path
from collections import defaultdict
import logging
from datetime import datetime

# Configuration
CATEGORY = "A003"
CATEGORY_NAME = "패키징/포장재"

INPUT_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_{CATEGORY}_complete.jsonl")
OUTPUT_DIR = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_by_category")
SUMMARY_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/{CATEGORY.lower()}_summary.json")
OUTPUT_FILE = OUTPUT_DIR / f"{CATEGORY}.jsonl"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/tmp/freemold_phase3_{CATEGORY}_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print(f"🔄 FREEMOLD CATEGORY {CATEGORY} ({CATEGORY_NAME}) - PHASE 3 OPTIMIZATION")
print("="*80)
print(f"Input: {INPUT_FILE}")
print(f"Output: {OUTPUT_FILE}")
print(f"Summary: {SUMMARY_FILE}")
print("="*80 + "\n")

def validate_images(images):
    """Validate and filter image list"""
    if not isinstance(images, list):
        return []

    valid_images = []
    for img in images:
        if isinstance(img, str) and img.startswith('http'):
            # Check for valid image extension
            if any(ext in img.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                valid_images.append(img)

    return valid_images[:5]  # Return top 5 images

def select_best_images(product):
    """Select and optimize images for product"""
    images = product.get('images', [])

    # Validate and filter
    valid_images = validate_images(images)

    # Prioritize actual product images (not site logos/navigation)
    product_images = []
    nav_images = []

    for img in valid_images:
        # Check if likely product image
        if any(term in img.lower() for term in ['product', 'data/', 'item', 'goods']):
            product_images.append(img)
        else:
            nav_images.append(img)

    # Return product images first, then navigation images if needed
    selected = product_images + nav_images
    return selected[:3]  # Limit to 3 best images

def optimize_product_for_rag(product):
    """Optimize product data for RAG system"""
    optimized = {
        'product_id': product.get('product_id'),
        'category': product.get('category'),
        'category_name': product.get('category_name'),
        'url': product.get('url'),
        'name': product.get('name'),
        'description': product.get('description'),
        'specs': product.get('specs', {}),
        'contact': product.get('contact', {}),
        'images': select_best_images(product),  # Optimized image selection
        'extracted_at': product.get('extracted_at'),
        'extraction_success': product.get('extraction_success', True),
    }

    # Ensure contact info is clean
    if isinstance(optimized['contact'], dict):
        optimized['contact'] = {k: v for k, v in optimized['contact'].items() if v}

    # Ensure specs is dict
    if not isinstance(optimized['specs'], dict):
        optimized['specs'] = {}

    return optimized

def main():
    """Main processing"""

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Statistics
    stats = {
        'total_products': 0,
        'successful': 0,
        'failed': 0,
        'with_images': 0,
        'with_contact': 0,
        'with_specs': 0,
        'processing_time': None,
    }

    logger.info(f"Processing products from {INPUT_FILE}...")

    start_time = datetime.now()

    try:
        # Check if input file exists
        if not INPUT_FILE.exists():
            logger.warning(f"⚠️  Input file not found: {INPUT_FILE}")
            logger.info("This is expected if Phase 2 extraction hasn't started yet.")
            logger.info("Run Phase 2 extraction first: freemold_cat2_phase2_extraction.py")
            return

        # Process input file
        with open(INPUT_FILE, 'r', encoding='utf-8') as infile:
            # Open output file
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:

                for line_num, line in enumerate(infile, 1):
                    try:
                        product = json.loads(line)
                        stats['total_products'] += 1

                        # Verify category matches
                        category = product.get('category', 'unknown')
                        if category != CATEGORY:
                            logger.warning(f"Skipping line {line_num}: Wrong category {category}, expected {CATEGORY}")
                            continue

                        # Optimize product
                        optimized = optimize_product_for_rag(product)

                        # Write to output
                        outfile.write(json.dumps(optimized, ensure_ascii=False) + '\n')

                        # Update statistics
                        if optimized.get('extraction_success', True):
                            stats['successful'] += 1
                        else:
                            stats['failed'] += 1

                        if optimized.get('images'):
                            stats['with_images'] += 1

                        if optimized.get('contact'):
                            stats['with_contact'] += 1

                        if optimized.get('specs'):
                            stats['with_specs'] += 1

                        # Progress logging
                        if line_num % 500 == 0:
                            logger.info(f"Processed {line_num} products...")

                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing line {line_num}: {e}")
                        continue

        # Calculate time
        end_time = datetime.now()
        stats['processing_time'] = str(end_time - start_time)

        # Generate summary
        logger.info("\n" + "="*80)
        logger.info(f"✅ PHASE 3 OPTIMIZATION COMPLETE FOR CATEGORY {CATEGORY}")
        logger.info("="*80)
        logger.info(f"Total products processed: {stats['total_products']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"With images: {stats['with_images']}")
        logger.info(f"With contact info: {stats['with_contact']}")
        logger.info(f"With specifications: {stats['with_specs']}")
        logger.info(f"Processing time: {stats['processing_time']}")
        logger.info(f"Output file: {OUTPUT_FILE}")
        logger.info("="*80)

        # Save summary
        summary = {
            'processed_at': datetime.now().isoformat(),
            'category': CATEGORY,
            'category_name': CATEGORY_NAME,
            'total_products': stats['total_products'],
            'successful': stats['successful'],
            'failed': stats['failed'],
            'with_images': stats['with_images'],
            'with_contact': stats['with_contact'],
            'with_specs': stats['with_specs'],
            'processing_time': stats['processing_time'],
            'output_file': str(OUTPUT_FILE),
        }

        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"📈 Summary saved to: {SUMMARY_FILE}")
        logger.info("✨ Phase 3 optimization complete!")

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
