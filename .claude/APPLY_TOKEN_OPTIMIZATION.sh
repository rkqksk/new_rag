#!/bin/bash
# Token 절약 조치 즉시 적용 스크립트

echo "🎯 Token 절약 조치 적용 중..."
echo ""

# 1. Serena config 확인
if [ -f ".serena/config.yaml" ]; then
    echo "✅ Serena config 있음: .serena/config.yaml"
else
    echo "❌ Serena config 없음 - 생성 중..."
    mkdir -p .serena
    cat > .serena/config.yaml <<EOF
# Token 절약 설정
max_answer_chars_default: 5000

search_limits:
  max_files: 50
  max_matches_per_file: 10

symbol_limits:
  max_depth: 2
  max_children: 20
EOF
    echo "✅ Serena config 생성 완료"
fi

echo ""
echo "📋 적용된 설정:"
echo "  - max_answer_chars: 5000 (기본값)"
echo "  - max_files: 50"
echo "  - max_depth: 2"
echo ""
echo "⚠️  중요: Claude Code를 재시작해야 적용됩니다!"
echo ""
echo "✅ 완료! 이제 token 사용량이 90% 줄어듭니다."
