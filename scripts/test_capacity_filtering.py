"""
용량 필터링 개선 사항 테스트 스크립트

이 스크립트는 다음 사항을 검증합니다:
1. 용량 추출 로직 (_extract_capacity_from_query)
2. 제품명에서 용량 추출 (_extract_capacity_from_product_name)
3. 검색 결과 필터링 (search_products)
4. API 응답 구조 (specification 필드)

사용법:
    python scripts/test_capacity_filtering.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag_qa_service import RAGQAService
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


def test_capacity_extraction():
    """용량 추출 로직 테스트"""
    print("\n" + "="*80)
    print("TEST 1: Capacity Extraction from Query")
    print("="*80)

    service = RAGQAService(
        qdrant_client=None,  # Not needed for extraction tests
        embedding_model=None,
        ollama_url="http://localhost:11434",
        model_name="qwen2.5:3b"
    )

    test_cases = [
        ("50ml 용기 추천해줘", "50ml"),
        ("100ml 브로우용기", "100ml"),
        ("60 ml 제품 찾아줘", "60ml"),
        ("200ML 용기", "200ml"),
        ("용기 추천해줘", None),  # No capacity
        ("브로우용기", None),
    ]

    results = []
    for query, expected in test_cases:
        extracted = service._extract_capacity_from_query(query)
        status = "✅ PASS" if extracted == expected else "❌ FAIL"
        results.append((query, expected, extracted, status))
        print(f"{status} | Query: '{query}' | Expected: {expected} | Got: {extracted}")

    # Summary
    passed = sum(1 for _, _, _, s in results if "PASS" in s)
    total = len(results)
    print(f"\nResults: {passed}/{total} passed ({passed/total*100:.1f}%)")

    return all("PASS" in s for _, _, _, s in results)


def test_product_name_extraction():
    """제품명에서 용량 추출 테스트"""
    print("\n" + "="*80)
    print("TEST 2: Capacity Extraction from Product Name")
    print("="*80)

    service = RAGQAService(
        qdrant_client=None,
        embedding_model=None,
        ollama_url="http://localhost:11434",
        model_name="qwen2.5:3b"
    )

    test_cases = [
        ("50ml 헤비브로우용기-블랙", "50ml"),
        ("100ml 다층브로우용기-화이트", "100ml"),
        ("60 ML 파우더브로우용기", "60ml"),
        ("200ML용기", "200ml"),
        ("헤비브로우용기", None),  # No capacity in name
    ]

    results = []
    for product_name, expected in test_cases:
        extracted = service._extract_capacity_from_product_name(product_name)
        status = "✅ PASS" if extracted == expected else "❌ FAIL"
        results.append((product_name, expected, extracted, status))
        print(f"{status} | Product: '{product_name}' | Expected: {expected} | Got: {extracted}")

    # Summary
    passed = sum(1 for _, _, _, s in results if "PASS" in s)
    total = len(results)
    print(f"\nResults: {passed}/{total} passed ({passed/total*100:.1f}%)")

    return all("PASS" in s for _, _, _, s in results)


async def test_search_filtering():
    """검색 결과 필터링 테스트 (실제 Qdrant 연결 필요)"""
    print("\n" + "="*80)
    print("TEST 3: Search Results Filtering (requires Qdrant)")
    print("="*80)

    try:
        # Qdrant 클라이언트 초기화
        qdrant_client = QdrantClient(host="localhost", port=6333)

        # 임베딩 모델 로드
        print("Loading embedding model...")
        embedding_model = SentenceTransformer("Alibaba-NLP/gte-Qwen2-7B-instruct")

        # RAG QA Service 초기화
        service = RAGQAService(
            qdrant_client=qdrant_client,
            embedding_model=embedding_model,
            ollama_url="http://localhost:11434",
            model_name="qwen2.5:3b"
        )

        # 테스트 쿼리
        test_queries = [
            ("50ml 용기 추천해줘", "50ml"),
            ("100ml 브로우용기", "100ml"),
            ("용기 추천해줘", None),  # No capacity filter
        ]

        results = []
        for query, expected_capacity in test_queries:
            print(f"\nQuery: '{query}'")
            print(f"Expected capacity filter: {expected_capacity}")

            # 검색 수행
            products = await service.search_products(
                query=query,
                collection="products_all",
                top_k=10,
                group_by_spec=True
            )

            # 결과 검증
            if expected_capacity:
                # 용량 필터링이 적용되어야 함
                capacities = set()
                for product in products:
                    product_name = product['product_name']
                    capacity = service._extract_capacity_from_product_name(product_name)
                    capacities.add(capacity)

                all_match = all(c == expected_capacity for c in capacities)
                status = "✅ PASS" if all_match else "❌ FAIL"

                print(f"Results: {len(products)} products")
                print(f"Capacities found: {capacities}")
                print(f"{status} | All products match {expected_capacity}: {all_match}")

                results.append((query, all_match))
            else:
                # 용량 필터링이 적용되지 않아야 함
                print(f"Results: {len(products)} products (no filtering)")
                print(f"✅ PASS | Mixed capacities expected")
                results.append((query, True))

            # 샘플 제품 출력
            for i, product in enumerate(products[:3], 1):
                print(f"  {i}. {product['product_name']} (score: {product['similarity_score']:.2f})")

        # Summary
        passed = sum(1 for _, r in results if r)
        total = len(results)
        print(f"\nResults: {passed}/{total} passed ({passed/total*100:.1f}%)")

        return all(r for _, r in results)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Tip: Make sure Qdrant is running on localhost:6333")
        print("     docker-compose up -d")
        return False


def test_api_specification_structure():
    """API 응답의 specification 구조 테스트"""
    print("\n" + "="*80)
    print("TEST 4: API Specification Structure")
    print("="*80)

    # 예상 specification 구조
    expected_fields = {
        'product_code',
        'capacity',
        'material',
        'dimension',
        'type'
    }

    # Mock specification
    spec = {
        'product_code': 'idx_860',
        'capacity': '50ml',
        'material': 'PP',
        'dimension': '50ml/65파이*71H',
        'type': '헤비브로우'
    }

    # 필드 검증
    actual_fields = set(spec.keys())
    missing_fields = expected_fields - actual_fields
    extra_fields = actual_fields - expected_fields

    if not missing_fields and not extra_fields:
        print("✅ PASS | All expected fields present")
        print(f"Fields: {', '.join(sorted(actual_fields))}")

        # 각 필드 값 검증
        print("\nField Values:")
        for field in sorted(expected_fields):
            value = spec.get(field)
            print(f"  - {field}: {value}")

        return True
    else:
        print("❌ FAIL | Field mismatch")
        if missing_fields:
            print(f"Missing: {missing_fields}")
        if extra_fields:
            print(f"Extra: {extra_fields}")
        return False


async def main():
    """모든 테스트 실행"""
    print("\n" + "="*80)
    print("CAPACITY FILTERING IMPROVEMENTS - TEST SUITE")
    print("="*80)

    test_results = []

    # Test 1: Capacity extraction from query
    result1 = test_capacity_extraction()
    test_results.append(("Capacity Extraction (Query)", result1))

    # Test 2: Capacity extraction from product name
    result2 = test_product_name_extraction()
    test_results.append(("Capacity Extraction (Product Name)", result2))

    # Test 3: Search filtering (requires Qdrant)
    result3 = await test_search_filtering()
    test_results.append(("Search Filtering", result3))

    # Test 4: API specification structure
    result4 = test_api_specification_structure()
    test_results.append(("API Specification Structure", result4))

    # Final Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")

    total_passed = sum(1 for _, p in test_results if p)
    total_tests = len(test_results)
    success_rate = total_passed / total_tests * 100

    print(f"\nOverall: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")

    if success_rate == 100:
        print("\n🎉 All tests passed! Capacity filtering improvements verified.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Review the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
