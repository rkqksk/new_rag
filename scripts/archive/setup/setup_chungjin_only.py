#!/usr/bin/env python3
"""
청진코리아 데이터만 벡터화 및 서버 가동
- onehago/freemold는 제외
- chungjinkorea 데이터만 임베딩
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict
import ollama

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient, models


class ChungjinVectorizer:
    """청진코리아 데이터 벡터화"""

    def __init__(self):
        self.client = QdrantClient(path="./data/chungjinkorea_qdrant")
        self.collection_name = "chungjin_products"
        self.model_name = "nomic-embed-text"

        # 통계
        self.stats = {
            'products_processed': 0,
            'vectors_created': 0,
            'errors': 0
        }

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        try:
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"  ⚠️ Embedding failed: {e}")
            return None

    def load_products(self) -> List[Dict]:
        """청진코리아 제품 데이터 로드"""
        products = []
        data_dir = Path("data/chungjinkorea/crawled_products_final")

        # 모든 카테고리 탐색
        for category_dir in data_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # Skip backup files
            if '_old' in category_dir.name or 'backup' in category_dir.name:
                continue

            print(f"📦 Loading category: {category_dir.name}")

            # 재질별 디렉토리 탐색
            for material_dir in category_dir.iterdir():
                if not material_dir.is_dir():
                    continue

                products_dir = material_dir / "products"
                if not products_dir.exists():
                    continue

                # JSON 파일 로드
                for json_file in products_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            product = json.load(f)

                            # 필수 필드 확인
                            if 'product_code' in product and 'product_name' in product:
                                # 카테고리와 재질 추가
                                product['category'] = category_dir.name
                                product['material'] = material_dir.name
                                products.append(product)
                    except Exception as e:
                        print(f"    ⚠️ Failed to load {json_file.name}: {e}")

        print(f"\n✅ Loaded {len(products)} products")
        return products

    def create_product_text(self, product: Dict) -> str:
        """제품 정보를 검색 가능한 텍스트로 변환"""
        parts = []

        # 기본 정보
        if 'product_code' in product:
            parts.append(f"제품코드: {product['product_code']}")

        if 'product_name' in product:
            parts.append(f"제품명: {product['product_name']}")

        # 카테고리와 재질
        if 'category' in product:
            parts.append(f"카테고리: {product['category']}")

        if 'material' in product:
            parts.append(f"재질: {product['material']}")

        # 사양
        specs = product.get('specifications', {})
        if 'capacity' in specs:
            parts.append(f"용량: {specs['capacity']}")

        if 'neck_size' in specs:
            parts.append(f"Neck: {specs['neck_size']}")

        if 'dimensions' in specs:
            parts.append(f"사이즈: {specs['dimensions']}")

        # 가격 정보
        pricing = product.get('pricing', {})
        if 'moq' in pricing:
            parts.append(f"MOQ: {pricing['moq']}")

        # 추가 설명
        if 'description' in product:
            parts.append(f"설명: {product['description']}")

        return " | ".join(parts)

    def setup_collection(self):
        """Qdrant 컬렉션 설정"""
        print("\n🔧 Setting up Qdrant collection...")

        # 기존 컬렉션 삭제 (있으면)
        try:
            self.client.delete_collection(self.collection_name)
            print(f"  🗑️ Deleted existing collection: {self.collection_name}")
        except:
            pass

        # 새 컬렉션 생성
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=768,  # nomic-embed-text dimension
                distance=models.Distance.COSINE
            )
        )
        print(f"  ✅ Created collection: {self.collection_name}")

    def vectorize_products(self, products: List[Dict], batch_size: int = 10):
        """제품 데이터를 벡터화하여 Qdrant에 저장"""
        print(f"\n🚀 Vectorizing {len(products)} products...")

        points = []

        for idx, product in enumerate(products):
            try:
                # 텍스트 생성
                text = self.create_product_text(product)

                # 벡터 생성
                vector = self.embed_text(text)

                if vector is None:
                    self.stats['errors'] += 1
                    continue

                # Point 생성
                point = models.PointStruct(
                    id=idx,
                    vector=vector,
                    payload={
                        'product_code': product.get('product_code', ''),
                        'product_name': product.get('product_name', ''),
                        'category': product.get('category', ''),
                        'material': product.get('material', ''),
                        'specifications': product.get('specifications', {}),
                        'pricing': product.get('pricing', {}),
                        'text': text
                    }
                )

                points.append(point)
                self.stats['products_processed'] += 1
                self.stats['vectors_created'] += 1

                # 배치 단위로 저장
                if len(points) >= batch_size:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    print(f"  ✅ Uploaded {len(points)} vectors ({idx + 1}/{len(products)})")
                    points = []

            except Exception as e:
                print(f"  ⚠️ Failed to vectorize product {idx}: {e}")
                self.stats['errors'] += 1

        # 남은 points 저장
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"  ✅ Uploaded final {len(points)} vectors")

    def test_search(self):
        """벡터 검색 테스트"""
        print("\n🔍 Testing vector search...")

        test_queries = [
            "50ml PET 병",
            "펌프",
            "나사캡"
        ]

        for query in test_queries:
            print(f"\n  Query: {query}")

            # 벡터 생성
            query_vector = self.embed_text(query)

            if query_vector is None:
                print(f"    ⚠️ Failed to embed query")
                continue

            # 검색
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=3
            )

            for i, result in enumerate(results):
                print(f"    {i + 1}. {result.payload['product_name']} "
                      f"({result.payload['product_code']}) "
                      f"- Score: {result.score:.3f}")

    def run(self):
        """전체 프로세스 실행"""
        print("="*60)
        print("청진코리아 데이터 벡터화")
        print("="*60)

        # 1. 제품 데이터 로드
        products = self.load_products()

        if not products:
            print("❌ No products found!")
            return

        # 2. 컬렉션 설정
        self.setup_collection()

        # 3. 벡터화
        self.vectorize_products(products)

        # 4. 테스트
        self.test_search()

        # 5. 통계
        print("\n" + "="*60)
        print("✅ Vectorization Complete!")
        print("="*60)
        print(f"Products processed: {self.stats['products_processed']}")
        print(f"Vectors created: {self.stats['vectors_created']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Collection: {self.collection_name}")
        print(f"Qdrant path: ./data/chungjinkorea_qdrant")
        print("="*60)


if __name__ == "__main__":
    vectorizer = ChungjinVectorizer()
    vectorizer.run()
