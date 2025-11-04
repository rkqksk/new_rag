#!/usr/bin/env python3
"""
Extract Direct Blow products grouped by company for manual M.Bottle identification
"""

import pandas as pd
import os

# Read the CSV
csv_path = 'data/freemold/freemold_products_page1.csv'
df = pd.read_csv(csv_path)

# Filter for Direct Blow only
direct_blow = df[df['category_code'] == 'B001'].copy()

# Get unique companies
companies = direct_blow.groupby('company_id').size().reset_index(name='product_count')
companies = companies.sort_values('product_count', ascending=False)

print("=" * 70)
print("DIRECT BLOW (다이렉트 브로우) - COMPANIES ON PAGE 1")
print("=" * 70)
print()

# Create separate CSV for each company
output_dir = 'data/freemold/companies_direct_blow'
os.makedirs(output_dir, exist_ok=True)

for _, row in companies.iterrows():
    company_id = row['company_id']
    count = row['product_count']

    # Filter products for this company
    company_products = direct_blow[direct_blow['company_id'] == company_id]

    # Save to CSV
    output_file = f"{output_dir}/company_{company_id}_{count}products.csv"
    company_products.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"Company {company_id}: {count} products")
    print(f"  ✅ Saved to: {output_file}")
    print(f"  📍 Company URL: https://www.freemold.net/Front/Company/?mIdx={company_id}")
    print(f"  📄 Sample product URL: {company_products.iloc[0]['product_url']}")
    print()

print("=" * 70)
print(f"Total companies: {len(companies)}")
print(f"Total products: {len(direct_blow)}")
print()
print("🎯 NEXT STEP:")
print("   1. Check the URLs manually to identify which company is M.Bottle (엠보틀)")
print("   2. Or run the full crawler and filter afterward")
print("=" * 70)
