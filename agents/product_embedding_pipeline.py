"""
제품 데이터 멀티모달 임베딩 파이프라인
- 텍스트 임베딩: gte-Qwen2-7B-instruct
- 이미지 임베딩: OpenCLIP-ViT-H-14
- 메타데이터 추출 및 벡터화
- Qdrant 통합 업로드
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import concurrent.futures
from datetime import datetime

import numpy as np
from PIL import Image
import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ProductEmbedding:
    """제품 임베딩 데이터"""
    product_id: str
    product_name: str
    category: str
    text_embedding: List[float]
    image_embeddings: List[List[float]]
    metadata: Dict[str, Any]
    embedding_timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


class ProductEmbedder:
    """제품 임베딩 처리기"""

    def __init__(
        self,
        text_model: str = "GTE_Qwen2_7B_instruct",
        image_model: str = "openai/ViT-H-14",
        device: str = "auto"
    ):
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        # 텍스트 모델
        try:
            self.text_model = SentenceTransformer(
                "Alibaba-NLP/gte-Qwen2-7B-instruct",
                device=self.device
            )
            logger.info("✅ Text model loaded: gte-Qwen2-7B-instruct")
        except Exception as e:
            logger.warning(f"Failed to load gte-Qwen2-7B-instruct: {e}")
            self.text_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=self.device)
            logger.info("⚠️ Using fallback model: all-MiniLM-L6-v2")

        # 이미지 모델 (OpenCLIP)
        try:
            import open_clip
            self.image_model, self.image_processor, _ = open_clip.create_model_and_transforms(
                model_name="ViT-H-14",
                pretrained="laion2b-s32b-b79k",
                device=self.device
            )
            logger.info("✅ Image model loaded: OpenCLIP-ViT-H-14")
        except Exception as e:
            logger.warning(f"Failed to load OpenCLIP: {e}")
            self.image_model = None
            self.image_processor = None
            logger.info("⚠️ Image embedding disabled")

    def embed_text(self, text: str) -> List[float]:
        """텍스트 임베딩"""
        if not text or not text.strip():
            return [0.0] * 768  # 기본 벡터

        try:
            embedding = self.text_model.encode(
                text.strip()[:512],  # 최대 512자
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Text embedding error: {e}")
            return [0.0] * 768

    def embed_image(self, image_path: str) -> Optional[List[float]]:
        """이미지 임베딩"""
        if not self.image_model or not self.image_processor:
            return None

        try:
            if not os.path.exists(image_path):
                return None

            image = Image.open(image_path).convert("RGB")
            image_tensor = self.image_processor(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                image_embedding = self.image_model.encode_image(image_tensor)

            return image_embedding.squeeze(0).cpu().numpy().tolist()
        except Exception as e:
            logger.debug(f"Image embedding error for {image_path}: {e}")
            return None

    def process_product_json(
        self,
        json_path: str,
        category: str,
        images_base_dir: str
    ) -> Optional[ProductEmbedding]:
        """JSON 제품 데이터 처리"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                product_data = json.load(f)

            # 제품 ID 추출
            product_id = Path(json_path).stem  # idx_123
            product_name = product_data.get("product_name", "Unknown")

            # 텍스트 생성 (제품명 + 명세)
            text_parts = [product_name]

            if "specifications" in product_data:
                specs = product_data["specifications"]
                if isinstance(specs, dict):
                    spec_text = " ".join(f"{k}: {v}" for k, v in specs.items())
                    text_parts.append(spec_text)

            full_text = " ".join(text_parts)

            # 텍스트 임베딩
            text_embedding = self.embed_text(full_text)

            # 이미지 임베딩
            image_embeddings = []
            if "downloaded_images" in product_data and self.image_model:
                for img_info in product_data["downloaded_images"][:3]:  # 최대 3개
                    img_path = os.path.join(images_base_dir, category, "products", img_info)
                    img_embedding = self.embed_image(img_path)
                    if img_embedding:
                        image_embeddings.append(img_embedding)

            # 메타데이터
            metadata = {
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "text_length": len(full_text),
                "num_images": len(image_embeddings),
                "specifications": product_data.get("specifications", {}),
                "print_area_url": product_data.get("print_area_url"),
            }

            return ProductEmbedding(
                product_id=product_id,
                product_name=product_name,
                category=category,
                text_embedding=text_embedding,
                image_embeddings=image_embeddings,
                metadata=metadata,
                embedding_timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Error processing {json_path}: {e}")
            return None


class QdrantVectorDB:
    """Qdrant 벡터 DB 관리"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        logger.info(f"✅ Connected to Qdrant: {host}:{port}")

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: str = "COSINE"
    ) -> bool:
        """컬렉션 생성"""
        try:
            existing_collections = [col.name for col in self.client.get_collections().collections]

            if collection_name in existing_collections:
                logger.info(f"⚠️ Collection already exists: {collection_name}")
                return True

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE if distance == "COSINE" else Distance.EUCLID
                )
            )
            logger.info(f"✅ Created collection: {collection_name} (dim: {vector_size})")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False

    def upsert_embeddings(
        self,
        collection_name: str,
        embeddings: List[ProductEmbedding],
        batch_size: int = 100
    ) -> int:
        """임베딩 벡터 업로드"""
        if not embeddings:
            logger.warning("No embeddings to upsert")
            return 0

        try:
            points = []
            for idx, emb in enumerate(embeddings):
                # 메인 텍스트 벡터로 포인트 생성
                point = PointStruct(
                    id=hash(emb.product_id) % (2**31),  # 양수 ID
                    vector=emb.text_embedding,
                    payload={
                        "product_id": emb.product_id,
                        "product_name": emb.product_name,
                        "category": emb.category,
                        "text_length": emb.metadata["text_length"],
                        "num_images": emb.metadata["num_images"],
                        "product_name_text": emb.product_name,
                        "category_text": emb.category,
                    }
                )
                points.append(point)

            # 배치 업로드
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )

            logger.info(f"✅ Upserted {len(points)} embeddings to {collection_name}")
            return len(points)

        except Exception as e:
            logger.error(f"Error upserting embeddings: {e}")
            return 0

    def verify_collection(self, collection_name: str) -> Dict[str, Any]:
        """컬렉션 검증"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "collection_name": collection_name,
                "vector_count": info.points_count,
                "vector_size": info.config.params.vectors.size,
            }
        except Exception as e:
            logger.error(f"Error verifying collection: {e}")
            return {}


