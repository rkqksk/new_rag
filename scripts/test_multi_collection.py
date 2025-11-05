#!/usr/bin/env python3
"""
Multi-Collection Routing 통합 테스트

테스트 레벨:
    Level 1: Skill 컴포넌트 테스트
    Level 2: CollectionManager 테스트
    Level 3: 멀티 컬렉션 검색 테스트
    Level 4: API 통합 테스트

Usage:
    python3 scripts/test_multi_collection.py --level 1
    python3 scripts/test_multi_collection.py --level all
"""
import sys
from pathlib import Path
import json

# Add project root and skill path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
skill_path = project_root / '.claude/skills/rag-pipeline/scripts'
sys.path.insert(0, str(skill_path))

from skill import (
    list_collections,
    get_collection_stats,
    vector_search,
    execute
)
from collection_manager import get_collection_manager


# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(name):
    """Print test name"""
    print(f"\n{BLUE}[TEST]{RESET} {name}")


def print_pass(message):
    """Print pass message"""
    print(f"  {GREEN}✅ PASS:{RESET} {message}")


def print_fail(message):
    """Print fail message"""
    print(f"  {RED}❌ FAIL:{RESET} {message}")


def print_info(message):
    """Print info message"""
    print(f"  {YELLOW}ℹ️  INFO:{RESET} {message}")


def test_level_1_collection_manager():
    """Level 1: CollectionManager 기본 기능 테스트"""
    print(f"\n{YELLOW}{'='*80}")
    print("LEVEL 1: CollectionManager 컴포넌트 테스트")
    print(f"{'='*80}{RESET}\n")

    # Test 1: CollectionManager 초기화
    print_test("CollectionManager 초기화")
    try:
        manager = get_collection_manager()
        print_pass("CollectionManager 싱글톤 생성 성공")
    except Exception as e:
        print_fail(f"초기화 실패: {e}")
        return False

    # Test 2: get_collection() - chungjinkorea
    print_test("get_collection() - chungjinkorea")
    try:
        col = manager.get_collection('chungjinkorea')
        assert col is not None, "chungjinkorea not found"
        assert col['enabled'] == True, "chungjinkorea not enabled"
        assert col['embedded'] == True, "chungjinkorea not embedded"
        print_pass(f"chungjinkorea 메타데이터 조회 성공: {col['name']}")
    except Exception as e:
        print_fail(f"조회 실패: {e}")
        return False

    # Test 3: get_collection() - onehago
    print_test("get_collection() - onehago")
    try:
        col = manager.get_collection('onehago')
        assert col is not None, "onehago not found"
        assert col['enabled'] == True, "onehago not enabled"
        assert col['embedded'] == True, "onehago not embedded"
        assert col['total_documents'] == 22871, "onehago document count mismatch"
        print_pass(f"onehago 메타데이터 조회 성공: {col['total_documents']} docs")
    except Exception as e:
        print_fail(f"조회 실패: {e}")
        return False

    # Test 4: get_collection_name()
    print_test("get_collection_name() - collection ID → Qdrant name")
    try:
        name1 = manager.get_collection_name('chungjinkorea')
        name2 = manager.get_collection_name('onehago')
        assert name1 == 'products', f"chungjinkorea should map to 'products', got {name1}"
        assert name2 == 'onehago', f"onehago should map to 'onehago', got {name2}"
        print_pass(f"chungjinkorea → {name1}, onehago → {name2}")
    except Exception as e:
        print_fail(f"매핑 실패: {e}")
        return False

    # Test 5: validate_collections()
    print_test("validate_collections() - 유효한 컬렉션 필터링")
    try:
        valid = manager.validate_collections(['chungjinkorea', 'onehago', 'freemold'])
        assert 'chungjinkorea' in valid, "chungjinkorea should be valid"
        assert 'onehago' in valid, "onehago should be valid"
        assert 'freemold' not in valid, "freemold should not be valid (not embedded)"
        print_pass(f"유효한 컬렉션: {valid}")
    except Exception as e:
        print_fail(f"검증 실패: {e}")
        return False

    # Test 6: get_active_collections()
    print_test("get_active_collections() - 활성 컬렉션 조회")
    try:
        active = manager.get_active_collections()
        assert 'chungjinkorea' in active, "chungjinkorea should be active"
        assert 'onehago' in active, "onehago should be active"
        print_pass(f"활성 컬렉션: {active}")
    except Exception as e:
        print_fail(f"조회 실패: {e}")
        return False

    print(f"\n{GREEN}✅ Level 1 테스트 통과{RESET}")
    return True


