#!/usr/bin/env python3
"""
Update MOQ for all heavy bottles to 10,000
헤비브로우 제품의 MOQ를 10K로 일괄 변경
"""

import json
from pathlib import Path
from datetime import datetime

def update_heavy_bottle_moq(dry_run: bool = True):
    """Update MOQ for all heavy bottles"""

    base_dir = Path("data/crawled_products_final")

    updated_count = 0
    json_files = list(base_dir.rglob("*.json"))

    print(f"Found {len(json_files)} product files to check")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Get product info
            product_name = data.get('product_name', '')
            product_code = data.get('specifications', {}).get('제품 코드', 'N/A')

            # Skip if not a heavy bottle
            if '헤비' not in product_name:
                continue

            # Check current pricing
            pricing = data.get('pricing', {})
            current_moq = pricing.get('moq')

            # Update MOQ to 10,000
            if 'pricing' not in data:
                data['pricing'] = {}

            data['pricing']['moq'] = 10000
            data['pricing']['moq_updated_at'] = datetime.now().isoformat()

            # Write back
            if not dry_run:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            updated_count += 1

            if updated_count <= 10:  # Show first 10 examples
                print(f"  ✓ {product_code}: {product_name}")
                print(f"    MOQ: {current_moq} → 10,000")

        except Exception as e:
            print(f"  ❌ Error processing {json_file}: {e}")

    # Summary
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Updated: {updated_count} heavy bottle products")
    print(f"  MOQ set to: 10,000")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Update MOQ for heavy bottles to 10K")
    parser.add_argument("--execute", action="store_true", help="Actually write changes")
    args = parser.parse_args()

    dry_run = not args.execute

    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No files will be modified")
        print("=" * 80)
    else:
        print("=" * 80)
        print("EXECUTION MODE - Files will be modified")
        print("=" * 80)

    update_heavy_bottle_moq(dry_run)

    if dry_run:
        print("\nTo apply these changes, run with --execute flag:")
        print("  python scripts/update_heavy_bottle_moq.py --execute")

if __name__ == "__main__":
    main()
