#!/usr/bin/env python3
"""
Extract Packaging Products from Already Crawled Data

이미 크롤링된 248,000개 제품 중에서 packaging 제품(category_id 2-113)만 추출합니다.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production')
CLASSIFICATION_FILE = BASE_PATH / 'category_classification.json'
TEXT_ONLY_DIR = BASE_PATH / 'products_text_only'
OUTPUT_FILE = BASE_PATH / 'packaging_extracted.jsonl'

def load_classification():
    """카테고리 분류 규칙 로드"""
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_packaging(category_id: int, classification: dict) -> bool:
    """Packaging 카테고리인지 확인 (category_id 2-113)"""
    return category_id in classification['category_types']['packaging']['category_ids']

def get_subcategory(category_id: int, classification: dict) -> str:
    """Packaging 세부 카테고리 이름 반환"""
    for subcat_name, cat_ids in classification['packaging_subcategories'].items():
        if category_id in cat_ids:
            return subcat_name
    return 'unknown'

def extract_packaging_products():
    """이미 크롤링된 데이터에서 packaging 제품만 추출"""
    classification = load_classification()

    print("=" * 80)
    print("📦 PACKAGING PRODUCT EXTRACTION FROM CRAWLED DATA")
    print("=" * 80)
    print()

    # 통계
    total_read = 0
    packaging_extracted = 0
    category_counts = Counter()
    subcategory_counts = defaultdict(int)

    # 출력 파일 준비
    output_file = open(OUTPUT_FILE, 'w', encoding='utf-8')

    print(f"📥 Reading from: {TEXT_ONLY_DIR}")
    print(f"💾 Writing to: {OUTPUT_FILE}")
    print()

    # 모든 JSONL 파일 처리
    all_files = sorted(TEXT_ONLY_DIR.glob('batch_*.jsonl')) + \
                sorted(TEXT_ONLY_DIR.glob('worker_*_output.jsonl'))

    print(f"📂 Found {len(all_files)} files to process")
    print()

    for file_idx, file in enumerate(all_files, 1):
        file_packaging_count = 0

        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    total_read += 1

                    try:
                        data = json.loads(line)
                        category_id = data.get('category_id')

                        if category_id and is_packaging(category_id, classification):
                            # Packaging 제품 발견!
                            packaging_extracted += 1
                            file_packaging_count += 1
                            category_counts[category_id] += 1

                            # 세부 카테고리 분류
                            subcat = get_subcategory(category_id, classification)
                            subcategory_counts[subcat] += 1

                            # 메타데이터 추가
                            data['category_type'] = 'packaging'  # 명확한 packaging 라벨 추가
                            data['packaging_subcategory'] = subcat
                            data['extracted_at'] = datetime.now().isoformat()

                            # 출력 파일에 저장
                            output_file.write(json.dumps(data, ensure_ascii=False) + '\n')

                    except json.JSONDecodeError:
                        continue

                    # 진행상황 표시 (10,000개마다)
                    if total_read % 10000 == 0:
                        print(f"   Processed {total_read:,} products... "
                              f"(Found {packaging_extracted:,} packaging so far)")

        except Exception as e:
            print(f"⚠️  Error reading {file.name}: {e}")
            continue

        # 파일별 요약
        if file_packaging_count > 0:
            print(f"✅ {file.name}: {file_packaging_count:,} packaging products")

    output_file.close()

    # 최종 요약
    print()
    print("=" * 80)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 80)
    print()
    print(f"📥 Total products read: {total_read:,}")
    print(f"📦 Packaging products extracted: {packaging_extracted:,}")
    print(f"📈 Percentage: {packaging_extracted / total_read * 100:.2f}%")
    print()

    # 세부 카테고리별 통계
    print("=" * 80)
    print("🏷️  PACKAGING BY SUBCATEGORY")
    print("=" * 80)
    print()
    for subcat, count in sorted(subcategory_counts.items(), key=lambda x: -x[1]):
        percentage = count / packaging_extracted * 100
        print(f"   {subcat:25s}: {count:8,} products ({percentage:5.2f}%)")
    print()

    # Top 10 카테고리
    print("=" * 80)
    print("🔝 TOP 10 CATEGORIES")
    print("=" * 80)
    print()
    for cat_id, count in category_counts.most_common(10):
        subcat = get_subcategory(cat_id, classification)
        percentage = count / packaging_extracted * 100
        print(f"   Category {cat_id:3d} ({subcat:20s}): {count:6,} products ({percentage:5.2f}%)")
    print()

    print("=" * 80)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print(f"📁 Output file: {OUTPUT_FILE}")
    print(f"📊 Total packaging products: {packaging_extracted:,}")
    print()
    print("💡 Next steps:")
    print("   1. Review extracted data quality")
    print("   2. Download images for these products (1 image per product)")
    print("   3. Upload to RAG system")
    print()

if __name__ == '__main__':
    extract_packaging_products()
