"""
RAG Enterprise API Server
Basic implementation for document upload and search
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import redis
import psycopg2
from typing import List, Dict, Any
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from pydantic import BaseModel

# Import dependency injection
from app.core.dependencies import (
    get_config,
    get_qdrant_client,
    get_redis_client,
    get_embedding_model,
    get_rag_qa_service,
    get_consultation_service,
    get_document_ingestion_service,
)

# Import metrics and middleware
from app.core.metrics import REGISTRY
from app.core.middleware import MetricsMiddleware

# Import schemas
from app.models.schemas import QARequest, QAResponse, ConsultationRequest, ConsultationResponse

# Import route handlers
from app.api import dashboard_routes, query_routes, ingestion_routes
from app.api.routes import health as health_routes
# Note: workflow_routes has agent dependencies - loaded lazily if needed

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="RAG Enterprise API",
    description="Document processing and semantic search system",
    version="1.0.0"
)

# Get configuration (initializes all validation)
_config = get_config()

# Add metrics middleware (must be added first for proper wrapping)
app.add_middleware(MetricsMiddleware)

# Add CORS middleware with configuration from DI
app.add_middleware(
    CORSMiddleware,
    allow_origins=_config.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Register routers (services are injected via FastAPI DI)
app.include_router(health_routes.router)      # Health check & monitoring endpoints
app.include_router(query_routes.router)       # Query routing with Ollama LLMs
app.include_router(ingestion_routes.router)   # Document ingestion & crawling
app.include_router(dashboard_routes.router)   # Dashboard & monitoring
# Note: workflow_routes disabled due to agent module dependencies (will be lazy-loaded if needed)

# Mount static files
import os.path as osp
static_dir = osp.join(osp.dirname(__file__), '..', 'static')
if osp.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Collection name
COLLECTION_NAME = "documents"

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting RAG Enterprise API...")

    # Get config to validate environment
    config = get_config()
    logger.info(f"✅ Configuration validated")

    # Initialize Qdrant collection
    try:
        qdrant = get_qdrant_client(config)
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=config.embedding_dim,
                distance=Distance.COSINE
            ),
        )
        logger.info(
            f"✅ Qdrant collection initialized "
            f"(dimension: {config.embedding_dim})"
        )
    except Exception as e:
        logger.info(f"ℹ️ Collection already exists or creation skipped: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down RAG Enterprise API...")


@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard"""
    return {
        "message": "RAG Enterprise API",
        "version": "1.0.0",
        "status": "running",
        "dashboard": "/static/index.html",
        "docs": "/docs"
    }

@app.get("/dashboard")
async def dashboard():
    """Dashboard page"""
    dashboard_path = osp.join(osp.dirname(__file__), '..', 'static', 'index.html')
    if osp.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"error": "Dashboard not found"}

@app.get("/chat")
async def chat():
    """Q&A Chat interface"""
    chat_path = osp.join(osp.dirname(__file__), '..', 'static', 'qa_chat.html')
    if osp.exists(chat_path):
        return FileResponse(chat_path)
    return {"error": "Chat interface not found"}

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Save file
        doc_id = str(uuid.uuid4())
        file_path = f"/tmp/{doc_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text (simple version)
        text_content = ""
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # For PDF, we'll need PyPDF2
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
        else:
            text_content = f"Uploaded file: {file.filename}"
        
        # Chunk text (simple version - every 500 chars)
        chunks = [text_content[i:i+500] for i in range(0, len(text_content), 500)]

        # Generate embeddings and store
        points = []
        for i, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()

            # Create unique ID using hash (Qdrant requires UUID or unsigned integer)
            point_id = hash(f"{doc_id}_{i}") & 0x7FFFFFFF  # Ensure positive integer

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "chunk_id": i,
                    "text": chunk,
                    "filename": file.filename,
                    "upload_time": datetime.now().isoformat()
                }
            )
            points.append(point)
        
        # Store in Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        # Cache in Redis
        redis_client.setex(
            f"doc:{doc_id}",
            3600,  # 1 hour TTL
            text_content[:1000]  # Store first 1000 chars
        )
        
        # Clean up temp file
        os.remove(file_path)
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "message": f"Document processed with {len(chunks)} chunks"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/search")
async def search(query: str, top_k: int = 5):
    """Search for relevant documents"""
    try:
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "score": result.score,
                "text": result.payload.get("text", ""),
                "doc_id": result.payload.get("doc_id", ""),
                "filename": result.payload.get("filename", ""),
                "chunk_id": result.payload.get("chunk_id", 0)
            })
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics"""
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)

        return {
            "total_documents": collection_info.vectors_count,
            "collection": COLLECTION_NAME,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "model": EMBEDDING_MODEL
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/consult/recommend")
async def recommend_product(request: ConsultationRequest):
    """
    제품 추천 상담 엔드포인트

    Request:
        - query: 사용자 질문 (e.g., "50미리 용기 추천해줘")
        - customer_id: 고객 ID (optional)
        - context: 추가 컨텍스트 (optional)
        - consultation_type: "product_recommendation"

    Response:
        - consultation_id: 상담 ID
        - query: 원본 질문
        - response: LLM 기반 추천 이유
        - related_products: 추천 제품 목록
        - confidence_score: 신뢰도 스코어
        - source_documents: 참고 문서 목록
    """
    try:
        logger.info(f"Product recommendation request: {request.query}")
        response = await consultation_service.recommend_product(request)
        logger.info(f"Product recommendation response: {response.consultation_id}")
        return response
    except Exception as e:
        logger.error(f"Product recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/consult/defect")
async def handle_defect_inquiry(request: ConsultationRequest):
    """
    불량 문의 상담 엔드포인트

    Request:
        - query: 불량 문의 (e.g., "제품에서 이상한 냄새가 나요")
        - customer_id: 고객 ID (optional)
        - context: 추가 컨텍스트 (optional)
        - consultation_type: "defect_inquiry"

    Response:
        - consultation_id: 상담 ID
        - query: 원본 문의
        - response: LLM 기반 진단 및 조치 안내
        - confidence_score: 신뢰도 스코어
        - source_documents: 참고 문서 목록
    """
    try:
        logger.info(f"Defect inquiry request: {request.query}")
        response = await consultation_service.handle_defect_inquiry(request)
        logger.info(f"Defect inquiry response: {response.consultation_id}")
        return response
    except Exception as e:
        logger.error(f"Defect inquiry error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/qa/ask")
async def ask_question(request: QARequest):
    """
    RAG 기반 Q&A 엔드포인트

    Request:
        - question: 사용자 질문 (e.g., "50ml 용기 추천해줘")
        - collection: 검색할 컬렉션 (default: "products_all")
        - top_k: 검색할 제품 수 (default: 3)
        - customer_id: 고객 ID (optional)

    Response:
        - qa_id: Q&A ID
        - question: 원본 질문
        - answer: LLM 생성 답변
        - related_products: 관련 제품 목록 (product_id, product_name, category, similarity_score)
        - confidence: 신뢰도 점수 (0.0-1.0)
        - timestamp: 응답 생성 시각
    """
    try:
        logger.info(f"RAG Q&A request: {request.question}")
        service = get_rag_qa_service()
        response = await service.answer_question(request)
        logger.info(f"RAG Q&A response: {response.qa_id} (confidence: {response.confidence:.2f})")
        return response
    except Exception as e:
        logger.error(f"RAG Q&A error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)