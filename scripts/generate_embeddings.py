#!/usr/bin/env python3
"""
임베딩 생성 및 Qdrant 업로드 스크립트
Generate Embeddings and Upload to Qdrant

목적: Atomic Chunks → Embeddings → Qdrant 업로드
"""

import sys
import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_chunks(chunks_path: Path) -> List[Dict]:
    """청크 데이터 로드"""
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {chunks_path}")
    return chunks


def generate_embeddings(chunks: List[Dict], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    임베딩 생성

    Args:
        chunks: 청크 리스트
        model_name: Sentence Transformer 모델명

    Returns:
        numpy array of embeddings
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Error: sentence-transformers not installed")
        print("Install with: pip install sentence-transformers")
        return None

    print(f"\n[Embedding Generation]")
    print(f"Model: {model_name}")

    # Load model
    print("Loading model...")
    model = SentenceTransformer(model_name)

    # Extract texts
    texts = [chunk['text'] for chunk in chunks]

    # Generate embeddings with progress bar
    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32
    )

    print(f"Generated embeddings shape: {embeddings.shape}")
    return embeddings


def save_embeddings(embeddings: np.ndarray, output_path: Path):
    """임베딩 저장 (numpy format)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    np.save(output_path, embeddings)
    print(f"Saved embeddings to {output_path}")


def upload_to_qdrant(
    chunks: List[Dict],
    embeddings: np.ndarray,
    collection_name: str = "products_atomic",
    qdrant_url: str = "http://localhost:6333"
):
    """
    Qdrant에 업로드

    Args:
        chunks: 청크 데이터
        embeddings: 임베딩 벡터
        collection_name: Collection 이름
        qdrant_url: Qdrant 서버 URL
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
    except ImportError:
        print("Error: qdrant-client not installed")
        print("Install with: pip install qdrant-client")
        return False

    print(f"\n[Qdrant Upload]")
    print(f"URL: {qdrant_url}")
    print(f"Collection: {collection_name}")

    # Connect to Qdrant
    try:
        client = QdrantClient(url=qdrant_url)
        print("✓ Connected to Qdrant")
    except Exception as e:
        print(f"✗ Failed to connect to Qdrant: {e}")
        print("\nMake sure Qdrant is running:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        return False

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name in collection_names:
        print(f"⚠ Collection '{collection_name}' already exists")
        response = input("Delete and recreate? (y/N): ")
        if response.lower() == 'y':
            client.delete_collection(collection_name)
            print(f"✓ Deleted existing collection")
        else:
            print("Skipping upload")
            return False

    # Create collection
    vector_size = embeddings.shape[1]
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    print(f"✓ Created collection (vector size: {vector_size})")

    # Prepare points
    print("Preparing points...")
    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=idx,
            vector=embedding.tolist(),
            payload=chunk['metadata']
        )
        points.append(point)

    # Upload in batches
    batch_size = 100
    total_batches = (len(points) + batch_size - 1) // batch_size

    print(f"Uploading {len(points)} points in {total_batches} batches...")

    for i in tqdm(range(0, len(points), batch_size), desc="Upload"):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch
        )

    print(f"✓ Uploaded {len(points)} points to Qdrant")

    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"\nCollection info:")
    print(f"  Points count: {collection_info.points_count}")
    print(f"  Vector size: {collection_info.config.params.vectors.size}")

    return True


def main():
    """메인 실행 함수"""
    print("="*80)
    print("EMBEDDING GENERATION & QDRANT UPLOAD")
    print("="*80)

    # Paths
    chunks_path = PROJECT_ROOT / "data/embeddings/atomic_chunks.json"
    embeddings_path = PROJECT_ROOT / "data/embeddings/atomic_chunks_embeddings.npy"

    # Step 1: Load chunks
    print("\n[Step 1] Loading chunks...")
    chunks = load_chunks(chunks_path)

    # Step 2: Generate embeddings
    print("\n[Step 2] Generating embeddings...")
    embeddings = generate_embeddings(chunks)

    if embeddings is None:
        print("Failed to generate embeddings")
        return 1

    # Step 3: Save embeddings
    print("\n[Step 3] Saving embeddings...")
    save_embeddings(embeddings, embeddings_path)

    # Step 4: Upload to Qdrant
    print("\n[Step 4] Uploading to Qdrant...")
    success = upload_to_qdrant(chunks, embeddings)

    if success:
        print("\n" + "="*80)
        print("✅ EMBEDDING GENERATION & UPLOAD COMPLETED")
        print("="*80)
        print(f"\nEmbeddings: {embeddings_path}")
        print(f"Qdrant Collection: products_atomic")
        print(f"Total Points: {len(chunks)}")
        print("\nReady for search!")
        return 0
    else:
        print("\n⚠ Qdrant upload skipped or failed")
        print("Embeddings saved locally. Upload manually later.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
