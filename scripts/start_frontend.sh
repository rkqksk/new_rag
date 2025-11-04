#!/bin/bash
# 프론트엔드 서버 시작 스크립트
# 포트: 8001 (고정)

cd "$(dirname "$0")/frontend"

echo "🚀 프론트엔드 서버 시작 중..."
echo "📍 포트: 8001"
echo "🌐 URL: http://localhost:8001/chat-demo-final.html"
echo ""
echo "Ctrl+C로 종료할 수 있습니다."
echo ""

python3 -m http.server 8001
