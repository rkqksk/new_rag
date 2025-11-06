"""Search API Endpoints - Complete Implementation"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from app.services.search_service import SearchService
from app.dependencies.services import get_search_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: int = 20
    use_cache: bool = True

class SearchResponse(BaseModel):
    results: List[dict]
    total: int
    query: str
    session_id: Optional[str]
    cached: bool = False

@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service)
):
    """
    Tri-modal search with personalization
    
    Features:
    - Vector similarity search
    - Query routing
    - Cross-encoder re-ranking
    - Personalization
    - Compatibility filtering
    - Caching
    """
    result = await service.search(
        query=request.query,
        session_id=request.session_id,
        top_k=request.top_k,
        use_cache=request.use_cache
    )
    
    return SearchResponse(**result)

@router.post("/image")
async def image_search(
    image: UploadFile = File(...),
    session_id: Optional[str] = None,
    top_k: int = 20,
    service: SearchService = Depends(get_search_service)
):
    """Image-based search"""
    # Save uploaded file temporarily
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
        contents = await image.read()
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        result = await service.image_search(
            image_path=tmp_path,
            session_id=session_id,
            top_k=top_k
        )
        return result
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/hybrid")
async def hybrid_search(
    query: Optional[str] = None,
    image: Optional[UploadFile] = File(None),
    text_weight: float = 0.6,
    image_weight: float = 0.4,
    session_id: Optional[str] = None,
    top_k: int = 20,
    service: SearchService = Depends(get_search_service)
):
    """Hybrid search (text + image)"""
    image_path = None
    
    if image:
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
            contents = await image.read()
            tmp.write(contents)
            image_path = tmp.name
    
    try:
        result = await service.hybrid_search(
            query=query,
            image_path=image_path,
            text_weight=text_weight,
            image_weight=image_weight,
            session_id=session_id,
            top_k=top_k
        )
        return result
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
