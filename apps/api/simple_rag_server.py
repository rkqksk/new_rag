#!/usr/bin/env python3
"""
청진코리아 제품 RAG 서버 (간단 버전)
- chungjinkorea 데이터만 사용
- 벡터 검색 + LLM 응답
"""

from typing import List

import ollama
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient

app = FastAPI(title="청진코리아 제품 검색 API")

# Qdrant 클라이언트
client = QdrantClient(path="./data/chungjinkorea_qdrant")
COLLECTION_NAME = "chungjin_products"
MODEL_NAME = "nomic-embed-text"
LLM_MODEL = "llama3.1:8b"


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    product_code: str
    product_name: str
    category: str
    material: str
    specifications: dict
    score: float


class RAGRequest(BaseModel):
    question: str
    top_k: int = 5


class RAGResponse(BaseModel):
    answer: str
    sources: List[SearchResult]


def embed_text(text: str) -> List[float]:
    """텍스트를 벡터로 변환"""
    response = ollama.embeddings(model=MODEL_NAME, prompt=text)
    return response["embedding"]


@app.get("/")
async def root():
    return {
        "message": "청진코리아 제품 검색 API",
        "endpoints": {"/search": "벡터 검색", "/ask": "RAG 질의응답", "/stats": "통계 정보"},
    }


@app.post("/search", response_model=List[SearchResult])
async def search_products(request: SearchRequest):
    """제품 벡터 검색"""
    try:
        # 쿼리 벡터화
        query_vector = embed_text(request.query)

        # Qdrant 검색
        results = client.search(
            collection_name=COLLECTION_NAME, query_vector=query_vector, limit=request.top_k
        )

        # 결과 변환
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    product_code=result.payload.get("product_code", ""),
                    product_name=result.payload.get("product_name", ""),
                    category=result.payload.get("category", ""),
                    material=result.payload.get("material", ""),
                    specifications=result.payload.get("specifications", {}),
                    score=result.score,
                )
            )

        return search_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=RAGResponse)
async def ask_question(request: RAGRequest):
    """RAG 기반 질의응답"""
    try:
        # 1. 관련 제품 검색
        query_vector = embed_text(request.question)

        results = client.search(
            collection_name=COLLECTION_NAME, query_vector=query_vector, limit=request.top_k
        )

        if not results:
            return RAGResponse(answer="관련 제품을 찾을 수 없습니다.", sources=[])

        # 2. 컨텍스트 생성
        context_parts = []
        sources = []

        for i, result in enumerate(results):
            product_code = result.payload.get("product_code", "")
            product_name = result.payload.get("product_name", "")
            specs = result.payload.get("specifications", {})

            context_parts.append(f"제품 {i+1}: {product_name} ({product_code})\n" f"사양: {specs}")

            sources.append(
                SearchResult(
                    product_code=product_code,
                    product_name=product_name,
                    category=result.payload.get("category", ""),
                    material=result.payload.get("material", ""),
                    specifications=specs,
                    score=result.score,
                )
            )

        context = "\n\n".join(context_parts)

        # 3. LLM 응답 생성
        prompt = f"""당신은 청진코리아 제품 전문가입니다.
아래 제품 정보를 바탕으로 사용자 질문에 답변하세요.

제품 정보:
{context}

사용자 질문: {request.question}

답변 (간결하고 정확하게):"""

        response = ollama.generate(model=LLM_MODEL, prompt=prompt)

        answer = response["response"].strip()

        return RAGResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """통계 정보"""
    try:
        collection_info = client.get_collection(COLLECTION_NAME)

        return {
            "collection": COLLECTION_NAME,
            "total_products": collection_info.points_count,
            "vector_dimension": collection_info.config.params.vectors.size,
            "model": {"embedding": MODEL_NAME, "llm": LLM_MODEL},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("=" * 60)
    print("청진코리아 제품 RAG 서버 시작")
    print("=" * 60)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Embedding Model: {MODEL_NAME}")
    print(f"LLM Model: {LLM_MODEL}")
    print(f"Server: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
