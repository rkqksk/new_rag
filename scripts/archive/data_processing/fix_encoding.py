#!/usr/bin/env python3
"""
인코딩 깨진 제품 데이터 수정
- UTF-8로 잘못 저장된 EUC-KR 텍스트 복원
"""
import json
import os
from pathlib import Path

def fix_encoding(text):
    """깨진 인코딩 복원 시도"""
    if not isinstance(text, str):
        return text

    try:
        # UTF-8로 잘못 저장된 EUC-KR 복원 시도
        # 방법 1: UTF-8 → bytes → EUC-KR
        restored = text.encode('latin1').decode('euc-kr')
        return restored
    except:
        try:
            # 방법 2: CP949 시도
            restored = text.encode('latin1').decode('cp949')
            return restored
        except:
            # 복원 실패 → 원본 반환
            return text

def fix_specifications(specs):
    """specifications 딕셔너리의 모든 값 수정"""
    if not isinstance(specs, dict):
        return specs

    fixed = {}
    for key, value in specs.items():
        fixed_key = fix_encoding(key)
        fixed_value = fix_encoding(value) if isinstance(value, str) else value
        fixed[fixed_key] = fixed_value

    return fixed

def fix_product_data(product):
    """제품 데이터의 모든 필드 수정"""
    fixed = product.copy()

    # specifications 수정
    if 'specifications' in fixed:
        fixed['specifications'] = fix_specifications(fixed['specifications'])

    # 기타 텍스트 필드 수정
    text_fields = ['product_name', 'category_name', 'manufacturer', 'phone',
                   'fax', 'email', 'contact']
    for field in text_fields:
        if field in fixed and isinstance(fixed[field], str):
            fixed[field] = fix_encoding(fixed[field])

    return fixed

def main():
    """메인 실행 함수"""
    input_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_complete.json'
    output_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_complete_fixed.json'

    print("🔧 인코딩 수정 시작...")
    print(f"입력: {input_file}")
    print(f"출력: {output_file}")
    print()

    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"📊 총 {len(products):,}개 제품 처리 중...")

    # 인코딩 수정
    fixed_products = []
    fixed_count = 0

    for i, product in enumerate(products):
        fixed = fix_product_data(product)

        # 수정 여부 확인
        if json.dumps(fixed, ensure_ascii=False) != json.dumps(product, ensure_ascii=False):
            fixed_count += 1

        fixed_products.append(fixed)

        if (i + 1) % 100 == 0:
            print(f"진행: {i + 1}/{len(products)} ({fixed_count} 수정됨)")

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_products, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 완료!")
    print(f"   - 총 제품: {len(fixed_products):,}개")
    print(f"   - 수정됨: {fixed_count:,}개")
    print(f"   - 출력: {output_file}")
    print()

    # 수정 전후 비교 (샘플)
    print("📝 수정 예시 (product_id: 40934):")
    for p in fixed_products:
        if p.get('product_id') == '40934':
            print("수정 후:")
            specs = p.get('specifications', {})
            for key in list(specs.keys())[:3]:
                print(f"  - {key}: {specs[key]}")
            break

if __name__ == '__main__':
    main()
