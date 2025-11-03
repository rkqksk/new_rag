#!/usr/bin/env python3
"""
Analyze category distribution in Phase 2 output
Shows breakdown by category type and subcategory
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'
INPUT_FILE = BASE_PATH / 'all_product_urls.jsonl'

def load_classification():
    """Load category classification rules"""
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_category(category_id: int, classification: dict) -> str:
    """Get category type for a category ID"""
    for cat_type, config in classification['category_types'].items():
        if category_id in config['category_ids']:
            return cat_type
    return 'other'

def get_packaging_subcategory(category_id: int, classification: dict) -> str:
    """Get packaging subcategory name"""
    for subcat_name, cat_ids in classification['packaging_subcategories'].items():
        if category_id in cat_ids:
            return subcat_name
    return 'unknown'

def main():
    print("="*80)
    print("📊 CATEGORY DISTRIBUTION ANALYSIS")
    print("="*80)
    print()

    # Load classification
    classification = load_classification()

    # Count products by category
    category_counts = Counter()
    type_counts = defaultdict(int)
    packaging_subcat_counts = defaultdict(int)

    print("📥 Loading product URLs...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            cat_id = data['category_id']
            category_counts[cat_id] += 1

            # Classify
            cat_type = classify_category(cat_id, classification)
            type_counts[cat_type] += 1

            if cat_type == 'packaging':
                subcat = get_packaging_subcategory(cat_id, classification)
                packaging_subcat_counts[subcat] += 1

    total_products = sum(category_counts.values())

    print(f"✅ Analyzed {total_products:,} products\n")

    # Summary by type
    print("="*80)
    print("📦 CATEGORY TYPE BREAKDOWN")
    print("="*80)
    print()

    for cat_type in ['packaging', 'oem_odm', 'design', 'marketing', 'other']:
        count = type_counts[cat_type]
        percentage = count / total_products * 100
        config = classification['category_types'].get(cat_type, {})
        download = "✅ YES" if config.get('download_images', False) else "❌ NO"

        print(f"🏷️  {cat_type.upper()}")
        print(f"   Products: {count:,} ({percentage:.2f}%)")
        print(f"   Download Images: {download}")
        print(f"   Priority: {config.get('priority', 'N/A').upper()}")
        print()

    # Packaging subcategories
    if packaging_subcat_counts:
        print("="*80)
        print("🎁 PACKAGING SUBCATEGORY BREAKDOWN")
        print("="*80)
        print()

        for subcat, count in sorted(packaging_subcat_counts.items(), key=lambda x: -x[1]):
            percentage = count / type_counts['packaging'] * 100
            print(f"   {subcat:25s}: {count:8,} products ({percentage:5.2f}%)")

    # Storage estimates
    print()
    print("="*80)
    print("💾 STORAGE ESTIMATES")
    print("="*80)
    print()

    packaging_count = type_counts['packaging']

    print("📊 Phase 2 (Text Only):")
    print(f"   Total products: {total_products:,}")
    print(f"   Storage per product: ~1 KB")
    print(f"   Total storage: ~{total_products / 1000:.1f} MB (~{total_products / 1000000:.2f} GB)")
    print()

    print("📸 Phase 4 (Images - Packaging Only):")
    print(f"   Packaging products: {packaging_count:,}")
    print(f"   Images per product: 3 max")
    print(f"   Storage per image: ~100 KB")
    print(f"   Total storage: ~{packaging_count * 3 * 100 / 1000000:.1f} GB")
    print()

    print("💡 Recommendations:")
    if packaging_count * 3 * 100 / 1000000 > 100:
        print("   ⚠️  WARNING: Estimated image storage exceeds 100GB limit!")
        print("   Option 1: Download 1 image per product (reduces to ~{:.1f} GB)".format(
            packaging_count * 1 * 100 / 1000000))
        print("   Option 2: Select specific subcategories only")
        print("   Option 3: Prioritize top subcategories first")
    else:
        print("   ✅ Storage within 100GB limit for 3 images per product")

    # Top categories
    print()
    print("="*80)
    print("📈 TOP 20 CATEGORIES BY PRODUCT COUNT")
    print("="*80)
    print()

    for cat_id, count in category_counts.most_common(20):
        cat_type = classify_category(cat_id, classification)
        percentage = count / total_products * 100
        subcat = ""
        if cat_type == 'packaging':
            subcat = f" ({get_packaging_subcategory(cat_id, classification)})"
        print(f"   Category {cat_id:3d} [{cat_type:10s}]{subcat:25s}: {count:8,} ({percentage:5.2f}%)")

    print()
    print("="*80)

if __name__ == "__main__":
    main()
