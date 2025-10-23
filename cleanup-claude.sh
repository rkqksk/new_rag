#!/bin/bash
# Claude 설정 정리 스크립트

echo "🧹 Claude 설정 정리 시작..."
echo ""

# 1. 현재 상태 백업
BACKUP_DIR=".claude.backup.$(date +%Y%m%d_%H%M%S)"
echo "📦 현재 상태 백업 중..."
mkdir -p backups
tar -czf "backups/claude-all-$(date +%Y%m%d_%H%M%S).tar.gz" \
    .claude* .mcp* 2>/dev/null || true
echo "   ✓ 백업 완료: backups/"

# 2. 임시 작업 디렉토리
TEMP_DIR=".claude.temp"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# 3. 기존 .claude 백업하고 새로 시작
if [ -d ".claude" ]; then
    mv .claude $BACKUP_DIR
    echo "   ✓ 기존 .claude → $BACKUP_DIR"
fi

# 4. 깨끗한 .claude 구조 생성
echo ""
echo "🔨 새로운 통합 구조 생성 중..."
mkdir -p .claude/{skills,commands,agents,workflows}

echo "   ✓ .claude/skills/ - 스킬 디렉토리"
echo "   ✓ .claude/commands/ - 명령어 디렉토리"
echo "   ✓ .claude/agents/ - 에이전트 디렉토리"
echo "   ✓ .claude/workflows/ - 워크플로우 디렉토리"

echo ""
echo "✅ 정리 완료!"
echo ""
echo "다음 단계:"
echo "1. python consolidate-claude.py 실행하여 파일 통합"
echo "2. ./apply-claude-config.sh 실행하여 설정 적용"
