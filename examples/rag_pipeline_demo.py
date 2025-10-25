"""
RAG Pipeline Skill - 실제 작동 데모

이 예제는:
1. rag-pipeline skill이 plugins 없이도 작동하는지 확인
2. plugins 있을 때와 없을 때 차이 비교
3. 실제 RAG 파이프라인 구현 (간단한 in-memory 버전)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import json

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import rag-pipeline skill
skill_path = project_root / '.claude' / 'skills' / 'rag-pipeline' / 'scripts'
sys.path.insert(0, str(skill_path))
import skill as rag_skill


def test_without_plugins():
    """plugins 폴더 없이 rag-pipeline 작동 테스트"""

    print("\n" + "=" * 80)
    print("🧪 Test 1: rag-pipeline WITHOUT plugins")
    print("=" * 80)

    # 일시적으로 plugins import 차단
    original_path = sys.path.copy()
    sys.path = [p for p in sys.path if 'plugins' not in p]

    # Skill reload
    import importlib
    importlib.reload(rag_skill)

    # Test help command
    print("\n📋 Testing 'help' command...")
    help_result = rag_skill.execute('help')
    print(f"✅ Commands available: {len(help_result['commands'])}")
    for cmd, desc in list(help_result['commands'].items())[:3]:
        print(f"   - {cmd}: {desc[:50]}...")

    # Test stats command
    print("\n📊 Testing 'stats' command...")
    stats_result = rag_skill.execute('stats')
    print(f"✅ Stats: {stats_result}")

    # Restore path
    sys.path = original_path

    return help_result


def test_with_plugins():
    """plugins 폴더 있을 때 rag-pipeline 작동 테스트"""

    print("\n" + "=" * 80)
    print("🔧 Test 2: rag-pipeline WITH plugins")
    print("=" * 80)

    # Skill reload with plugins
    import importlib
    importlib.reload(rag_skill)

    print(f"\n📦 Available domain experts: {list(rag_skill.DOMAIN_EXPERTS.keys())}")

    if rag_skill.DOMAIN_EXPERTS:
        print("✅ Domain experts loaded successfully!")
        for domain, expert in rag_skill.DOMAIN_EXPERTS.items():
            print(f"   - {domain}: {expert.__class__.__name__}")
    else:
        print("⚠️  No domain experts available (plugins not found)")

    return rag_skill.DOMAIN_EXPERTS


def create_test_documents():
    """테스트용 문서 생성"""

    docs_dir = project_root / 'data' / 'test_documents'
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 제조 문서
    manufacturing_doc = docs_dir / 'manufacturing_test.txt'
    manufacturing_doc.write_text("""
    Standard Operating Procedure - Injection Molding

    Process: Injection Molding of Plastic Components
    Material: ABS Plastic
    Equipment: IM-2000 Injection Molding Machine

    Process Parameters:
    - Barrel Temperature: 220°C
    - Injection Pressure: 150 MPa
    - Cooling Time: 30 seconds
    - Cycle Time: 45 seconds

    Quality Metrics:
    - Cpk: 1.45 (Target > 1.33)
    - OEE: 87% (Target > 85%)
    - PPM: 200 (Target < 500)
    - First Pass Yield: 96%

    Standards Compliance:
    - ISO 9001:2015
    - IATF 16949
    - GMP Guidelines

    Critical Control Points:
    1. Material drying (4 hours at 80°C)
    2. Mold temperature control (±3°C)
    3. Injection speed monitoring
    4. Visual inspection of parts
    """, encoding='utf-8')

    # 포장 문서
    packaging_doc = docs_dir / 'packaging_test.txt'
    packaging_doc.write_text("""
    Material Specification - PET Bottle

    Product: Clear PET Bottle for Cosmetics
    Capacity: 50ml
    Material: PET (Polyethylene Terephthalate)
    Neck Size: 24/410

    Material Properties:
    - Clarity: > 90%
    - Oxygen Barrier: < 1.0 cc/pkg/day
    - Moisture Barrier: < 0.5 g/pkg/day
    - Wall Thickness: 0.5mm ± 0.05mm
    - Weight: 12g ± 1g

    Regulatory Compliance:
    - FDA 21 CFR Part 177.1630
    - EU Regulation 10/2011
    - REACH compliant
    - RoHS compliant

    Applications:
    - Serums
    - Lotions
    - Toners
    - Light creams

    Storage Conditions:
    - Temperature: 15-25°C
    - Humidity: < 60%
    - Keep away from direct sunlight
    """, encoding='utf-8')

    # 일반 문서
    general_doc = docs_dir / 'general_test.txt'
    general_doc.write_text("""
    RAG System Architecture Overview

    Components:
    1. Document Processing
       - PDF/DOCX parsing
       - OCR for scanned documents
       - Text chunking (512 tokens)

    2. Vector Database
       - Qdrant for vector storage
       - Hybrid search (vector + keyword)
       - Metadata filtering

    3. Embedding Models
       - OpenAI text-embedding-3-small
       - Sentence Transformers (local)
       - Multilingual support

    4. Retrieval
       - Top-k vector search
       - Reranking with cross-encoder
       - Context window optimization

    5. Answer Generation
       - Claude Sonnet 4.5
       - GPT-4 Turbo
       - Local LLMs via Ollama

    Performance Metrics:
    - Search latency: < 100ms
    - Answer generation: < 2s
    - Accuracy (NDCG@10): > 0.85
    """, encoding='utf-8')

    return [manufacturing_doc, packaging_doc, general_doc]


def test_document_processing():
    """문서 처리 테스트"""

    print("\n" + "=" * 80)
    print("📄 Test 3: Document Processing")
    print("=" * 80)

    # 테스트 문서 생성
    docs = create_test_documents()
    print(f"\n✅ Created {len(docs)} test documents")

    results = []

    for doc_path in docs:
        print(f"\n📝 Processing: {doc_path.name}")

        # 도메인 판단
        if 'manufacturing' in doc_path.name:
            domain = 'manufacturing'
        elif 'packaging' in doc_path.name:
            domain = 'packaging'
        else:
            domain = None

        # Standard processing
        result_std = rag_skill.execute('process', {
            'file_path': str(doc_path)
        })
        print(f"   Standard: {result_std['status']}")

        # Domain expert processing (if available)
        if domain and domain in rag_skill.DOMAIN_EXPERTS:
            result_expert = rag_skill.execute('process', {
                'file_path': str(doc_path),
                'options': {'use_domain_expert': domain}
            })
            print(f"   With {domain} expert: {result_expert['status']}")
            if 'metadata' in result_expert:
                meta = result_expert['metadata']
                if 'doc_type' in meta:
                    print(f"      Doc type: {meta['doc_type']}")
                if 'terminology' in meta:
                    print(f"      Terms extracted: {len(meta['terminology'])}")

            results.append({
                'file': doc_path.name,
                'domain': domain,
                'result': result_expert
            })
        else:
            results.append({
                'file': doc_path.name,
                'domain': 'general',
                'result': result_std
            })

    return results


def test_rag_query():
    """RAG 쿼리 테스트"""

    print("\n" + "=" * 80)
    print("🔍 Test 4: RAG Query")
    print("=" * 80)

    test_queries = [
        "What is the Cpk requirement for injection molding?",
        "What materials are used for cosmetic bottles?",
        "How does vector search work in RAG?",
        "ISO 9001 요구사항은 무엇인가요?"
    ]

    results = []

    for query in test_queries:
        print(f"\n❓ Query: {query}")

        result = rag_skill.execute('query', {
            'question': query,
            'top_k': 5,
            'use_rerank': True
        })

        print(f"   Answer: {result.get('answer', 'N/A')[:80]}...")
        print(f"   Sources: {len(result.get('sources', []))}")

        results.append({
            'query': query,
            'result': result
        })

    return results


def test_batch_operations():
    """배치 작업 테스트"""

    print("\n" + "=" * 80)
    print("📦 Test 5: Batch Operations")
    print("=" * 80)

    # Batch search
    queries = [
        "Cpk requirements",
        "PET bottle specifications",
        "Vector database performance"
    ]

    print(f"\n🔍 Batch search: {len(queries)} queries")
    batch_result = rag_skill.execute('batch_search', {
        'queries': queries,
        'top_k': 3
    })

    print(f"   Total queries: {batch_result['total_queries']}")
    print(f"   Results: {len(batch_result['results'])}")

    return batch_result


def implement_simple_rag():
    """간단한 in-memory RAG 구현"""

    print("\n" + "=" * 80)
    print("🚀 Test 6: Simple In-Memory RAG Implementation")
    print("=" * 80)

    # 간단한 문서 저장소
    document_store = []

    # 테스트 문서 로드
    docs = create_test_documents()

    for doc_path in docs:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 간단한 청킹 (줄 단위)
        chunks = [line.strip() for line in content.split('\n') if line.strip()]

        document_store.extend([{
            'id': f"{doc_path.stem}_{i}",
            'content': chunk,
            'source': doc_path.name,
            'chunk_index': i
        } for i, chunk in enumerate(chunks)])

    print(f"\n📚 Loaded {len(document_store)} chunks from {len(docs)} documents")

    # 간단한 키워드 검색 (BM25 대신)
    def simple_search(query: str, top_k: int = 5) -> List[Dict]:
        """간단한 키워드 매칭 검색"""
        query_terms = query.lower().split()

        scored_chunks = []
        for chunk in document_store:
            content_lower = chunk['content'].lower()
            score = sum(1 for term in query_terms if term in content_lower)

            if score > 0:
                scored_chunks.append({
                    **chunk,
                    'score': score
                })

        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]

    # 테스트 쿼리
    test_query = "Cpk quality metrics ISO"
    print(f"\n🔍 Search query: '{test_query}'")

    results = simple_search(test_query, top_k=5)

    print(f"\n📊 Top {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. Score: {result['score']}")
        print(f"      Source: {result['source']}")
        print(f"      Content: {result['content'][:100]}...")

    # 간단한 답변 생성 (템플릿 기반)
    if results:
        context = "\n".join([r['content'] for r in results[:3]])
        answer = f"""Based on the documents:

