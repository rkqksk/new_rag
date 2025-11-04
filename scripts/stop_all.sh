#!/bin/bash
# 전체 시스템 종료 스크립트

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🛑 RAG Enterprise 시스템 종료 중..."
echo ""

# PID 파일에서 프로세스 ID 읽기
if [ -f "$PROJECT_DIR/.backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_DIR/.backend.pid")
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "📡 백엔드 종료 중... (PID: $BACKEND_PID)"
        kill "$BACKEND_PID"
    else
        echo "⚠️  백엔드 프로세스가 이미 종료되었습니다."
    fi
    rm "$PROJECT_DIR/.backend.pid"
fi

if [ -f "$PROJECT_DIR/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_DIR/.frontend.pid")
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "🌐 프론트엔드 종료 중... (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID"
    else
        echo "⚠️  프론트엔드 프로세스가 이미 종료되었습니다."
    fi
    rm "$PROJECT_DIR/.frontend.pid"
fi

# 추가로 포트 사용 중인 프로세스 강제 종료
echo ""
echo "🔍 포트 8000, 8001 확인 중..."
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "   포트 8000 정리 완료"
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "   포트 8001 정리 완료"

echo ""
echo "✅ 시스템 종료 완료!"
