#!/bin/bash
# 전체 시스템 시작 스크립트
# 백엔드(8000) + 프론트엔드(8001) 동시 실행

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 RAG Enterprise 시스템 시작"
echo "================================"
echo ""

# 백엔드 실행 (8000 포트)
echo "📡 백엔드 API 시작 중... (포트 8000)"
cd "$PROJECT_DIR"
python3 run_chat_server.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"

# 2초 대기 (백엔드 시작 대기)
sleep 2

# 프론트엔드 실행 (8001 포트)
echo "🌐 프론트엔드 서버 시작 중... (포트 8001)"
cd "$PROJECT_DIR/frontend"
python3 -m http.server 8001 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"

echo ""
echo "✅ 시스템 시작 완료!"
echo "================================"
echo ""
echo "📌 접속 정보:"
echo "   백엔드 API:    http://localhost:8000"
echo "   프론트엔드:     http://localhost:8001/chat-demo-final.html"
echo ""
echo "🛑 종료 방법:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📋 로그 확인:"
echo "   백엔드:  tail -f $PROJECT_DIR/logs/backend.log"
echo "   프론트엔드: tail -f $PROJECT_DIR/logs/frontend.log"
echo ""

# PID 파일 저장
echo "$BACKEND_PID" > "$PROJECT_DIR/.backend.pid"
echo "$FRONTEND_PID" > "$PROJECT_DIR/.frontend.pid"

echo "💡 Tip: ./stop_all.sh 로 전체 종료 가능"
