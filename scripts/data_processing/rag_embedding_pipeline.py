#!/usr/bin/env python3
"""
RAG 임베딩 파이프라인
crawled_products_organized 폴더의 제품 데이터를 처리하여 Qdrant에 저장

처리 단계:
1. JSON 제품 데이터 로드
2. 청킹 (제품 정보를 의미 단위로 분할)
3. 임베딩 (텍스트를 벡터로 변환)
4. Qdrant 업로드
"""

import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.chunking_agent import chunk_text
from agents.vector_db_loader_agent import upload_to_qdrant

# 임베딩 함수를 여기에 정의 (메모리 효율성을 위해)
from sentence_transformers import SentenceTransformer

# 전역 모델 (한 번만 로드)
_embedding_model = None

def get_embedding_model(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """임베딩 모델 싱글톤"""
    global _embedding_model
    if _embedding_model is None:
        print(f"임베딩 모델 로딩 중: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model

def embed_text(text, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """텍스트를 벡터로 변환"""
    model = get_embedding_model(model_name)
    embedding = model.encode([text], show_progress_bar=False)[0]
    return embedding.tolist()


def process_product_json(json_path, category):
    """제품 JSON 파일을 텍스트로 변환"""
    with open(json_path, encoding="utf-8") as f:
        product = json.load(f)

    # 제품 정보를 검색 가능한 텍스트로 변환
    text_parts = []

    # 제품명
    if product.get("product_name"):
        text_parts.append(f"제품명: {product['product_name']}")

    # 카테고리
    text_parts.append(f"카테고리: {category}")

    # 사양 정보
    if product.get("specifications"):
        specs_text = " ".join([f"{k}: {v}" for k, v in product["specifications"].items()])
        text_parts.append(f"사양: {specs_text}")

    # URL
    if product.get("url"):
        text_parts.append(f"URL: {product['url']}")

    # IDX
    if product.get("idx"):
        text_parts.append(f"제품코드: {product['idx']}")

    combined_text = "\n".join(text_parts)

    return {
        "text": combined_text,
        "metadata": {
            "product_name": product.get("product_name", ""),
            "category": category,
            "idx": product.get("idx", ""),
            "url": product.get("url", ""),
            "has_image": len(product.get("images", [])) > 0
        }
    }


def process_category(category_path, category_name, output_base, model_name):
    """카테고리별 제품 처리"""
    products_path = category_path / "products"

    if not products_path.exists():
        print(f"[경고] 제품 폴더 없음: {products_path}")
        return []

    json_files = list(products_path.glob("*.json"))
    print(f"\n[{category_name}] {len(json_files)}개 제품 파일 발견")

    embeddings = []
    metadata_list = []

    for idx, json_file in enumerate(json_files, 1):
        try:
            # 1. JSON → 텍스트 변환
            processed = process_product_json(json_file, category_name)
            text = processed["text"]
            meta = processed["metadata"]

            # 2. 청킹 (필요시)
            chunks = chunk_text(text, chunk_size=500, overlap=50)

            # 3. 각 청크 임베딩
            for chunk_idx, chunk in enumerate(chunks):
                try:
                    embedding = embed_text(chunk, model_name)
                    embeddings.append(embedding)
                    metadata_list.append({
                        **meta,
                        "chunk_idx": chunk_idx,
                        "chunk_text": chunk[:200],  # 처음 200자만 저장
                        "source_file": str(json_file.name)
                    })
                except Exception as e:
                    print(f"[오류] 임베딩 실패 {json_file.name} chunk{chunk_idx}: {e}")

            if idx % 50 == 0:
                print(f"  진행: {idx}/{len(json_files)} 처리 완료")

        except Exception as e:
            print(f"[오류] {json_file.name} 처리 실패: {e}")
            continue

    print(f"[{category_name}] 총 {len(embeddings)}개 임베딩 생성")
    return embeddings, metadata_list


def main():
    """메인 파이프라인 실행"""
    print("=" * 60)
    print("RAG 임베딩 파이프라인 시작")
    print("=" * 60)

    # 설정
    data_root = project_root / "data" / "crawled_products_organized"
    output_base = project_root / "data" / "rag_embeddings"
    output_base.mkdir(parents=True, exist_ok=True)

    # 임베딩 모델
    model_name = "sentence-transformers/all-MiniLM-L6-v2"

    # Qdrant 설정
    qdrant_host = "localhost"
    qdrant_port = 6333

    # 카테고리별 처리
    categories = ["Bottle", "CapPump", "Jar"]

    for category in categories:
        category_path = data_root / category

        if not category_path.exists():
            print(f"[건너뛰기] 카테고리 폴더 없음: {category}")
            continue

        print(f"\n{'=' * 60}")
        print(f"카테고리: {category}")
        print(f"{'=' * 60}")

        # 처리
        embeddings, metadata_list = process_category(
            category_path, category, output_base,
            model_name
        )

        if not embeddings:
            print(f"[건너뛰기] {category} - 임베딩 없음")
            continue

        # Qdrant 업로드
        collection_name = f"products_{category.lower()}"

        try:
            uploaded_count = upload_to_qdrant(
                embeddings, metadata_list, collection_name,
                qdrant_host, qdrant_port
            )
            print(f"[완료] {category} - Qdrant에 {uploaded_count}개 벡터 업로드")
        except Exception as e:
            print(f"[오류] {category} - Qdrant 업로드 실패: {e}")

    print("\n" + "=" * 60)
    print("RAG 임베딩 파이프라인 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
