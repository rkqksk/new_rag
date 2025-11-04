#!/bin/bash

# 크롤러 진행 상황 확인 스크립트
# 사용법: bash scripts/check_crawler_progress.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 크롤러 진행 상황 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "현재 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Freemold Detail Crawler 진행률
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Freemold Detail Crawler"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f data/freemold/crawled_v2/crawl_progress.json ]; then
  python3 << 'EOF'
import json
from datetime import datetime

# Progress 파일 읽기
with open('data/freemold/crawled_v2/crawl_progress.json', 'r') as f:
    progress = json.load(f)

# 전체 제품 수
total = 21592

# 완료된 제품 수
completed = len(progress['completed'])

# 진행률
percentage = (completed / total) * 100

# 남은 제품 수
remaining = total - completed

# 예상 시간 계산 (평균 4초/제품 가정)
estimated_hours = (remaining * 4) / 3600

# 마지막 업데이트
last_updated = progress.get('last_updated', 'N/A')
if last_updated != 'N/A':
    last_updated = last_updated[:19]  # 초 단위까지만

print(f"✅ 완료: {completed:,} 제품")
print(f"⏳ 남은: {remaining:,} 제품")
print(f"📊 진행률: {percentage:.2f}%")
print(f"⏱️  예상 완료: 약 {estimated_hours:.1f}시간")
print(f"🕒 마지막 업데이트: {last_updated}")

# 진행 바 생성
bar_length = 50
filled = int(bar_length * percentage / 100)
bar = '█' * filled + '░' * (bar_length - filled)
print(f"[{bar}] {percentage:.1f}%")
EOF
else
  echo "❌ Progress 파일을 찾을 수 없습니다."
fi

echo ""

# 2. Onehago Full Crawler 진행률
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛒 Onehago Full Crawler"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f data/onehago/full_crawl_clean/progress.json ]; then
  python3 << 'EOF'
import json
from datetime import datetime

# Progress 파일 읽기
with open('data/onehago/full_crawl_clean/progress.json', 'r') as f:
    progress = json.load(f)

# 전체 카테고리 수
total = 217

# 완료된 카테고리 수
completed = len(progress['processed_categories'])

# 진행률
percentage = (completed / total) * 100

# 남은 카테고리 수
remaining = total - completed

# 예상 시간 계산 (평균 3분/카테고리 가정)
estimated_hours = (remaining * 3) / 60

# 다음 카테고리
next_category = progress.get('last_category_index', 'N/A')

print(f"✅ 완료: {completed} 카테고리")
print(f"⏳ 남은: {remaining} 카테고리")
print(f"📊 진행률: {percentage:.2f}%")
print(f"⏱️  예상 완료: 약 {estimated_hours:.1f}시간")
print(f"🔜 다음 카테고리 인덱스: {next_category}")

# 진행 바 생성
bar_length = 50
filled = int(bar_length * percentage / 100)
bar = '█' * filled + '░' * (bar_length - filled)
print(f"[{bar}] {percentage:.1f}%")
EOF
else
  echo "❌ Progress 파일을 찾을 수 없습니다."
fi

echo ""

# 3. 실행 중인 프로세스 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 실행 중인 크롤러 프로세스"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FREEMOLD_RUNNING=$(ps aux | grep -E "crawl_freemold_complete_v2" | grep -v grep | wc -l)
ONEHAGO_RUNNING=$(ps aux | grep -E "crawl_onehago_full_clean" | grep -v grep | wc -l)

if [ $FREEMOLD_RUNNING -gt 0 ]; then
  echo "✅ Freemold: $FREEMOLD_RUNNING 프로세스 실행 중"
  ps aux | grep -E "crawl_freemold_complete_v2" | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%"}'
else
  echo "❌ Freemold: 실행 중이 아님"
fi

echo ""

if [ $ONEHAGO_RUNNING -gt 0 ]; then
  echo "✅ Onehago: $ONEHAGO_RUNNING 프로세스 실행 중"
  ps aux | grep -E "crawl_onehago_full_clean" | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%"}'
else
  echo "❌ Onehago: 실행 중이 아님"
fi

echo ""

# 4. 수집된 데이터 통계
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 수집된 데이터 통계"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Freemold 데이터
if [ -d data/freemold/crawled_v2 ]; then
  FREEMOLD_JSON_COUNT=$(find data/freemold/crawled_v2 -name "*.json" -not -name "crawl_progress.json" | wc -l)
  FREEMOLD_IMAGE_COUNT=$(find data/freemold/crawled_v2/images -type f 2>/dev/null | wc -l)
  echo "📦 Freemold:"
  echo "   JSON 파일: $FREEMOLD_JSON_COUNT 개"
  echo "   이미지: $FREEMOLD_IMAGE_COUNT 개"
fi

echo ""

# Onehago 데이터
if [ -d data/onehago/full_crawl_clean ]; then
  ONEHAGO_JSON_COUNT=$(find data/onehago/full_crawl_clean/products -name "*.json" 2>/dev/null | wc -l)
  ONEHAGO_IMAGE_COUNT=$(find data/onehago/full_crawl_clean/images -type f 2>/dev/null | wc -l)
  echo "🛒 Onehago:"
  echo "   JSON 파일: $ONEHAGO_JSON_COUNT 개"
  echo "   이미지: $ONEHAGO_IMAGE_COUNT 개"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
