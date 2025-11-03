#!/usr/bin/env python3
"""
Investigate Packaging Data Inconsistency

Resolves the mystery of why packaging_product_urls.jsonl has far fewer products
than packaging_extracted.jsonl.
"""

import json
from pathlib import Path
from collections import Counter

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'
PHASE1_URL_FILE = BASE_PATH / 'all_product_urls.jsonl'
PACKAGING_URLS_FILE = BASE_PATH / 'packaging_product_urls.jsonl'
PACKAGING_EXTRACTED_FILE = BASE_PATH / 'packaging_extracted.jsonl'
TEXT_ONLY_DIR = BASE_PATH / 'products_text_only'

def load_classification():
    """Load category classification"""
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_packaging(category_id: int, classification: dict) -> bool:
    """Check if category_id is packaging"""
    return category_id in classification['category_types']['packaging']['category_ids']

print("=" * 80)
print("🔍 PACKAGING DATA INCONSISTENCY INVESTIGATION")
print("=" * 80)
print()

# Load classification
classification = load_classification()
packaging_cat_ids = set(classification['category_types']['packaging']['category_ids'])
print(f"📦 Packaging category IDs: {len(packaging_cat_ids)} categories")
print(f"   Range: {min(packaging_cat_ids)} to {max(packaging_cat_ids)}")
print()

# 1. Check Phase 1 URL list
print("1️⃣ Analyzing Phase 1 URL list (all_product_urls.jsonl)...")
phase1_total = 0
phase1_packaging = 0
phase1_packaging_ids = set()

