#!/usr/bin/env python3
"""
Packaging Extraction Validation Script

Validates existing packaging_extracted.jsonl against cleaned packaging data
Creates benchmark datasets and quality reports

Input:
    - packaging_extracted.jsonl (old extraction - 245,804 entries with duplication)
    - cleaned/packaging_products_clean.jsonl (20,043 unique packaging products)

Output:
    - validation_report.json (comprehensive quality metrics)
    - benchmark_sample.jsonl (100 products for quality benchmarking)
    - gaps_analysis.json (missing products, incomplete extractions)
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set
import random

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
OLD_EXTRACTION = BASE_PATH / 'packaging_extracted.jsonl'
CLEANED_PACKAGING = BASE_PATH / 'cleaned' / 'packaging_products_clean.jsonl'
VALIDATION_OUTPUT_DIR = BASE_PATH / 'validation'
VALIDATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
VALIDATION_REPORT = VALIDATION_OUTPUT_DIR / 'packaging_validation_report.json'
BENCHMARK_SAMPLE = VALIDATION_OUTPUT_DIR / 'packaging_benchmark_sample.jsonl'
GAPS_ANALYSIS = VALIDATION_OUTPUT_DIR / 'packaging_gaps_analysis.json'

def load_cleaned_packaging() -> Dict[str, Dict]:
    """Load cleaned packaging products (ground truth)"""
    print("📥 Loading cleaned packaging products...")
    packaging_products = {}
    with open(CLEANED_PACKAGING, 'r', encoding='utf-8') as f:
        for line in f:
            product = json.loads(line)
            packaging_products[product['product_id']] = product
    print(f"✅ Loaded {len(packaging_products):,} unique packaging products")
    return packaging_products

def load_old_extraction() -> Dict[str, List[Dict]]:
    """Load old extraction data (may have duplicates)"""
    print("\n📥 Loading old packaging extraction...")
    extraction_data = defaultdict(list)
    total_entries = 0

    with open(OLD_EXTRACTION, 'r', encoding='utf-8') as f:
        for line in f:
            product = json.loads(line)
            product_id = product.get('product_id')
            extraction_data[product_id].append(product)
            total_entries += 1

    unique_products = len(extraction_data)
    print(f"✅ Loaded {total_entries:,} extraction entries")
    print(f"📊 Unique products: {unique_products:,}")
    print(f"📊 Duplicate rate: {(total_entries - unique_products) / total_entries * 100:.2f}%")

    return extraction_data

def validate_extraction_quality(extracted_product: Dict) -> Dict[str, any]:
    """Validate quality of a single extracted product"""
    quality = {
        'has_product_name': bool(extracted_product.get('product_name')),
        'has_specifications': bool(extracted_product.get('specifications')),
        'specs_count': len(extracted_product.get('specifications', {})),
        'has_company_info': bool(extracted_product.get('company_info')),
        'company_info_count': len(extracted_product.get('company_info', {})),
        'has_contact_details': any([
            extracted_product.get('phone'),
            extracted_product.get('fax'),
            extracted_product.get('email')
        ]),
        'has_images': bool(extracted_product.get('image_urls')),
        'image_count': len(extracted_product.get('image_urls', [])),
        'detail_crawled': extracted_product.get('detail_crawled', False),
        'completeness_score': 0.0
    }

    # Calculate completeness score (0-100)
    score = 0
    if quality['has_product_name']: score += 20
    if quality['specs_count'] > 0: score += 20
    if quality['specs_count'] >= 3: score += 10  # Bonus for multiple specs
    if quality['company_info_count'] > 0: score += 15
    if quality['has_contact_details']: score += 15
    if quality['has_images']: score += 10
    if quality['image_count'] >= 3: score += 10  # Bonus for multiple images

    quality['completeness_score'] = score

    return quality

def main():
    print("="*80)
    print("📊 PACKAGING EXTRACTION VALIDATION")
    print("="*80)
    print()

    # Load data
    cleaned_packaging = load_cleaned_packaging()
    old_extraction = load_old_extraction()

    # Validation statistics
    stats = {
        'timestamp': datetime.now().isoformat(),
        'cleaned_packaging_count': len(cleaned_packaging),
        'old_extraction_total_entries': sum(len(entries) for entries in old_extraction.values()),
        'old_extraction_unique_products': len(old_extraction),
        'duplication_analysis': {},
        'coverage_analysis': {},
        'quality_analysis': {},
        'gaps_analysis': {},
        'benchmark_info': {}
    }

    print("\n" + "="*80)
    print("🔍 DUPLICATION ANALYSIS")
    print("="*80)

    duplication_counts = Counter(len(entries) for entries in old_extraction.values())
    stats['duplication_analysis'] = {
        'products_with_1_extraction': duplication_counts.get(1, 0),
        'products_with_2_extractions': duplication_counts.get(2, 0),
        'products_with_3+_extractions': sum(count for dup_level, count in duplication_counts.items() if dup_level >= 3),
        'max_duplications': max(duplication_counts.keys()) if duplication_counts else 0,
        'total_duplicate_entries': stats['old_extraction_total_entries'] - stats['old_extraction_unique_products']
    }

    print(f"  Products with 1 extraction: {stats['duplication_analysis']['products_with_1_extraction']:,}")
    print(f"  Products with 2 extractions: {stats['duplication_analysis']['products_with_2_extractions']:,}")
    print(f"  Products with 3+ extractions: {stats['duplication_analysis']['products_with_3+_extractions']:,}")
    print(f"  Max duplications for single product: {stats['duplication_analysis']['max_duplications']}")
    print(f"  Total duplicate entries: {stats['duplication_analysis']['total_duplicate_entries']:,}")

    print("\n" + "="*80)
    print("📊 COVERAGE ANALYSIS")
    print("="*80)

    extracted_product_ids = set(old_extraction.keys())
    cleaned_product_ids = set(cleaned_packaging.keys())

    covered_products = extracted_product_ids & cleaned_product_ids
    missing_products = cleaned_product_ids - extracted_product_ids
    unexpected_products = extracted_product_ids - cleaned_product_ids

    stats['coverage_analysis'] = {
        'covered_products': len(covered_products),
        'missing_products': len(missing_products),
        'unexpected_products': len(unexpected_products),
        'coverage_rate': len(covered_products) / len(cleaned_product_ids) * 100 if cleaned_product_ids else 0
    }

    print(f"  Covered products: {len(covered_products):,} ({stats['coverage_analysis']['coverage_rate']:.2f}%)")
    print(f"  Missing products: {len(missing_products):,}")
    print(f"  Unexpected products (not in cleaned): {len(unexpected_products):,}")

    print("\n" + "="*80)
    print("✅ QUALITY ANALYSIS")
    print("="*80)

    # Analyze quality of extracted products
    quality_scores = []
    quality_distribution = defaultdict(int)

    for product_id in covered_products:
        # Use first extraction if duplicates exist
        extracted = old_extraction[product_id][0]
        quality = validate_extraction_quality(extracted)
        quality_scores.append(quality['completeness_score'])

        # Categorize quality
        if quality['completeness_score'] >= 80:
            quality_distribution['excellent'] += 1
        elif quality['completeness_score'] >= 60:
            quality_distribution['good'] += 1
        elif quality['completeness_score'] >= 40:
            quality_distribution['fair'] += 1
        else:
            quality_distribution['poor'] += 1

    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    stats['quality_analysis'] = {
        'average_completeness_score': round(avg_quality, 2),
        'excellent_quality': quality_distribution['excellent'],
        'good_quality': quality_distribution['good'],
        'fair_quality': quality_distribution['fair'],
        'poor_quality': quality_distribution['poor'],
        'total_analyzed': len(quality_scores)
    }

    print(f"  Average completeness score: {avg_quality:.2f}/100")
    print(f"  Excellent quality (80-100): {quality_distribution['excellent']:,} products")
    print(f"  Good quality (60-79): {quality_distribution['good']:,} products")
    print(f"  Fair quality (40-59): {quality_distribution['fair']:,} products")
    print(f"  Poor quality (0-39): {quality_distribution['poor']:,} products")

    print("\n" + "="*80)
    print("🔎 GAPS ANALYSIS")
    print("="*80)

    # Sample missing products for analysis
    missing_sample = random.sample(list(missing_products), min(10, len(missing_products))) if missing_products else []
    missing_details = [cleaned_packaging[pid] for pid in missing_sample]

    # Sample poor quality products
    poor_quality_products = []
    for product_id in covered_products:
        extracted = old_extraction[product_id][0]
        quality = validate_extraction_quality(extracted)
        if quality['completeness_score'] < 40:
            poor_quality_products.append({
                'product_id': product_id,
                'product_url': extracted.get('product_url'),
                'completeness_score': quality['completeness_score'],
                'quality_details': quality
            })
            if len(poor_quality_products) >= 10:
                break

    gaps = {
        'missing_products_sample': missing_details,
        'missing_products_count': len(missing_products),
        'poor_quality_products_sample': poor_quality_products,
        'poor_quality_products_count': quality_distribution['poor']
    }

    print(f"  Missing products: {len(missing_products):,}")
    print(f"  Poor quality extractions: {quality_distribution['poor']:,}")
    print(f"  Sample of missing products: {len(missing_details)} (saved to gaps_analysis.json)")
    print(f"  Sample of poor quality products: {len(poor_quality_products)} (saved to gaps_analysis.json)")

    print("\n" + "="*80)
    print("📦 BENCHMARK DATASET CREATION")
    print("="*80)

    # Create benchmark dataset - stratified sample
    benchmark_products = []

    # Select products from each quality category
    categories = [
        ('excellent', 80, 30),
        ('good', 60, 30),
        ('fair', 40, 20),
        ('poor', 0, 20)
    ]

    for category_name, min_score, sample_size in categories:
        category_products = []
        for product_id in covered_products:
            extracted = old_extraction[product_id][0]
            quality = validate_extraction_quality(extracted)
            score = quality['completeness_score']

            if category_name == 'excellent' and score >= 80:
                category_products.append((product_id, extracted, quality))
            elif category_name == 'good' and 60 <= score < 80:
                category_products.append((product_id, extracted, quality))
            elif category_name == 'fair' and 40 <= score < 60:
                category_products.append((product_id, extracted, quality))
            elif category_name == 'poor' and score < 40:
                category_products.append((product_id, extracted, quality))

        # Sample from category
        selected = random.sample(category_products, min(sample_size, len(category_products)))
        for product_id, extracted, quality in selected:
            benchmark_products.append({
                **extracted,
                'benchmark_category': category_name,
                'benchmark_quality': quality
            })

    # Save benchmark dataset
    with open(BENCHMARK_SAMPLE, 'w', encoding='utf-8') as f:
        for product in benchmark_products:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')

    stats['benchmark_info'] = {
        'benchmark_sample_size': len(benchmark_products),
        'benchmark_file': str(BENCHMARK_SAMPLE),
        'benchmark_categories': {
            'excellent': sum(1 for p in benchmark_products if p['benchmark_category'] == 'excellent'),
            'good': sum(1 for p in benchmark_products if p['benchmark_category'] == 'good'),
            'fair': sum(1 for p in benchmark_products if p['benchmark_category'] == 'fair'),
            'poor': sum(1 for p in benchmark_products if p['benchmark_category'] == 'poor')
        }
    }

    print(f"  Benchmark sample size: {len(benchmark_products)} products")
    print(f"  Excellent: {stats['benchmark_info']['benchmark_categories']['excellent']} products")
    print(f"  Good: {stats['benchmark_info']['benchmark_categories']['good']} products")
    print(f"  Fair: {stats['benchmark_info']['benchmark_categories']['fair']} products")
    print(f"  Poor: {stats['benchmark_info']['benchmark_categories']['poor']} products")
    print(f"  Saved to: {BENCHMARK_SAMPLE}")

    print("\n" + "="*80)
    print("💾 SAVING VALIDATION RESULTS")
    print("="*80)

    # Save validation report
    with open(VALIDATION_REPORT, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"✅ Validation report: {VALIDATION_REPORT}")

    # Save gaps analysis
    with open(GAPS_ANALYSIS, 'w', encoding='utf-8') as f:
        json.dump(gaps, f, indent=2, ensure_ascii=False)
    print(f"✅ Gaps analysis: {GAPS_ANALYSIS}")

    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE")
    print("="*80)
    print()
    print("📊 Summary:")
    print(f"  Coverage: {stats['coverage_analysis']['coverage_rate']:.2f}%")
    print(f"  Average quality: {stats['quality_analysis']['average_completeness_score']:.2f}/100")
    print(f"  Benchmark dataset: {len(benchmark_products)} products")
    print(f"  Duplicates removed: {stats['duplication_analysis']['total_duplicate_entries']:,} entries")
    print()
    print("📁 Output files:")
    print(f"  - {VALIDATION_REPORT} (comprehensive report)")
    print(f"  - {BENCHMARK_SAMPLE} (100 benchmark products)")
    print(f"  - {GAPS_ANALYSIS} (missing & poor quality details)")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
