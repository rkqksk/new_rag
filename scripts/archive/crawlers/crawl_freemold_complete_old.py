#!/usr/bin/env python3
"""
완벽한 Freemold 크롤러 - 상세 정보 + 이미지 다운로드
- IP 차단 우회: 랜덤 지연, User-Agent 로테이션, 프록시 지원
- 완전한 데이터: 제품명, 이미지, 가격, 스펙, 설명
- 배치 처리: 진행상황 추적, 에러 복구, 재시도
"""

import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import hashlib

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ Playwright not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "playwright", "aiohttp"], check=True)
    subprocess.run(["playwright", "install", "chromium"], check=True)
    from playwright.async_api import async_playwright, Page, Browser


class AntiBlockCrawler:
    """IP 차단 방지 크롤러"""

    # User-Agent 로테이션 풀
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(
        self,
        output_dir: str = "data/freemold/complete_crawl",
        image_dir: str = "data/freemold/images",
        delay_min: float = 3.0,
        delay_max: float = 8.0,
        max_retries: int = 3,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.image_dir = Path(image_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_retries = max_retries
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url

        self.progress_file = self.output_dir / "crawl_progress.json"
        self.error_log_file = self.output_dir / "error_log.json"

        self.progress = self._load_progress()
        self.errors = []
        self.stats = {
            "total_products": 0,
            "successful": 0,
            "failed": 0,
            "images_downloaded": 0,
            "start_time": None,
            "end_time": None
        }

    def _load_progress(self) -> Dict[str, Any]:
        """진행상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        return {"completed": [], "failed": []}

    def _save_progress(self):
        """진행상황 저장"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def _save_errors(self):
        """에러 로그 저장"""
        with open(self.error_log_file, 'w') as f:
            json.dump(self.errors, f, indent=2, ensure_ascii=False)

    async def random_delay(self):
        """랜덤 지연 (봇 탐지 회피)"""
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)

    def get_random_user_agent(self) -> str:
        """랜덤 User-Agent"""
        return random.choice(self.USER_AGENTS)

    async def download_image(self, image_url: str, product_id: str) -> Optional[str]:
        """이미지 다운로드"""
        try:
            # URL 정규화
            if not image_url.startswith('http'):
                image_url = f"https://www.freemold.net{image_url}"

            # 파일명 생성 (URL 해시)
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
            ext = Path(image_url).suffix or '.jpg'
            filename = f"{product_id}_{url_hash}{ext}"
            filepath = self.image_dir / filename

            # 이미 다운로드 완료
            if filepath.exists():
                return str(filepath)

            # 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image_url,
                    headers={"User-Agent": self.get_random_user_agent()},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        filepath.write_bytes(content)
                        self.stats["images_downloaded"] += 1
                        return str(filepath)

        except Exception as e:
            print(f"      ⚠️ Image download failed: {e}")
            return None

    async def extract_product_details(self, page: Page, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """제품 상세 정보 추출"""

        for attempt in range(self.max_retries):
            try:
                # 랜덤 지연 (첫 시도 제외)
                if attempt > 0:
                    print(f"        🔄 Retry {attempt}/{self.max_retries}...")
                    await self.random_delay()

                # 페이지 로드
                await page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)

                # 에러 페이지 체크
                error_text = await page.eval_on_selector_all(
                    "body",
                    "elements => elements.map(el => el.textContent)"
                )
                if any("error occurred" in text.lower() for text in error_text):
                    print(f"        ❌ Server error detected, waiting longer...")
                    await asyncio.sleep(10)  # 서버 에러 시 10초 대기
                    continue

                # 제품 정보 추출
                product_data = {
                    "product_id": product_id,
                    "product_url": product_url,
                    "crawled_at": datetime.now().isoformat()
                }

                # 1. 제품명
                for selector in ["h1", "h2", ".product-title", ".prd-name"]:
                    try:
                        el = await page.query_selector(selector)
                        if el:
                            name = (await el.text_content()).strip()
                            if name and len(name) > 2:
                                product_data["product_name"] = name
                                break
                    except:
                        pass

                # 2. 이미지
                images = []
                for selector in ["img[src*='product']", "img[src*='Product']", ".product-img img", "img"]:
                    try:
                        elements = await page.query_selector_all(selector)
                        for el in elements:
                            src = await el.get_attribute('src')
                            if src and ('product' in src.lower() or 'upload' in src.lower()):
                                if src not in images:
                                    images.append(src)
                        if images:
                            break
                    except:
                        pass

                product_data["images"] = images[:5]  # 최대 5개

                # 3. 테이블 데이터 (스펙)
                specifications = {}
                tables = await page.query_selector_all("table")
                for table in tables[:3]:
                    try:
                        rows = await table.query_selector_all("tr")
                        for row in rows:
                            cells = await row.query_selector_all("th, td")
                            if len(cells) >= 2:
                                key = (await cells[0].text_content()).strip()
                                value = (await cells[1].text_content()).strip()
                                if key and value and len(key) < 50:
                                    specifications[key] = value
                    except:
                        pass

                product_data["specifications"] = specifications

                # 4. 가격 정보
                price_keywords = ['가격', 'price', '단가', 'moq']
                for keyword in price_keywords:
                    try:
                        el = await page.query_selector(f"text=/{keyword}/i")
                        if el:
                            parent = await el.evaluate("el => el.parentElement")
                            if parent:
                                product_data["price_info"] = parent.get("textContent", "").strip()
                                break
                    except:
                        pass

                # 5. 본문 텍스트 (설명)
                try:
                    body_text = await page.eval_on_selector("body", "el => el.innerText")
                    # 용량, 재질, 넥사이즈 추출
                    import re
                    capacities = re.findall(r'(\d+(?:\.\d+)?)\s*(ml|ML|L|g|cc)', body_text)
                    materials = re.findall(r'\b(PET|PETG|PP|PE|HDPE|LDPE|PVC|ABS|AS|PC)\b', body_text)
                    neck_sizes = re.findall(r'\b(\d+/\d+)\b', body_text)

                    product_data["capacities"] = list(set(capacities[:5]))
                    product_data["materials"] = list(set(materials))
                    product_data["neck_sizes"] = list(set(neck_sizes[:5]))
                except:
                    pass

                # 6. 이미지 다운로드
                downloaded_images = []
                for idx, img_url in enumerate(images[:3], 1):  # 최대 3개만
                    print(f"        📥 Downloading image {idx}/{min(len(images), 3)}...")
                    local_path = await self.download_image(img_url, product_id)
                    if local_path:
                        downloaded_images.append(local_path)
                    await asyncio.sleep(0.5)  # 이미지 다운로드 간 짧은 지연

                product_data["downloaded_images"] = downloaded_images

                # 성공
                if product_data.get("product_name"):
                    return product_data
                else:
                    print(f"        ⚠️ No product name found, retrying...")
                    continue

            except Exception as e:
                print(f"        ❌ Attempt {attempt+1} failed: {e}")
                if attempt == self.max_retries - 1:
                    self.errors.append({
                        "product_id": product_id,
                        "product_url": product_url,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                continue

        return None

    async def crawl_product_list(
        self,
        product_list_file: Path,
        start_index: int = 0,
        max_products: Optional[int] = None
    ):
        """제품 목록 크롤링"""

        # 제품 목록 로드
        with open(product_list_file) as f:
            products = json.load(f)

        total = len(products)
        if max_products:
            products = products[start_index:start_index + max_products]
        else:
            products = products[start_index:]

        self.stats["total_products"] = len(products)
        self.stats["start_time"] = datetime.now().isoformat()

        print(f"\n📦 Total products to crawl: {len(products)} (from index {start_index})")
        print(f"⏱️  Estimated time: {len(products) * self.delay_max / 60:.1f} - {len(products) * self.delay_min / 60:.1f} minutes")
        print(f"🛡️  Anti-block: {self.delay_min}-{self.delay_max}s delay, User-Agent rotation")

        async with async_playwright() as p:
            # 기존 Chrome에 연결 시도
            try:
                print("\n🔗 Connecting to Chrome debugging instance...")
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Connected to existing Chrome")
            except Exception as e:
                print(f"⚠️ Could not connect to remote Chrome: {e}")
                print("🔄 Launching new browser...")
                # 브라우저 설정
                launch_options = {"headless": False}
                if self.use_proxy and self.proxy_url:
                    launch_options["proxy"] = {"server": self.proxy_url}
                browser = await p.chromium.launch(**launch_options)

            # 컨텍스트 생성 (쿠키/로컬스토리지 유지)
            context = await browser.new_context(
                user_agent=self.get_random_user_agent(),
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            detailed_products = []

            for idx, product in enumerate(products, start_index + 1):
                product_id = product.get("pIdx", f"unknown_{idx}")
                product_url = product.get("product_url")

                # 이미 완료된 제품 스킵
                if product_id in self.progress["completed"]:
                    print(f"[{idx}/{total}] ⏭️  Skipping (already done): {product_id}")
                    continue

                print(f"\n[{idx}/{total}] 🔍 Crawling: {product_id}")
                print(f"      URL: {product_url}")

                # User-Agent 주기적 변경 (5개마다)
                if idx % 5 == 0:
                    await context.set_extra_http_headers({
                        "User-Agent": self.get_random_user_agent()
                    })

                # 상세 정보 추출
                details = await self.extract_product_details(page, product_url, product_id)

                if details:
                    # 기존 정보와 병합
                    product_complete = {**product, **details}
                    detailed_products.append(product_complete)

                    self.progress["completed"].append(product_id)
                    self.stats["successful"] += 1

                    print(f"      ✅ Success: {details.get('product_name', 'N/A')}")
                    print(f"      📸 Images: {len(details.get('downloaded_images', []))}")
                else:
                    self.progress["failed"].append(product_id)
                    self.stats["failed"] += 1
                    print(f"      ❌ Failed after {self.max_retries} retries")

                # 진행상황 저장 (10개마다)
                if idx % 10 == 0:
                    self._save_progress()
                    self._save_errors()

                    # 중간 결과 저장
                    category_code = product.get("category_code", "unknown")
                    temp_output = self.output_dir / f"{category_code}_detailed_temp.json"
                    with open(temp_output, 'w', encoding='utf-8') as f:
                        json.dump(detailed_products, f, ensure_ascii=False, indent=2)

                    print(f"\n      💾 Progress saved: {len(self.progress['completed'])} completed, {len(self.progress['failed'])} failed")

                # 랜덤 지연 (봇 탐지 회피)
                await self.random_delay()

            # 최종 저장
            await context.close()
            await browser.close()

            self.stats["end_time"] = datetime.now().isoformat()

            # 최종 결과 저장
            category_code = products[0].get("category_code", "unknown")
            final_output = self.output_dir / f"{category_code}_detailed_complete.json"
            with open(final_output, 'w', encoding='utf-8') as f:
                json.dump(detailed_products, f, ensure_ascii=False, indent=2)

            self._save_progress()
            self._save_errors()

            # 통계 저장
            stats_file = self.output_dir / "crawl_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)

            print("\n" + "="*60)
            print("✅ Crawling Complete!")
            print("="*60)
            print(f"Total: {self.stats['total_products']}")
            print(f"✅ Successful: {self.stats['successful']}")
            print(f"❌ Failed: {self.stats['failed']}")
            print(f"📸 Images downloaded: {self.stats['images_downloaded']}")
            print(f"📁 Output: {final_output}")
            print("="*60)


async def main():
    """메인 실행"""
    import sys

    # 사용법
    if len(sys.argv) < 2:
        print("Usage: python crawl_freemold_complete.py <product_list.json> [start_index] [max_products]")
        print("\nExample:")
        print("  python crawl_freemold_complete.py data/freemold/crawled_products/B001/B001_products.json 0 50")
        print("\n  # Crawl first 50 products from B001")
        sys.exit(1)

    product_list_file = Path(sys.argv[1])
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    max_products = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not product_list_file.exists():
        print(f"❌ File not found: {product_list_file}")
        sys.exit(1)

    # 크롤러 생성
    crawler = AntiBlockCrawler(
        delay_min=3.0,  # 최소 3초 지연
        delay_max=8.0,  # 최대 8초 지연
        max_retries=3,
        use_proxy=False  # 필요시 True로 변경
    )

    # 크롤링 실행
    await crawler.crawl_product_list(product_list_file, start_index, max_products)


if __name__ == "__main__":
    asyncio.run(main())
