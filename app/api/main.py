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
import json
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

# Import metrics
from app.core.metrics import get_metrics_collector
from app.core.prometheus_metrics import metrics_endpoint

# Import schemas
from app.models.schemas import QARequest, QAResponse, ConsultationRequest, ConsultationResponse

# Import route handlers
from app.api import dashboard_routes, query_routes, ingestion_routes
from app.api.routes import health as health_routes, image as image_routes, excel as excel_routes, async_qa
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

# Get metrics collector and add middleware (must be added first for proper wrapping)
_metrics = get_metrics_collector()
app.add_middleware(_metrics.get_middleware())

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
app.include_router(async_qa.router)           # Async Q&A endpoints (v2 API)
app.include_router(image_routes.router)       # Image search with drag & drop
app.include_router(excel_routes.router)       # Excel upload & data quality check
app.include_router(ingestion_routes.router)   # Document ingestion & crawling
app.include_router(dashboard_routes.router)   # Dashboard & monitoring
# Note: workflow_routes disabled due to agent module dependencies (will be lazy-loaded if needed)

# Mount static files
import os.path as osp
static_dir = osp.join(osp.dirname(__file__), '..', 'static')
if osp.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount data directory for product images and print areas
# Use absolute path for Docker compatibility
data_dir = osp.abspath(osp.join(osp.dirname(__file__), '..', '..', 'data'))
logger.info(f"Data directory path: {data_dir}")
logger.info(f"Data directory exists: {osp.exists(data_dir)}")
if osp.exists(data_dir):
    app.mount("/data", StaticFiles(directory=data_dir), name="data")
    logger.info(f"✅ Mounted /data → {data_dir}")
else:
    logger.warning(f"⚠️  Data directory not found: {data_dir}")

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

