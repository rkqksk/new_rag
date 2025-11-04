#!/usr/bin/env python3
"""
Analyze Crawled Freemold Data

Provides comprehensive analysis of crawled product data:
- Product count by category
- Company statistics
- Data quality checks
- Storage usage
- Export to CSV
"""

import json
from pathlib import Path
from collections import Counter
import csv

def analyze_data():
    """Analyze all crawled data"""

    data_dir = Path('data/freemold/crawled_products')

    print("=" * 70)
    print("FREEMOLD CRAWLED DATA ANALYSIS")
    print("=" * 70)

    categories = ['B001', 'B002', 'B003', 'B004']
    category_names = {
        'B001': '다이렉트 브로우 (Direct Blow)',
        'B002': '인젝션 브로우 (Injection Blow)',
        'B003': '헤비 브로우 (Heavy Blow)',
        'B004': '다층 브로우 (Multi-layer Blow)',
    }

    all_stats = {}
    total_products = 0
    all_companies = set()

    for category in categories:
        json_file = data_dir / category / f"{category}_products.json"

        if not json_file.exists():
            print(f"\n❌ {category}: No data file found")
            continue

        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # Basic stats
        product_count = len(products)
        total_products += product_count

        # Company stats
        companies = [p['mIdx'] for p in products if p['mIdx'] != 'unknown']
        unique_companies = set(companies)
        all_companies.update(unique_companies)
        company_counts = Counter(companies)
        top_companies = company_counts.most_common(5)

        # Product ID stats
        product_ids = [p['pIdx'] for p in products]
        unique_products = len(set(product_ids))
        duplicates = product_count - unique_products

        # Storage
        file_size = json_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        stats = {
            'category': category,
            'name': category_names[category],
            'products': product_count,
            'unique_products': unique_products,
            'duplicates': duplicates,
            'companies': len(unique_companies),
            'top_companies': top_companies,
            'file_size_mb': file_size_mb,
        }

        all_stats[category] = stats

        # Print category stats
        print(f"\n📦 {category}: {category_names[category]}")
        print(f"   Products: {product_count:,} ({unique_products:,} unique, {duplicates} duplicates)")
        print(f"   Companies: {len(unique_companies):,}")
        print(f"   File size: {file_size_mb:.2f} MB")
        print(f"   Top 5 companies:")
        for (mIdx, count) in top_companies:
            print(f"      - Company {mIdx}: {count} products")

    # Overall stats
    print(f"\n{'='*70}")
    print("OVERALL STATISTICS")
    print(f"{'='*70}")
    print(f"Total products: {total_products:,}")
    print(f"Total companies: {len(all_companies):,}")
    print(f"Average products per company: {total_products / len(all_companies):.1f}")

    total_size = sum(s['file_size_mb'] for s in all_stats.values())
    print(f"Total storage: {total_size:.2f} MB")

    # Data quality checks
    print(f"\n{'='*70}")
    print("DATA QUALITY CHECKS")
    print(f"{'='*70}")

    for category, stats in all_stats.items():
        print(f"\n{category}:")

        # Check for issues
        if stats['duplicates'] > 0:
            print(f"   ⚠️ {stats['duplicates']} duplicate products found")
        else:
            print(f"   ✅ No duplicates")

        # Load and check data structure
        json_file = data_dir / category / f"{category}_products.json"
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # Check required fields
        required_fields = ['pIdx', 'mIdx', 'category_code', 'product_url', 'company_url', 'crawled_at']
        missing_fields = {}

        for product in products:
            for field in required_fields:
                if field not in product or not product[field]:
                    missing_fields[field] = missing_fields.get(field, 0) + 1

        if missing_fields:
            print(f"   ⚠️ Missing/empty fields:")
            for field, count in missing_fields.items():
                print(f"      - {field}: {count} products")
        else:
            print(f"   ✅ All fields present")

    # Export to CSV
    print(f"\n{'='*70}")
    print("EXPORTING TO CSV")
    print(f"{'='*70}")

    for category in categories:
        json_file = data_dir / category / f"{category}_products.json"
        if not json_file.exists():
            continue

        csv_file = data_dir / category / f"{category}_products.csv"

        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        if products:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)

            csv_size = csv_file.stat().st_size / (1024 * 1024)
            print(f"   ✅ {category}: {csv_file} ({csv_size:.2f} MB)")

    # Sample products
    print(f"\n{'='*70}")
    print("SAMPLE PRODUCTS (First 3 from each category)")
    print(f"{'='*70}")

    for category in categories:
        json_file = data_dir / category / f"{category}_products.json"
        if not json_file.exists():
            continue

        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"\n{category}:")
        for i, product in enumerate(products[:3]):
            print(f"   {i+1}. pIdx={product['pIdx']}, mIdx={product['mIdx']}")
            print(f"      URL: {product['product_url']}")

    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")

    return all_stats

if __name__ == '__main__':
    analyze_data()