with open(PHASE1_URL_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        phase1_total += 1
        data = json.loads(line)
        cat_id = data['category_id']

        if is_packaging(cat_id, classification):
            phase1_packaging += 1
            phase1_packaging_ids.add(data['product_id'])

        if phase1_total % 500000 == 0:
            print(f"   Processed {phase1_total:,} URLs... (found {phase1_packaging:,} packaging so far)")

print(f"✅ Phase 1 Complete:")
print(f"   Total URLs: {phase1_total:,}")
print(f"   Packaging URLs: {phase1_packaging:,} ({phase1_packaging/phase1_total*100:.2f}%)")
print()

# 2. Check packaging_product_urls.jsonl
print("2️⃣ Analyzing packaging_product_urls.jsonl...")
packaging_urls_count = 0
packaging_urls_ids = set()

with open(PACKAGING_URLS_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        packaging_urls_count += 1
        data = json.loads(line)
        packaging_urls_ids.add(data['product_id'])

print(f"✅ Packaging URLs file:")
print(f"   Total products: {packaging_urls_count:,}")
print()

# 3. Check packaging_extracted.jsonl
print("3️⃣ Analyzing packaging_extracted.jsonl...")
extracted_count = 0
extracted_ids = set()
extracted_categories = Counter()

with open(PACKAGING_EXTRACTED_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        extracted_count += 1
        data = json.loads(line)
        extracted_ids.add(data['product_id'])
        extracted_categories[data['category_id']] += 1

        if extracted_count % 100000 == 0:
            print(f"   Processed {extracted_count:,} extracted products...")

print(f"✅ Packaging extracted file:")
print(f"   Total products: {extracted_count:,}")
print(f"   Unique categories: {len(extracted_categories)}")
print()

# 4. Check products_text_only directory
print("4️⃣ Analyzing products_text_only directory...")
text_only_total = 0
text_only_packaging = 0
text_only_packaging_ids = set()

all_files = sorted(TEXT_ONLY_DIR.glob('batch_*.jsonl')) + \
            sorted(TEXT_ONLY_DIR.glob('worker_*_output.jsonl'))

print(f"   Found {len(all_files)} files to scan")

for file_idx, file in enumerate(all_files, 1):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                text_only_total += 1
                try:
                    data = json.loads(line)
                    cat_id = data.get('category_id')

                    if cat_id and is_packaging(cat_id, classification):
                        text_only_packaging += 1
                        text_only_packaging_ids.add(data['product_id'])

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"⚠️  Error reading {file.name}: {e}")
        continue

    if file_idx % 50 == 0:
        print(f"   Scanned {file_idx}/{len(all_files)} files... ({text_only_packaging:,} packaging found)")

print(f"✅ Products text_only directory:")
print(f"   Total products: {text_only_total:,}")
print(f"   Packaging products: {text_only_packaging:,} ({text_only_packaging/text_only_total*100:.2f}%)")
print()

# 5. Data consistency analysis
print("=" * 80)
print("📊 DATA CONSISTENCY ANALYSIS")
print("=" * 80)
print()

print("🔍 Comparing product ID sets:")
print(f"   Phase 1 packaging IDs:       {len(phase1_packaging_ids):,}")
print(f"   packaging_urls.jsonl IDs:    {len(packaging_urls_ids):,}")
print(f"   packaging_extracted.jsonl:   {len(extracted_ids):,}")
print(f"   text_only packaging IDs:     {len(text_only_packaging_ids):,}")
print()

# Check overlap
urls_in_phase1 = packaging_urls_ids & phase1_packaging_ids
extracted_in_phase1 = extracted_ids & phase1_packaging_ids
extracted_in_urls = extracted_ids & packaging_urls_ids

print("🔗 Overlap Analysis:")
print(f"   packaging_urls ∩ phase1:     {len(urls_in_phase1):,} ({len(urls_in_phase1)/len(packaging_urls_ids)*100:.1f}%)")
print(f"   extracted ∩ phase1:          {len(extracted_in_phase1):,} ({len(extracted_in_phase1)/len(extracted_ids)*100:.1f}%)")
print(f"   extracted ∩ packaging_urls:  {len(extracted_in_urls):,} ({len(extracted_in_urls)/len(extracted_ids)*100:.1f}%)")
print()

# Find products NOT in Phase 1
not_in_phase1 = extracted_ids - phase1_packaging_ids
if not_in_phase1:
    print(f"⚠️  CRITICAL: {len(not_in_phase1):,} extracted products are NOT in Phase 1 URL list!")
    print(f"   This means they came from somewhere else (batch files, worker outputs, etc.)")
    print()

# Conclusion
print("=" * 80)
print("💡 ROOT CAUSE ANALYSIS")
print("=" * 80)
print()

if len(extracted_ids) > len(phase1_packaging_ids):
    print("🎯 PROBLEM IDENTIFIED:")
    print(f"   The extracted packaging products ({len(extracted_ids):,}) exceed")
    print(f"   Phase 1 packaging URLs ({len(phase1_packaging_ids):,})")
    print()
    print("🔍 Possible explanations:")
    print("   1. Phase 1 URL list is incomplete or was regenerated")
    print("   2. Extraction used a different/older Phase 1 URL list")
    print("   3. products_text_only folder contains data from multiple sources")
    print()
    print("✅ RECOMMENDATION:")
    print("   Use the ACTUAL extracted packaging products as the source of truth")
    print(f"   Total packaging products: {len(extracted_ids):,}")
    print()
elif len(packaging_urls_ids) < len(phase1_packaging_ids):
    print("🎯 PROBLEM IDENTIFIED:")
    print(f"   packaging_product_urls.jsonl ({len(packaging_urls_ids):,}) is incomplete!")
    print(f"   It should contain {len(phase1_packaging_ids):,} packaging products")
    print()
    print("✅ RECOMMENDATION:")
    print("   Re-run onehago_packaging_analysis.py to regenerate packaging_product_urls.jsonl")
    print()

# Calculate remaining work
remaining = phase1_packaging_ids - text_only_packaging_ids
print("=" * 80)
print("📈 REMAINING WORK CALCULATION")
print("=" * 80)
print()
print(f"🎯 Target: {len(phase1_packaging_ids):,} packaging products (from Phase 1)")
print(f"✅ Already crawled: {len(text_only_packaging_ids):,} ({len(text_only_packaging_ids)/len(phase1_packaging_ids)*100:.2f}%)")
print(f"⏳ Remaining: {len(remaining):,} ({len(remaining)/len(phase1_packaging_ids)*100:.2f}%)")
print()

print("=" * 80)
print("✅ INVESTIGATION COMPLETE")
print("=" * 80)
