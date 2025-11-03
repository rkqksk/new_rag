#!/usr/bin/env python3
"""
Phase 1 Cleanup and Organization Script

Comprehensive cleanup of Phase 1 raw data (2M+ product URLs):
- Deduplicates by product_id
- Adds category_type labels (packaging/oem_odm/design/marketing/other)
- Adds packaging_subcategory labels for packaging products
- Generates organized output files by category
- Creates comprehensive statistics report

Input:
    - all_product_urls.jsonl (2,011,553 URLs with duplication)
    - category_classification.json (category mapping rules)

Output:
    - all_products_clean.jsonl (deduplicated with labels)
    - packaging_products_clean.jsonl (packaging only)
    - non_packaging_products_clean.jsonl (non-packaging only)
    - cleanup_report.json (statistics and metadata)
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, Set, Tuple

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'
INPUT_FILE = BASE_PATH / 'all_product_urls.jsonl'
OUTPUT_DIR = BASE_PATH / 'cleaned'

# Output files
ALL_PRODUCTS_CLEAN = OUTPUT_DIR / 'all_products_clean.jsonl'
PACKAGING_CLEAN = OUTPUT_DIR / 'packaging_products_clean.jsonl'
NON_PACKAGING_CLEAN = OUTPUT_DIR / 'non_packaging_products_clean.jsonl'
CLEANUP_REPORT = OUTPUT_DIR / 'cleanup_report.json'

# Category type mapping
CATEGORY_TYPE_MAP = {}  # category_id -> category_type
PACKAGING_SUBCAT_MAP = {}  # category_id -> packaging_subcategory


def load_classification() -> Dict:
    """Load category classification rules"""
    print("📥 Loading category classification...")
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_category_maps(classification: Dict):
    """Build category_id to category_type and subcategory mappings"""
    global CATEGORY_TYPE_MAP, PACKAGING_SUBCAT_MAP

    print("🔨 Building category mapping tables...")

    # Map category_id to category_type
    for cat_type, cat_info in classification['category_types'].items():
        for cat_id in cat_info['category_ids']:
            CATEGORY_TYPE_MAP[cat_id] = cat_type

    # Map category_id to packaging_subcategory
    for subcat, cat_ids in classification['packaging_subcategories'].items():
        for cat_id in cat_ids:
            PACKAGING_SUBCAT_MAP[cat_id] = subcat

    print(f"   ✅ Mapped {len(CATEGORY_TYPE_MAP)} category IDs to category types")
    print(f"   ✅ Mapped {len(PACKAGING_SUBCAT_MAP)} category IDs to packaging subcategories")


def get_category_labels(category_id: int) -> Tuple[str, str]:
    """Get category_type and packaging_subcategory for a category_id"""
    category_type = CATEGORY_TYPE_MAP.get(category_id, 'other')
    packaging_subcategory = PACKAGING_SUBCAT_MAP.get(category_id, None) if category_type == 'packaging' else None
    return category_type, packaging_subcategory


def add_labels_to_product(product: Dict) -> Dict:
    """Add category_type and packaging_subcategory labels to product"""
    category_id = product['category_id']
    category_type, packaging_subcategory = get_category_labels(category_id)

    product['category_type'] = category_type
    if packaging_subcategory:
        product['packaging_subcategory'] = packaging_subcategory

    return product


def cleanup_and_organize():
    """Main cleanup and organization function"""
    print("=" * 80)
    print("🧹 PHASE 1 CLEANUP AND ORGANIZATION")
    print("=" * 80)
    print()

    # Load classification
    classification = load_classification()
    build_category_maps(classification)
    print()

    # Statistics tracking
    stats = {
        'total_urls_read': 0,
        'unique_products': 0,
        'duplicates_removed': 0,
        'by_category_type': defaultdict(int),
        'by_packaging_subcategory': defaultdict(int),
        'categories_found': set(),
        'processing_time_seconds': 0,
        'timestamp': datetime.now().isoformat()
    }

    # Tracking structures
    unique_products = {}  # product_id -> product_data (with labels)
    duplicate_count = 0
    category_counts = Counter()

    print(f"📂 Reading from: {INPUT_FILE}")
    print(f"📊 Total lines to process: {sum(1 for _ in open(INPUT_FILE))}")
    print()

    start_time = datetime.now()

    # Process all URLs
    print("🔄 Processing URLs and deduplicating...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            stats['total_urls_read'] += 1

            # Progress indicator
            if line_num % 100000 == 0:
                print(f"   Processed: {line_num:,} lines... ({len(unique_products):,} unique products)")

            try:
                product = json.loads(line)
                product_id = product['product_id']
                category_id = product['category_id']

                # Track categories
                stats['categories_found'].add(category_id)
                category_counts[category_id] += 1

                # Deduplication logic
                if product_id in unique_products:
                    duplicate_count += 1
                else:
                    # Add labels
                    product_with_labels = add_labels_to_product(product)
                    unique_products[product_id] = product_with_labels

                    # Update category type stats
                    category_type = product_with_labels['category_type']
                    stats['by_category_type'][category_type] += 1

                    # Update packaging subcategory stats
                    if 'packaging_subcategory' in product_with_labels:
                        packaging_subcat = product_with_labels['packaging_subcategory']
                        stats['by_packaging_subcategory'][packaging_subcat] += 1

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"   ⚠️ Error processing line {line_num}: {e}")
                continue

    # Calculate statistics
    stats['unique_products'] = len(unique_products)
    stats['duplicates_removed'] = duplicate_count
    stats['processing_time_seconds'] = (datetime.now() - start_time).total_seconds()
    stats['categories_found'] = sorted(list(stats['categories_found']))

    print()
    print(f"✅ Deduplication complete:")
    print(f"   Total URLs read: {stats['total_urls_read']:,}")
    print(f"   Duplicate entries: {stats['duplicates_removed']:,}")
    print(f"   Unique products: {stats['unique_products']:,}")
    print(f"   Deduplication rate: {(stats['duplicates_removed']/stats['total_urls_read'])*100:.2f}%")
    print()

    # Category type breakdown
    print("=" * 80)
    print("📊 BREAKDOWN BY CATEGORY TYPE")
    print("=" * 80)
    print()
    for cat_type in ['packaging', 'oem_odm', 'design', 'marketing', 'other']:
        count = stats['by_category_type'][cat_type]
        percentage = (count / stats['unique_products']) * 100 if stats['unique_products'] > 0 else 0
        print(f"   {cat_type:15s}: {count:8,} products ({percentage:5.2f}%)")
    print()

    # Packaging subcategory breakdown
    if stats['by_packaging_subcategory']:
        print("=" * 80)
        print("📦 PACKAGING SUBCATEGORY BREAKDOWN")
        print("=" * 80)
        print()
        for subcat, count in sorted(stats['by_packaging_subcategory'].items(), key=lambda x: -x[1]):
            packaging_count = stats['by_category_type']['packaging']
            percentage = (count / packaging_count) * 100 if packaging_count > 0 else 0
            print(f"   {subcat:20s}: {count:7,} products ({percentage:5.2f}%)")
        print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save organized outputs
    print("=" * 80)
    print("💾 SAVING ORGANIZED OUTPUTS")
    print("=" * 80)
    print()

    # 1. All products (deduplicated with labels)
    print(f"📝 Saving all products to: {ALL_PRODUCTS_CLEAN}")
    with open(ALL_PRODUCTS_CLEAN, 'w', encoding='utf-8') as f:
        for product in unique_products.values():
            f.write(json.dumps(product, ensure_ascii=False) + '\n')
    print(f"   ✅ Saved {len(unique_products):,} products")
    print()

    # 2. Packaging products only
    print(f"📦 Saving packaging products to: {PACKAGING_CLEAN}")
    packaging_products = [p for p in unique_products.values() if p['category_type'] == 'packaging']
    with open(PACKAGING_CLEAN, 'w', encoding='utf-8') as f:
        for product in packaging_products:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')
    print(f"   ✅ Saved {len(packaging_products):,} packaging products")
    print()

    # 3. Non-packaging products
    print(f"📄 Saving non-packaging products to: {NON_PACKAGING_CLEAN}")
    non_packaging_products = [p for p in unique_products.values() if p['category_type'] != 'packaging']
    with open(NON_PACKAGING_CLEAN, 'w', encoding='utf-8') as f:
        for product in non_packaging_products:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')
    print(f"   ✅ Saved {len(non_packaging_products):,} non-packaging products")
    print()

    # 4. Save comprehensive report
    print(f"📊 Saving cleanup report to: {CLEANUP_REPORT}")

    # Convert defaultdicts to regular dicts for JSON serialization
    report = {
        'summary': {
            'total_urls_read': stats['total_urls_read'],
            'unique_products': stats['unique_products'],
            'duplicates_removed': stats['duplicates_removed'],
            'deduplication_rate_percent': round((stats['duplicates_removed']/stats['total_urls_read'])*100, 2),
            'processing_time_seconds': round(stats['processing_time_seconds'], 2),
            'timestamp': stats['timestamp']
        },
        'by_category_type': dict(stats['by_category_type']),
        'by_packaging_subcategory': dict(stats['by_packaging_subcategory']),
        'categories_found': stats['categories_found'],
        'category_distribution': {
            cat_id: category_counts[cat_id]
            for cat_id in sorted(category_counts.keys())
        },
        'output_files': {
            'all_products_clean': str(ALL_PRODUCTS_CLEAN),
            'packaging_products_clean': str(PACKAGING_CLEAN),
            'non_packaging_products_clean': str(NON_PACKAGING_CLEAN),
            'cleanup_report': str(CLEANUP_REPORT)
        }
    }

    with open(CLEANUP_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Report saved")
    print()

    # Final summary
    print("=" * 80)
    print("✅ PHASE 1 CLEANUP COMPLETE")
    print("=" * 80)
    print()
    print(f"📊 Summary:")
    print(f"   Processed: {stats['total_urls_read']:,} URLs")
    print(f"   Unique products: {stats['unique_products']:,}")
    print(f"   Duplicates removed: {stats['duplicates_removed']:,} ({(stats['duplicates_removed']/stats['total_urls_read'])*100:.2f}%)")
    print(f"   Processing time: {stats['processing_time_seconds']:.1f} seconds")
    print()
    print(f"📁 Output directory: {OUTPUT_DIR}/")
    print(f"   ✅ all_products_clean.jsonl ({len(unique_products):,} products)")
    print(f"   ✅ packaging_products_clean.jsonl ({len(packaging_products):,} products)")
    print(f"   ✅ non_packaging_products_clean.jsonl ({len(non_packaging_products):,} products)")
    print(f"   ✅ cleanup_report.json (comprehensive statistics)")
    print()
    print("🎯 Next Steps:")
    print("   1. Review cleanup_report.json for detailed statistics")
    print("   2. Verify data quality with sample checks")
    print("   3. Use cleaned files for Phase 2 (2M+ product crawl)")
    print()


def main():
    try:
        cleanup_and_organize()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Partial cleanup may be saved.")
    except Exception as e:
        print(f"\n\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
