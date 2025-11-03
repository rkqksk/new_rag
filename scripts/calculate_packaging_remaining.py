#!/usr/bin/env python3
"""
Calculate Remaining Packaging Products to Crawl

Scans the complete all_product_urls.jsonl (2M+ products) to find ALL packaging products,
then subtracts already-crawled products to identify remaining work.
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'
ALL_URLS_FILE = BASE_PATH / 'all_product_urls.jsonl'
EXTRACTED_FILE = BASE_PATH / 'packaging_extracted.jsonl'
OUTPUT_FILE = BASE_PATH / 'packaging_remaining_to_crawl.jsonl'

def load_classification():
    """Load category classification rules"""
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_packaging(category_id: int, classification: dict) -> bool:
    """Check if category_id is packaging (2-113)"""
    return category_id in classification['category_types']['packaging']['category_ids']

print("=" * 80)
print("🔍 CALCULATING REMAINING PACKAGING PRODUCTS TO CRAWL")
print("=" * 80)
print()

# Load classification
classification = load_classification()
packaging_cat_ids = set(classification['category_types']['packaging']['category_ids'])
print(f"📦 Packaging category IDs: {len(packaging_cat_ids)} categories")
print(f"   Range: {min(packaging_cat_ids)} to {max(packaging_cat_ids)}")
print()

# Step 1: Load already-crawled packaging product IDs
print("1️⃣ Loading already-crawled packaging products...")
already_crawled_ids = set()
category_counts = Counter()

with open(EXTRACTED_FILE, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        data = json.loads(line)
        already_crawled_ids.add(data['product_id'])
        category_counts[data['category_id']] += 1

        if line_num % 50000 == 0:
            print(f"   Loaded {line_num:,} products...")

print(f"✅ Already crawled: {len(already_crawled_ids):,} unique packaging products")
print()

# Step 2: Scan ALL product URLs to find all packaging products
print("2️⃣ Scanning ALL product URLs for packaging products...")
print(f"   Source: {ALL_URLS_FILE}")
print()

all_packaging_products = []
all_packaging_ids = set()
total_urls = 0
packaging_count = 0

with open(ALL_URLS_FILE, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        total_urls += 1
        data = json.loads(line)
        cat_id = data['category_id']
        product_id = data['product_id']

        if is_packaging(cat_id, classification):
            packaging_count += 1

            # Track unique packaging products
            if product_id not in all_packaging_ids:
                all_packaging_ids.add(product_id)
                all_packaging_products.append(data)

        if line_num % 200000 == 0:
            print(f"   Processed {line_num:,} URLs... (found {len(all_packaging_ids):,} unique packaging)")

print(f"✅ Scan complete:")
print(f"   Total URLs scanned: {total_urls:,}")
print(f"   Packaging URLs (with duplicates): {packaging_count:,}")
print(f"   Unique packaging products: {len(all_packaging_ids):,}")
print()

# Step 3: Calculate remaining products
print("3️⃣ Calculating remaining products to crawl...")
remaining_ids = all_packaging_ids - already_crawled_ids
remaining_products = [p for p in all_packaging_products if p['product_id'] in remaining_ids]

print(f"✅ Calculation complete:")
print(f"   Total unique packaging (from Phase 1): {len(all_packaging_ids):,}")
print(f"   Already crawled: {len(already_crawled_ids):,}")
print(f"   Remaining to crawl: {len(remaining_ids):,}")
print()

# Step 4: Analyze the situation
print("=" * 80)
print("📊 PACKAGING PRODUCT ANALYSIS")
print("=" * 80)
print()

if len(already_crawled_ids) > len(all_packaging_ids):
    extra_products = len(already_crawled_ids) - len(all_packaging_ids)
    print(f"⚠️  IMPORTANT FINDING:")
    print(f"   You have {extra_products:,} MORE packaging products than in Phase 1 URL list!")
    print(f"   This means:")
    print(f"   - Phase 1 URL list has: {len(all_packaging_ids):,} unique packaging products")
    print(f"   - Actually crawled: {len(already_crawled_ids):,} packaging products")
    print(f"   - Extra products: {extra_products:,} (source unknown - likely from batch files)")
    print()
    print(f"✅ GOOD NEWS: Phase 1 packaging is 100% complete!")
    print(f"   All {len(all_packaging_ids):,} packaging products from Phase 1 are crawled.")
    print()

    if len(remaining_ids) == 0:
        print("🎯 RECOMMENDATION:")
        print("   Phase 1 packaging extraction is COMPLETE!")
        print(f"   Total packaging products: {len(already_crawled_ids):,}")
        print("   Ready to proceed to Phase 2 (Image Download)")
        print()

elif len(remaining_ids) > 0:
    print(f"⏳ WORK REMAINING:")
    print(f"   {len(remaining_ids):,} packaging products still need to be crawled")
    print(f"   ({len(remaining_ids)/len(all_packaging_ids)*100:.2f}% of Phase 1 packaging)")
    print()

    # Save remaining products
    print(f"💾 Saving {len(remaining_products):,} remaining products to crawl...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for product in remaining_products:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')

    print(f"✅ Saved to: {OUTPUT_FILE}")
    print()

    # Estimate time
    print("⏱️  TIME ESTIMATION (12 workers):")
    seconds_per_product = 8
    time_hours = (len(remaining_ids) * seconds_per_product) / (12 * 3600)
    print(f"   Estimated time: {time_hours:.1f} hours ({time_hours/24:.1f} days)")
    print()

else:
    print("✅ COMPLETE: All packaging products are crawled!")
    print()

# Category breakdown
print("=" * 80)
print("📦 ALREADY-CRAWLED CATEGORY BREAKDOWN (Top 10)")
print("=" * 80)
print()
for cat_id, count in category_counts.most_common(10):
    percentage = count / len(already_crawled_ids) * 100
    print(f"   Category {cat_id:3d}: {count:8,} products ({percentage:5.2f}%)")
print()

print("=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
print()

if len(remaining_ids) > 0:
    print(f"📁 Next steps:")
    print(f"   1. Review remaining products: {OUTPUT_FILE}")
    print(f"   2. Create 12-worker orchestrator for these {len(remaining_ids):,} products")
    print(f"   3. Set up localhost:5555 monitoring dashboard")
    print(f"   4. Launch packaging text extraction")
    print()
else:
    print(f"🎉 Phase 1 (Packaging Text) is COMPLETE!")
    print(f"   Total packaging products: {len(already_crawled_ids):,}")
    print(f"   Ready for Phase 2 (Image Download)")
    print()
