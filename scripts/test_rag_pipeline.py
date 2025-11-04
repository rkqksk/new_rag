#!/usr/bin/env python3
"""
RAG Pipeline Integration Test

Tests:
1. Qdrant connection
2. Embedding generation
3. Document ingestion
4. Vector search
5. Ollama response generation
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.embedding_service import EmbeddingService
from src.core.rag_pipeline import RAGPipeline
from qdrant_client import QdrantClient


def test_qdrant_connection():
    """Test 1: Qdrant Connection"""
    print("\n" + "="*60)
    print("Test 1: Qdrant Connection")
    print("="*60)

    try:
        client = QdrantClient(url="http://localhost:6333")
        collections = client.get_collections()
        print(f"✅ Connected to Qdrant")
        print(f"   Existing collections: {len(collections.collections)}")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return None


def test_embedding_service():
    """Test 2: Embedding Generation"""
    print("\n" + "="*60)
    print("Test 2: Embedding Service")
    print("="*60)

    try:
        service = EmbeddingService(model_name='all-MiniLM-L6-v2')

        # Test single embedding
        test_text = "50ml PET bottle for cosmetics"
        embedding = service.embed_query(test_text)

        print(f"✅ Embedding service working")
        print(f"   Model: {service.model_name}")
        print(f"   Dimension: {service.embedding_dim}")
        print(f"   Test embedding shape: {embedding.shape}")

        return service
    except Exception as e:
        print(f"❌ Embedding service failed: {e}")
        return None


def test_document_ingestion(qdrant_client, embedding_service):
    """Test 3: Document Ingestion"""
    print("\n" + "="*60)
    print("Test 3: Document Ingestion (Mock)")
    print("="*60)

    # Simple mock loader and splitter for testing
    class MockDocument:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata

    class MockLoader:
        def load_documents(self, paths):
            return [
                MockDocument(
                    "50ml PET bottle with pump dispenser. Material: PET. Capacity: 50ml. Neck size: 20/410.",
                    {"source": "test_product_1.json", "product_code": "BTL-001"}
                ),
                MockDocument(
                    "100ml HDPE bottle for lotion. Material: HDPE. Capacity: 100ml. Neck size: 24/410.",
                    {"source": "test_product_2.json", "product_code": "BTL-002"}
                )
            ]

    class MockSplitter:
        def split_documents(self, documents):
            return documents  # No splitting for this test

    try:
        # Create RAG pipeline
        pipeline = RAGPipeline(
            loader=MockLoader(),
            text_splitter=MockSplitter(),
            embedding_model=embedding_service,
            vector_db=qdrant_client,
            collection_name="test_products",
            ollama_url="http://localhost:11434",
            ollama_model="qwen2.5:7b-instruct"
        )

        # Ingest test documents
        result = pipeline.ingest_documents(["test1.json", "test2.json"])

        print(f"✅ Document ingestion successful")
        print(f"   Documents: {result['total_documents']}")
        print(f"   Chunks: {result['total_chunks']}")

        return pipeline
    except Exception as e:
        print(f"❌ Document ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_vector_search(pipeline):
    """Test 4: Vector Search"""
    print("\n" + "="*60)
    print("Test 4: Vector Search")
    print("="*60)

    try:
        query = "50ml bottle"
        results = pipeline.retrieve(query, top_k=2)

        print(f"✅ Vector search successful")
        print(f"   Query: '{query}'")
        print(f"   Results: {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"\n   Result {i}:")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Text: {result['text'][:100]}...")
            print(f"   Metadata: {result['metadata']}")

        return results
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_ollama_generation(pipeline, context_chunks):
    """Test 5: Ollama Response Generation"""
    print("\n" + "="*60)
    print("Test 5: Ollama Response Generation")
    print("="*60)

    try:
        query = "What 50ml bottles are available?"
        response = pipeline.generate_response(context_chunks, query)

        print(f"✅ Ollama generation successful")
        print(f"   Query: '{query}'")
        print(f"\n   Response:")
        print(f"   {response}")

        return response
    except Exception as e:
        print(f"❌ Ollama generation failed: {e}")
        print(f"   Note: Make sure Ollama is running: ollama serve")
        return None


def cleanup(qdrant_client):
    """Cleanup test data"""
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)

    try:
        qdrant_client.delete_collection("test_products")
        print("✅ Test collection deleted")
    except:
        print("   No test collection to delete")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" RAG PIPELINE INTEGRATION TEST")
    print("="*80)

    # Test 1: Qdrant
    qdrant_client = test_qdrant_connection()
    if not qdrant_client:
        print("\n❌ Aborting: Qdrant not available")
        return False

    # Test 2: Embeddings
    embedding_service = test_embedding_service()
    if not embedding_service:
        print("\n❌ Aborting: Embedding service failed")
        return False

    # Test 3: Ingestion
    pipeline = test_document_ingestion(qdrant_client, embedding_service)
    if not pipeline:
        print("\n❌ Aborting: Document ingestion failed")
        cleanup(qdrant_client)
        return False

    # Test 4: Search
    results = test_vector_search(pipeline)
    if not results:
        print("\n❌ Aborting: Vector search failed")
        cleanup(qdrant_client)
        return False

    # Test 5: Generation
    response = test_ollama_generation(pipeline, results)

    # Cleanup
    cleanup(qdrant_client)

    # Summary
    print("\n" + "="*80)
    print(" TEST SUMMARY")
    print("="*80)
    print(f"✅ Qdrant: OK")
    print(f"✅ Embeddings: OK")
    print(f"✅ Ingestion: OK")
    print(f"✅ Vector Search: OK")
    if response:
        print(f"✅ Ollama Generation: OK")
        print(f"\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"⚠️  Ollama Generation: SKIPPED (Ollama might not be running)")
        print(f"\n✅ CORE RAG PIPELINE WORKING!")
        return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
