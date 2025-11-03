#!/bin/bash
# 개선된 차단 회피 크롤러 시작 스크립트
# - 랜덤 지연: 3-8초
# - User-Agent 로테이션
# - 로그인 세션 유지 (freemold)
# - 진행 상황 저장/이어하기

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Safe Crawlers with Anti-Blocking"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 기존 프로세스 확인 및 종료
echo "🔍 Checking for existing crawler processes..."
if pgrep -f "crawl.*freemold" > /dev/null; then
    echo "⚠️  Stopping existing freemold crawler..."
    pkill -f "crawl.*freemold"
    sleep 5
fi

if pgrep -f "crawl.*onehago" > /dev/null; then
    echo "⚠️  Stopping existing onehago crawler..."
    pkill -f "crawl.*onehago"
    sleep 5
fi

echo "✅ Ready to start"
echo ""

# Freemold 크롤러 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏭 Starting Freemold Crawler"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Current Progress:"
if [ -f "data/freemold/universal/crawl_progress_universal.json" ]; then
    python3 -c "
import json
try:
    progress = json.load(open('data/freemold/universal/crawl_progress_universal.json'))
    for cat, info in progress.items():
        print(f'  {cat}: Page {info[\"last_page\"]} (Updated: {info[\"updated_at\"][:19]})')
except Exception as e:
    print(f'  Error reading progress: {e}')
"
else
    echo "  No progress file found - starting fresh"
fi
echo ""

# Freemold 크롤러는 로그인 필요
echo "⚠️  IMPORTANT: Freemold requires manual login"
echo ""
echo "Please follow these steps:"
echo "1. A browser window will open"
echo "2. Login to freemold.net manually"
echo "3. Wait for the crawler to continue automatically"
echo ""
read -p "Press Enter to start freemold crawler..."

# Freemold 실행
nohup python3 scripts/crawl_freemold_complete.py > /tmp/freemold_safe_crawl.log 2>&1 &
FREEMOLD_PID=$!
echo "✅ Freemold crawler started (PID: $FREEMOLD_PID)"
echo "📄 Log: /tmp/freemold_safe_crawl.log"
echo "   Monitor: tail -f /tmp/freemold_safe_crawl.log"
echo ""

sleep 3

# Onehago 크롤러 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛒 Starting Onehago Crawler"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Onehago 진행 상황 확인
if [ -f "data/onehago/crawled/all_products.json" ]; then
    product_count=$(python3 -c "
import json
try:
    data = json.load(open('data/onehago/crawled/all_products.json'))
    print(len(data))
except:
    print(0)
" 2>/dev/null)
    echo "📊 Already crawled: $product_count products"
else
    echo "📊 No previous data - starting fresh"
fi
echo ""

# Onehago는 CDP 기반 크롤러 사용 (scripts/crawlers/complete_crawler.py에서 onehago 부분)
# 또는 간단한 requests 기반으로 시작
echo "Starting onehago crawler..."

# 임시로 간단한 onehago 크롤러 스크립트 생성
cat > /tmp/start_onehago_safe.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Onehago 안전 크롤러
- CDP 기반
- 3-8초 랜덤 지연
- User-Agent 로테이션
"""
import asyncio
import json
import random
import time
from pathlib import Path
from playwright.async_api import async_playwright

CATEGORIES = [
    {"id": 2, "name": "PACKAGING"},
    {"id": 4, "name": "CAP"},
    {"id": 5, "name": "PUMP"},
    {"id": 7, "name": "BOTTLE"},
    {"id": 21, "name": "CONTAINER"}
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def random_delay():
    """3-8초 랜덤 지연"""
    delay = random.uniform(3.0, 8.0)
    print(f"  ⏳ Waiting {delay:.1f}s...")
    await asyncio.sleep(delay)

async def main():
    output_dir = Path("data/onehago/crawled")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_products = []

    async with async_playwright() as p:
        # CDP 연결 시도
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ Connected to Chrome via CDP")
        except:
            # CDP 실패시 새 브라우저 시작
            print("⚠️  CDP connection failed, launching new browser...")
            browser = await p.chromium.launch(headless=False)

        context = browser.contexts[0] if browser.contexts else await browser.new_context(
            user_agent=random.choice(USER_AGENTS)
        )
        page = await context.new_page()

        print("\n============================================================")
        print("🚀 Starting Onehago.com Safe Crawler")
        print("============================================================")
        print(f"Categories to crawl: {len(CATEGORIES)}")
        print(f"Delay: 3-8 seconds (random)")
        print("============================================================\n")

        for idx, cat in enumerate(CATEGORIES, 1):
            cat_id = cat["id"]
            cat_name = cat["name"]

            print(f"[{idx}/{len(CATEGORIES)}]\n")
            print(f"📦 Category: {cat_name} (ID: {cat_id})")

            try:
                url = f"https://onehago.com/mall/?cate={cat_id}"
                print(f"  URL: {url}")

                await page.goto(url, wait_until="networkidle", timeout=30000)
                await random_delay()

                # 제품 리스트 수집 (간단한 예시)
                products = await page.query_selector_all(".product-item, .item, article")
                print(f"  ✅ Found {len(products)} products")

                # 진행률 표시를 위한 카운터
                for prod_idx, product in enumerate(products[:10], 1):  # 테스트: 10개만
                    try:
                        title_elem = await product.query_selector("h3, .title, .product-name")
                        title = await title_elem.text_content() if title_elem else "Unknown"

                        print(f"    [{prod_idx}/10] {title[:50]}")

                        all_products.append({
                            "category": cat_name,
                            "category_id": cat_id,
                            "title": title.strip()
                        })

                        await random_delay()
                    except Exception as e:
                        print(f"    ⚠️  Error on product {prod_idx}: {e}")

                # 카테고리 저장
                cat_file = output_dir / f"category_{cat_id}_{cat_name}.json"
                with open(cat_file, 'w', encoding='utf-8') as f:
                    json.dump(all_products[-len(products):], f, ensure_ascii=False, indent=2)
                print(f"  💾 Saved to: {cat_file.name}\n")

            except Exception as e:
                print(f"  ❌ Error on category {cat_name}: {e}\n")

        # 전체 저장
        output_file = output_dir / "all_products.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        print("\n============================================================")
        print("✅ Crawling Complete!")
        print("============================================================")
        print(f"Total products: {len(all_products)}")
        print(f"Output file: {output_file}")
        print("============================================================\n")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
PYTHON_SCRIPT

chmod +x /tmp/start_onehago_safe.py

# Onehago 실행
nohup python3 /tmp/start_onehago_safe.py > /tmp/onehago_safe_crawl.log 2>&1 &
ONEHAGO_PID=$!
echo "✅ Onehago crawler started (PID: $ONEHAGO_PID)"
echo "📄 Log: /tmp/onehago_safe_crawl.log"
echo "   Monitor: tail -f /tmp/onehago_safe_crawl.log"
echo ""

# 요약
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Both Crawlers Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🏭 Freemold:"
echo "   PID: $FREEMOLD_PID"
echo "   Log: tail -f /tmp/freemold_safe_crawl.log"
echo ""
echo "🛒 Onehago:"
echo "   PID: $ONEHAGO_PID"
echo "   Log: tail -f /tmp/onehago_safe_crawl.log"
echo ""
echo "📊 Check Status:"
echo "   ps aux | grep -E '(freemold|onehago)' | grep -v grep"
echo ""
echo "🛑 Stop All:"
echo "   pkill -f 'crawl.*freemold'; pkill -f 'crawl.*onehago'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
