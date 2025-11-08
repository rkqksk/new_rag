"""
문서 수집 및 크롤링 API 엔드포인트
- 파일 업로드
- 웹 크롤링 관리
- 수집 현황 조회
"""

import logging
import os
import shutil
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# API 라우터 생성
router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])

# 전역 서비스 참조 (main.py에서 주입됨)
document_ingestion_service = None
web_crawler_service = None


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답"""

    status: str
    doc_id: str
    doc_type: str
    file_name: str
    chunks_count: int
    vectors_stored: int
    message: str
    processed_at: str


class CrawlerSourceRequest(BaseModel):
    """크롤러 소스 추가 요청"""

    source_id: str
    url: str
    name: str
    category: str = "general"
    selectors: dict = {}


class CrawlerStartRequest(BaseModel):
    """크롤러 시작 요청"""

    source_id: Optional[str] = None  # None이면 모든 소스
    use_selenium: bool = False


class SearchRequest(BaseModel):
    """문서 검색 요청"""

    query: str
    top_k: int = 5


class SearchResponse(BaseModel):
    """문서 검색 응답"""

    query: str
    results_count: int
    results: list
    timestamp: str


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Query(None),
    custom_metadata: Optional[str] = Query(None),
):
    """
    문서 파일 업로드 및 처리

    지원 형식:
    - PDF (.pdf)
    - Excel (.xlsx, .xls, .csv)
    - 이미지 (.png, .jpg, .jpeg, .gif)
    - HTML (.html, .htm)
    - 텍스트 (.txt, .md, .rst)

    Parameters:
    - file: 업로드할 파일
    - doc_type: 문서 타입 (자동 감지 시 None)
    - custom_metadata: JSON 형식의 추가 메타데이터

    Returns:
    - doc_id: 문서 ID
    - chunks_count: 생성된 청크 개수
    - vectors_stored: 저장된 벡터 개수
    """
    if not document_ingestion_service:
        raise HTTPException(status_code=500, detail="Document ingestion service not initialized")

    try:
        # 임시 파일 저장
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        try:
            with open(temp_file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # 메타데이터 파싱
            metadata = {}
            if custom_metadata:
                import json

                try:
                    metadata = json.loads(custom_metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid metadata JSON: {custom_metadata}")

            # 문서 처리
            result = await document_ingestion_service.ingest_file(
                file_path=temp_file_path, doc_type=doc_type, metadata=metadata
            )

            return DocumentUploadResponse(
                status="success",
                doc_id=result["doc_id"],
                doc_type=result["doc_type"],
                file_name=result["file_name"],
                chunks_count=result["chunks_count"],
                vectors_stored=result["vectors_stored"],
                message=f"Document processed successfully: {result['chunks_count']} chunks",
                processed_at=result["processed_at"],
            )

        finally:
            # 임시 파일 정리
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing document: {str(e)}")


@router.post("/crawler/source/add")
async def add_crawler_source(request: CrawlerSourceRequest):
    """
    크롤러 소스 추가

    Parameters:
    - source_id: 소스 ID (고유값)
    - url: 크롤링할 URL
    - name: 소스 이름
    - category: 카테고리 (product, msds, supplier, etc.)
    - selectors: CSS 선택자 매핑 (예: {"title": ".product-title"})
    """
    if not web_crawler_service:
        raise HTTPException(status_code=500, detail="Web crawler service not initialized")

    try:
        from app.services.web_crawler_service import WebSource

        source = WebSource(
            url=request.url,
            selectors=request.selectors,
            name=request.name,
            category=request.category,
        )

        web_crawler_service.add_source(request.source_id, source)

        return {
            "status": "success",
            "source_id": request.source_id,
            "message": f"Source added: {request.name}",
        }

    except Exception as e:
        logger.error(f"Error adding crawler source: {e}")
        raise HTTPException(status_code=400, detail=f"Error adding source: {str(e)}")


@router.post("/crawler/start")
async def start_crawler(request: CrawlerStartRequest, background_tasks: BackgroundTasks):
    """
    웹 크롤링 시작

    Parameters:
    - source_id: 특정 소스만 크롤링 (None이면 모든 소스)
    - use_selenium: JavaScript 렌더링 필요 여부

    Returns:
    - task_id: 백그라운드 작업 ID
    - status: 작업 상태
    """
    if not web_crawler_service:
        raise HTTPException(status_code=500, detail="Web crawler service not initialized")

    try:
        task_id = f"crawl_{datetime.utcnow().timestamp()}"

        if request.source_id:
            # 특정 소스 크롤링
            background_tasks.add_task(
                web_crawler_service.crawl_source, request.source_id, request.use_selenium
            )
        else:
            # 모든 소스 크롤링
            background_tasks.add_task(web_crawler_service.crawl_all_sources)

        return {
            "status": "started",
            "task_id": task_id,
            "source_id": request.source_id,
            "message": f"Crawler started (task_id: {task_id})",
        }

    except Exception as e:
        logger.error(f"Error starting crawler: {e}")
        raise HTTPException(status_code=400, detail=f"Error starting crawler: {str(e)}")


@router.get("/crawler/sources")
async def get_crawler_sources():
    """
    모든 크롤러 소스 조회

    Returns:
    - sources: 소스 목록
    """
    if not web_crawler_service:
        raise HTTPException(status_code=500, detail="Web crawler service not initialized")

    try:
        sources = web_crawler_service.get_sources_status()

        return {
            "status": "success",
            "sources_count": len(sources),
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting crawler sources: {e}")
        raise HTTPException(status_code=400, detail=f"Error retrieving sources: {str(e)}")


@router.get("/crawler/history")
async def get_crawler_history(source_id: Optional[str] = Query(None)):
    """
    크롤링 히스토리 조회

    Parameters:
    - source_id: 특정 소스의 히스토리만 조회 (선택사항)

    Returns:
    - history: 크롤링 히스토리
    """
    if not web_crawler_service:
        raise HTTPException(status_code=500, detail="Web crawler service not initialized")

    try:
        history = web_crawler_service.get_crawl_history(source_id)

        return {
            "status": "success",
            "records_count": len(history),
            "history": history,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting crawler history: {e}")
        raise HTTPException(status_code=400, detail=f"Error retrieving history: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    업로드된 문서에서 검색

    Parameters:
    - query: 검색 쿼리
    - top_k: 반환할 상위 결과 개수 (기본값: 5)

    Returns:
    - results: 유사도 점수와 함께 검색 결과
    """
    if not document_ingestion_service:
        raise HTTPException(status_code=500, detail="Document ingestion service not initialized")

    try:
        results = await document_ingestion_service.search_documents(
            query=request.query, top_k=request.top_k
        )

        return SearchResponse(
            query=request.query,
            results_count=len(results),
            results=results,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=400, detail=f"Error searching documents: {str(e)}")


@router.get("/stats")
async def get_ingestion_stats():
    """
    수집 시스템 통계 조회

    Returns:
    - document_stats: 문서 통계
    - crawler_stats: 크롤러 통계
    """
    if not document_ingestion_service:
        raise HTTPException(status_code=500, detail="Document ingestion service not initialized")

    try:
        doc_stats = document_ingestion_service.get_collection_stats()
        crawler_stats = {
            "total_sources": len(web_crawler_service.sources) if web_crawler_service else 0,
            "crawl_history_count": (
                len(web_crawler_service.crawl_history) if web_crawler_service else 0
            ),
            "last_crawl": (
                web_crawler_service.crawl_history[-1]["crawled_at"]
                if web_crawler_service and web_crawler_service.crawl_history
                else None
            ),
        }

        return {
            "status": "success",
            "document_stats": doc_stats,
            "crawler_stats": crawler_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting ingestion stats: {e}")
        raise HTTPException(status_code=400, detail=f"Error retrieving stats: {str(e)}")
