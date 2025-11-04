#!/bin/bash
# RAG Enterprise 프로젝트 정리 스크립트

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧹 프로젝트 정리 시작..."

# ============================================
# 1. 임시 파일 정리
# ============================================
echo "📂 임시 파일 정리 중..."

# 7일 이상 된 임시 파일 삭제
if [ -d "temp" ]; then
    OLD_COUNT=$(find temp/ -type f -mtime +7 | wc -l)
    if [ "$OLD_COUNT" -gt 0 ]; then
        echo "  → $OLD_COUNT 개의 오래된 임시 파일 삭제"
        find temp/ -type f -mtime +7 -delete
    else
        echo "  → 삭제할 임시 파일 없음"
    fi
fi

# ============================================
# 2. 로그 아카이브
# ============================================
echo "📋 로그 아카이브 중..."

if [ -d "logs" ]; then
    # 90일 지난 로그 파일 아카이브
    ARCHIVE_DATE=$(date +%Y%m%d)
    ARCHIVE_DIR="archives/logs_$ARCHIVE_DATE"

    OLD_LOGS=$(find logs/ -name "*.log" -type f -mtime +90 2>/dev/null | wc -l)
    if [ "$OLD_LOGS" -gt 0 ]; then
        mkdir -p "$ARCHIVE_DIR"
        echo "  → $OLD_LOGS 개의 오래된 로그를 $ARCHIVE_DIR 로 이동"
        find logs/ -name "*.log" -type f -mtime +90 -exec mv {} "$ARCHIVE_DIR/" \; 2>/dev/null
    else
        echo "  → 아카이브할 로그 없음"
    fi
fi

# ============================================
# 3. 아카이브 압축
# ============================================
echo "🗜️ 오래된 아카이브 압축 중..."

if [ -d "archives" ]; then
    # 1년 지난 파일 압축
    OLD_ARCHIVES=$(find archives/ -type f ! -name "*.gz" -mtime +365 2>/dev/null | wc -l)
    if [ "$OLD_ARCHIVES" -gt 0 ]; then
        echo "  → $OLD_ARCHIVES 개의 파일 압축"
        find archives/ -type f ! -name "*.gz" -mtime +365 -exec gzip {} \; 2>/dev/null
    else
        echo "  → 압축할 파일 없음"
    fi
fi

# ============================================
# 4. Python 캐시 정리
# ============================================
echo "🐍 Python 캐시 정리 중..."

CACHE_COUNT=$(find . -type d -name "__pycache__" | wc -l)
if [ "$CACHE_COUNT" -gt 0 ]; then
    echo "  → $CACHE_COUNT 개의 __pycache__ 디렉토리 삭제"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
fi

PYC_COUNT=$(find . -name "*.pyc" -o -name "*.pyo" | wc -l)
if [ "$PYC_COUNT" -gt 0 ]; then
    echo "  → $PYC_COUNT 개의 .pyc/.pyo 파일 삭제"
    find . -name "*.pyc" -o -name "*.pyo" -delete 2>/dev/null || true
fi

# ============================================
# 5. Docker 볼륨 정리 (선택적)
# ============================================
if [ "$1" = "--docker" ]; then
    echo "🐳 Docker 볼륨 정리 중..."

    # 사용하지 않는 볼륨 제거
    DANGLING_VOLUMES=$(docker volume ls -qf dangling=true | wc -l)
    if [ "$DANGLING_VOLUMES" -gt 0 ]; then
        echo "  → $DANGLING_VOLUMES 개의 dangling 볼륨 삭제"
        docker volume prune -f
    else
        echo "  → 삭제할 볼륨 없음"
    fi
fi

# ============================================
# 6. 디스크 사용량 리포트
# ============================================
echo ""
echo "📊 디스크 사용량 리포트:"
echo ""

du -sh * 2>/dev/null | sort -h | tail -10

echo ""
echo "📁 디렉토리별 파일 개수:"
echo ""

for dir in app mcp_servers agents tests dev docs archives; do
    if [ -d "$dir" ]; then
        COUNT=$(find "$dir" -type f | wc -l)
        echo "  $dir: $COUNT 개"
    fi
done

echo ""
echo "✨ 정리 완료!"
echo ""

# ============================================
# 7. 정리 통계
# ============================================
echo "📈 정리 통계:"
echo "  - 임시 파일: $OLD_COUNT 개 삭제"
echo "  - 로그 파일: $OLD_LOGS 개 아카이브"
echo "  - 아카이브: $OLD_ARCHIVES 개 압축"
echo "  - Python 캐시: $CACHE_COUNT 디렉토리, $PYC_COUNT 파일 삭제"

if [ "$1" = "--docker" ]; then
    echo "  - Docker 볼륨: $DANGLING_VOLUMES 개 삭제"
fi

echo ""
