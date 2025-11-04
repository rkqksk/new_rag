#!/usr/bin/env python3
"""Verify product data updates"""

import json
from pathlib import Path
from collections import defaultdict

def verify_directory(base_dir: Path, category_type: str):
    """Verify all JSON files in directory"""
    stats = {
        'total': 0,
        'with_moq': 0,
        'moq_10000': 0,
        'with_neck_size': 0,
        'missing_moq': [],
        'wrong_moq': [],
        'missing_neck_size': []
    }

    json_files = list(base_dir.rglob("*.json"))
    stats['total'] = len(json_files)

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check MOQ
            if "pricing" in data and "moq" in data["pricing"]:
                stats['with_moq'] += 1
                if data["pricing"]["moq"] == 10000:
                    stats['moq_10000'] += 1
                else:
                    stats['wrong_moq'].append((json_file.name, data["pricing"]["moq"]))
            else:
                stats['missing_moq'].append(json_file.name)

            # Check neck_size
            if "specifications" in data and "neck_size" in data["specifications"]:
                stats['with_neck_size'] += 1
            else:
                stats['missing_neck_size'].append(json_file.name)

        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    return stats

def main():
    print("=" * 80)
    print("PRODUCT DATA VERIFICATION")
    print("=" * 80)

    # Verify Pump
    pump_dir = Path("data/crawled_products_final/Pump")
    if pump_dir.exists():
        print("\n📦 PUMP Products")
        print("-" * 80)
        pump_stats = verify_directory(pump_dir, "PUMP")

        print(f"Total files: {pump_stats['total']}")
        print(f"With MOQ: {pump_stats['with_moq']} ({pump_stats['with_moq']/pump_stats['total']*100:.1f}%)")
        print(f"MOQ = 10,000: {pump_stats['moq_10000']} ({pump_stats['moq_10000']/pump_stats['total']*100:.1f}%)")
        print(f"With neck_size: {pump_stats['with_neck_size']} ({pump_stats['with_neck_size']/pump_stats['total']*100:.1f}%)")

        if pump_stats['missing_moq']:
            print(f"\n⚠️  Missing MOQ: {len(pump_stats['missing_moq'])} files")
            for fname in pump_stats['missing_moq'][:5]:
                print(f"  - {fname}")

        if pump_stats['wrong_moq']:
            print(f"\n⚠️  Wrong MOQ: {len(pump_stats['wrong_moq'])} files")
            for fname, moq in pump_stats['wrong_moq'][:5]:
                print(f"  - {fname}: {moq}")

        if pump_stats['missing_neck_size']:
            print(f"\n⚠️  Missing neck_size: {len(pump_stats['missing_neck_size'])} files")
            for fname in pump_stats['missing_neck_size'][:5]:
                print(f"  - {fname}")

    # Verify Cap
    cap_dir = Path("data/crawled_products_final/Cap")
    if cap_dir.exists():
        print("\n\n🧢 CAP Products")
        print("-" * 80)
        cap_stats = verify_directory(cap_dir, "CAP")

        print(f"Total files: {cap_stats['total']}")
        print(f"With MOQ: {cap_stats['with_moq']} ({cap_stats['with_moq']/cap_stats['total']*100:.1f}%)")
        print(f"MOQ = 10,000: {cap_stats['moq_10000']} ({cap_stats['moq_10000']/cap_stats['total']*100:.1f}%)")
        print(f"With neck_size: {cap_stats['with_neck_size']} ({cap_stats['with_neck_size']/cap_stats['total']*100:.1f}%)")

        if cap_stats['missing_moq']:
            print(f"\n⚠️  Missing MOQ: {len(cap_stats['missing_moq'])} files")
            for fname in cap_stats['missing_moq'][:5]:
                print(f"  - {fname}")

        if cap_stats['wrong_moq']:
            print(f"\n⚠️  Wrong MOQ: {len(cap_stats['wrong_moq'])} files")
            for fname, moq in cap_stats['wrong_moq'][:5]:
                print(f"  - {fname}: {moq}")

        if cap_stats['missing_neck_size']:
            print(f"\n⚠️  Missing neck_size: {len(cap_stats['missing_neck_size'])} files")
            for fname in cap_stats['missing_neck_size'][:5]:
                print(f"  - {fname}")

    # Overall summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_files = pump_stats['total'] + cap_stats['total']
    total_moq = pump_stats['moq_10000'] + cap_stats['moq_10000']
    total_neck = pump_stats['with_neck_size'] + cap_stats['with_neck_size']

    print(f"✅ Total files processed: {total_files}")
    print(f"✅ Files with MOQ=10,000: {total_moq} ({total_moq/total_files*100:.1f}%)")
    print(f"✅ Files with neck_size: {total_neck} ({total_neck/total_files*100:.1f}%)")

    if total_moq == total_files:
        print("\n🎉 SUCCESS: All products have MOQ set to 10,000!")
    else:
        print(f"\n⚠️  WARNING: {total_files - total_moq} files missing correct MOQ")

if __name__ == "__main__":
    main()
