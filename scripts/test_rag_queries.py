#!/usr/bin/env python3
"""
Simple RAG Query Testing Script

Tests the Qdrant vector search with sample queries.

Usage:
    python scripts/test_rag_queries.py
    python scripts/test_rag_queries.py --query "PP 소재에 어떤 첨가제가 사용되나요?"
"""

import argparse
import sys
import requests
from typing import List, Dict
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("❌ qdrant-client not installed. Run: pip install qdrant-client")
    sys.exit(1)


def generate_ollama_embedding(text: str, model='nomic-embed-text') -> List[float]:
    """Generate embedding using Ollama"""
    try:
        response = requests.post(
            'http://localhost:11434/api/embeddings',
            json={'model': model, 'prompt': text}
        )
        response.raise_for_status()
        return response.json()['embedding']
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        raise


def search_rag(query: str, collection_name='cosmetic_packaging', top_k=5, qdrant_url='http://localhost:6333'):
    """Search RAG system with a query"""

    print("\n" + "="*80)
    print(f"🔍 RAG Query Test")
    print("="*80)

    # Connect to Qdrant
    try:
        client = QdrantClient(url=qdrant_url)
        print(f"✅ Connected to Qdrant at {qdrant_url}")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return []

    # Generate query embedding
    print(f"\n📝 Query: \"{query}\"")
    print(f"🧮 Generating embedding...")

    try:
        query_embedding = generate_ollama_embedding(query)
        print(f"✅ Embedding generated (dim: {len(query_embedding)})")
    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        return []

    # Search Qdrant
    print(f"\n🔍 Searching collection '{collection_name}' (top {top_k})...")

    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        print(f"✅ Found {len(results)} results")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return []

    # Display results
    print(f"\n" + "="*80)
    print(f"📊 Search Results")
    print("="*80)

    for i, result in enumerate(results, 1):
        print(f"\n{'─'*80}")
        print(f"Result #{i}")
        print(f"{'─'*80}")
        print(f"🎯 Score: {result.score:.4f}")
        print(f"🆔 Q&A ID: {result.payload['qa_id']}")
        print(f"📁 Category: {result.payload.get('category', 'N/A')}")

        if result.payload.get('keywords'):
            print(f"🏷️  Keywords: {', '.join(result.payload['keywords'][:5])}")

        if result.payload.get('related_materials'):
            print(f"🧪 Materials: {', '.join(result.payload['related_materials'])}")

        # Extract question and answer from text
        text = result.payload['text']
        if '질문:' in text and '답변:' in text:
            parts = text.split('답변:')
            question = parts[0].replace('질문:', '').strip()
            answer = parts[1].strip() if len(parts) > 1 else ''

            print(f"\n💬 Question:")
            print(f"   {question[:150]}{'...' if len(question) > 150 else ''}")
            print(f"\n💡 Answer:")
            print(f"   {answer[:300]}{'...' if len(answer) > 300 else ''}")

    print(f"\n{'='*80}\n")

    return results


def run_sample_queries():
    """Run a set of sample queries"""

    sample_queries = [
        "PP 소재에 어떤 첨가제가 사용되나요?",
        "화장품 용기 금형 설계 시 주의사항은?",
        "이형제 사용할 때 주의할 점",
        "용기 밀폐성을 높이는 방법",
        "화장품 용기 온도 테스트 기준",
        "50미리 세럼 용기 추천",
        "PE와 PET 재질의 차이점",
        "친환경 용기 설계 원칙"
    ]

    print("\n" + "="*80)
    print("🧪 Running Sample Queries")
    print("="*80)
    print(f"\nTotal queries: {len(sample_queries)}")
    print("\nPress Enter to run each query, or 'q' to quit")

    for i, query in enumerate(sample_queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}/{len(sample_queries)}")
        print(f"{'='*80}")

        user_input = input(f"\nRun: \"{query}\"? [Enter/q]: ").strip().lower()

        if user_input == 'q':
            print("\n👋 Exiting...")
            break

        results = search_rag(query, top_k=3)

        if not results:
            print("⚠️  No results found or error occurred")

        if i < len(sample_queries):
            input("\nPress Enter to continue to next query...")

    print("\n" + "="*80)
    print("✅ Sample Queries Complete!")
    print("="*80)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Test RAG query system')
    parser.add_argument('--query', type=str, help='Single query to test')
    parser.add_argument('--collection', default='cosmetic_packaging', help='Qdrant collection name')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results to return')
    parser.add_argument('--qdrant-url', default='http://localhost:6333', help='Qdrant URL')
    parser.add_argument('--sample', action='store_true', help='Run sample queries interactively')

    args = parser.parse_args()

    if args.sample:
        run_sample_queries()
    elif args.query:
        search_rag(args.query, args.collection, args.top_k, args.qdrant_url)
    else:
        # Interactive mode
        print("\n" + "="*80)
        print("🤖 Interactive RAG Query Mode")
        print("="*80)
        print("\nEnter your queries below. Type 'quit' or 'exit' to stop.")
        print("Type 'sample' to run sample queries.\n")

        while True:
            try:
                query = input("💬 Query: ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                if query.lower() == 'sample':
                    run_sample_queries()
                    continue

                search_rag(query, args.collection, args.top_k, args.qdrant_url)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
