#!/usr/bin/env python3
"""
Add spec field to product_dictionary.json from Excel master comparison
"""

import json
import pandas as pd


def add_spec_to_products():
    """Add spec (with neck size Ø) to all products"""

    print("Loading product dictionary...")
    with open('data/product_dictionary.json') as f:
        products = json.load(f)

    print("Loading master comparison from Excel...")
    df = pd.read_excel(
        'data/excel_uploads/MASTER_COMPARISON_REVIEW.xlsx',
        sheet_name='Master Comparison'
    )

    print(f"\nTotal products in dictionary: {len(products)}")
    print(f"Total products in Excel: {len(df)}")

    updated_count = 0
    missing_count = 0

    for product_id, product in products.items():
        product_code = product.get('product_code')

        if not product_code:
            continue

        # Find in Excel
        excel_row = df[df['Product Code'] == product_code]

        if not excel_row.empty:
            # Get spec from Crawled first, fallback to Excel
            spec_crawled = excel_row['Spec (Crawled)'].values[0]
            spec_excel = excel_row['Spec (Excel)'].values[0]

            spec = spec_crawled if pd.notna(spec_crawled) else spec_excel

            if pd.notna(spec):
                product['spec'] = str(spec)
                updated_count += 1
            else:
                missing_count += 1
        else:
            missing_count += 1

    print(f"\n✅ Updated {updated_count} products with spec")
    print(f"⚠️  Missing spec for {missing_count} products")

    # Save updated dictionary
    print("\nSaving updated product dictionary...")
    with open('data/product_dictionary.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print("✅ Done!")

    # Verify by showing sample
    print("\n📊 Sample products with spec:")
    count = 0
    for product_id, product in products.items():
        if product.get('spec'):
            print(f"  {product.get('product_code')}: {product.get('spec')}")
            count += 1
            if count >= 5:
                break


if __name__ == "__main__":
    add_spec_to_products()