def test_level_2_skill_commands():
    """Level 2: Skill 명령어 테스트"""
    print(f"\n{YELLOW}{'='*80}")
    print("LEVEL 2: Skill 명령어 테스트")
    print(f"{'='*80}{RESET}\n")

    # Test 1: list_collections
    print_test("list_collections() - 전체 컬렉션 목록")
    try:
        result = list_collections({'enabled_only': False, 'embedded_only': False})
        assert result['status'] == 'success', "list_collections failed"
        assert result['total'] >= 2, "Should have at least 2 collections"
        print_pass(f"총 {result['total']} 컬렉션 조회")
        for col in result['collections'][:3]:
            print_info(f"  - {col['id']}: {col['name']} (enabled: {col['enabled']}, embedded: {col['embedded']})")
    except Exception as e:
        print_fail(f"조회 실패: {e}")
        return False

    # Test 2: list_collections with filters
    print_test("list_collections() - 임베딩된 컬렉션만")
    try:
        result = list_collections({'enabled_only': True, 'embedded_only': True})
        assert result['status'] == 'success', "list_collections failed"
        assert result['total'] == 2, "Should have exactly 2 embedded collections"
        print_pass(f"임베딩된 컬렉션: {result['total']}개")
    except Exception as e:
        print_fail(f"조회 실패: {e}")
        return False

    # Test 3: get_collection_stats
    print_test("collection_stats() - chungjinkorea 통계")
    try:
        result = get_collection_stats({'collection_id': 'chungjinkorea'})
        assert result['status'] == 'success', "collection_stats failed"
        assert result['collection_name'] == 'products', "Wrong collection name"
        print_pass(f"Vector count: {result.get('vector_count', 'N/A')}")
    except Exception as e:
        print_fail(f"통계 조회 실패: {e}")
        return False

    # Test 4: get_collection_stats - onehago
    print_test("collection_stats() - onehago 통계")
    try:
        result = get_collection_stats({'collection_id': 'onehago'})
        assert result['status'] == 'success', "collection_stats failed"
        assert result['collection_name'] == 'onehago', "Wrong collection name"
        print_pass(f"Vector count: {result.get('vector_count', 'N/A')}")
    except Exception as e:
        print_fail(f"통계 조회 실패: {e}")
        return False

    print(f"\n{GREEN}✅ Level 2 테스트 통과{RESET}")
    return True


def test_level_3_multi_collection_search():
    """Level 3: 멀티 컬렉션 검색 테스트"""
    print(f"\n{YELLOW}{'='*80}")
    print("LEVEL 3: 멀티 컬렉션 검색 테스트")
    print(f"{'='*80}{RESET}\n")

    # Test 1: Single collection search - chungjinkorea
    print_test("vector_search() - chungjinkorea 단일 검색")
    try:
        result = vector_search({
            'query': '50ml bottle',
            'top_k': 5,
            'collections': ['chungjinkorea']
        })
        assert result['status'] == 'success', "Search failed"
        assert len(result['results']) > 0, "No results found"
        assert result['collections'] == ['chungjinkorea'], "Wrong collections"
        print_pass(f"{len(result['results'])} 결과 (chungjinkorea)")
        if result['results']:
            top = result['results'][0]
            print_info(f"  Top: {top['metadata'].get('product_name', 'N/A')[:50]} (score: {top['score']:.4f})")
    except Exception as e:
        print_fail(f"검색 실패: {e}")
        return False

    # Test 2: Single collection search - onehago
    print_test("vector_search() - onehago 단일 검색")
    try:
        result = vector_search({
            'query': '50ml PET bottle',
            'top_k': 5,
            'collections': ['onehago']
        })
        assert result['status'] == 'success', "Search failed"
        assert len(result['results']) > 0, "No results found"
        assert result['collections'] == ['onehago'], "Wrong collections"
        print_pass(f"{len(result['results'])} 결과 (onehago)")
        if result['results']:
            top = result['results'][0]
            print_info(f"  Top: {top['metadata'].get('product_name', 'N/A')[:50]} (score: {top['score']:.4f})")
    except Exception as e:
        print_fail(f"검색 실패: {e}")
        return False

    # Test 3: Multi-collection search
    print_test("vector_search() - 멀티 컬렉션 검색 (both)")
    try:
        result = vector_search({
            'query': '50ml cosmetic bottle',
            'top_k': 10,
            'collections': ['chungjinkorea', 'onehago']
        })
        assert result['status'] == 'success', "Search failed"
        assert len(result['results']) > 0, "No results found"
        assert set(result['collections']) == {'chungjinkorea', 'onehago'}, "Wrong collections"

        # Check if results from both collections
        sources = {r['metadata'].get('source_collection') for r in result['results']}
        print_pass(f"{len(result['results'])} 결과 from collections: {sources}")

        # Show top 3
        for i, r in enumerate(result['results'][:3], 1):
            name = r['metadata'].get('product_name', 'N/A')[:40]
            score = r['score']
            source = r['metadata'].get('source_collection', 'unknown')
            print_info(f"  {i}. [{source}] {name} (score: {score:.4f})")
    except Exception as e:
        print_fail(f"검색 실패: {e}")
        return False

    # Test 4: Default search (no collections specified)
    print_test("vector_search() - 기본 검색 (collections 미지정)")
    try:
        result = vector_search({
            'query': '화장품 용기',
            'top_k': 5
        })
        assert result['status'] == 'success', "Search failed"
        assert len(result['collections']) > 0, "No collections used"
        print_pass(f"기본 컬렉션 사용: {result['collections']}")
    except Exception as e:
        print_fail(f"검색 실패: {e}")
        return False

    # Test 5: Score merging verification
    print_test("Score 병합 검증 - 상위 결과가 올바르게 정렬되는지")
    try:
        result = vector_search({
            'query': 'PET bottle 50ml transparent',
            'top_k': 10,
            'collections': ['chungjinkorea', 'onehago']
        })
        scores = [r['score'] for r in result['results']]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"
        print_pass(f"Score 내림차순 정렬 확인: {scores[:3]}")
    except Exception as e:
        print_fail(f"정렬 검증 실패: {e}")
        return False

    print(f"\n{GREEN}✅ Level 3 테스트 통과{RESET}")
    return True


