#!/usr/bin/env python3
"""
컨텍스트 인식 채팅 서버 실행 스크립트
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.chat import router as chat_router


# FastAPI 앱 생성
app = FastAPI(
    title="RAG Enterprise - 컨텍스트 인식 채팅 API",
    description="대화 컨텍스트를 유지하는 지능형 제품 검색 채팅 시스템",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat 라우터 등록
app.include_router(chat_router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "RAG Enterprise - 컨텍스트 인식 채팅 API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/chat/health",
            "create_session": "/chat/create_session",
            "query": "/chat/query",
            "websocket": "/chat/ws/{session_id}"
        }
    }


if __name__ == "__main__":
    print("🚀 컨텍스트 인식 채팅 서버 시작...")
    print("📝 API 문서: http://localhost:8001/docs")
    print("💬 WebSocket: ws://localhost:8001/chat/ws/{session_id}")
    print()
    print("⚠️  사전 요구사항:")
    print("   1. Redis 서버 실행: redis-server")
    print("   2. 필요한 패키지 설치: pip install -r requirements-chat.txt")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
