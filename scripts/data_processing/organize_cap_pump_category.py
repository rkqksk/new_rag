#!/usr/bin/env python3
"""
Cap&Pump 카테고리 데이터 정리 스크립트
test_cap_pump_category → crawled_products_organized/CapPump
"""

import json
import shutil
from pathlib import Path
import csv
from datetime import datetime

# 경로 설정
SOURCE_DIR = Path("data/test_cap_pump_category")
TARGET_DIR = Path("data/crawled_products_organized/CapPump")

def find_category_json():
    """카테고리 JSON 파일 찾기"""
    category_files = list(SOURCE_DIR.glob("category_*.json"))
    if category_files:
        return category_files[0]
    return None

def create_directory_structure():
    """필요한 디렉토리 구조 생성"""
    dirs = [
        TARGET_DIR,
        TARGET_DIR / "products",
        TARGET_DIR / "images",
        TARGET_DIR / "print_area"
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ 디렉토리 구조 생성: {TARGET_DIR}")

def copy_product_files():
    """제품 JSON 파일 복사"""
    product_files = list(SOURCE_DIR.glob("idx_*.json"))
    copied_count = 0

    for src_file in product_files:
        dst_file = TARGET_DIR / "products" / src_file.name
        shutil.copy2(src_file, dst_file)
        copied_count += 1

    print(f"✅ 제품 JSON 파일 복사: {copied_count}개")
    return copied_count

def copy_image_files():
    """이미지 파일 복사"""
    images_src = SOURCE_DIR / "images"
    images_dst = TARGET_DIR / "images"

    if images_src.exists():
        # 기존 images 디렉토리가 있으면 삭제
        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)
        image_count = len(list(images_dst.glob("*")))
        print(f"✅ 이미지 파일 복사: {image_count}개")
        return image_count
    else:
        print("⚠️ 원본 images 디렉토리가 없습니다")
        return 0

def copy_print_area_files():
    """인쇄 영역 파일 복사"""
    print_area_src = SOURCE_DIR / "print_area"
    print_area_dst = TARGET_DIR / "print_area"

    if print_area_src.exists():
        # 기존 print_area 디렉토리가 있으면 삭제
        if print_area_dst.exists():
            shutil.rmtree(print_area_dst)
        shutil.copytree(print_area_src, print_area_dst)
        file_count = len(list(print_area_dst.glob("*")))
        print(f"✅ 인쇄 영역 파일 복사: {file_count}개")
        return file_count
    else:
        print("⚠️ 원본 print_area 디렉토리가 없습니다")
        return 0

def generate_csv_report():
    """CSV 리포트 생성"""
    product_files = sorted(TARGET_DIR.glob("products/idx_*.json"))

    csv_path = TARGET_DIR / "CapPump_report.csv"

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = [
            'idx', 'product_name', 'url', 'crawl_status',
            'image_count', 'image_status', 'image_types',
            'print_area_status', 'spec_count', 'spec_status', 'spec_keys',
            'crawled_at', 'json_path'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for product_file in product_files:
            try:
                with open(product_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                idx = data.get('idx', 'unknown')
                product_name = data.get('product_name', 'Unknown Product')
                url = data.get('url', '')

                # 이미지 정보
                images = data.get('downloaded_images', [])
                image_count = len(images)
                image_types = ','.join(set([img.get('type', 'unknown') for img in images]))

                # 인쇄 영역 정보
                print_area_path = data.get('print_area_local_path', '')
                print_area_status = '성공' if print_area_path else '없음'

                # 스펙 정보
                specs = data.get('specifications', {})
                spec_count = len(specs)
                spec_keys = ','.join(specs.keys()) if specs else ''

                crawled_at = data.get('crawled_at', '')

                writer.writerow({
                    'idx': idx,
                    'product_name': product_name,
                    'url': url,
                    'crawl_status': '성공',
                    'image_count': image_count,
                    'image_status': '성공' if image_count > 0 else '없음',
                    'image_types': image_types,
                    'print_area_status': print_area_status,
                    'spec_count': spec_count,
                    'spec_status': '완료' if spec_count > 0 else '없음',
                    'spec_keys': spec_keys,
                    'crawled_at': crawled_at,
                    'json_path': f"products/{product_file.name}"
                })
            except Exception as e:
                print(f"⚠️ 파일 처리 오류 {product_file.name}: {e}")

    print(f"✅ CSV 리포트 생성: {csv_path}")
    print(f"   총 {len(product_files)}개 제품 정보 기록")
    return csv_path

def copy_category_json():
    """카테고리 요약 JSON 복사"""
    category_json = find_category_json()
    if category_json and category_json.exists():
        dst_file = TARGET_DIR / category_json.name
        shutil.copy2(category_json, dst_file)
        print(f"✅ 카테고리 JSON 복사: {category_json.name}")
    else:
        print("⚠️ 카테고리 JSON 파일이 없습니다")

def main():
    print("=" * 60)
    print("Cap&Pump 카테고리 데이터 정리 시작")
    print("=" * 60)

    # 1. 디렉토리 구조 생성
    create_directory_structure()

    # 2. 카테고리 JSON 복사
    copy_category_json()

    # 3. 제품 JSON 파일 복사
    product_count = copy_product_files()

    # 4. 이미지 파일 복사
    image_count = copy_image_files()

    # 5. 인쇄 영역 파일 복사
    print_area_count = copy_print_area_files()

    # 6. CSV 리포트 생성
    csv_path = generate_csv_report()

    print("\n" + "=" * 60)
    print("✅ Cap&Pump 카테고리 데이터 정리 완료")
    print("=" * 60)
    print(f"📁 대상 디렉토리: {TARGET_DIR}")
    print(f"📦 제품 수: {product_count}")
    print(f"🖼️  이미지 수: {image_count}")
    print(f"📄 인쇄 영역: {print_area_count}")
    print(f"📊 CSV 리포트: {csv_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