def test_level_4_rag_query():
    """Level 4: RAG Query 테스트"""
    print(f"\n{YELLOW}{'='*80}")
    print("LEVEL 4: RAG Query (Search + Generation) 테스트")
    print(f"{'='*80}{RESET}\n")

    # Test 1: RAG query with single collection
    print_test("rag_query() - chungjinkorea RAG")
    try:
        result = execute('query', {
            'question': 'Recommend a 50ml bottle for cosmetics',
            'top_k': 3,
            'collections': ['chungjinkorea']
        })
        assert result['status'] == 'success', "RAG query failed"
        assert 'answer' in result, "No answer generated"
        assert len(result['sources']) > 0, "No sources"
        print_pass(f"Answer generated: {len(result['answer'])} chars")
        print_info(f"  Answer preview: {result['answer'][:100]}...")
        print_info(f"  Sources: {len(result['sources'])}")
    except Exception as e:
        print_fail(f"RAG 실패: {e}")
        return False

    # Test 2: RAG query with multi-collection
    print_test("rag_query() - 멀티 컬렉션 RAG")
    try:
        result = execute('query', {
            'question': '50ml 화장품 용기 추천해주세요',
            'top_k': 5,
            'collections': ['chungjinkorea', 'onehago']
        })
        assert result['status'] == 'success', "RAG query failed"
        assert 'answer' in result, "No answer generated"
        assert len(result['collections']) == 2, "Should search both collections"
        print_pass(f"Multi-collection RAG: {result['collections']}")
        print_info(f"  Answer length: {len(result['answer'])} chars")
        print_info(f"  Confidence: {result['confidence']:.4f}")
    except Exception as e:
        print_fail(f"RAG 실패: {e}")
        return False

    print(f"\n{GREEN}✅ Level 4 테스트 통과{RESET}")
    return True


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Collection Routing 테스트')
    parser.add_argument('--level', default='all',
                       choices=['1', '2', '3', '4', 'all'],
                       help='테스트 레벨 (1-4 또는 all)')

    args = parser.parse_args()

    print(f"\n{BLUE}{'='*80}")
    print("MULTI-COLLECTION ROUTING 통합 테스트")
    print(f"{'='*80}{RESET}")

    results = {}

    if args.level in ['1', 'all']:
        results['level_1'] = test_level_1_collection_manager()

    if args.level in ['2', 'all']:
        results['level_2'] = test_level_2_skill_commands()

    if args.level in ['3', 'all']:
        results['level_3'] = test_level_3_multi_collection_search()

    if args.level in ['4', 'all']:
        results['level_4'] = test_level_4_rag_query()

    # Summary
    print(f"\n{BLUE}{'='*80}")
    print("테스트 결과 요약")
    print(f"{'='*80}{RESET}\n")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for level, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {level}: {status}")

    print(f"\n  총 {passed}/{total} 테스트 통과\n")

    if passed == total:
        print(f"{GREEN}🎉 모든 테스트 통과!{RESET}\n")
        return 0
    else:
        print(f"{RED}❌ 일부 테스트 실패{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
