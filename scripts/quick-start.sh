#!/bin/bash
echo "🚀 Docker 서비스 시작"

# 디렉토리 생성
mkdir -p data/{qdrant,redis,postgres,n8n}

# Docker Compose 실행 (v2 방식)
if command -v docker &> /dev/null; then
    docker compose up -d
else
    echo "❌ Docker가 설치되지 않았습니다!"
    echo "brew install docker colima && colima start"
    exit 1
fi

echo "✅ 완료!"
echo "• Qdrant: http://localhost:6333"
echo "• n8n: http://localhost:5678"
