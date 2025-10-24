#!/bin/bash
# 문서 자동 정리 시스템 설치

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================="
echo "📦 문서 자동 정리 시스템 설치"
echo "=================================="
echo ""

# 1. 실행 권한 부여
echo "1️⃣  실행 권한 설정..."
chmod +x scripts/maintenance/*.sh
chmod +x scripts/maintenance/*.py
echo "✓ 완료"
echo ""

# 2. 디렉토리 구조 생성
echo "2️⃣  디렉토리 구조 생성..."
python3 scripts/maintenance/auto_organize_docs.py --create-dirs --execute
echo "✓ 완료"
echo ""

# 3. Git hook 설치 (선택사항)
echo "3️⃣  Git pre-commit hook 설치"
echo "   커밋 시 자동으로 문서를 정리합니다."
echo ""
read -p "   설치하시겠습니까? (y/N): " install_hook

if [ "$install_hook" = "y" ] || [ "$install_hook" = "Y" ]; then
    cp scripts/maintenance/git-pre-commit-hook.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✓ Git hook 설치 완료"
else
    echo "⊘ Git hook 설치 건너뜀"
fi
echo ""

# 4. cron 설정 안내 (선택사항)
echo "4️⃣  주기적 실행 설정 (선택사항)"
echo "   매주 일요일 자동으로 문서를 정리하려면:"
echo ""
echo "   crontab -e 실행 후 다음 줄 추가:"
echo "   0 9 * * 0 cd $PROJECT_ROOT && ./scripts/maintenance/weekly_organize.sh"
echo ""

echo "=================================="
echo "✅ 설치 완료!"
echo "=================================="
echo ""
echo "사용법:"
echo "  • 수동 실행: python3 scripts/maintenance/auto_organize_docs.py"
echo "  • 실제 적용: python3 scripts/maintenance/auto_organize_docs.py --execute"
echo "  • 주간 정리: ./scripts/maintenance/weekly_organize.sh"
echo ""
