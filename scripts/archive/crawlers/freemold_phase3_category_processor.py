#!/usr/bin/env python3
"""
FREEMOLD PHASE 3 - CATEGORY PROCESSOR & IMAGE OPTIMIZER
Filter products by category and select best images
Creates category-specific datasets for RAG system

Workflow:
  Input: products_text_complete.jsonl (all extracted products)
  Process:
    1. Filter by category (A001, A003, A004, A006, A007, A008, A009)
    2. Validate and select best images
    3. Optimize data for RAG/search
  Output:
    - products_by_category/{category}.jsonl (category-specific files)
    - category_summary.json (statistics)

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
INPUT_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_complete.jsonl")
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_by_category")
SUMMARY_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/category_summary.json")

# All Freemold categories
CATEGORIES = {
    "A001": "프리몰드",           # Pre-molds
    "A003": "패키징/포장재",      # Packaging/packing materials
    "A004": "후가공/임가공",      # Post-processing/contract manufacturing
    "A006": "원료",               # Raw materials
    "A007": "인증/임상기관",      # Certification/clinical
    "A008": "금형/기계/시공",     # Molds/machinery/construction
    "A009": "디자인/마케팅",      # Design/marketing
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/freemold_phase3_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("🔄 FREEMOLD PHASE 3 - CATEGORY PROCESSOR & IMAGE OPTIMIZER")
print("="*80)
print(f"Input: {INPUT_FILE}")
print(f"Output: {OUTPUT_DIR}")
print(f"Categories: {len(CATEGORIES)}")
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
        'by_category': defaultdict(int),
        'with_images': defaultdict(int),
        'by_success': defaultdict(int),
        'processing_time': None,
    }

    # Category-specific output files
    category_files = {}
    for cat_code in CATEGORIES.keys():
        output_file = OUTPUT_DIR / f"{cat_code}.jsonl"
        category_files[cat_code] = output_file

    logger.info(f"Processing products from {INPUT_FILE}...")

    start_time = datetime.now()

    try:
        # Process input file
        with open(INPUT_FILE, 'r', encoding='utf-8') as infile:
            # Open all category output files
            outfiles = {}
            for cat_code in CATEGORIES.keys():
                outfiles[cat_code] = open(category_files[cat_code], 'w', encoding='utf-8')

            try:
                for line_num, line in enumerate(infile, 1):
                    try:
                        product = json.loads(line)
                        stats['total_products'] += 1

                        # Get category
                        category = product.get('category', 'unknown')
                        if category in CATEGORIES:
                            # Optimize product
                            optimized = optimize_product_for_rag(product)

                            # Write to category file
                            outfiles[category].write(json.dumps(optimized, ensure_ascii=False) + '\n')

                            # Update statistics
                            stats['by_category'][category] += 1
                            if optimized.get('images'):
                                stats['with_images'][category] += 1
                            if optimized.get('extraction_success', True):
                                stats['by_success']['successful'] += 1
                            else:
                                stats['by_success']['failed'] += 1

                        # Progress logging
                        if line_num % 500 == 0:
                            logger.info(f"Processed {line_num} products...")

                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing line {line_num}: {e}")
                        continue

            finally:
                # Close all output files
                for outfile in outfiles.values():
                    outfile.close()

        # Calculate time
        end_time = datetime.now()
        stats['processing_time'] = str(end_time - start_time)

        # Generate summary
        logger.info("\n" + "="*80)
        logger.info("✅ PHASE 3 PROCESSING COMPLETE")
        logger.info("="*80)
        logger.info(f"Total products processed: {stats['total_products']}")
        logger.info(f"Processing time: {stats['processing_time']}")
        logger.info()
        logger.info("📊 Products by Category:")
        logger.info("-"*80)

        for cat_code, cat_name in CATEGORIES.items():
            count = stats['by_category'].get(cat_code, 0)
            with_images = stats['with_images'].get(cat_code, 0)
            output_file = category_files[cat_code]

            if count > 0:
                image_pct = (with_images / count * 100) if count > 0 else 0
                logger.info(f"  {cat_code} ({cat_name}): {count:,} products")
                logger.info(f"    └─ With images: {with_images:,} ({image_pct:.1f}%)")
                logger.info(f"    └─ File: {output_file}")
            else:
                logger.info(f"  {cat_code} ({cat_name}): No products")

        # Save summary
        summary = {
            'processed_at': datetime.now().isoformat(),
            'total_products': stats['total_products'],
            'processing_time': stats['processing_time'],
            'categories': CATEGORIES,
            'by_category': dict(stats['by_category']),
            'with_images': dict(stats['with_images']),
            'by_success': dict(stats['by_success']),
            'output_directory': str(OUTPUT_DIR),
            'output_files': {k: str(v) for k, v in category_files.items()},
        }

        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info()
        logger.info(f"📈 Summary saved to: {SUMMARY_FILE}")
        logger.info("="*80)
        logger.info("✨ Phase 3 processing complete!")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
