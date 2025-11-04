#!/usr/bin/env python3
"""
Analyze Missing Products from Comparison Report
Separates valid product codes from invalid entries (specs, dimensions)
"""

import json
import re
from pathlib import Path

def is_valid_product_code(code: str) -> bool:
    """
    Check if string matches product code pattern.
    Valid patterns:
    - XX000-X000: BT111-RP09, HT030-RP01
    - XX000-X000(N): MH400-G001(24), BG070-R001(20)
    - Special: Ignore specs like "PET / 200g", dimensions like "60 x 109(mm)"
    """
    # Invalid patterns
    if '/' in code:  # Specs like "PET / 200g"
        return False
    if 'x' in code.lower() and '(' not in code:  # Dimensions like "60 x 109(mm)"
        return False
    if code.startswith('Ø'):  # Diameters like "Ø43"
        return False
    if code.lower() in ['pe', 'pet', 'pp', 'petg', 'hdpe']:  # Material names
        return False

    # Valid patterns: XX000-X000 or XX000-X000(N)
    pattern = r'^[A-Z]{2}\d{3}-[A-Z]{1,2}\d{2,3}(\(\d+\))?(\(.*\))?$'
    return bool(re.match(pattern, code))


def analyze_missing_products():
    """Analyze comparison report and categorize missing products"""

    report_path = Path("data/excel_uploads/processed/comparison_report.json")

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    missing_in_crawled = report['details']['missing_in_crawled']

    # Categorize
    valid_codes = []
    invalid_entries = []

    for code in missing_in_crawled:
        if is_valid_product_code(code):
            valid_codes.append(code)
        else:
            invalid_entries.append(code)

    # Results
    print(f"📊 Missing Products Analysis")
    print(f"=" * 60)
    print(f"Total missing: {len(missing_in_crawled)}")
    print(f"Valid product codes: {len(valid_codes)}")
    print(f"Invalid entries (specs/dimensions): {len(invalid_entries)}")
    print()

    print(f"✅ Valid Product Codes to Re-crawl ({len(valid_codes)}):")
    print("-" * 60)
    for code in sorted(valid_codes):
        print(f"  {code}")

    print(f"\n❌ Invalid Entries (cannot crawl) ({len(invalid_entries)}):")
    print("-" * 60)
    for entry in sorted(invalid_entries)[:20]:  # Show first 20
        print(f"  {entry}")
    if len(invalid_entries) > 20:
        print(f"  ... and {len(invalid_entries) - 20} more")

    # Save valid codes to file for re-crawling
    output_path = Path("data/excel_uploads/processed/missing_product_codes.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        for code in sorted(valid_codes):
            f.write(f"{code}\n")

    print(f"\n💾 Valid codes saved to: {output_path}")

    return valid_codes, invalid_entries


if __name__ == "__main__":
    valid_codes, invalid_entries = analyze_missing_products()
