#!/usr/bin/env python3
"""
크롤링 결과 CSV 리포트 생성 스크립트
기존 data/crawled_products/ 파일들을 분석해서 상세 리포트 생성
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def analyze_product_json(json_path: Path) -> Dict[str, Any]:
    """제품 JSON 파일 분석"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        idx = data.get('idx', 'unknown')
        product_name = data.get('product_name', 'Unknown')
        url = data.get('url', '')
        crawled_at = data.get('crawled_at', '')

        # 이미지 분석
        downloaded_images = data.get('downloaded_images', [])
        image_count = len(downloaded_images)
        image_types = ','.join(set(img.get('type', 'unknown') for img in downloaded_images))

        if image_count > 0:
            image_status = '성공'
        elif len(data.get('images', [])) > 0:
            image_status = '부분성공'
        else:
            image_status = '실패'

        # 인쇄영역 분석
        if data.get('print_area_local_path'):
            print_area_status = '성공'
        elif data.get('print_area_url'):
            print_area_status = '실패'
        else:
            print_area_status = '없음'

        # 사양 분석
        specifications = data.get('specifications', {})
        spec_count = len(specifications)
        spec_keys = ','.join(specifications.keys()) if specifications else ''
        spec_status = '완료' if spec_count > 0 else '실패'

        return {
            'idx': idx,
            'product_name': product_name,
            'url': url,
            'crawl_status': '성공',
            'image_count': image_count,
            'image_status': image_status,
            'image_types': image_types,
            'print_area_status': print_area_status,
            'spec_count': spec_count,
            'spec_status': spec_status,
            'spec_keys': spec_keys,
            'crawled_at': crawled_at,
            'json_path': str(json_path.relative_to(json_path.parent.parent))
        }

    except Exception as e:
        print(f"⚠️  {json_path.name} 분석 실패: {e}")
        idx = json_path.stem.replace('idx_', '')
        return {
            'idx': idx,
            'product_name': 'ERROR',
            'url': '',
            'crawl_status': '실패',
            'image_count': 0,
            'image_status': '실패',
            'image_types': '',
            'print_area_status': '실패',
            'spec_count': 0,
            'spec_status': '실패',
            'spec_keys': '',
            'crawled_at': '',
            'json_path': str(json_path)
        }


def get_category_from_summary(summary_path: Path) -> str:
    """카테고리 요약 파일에서 카테고리명 추출"""
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('category', 'Unknown')
    except:
        # 파일명에서 추출 시도 (category_Bottle_*.json)
        parts = summary_path.stem.split('_')
        if len(parts) >= 2:
            return parts[1]
        return 'Unknown'


def generate_csv_report(
    crawled_dir: Path,
    output_csv: Path,
    category_name: str = None
):
    """
    크롤링 결과 CSV 리포트 생성

    Args:
        crawled_dir: 크롤링 데이터 디렉토리 (예: data/crawled_products)
        output_csv: 출력 CSV 파일 경로
        category_name: 카테고리명 (None이면 전체)
    """
    print(f"\n{'='*80}")
    print(f"CSV 리포트 생성: {output_csv.name}")
    print(f"{'='*80}")

    # JSON 파일 수집
    json_files = sorted(crawled_dir.glob('idx_*.json'))

    if not json_files:
        print(f"⚠️  JSON 파일이 없습니다: {crawled_dir}")
        return

    print(f"발견된 제품: {len(json_files)}개")

    # 각 제품 분석
    products = []
    for json_path in json_files:
        product_data = analyze_product_json(json_path)
        products.append(product_data)

    # CSV 작성
    fieldnames = [
        'idx',
        'product_name',
        'url',
        'crawl_status',
        'image_count',
        'image_status',
        'image_types',
        'print_area_status',
        'spec_count',
        'spec_status',
        'spec_keys',
        'crawled_at',
        'json_path'
    ]

    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    # 통계
    total = len(products)
    success = sum(1 for p in products if p['crawl_status'] == '성공')
    has_images = sum(1 for p in products if p['image_count'] > 0)
    has_print_area = sum(1 for p in products if p['print_area_status'] == '성공')
    has_specs = sum(1 for p in products if p['spec_count'] > 0)

    print(f"\n✅ CSV 리포트 생성 완료!")
    print(f"   파일: {output_csv}")
    print(f"\n📊 통계:")
    print(f"   총 제품: {total}개")
    print(f"   크롤링 성공: {success}개 ({success/total*100:.1f}%)")
    print(f"   이미지 있음: {has_images}개 ({has_images/total*100:.1f}%)")
    print(f"   인쇄영역 있음: {has_print_area}개 ({has_print_area/total*100:.1f}%)")
    print(f"   사양 정보 있음: {has_specs}개 ({has_specs/total*100:.1f}%)")


def generate_master_report(crawled_dir: Path):
    """
    카테고리별 리포트를 통합한 마스터 리포트 생성

    Args:
        crawled_dir: 크롤링 데이터 디렉토리
    """
    # 카테고리별 요약 파일 찾기
    summary_files = list(crawled_dir.glob('category_*.json'))

    if not summary_files:
        print("⚠️  카테고리 요약 파일을 찾을 수 없습니다")
        return

    # 카테고리별 제품 매핑
    category_products = {}

    for summary_path in summary_files:
        category = get_category_from_summary(summary_path)

        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        results = summary_data.get('results', [])

        for result in results:
            if result.get('status') == 'success':
                idx = result.get('idx')
                if idx:
                    category_products[idx] = category

    # 전체 제품 JSON 수집 및 카테고리 추가
    json_files = sorted(crawled_dir.glob('idx_*.json'))
    products = []

    for json_path in json_files:
        product_data = analyze_product_json(json_path)

        # 카테고리 추가
        idx = product_data['idx']
        category = category_products.get(idx, 'Unknown')
        product_data['category'] = category

        products.append(product_data)

    # CSV 작성 (카테고리 컬럼 추가)
    output_csv = crawled_dir / 'master_report.csv'

    fieldnames = [
        'category',
        'idx',
        'product_name',
        'url',
        'crawl_status',
        'image_count',
        'image_status',
        'image_types',
        'print_area_status',
        'spec_count',
        'spec_status',
        'spec_keys',
        'crawled_at',
        'json_path'
    ]

    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    print(f"\n✅ 마스터 리포트 생성 완료: {output_csv}")

    # 카테고리별 통계
    print(f"\n📊 카테고리별 통계:")
    for category in ['Bottle', 'Jar', 'Cap&Pump', 'Unknown']:
        cat_products = [p for p in products if p['category'] == category]
        if cat_products:
            total = len(cat_products)
            success = sum(1 for p in cat_products if p['crawl_status'] == '성공')
            print(f"   {category:10} - {total:3}개 (성공: {success}/{total})")


def main():
    """메인 실행"""
    crawled_dir = Path('data/crawled_products')

    if not crawled_dir.exists():
        print(f"⚠️  디렉토리가 없습니다: {crawled_dir}")
        return

    # 마스터 리포트 생성
    generate_master_report(crawled_dir)


if __name__ == '__main__':
    main()
