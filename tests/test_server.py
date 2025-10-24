"""Simple test server for image search frontend testing"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

app = FastAPI(title="Image Search Test Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Mock image search endpoint
@app.post("/api/v1/search/image")
async def mock_image_search(
    image: UploadFile = File(...),
    query: Optional[str] = Form(None),
    top_k: int = Form(10)
):
    """Mock image search - returns dummy results for testing frontend"""
    return JSONResponse({
        "search_id": "test-123",
        "search_type": "image",
        "query_text": query,
        "image_filename": image.filename,
        "file_size_mb": 0.5,
        "results": [
            {
                "product_id": "idx_100",
                "product_name": "테스트 용기 50ml",
                "category": "Bottle/PET",
                "similarity_score": 0.95,
                "image_url": "/data/crawled_products_final/Bottle/images/idx_100_main_1.jpg",
                "match_type": "hybrid" if query else "visual"
            },
            {
                "product_id": "idx_200",
                "product_name": "샘플 병 100ml",
                "category": "Bottle/PP",
                "similarity_score": 0.87,
                "image_url": "/data/crawled_products_final/Bottle/images/idx_200_main_1.jpg",
                "match_type": "hybrid" if query else "visual"
            }
        ],
        "count": 2,
        "processing_time_ms": 123.45,
        "timestamp": "2025-10-22T14:30:00Z"
    })

# Mock QA endpoint for text search
@app.post("/api/v1/qa/ask")
async def mock_qa_search(request: dict):
    """Mock QA search for testing"""
    return JSONResponse({
        "answer": "테스트 응답입니다.",
        "related_products": [],
        "confidence": 0.8
    })

# Mock product detail endpoint
@app.get("/api/v1/products/{product_id}")
async def mock_product_detail(product_id: str):
    """Mock product detail"""
    return JSONResponse({
        "product_id": product_id,
        "product_name": f"테스트 제품 {product_id}",
        "category": "Bottle/PET",
        "specification": {
            "product_code": "TEST-001",
            "capacity": "50ml",
            "material": "PET",
            "dimension": "50x100mm"
        },
        "image_url": f"/data/crawled_products_final/Bottle/images/{product_id}_main_1.jpg"
    })

if __name__ == "__main__":
    print("🚀 Starting test server on http://localhost:8001")
    print("📁 Access frontend: http://localhost:8001/static/qa_chat.html")
    uvicorn.run(app, host="0.0.0.0", port=8001)
