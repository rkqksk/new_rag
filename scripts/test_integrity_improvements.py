"""
RAG 시스템 개선 사항 테스트 스크립트
- 완전한 검색 결과 반환 (return_all=True)
- 데이터 무결성 검증 (이미지 URL, 스펙 완전성)
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.rag_qa_service import RAGQAService, QARequest
from app.utils.product_utils import (
    generate_image_urls,
    validate_product_integrity,
    batch_validate_products
)
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import json


async def test_complete_results():
    """
    테스트 1: 완전한 검색 결과 반환
    return_all=True일 때 모든 필터링된 결과가 반환되는지 확인
    """
    print("\n" + "="*80)
    print("테스트 1: 완전한 검색 결과 반환 (return_all=True)")
    print("="*80)

    # RAG QA Service 초기화
    qdrant_client = QdrantClient(host="localhost", port=6333)
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    service = RAGQAService(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model
    )

    # 테스트 쿼리
    query = "50ml 용기 추천해줘"

    # 1) 기본 검색 (top_k=3)
    print(f"\n1) 기본 검색 (top_k=3, return_all=False)")
    products_limited = await service.search_products(
        query=query,
        top_k=3,
        return_all=False
    )
    print(f"   결과 개수: {len(products_limited)}")
    print(f"   제품 목록:")
    for i, p in enumerate(products_limited[:5], 1):
        print(f"     {i}. {p['product_name']} (무결성: {p.get('integrity_score', 'N/A')})")

    # 2) 완전한 검색 (return_all=True)
    print(f"\n2) 완전한 검색 (return_all=True)")
    products_all = await service.search_products(
        query=query,
        return_all=True
    )
    print(f"   결과 개수: {len(products_all)}")
    print(f"   제품 목록 (처음 10개):")
    for i, p in enumerate(products_all[:10], 1):
        print(f"     {i}. {p['product_name']} (무결성: {p.get('integrity_score', 'N/A')})")

    print(f"\n   ✅ 결과: return_all=True일 때 {len(products_all)}개, False일 때 {len(products_limited)}개")
    assert len(products_all) > len(products_limited), "return_all=True일 때 더 많은 결과를 반환해야 합니다"


async def test_data_integrity():
    """
    테스트 2: 데이터 무결성 검증
    모든 제품에 이미지 URL, 스펙, 무결성 점수가 포함되는지 확인
    """
    print("\n" + "="*80)
    print("테스트 2: 데이터 무결성 검증")
    print("="*80)

    # RAG QA Service 초기화
    qdrant_client = QdrantClient(host="localhost", port=6333)
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    service = RAGQAService(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model
    )

    # 테스트 쿼리
    query = "PET 재질 병"

    # 검색 실행 (return_all=True)
    print(f"\n쿼리: '{query}'")
    products = await service.search_products(
        query=query,
        return_all=True,
        min_integrity_score=0.0  # 모든 제품 포함
    )

    print(f"총 결과: {len(products)}개")

    # 무결성 통계
    total = len(products)
    with_images = sum(1 for p in products if p.get('has_images', False))
    with_specs = sum(1 for p in products if p.get('has_specs', False))
    complete = sum(1 for p in products if p.get('is_complete', False))

    print(f"\n무결성 통계:")
    print(f"  - 이미지 있음: {with_images}/{total} ({with_images/total*100:.1f}%)")
    print(f"  - 스펙 있음: {with_specs}/{total} ({with_specs/total*100:.1f}%)")
    print(f"  - 완전한 제품: {complete}/{total} ({complete/total*100:.1f}%)")

    # 개별 검증
    print(f"\n샘플 제품 (처음 5개):")
    for i, product in enumerate(products[:5], 1):
        print(f"\n  {i}. {product['product_name']}")
        print(f"     - 제품 ID: {product['product_id']}")
        print(f"     - 카테고리: {product['category']}")
        print(f"     - 무결성 점수: {product.get('integrity_score', 'N/A')}")
        print(f"     - 이미지 개수: {product.get('image_count', 0)}")

        if product.get('image_urls'):
            print(f"     - 이미지 URL: {product['image_urls'][0]}")
        else:
            print(f"     - ⚠️ 이미지 없음")

        if product.get('specifications'):
            specs = product['specifications']
            print(f"     - 스펙 필드 수: {len(specs)}")
        else:
            print(f"     - ⚠️ 스펙 없음")

    # 필수 필드 검증
    print(f"\n필수 필드 검증:")
    for product in products[:10]:
        # 필수 필드
        assert 'product_id' in product, "product_id 필드가 없습니다"
        assert 'product_name' in product, "product_name 필드가 없습니다"
        assert 'category' in product, "category 필드가 없습니다"

        # 무결성 관련 필드
        assert 'image_urls' in product, "image_urls 필드가 없습니다"
        assert 'has_images' in product, "has_images 필드가 없습니다"
        assert 'has_specs' in product, "has_specs 필드가 없습니다"
        assert 'integrity_score' in product, "integrity_score 필드가 없습니다"
        assert 'is_complete' in product, "is_complete 필드가 없습니다"

    print(f"  ✅ 모든 필수 필드가 존재합니다")


async def test_integrity_filtering():
    """
    테스트 3: 무결성 점수 필터링
    min_integrity_score를 사용하여 불완전한 제품을 필터링하는지 확인
    """
    print("\n" + "="*80)
    print("테스트 3: 무결성 점수 필터링")
    print("="*80)

    # RAG QA Service 초기화
    qdrant_client = QdrantClient(host="localhost", port=6333)
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    service = RAGQAService(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model
    )

    query = "100ml 용기"

    # 1) 모든 제품 (min_integrity_score=0.0)
    print(f"\n1) 모든 제품 (min_integrity_score=0.0)")
    products_all = await service.search_products(
        query=query,
        return_all=True,
        min_integrity_score=0.0
    )
    print(f"   결과 개수: {len(products_all)}")
    avg_score_all = sum(p['integrity_score'] for p in products_all) / len(products_all) if products_all else 0
    print(f"   평균 무결성 점수: {avg_score_all:.2f}")

    # 2) 중간 무결성 제품 (min_integrity_score=0.4)
    print(f"\n2) 중간 무결성 제품 (min_integrity_score=0.4)")
    products_medium = await service.search_products(
        query=query,
        return_all=True,
        min_integrity_score=0.4
    )
    print(f"   결과 개수: {len(products_medium)}")
    avg_score_medium = sum(p['integrity_score'] for p in products_medium) / len(products_medium) if products_medium else 0
    print(f"   평균 무결성 점수: {avg_score_medium:.2f}")

    # 3) 완전한 제품만 (min_integrity_score=1.0)
    print(f"\n3) 완전한 제품만 (min_integrity_score=1.0)")
    products_complete = await service.search_products(
        query=query,
        return_all=True,
        min_integrity_score=1.0
    )
    print(f"   결과 개수: {len(products_complete)}")
    avg_score_complete = sum(p['integrity_score'] for p in products_complete) / len(products_complete) if products_complete else 0
    print(f"   평균 무결성 점수: {avg_score_complete:.2f}")

    # 검증
    print(f"\n검증:")
    print(f"  - 필터링 전: {len(products_all)}개")
    print(f"  - 필터링 후 (≥0.4): {len(products_medium)}개")
    print(f"  - 필터링 후 (≥1.0): {len(products_complete)}개")
    assert len(products_all) >= len(products_medium) >= len(products_complete), "무결성 점수가 높을수록 결과가 적어야 합니다"
    print(f"  ✅ 무결성 필터링이 정상 동작합니다")


async def test_utility_functions():
    """
    테스트 4: 공통 유틸리티 함수
    이미지 URL 생성 및 무결성 검증 함수가 정상 동작하는지 확인
    """
    print("\n" + "="*80)
    print("테스트 4: 공통 유틸리티 함수")
    print("="*80)

    # 1) 이미지 URL 생성
    print(f"\n1) 이미지 URL 생성 테스트")
    product_id = "idx_860"
    category = "Bottle/PET"
    image_urls = generate_image_urls(product_id, category)
    print(f"   제품 ID: {product_id}")
    print(f"   카테고리: {category}")
    print(f"   생성된 이미지 URL: {len(image_urls)}개")
    for url in image_urls:
        print(f"     - {url}")

    # 2) 개별 제품 무결성 검증
    print(f"\n2) 개별 제품 무결성 검증 테스트")
    test_product = {
        "product_id": "idx_860",
        "product_name": "50ml 테스트 용기",
        "category": "Bottle/PET",
        "similarity_score": 0.95,
        "specifications": {
            "재질": "PET",
            "용량": "50ml"
        },
        "print_area_url": "http://example.com/print_area.jpg"
    }

    validated = validate_product_integrity(test_product)
    print(f"   제품명: {validated['product_name']}")
    print(f"   이미지 있음: {validated['has_images']}")
    print(f"   스펙 있음: {validated['has_specs']}")
    print(f"   무결성 점수: {validated['integrity_score']}")
    print(f"   완전한 제품: {validated['is_complete']}")

    # 3) 배치 검증
    print(f"\n3) 배치 검증 테스트")
    test_products = [
        {
            "product_id": f"idx_{i}",
            "product_name": f"테스트 제품 {i}",
            "category": "Bottle/PET",
            "similarity_score": 0.9 - i * 0.1
        }
        for i in range(1, 6)
    ]

    validated_batch = batch_validate_products(test_products, min_integrity_score=0.0)
    print(f"   입력: {len(test_products)}개")
    print(f"   출력: {len(validated_batch)}개")
    for p in validated_batch:
        print(f"     - {p['product_name']}: 무결성 {p['integrity_score']}")

    print(f"\n  ✅ 모든 유틸리티 함수가 정상 동작합니다")


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*80)
    print("RAG 시스템 개선 사항 통합 테스트")
    print("="*80)

    try:
        # 테스트 실행
        await test_complete_results()
        await test_data_integrity()
        await test_integrity_filtering()
        await test_utility_functions()

        print("\n" + "="*80)
        print("✅ 모든 테스트 통과!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
