import os
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

def load_embeddings_from_folder(embedding_folder):
    """임베딩 폴더에서 벡터와 메타데이터 로드"""
    embeddings, metadata = [], []
    for fname in sorted(os.listdir(embedding_folder)):
        if fname.endswith('_embedding.json'):
            with open(os.path.join(embedding_folder, fname), encoding="utf-8") as f:
                emb_data = json.load(f)
                embeddings.append(emb_data["embedding"])
                metadata.append({
                    "chunk_file": emb_data["chunk_file"],
                    "text_length": emb_data["text_length"],
                    "embedding_dim": emb_data["embedding_dim"]
                })
    return embeddings, metadata if embeddings else (None, None)

def upload_to_qdrant(embeddings, metadata, collection_name, qdrant_host="localhost", qdrant_port=6333):
    """Qdrant 벡터DB에 임베딩 업로드"""
    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # 컬렉션 존재 확인 및 생성
    collections = client.get_collections().collections
    collection_exists = any(col.name == collection_name for col in collections)

    if not collection_exists:
        vector_size = metadata[0]["embedding_dim"]
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"[생성] Qdrant 컬렉션: {collection_name} (dim: {vector_size})")
    else:
        print(f"[존재] Qdrant 컬렉션: {collection_name}")

    # 포인트 생성 및 업로드
    points = []
    for idx, (vector, meta) in enumerate(zip(embeddings, metadata)):
        point = PointStruct(
            id=idx,
            vector=vector,
            payload={
                "chunk_file": meta["chunk_file"],
                "text_length": meta["text_length"],
                "embedding_dim": meta["embedding_dim"]
            }
        )
        points.append(point)

    client.upsert(
        collection_name=collection_name,
        points=points
    )

    return len(points)

def run_loader_from_config(config_path):
    """설정 파일 기반 Qdrant 벡터DB 적재"""
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    qdrant_host = config.get("qdrant_host", "localhost")
    qdrant_port = config.get("qdrant_port", 6333)

    for job in config["vector_db_loader_jobs"]:
        embedding_folder = job["embedding_folder"]
        collection_name = job["collection_name"]

        print(f"\n=== 벡터DB 적재 작업 시작: {embedding_folder} → {collection_name} ===")

        embeddings, metadata = load_embeddings_from_folder(embedding_folder)
        if embeddings is None or metadata is None:
            print(f"[오류] 벡터 임베딩 로드 실패: {embedding_folder}")
            continue

        print(f"로드된 임베딩 개수: {len(embeddings)}")

        uploaded_count = upload_to_qdrant(
            embeddings, metadata, collection_name, qdrant_host, qdrant_port
        )

        print(f"[완료] Qdrant에 {uploaded_count}개 벡터 업로드 완료")

if __name__ == "__main__":
    config_fn = input("config 파일 (예: config/vector_db_loader_config.json): ").strip()
    run_loader_from_config(config_fn)
