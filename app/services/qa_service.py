"""
Q&A Service
Handles Q&A knowledge base search via Qdrant
"""
from typing import List, Dict, Any
import httpx
from app.services.embedding_service import generate_embedding


async def search_qa_qdrant(query: str, limit: int = 1000, qdrant_url: str = "http://localhost:6333") -> List[Dict[str, Any]]:
    """Search Q&A knowledge base using Qdrant VECTOR SIMILARITY SEARCH
    
    Args:
        query: Search query
        limit: Maximum results
        qdrant_url: Qdrant API URL
        
    Returns:
        List of Q&A results with scores
    """
    try:
        # Step 1: Generate embedding for the query
        query_vector = await generate_embedding(query)

        if not query_vector:
            print("Failed to generate query embedding")
            return []

        # Step 2: Perform vector similarity search in Qdrant
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{qdrant_url}/collections/cosmetic_packaging/points/search',
                json={
                    "vector": query_vector,
                    "limit": limit,
                    "with_payload": True,
                    "with_vector": False
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                points = data.get('result', [])

                results = []
                for point in points:
                    payload = point.get('payload', {})

                    # Extract question and answer from text field
                    text = payload.get('text', '')
                    question = ''
                    answer = ''

                    if '질문:' in text and '답변:' in text:
                        parts = text.split('답변:', 1)
                        question = parts[0].replace('질문:', '').strip()
                        answer = parts[1].strip()
                    else:
                        # Fallback: try separate fields
                        question = payload.get('question', '')
                        answer = payload.get('answer', '')

                    results.append({
                        'qa_id': payload.get('qa_id', ''),
                        'question': question,
                        'answer': answer,
                        'keywords': payload.get('keywords', []),
                        'score': point.get('score', 0.0)
                    })

                return results

    except Exception as e:
        print(f"Q&A search error: {e}")

    return []
