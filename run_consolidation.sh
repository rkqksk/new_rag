#!/bin/bash

# Claude 통합 스크립트 실행

echo "🚀 Claude 설정 통합 시작..."
cd /Users/oypnus/Project/rag-enterprise

# Python 스크립트 실행
python3 consolidate_claude.py

# 결과 확인
if [ -d ".claude-consolidated" ]; then
    echo ""
    echo "✅ 통합 완료!"
    echo ""
    echo "📁 통합된 구조:"
    ls -la .claude-consolidated/
    echo ""
    echo "📊 파일 수:"
    find .claude-consolidated -type f | wc -l
else
    echo "❌ 통합 실패"
fi