class EmbeddingPipeline:
    """멀티모달 임베딩 파이프라인"""

    def __init__(
        self,
        data_dir: str,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        max_workers: int = 4
    ):
        self.data_dir = data_dir
        self.embedder = ProductEmbedder()
        self.vector_db = QdrantVectorDB(qdrant_host, qdrant_port)
        self.max_workers = max_workers

    def process_category(self, category: str) -> Tuple[List[ProductEmbedding], int]:
        """카테고리별 제품 처리"""
        category_path = os.path.join(self.data_dir, category)
        products_path = os.path.join(category_path, "products")

        if not os.path.exists(products_path):
            logger.error(f"Products directory not found: {products_path}")
            return [], 0

        json_files = sorted([f for f in os.listdir(products_path) if f.endswith(".json")])
        logger.info(f"Processing {len(json_files)} products from {category}")

        embeddings = []
        failed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.embedder.process_product_json,
                    os.path.join(products_path, json_file),
                    category,
                    os.path.dirname(category_path)
                ): json_file
                for json_file in json_files
            }

            for idx, future in enumerate(concurrent.futures.as_completed(futures)):
                json_file = futures[future]
                try:
                    result = future.result()
                    if result:
                        embeddings.append(result)
                        if (idx + 1) % 50 == 0:
                            logger.info(f"Progress: {idx + 1}/{len(json_files)} processed")
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    failed += 1

        logger.info(f"✅ Completed {category}: {len(embeddings)} success, {failed} failed")
        return embeddings, failed

    def run(self, categories: List[str] = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        if categories is None:
            categories = ["Bottle", "Jar", "CapPump"]

        logger.info(f"Starting embedding pipeline for: {categories}")

        results = {}
        all_embeddings = []

        for category in categories:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing category: {category}")
            logger.info(f"{'='*60}")

            embeddings, failed = self.process_category(category)
            all_embeddings.extend(embeddings)

            # Qdrant 업로드
            collection_name = f"products_{category.lower()}"

            if embeddings:
                self.vector_db.create_collection(collection_name)
                uploaded = self.vector_db.upsert_embeddings(
                    collection_name,
                    embeddings
                )

                info = self.vector_db.verify_collection(collection_name)
                results[category] = {
                    "processed": len(embeddings),
                    "failed": failed,
                    "uploaded": uploaded,
                    "collection_info": info
                }
            else:
                results[category] = {
                    "processed": 0,
                    "failed": failed,
                    "uploaded": 0,
                    "collection_info": None
                }

        # 통합 컬렉션 생성 (모든 제품)
        if all_embeddings:
            self.vector_db.create_collection("products_all")
            uploaded_all = self.vector_db.upsert_embeddings(
                "products_all",
                all_embeddings
            )
            info_all = self.vector_db.verify_collection("products_all")
            results["all"] = {
                "total_products": len(all_embeddings),
                "uploaded": uploaded_all,
                "collection_info": info_all
            }

        return results


def main():
    """메인 실행 함수"""
    data_dir = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_organized"

    pipeline = EmbeddingPipeline(
        data_dir=data_dir,
        qdrant_host="localhost",
        qdrant_port=6333,
        max_workers=4
    )

    results = pipeline.run(categories=["Bottle", "Jar", "CapPump"])

    # 결과 출력
    logger.info(f"\n{'='*60}")
    logger.info("Embedding Pipeline Results")
    logger.info(f"{'='*60}")

    for category, result in results.items():
        logger.info(f"\n{category}:")
        for key, value in result.items():
            logger.info(f"  {key}: {value}")

    # 결과를 JSON으로 저장
    report_path = "/Users/oypnus/Project/rag-enterprise/embedding_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"\n✅ Report saved to {report_path}")


if __name__ == "__main__":
    main()
