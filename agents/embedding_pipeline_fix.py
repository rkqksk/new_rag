"""
Fix: 올바른 데이터 경로로 벡터 임베딩 생성 및 Qdrant 업데이트
- crawled_products_final 구조 사용
- 이미지 개수 계산 및 업데이트
- 벡터 임베딩 생성 및 업로드
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class EmbeddingPipelineFix:
    def __init__(self):
        self.data_dir = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final")
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"✅ Embedding model loaded")

    def count_images(self, product_id: str, category: str) -> int:
        """이미지 개수 계산"""
        category_parts = category.split('/')
        if len(category_parts) == 2:
            main_cat, material = category_parts
        else:
            return 0

        images_dir = self.data_dir / main_cat / material / "images"
        if not images_dir.exists():
            return 0

        # idx_XXX로 시작하는 파일 찾기
        count = 0
        for f in images_dir.glob(f"{product_id}*"):
            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                count += 1
        return count

    def fix_qdrant_data(self):
        """Qdrant의 데이터 수정: 이미지 개수 업데이트 및 벡터 생성"""

        collection_name = "products_all"

        # 모든 포인트 가져오기
        logger.info("📥 Qdrant에서 모든 포인트 로드 중...")
        offset = 0
        all_points = []

        while True:
            response = self.qdrant.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            if not response[0]:
                break

            all_points.extend(response[0])
            offset = response[1]
            logger.info(f"  로드됨: {len(all_points)}개 포인트")

        logger.info(f"✅ 총 {len(all_points)}개 포인트 로드 완료")

        # 벡터 임베딩 생성 및 업데이트
        logger.info("\n🔄 벡터 임베딩 생성 중...")

        vectors_to_upload = []

        for idx, point in enumerate(all_points):
            payload = point.payload
            product_id = payload.get("product_id", "")
            product_name = payload.get("product_name", "")
            category = payload.get("category", "")

            # 이미지 개수 계산
            num_images = self.count_images(product_id, category)
            payload["num_images"] = num_images

            # 텍스트 벡터 임베딩 생성
            text_to_embed = f"{product_name} {category}"
            text_embedding = self.embedder.encode(text_to_embed, convert_to_numpy=True).tolist()

            # Qdrant 포인트 생성 (text 벡터만)
            point_struct = PointStruct(
                id=point.id,
                vector={"text": text_embedding},  # Named vector
                payload=payload
            )
            vectors_to_upload.append(point_struct)

            if (idx + 1) % 100 == 0:
                logger.info(f"  처리됨: {idx + 1}/{len(all_points)}")

        # Qdrant에 업로드
        logger.info(f"\n📤 Qdrant에 벡터 업로드 중 ({len(vectors_to_upload)}개)...")

        # 배치로 업로드
        batch_size = 50
        for i in range(0, len(vectors_to_upload), batch_size):
            batch = vectors_to_upload[i:i+batch_size]
            self.qdrant.upsert(
                collection_name=collection_name,
                points=batch
            )
            logger.info(f"  업로드됨: {min(i+batch_size, len(vectors_to_upload))}/{len(vectors_to_upload)}")

        # 최종 상태 확인
        collection_info = self.qdrant.get_collection(collection_name)
        logger.info(f"\n✅ 완료!")
        logger.info(f"   - 총 포인트: {collection_info.points_count}")
        logger.info(f"   - 인덱싱된 벡터: {collection_info.indexed_vectors_count}")

if __name__ == "__main__":
    pipeline = EmbeddingPipelineFix()
    pipeline.fix_qdrant_data()
