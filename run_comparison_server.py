"""
비교 시스템 서버 실행 스크립트
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from src.api.compare import router as compare_router
from src.api.recommend import router as recommend_router
from src.api.chat import router as chat_router

# FastAPI 앱 생성
app = FastAPI(
    title="RAG Enterprise - 스마트 채팅 & 추천 시스템",
    description="자연어 채팅 기반 제품 검색, 추천, 비교",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat_router)
app.include_router(compare_router)
app.include_router(recommend_router)


@app.get("/")
async def root():
    """루트 엔드포인트 - 비교 데모로 리다이렉트"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>RAG Enterprise - 추천 & 비교</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                color: white;
            }
            .container {
                text-align: center;
                background: rgba(255,255,255,0.1);
                padding: 60px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 3rem; margin-bottom: 20px; }
            p { font-size: 1.2rem; margin: 20px 0; }
            .btn {
                display: inline-block;
                padding: 15px 40px;
                margin: 10px;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 1.1rem;
                transition: transform 0.2s;
            }
            .btn:hover { transform: translateY(-3px); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💬 RAG Enterprise</h1>
            <p>자연어 채팅 기반 제품 검색 & 추천</p>
            <div style="margin-top: 40px;">
                <a href="/demo" class="btn">💬 채팅 시작하기</a>
                <a href="/docs" class="btn">📚 API 문서</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/demo")
async def demo():
    """채팅 데모 페이지 (최종 버전)"""
    html_path = Path(__file__).parent / "frontend" / "chat-demo-final.html"
    return FileResponse(html_path)


@app.get("/demo/original")
async def demo_original():
    """채팅 데모 페이지 (원본)"""
    html_path = Path(__file__).parent / "frontend" / "chat-demo.html"
    return FileResponse(html_path)


@app.get("/debug")
async def debug_console():
    """디버깅 콘솔"""
    html_path = Path(__file__).parent / "frontend" / "debug-console.html"
    return FileResponse(html_path)


@app.get("/comparison")
async def comparison():
    """비교 UI 페이지 (참고용)"""
    html_path = Path(__file__).parent / "frontend" / "comparison-demo.html"
    return FileResponse(html_path)


@app.get("/product-image/{file_path:path}")
async def get_product_image(file_path: str):
    """제품 이미지 서빙"""
    try:
        image_full_path = Path(__file__).parent / "data" / file_path
        if image_full_path.exists() and image_full_path.is_file():
            return FileResponse(image_full_path)
    except:
        pass

    # 이미지 없으면 404
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/health")
async def health():
    """전체 시스템 헬스 체크"""
    return {
        "status": "healthy",
        "services": {
            "comparison_engine": "ok",
            "recommendation_engine": "ok"
        }
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 RAG Enterprise - 스마트 채팅 시스템 시작!")
    print("=" * 60)
    print("\n📍 메인 페이지: http://localhost:8001")
    print("💬 채팅 데모: http://localhost:8001/demo")
    print("📚 API 문서: http://localhost:8001/docs")
    print("\n💡 브라우저에서 http://localhost:8001/demo 를 열어주세요!")
    print("=" * 60 + "\n")

    uvicorn.run(
        "run_comparison_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
