#!/bin/bash
# 완전 크롤링 진행 상황 모니터링

clear
echo "========================================================================"
echo "완전 크롤링 진행 상황 모니터링"
echo "========================================================================"
echo ""

# 1. 프로세스 확인
if ps aux | grep -v grep | grep "complete_crawler.py" > /dev/null; then
    echo "✅ 크롤링 프로세스: 실행 중"
else
    echo "❌ 크롤링 프로세스: 중지됨"
fi

echo ""
echo "------------------------------------------------------------------------"

# 2. 진행 상황 파일 확인
if [ -f "complete_crawl_progress.json" ]; then
    echo "📊 진행 상황:"

    last_idx=$(jq -r '.last_idx' complete_crawl_progress.json)
    completed=$(jq -r '.completed_indices | length' complete_crawl_progress.json)
    failed=$(jq -r '.failed_indices | length' complete_crawl_progress.json)
    started=$(jq -r '.started_at' complete_crawl_progress.json)
    updated=$(jq -r '.updated_at' complete_crawl_progress.json)

    echo "  마지막 인덱스: $last_idx"
    echo "  완료: $completed개"
    echo "  실패: $failed개"
    echo "  진행률: $last_idx / 970 ($(echo "scale=1; $last_idx * 100 / 970" | bc)%)"
    echo "  시작 시간: $started"
    echo "  업데이트: $updated"
else
    echo "⚠️  진행 상황 파일 없음"
fi

echo ""
echo "------------------------------------------------------------------------"

# 3. 로그 마지막 10줄
if [ -f "complete_crawl.log" ]; then
    echo "📝 최근 로그 (마지막 10줄):"
    tail -10 complete_crawl.log
else
    echo "⚠️  로그 파일 없음"
fi

echo ""
echo "========================================================================"
echo "명령어:"
echo "  실시간 로그: tail -f complete_crawl.log"
echo "  진행 확인: bash scripts/monitor_complete_crawl.sh"
echo "  크롤링 중지: pkill -f complete_crawler.py"
echo "========================================================================"