@app.get("/metrics")
def get_prometheus_metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus format for monitoring:
    - HTTP request metrics
    - Q&A performance metrics
    - Vector DB metrics
    - LLM metrics
    - Error rates
    """
    return metrics_endpoint()

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
async def ask_question(
    request: QARequest,
    service = Depends(get_rag_qa_service)
):
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
        response = await service.answer_question(request)
        logger.info(f"RAG Q&A response: {response.qa_id} (confidence: {response.confidence:.2f})")
        return response
    except Exception as e:
        logger.error(f"RAG Q&A error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/{product_id}")
async def get_product_detail(
    product_id: str,
    qdrant_client = Depends(get_qdrant_client)
):
    """
    제품 상세 정보 조회 엔드포인트 (완전한 specification 포함)

    Args:
        product_id: 제품 ID (e.g., "idx_860")

    Response:
        - product_id: 제품 ID
        - product_name: 제품명
        - category: 카테고리
        - specification: 완전한 스펙 정보 {product_code, capacity, material, dimension, type}
        - description: 제품 설명
        - price: 가격 정보
        - moq: 최소 주문 수량
        - image_url: 대표 이미지 URL
        - print_area_url: 인쇄영역 다운로드 링크
        - full_payload: 전체 페이로드 정보
    """
    import re

    try:
        logger.info(f"Product detail request: {product_id}")

        # JSON 파일에서 원본 데이터 로드하기 위한 헬퍼 함수
        def load_product_json(product_id_str):
            """product_id 형식: idx_123 -> JSON 파일 경로에서 로드"""
            match = re.search(r'idx_(\d+)', product_id_str)
            if not match:
                return None

            idx = match.group(1)
            base_path = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final"

            # 가능한 경로들 확인
            possible_paths = [
                f"{base_path}/Bottle/PE/products/idx_{idx}.json",
                f"{base_path}/Bottle/PET/products/idx_{idx}.json",
                f"{base_path}/Bottle/PETG/products/idx_{idx}.json",
                f"{base_path}/Bottle/Other/products/idx_{idx}.json",
                f"{base_path}/Jar/PE/products/idx_{idx}.json",
                f"{base_path}/Jar/PET/products/idx_{idx}.json",
                f"{base_path}/Jar/PP/products/idx_{idx}.json",
                f"{base_path}/Cap/PET/products/idx_{idx}.json",
                f"{base_path}/Cap/PETG/products/idx_{idx}.json",
                f"{base_path}/Cap/PP/products/idx_{idx}.json",
                f"{base_path}/Cap/Other/products/idx_{idx}.json",
                f"{base_path}/Pump/Other/products/idx_{idx}.json",
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        logger.debug(f"Failed to load {path}: {e}")
                        pass

            return None

        # 먼저 JSON 파일에서 직접 로드 (Qdrant 없이도 작동)
        json_data = load_product_json(product_id)
        if not json_data:
            logger.warning(f"Product JSON not found: {product_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )

        # JSON 데이터에서 필요한 정보 추출
        product_name = json_data.get('product_name', 'N/A')
        specs_from_json = json_data.get('specifications', {})
        pricing_info = json_data.get('pricing', {})
        product_list_info = json_data.get('product_list_info', {})

        # 카테고리 결정 (JSON에서 없으면 ID에서 추론)
        category = json_data.get('category_label', '').lower()
        if not category:
            # ID 기반으로 추론
            idx_match = re.search(r'idx_(\d+)', product_id)
            if idx_match:
                idx = int(idx_match.group(1))
                if idx < 400:  # Bottle products
                    category = 'bottle'
                elif idx < 600:  # Jar products
                    category = 'jar'
                elif idx < 800:  # Cap products
                    category = 'cap'
                else:  # Pump products
                    category = 'pump'

        # 용량 추출 (specifications 우선, fallback은 제품명)
        capacity = specs_from_json.get('capacity', '')
        if not capacity:
            capacity_match = re.search(r'(\d+ml)', product_name)
            capacity = capacity_match.group(1) if capacity_match else 'N/A'
        else:
            # "50ml" 형식으로 정규화
            if capacity and '/' in str(capacity):
                capacity = str(capacity).split('/')[0].strip()

        # 제품 타입 추출 (제품명 기반)
        product_type = '일반제품'
        if '헤비' in product_name:
            product_type = '헤비'
        elif '다층' in product_name:
            product_type = '다층'
        elif '파우더' in product_name:
            product_type = '파우더'

        spec = {
            'product_code': specs_from_json.get('제품 코드', 'N/A'),
            'capacity': capacity,
            'material': specs_from_json.get('재질(원료)', 'N/A'),
            'dimension': specs_from_json.get('사양', 'N/A'),
            'type': product_type,
        }

        # 이미지 URL 생성
        idx_match = re.search(r'idx_(\d+)', product_id)
        image_url = None
        if idx_match:
            idx = idx_match.group(1)
            image_url = f"/data/crawled_products_final/{category}/images/idx_{idx}_main_1.jpg"

        # print_area_url 추출
        print_area_url = json_data.get("print_area_url")

        # Primary price 결정: regular_price > selling_price > supply_price 순으로 우선
        primary_price = None
        price_source = None
        discount_price = None

        if pricing_info.get('regular_price'):
            primary_price = pricing_info.get('regular_price')
            price_source = '정상가'
            discount_price = pricing_info.get('discount_price')
        elif pricing_info.get('selling_price'):
            primary_price = pricing_info.get('selling_price')
            price_source = '판매가'
        elif pricing_info.get('supply_price'):
            primary_price = pricing_info.get('supply_price')
            price_source = '공급가'

        # MOQ 정보 추출
        moq = None
        if product_list_info and 'package' in product_list_info:
            moq = product_list_info.get('package')

        # 제품 설명 생성
        description = f"""
제품 스펙:
- 제품 코드: {spec['product_code']}
- 용량: {spec['capacity']}
- 재질(원료): {spec['material']}
- 사양: {spec['dimension']}
- 종류: {spec['type']}
- 카테고리: {category}

가격 정보:
- {price_source or '가격 정보'}: {primary_price or 'N/A'} (원)
- 할인가: {pricing_info.get('discount_price') or 'N/A'} (원)
- MOQ: {moq or 'N/A'}

제품 정보:
- 이 제품은 당사의 제품 데이터베이스에 등록된 제품입니다.
- 더 자세한 정보나 샘플이 필요하시면 상담 팀에 문의해주세요.

인쇄영역 다운로드:
- {print_area_url or 'N/A'}
        """

        return {
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "specification": spec,
            "description": description.strip(),
            "price": {
                "primary_price": primary_price,
                "primary_price_label": price_source,
                "discount_price": pricing_info.get('discount_price'),
                "supply_price": pricing_info.get('supply_price'),
                "selling_price": pricing_info.get('selling_price'),
                "regular_price": pricing_info.get('regular_price'),
            },
            "moq": moq,
            "image_url": image_url,
            "print_area_url": print_area_url,
            "status": "found"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)