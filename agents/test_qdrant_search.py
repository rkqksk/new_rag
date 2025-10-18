"""
Qdrant 벡터 검색 테스트
임베딩된 제품 데이터의 검색 기능 검증
"""

import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Qdrant 클라이언트 초기화
client = QdrantClient(host="localhost", port=6333)
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

def search_products(query: str, collection: str = "products_all", top_k: int = 5):
    """제품 검색"""
    print(f"\n🔍 검색어: '{query}'")
    print(f"컬렉션: {collection}")
    print(f"상위 {top_k}개 결과:\n")

    # 쿼리 임베딩
    query_embedding = embedder.encode(query, convert_to_numpy=True).tolist()

    # Qdrant 검색
    results = client.search(
        collection_name=collection,
        query_vector=query_embedding,
        limit=top_k,
        score_threshold=0.0
    )

    if not results:
        print("검색 결과 없음")
        return

    for idx, result in enumerate(results, 1):
        print(f"{idx}. ID: {result.id}")
        print(f"   제품명: {result.payload.get('product_name', 'N/A')}")
        print(f"   카테고리: {result.payload.get('category', 'N/A')}")
        print(f"   유사도 점수: {result.score:.4f}")
        print()


def get_collection_info():
    """컬렉션 정보 조회"""
    print("\n" + "="*60)
    print("Qdrant 컬렉션 정보")
    print("="*60)

    try:
        collections = client.get_collections()
        print(f"\n✅ Qdrant 연결 성공")
        print(f"   컬렉션: {[col.name for col in collections.collections]}")
    except Exception as e:
        print(f"\n⚠️ 컬렉션 정보 조회 중 오류: {e}")


def main():
    """메인 테스트"""

    # 컬렉션 정보 출력
    get_collection_info()

    # 테스트 검색 쿼리
    test_queries = [
        "브로우 용기",
        "50ml 병",
        "유리 용기",
        "플라스틱 커버",
        "뚜껑 펌프",
    ]

    print("\n\n" + "="*60)
    print("검색 테스트")
    print("="*60)

    for query in test_queries:
        search_products(query, collection="products_all", top_k=3)

    # 카테고리별 검색
    print("\n\n" + "="*60)
    print("카테고리별 검색")
    print("="*60)

    search_products("용기 병", collection="products_bottle", top_k=3)
    search_products("뚜껑", collection="products_cappump", top_k=3)


if __name__ == "__main__":
    main()
