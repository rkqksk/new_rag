"""
Onehago 제품 임베딩 생성 스크립트
24,745개 JSON → Qdrant onehago_v2 collection

사용법:
    python scripts/embed_onehago_products.py \
        --input data/onehago/*.json \
        --collection onehago_v2 \
        --batch-size 100

예상 시간: 2-3시간 (24,745개 제품)
"""

import json
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Any
import logging
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OnehagoEmbedder:
    """Onehago 제품 임베딩 생성기"""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        collection_name: str = "onehago_v2"
    ):
        """
        Initialize embedder

        Args:
            qdrant_host: Qdrant 호스트
            qdrant_port: Qdrant 포트
            model_name: Sentence Transformer 모델
            collection_name: Qdrant collection 이름
        """
        logger.info(f"Initializing embedder...")

        # Qdrant client
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        logger.info(f"✅ Connected to Qdrant: {qdrant_host}:{qdrant_port}")

        # Embedding model
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"✅ Loaded model: {model_name} (dim: {self.dimension})")

        self.collection_name = collection_name

    def create_collection(self):
        """Qdrant collection 생성"""
        try:
            # Check if collection exists
            collections = self.qdrant.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if exists:
                logger.warning(f"⚠️  Collection '{self.collection_name}' already exists")
                response = input("Delete and recreate? (y/N): ")
                if response.lower() == 'y':
                    self.qdrant.delete_collection(self.collection_name)
                    logger.info(f"🗑️  Deleted existing collection")
                else:
                    logger.info("Continuing with existing collection...")
                    return

            # Create collection
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def load_json_files(self, pattern: str) -> List[Dict[str, Any]]:
        """
        JSON 파일들 로드

        Args:
            pattern: Glob pattern (e.g., "data/onehago/*.json")

        Returns:
            제품 데이터 리스트
        """
        logger.info(f"Loading JSON files: {pattern}")

        files = glob.glob(pattern)
        logger.info(f"Found {len(files)} JSON files")

        if not files:
            raise ValueError(f"No JSON files found matching: {pattern}")

        products = []

        for file_path in tqdm(files, desc="Loading JSON"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Handle both single product and list of products
                    if isinstance(data, list):
                        products.extend(data)
                    else:
                        products.append(data)

            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
                continue

        logger.info(f"✅ Loaded {len(products)} products")
        return products

    def generate_embedding_text(self, product: Dict[str, Any]) -> str:
        """
        제품 데이터 → 임베딩용 텍스트 생성

        Args:
            product: 제품 데이터

        Returns:
            임베딩용 텍스트
        """
        parts = []

        # Product name/title
        if 'product_name' in product:
            parts.append(product['product_name'])
        elif 'title' in product:
            parts.append(product['title'])
        elif 'name' in product:
            parts.append(product['name'])

        # Product code
        if 'product_code' in product:
            parts.append(f"제품코드: {product['product_code']}")

        # Category
        if 'category' in product:
            parts.append(f"카테고리: {product['category']}")

        # Specifications
        if 'spec' in product and product['spec']:
            parts.append(str(product['spec']))

        # Description
        if 'description' in product and product['description']:
            desc = str(product['description'])
            if len(desc) > 200:
                desc = desc[:200]
            parts.append(desc)

        # Material
        if 'material' in product:
            parts.append(f"재질: {product['material']}")

        # Price
        if 'price' in product:
            parts.append(f"가격: {product['price']}")

        text = " | ".join(str(p) for p in parts if p)

        # Limit length
        if len(text) > 500:
            text = text[:500]

        return text

    def embed_products(
        self,
        products: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        제품 임베딩 생성 및 Qdrant 업로드

        Args:
            products: 제품 데이터 리스트
            batch_size: 배치 크기
        """
        logger.info(f"Generating embeddings for {len(products)} products...")
        logger.info(f"Batch size: {batch_size}")

        total_batches = (len(products) + batch_size - 1) // batch_size

        uploaded_count = 0

        for batch_idx in tqdm(range(total_batches), desc="Embedding batches"):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(products))

            batch_products = products[start_idx:end_idx]

            # Generate texts
            texts = [self.generate_embedding_text(p) for p in batch_products]

            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True
            )

            # Prepare points
            points = []
            for i, (product, embedding) in enumerate(zip(batch_products, embeddings)):
                point_id = start_idx + i + 1  # Start from 1

                # Payload
                payload = {
                    'product_id': product.get('product_id', f'onehago_{point_id}'),
                    'product_name': product.get('product_name') or product.get('title') or product.get('name', 'Unknown'),
                    'product_code': product.get('product_code', ''),
                    'category': product.get('category', ''),
                    'source': 'onehago.com'
                }

                # Add optional fields
                for field in ['spec', 'material', 'price', 'manufacturer', 'origin']:
                    if field in product and product[field]:
                        payload[field] = str(product[field])[:200]  # Limit length

                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload
                )
                points.append(point)

            # Upload to Qdrant
            try:
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                uploaded_count += len(points)

            except Exception as e:
                logger.error(f"Failed to upload batch {batch_idx}: {e}")
                continue

        logger.info(f"✅ Uploaded {uploaded_count}/{len(products)} products")

    def verify(self):
        """Collection 검증"""
        collection_info = self.qdrant.get_collection(self.collection_name)

        logger.info(f"")
        logger.info(f"=" * 60)
        logger.info(f"✅ Collection Verification")
        logger.info(f"=" * 60)
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Points count: {collection_info.points_count}")
        logger.info(f"Vectors count: {collection_info.vectors_count}")
        logger.info(f"Status: {collection_info.status}")
        logger.info(f"=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Onehago 제품 임베딩 생성")

    parser.add_argument(
        '--input',
        type=str,
        default='data/onehago/*.json',
        help='입력 JSON 파일 패턴 (default: data/onehago/*.json)'
    )

    parser.add_argument(
        '--collection',
        type=str,
        default='onehago_v2',
        help='Qdrant collection 이름 (default: onehago_v2)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='배치 크기 (default: 100)'
    )

    parser.add_argument(
        '--qdrant-host',
        type=str,
        default='localhost',
        help='Qdrant 호스트 (default: localhost)'
    )

    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=6333,
        help='Qdrant 포트 (default: 6333)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='sentence-transformers/all-MiniLM-L6-v2',
        help='Sentence Transformer 모델'
    )

    parser.add_argument(
        '--skip-create',
        action='store_true',
        help='Collection 생성 스킵 (이미 존재하는 경우)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("🚀 Onehago 제품 임베딩 생성")
    print("=" * 80)
    print(f"Input: {args.input}")
    print(f"Collection: {args.collection}")
    print(f"Batch size: {args.batch_size}")
    print(f"Qdrant: {args.qdrant_host}:{args.qdrant_port}")
    print(f"Model: {args.model}")
    print("=" * 80)
    print("")

    try:
        # Initialize
        embedder = OnehagoEmbedder(
            qdrant_host=args.qdrant_host,
            qdrant_port=args.qdrant_port,
            model_name=args.model,
            collection_name=args.collection
        )

        # Create collection
        if not args.skip_create:
            embedder.create_collection()

        # Load products
        products = embedder.load_json_files(args.input)

        if not products:
            logger.error("No products loaded!")
            return

        # Embed and upload
        embedder.embed_products(products, batch_size=args.batch_size)

        # Verify
        embedder.verify()

        print("")
        print("=" * 80)
        print("✅ 완료!")
        print("=" * 80)
        print("")
        print("다음 단계:")
        print("1. Snapshot 생성: ./scripts/create_snapshot.sh onehago_v2")
        print("2. 검색 테스트: curl http://localhost:6333/collections/onehago_v2")
        print("")

    except Exception as e:
        logger.error(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
