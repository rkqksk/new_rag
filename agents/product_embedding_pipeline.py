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
import hashlib
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
        text_model: str = "all-MiniLM-L6-v2",
        image_model: str = "openai/ViT-H-14",
        device: str = "auto"
    ):
        # Use MPS (Metal Performance Shaders) for Apple Silicon M1/M2/M3/M4
        if device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device
        logger.info(f"Using device: {self.device}")

        # 텍스트 모델 - PRIMARY: all-MiniLM-L6-v2 (fast, efficient, 384 dimensions)
        try:
            self.text_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                device=self.device
            )
            logger.info("✅ Primary text model loaded: all-MiniLM-L6-v2 (384 dim)")
        except Exception as e:
            logger.error(f"Failed to load all-MiniLM-L6-v2: {e}")
            raise

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
            return [0.0] * 384  # 기본 벡터 (all-MiniLM-L6-v2 dimension)

        try:
            embedding = self.text_model.encode(
                text.strip()[:512],  # 최대 512자
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Text embedding error: {e}")
            return [0.0] * 384  # all-MiniLM-L6-v2 dimension

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
                    # Handle both dict and string formats
                    if isinstance(img_info, dict):
                        filename = img_info.get("filename", "")
                    else:
                        filename = img_info

                    if not filename:
                        continue

                    # Try to find image in category/material/images directory
                    img_path = os.path.join(images_base_dir, category, "images", filename)
                    img_embedding = self.embed_image(img_path)
                    if img_embedding:
                        image_embeddings.append(img_embedding)

            # 메타데이터 (가격 정보 포함)
            metadata = {
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "text_length": len(full_text),
                "num_images": len(image_embeddings),
                "specifications": product_data.get("specifications", {}),
                "print_area_url": product_data.get("print_area_url"),
            }

            # 가격 정보 추가 (있는 경우)
            pricing_data = product_data.get("pricing", {})
            if pricing_data:
                metadata["pricing"] = pricing_data

            # product_list_info 추가 (Cap/Pump의 경우)
            product_list_info = product_data.get("product_list_info")
            if product_list_info:
                metadata["product_list_info"] = product_list_info

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
        text_dim: int = 384,  # all-MiniLM-L6-v2 dimension
        image_dim: int = 1024,  # OpenCLIP-ViT-H-14 dimension
        distance: str = "COSINE"
    ) -> bool:
        """컬렉션 생성 (Multi-Vector: text + image)"""
        try:
            existing_collections = [col.name for col in self.client.get_collections().collections]

            if collection_name in existing_collections:
                logger.info(f"⚠️ Collection already exists: {collection_name}")
                return True

            # Multi-vector configuration: named vectors for text and image
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "text": VectorParams(
                        size=text_dim,
                        distance=Distance.COSINE if distance == "COSINE" else Distance.EUCLID
                    ),
                    "image": VectorParams(
                        size=image_dim,
                        distance=Distance.COSINE if distance == "COSINE" else Distance.EUCLID
                    )
                }
            )
            logger.info(f"✅ Created multi-vector collection: {collection_name} (text: {text_dim}, image: {image_dim})")
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
                # Deterministic hash using MD5 (first 8 bytes as integer)
                hash_bytes = hashlib.md5(emb.product_id.encode()).digest()[:8]
                deterministic_id = int.from_bytes(hash_bytes, byteorder='big') % (2**31)

                # Multi-vector point: text + image embeddings
                # Use first image embedding if available, else zero vector
                image_vector = (
                    emb.image_embeddings[0] if emb.image_embeddings
                    else [0.0] * 1024  # Default zero vector for products without images
                )

                # Payload 구성 (가격 및 제품 정보 포함)
                payload = {
                    "product_id": emb.product_id,
                    "product_name": emb.product_name,
                    "category": emb.category,
                    "text_length": emb.metadata["text_length"],
                    "num_images": emb.metadata["num_images"],
                    "specifications": emb.metadata.get("specifications", {}),
                    "print_area_url": emb.metadata.get("print_area_url"),
                }

                # 가격 정보 추가
                if "pricing" in emb.metadata:
                    payload["pricing"] = emb.metadata["pricing"]

                # 제품 리스트 정보 추가
                if "product_list_info" in emb.metadata:
                    payload["product_list_info"] = emb.metadata["product_list_info"]

                point = PointStruct(
                    id=deterministic_id,  # 양수 deterministic ID
                    vector={
                        "text": emb.text_embedding,  # 384-dim
                        "image": image_vector        # 1024-dim
                    },
                    payload=payload
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
        """카테고리별 제품 처리 (NEW: Category/Material/products 구조)"""
        category_path = os.path.join(self.data_dir, category)

        if not os.path.exists(category_path):
            logger.error(f"Category directory not found: {category_path}")
            return [], 0

        materials = ["PE", "PET", "PETG", "PP", "Other"]
        embeddings = []
        failed = 0
        total_files = 0

        # Collect all JSON files across all materials
        all_json_files = []
        for material in materials:
            products_path = os.path.join(category_path, material, "products")

            if not os.path.exists(products_path):
                logger.debug(f"Skipping {category}/{material} - directory not found")
                continue

            json_files = [
                (os.path.join(products_path, f), f, material)
                for f in os.listdir(products_path)
                if f.endswith(".json")
            ]
            all_json_files.extend(json_files)
            total_files += len(json_files)
            logger.info(f"Found {len(json_files)} products in {category}/{material}")

        logger.info(f"Processing total {total_files} products from {category} across all materials")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.embedder.process_product_json,
                    json_path,
                    f"{category}/{material}",  # Include material in category label
                    self.data_dir
                ): (json_file, material)
                for json_path, json_file, material in all_json_files
            }

            for idx, future in enumerate(concurrent.futures.as_completed(futures)):
                json_file, material = futures[future]
                try:
                    result = future.result()
                    if result:
                        embeddings.append(result)
                        if (idx + 1) % 50 == 0:
                            logger.info(f"Progress: {idx + 1}/{total_files} processed")
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error processing {json_file} ({material}): {e}")
                    failed += 1

        logger.info(f"✅ Completed {category}: {len(embeddings)} success, {failed} failed")
        return embeddings, failed

    def run(self, categories: List[str] = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        if categories is None:
            categories = ["Bottle", "Jar", "Cap", "Pump"]

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
    data_dir = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final"

    pipeline = EmbeddingPipeline(
        data_dir=data_dir,
        qdrant_host="localhost",
        qdrant_port=6333,
        max_workers=4
    )

    results = pipeline.run(categories=["Bottle", "Jar", "Cap", "Pump"])

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
