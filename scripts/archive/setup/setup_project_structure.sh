#!/bin/bash
# RAG Enterprise 프로젝트 구조 초기화 스크립트

set -e  # 에러 발생 시 중단

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 RAG Enterprise 프로젝트 구조 초기화 시작..."

# ============================================
# 1. 새 디렉토리 생성
# ============================================
echo "📁 디렉토리 구조 생성 중..."

# Development
mkdir -p dev/{experiments,prototypes,notebooks,sandbox}

# Documentation
mkdir -p docs/{architecture,api,guides,archive}
mkdir -p claudedocs

# Archives
mkdir -p archives/{logs,backups,deprecated}

# Tests
mkdir -p tests/{unit,integration,e2e}

# Temporary
mkdir -p temp

# Assets
mkdir -p local_models
mkdir -p images/containers

echo "✅ 디렉토리 구조 생성 완료"

# ============================================
# 2. .gitkeep 파일 추가 (빈 디렉토리 유지)
# ============================================
echo "📝 .gitkeep 파일 추가 중..."

touch dev/experiments/.gitkeep
touch dev/prototypes/.gitkeep
touch dev/sandbox/.gitkeep
touch dev/notebooks/.gitkeep
touch archives/logs/.gitkeep
touch archives/backups/.gitkeep
touch archives/deprecated/.gitkeep
touch temp/.gitkeep
touch tests/unit/.gitkeep
touch tests/integration/.gitkeep
touch tests/e2e/.gitkeep

echo "✅ .gitkeep 파일 추가 완료"

# ============================================
# 3. 기존 파일 정리 (선택적)
# ============================================
echo "🧹 기존 파일 정리 중..."

# 루트의 테스트 파일 이동
if ls test_*.py 1> /dev/null 2>&1; then
    echo "  → 테스트 파일을 tests/unit/로 이동"
    mv test_*.py tests/unit/ 2>/dev/null || true
fi

# 루트의 임시 파일 이동
if ls *.tmp 1> /dev/null 2>&1; then
    echo "  → 임시 파일을 temp/로 이동"
    mv *.tmp temp/ 2>/dev/null || true
fi

# 루트의 백업 파일 이동
if ls *_backup.* 1> /dev/null 2>&1 || ls *.bak 1> /dev/null 2>&1; then
    echo "  → 백업 파일을 archives/backups/로 이동"
    mv *_backup.* archives/backups/ 2>/dev/null || true
    mv *.bak archives/backups/ 2>/dev/null || true
fi

# claude-code 디렉토리 처리
if [ -d "claude-code" ]; then
    echo "  → claude-code 디렉토리를 archives/deprecated/로 이동"
    mv claude-code archives/deprecated/ 2>/dev/null || true
fi

echo "✅ 기존 파일 정리 완료"

# ============================================
# 4. README 파일 생성
# ============================================
echo "📄 README 파일 생성 중..."

cat > dev/README.md << 'EOF'
# Development Directory

개발 관련 파일을 위한 디렉토리입니다.

## 📁 구조

- `experiments/` - 실험적 코드 및 프로토타입
- `prototypes/` - 검증된 프로토타입
- `notebooks/` - Jupyter Notebooks
- `sandbox/` - 테스트용 샌드박스

## 📋 사용 규칙

1. 새 실험은 `experiments/YYYYMMDD_feature_name/` 형식으로 생성
2. 검증된 코드만 `app/` 또는 적절한 위치로 이동
3. 실험 완료 후 결과를 README에 기록
EOF

cat > archives/README.md << 'EOF'
# Archives Directory

더 이상 사용하지 않거나 보관이 필요한 파일을 위한 디렉토리입니다.

## 📁 구조

- `logs/` - 과거 로그 파일
- `backups/` - 백업 파일
- `deprecated/` - 사용 중단된 코드

## 📋 정리 규칙

- 90일 이상 된 로그는 자동으로 이곳으로 이동
- 1년 이상 된 파일은 자동으로 압축
EOF

cat > temp/README.md << 'EOF'
# Temporary Files Directory

임시 파일을 위한 디렉토리입니다.

## ⚠️ 주의사항

- 이 디렉토리의 파일은 자동으로 정리됩니다 (7일 이상 된 파일)
- 중요한 파일은 여기에 두지 마세요
- Git에 커밋되지 않습니다
EOF

echo "✅ README 파일 생성 완료"

# ============================================
# 5. 디렉토리 구조 출력
# ============================================
echo ""
echo "📊 현재 프로젝트 구조:"
echo ""

tree -L 2 -d -I 'node_modules|.git|__pycache__|.venv|venv|data' || \
find . -maxdepth 2 -type d | grep -v ".git" | grep -v "node_modules" | grep -v "__pycache__" | sort

echo ""
echo "✨ 프로젝트 구조 초기화 완료!"
echo ""
echo "📚 상세 규칙은 PROJECT_STRUCTURE_RULES.md 참조"
echo ""
