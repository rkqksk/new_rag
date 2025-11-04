#!/usr/bin/env python3
"""Check 사양 field patterns"""

import json
from pathlib import Path
from collections import defaultdict
import re

def analyze_sayang_patterns():
    """Analyze 사양 field patterns across all products"""
    patterns = defaultdict(list)

    # Check Cap and Pump directories
    for base_dir in ["data/crawled_products_final/Cap", "data/crawled_products_final/Pump"]:
        base_path = Path(base_dir)
        if not base_path.exists():
            continue

        for json_file in base_path.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                sayang = data.get("specifications", {}).get("사양", "")
                if sayang:
                    # Check if contains /Ø or /내경 pattern
                    if "/Ø" in sayang or "/내경" in sayang:
                        patterns["with_slash_diameter"].append({
                            "file": json_file.name,
                            "sayang": sayang,
                            "code": data.get("product_code", "N/A")
                        })
                    else:
                        patterns["without_slash"].append({
                            "file": json_file.name,
                            "sayang": sayang,
                            "code": data.get("product_code", "N/A")
                        })

            except Exception as e:
                print(f"Error reading {json_file}: {e}")

    return patterns

def main():
    print("=" * 80)
    print("사양 FIELD PATTERN ANALYSIS")
    print("=" * 80)

    patterns = analyze_sayang_patterns()

    # Show files with /Ø or /내경 pattern
    if patterns["with_slash_diameter"]:
        print(f"\n📋 Files with /Ø or /내경 pattern: {len(patterns['with_slash_diameter'])}")
        print("-" * 80)
        for item in patterns["with_slash_diameter"][:20]:
            print(f"  {item['code']}: {item['sayang']}")
        if len(patterns["with_slash_diameter"]) > 20:
            print(f"  ... and {len(patterns['with_slash_diameter']) - 20} more")

    # Show files without slash
    if patterns["without_slash"]:
        print(f"\n📋 Files without /Ø or /내경 pattern: {len(patterns['without_slash'])}")
        print("-" * 80)
        for item in patterns["without_slash"][:10]:
            print(f"  {item['code']}: {item['sayang']}")
        if len(patterns["without_slash"]) > 10:
            print(f"  ... and {len(patterns['without_slash']) - 10} more")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"With /Ø or /내경: {len(patterns['with_slash_diameter'])}")
    print(f"Without pattern: {len(patterns['without_slash'])}")

if __name__ == "__main__":
    main()
