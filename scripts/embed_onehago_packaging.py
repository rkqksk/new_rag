#!/usr/bin/env python3
"""
Embed Onehago Packaging Data to Qdrant

Embeds 22,871 packaging products from onehago to 'onehago' collection
Matching chungjinkorea quality standards
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


class OnehagoPackagingLoader:
    """Load onehago packaging JSONL file"""

    def load_documents(self, paths):
        """Load packaging documents from JSONL"""
        documents = []

        for path in paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            data = json.loads(line.strip())

                            # Create searchable text from product data
                            text_parts = []

                            # Product name
                            if 'product_name' in data and data['product_name']:
                                text_parts.append(f"Product: {data['product_name']}")

                            # Product ID
                            if 'product_id' in data:
                                text_parts.append(f"ID: {data['product_id']}")

                            # Specifications
                            if 'specifications' in data and isinstance(data['specifications'], dict):
                                for key, value in data['specifications'].items():
                                    if value and str(value) != 'N/A':
                                        text_parts.append(f"{key}: {value}")

                            # Company info
                            if 'company_info' in data and isinstance(data['company_info'], dict):
                                for key, value in data['company_info'].items():
                                    if value:
                                        text_parts.append(f"{key}: {value}")

                            # Email
                            if 'email' in data and data['email']:
                                text_parts.append(f"Email: {data['email']}")

                            content = " | ".join(text_parts)

                            # Skip if no meaningful content
                            if len(content) < 10:
                                continue

                            # Create document object
                            class Document:
                                def __init__(self, content, metadata):
                                    self.page_content = content
                                    self.metadata = metadata

                            metadata = {
                                'source': str(path),
                                'line_number': line_num,
                                'product_id': data.get('product_id', ''),
                                'product_name': data.get('product_name', ''),
                                'category_id': data.get('category_id', ''),
                                'company_no': data.get('company_no', ''),
                                'product_url': data.get('product_url', ''),
                                'source_collection': 'onehago',
                                'source_name': '원하고',
                            }

                            documents.append(Document(content, metadata))

                        except json.JSONDecodeError as e:
                            print(f"  ⚠️  JSON error line {line_num}: {e}")
                            continue

            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
                continue

        return documents


class SimpleTextSplitter:
    """Simple text splitter (no splitting for product data)"""

    def split_documents(self, documents):
        """Return documents as-is"""
        return documents


def main():
    """Embed onehago packaging data"""

    print("\n" + "="*80)
    print(" ONEHAGO PACKAGING DATA EMBEDDING")
    print("="*80)

    # Step 1: Check file
    packaging_file = Path('data/crawled/onehago/crawled/production/packaging_unique_for_images.jsonl')

    if not packaging_file.exists():
        print(f"❌ File not found: {packaging_file}")
        return False

    print(f"\n[1/4] Data source:")
    print(f"   File: {packaging_file}")
    print(f"   Size: {packaging_file.stat().st_size / 1024 / 1024:.1f} MB")

    # Count lines
    with open(packaging_file, 'r') as f:
        total_lines = sum(1 for _ in f)
    print(f"   Products: {total_lines:,}")

    # Step 2: Initialize services
    print("\n[2/4] Initializing services...")

    try:
        qdrant_client = QdrantClient(url="http://localhost:6333")
        embedding_service = EmbeddingService(model_name='all-MiniLM-L6-v2')

        pipeline = RAGPipeline(
            loader=OnehagoPackagingLoader(),
            text_splitter=SimpleTextSplitter(),
            embedding_model=embedding_service,
            vector_db=qdrant_client,
            collection_name="onehago",  # ← New collection
            ollama_url="http://localhost:11434",
            ollama_model="qwen2.5:7b-instruct"
        )

        print("✅ Services initialized")
        print(f"   Qdrant: http://localhost:6333")
        print(f"   Collection: onehago (NEW)")
        print(f"   Embedding: all-MiniLM-L6-v2 (384 dim)")

    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return False

    # Step 3: Process documents in batches
    print("\n[3/4] Processing documents...")
    print("   Processing in batches of 100 products to avoid timeout")
    print("   This will take approximately 30-45 minutes for 22,871 products\n")

    try:
        # Read all products
        all_products = []
        with open(packaging_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    all_products.append(json.loads(line.strip()))
                except:
                    pass

        print(f"   Loaded {len(all_products)} products from file")

        # Process in batches
        batch_size = 100
        total_batches = (len(all_products) + batch_size - 1) // batch_size
        total_processed = 0
        total_failed = 0

        for batch_idx in tqdm(range(0, len(all_products), batch_size),
                              total=total_batches,
                              desc="Embedding"):
            batch = all_products[batch_idx:batch_idx + batch_size]

            # Create temp file for batch
            temp_file = Path(f'/tmp/onehago_batch_{batch_idx}.jsonl')
            with open(temp_file, 'w', encoding='utf-8') as f:
                for product in batch:
                    f.write(json.dumps(product, ensure_ascii=False) + '\n')

            try:
                result = pipeline.ingest_documents([str(temp_file)])
                total_processed += result['total_documents']
            except Exception as e:
                print(f"\n   ⚠️  Batch {batch_idx//batch_size + 1} failed: {e}")
                total_failed += len(batch)
            finally:
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()

        print(f"\n✅ Embedding complete!")
        print(f"   Total processed: {total_processed}")
        print(f"   Total failed: {total_failed}")
        print(f"   Success rate: {total_processed/(total_processed+total_failed)*100:.1f}%")

    except Exception as e:
        print(f"\n❌ Embedding failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Test search
    print("\n[4/4] Testing search...")
    print("="*80)

    try:
        test_queries = [
            "50ml PET bottle",
            "화장품 용기",
            "펌프 디스펜서"
        ]

        for query in test_queries:
            results = pipeline.retrieve(query, top_k=3)

            print(f"\n🔍 Query: '{query}'")
            print(f"   Results: {len(results)}\n")

            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['metadata'].get('product_name', 'N/A')[:60]}")
                print(f"      Score: {result['score']:.4f}")
                print(f"      ID: {result['metadata'].get('product_id', 'N/A')}")

        print("\n✅ Search test passed!")

    except Exception as e:
        print(f"❌ Search test failed: {e}")

    print("\n" + "="*80)
    print(" EMBEDDING COMPLETE")
    print("="*80)
    print(f"\n✅ Collection: onehago")
    print(f"✅ Products: {total_lines:,}")
    print(f"✅ Ready for multi-collection routing")

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
