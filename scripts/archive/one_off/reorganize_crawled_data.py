#!/usr/bin/env python3
"""
크롤링 데이터 재구조화 스크립트
기존 data/crawled_products/ 파일들을 카테고리별 디렉토리로 재구성
"""

import json
import shutil
from pathlib import Path
from typing import Dict


def get_category_mapping(source_dir: Path) -> Dict[str, str]:
    """
    카테고리 요약 파일에서 idx → 카테고리 매핑 추출

    Returns:
        Dict[idx, category_name]
    """
    mapping = {}

    summary_files = list(source_dir.glob('category_*.json'))

    for summary_file in summary_files:
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            category = data.get('category', 'Unknown')
            results = data.get('results', [])

            for result in results:
                if result.get('status') == 'success':
                    idx = result.get('idx')
                    if idx:
                        mapping[idx] = category

        except Exception as e:
            print(f"⚠️  {summary_file.name} 처리 실패: {e}")

    return mapping


def create_category_structure(base_dir: Path, categories: list):
    """카테고리별 디렉토리 구조 생성"""
    for category in categories:
        # Cap&Pump는 파일시스템에서 Cap_Pump로 저장
        safe_category = category.replace('&', '_')
        category_dir = base_dir / safe_category

        # 서브 디렉토리 생성
        (category_dir / 'products').mkdir(parents=True, exist_ok=True)
        (category_dir / 'images').mkdir(parents=True, exist_ok=True)
        (category_dir / 'print_area').mkdir(parents=True, exist_ok=True)

        print(f"✅ 디렉토리 생성: {category_dir}")


def reorganize_files(source_dir: Path, target_dir: Path, idx_category_map: Dict[str, str]):
    """
    파일들을 카테고리별로 재구성

    Args:
        source_dir: 기존 data/crawled_products
        target_dir: 새로운 data/crawled_products_organized
        idx_category_map: idx → category 매핑
    """
    print(f"\n{'='*80}")
    print(f"파일 재구성 시작")
    print(f"{'='*80}")

    # 통계
    stats = {
        'products': 0,
        'images': 0,
        'print_area': 0,
        'unknown': 0
    }

    # 1. 제품 JSON 파일 이동
    print(f"\n[1/3] 제품 JSON 파일 이동 중...")
    json_files = list(source_dir.glob('idx_*.json'))

    for json_file in json_files:
        idx = json_file.stem.replace('idx_', '')
        category = idx_category_map.get(idx, 'Unknown')

        if category == 'Unknown':
            stats['unknown'] += 1
            continue

        safe_category = category.replace('&', '_')
        target_path = target_dir / safe_category / 'products' / json_file.name

        shutil.copy2(json_file, target_path)
        stats['products'] += 1

    print(f"   ✓ {stats['products']}개 제품 JSON 이동 완료")

    # 2. 이미지 파일 이동
    print(f"\n[2/3] 이미지 파일 이동 중...")
    image_dir = source_dir / 'images'

    if image_dir.exists():
        for image_file in image_dir.glob('idx_*'):
            # 파일명에서 idx 추출 (idx_417_main_1.jpg → 417)
            parts = image_file.stem.split('_')
            if len(parts) >= 2:
                idx = parts[1]
                category = idx_category_map.get(idx, 'Unknown')

                if category == 'Unknown':
                    continue

                safe_category = category.replace('&', '_')
                target_path = target_dir / safe_category / 'images' / image_file.name

                shutil.copy2(image_file, target_path)
                stats['images'] += 1

    print(f"   ✓ {stats['images']}개 이미지 이동 완료")

    # 3. 인쇄영역 PDF 파일 이동
    print(f"\n[3/3] 인쇄영역 PDF 파일 이동 중...")
    print_dir = source_dir / 'print_area'

    if print_dir.exists():
        for pdf_file in print_dir.glob('idx_*_print_area.pdf'):
            # 파일명에서 idx 추출
            parts = pdf_file.stem.split('_')
            if len(parts) >= 2:
                idx = parts[1]
                category = idx_category_map.get(idx, 'Unknown')

                if category == 'Unknown':
                    continue

                safe_category = category.replace('&', '_')
                target_path = target_dir / safe_category / 'print_area' / pdf_file.name

                shutil.copy2(pdf_file, target_path)
                stats['print_area'] += 1

    print(f"   ✓ {stats['print_area']}개 인쇄영역 PDF 이동 완료")

    # 통계 출력
    print(f"\n{'='*80}")
    print(f"재구성 완료!")
    print(f"{'='*80}")
    print(f"제품 JSON: {stats['products']}개")
    print(f"이미지: {stats['images']}개")
    print(f"인쇄영역 PDF: {stats['print_area']}개")
    print(f"카테고리 미분류: {stats['unknown']}개")


def generate_category_reports(target_dir: Path, categories: list):
    """각 카테고리별 CSV 리포트 생성"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from generate_crawl_report import generate_csv_report

    print(f"\n{'='*80}")
    print(f"카테고리별 CSV 리포트 생성")
    print(f"{'='*80}")

    for category in categories:
        safe_category = category.replace('&', '_')
        category_dir = target_dir / safe_category

        if not category_dir.exists():
            continue

        output_csv = category_dir / f"{safe_category}_report.csv"

        generate_csv_report(
            crawled_dir=category_dir / 'products',
            output_csv=output_csv,
            category_name=category
        )


def main():
    """메인 실행"""
    source_dir = Path('data/crawled_products')
    target_dir = Path('data/crawled_products_organized')

    if not source_dir.exists():
        print(f"⚠️  소스 디렉토리가 없습니다: {source_dir}")
        return

    print(f"\n{'='*80}")
    print(f"크롤링 데이터 재구조화")
    print(f"{'='*80}")
    print(f"소스: {source_dir}")
    print(f"타겟: {target_dir}")

    # 1. idx → 카테고리 매핑 추출
    print(f"\n[Step 1] 카테고리 매핑 추출 중...")
    idx_category_map = get_category_mapping(source_dir)
    print(f"✓ {len(idx_category_map)}개 제품의 카테고리 매핑 완료")

    # 카테고리 목록
    categories = sorted(set(idx_category_map.values()))
    print(f"✓ 발견된 카테고리: {', '.join(categories)}")

    # 2. 카테고리별 디렉토리 구조 생성
    print(f"\n[Step 2] 디렉토리 구조 생성 중...")
    create_category_structure(target_dir, categories)

    # 3. 파일 재구성
    print(f"\n[Step 3] 파일 재구성 중...")
    reorganize_files(source_dir, target_dir, idx_category_map)

    # 4. 카테고리별 CSV 리포트 생성
    print(f"\n[Step 4] CSV 리포트 생성 중...")
    generate_category_reports(target_dir, categories)

    print(f"\n{'='*80}")
    print(f"✅ 재구조화 완료!")
    print(f"{'='*80}")
    print(f"새로운 구조: {target_dir}")
    print(f"\n다음 단계:")
    print(f"1. 재구성된 데이터 확인: ls -R {target_dir}")
    print(f"2. CSV 리포트 확인: open {target_dir}/*/")
    print(f"3. 문제 없으면 기존 디렉토리 교체:")
    print(f"   mv {source_dir} {source_dir}_backup")
    print(f"   mv {target_dir} {source_dir}")


if __name__ == '__main__':
    main()
