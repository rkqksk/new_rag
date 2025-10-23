#!/usr/bin/env python3
"""
배치 작업: Bottle 제품 JSON 파일에 대해
1. 사양(specification)에서 Ø 표기 제거
2. MOQ 필드 추가 (10,000개)
"""

import json
import os
import re
import glob
from pathlib import Path
from datetime import datetime

def remove_diameter_notation(text):
    """
    사양 텍스트에서 Ø 표기 제거
    예: "30x69(mm)/Ø20" -> "30x69(mm)"
    """
    if not text:
        return text

    # /Ø 뒤의 숫자 제거
    cleaned = re.sub(r'/Ø\d+', '', text)
    return cleaned.strip()

def process_product_file(file_path):
    """
    개별 제품 파일 처리
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        original_data = json.dumps(data, ensure_ascii=False, indent=2)

        # specifications에서 사양 필드 정리
        specs = data.get('specifications', {})
        if '사양' in specs and specs['사양']:
            specs['사양'] = remove_diameter_notation(specs['사양'])

        # MOQ 추가 (없으면)
        if 'moq' not in specs:
            specs['moq'] = '10,000개'

        data['specifications'] = specs

        # 파일에 쓰기
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 변경 여부 확인
        new_data = json.dumps(data, ensure_ascii=False, indent=2)
        changed = original_data != new_data

        return {
            'status': 'success',
            'changed': changed,
            'moq_added': 'moq' not in json.loads(original_data).get('specifications', {})
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def main():
    base_path = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle"

    # Bottle 제품 JSON 파일만 찾기
    product_files = glob.glob(f"{base_path}/**/products/*.json", recursive=True)

    print(f"Bottle 제품: {len(product_files)}개 파일 발견")
    print(f"처리 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    stats = {
        'total': len(product_files),
        'processed': 0,
        'changed': 0,
        'moq_added': 0,
        'errors': 0,
        'errors_list': []
    }

    for i, file_path in enumerate(product_files, 1):
        result = process_product_file(file_path)

        if result['status'] == 'success':
            stats['processed'] += 1
            if result['changed']:
                stats['changed'] += 1
            if result['moq_added']:
                stats['moq_added'] += 1
        else:
            stats['errors'] += 1
            stats['errors_list'].append({
                'file': file_path,
                'error': result['error']
            })

        # 진행률 표시 (50개마다)
        if i % 50 == 0:
            print(f"처리 중: {i}/{len(product_files)} ({100*i//len(product_files)}%)")

    print("-" * 80)
    print(f"처리 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n결과 요약:")
    print(f"  총 파일: {stats['total']}")
    print(f"  성공: {stats['processed']}")
    print(f"  변경됨: {stats['changed']}")
    print(f"  MOQ 추가됨: {stats['moq_added']}")
    print(f"  오류: {stats['errors']}")

    if stats['errors_list']:
        print(f"\n오류 목록:")
        for error in stats['errors_list'][:5]:
            print(f"  - {error['file']}: {error['error']}")

    return stats

if __name__ == "__main__":
    stats = main()
