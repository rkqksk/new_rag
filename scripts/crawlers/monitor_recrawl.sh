#!/bin/bash
# 재크롤링 진행 상황 모니터링 스크립트

echo "=========================================="
echo "재크롤링 진행 상황 모니터링"
echo "=========================================="
echo ""

# 로그 파일 경로
LOG_FILE="recrawl_all_products.log"
DATA_DIR="data/crawled_products_updated"

# 로그 파일 확인
if [ -f "$LOG_FILE" ]; then
    echo "📋 최근 로그 (마지막 20줄):"
    echo "------------------------------------------"
    tail -20 "$LOG_FILE"
    echo ""
fi

# 진행 상황 통계
if [ -d "$DATA_DIR" ]; then
    echo "📊 현재 진행 상황:"
    echo "------------------------------------------"

    # JSON 파일 개수
    json_count=$(find "$DATA_DIR" -name "idx_*.json" 2>/dev/null | wc -l)
    echo "JSON 파일: ${json_count}개"

    # 이미지 개수
    img_count=$(find "$DATA_DIR/images" -name "*.jpg" 2>/dev/null | wc -l)
    echo "이미지 파일: ${img_count}개"

    # PDF 개수
    pdf_count=$(find "$DATA_DIR/print_area" -name "*.pdf" 2>/dev/null | wc -l)
    echo "PDF 파일: ${pdf_count}개"

    # 디스크 사용량
    du_size=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
    echo "디스크 사용: ${du_size}"

    echo ""

    # 진행률 계산 (목표: 398개)
    target=398
    progress=$(echo "scale=1; $json_count * 100 / $target" | bc)
    echo "전체 진행률: ${progress}% (${json_count}/${target})"

    echo ""
fi

# 프로세스 확인
echo "🔍 프로세스 상태:"
echo "------------------------------------------"
if pgrep -f "recrawl_all_products.py" > /dev/null; then
    echo "✅ 재크롤링 프로세스 실행 중"
    ps aux | grep "[r]ecrawl_all_products.py"
else
    echo "⚠️  재크롤링 프로세스 없음 (완료 또는 에러)"
fi

echo ""
echo "=========================================="
echo "모니터링 완료"
echo "실시간 로그: tail -f $LOG_FILE"
echo "=========================================="
