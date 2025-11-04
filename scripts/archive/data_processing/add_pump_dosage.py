#!/usr/bin/env python3
"""
Add dosage (토출량) field to pump products

펌프 토출량 기준:
- 미스트/스프레이: 0.1-0.15cc (가장 작음)
- 에센스 펌프: 0.15-0.2cc
- 일반 펌프: 0.2-0.3cc
- 로션 펌프: 0.3-0.5cc
- 고점도 펌프: 0.5-1.0cc (점도 높은 제품용)
- 대용량 펌프 (500ml+): 1.0-2.0cc
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

def infer_dosage_from_pump_type(product_name: str, neck_size: str) -> Optional[float]:
    """
    펌프 타입과 네크사이즈로 토출량 추정

    토출량 결정 요소:
    1. 펌프 타입 (미스트 < 에센스 < 일반 < 로션 < 고점도)
    2. 네크사이즈 (작은 네크 = 작은 토출량)

    주의: 미스트/스프레이는 네크사이즈와 무관하게 고정 토출량 사용
    """
    product_lower = product_name.lower()

    # 네크사이즈에서 숫자 추출
    neck_value = None
    if neck_size:
        neck_match = re.search(r'(\d+)', neck_size)
        if neck_match:
            neck_value = int(neck_match.group(1))

    # 미스트/스프레이 펌프는 특별 처리 (네크사이즈 조정 없음)
    is_mist = any(kw in product_lower for kw in ['미스트', 'mist', '스프레이', 'spray'])

    # 펌프 타입별 기본 토출량
    if is_mist:
        # 미스트/스프레이: 0.1-0.15cc (네크사이즈 무관)
        if neck_value and neck_value <= 20:
            dosage = 0.1
        elif neck_value and neck_value >= 28:
            dosage = 0.15
        else:
            dosage = 0.12
    elif any(kw in product_lower for kw in ['에센스', 'essence', '세럼', 'serum']):
        # 에센스 펌프: 0.15-0.25cc
        base_dosage = 0.2
        dosage = adjust_by_neck_size(base_dosage, neck_value)
    elif any(kw in product_lower for kw in ['오일', 'oil']):
        # 오일 펌프: 0.2-0.3cc
        base_dosage = 0.25
        dosage = adjust_by_neck_size(base_dosage, neck_value)
    elif any(kw in product_lower for kw in ['고점도', 'high-density', '점도']):
        # 고점도 펌프: 0.5-1.0cc
        base_dosage = 0.8
        dosage = adjust_by_neck_size(base_dosage, neck_value)
    elif any(kw in product_lower for kw in ['로션', 'lotion']):
        # 로션 펌프: 0.3-0.5cc
        base_dosage = 0.4
        dosage = adjust_by_neck_size(base_dosage, neck_value)
    else:
        # 일반 펌프: 0.25-0.35cc
        base_dosage = 0.3
        dosage = adjust_by_neck_size(base_dosage, neck_value)

    # 소수점 2자리로 반올림
    return round(dosage, 2)

def adjust_by_neck_size(base_dosage: float, neck_value: Optional[int]) -> float:
    """네크사이즈에 따른 토출량 조정 (미스트 제외)"""
    if neck_value is None:
        return base_dosage

    if neck_value <= 20:
        # 작은 네크 (20파이 이하): -20%
        return base_dosage * 0.8
    elif neck_value <= 24:
        # 중간 네크 (24파이): 기본값
        return base_dosage
    elif neck_value <= 28:
        # 큰 네크 (28파이): +20%
        return base_dosage * 1.2
    else:
        # 매우 큰 네크 (32파이 이상): +40%
        return base_dosage * 1.4

def add_dosage_to_pumps(dry_run: bool = True):
    """Add dosage field to all pump products"""

    # Check both Pump and Cap directories (pumps can be in either)
    base_dir = Path("data/crawled_products_final")
    search_dirs = [base_dir / "Pump", base_dir / "Cap"]

    updated_count = 0
    dosage_distribution = {}
    json_files = []

    # Collect all JSON files from both directories
    for dir_path in search_dirs:
        if dir_path.exists():
            json_files.extend(list(dir_path.rglob("*.json")))

    print(f"Found {len(json_files)} product files to check")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Get product info
            product_name = data.get('product_name', '')
            category_type = data.get('category_type', '').upper()
            neck_size = data.get('specifications', {}).get('neck_size', '')
            product_code = data.get('product_code', 'N/A')

            # Skip if not a pump
            if category_type != 'PUMP':
                # Also check product name for pump keywords
                name_lower = product_name.lower()
                if not any(kw in name_lower for kw in ['펌프', 'pump', '미스트', 'mist', '스프레이', 'spray']):
                    continue

            # Infer dosage
            dosage = infer_dosage_from_pump_type(product_name, neck_size)

            if dosage:
                # Add to specifications
                if 'specifications' not in data:
                    data['specifications'] = {}

                data['specifications']['dosage'] = f"{dosage}cc"
                data['specifications']['dosage_value'] = dosage
                data['specifications']['dosage_updated_at'] = datetime.now().isoformat()

                # Track distribution
                dosage_key = f"{dosage}cc"
                dosage_distribution[dosage_key] = dosage_distribution.get(dosage_key, 0) + 1

                # Write back
                if not dry_run:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                updated_count += 1

                if updated_count <= 5:  # Show first 5 examples
                    print(f"  ✓ {product_code}: {product_name}")
                    print(f"    Neck: {neck_size} → Dosage: {dosage}cc")

        except Exception as e:
            print(f"  ❌ Error processing {json_file}: {e}")

    # Summary
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Updated: {updated_count} pump products")
    print(f"\nDosage Distribution:")
    for dosage, count in sorted(dosage_distribution.items()):
        print(f"  {dosage}: {count} products")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Add dosage field to pump products")
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

    add_dosage_to_pumps(dry_run)

    if dry_run:
        print("\nTo apply these changes, run with --execute flag:")
        print("  python scripts/add_pump_dosage.py --execute")

if __name__ == "__main__":
    main()
