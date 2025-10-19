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

# Import RAG Q&A service
from app.services.rag_qa_service import (
    RAGQAService,
    QARequest,
    QAResponse,
)

# Import ingestion services - lazy loading to avoid startup import errors
# from app.services.document_ingestion_service import DocumentIngestionService
# from app.services.web_crawler_service import WebCrawlerService
from app.api import dashboard_routes, query_routes
# from app.api import ingestion_routes, workflow_routes  # Disabled - document_ingestion not ready

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
# Get allowed origins from environment, default to localhost for development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

# Validate CORS configuration in production
if os.getenv("ENVIRONMENT") == "production" and ALLOWED_ORIGINS == ["http://localhost:3000"]:
    logger.warning("CORS configuration uses development defaults in production. Set ALLOWED_ORIGINS environment variable.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Register ingestion routes later after service initialization

# Environment variables
QDRANT_HOST = os.getenv("QDRANT_HOST", "172.28.0.2")
QDRANT_PORT = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
REDIS_HOST = os.getenv("REDIS_HOST", "172.28.0.3")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "172.28.0.4")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")

# Validate critical credentials are set
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
if not POSTGRES_PASSWORD:
    raise ValueError(
        "POSTGRES_PASSWORD environment variable is required and must not be empty. "
        "Set a strong password in your .env file or production secrets."
    )

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

# Initialize RAG Q&A service (lazy initialization)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://172.28.0.6:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

rag_qa_service = None

def get_rag_qa_service():
    global rag_qa_service
    if rag_qa_service is None:
        rag_qa_service = RAGQAService(
            qdrant_client=qdrant_client,
            embedding_model=model,
            ollama_url=OLLAMA_URL,
            model_name=OLLAMA_MODEL
        )
    return rag_qa_service

# Initialize document ingestion service - lazy loading
# Commented out to avoid import errors on startup
# document_ingestion_service = DocumentIngestionService(
#     qdrant_client=qdrant_client,
#     embedding_model='sentence-transformers/all-MiniLM-L6-v2'
# )
# web_crawler_service = WebCrawlerService(
#     document_ingestion_service=document_ingestion_service
# )

# Inject services into routes - lazy loading
# ingestion_routes.document_ingestion_service = document_ingestion_service
# ingestion_routes.web_crawler_service = web_crawler_service
# dashboard_routes.document_ingestion_service = document_ingestion_service
# dashboard_routes.web_crawler_service = web_crawler_service
dashboard_routes.qdrant_client = qdrant_client
dashboard_routes.redis_client = redis_client

# Register routers
app.include_router(query_routes.router)  # Query routing with Ollama LLMs
# app.include_router(ingestion_routes.router)  # Disabled - document_ingestion not ready
# app.include_router(dashboard_routes.router)  # Disabled - document_ingestion not ready
# app.include_router(workflow_routes.router)  # Disabled - n8n workflows not configured

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
    logger.info(f"Created collection: {COLLECTION_NAME}")
except Exception as e:
    logger.info(f"Collection {COLLECTION_NAME} already exists or creation skipped: {e}")

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

@app.get("/health")
async def health_check():
    """Health check endpoint with configuration validation"""
    health = {
        "api": "healthy",
        "qdrant": False,
        "redis": False,
        "postgres": False,
        "config": {
            "loaded": False,
            "valid": False,
            "source": "CLAUDE.md"
        }
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

    # Check system configuration
    try:
        from pathlib import Path
        import yaml

        config_path = Path("config/system_config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            health["config"]["loaded"] = True
            health["config"]["version"] = config_data.get("version", "unknown")
            health["config"]["last_sync"] = config_data.get("last_sync", "unknown")

            # Basic validation
            required_keys = ['architecture', 'llm', 'docker', 'agents']
            is_valid = all(key in config_data for key in required_keys)
            health["config"]["valid"] = is_valid

            if is_valid:
                logger.info("✓ System configuration is valid")
            else:
                logger.warning("⚠ System configuration is incomplete")

    except Exception as e:
        logger.error(f"✗ Config check failed: {e}")

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