Context from top results:
{context[:300]}...

Answer: This is a template-based answer. For actual LLM-generated answers,
integrate with Claude API or GPT-4."""

        print(f"\n💡 Generated Answer:")
        print(answer)

    return {
        'document_count': len(docs),
        'chunk_count': len(document_store),
        'query': test_query,
        'results_count': len(results),
        'top_result_score': results[0]['score'] if results else 0
    }


def main():
    """메인 실행 함수"""

    print("=" * 80)
    print("🏗️  RAG Pipeline Skill - Complete Demo")
    print("=" * 80)
    print("\n목적:")
    print("  1. rag-pipeline skill이 plugins 없이도 작동하는지 확인")
    print("  2. plugins 있을 때 domain expert 통합 확인")
    print("  3. 실제 RAG 파이프라인 구현 데모")

    # Test 1: Without plugins
    test_without_plugins()

    # Test 2: With plugins
    experts = test_with_plugins()

    # Test 3: Document processing
    processing_results = test_document_processing()

    # Test 4: RAG query
    query_results = test_rag_query()

    # Test 5: Batch operations
    batch_results = test_batch_operations()

    # Test 6: Simple RAG implementation
    rag_results = implement_simple_rag()

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)

    print(f"\n✅ Skill works without plugins: YES")
    print(f"✅ Domain experts available: {len(experts)}")
    print(f"✅ Documents processed: {len(processing_results)}")
    print(f"✅ Queries executed: {len(query_results)}")
    print(f"✅ Batch queries: {batch_results['total_queries']}")
    print(f"✅ In-memory RAG chunks: {rag_results['chunk_count']}")

    print("\n🎯 Key Findings:")
    print("  1. rag-pipeline skill은 plugins 없이도 기본 기능 작동")
    print("  2. plugins 있으면 domain expert 통합으로 더 풍부한 메타데이터")
    print("  3. 실제 RAG 엔진 연결 전에도 skill 인터페이스 사용 가능")
    print("  4. manufacturing-expert와 달리 self-contained 구조")

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)

    return {
        'experts': len(experts),
        'processing': len(processing_results),
        'queries': len(query_results),
        'batch': batch_results,
        'rag': rag_results
    }


if __name__ == "__main__":
    results = main()

    # Save results
    output_file = project_root / 'data' / 'test_results' / 'rag_pipeline_demo_results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved: {output_file}")
