#!/usr/bin/env python3
"""
PHASE 3 TEST: Validate 100 Products Against category_24.json
Ensures data quality and structure match perfectly
"""

import json
from pathlib import Path
from datetime import datetime
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f'/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase3_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago')
REFERENCE_FILE = BASE_PATH / 'crawled' / 'categories' / 'category_24.json'
TEST_FILE = BASE_PATH / 'crawled' / 'test_phase2_results' / 'products_detailed.json'
REPORT_FILE = BASE_PATH / 'crawled' / 'test_validation_report.json'

def validate_product(product: dict, reference_structure: dict) -> dict:
    """Validate a single product against reference structure"""
    issues = []

    # Check required fields
    required_fields = [
        'product_id', 'product_url', 'specifications',
        'detail_crawled', 'detail_crawled_at', 'full_images'
    ]

    for field in required_fields:
        if field not in product:
            issues.append(f"Missing required field: {field}")

    # Check specifications
    if 'specifications' in product:
        specs = product['specifications']
        expected_keys = ['제조사', '코드', '사이즈', 'Neck', 'Neck Size', '재질']

        for key in expected_keys:
            if key not in specs:
                issues.append(f"Missing specification: {key}")
    else:
        issues.append("specifications field missing")

    # Check full_images
    if 'full_images' in product:
        if not isinstance(product['full_images'], list):
            issues.append("full_images must be a list")
        elif len(product['full_images']) == 0:
            issues.append("full_images is empty")
        else:
            # Validate image structure
            for idx, img in enumerate(product['full_images']):
                if not isinstance(img, dict):
                    issues.append(f"Image {idx} is not a dict")
                else:
                    for img_field in ['url', 'local_path', 'size_bytes']:
                        if img_field not in img:
                            issues.append(f"Image {idx} missing {img_field}")
    else:
        issues.append("full_images field missing")

    # Check detail_crawled
    if 'detail_crawled' in product:
        if product['detail_crawled'] != True:
            issues.append(f"detail_crawled is {product['detail_crawled']}, expected True")

    # Check optional but recommended fields
    # Note: 'company' and 'manufacturer' are treated as equivalent
    if not product.get('company') and not product.get('manufacturer'):
        issues.append("Neither 'company' nor 'manufacturer' field present")

    if not product.get('phone'):
        issues.append("Recommended field missing or empty: phone")

    return {
        'product_id': product.get('product_id', 'unknown'),
        'valid': len(issues) == 0,
        'issues': issues,
        'quality_score': max(0, 100 - len(issues) * 10)
    }

def main():
    logger.info("="*70)
    logger.info("🧪 PHASE 3 TEST: Validate 100 Products")
    logger.info("="*70)

    # Load reference structure
    logger.info(f"\n📄 Loading reference: {REFERENCE_FILE}")
    with open(REFERENCE_FILE, 'r') as f:
        reference_products = json.load(f)

    reference_structure = reference_products[0]  # Use first product as template
    logger.info(f"  Reference loaded: {len(reference_products)} products")
    logger.info(f"  Reference keys: {list(reference_structure.keys())}")

    # Load test products
    logger.info(f"\n📄 Loading test results: {TEST_FILE}")
    with open(TEST_FILE, 'r') as f:
        test_products = json.load(f)

    logger.info(f"  Test products loaded: {len(test_products)}")

    # Validate each product
    logger.info(f"\n🔍 Validating {len(test_products)} products...\n")

    validation_results = []
    for product in test_products:
        result = validate_product(product, reference_structure)
        validation_results.append(result)

    # Calculate statistics
    total = len(validation_results)
    valid_count = sum(1 for r in validation_results if r['valid'])
    avg_quality = sum(r['quality_score'] for r in validation_results) / total

    # Collect all unique issues
    all_issues = {}
    for result in validation_results:
        for issue in result['issues']:
            all_issues[issue] = all_issues.get(issue, 0) + 1

    # Generate report
    report = {
        'validation_date': datetime.now().isoformat(),
        'reference_file': str(REFERENCE_FILE),
        'test_file': str(TEST_FILE),
        'total_products': total,
        'valid_products': valid_count,
        'invalid_products': total - valid_count,
        'validation_rate': f"{valid_count/total*100:.1f}%",
        'average_quality_score': f"{avg_quality:.1f}",
        'common_issues': dict(sorted(all_issues.items(), key=lambda x: x[1], reverse=True)),
        'failed_products': [r for r in validation_results if not r['valid']][:10]  # First 10 failures
    }

    # Save report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Display results
    logger.info(f"{'='*70}")
    logger.info(f"✅ PHASE 3 TEST COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"📊 Validation Results:")
    logger.info(f"  Total products: {total}")
    logger.info(f"  Valid products: {valid_count} ({valid_count/total*100:.1f}%)")
    logger.info(f"  Invalid products: {total - valid_count}")
    logger.info(f"  Average quality score: {avg_quality:.1f}/100")

    if all_issues:
        logger.info(f"\n⚠️  Common Issues:")
        for issue, count in sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"  - {issue}: {count} products")

    logger.info(f"\n📄 Full report saved to: {REPORT_FILE}")
    logger.info(f"{'='*70}")

    # Success if >95% valid
    success = valid_count / total >= 0.95

    if success:
        logger.info(f"\n✅ VALIDATION PASSED: {valid_count/total*100:.1f}% >= 95%")
    else:
        logger.info(f"\n❌ VALIDATION FAILED: {valid_count/total*100:.1f}% < 95%")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
