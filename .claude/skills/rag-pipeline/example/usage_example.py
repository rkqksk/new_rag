"""
RAG Pipeline SKILL - Usage Examples

Shows how to use rag-pipeline SKILL for document processing and querying
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the skill
from .claude.skills.rag_pipeline.scripts import skill


def example_1_process_single_document():
    """Example 1: Process and index a single document"""

    print("=" * 60)
    print("Example 1: Process Single Document")
    print("=" * 60)

    result = skill.execute('process', {
        'file_path': 'docs/technical-manual.pdf',
        'options': {
            'chunk_size': 512,
            'overlap': 50,
            'use_ocr': False,
            'use_domain_expert': None  # Auto-detect
        }
    })

    print(f"\n✓ Processing Status: {result['status']}")
    print(f"✓ Document ID: {result.get('document_id', 'N/A')}")
    print(f"✓ Chunks Created: {result.get('chunks_count', 0)}")


def example_2_process_with_domain_expert():
    """Example 2: Process manufacturing document with domain expert"""

    print("\n" + "=" * 60)
    print("Example 2: Process with Manufacturing Expert")
    print("=" * 60)

    result = skill.execute('process', {
        'file_path': 'docs/manufacturing-sop.pdf',
        'options': {
            'chunk_size': 512,
            'use_domain_expert': 'manufacturing'  # Explicitly use manufacturing expert
        }
    })

    print(f"\n✓ Processing Status: {result['status']}")
    print(f"✓ Domain Expert Used: manufacturing")
    if result.get('metadata'):
        print(f"✓ Document Type: {result['metadata'].get('doc_type', 'N/A')}")
        print(f"✓ Terminology Extracted: {len(result['metadata'].get('terminology', []))} terms")


def example_3_rag_query_with_reranking():
    """Example 3: RAG query with cross-encoder reranking"""

    print("\n" + "=" * 60)
    print("Example 3: RAG Query with Reranking")
    print("=" * 60)

    result = skill.execute('query', {
        'question': 'What are the Cpk requirements for injection molding?',
        'top_k': 10,
        'use_rerank': True,
        'rerank_top_n': 3,
        'filters': {
            'doc_type': 'sop',
            'domain': 'manufacturing'
        }
    })

    print(f"\n✓ Query: {result['query']}")
    print(f"✓ Answer Generated: {len(result.get('answer', ''))} characters")
    print(f"✓ Sources Used: {len(result.get('sources', []))}")
    print(f"\n{result.get('answer', 'No answer generated')}")


def example_4_vector_search_only():
    """Example 4: Vector search without answer generation"""

    print("\n" + "=" * 60)
    print("Example 4: Vector Search Only")
    print("=" * 60)

    result = skill.execute('search', {
        'query': 'PET bottle specifications',
        'top_k': 5,
        'filters': {
            'domain': 'packaging'
        }
    })

    print(f"\n✓ Search Query: {result['query']}")
    print(f"✓ Results Found: {len(result['results'])}")

    for i, doc in enumerate(result['results'][:3], 1):
        print(f"\n  {i}. Score: {doc.get('score', 0):.3f}")
        print(f"     Content: {doc.get('content', '')[:100]}...")


def example_5_batch_processing():
    """Example 5: Batch process multiple documents"""

    print("\n" + "=" * 60)
    print("Example 5: Batch Document Processing")
    print("=" * 60)

    result = skill.execute('batch_process', {
        'file_paths': [
            'docs/sop-001.pdf',
            'docs/equipment-spec.pdf',
            'docs/quality-report.pdf'
        ],
        'options': {
            'chunk_size': 512,
            'use_domain_expert': 'manufacturing'
        }
    })

    print(f"\n✓ Total Documents: {result['total']}")
    print(f"✓ Successfully Processed: {result['successful']}")
    print(f"✓ Failed: {result['failed']}")

    for doc_result in result['results']:
        print(f"  • {doc_result['file_path']}: {doc_result['status']}")


def example_6_batch_search():
    """Example 6: Batch search multiple queries"""

    print("\n" + "=" * 60)
    print("Example 6: Batch Search Queries")
    print("=" * 60)

    result = skill.execute('batch_search', {
        'queries': [
            'What are the safety requirements?',
            'How to perform calibration?',
            'What is the maintenance schedule?'
        ],
        'top_k': 3
    })

    print(f"\n✓ Total Queries: {result['total']}")

    for i, query_result in enumerate(result['results'], 1):
        print(f"\n  {i}. Query: {query_result['query']}")
        print(f"     Results: {len(query_result['results'])}")


def example_7_optimize_and_stats():
    """Example 7: Optimize index and get statistics"""

    print("\n" + "=" * 60)
    print("Example 7: Optimize & Statistics")
    print("=" * 60)

    # Get statistics
    stats = skill.execute('stats')

    print("\n✓ System Statistics:")
    print(f"  Collections: {stats.get('collections', 0)}")
    print(f"  Total Documents: {stats.get('total_documents', 0)}")
    print(f"  Total Vectors: {stats.get('total_vectors', 0)}")

    # Optimize index
    print("\n✓ Optimizing vector database indexes...")
    optimize_result = skill.execute('optimize_index', {
        'collection': 'manufacturing_docs'
    })

    print(f"  Optimization Status: {optimize_result['status']}")


def example_8_evaluate_search_quality():
    """Example 8: Evaluate search quality"""

    print("\n" + "=" * 60)
    print("Example 8: Evaluate Search Quality")
    print("=" * 60)

    result = skill.execute('evaluate', {
        'test_queries': [
            {
                'query': 'What is the Cpk requirement?',
                'expected_doc_id': 'doc-123',
                'relevance_threshold': 0.7
            }
        ]
    })

    print(f"\n✓ Evaluation Complete")
    print(f"  Queries Tested: {result.get('total', 0)}")
    print(f"  Average Precision: {result.get('avg_precision', 0):.3f}")
    print(f"  Average Recall: {result.get('avg_recall', 0):.3f}")


if __name__ == "__main__":
    print("\n" + "🔍" * 30)
    print("RAG Pipeline SKILL - Usage Examples")
    print("🔍" * 30 + "\n")

    # Run all examples
    example_1_process_single_document()
    example_2_process_with_domain_expert()
    example_3_rag_query_with_reranking()
    example_4_vector_search_only()
    example_5_batch_processing()
    example_6_batch_search()
    example_7_optimize_and_stats()
    example_8_evaluate_search_quality()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60 + "\n")
