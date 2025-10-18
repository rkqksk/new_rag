#!/usr/bin/env python3
"""재크롤링 진행 상황 실시간 체크"""

import json
import sys
from pathlib import Path
from datetime import datetime

def check_progress():
    """진행 상황 확인"""

    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "crawled_products_updated"

    print("="*80)
    print("재크롤링 진행 상황 체크")
    print("="*80)
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not data_dir.exists():
        print("⚠️  data/crawled_products_updated 디렉토리가 아직 생성되지 않았습니다.")
        print("   크롤러가 시작 중이거나 아직 실행되지 않았습니다.")
        return

    # JSON 파일 개수
    json_files = list(data_dir.glob("idx_*.json"))
    json_count = len(json_files)

    # 이미지 파일
    images_dir = data_dir / "images"
    img_count = len(list(images_dir.glob("*.jpg"))) if images_dir.exists() else 0

    # PDF 파일
    pdf_dir = data_dir / "print_area"
    pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0

    # 목표
    target = 398
    progress = (json_count / target * 100) if target > 0 else 0

    print(f"📊 통계:")
    print(f"  - JSON 파일: {json_count}개")
    print(f"  - 이미지 파일: {img_count}개")
    print(f"  - PDF 파일: {pdf_count}개")
    print(f"  - 진행률: {progress:.1f}% ({json_count}/{target})")
    print()

    # 최근 크롤링된 제품 확인
    if json_files:
        # 최신 5개 파일
        recent_files = sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]

        print(f"📝 최근 크롤링된 제품 (최신 5개):")
        for i, json_file in enumerate(recent_files, 1):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                product_name = data.get('product_name', 'Unknown')
                spec_count = len(data.get('specifications', {}))
                img_count_product = len(data.get('images', []))

                print(f"  {i}. {json_file.stem}")
                print(f"     제품명: {product_name}")
                print(f"     스펙: {spec_count}개, 이미지: {img_count_product}개")

            except Exception as e:
                print(f"  {i}. {json_file.stem} (읽기 실패: {e})")

        print()

    # 요약 파일 확인
    summary_files = list(data_dir.glob("*.json"))
    summary_files = [f for f in summary_files if not f.stem.startswith("idx_")]

    if summary_files:
        print(f"📄 요약 파일:")
        for summary_file in summary_files:
            print(f"  - {summary_file.name}")
        print()

    # 카테고리별 진행 상황 (카테고리 요약 파일이 있는 경우)
    category_summaries = list(data_dir.glob("category_*.json"))

    if category_summaries:
        print(f"📦 카테고리별 진행 상황:")
        for cat_file in category_summaries:
            try:
                with open(cat_file, 'r', encoding='utf-8') as f:
                    cat_data = json.load(f)

                cat_name = cat_data.get('category', 'Unknown')
                total = cat_data.get('total_products', 0)
                success = cat_data.get('success', 0)
                error = cat_data.get('error', 0)

                print(f"  - {cat_name}: {success}/{total}개 성공 ({error}개 실패)")

            except Exception as e:
                print(f"  - {cat_file.name} (읽기 실패)")

        print()

    print("="*80)
    print(f"💡 Tip: 실시간 모니터링은 scripts/crawlers/monitor_recrawl.sh 실행")
    print("="*80)

if __name__ == "__main__":
    check_progress()
