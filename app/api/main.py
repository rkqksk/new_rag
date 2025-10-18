"""
RAG Enterprise API Server
Basic implementation for document upload and search
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
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

# Import consultation service
from app.services.consultation_service import (
    ConsultationService,
    ConsultationRequest,
    ConsultationResponse,
)

# Import ingestion services
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.web_crawler_service import WebCrawlerService
from app.api import ingestion_routes, dashboard_routes, query_routes

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register ingestion routes later after service initialization

# Environment variables
QDRANT_HOST = os.getenv("QDRANT_HOST", "172.28.0.2")
QDRANT_PORT = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
REDIS_HOST = os.getenv("REDIS_HOST", "172.28.0.3")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "172.28.0.4")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_enterprise")

logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")
logger.info(f"Connecting to PostgreSQL at {POSTGRES_HOST}")

# Initialize services
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Initialize consultation service
consultation_service = ConsultationService(
    search_client=qdrant_client,
    embedding_model=model,
    llm_client=None  # Will be implemented later with Ollama
)

# Initialize document ingestion service
document_ingestion_service = DocumentIngestionService(
    qdrant_client=qdrant_client,
    embedding_model='sentence-transformers/all-MiniLM-L6-v2'
)

# Initialize web crawler service
web_crawler_service = WebCrawlerService(
    document_ingestion_service=document_ingestion_service
)

# Inject services into ingestion routes
ingestion_routes.document_ingestion_service = document_ingestion_service
ingestion_routes.web_crawler_service = web_crawler_service

# Inject services into dashboard routes
dashboard_routes.document_ingestion_service = document_ingestion_service
dashboard_routes.web_crawler_service = web_crawler_service
dashboard_routes.qdrant_client = qdrant_client
dashboard_routes.redis_client = redis_client

# Register routers
app.include_router(ingestion_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(query_routes.router)

# Mount static files
import os.path as osp
static_dir = osp.join(osp.dirname(__file__), '..', 'static')
if osp.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Collection name
COLLECTION_NAME = "documents"

# Initialize Qdrant collection
try:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Created collection: {COLLECTION_NAME}")
except:
    print(f"Collection {COLLECTION_NAME} already exists")

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = {
        "api": "healthy",
        "qdrant": False,
        "redis": False,
        "postgres": False
    }

    # Check Qdrant
    try:
        collections = qdrant_client.get_collections()
        health["qdrant"] = True
        logger.info("✓ Qdrant is healthy")
    except Exception as e:
        logger.error(f"✗ Qdrant check failed: {e}")

    # Check Redis
    try:
        redis_client.ping()
        health["redis"] = True
        logger.info("✓ Redis is healthy")
    except Exception as e:
        logger.error(f"✗ Redis check failed: {e}")

    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=5432,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.close()
        health["postgres"] = True
        logger.info("✓ PostgreSQL is healthy")
    except Exception as e:
        logger.error(f"✗ PostgreSQL check failed: {e}")

    return health

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
            "embedding_dimension": 384,
            "model": "sentence-transformers/all-MiniLM-L6-v2"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)