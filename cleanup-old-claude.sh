#!/bin/bash
# Claude 이전 폴더 정리 스크립트

set -e

echo "=============================================="
echo "🧹 Claude 이전 폴더 정리"
echo "=============================================="
echo ""

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 정리할 폴더들
OLD_FOLDERS=(
    ".claude-plugin"
    ".claude-unified"
    ".claude-v3"
    ".claude.backup.20251021_111051"
    ".claude"
)

# 보관할 폴더들
KEEP_FOLDERS=(
    ".claude-clean"
    ".claude-backup-20251023_104124"
)

echo "📋 정리 대상:"
echo ""
for folder in "${OLD_FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        size=$(du -sh "$folder" 2>/dev/null | cut -f1)
        echo -e "  ${RED}✗${NC} $folder ($size)"
    fi
done

echo ""
echo "💾 보관할 폴더:"
echo ""
for folder in "${KEEP_FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        size=$(du -sh "$folder" 2>/dev/null | cut -f1)
        echo -e "  ${GREEN}✓${NC} $folder ($size)"
    fi
done

echo ""
echo -e "${YELLOW}⚠️  경고: 이 작업은 되돌릴 수 없습니다!${NC}"
echo ""
read -p "계속하시겠습니까? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "🗑️  폴더 삭제 중..."

# 안전 백업 생성 (혹시 모르니)
SAFETY_BACKUP="claude-safety-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
echo "📦 안전 백업 생성: $SAFETY_BACKUP"
tar -czf "$SAFETY_BACKUP" "${OLD_FOLDERS[@]}" 2>/dev/null || true

# 폴더 삭제
for folder in "${OLD_FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        echo "  ↳ 삭제: $folder"
        rm -rf "$folder"
    fi
done

echo ""
echo "✅ 정리 완료!"
echo ""
echo "📊 결과:"
echo "  - 삭제된 폴더: ${#OLD_FOLDERS[@]}개"
echo "  - 보관된 폴더: ${#KEEP_FOLDERS[@]}개"
echo "  - 안전 백업: $SAFETY_BACKUP"
echo ""
echo "🚀 다음 단계:"
echo "  1. .claude-clean 내용 확인: ls -la .claude-clean/"
echo "  2. 활성화: bash .claude-clean/activate.sh"
echo "  3. Claude 재시작"
echo ""
