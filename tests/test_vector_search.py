#!/usr/bin/env python3
"""
벡터 검색 기반 프론트엔드 테스트
"""

import json
import time

import requests

BASE_URL = "http://localhost:8000"


def test_vector_qa(query, top_k=5):
    """벡터 기반 Q&A 검색 테스트"""
    print(f"\n{'='*80}")
    print(f"쿼리: {query}")
    print(f"{'='*80}")

    url = f"{BASE_URL}/api/v1/qa/ask"
    payload = {"question": query, "top_k": top_k}

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        print(f"\n상태: {response.status_code}")
        print(f"신뢰도: {data.get('confidence', 'N/A'):.2f}")
        print(f"\n답변:")
        print(data.get("answer", "N/A"))

        print(f"\n추천 제품 ({len(data.get('related_products', []))}개):")
        for i, product in enumerate(data.get("related_products", [])[:5], 1):
            print(f"\n{i}. {product.get('product_name')}")
            print(f"   제품 코드: {product.get('product_id')}")
            print(f"   용량: {product.get('capacity')}")
            if product.get("price"):
                print(f"   가격: {product.get('price')}원")

        return data
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def test_product_with_details(query):
    """제품 상세 정보까지 조회하는 테스트"""
    qa_data = test_vector_qa(query, top_k=3)

    if qa_data and qa_data.get("related_products"):
        product_id = qa_data["related_products"][0].get("product_id")

        print(f"\n{'='*80}")
        print(f"첫 번째 제품 상세 조회: {product_id}")
        print(f"{'='*80}")

        url = f"{BASE_URL}/api/v1/products/{product_id}"
        try:
            response = requests.get(url)
            detail = response.json()

            print(f"\n제품명: {detail.get('product_name')}")

            spec = detail.get("specification", {})
            print(f"\n사양:")
            print(f"  - 제품 코드: {spec.get('product_code')}")
            print(f"  - 용량: {spec.get('capacity')}")
            print(f"  - 재질: {spec.get('material')}")
            print(f"  - 크기: {spec.get('dimension')}")
            print(f"  - 종류: {spec.get('type')}")

            price = detail.get("price", {})
            print(f"\n가격:")
            print(f"  - {price.get('primary_price_label')}: {price.get('primary_price')}원")
            if price.get("discount_price"):
                print(f"  - 할인가: {price.get('discount_price')}원")

            print(f"\nMOQ: {detail.get('moq', 'N/A')}")

        except Exception as e:
            print(f"❌ 오류: {e}")


def main():
    print("\n" + "=" * 80)
    print("벡터 검색 기반 프론트엔드 테스트")
    print("=" * 80)

    # API 서버 준비 대기
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/static/qa_chat.html")
            print("✅ API 서버 준비 완료")
            break
        except:
            if i < 9:
                print(f"⏳ API 서버 준비 중... ({i+1}/10)")
                time.sleep(1)
            else:
                print("❌ API 서버 연결 실패")
                return

    # 테스트 쿼리들
    test_queries = [
        "50ml 용기 추천해줘",
        "작은 용기",
        "투명한 병",
        "PE 소재 용기",
        "30ml 브로우용기",
    ]

    # 각 쿼리로 테스트
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#'*80}")
        print(f"테스트 {i}/{len(test_queries)}")
        print(f"{'#'*80}")

        if i == 1:
            # 첫 번째 쿼리는 상세 조회까지 포함
            test_product_with_details(query)
        else:
            test_vector_qa(query)

        time.sleep(0.5)

    print(f"\n\n{'='*80}")
    print("✅ 모든 테스트 완료!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
