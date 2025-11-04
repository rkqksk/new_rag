#!/usr/bin/env python3
"""
Embed 857 Product Data to Qdrant

Processes all product JSON files and creates vector embeddings for RAG search
"""
import sys
import json
from pathlib import Path
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.embedding_service import EmbeddingService
from src.core.rag_pipeline import RAGPipeline
from qdrant_client import QdrantClient


class ProductDocumentLoader:
    """Load product JSON files"""

    def load_documents(self, paths):
        """Load product documents from JSON files"""
        documents = []

        for path in paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Create searchable text from product data
                text_parts = []

                # Product name
                if 'product_name' in data:
                    text_parts.append(f"Product: {data['product_name']}")

                # Product code
                if 'product_code' in data:
                    text_parts.append(f"Code: {data['product_code']}")

                # Specifications
                if 'specifications' in data:
                    specs = data['specifications']
                    for key, value in specs.items():
                        if value and str(value) != 'N/A':
                            text_parts.append(f"{key}: {value}")

                # Category
                if 'category' in data:
                    text_parts.append(f"Category: {data['category']}")

                # Material
                if 'material' in data:
                    text_parts.append(f"Material: {data['material']}")

                content = " | ".join(text_parts)

                # Create document object
                class Document:
                    def __init__(self, content, metadata):
                        self.page_content = content
                        self.metadata = metadata

                metadata = {
                    'source': str(path),
                    'idx': data.get('idx', ''),
                    'product_code': data.get('product_code', ''),
                    'product_name': data.get('product_name', ''),
                    'category': data.get('category', ''),
                    'material': data.get('material', ''),
                    'capacity': data.get('specifications', {}).get('capacity', ''),
                    'neck_size': data.get('specifications', {}).get('neck_size', ''),
                }

                documents.append(Document(content, metadata))

            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue

        return documents


class SimpleTextSplitter:
    """Simple text splitter (no splitting for product data)"""

    def split_documents(self, documents):
        """Return documents as-is"""
        return documents


def collect_product_files():
    """Collect all product JSON files"""
    base_path = Path('data/crawled/chungjinkorea/crawled_products_final')

    categories = ['Bottle', 'Jar', 'Cap', 'Pump']
    product_files = []

    for category in categories:
        category_path = base_path / category
        if category_path.exists():
            # Find all JSON files
            json_files = list(category_path.rglob('*.json'))
            product_files.extend(json_files)
            print(f"Found {len(json_files)} files in {category}/")

    return product_files


def main():
    """Embed all product data"""

    print("\n" + "="*80)
    print(" PRODUCT DATA EMBEDDING")
    print("="*80)

    # Step 1: Collect files
    print("\n[1/4] Collecting product files...")
    product_files = collect_product_files()
    print(f"Total files: {len(product_files)}")

    if len(product_files) == 0:
        print("❌ No product files found!")
        return False

    # Step 2: Initialize services
    print("\n[2/4] Initializing services...")

    try:
        qdrant_client = QdrantClient(url="http://localhost:6333")
        embedding_service = EmbeddingService(model_name='all-MiniLM-L6-v2')

        pipeline = RAGPipeline(
            loader=ProductDocumentLoader(),
            text_splitter=SimpleTextSplitter(),
            embedding_model=embedding_service,
            vector_db=qdrant_client,
            collection_name="products",
            ollama_url="http://localhost:11434",
            ollama_model="qwen2.5:7b-instruct"
        )

        print("✅ Services initialized")
        print(f"   Qdrant: http://localhost:6333")
        print(f"   Collection: products")
        print(f"   Embedding: all-MiniLM-L6-v2 (384 dim)")

    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return False

    # Step 3: Batch processing
    print("\n[3/4] Processing documents...")

    batch_size = 50
    total_batches = (len(product_files) + batch_size - 1) // batch_size
    successful = 0
    failed = 0

    for i in tqdm(range(0, len(product_files), batch_size),
                  total=total_batches,
                  desc="Embedding"):
        batch = product_files[i:i+batch_size]
        batch_paths = [str(f) for f in batch]

        try:
            result = pipeline.ingest_documents(batch_paths)
            successful += result['total_documents']
        except Exception as e:
            print(f"\n   Error in batch {i//batch_size + 1}: {e}")
            failed += len(batch)

    # Step 4: Summary
    print("\n[4/4] Summary")
    print("="*80)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {successful/(successful+failed)*100:.1f}%")

    # Test search
    print("\n" + "="*80)
    print(" TESTING SEARCH")
    print("="*80)

    try:
        test_query = "50ml PET bottle"
        results = pipeline.retrieve(test_query, top_k=3)

        print(f"\nQuery: '{test_query}'")
        print(f"Results: {len(results)}\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['metadata'].get('product_name', 'N/A')}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Material: {result['metadata'].get('material', 'N/A')}")
            print(f"   Capacity: {result['metadata'].get('capacity', 'N/A')}")
            print()

        print("✅ Search test passed!")

    except Exception as e:
        print(f"❌ Search test failed: {e}")

    print("\n" + "="*80)
    print(" EMBEDDING COMPLETE")
    print("="*80)

    return successful > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
