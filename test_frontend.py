#!/usr/bin/env python3
"""
프론트엔드 테스트 스크립트
- 검색 API 테스트
- 제품 상세 조회 테스트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_qa_search(query):
    """Q&A 검색 테스트"""
    print(f"\n{'='*80}")
    print(f"테스트: {query}")
    print(f"{'='*80}")

    url = f"{BASE_URL}/api/v1/qa/ask"
    payload = {"question": query, "top_k": 5}

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        print(f"\n상태: {response.status_code}")
        print(f"답변: {data.get('answer', 'N/A')}")
        print(f"신뢰도: {data.get('confidence', 'N/A')}")
        print(f"\n추천 제품 ({len(data.get('related_products', []))}개):")

        for i, product in enumerate(data.get('related_products', [])[:3], 1):
            print(f"  {i}. {product.get('product_name')} - {product.get('price')}원")
            print(f"     코드: {product.get('product_id')}")

        return data
    except Exception as e:
        print(f"오류: {e}")
        return None

def test_product_detail(product_id):
    """제품 상세 정보 조회 테스트"""
    print(f"\n{'='*80}")
    print(f"제품 상세: {product_id}")
    print(f"{'='*80}")

    url = f"{BASE_URL}/api/v1/products/{product_id}"

    try:
        response = requests.get(url)
        data = response.json()

        print(f"\n상태: {response.status_code}")
        print(f"제품명: {data.get('product_name', 'N/A')}")
        print(f"카테고리: {data.get('category', 'N/A')}")

        spec = data.get('specification', {})
        print(f"\n사양:")
        print(f"  - 제품 코드: {spec.get('product_code')}")
        print(f"  - 용량: {spec.get('capacity')}")
        print(f"  - 재질: {spec.get('material')}")
        print(f"  - 크기: {spec.get('dimension')}")

        price = data.get('price', {})
        print(f"\n가격:")
        print(f"  - 정상가: {price.get('primary_price')}원 ({price.get('primary_price_label')})")
        if price.get('discount_price'):
            print(f"  - 할인가: {price.get('discount_price')}원")

        print(f"\nMOQ: {data.get('moq', 'N/A')}")
        print(f"이미지: {data.get('image_url', 'N/A')}")

        return data
    except Exception as e:
        print(f"오류: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("RAG Enterprise 프론트엔드 테스트")
    print("="*80)

    # 테스트 1: 20ml 용기 검색
    qa_data_1 = test_qa_search("20ml 용기 추천해줘")

    # 첫 번째 제품 상세 조회
    if qa_data_1 and qa_data_1.get('related_products'):
        product_id = qa_data_1['related_products'][0].get('product_id')
        test_product_detail(product_id)

    # 테스트 2: 30ml 용기 검색
    qa_data_2 = test_qa_search("30ml 용기 추천해줘")

    # 두 번째 제품 상세 조회
    if qa_data_2 and qa_data_2.get('related_products'):
        product_id = qa_data_2['related_products'][0].get('product_id')
        test_product_detail(product_id)

    # 테스트 3: 직접 제품 ID로 조회
    test_product_detail("idx_68")
    test_product_detail("idx_439")
    test_product_detail("idx_660")

    print(f"\n{'='*80}")
    print("테스트 완료")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
