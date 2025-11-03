#!/usr/bin/env python3
"""
Company Filter Utility for Freemold Products

Filter crawled products by company ID (mIdx) to extract company-specific data.

Usage:
    python filter_by_company.py --mIdx 481
    python filter_by_company.py --mIdx 481,493,1324
    python filter_by_company.py --list-companies
"""

import json
import csv
import argparse
from pathlib import Path
from collections import defaultdict


class CompanyFilter:
    """Filter and analyze products by company ID"""

    def __init__(self, data_dir='data/freemold/crawled_products'):
        """
        Initialize company filter

        Args:
            data_dir: Directory containing crawled product data
        """
        self.data_dir = Path(data_dir)
        self.products = []
        self.companies = defaultdict(list)

    def load_all_products(self):
        """Load all products from crawled data"""
        print("\n" + "="*70)
        print("LOADING CRAWLED PRODUCTS")
        print("="*70)

        json_files = list(self.data_dir.rglob('*.json'))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                    self.products.extend(products)
                    print(f"  ✅ Loaded {len(products)} products from {json_file.name}")
            except Exception as e:
                print(f"  ❌ Error loading {json_file}: {e}")

        print(f"\n✅ Total products loaded: {len(self.products)}")

        # Group by company
        for product in self.products:
            mIdx = product.get('mIdx')
            if mIdx:
                self.companies[mIdx].append(product)

        print(f"✅ Unique companies found: {len(self.companies)}")

    def list_companies(self):
        """List all companies with product counts"""
        print("\n" + "="*70)
        print("COMPANY LIST (sorted by product count)")
        print("="*70)

        # Sort by product count
        sorted_companies = sorted(
            self.companies.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        print(f"\n{'Company ID':<15} {'Product Count':<15} {'Sample Product IDs'}")
        print("-"*70)

        for mIdx, products in sorted_companies[:50]:  # Top 50 companies
            sample_pIdx = [p['pIdx'] for p in products[:3]]
            print(f"{mIdx:<15} {len(products):<15} {', '.join(sample_pIdx)}")

        if len(sorted_companies) > 50:
            print(f"\n... and {len(sorted_companies) - 50} more companies")

        print("\n" + "="*70)

        return sorted_companies

    def filter_by_company(self, mIdx_list):
        """
        Filter products by company ID(s)

        Args:
            mIdx_list: List of company IDs (strings)

        Returns:
            Dictionary mapping mIdx to products
        """
        print("\n" + "="*70)
        print("FILTERING BY COMPANY")
        print("="*70)

        results = {}

        for mIdx in mIdx_list:
            if mIdx in self.companies:
                products = self.companies[mIdx]
                results[mIdx] = products
                print(f"\n  Company {mIdx}: {len(products)} products")

                # Show category breakdown
                categories = defaultdict(int)
                for p in products:
                    categories[p.get('category_name', 'Unknown')] += 1

                print(f"  Categories:")
                for cat, count in sorted(categories.items()):
                    print(f"    - {cat}: {count} products")
            else:
                print(f"\n  ⚠️ Company {mIdx}: No products found")

        return results

    def save_company_data(self, mIdx, products, output_dir='data/freemold/filtered'):
        """
        Save company-specific data to JSON and CSV

        Args:
            mIdx: Company ID
            products: List of products
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_file = output_path / f'company_{mIdx}_products.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        # Save CSV
        if products:
            csv_file = output_path / f'company_{mIdx}_products.csv'
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)

        print(f"\n  💾 Saved to:")
        print(f"    JSON: {json_file}")
        print(f"    CSV: {csv_file}")

    def export_company_summary(self, output_file='data/freemold/company_summary.csv'):
        """Export summary of all companies"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = []
        for mIdx, products in self.companies.items():
            # Category breakdown
            categories = defaultdict(int)
            for p in products:
                categories[p.get('category_code', 'Unknown')] += 1

            summary.append({
                'company_id': mIdx,
                'total_products': len(products),
                'B001_count': categories.get('B001', 0),
                'B002_count': categories.get('B002', 0),
                'B003_count': categories.get('B003', 0),
                'B004_count': categories.get('B004', 0),
                'sample_products': ','.join([p['pIdx'] for p in products[:3]])
            })

        # Sort by total products
        summary.sort(key=lambda x: x['total_products'], reverse=True)

        # Save CSV
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=summary[0].keys())
            writer.writeheader()
            writer.writerows(summary)

        print(f"\n✅ Company summary saved to: {output_path}")
        print(f"   Total companies: {len(summary)}")

        return summary


def main():
    parser = argparse.ArgumentParser(description='Filter Freemold products by company')
    parser.add_argument('--mIdx', type=str, help='Company ID(s) to filter (comma-separated)')
    parser.add_argument('--list-companies', action='store_true', help='List all companies')
    parser.add_argument('--export-summary', action='store_true', help='Export company summary CSV')
    parser.add_argument('--data-dir', type=str, default='data/freemold/crawled_products',
                        help='Directory containing crawled data')

    args = parser.parse_args()

    # Initialize filter
    filter_tool = CompanyFilter(data_dir=args.data_dir)
    filter_tool.load_all_products()

    if args.list_companies:
        # List all companies
        filter_tool.list_companies()

    if args.export_summary:
        # Export company summary
        filter_tool.export_company_summary()

    if args.mIdx:
        # Filter by company ID(s)
        mIdx_list = [m.strip() for m in args.mIdx.split(',')]
        results = filter_tool.filter_by_company(mIdx_list)

        # Save filtered data
        for mIdx, products in results.items():
            filter_tool.save_company_data(mIdx, products)

        print("\n" + "="*70)
        print("FILTERING COMPLETE")
        print("="*70)
        print(f"Companies filtered: {len(results)}")
        print(f"Total products: {sum(len(p) for p in results.values())}")
        print(f"Output: data/freemold/filtered/")
        print("="*70)

    if not (args.list_companies or args.export_summary or args.mIdx):
        parser.print_help()


if __name__ == "__main__":
    main()
