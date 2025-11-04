#!/usr/bin/env python3
"""
Update product data:
1. Pump: Keep only neck_size in specifications (other size info remains as context)
2. Cap: No changes to size info
3. Both: Set MOQ to 10,000
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def update_pump_product(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update pump product: ensure neck_size is primary size reference"""
    # Add MOQ to pricing
    if "pricing" not in data:
        data["pricing"] = {}

    data["pricing"]["moq"] = 10000
    data["pricing"]["moq_updated_at"] = datetime.now().isoformat()

    # Ensure neck_size is present in specifications
    if "specifications" in data and "neck_size" in data["specifications"]:
        # Keep neck_size as the primary size reference
        # Other size info (dimensions, 사양) kept for context
        pass

    return data

def update_cap_product(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update cap product: only add MOQ"""
    # Add MOQ to pricing
    if "pricing" not in data:
        data["pricing"] = {}

    data["pricing"]["moq"] = 10000
    data["pricing"]["moq_updated_at"] = datetime.now().isoformat()

    # No changes to size info for caps
    return data

def process_directory(base_dir: Path, category_type: str, dry_run: bool = True):
    """Process all JSON files in directory"""
    updated_count = 0
    error_count = 0

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {category_type} products in {base_dir}")

    # Find all JSON files
    json_files = list(base_dir.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files")

    for json_file in json_files:
        try:
            # Read existing data
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update based on category type
            if category_type == "PUMP":
                updated_data = update_pump_product(data)
            elif category_type == "CAP":
                updated_data = update_cap_product(data)
            else:
                print(f"⚠️  Unknown category type: {category_type} in {json_file}")
                continue

            # Write back (unless dry run)
            if not dry_run:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, ensure_ascii=False, indent=2)

            updated_count += 1

            if updated_count % 100 == 0:
                print(f"  ✓ Processed {updated_count} files...")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error processing {json_file}: {e}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary for {category_type}:")
    print(f"  ✓ Updated: {updated_count}")
    print(f"  ❌ Errors: {error_count}")

    return updated_count, error_count

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Update product data")
    parser.add_argument("--execute", action="store_true", help="Actually write changes (default is dry run)")
    parser.add_argument("--pump-dir", default="data/crawled_products_final/Pump", help="Pump products directory")
    parser.add_argument("--cap-dir", default="data/crawled_products_final/Cap", help="Cap products directory")
    args = parser.parse_args()

    dry_run = not args.execute

    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No files will be modified")
        print("Use --execute flag to actually apply changes")
        print("=" * 80)
    else:
        print("=" * 80)
        print("EXECUTION MODE - Files will be modified")
        print("=" * 80)

    # Process Pump products
    pump_dir = Path(args.pump_dir)
    if pump_dir.exists():
        pump_updated, pump_errors = process_directory(pump_dir, "PUMP", dry_run)
    else:
        print(f"⚠️  Pump directory not found: {pump_dir}")
        pump_updated, pump_errors = 0, 0

    # Process Cap products
    cap_dir = Path(args.cap_dir)
    if cap_dir.exists():
        cap_updated, cap_errors = process_directory(cap_dir, "CAP", dry_run)
    else:
        print(f"⚠️  Cap directory not found: {cap_dir}")
        cap_updated, cap_errors = 0, 0

    # Overall summary
    print("\n" + "=" * 80)
    print(f"{'[DRY RUN] ' if dry_run else ''}OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total Updated: {pump_updated + cap_updated}")
    print(f"Total Errors: {pump_errors + cap_errors}")

    if dry_run:
        print("\nTo apply these changes, run with --execute flag:")
        print(f"  python {Path(__file__).name} --execute")

if __name__ == "__main__":
    main()
