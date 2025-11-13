#!/bin/bash
# scripts/code-navigation.sh
# Serena CLI를 사용한 코드 네비게이션 유틸리티

set -e

PROJECT_ROOT="/home/user/new_rag"

echo "🔍 Serena Code Navigation Utility"
echo "=================================="
echo ""

# 1. RAG 관련 모든 함수 찾기
echo "📊 Finding all RAG-related functions..."
serena find-symbol --name "search" --type function --project "$PROJECT_ROOT"
echo ""

# 2. API 엔드포인트 찾기
echo "🌐 Finding all API endpoints..."
serena find-symbol --name "router" --type variable --project "$PROJECT_ROOT"
echo ""

# 3. Socket.IO 이벤트 핸들러 찾기
echo "⚡ Finding all Socket.IO event handlers..."
serena find-references --symbol "sio.event" --project "$PROJECT_ROOT"
echo ""

# 4. PostgreSQL LISTEN/NOTIFY 트리거 찾기
echo "🗄️  Finding all PostgreSQL triggers..."
serena find-references --symbol "pg_notify" --project "$PROJECT_ROOT"
echo ""

# 5. 복잡도 높은 함수 찾기 (리팩토링 대상)
echo "⚠️  Finding complex functions (refactoring candidates)..."
serena analyze-complexity --threshold 15 --project "$PROJECT_ROOT"
echo ""

echo "✅ Code navigation complete!"
