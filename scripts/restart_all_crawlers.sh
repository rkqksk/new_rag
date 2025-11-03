#!/bin/bash

# 크롤러 자동 재시작 스크립트
# 사용법: bash scripts/restart_all_crawlers.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 크롤러 자동 재시작 스크립트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 현재 디렉토리 확인
cd /Users/oypnus/Project/rag-enterprise

# 1. Freemold Detail Crawler 재시작
echo "📦 [1/2] Freemold Detail Crawler 재시작 중..."
nohup python3 scripts/crawl_freemold_complete_v2.py \
  data/freemold/universal/all_products_merged.json \
  2>&1 | tee /tmp/freemold_detail_restart.log &
FREEMOLD_PID=$!
echo "   ✅ 시작됨 (PID: $FREEMOLD_PID)"
echo "   📝 로그: tail -f /tmp/freemold_detail_restart.log"
echo ""

# 2. Onehago Full Crawler 재시작
echo "🛒 [2/2] Onehago Full Crawler 재시작 중..."
nohup python3 scripts/crawl_onehago_full_clean.py \
  2>&1 | tee /tmp/onehago_full_restart.log &
ONEHAGO_PID=$!
echo "   ✅ 시작됨 (PID: $ONEHAGO_PID)"
echo "   📝 로그: tail -f /tmp/onehago_full_restart.log"
echo ""

# 잠시 대기 후 상태 확인
echo "⏳ 크롤러 초기화 중..."
sleep 5

# 3. 진행 상황 확인
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 현재 진행 상황"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Freemold 진행률
if [ -f data/freemold/crawled_v2/crawl_progress.json ]; then
  FREEMOLD_COMPLETED=$(python3 -c "import json; print(len(json.load(open('data/freemold/crawled_v2/crawl_progress.json'))['completed']))")
  FREEMOLD_TOTAL=21592
  FREEMOLD_PERCENT=$(python3 -c "print(f'{($FREEMOLD_COMPLETED / $FREEMOLD_TOTAL * 100):.1f}')")
  echo "📦 Freemold Detail Crawler:"
  echo "   완료: $FREEMOLD_COMPLETED / $FREEMOLD_TOTAL 제품"
  echo "   진행률: $FREEMOLD_PERCENT%"
  echo ""
fi

# Onehago 진행률
if [ -f data/onehago/full_crawl_clean/progress.json ]; then
  ONEHAGO_COMPLETED=$(python3 -c "import json; print(len(json.load(open('data/onehago/full_crawl_clean/progress.json'))['processed_categories']))")
  ONEHAGO_TOTAL=217
  ONEHAGO_PERCENT=$(python3 -c "print(f'{($ONEHAGO_COMPLETED / $ONEHAGO_TOTAL * 100):.1f}')")
  echo "🛒 Onehago Full Crawler:"
  echo "   완료: $ONEHAGO_COMPLETED / $ONEHAGO_TOTAL 카테고리"
  echo "   진행률: $ONEHAGO_PERCENT%"
  echo ""
fi

# 4. 실행 중인 프로세스 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 실행 중인 크롤러 프로세스"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ps aux | grep -E "crawl_freemold_complete_v2|crawl_onehago_full_clean" | grep -v grep
echo ""

# 5. 모니터링 명령어 안내
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 유용한 명령어"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 로그 실시간 확인:"
echo "   Freemold: tail -f /tmp/freemold_detail_restart.log"
echo "   Onehago:  tail -f /tmp/onehago_full_restart.log"
echo ""
echo "📊 진행 상황 확인:"
echo "   bash scripts/check_crawler_progress.sh"
echo ""
echo "🛑 크롤러 종료:"
echo "   pkill -f crawl_freemold_complete_v2"
echo "   pkill -f crawl_onehago_full_clean"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 모든 크롤러가 재시작되었습니다!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
