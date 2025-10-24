#!/bin/bash
# 주기적 문서 정리 (주 1회 실행 권장)

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================="
echo "📅 주간 문서 정리"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================="
echo ""

# 먼저 dry-run으로 확인
echo "🔍 정리 대상 확인 중..."
python3 scripts/maintenance/auto_organize_docs.py

echo ""
echo "=================================="
echo "위 내용을 실행하시겠습니까? (y/N)"
read -p "> " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    python3 scripts/maintenance/auto_organize_docs.py --execute
    
    echo ""
    echo "Git에 커밋하시겠습니까? (y/N)"
    read -p "> " commit
    
    if [ "$commit" = "y" ] || [ "$commit" = "Y" ]; then
        git add .
        git commit -m "chore: 주간 문서 정리 ($(date '+%Y-%m-%d'))"
        echo "✅ 커밋 완료"
    fi
else
    echo "❌ 취소됨"
fi
