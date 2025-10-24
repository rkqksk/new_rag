#!/bin/bash
# Git pre-commit hook: 문서 자동 정리

# 프로젝트 루트로 이동
cd "$(git rev-parse --show-toplevel)"

# 루트에 새로운 .md, .py, .txt 파일이 있는지 확인
NEW_ROOT_FILES=$(git diff --cached --name-only --diff-filter=A | grep -E '^[^/]+\.(md|py|txt)$')

if [ -n "$NEW_ROOT_FILES" ]; then
    echo "🔍 루트에 새 파일 감지됨:"
    echo "$NEW_ROOT_FILES"
    echo ""
    echo "📁 문서 자동 정리 실행 중..."
    
    # dry-run으로 먼저 확인
    python3 scripts/maintenance/auto_organize_docs.py
    
    echo ""
    echo "❓ 자동 정리를 적용하시겠습니까?"
    echo "   y: 적용하고 커밋"
    echo "   n: 현재 상태로 커밋"
    echo "   c: 커밋 취소"
    read -p "선택 (y/n/c): " choice
    
    case "$choice" in
        y|Y)
            python3 scripts/maintenance/auto_organize_docs.py --execute
            git add .
            echo "✅ 정리 완료 및 커밋 진행"
            ;;
        n|N)
            echo "⚠️  정리 없이 커밋 진행"
            ;;
        c|C)
            echo "❌ 커밋 취소"
            exit 1
            ;;
        *)
            echo "❌ 잘못된 입력. 커밋 취소"
            exit 1
            ;;
    esac
fi

exit 0
