#!/usr/bin/env python3
"""
Clean 사양 field by removing /Ø pattern
Example: "26x52(mm)/Ø24" → "26x52(mm)"
         "29x22(mm)/내경Ø20" → "29x22(mm)"
"""

import json
import re
from pathlib import Path
from datetime import datetime

def clean_sayang_field(sayang: str) -> str:
    """
    Remove /Ø or /내경Ø pattern from 사양 field

    Examples:
        "26x52(mm)/Ø24" → "26x52(mm)"
        "29x22(mm)/내경Ø20" → "29x22(mm)"
        "내경 Ø20" → "내경 Ø20" (no change)
    """
    # Pattern to match /Ø followed by numbers or /내경Ø followed by numbers
    pattern = r'/(내경)?Ø\d+'

    cleaned = re.sub(pattern, '', sayang)
    return cleaned.strip()

def process_directory(base_dir: Path, dry_run: bool = True):
    """Process all JSON files in directory"""
    updated_count = 0
    changed_files = []

    json_files = list(base_dir.rglob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if 사양 field exists and contains pattern
            if "specifications" in data and "사양" in data["specifications"]:
                original_sayang = data["specifications"]["사양"]
                cleaned_sayang = clean_sayang_field(original_sayang)

                # Only update if changed
                if original_sayang != cleaned_sayang:
                    data["specifications"]["사양"] = cleaned_sayang

                    # Add metadata
                    data["specifications"]["sayang_cleaned_at"] = datetime.now().isoformat()

                    # Write back
                    if not dry_run:
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                    updated_count += 1
                    changed_files.append({
                        'file': json_file.name,
                        'code': data.get('product_code', 'N/A'),
                        'before': original_sayang,
                        'after': cleaned_sayang
                    })

        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")

    return updated_count, changed_files

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clean 사양 field")
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

    # Process Cap directory
    cap_dir = Path("data/crawled_products_final/Cap")
    cap_updated, cap_changes = 0, []
    if cap_dir.exists():
        cap_updated, cap_changes = process_directory(cap_dir, dry_run)

    # Process Pump directory
    pump_dir = Path("data/crawled_products_final/Pump")
    pump_updated, pump_changes = 0, []
    if pump_dir.exists():
        pump_updated, pump_changes = process_directory(pump_dir, dry_run)

    # Show changes
    all_changes = cap_changes + pump_changes

    if all_changes:
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Changes to be made: {len(all_changes)}")
        print("-" * 80)
        for change in all_changes:
            print(f"  {change['code']} ({change['file']})")
            print(f"    Before: {change['before']}")
            print(f"    After:  {change['after']}")
            print()
    else:
        print("\n✅ No files need to be updated")

    # Summary
    print("=" * 80)
    print(f"{'[DRY RUN] ' if dry_run else ''}SUMMARY")
    print("=" * 80)
    print(f"Files updated: {cap_updated + pump_updated}")

    if dry_run and all_changes:
        print("\nTo apply these changes, run with --execute flag:")
        print(f"  python {Path(__file__).name} --execute")

if __name__ == "__main__":
    main()
