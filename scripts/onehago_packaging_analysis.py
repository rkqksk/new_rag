#!/usr/bin/env python3
"""
Onehago Packaging Analysis Script

Analyzes packaging product distribution and identifies:
1. Total packaging products in Phase 1 URL list
2. Already crawled packaging products
3. Remaining packaging products to crawl
4. Estimated completion time for packaging-only extraction
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'
PHASE1_URL_FILE = BASE_PATH / 'all_product_urls.jsonl'
PHASE2_TEXT_DIR = BASE_PATH / 'products_text_only'
PACKAGING_URL_OUTPUT = BASE_PATH / 'packaging_product_urls.jsonl'

def load_classification():
    """Load category classification rules"""
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_packaging(category_id: int, classification: dict) -> bool:
    """Check if category_id is packaging"""
    return category_id in classification['category_types']['packaging']['category_ids']

def get_subcategory(category_id: int, classification: dict) -> str:
    """Get packaging subcategory name"""
    for subcat_name, cat_ids in classification['packaging_subcategories'].items():
        if category_id in cat_ids:
            return subcat_name
    return 'unknown'

def analyze_phase1_urls():
    """Analyze Phase 1 URL list for packaging products"""
    classification = load_classification()

    packaging_count = 0
    category_counts = Counter()
    subcategory_counts = defaultdict(int)
    packaging_urls = []

    print("📥 Loading Phase 1 URL list...")
    with open(PHASE1_URL_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 100000 == 0:
                print(f"   Processed {line_num:,} URLs...")

            data = json.loads(line)
            cat_id = data['category_id']

            if is_packaging(cat_id, classification):
                packaging_count += 1
                category_counts[cat_id] += 1

                subcat = get_subcategory(cat_id, classification)
                subcategory_counts[subcat] += 1

                packaging_urls.append(data)

    return packaging_count, category_counts, subcategory_counts, packaging_urls

def analyze_crawled_data():
    """Analyze already crawled products for packaging"""
    classification = load_classification()

    crawled_packaging = set()
    total_crawled = 0

    print("\n📥 Analyzing crawled products...")

    # Check all batch files and worker output files
    all_files = list(PHASE2_TEXT_DIR.glob('batch_*.jsonl')) + \
                list(PHASE2_TEXT_DIR.glob('worker_*_output.jsonl'))

    for file in all_files:
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                total_crawled += 1
                try:
                    data = json.loads(line)
                    product_id = data.get('product_id')
                    category_id = data.get('category_id')

                    if category_id and is_packaging(category_id, classification):
                        crawled_packaging.add(product_id)
                except:
                    continue

    return len(crawled_packaging), total_crawled, crawled_packaging

def save_packaging_urls(packaging_urls, output_file):
    """Save packaging URLs to separate file"""
    print(f"\n💾 Saving packaging URLs to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for url_data in packaging_urls:
            f.write(json.dumps(url_data, ensure_ascii=False) + '\n')
    print(f"✅ Saved {len(packaging_urls):,} packaging URLs")

def main():
    print("=" * 80)
    print("🎁 ONEHAGO PACKAGING PRODUCT ANALYSIS")
    print("=" * 80)
    print()

    # Analyze Phase 1 URLs
    print("🔍 Step 1: Analyzing Phase 1 URL list...")
    total_packaging, cat_counts, subcat_counts, packaging_urls = analyze_phase1_urls()

    print(f"\n✅ Phase 1 Analysis Complete:")
    print(f"   Total packaging products: {total_packaging:,}")
    print()

    # Analyze crawled data
    print("🔍 Step 2: Analyzing already crawled products...")
    crawled_packaging_count, total_crawled, crawled_packaging_ids = analyze_crawled_data()

    print(f"\n✅ Phase 2 Analysis Complete:")
    print(f"   Total crawled products: {total_crawled:,}")
    print(f"   Crawled packaging products: {crawled_packaging_count:,}")
    print(f"   Packaging coverage: {crawled_packaging_count / total_packaging * 100:.2f}%")
    print()

    # Calculate remaining
    remaining_packaging = total_packaging - crawled_packaging_count

    print("=" * 80)
    print("📊 PACKAGING EXTRACTION SUMMARY")
    print("=" * 80)
    print()
    print(f"🎯 Target: {total_packaging:,} packaging products")
    print(f"✅ Already crawled: {crawled_packaging_count:,} ({crawled_packaging_count / total_packaging * 100:.2f}%)")
    print(f"⏳ Remaining: {remaining_packaging:,} ({remaining_packaging / total_packaging * 100:.2f}%)")
    print()

    # Subcategory breakdown
    print("=" * 80)
    print("🏷️  PACKAGING SUBCATEGORY BREAKDOWN")
    print("=" * 80)
    print()
    for subcat, count in sorted(subcat_counts.items(), key=lambda x: -x[1]):
        percentage = count / total_packaging * 100
        print(f"   {subcat:25s}: {count:8,} products ({percentage:5.2f}%)")
    print()

    # Time estimation
    print("=" * 80)
    print("⏱️  TIME ESTIMATION")
    print("=" * 80)
    print()

    # Assume 8 seconds per product (conservative estimate)
    seconds_per_product = 8

    # With 12 workers
    workers_12 = 12
    time_12_hours = (remaining_packaging * seconds_per_product) / (workers_12 * 3600)

    # With 6 workers (half capacity)
    workers_6 = 6
    time_6_hours = (remaining_packaging * seconds_per_product) / (workers_6 * 3600)

    print(f"⚡ With 12 workers: {time_12_hours:.1f} hours ({time_12_hours / 24:.1f} days)")
    print(f"🔄 With 6 workers: {time_6_hours:.1f} hours ({time_6_hours / 24:.1f} days)")
    print()

    # Save packaging URLs
    save_packaging_urls(packaging_urls, PACKAGING_URL_OUTPUT)
    print()

    # Filter remaining URLs
    remaining_urls = [url for url in packaging_urls
                      if url['product_id'] not in crawled_packaging_ids]

    remaining_file = BASE_PATH / 'packaging_remaining_urls.jsonl'
    print(f"💾 Saving {len(remaining_urls):,} remaining packaging URLs...")
    with open(remaining_file, 'w', encoding='utf-8') as f:
        for url_data in remaining_urls:
            f.write(json.dumps(url_data, ensure_ascii=False) + '\n')
    print(f"✅ Saved to {remaining_file}")
    print()

    # Storage estimation
    print("=" * 80)
    print("💾 STORAGE ESTIMATION")
    print("=" * 80)
    print()

    print("📊 Text Data (Phase 2):")
    print(f"   Remaining products: {remaining_packaging:,}")
    print(f"   Storage per product: ~1 KB")
    print(f"   Total storage: ~{remaining_packaging / 1000:.1f} MB (~{remaining_packaging / 1000000:.2f} GB)")
    print()

    print("📸 Image Data (Phase 3):")
    print(f"   Packaging products: {total_packaging:,}")
    print(f"   Images per product: 3 max")
    print(f"   Storage per image: ~100 KB")
    print(f"   Total storage: ~{total_packaging * 3 * 100 / 1000000:.1f} GB")
    print()

    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print(f"📁 Output files:")
    print(f"   All packaging URLs: {PACKAGING_URL_OUTPUT}")
    print(f"   Remaining URLs: {remaining_file}")
    print()
    print(f"💡 Next steps:")
    print(f"   1. Pause current orchestrator (no data loss)")
    print(f"   2. Run packaging-only extraction using {remaining_file}")
    print(f"   3. Download images for packaging products")
    print(f"   4. Upload to RAG system")
    print(f"   5. Resume full crawl for remaining data")
    print()

if __name__ == '__main__':
    main()
