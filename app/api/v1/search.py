"""Search API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: int = 20

class SearchResponse(BaseModel):
    results: List[dict]
    total: int
    session_id: str

@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Tri-modal search with personalization"""
    # TODO: Integrate SearchService
    return SearchResponse(
        results=[],
        total=0,
        session_id=request.session_id or "default"
    )

@router.post("/image")
async def image_search(image_file: bytes):
    """Image-based search"""
    return {"message": "Image search endpoint"}
