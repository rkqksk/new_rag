"""
Q&A Routes
"""

from fastapi import APIRouter, HTTPException

from app.services.qa_service import search_qa_qdrant

router = APIRouter(prefix="/api/v1", tags=["qa"])


@router.get("/qa/search")
async def api_search_qa(query: str, limit: int = 1000):
    """Search Q&A knowledge base"""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    results = await search_qa_qdrant(query, limit)

    return {"query": query, "total": len(results), "results": results}
