#!/usr/bin/env python3
"""
Freemold 무료 프록시 크롤러
- 250개 무료 프록시 로테이션
- 안전한 지연 (5-15초)
- 프록시 실패 시 다음 프록시로 자동 전환
- 진행 상황 저장 및 재개
"""

import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page
import aiohttp


class FreeProxyCrawler:
    """무료 프록시 기반 크롤러"""

    def __init__(
        self,
        delay_min: float = 5.0,
        delay_max: float = 15.0,
        max_retries: int = 5,
        output_dir: str = "data/freemold/free_proxy_crawl"
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_retries = max_retries
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)

        # 프록시 로드
        self.proxies = self.load_proxies()
        self.proxy_index = 0
        self.failed_proxies = set()

        # 통계
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'proxy_failures': 0,
            'start_time': datetime.now().isoformat()
        }

    def load_proxies(self) -> List[str]:
        """작동하는 프록시 리스트 로드"""
        proxy_file = Path("data/freemold/free_proxies.txt")
        if not proxy_file.exists():
            raise FileNotFoundError(f"Proxy file not found: {proxy_file}")

        with open(proxy_file) as f:
            proxies = [line.strip() for line in f if line.strip()]

        print(f"📋 Loaded {len(proxies)} working proxies")
        return proxies

    def get_next_proxy(self) -> Optional[str]:
        """다음 프록시 가져오기 (실패한 프록시 제외)"""
        attempts = 0
        max_attempts = len(self.proxies)

        while attempts < max_attempts:
            proxy = self.proxies[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)

            if proxy not in self.failed_proxies:
                return proxy

            attempts += 1

        return None  # 모든 프록시가 실패한 경우

    def mark_proxy_failed(self, proxy: str):
        """프록시를 실패로 표시"""
        self.failed_proxies.add(proxy)
        self.stats['proxy_failures'] += 1
        print(f"  ⚠️ Proxy marked as failed: {proxy}")
        print(f"  📊 Failed proxies: {len(self.failed_proxies)}/{len(self.proxies)}")

    async def random_delay(self):
        """안전한 랜덤 지연"""
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)

    async def download_image(self, img_url: str, product_code: str) -> Optional[str]:
        """이미지 다운로드"""
        if not img_url or img_url == "N/A":
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        img_data = await response.read()
                        img_path = self.images_dir / f"{product_code}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        return str(img_path)
        except Exception as e:
            print(f"  ⚠️ Image download failed: {e}")

        return None

    async def crawl_product_page(self, page: Page, product: Dict, proxy: str) -> Dict:
        """제품 상세 페이지 크롤링"""
        url = product['product_url']

        try:
            # 페이지 이동
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # 제품 정보 추출
            product_data = {
                **product,
                'proxy_used': proxy,
                'crawled_at': datetime.now().isoformat()
            }

            # 제품명
            try:
                name_elem = await page.query_selector('.product-name, h1, .title')
                if name_elem:
                    product_data['product_name'] = await name_elem.text_content()
            except:
                product_data['product_name'] = 'N/A'

            # 이미지 URL
            try:
                img_elem = await page.query_selector('img.product-image, img.main-image, img[src*="product"]')
                if img_elem:
                    img_url = await img_elem.get_attribute('src')
                    if img_url and not img_url.startswith('http'):
                        img_url = f"https://www.freemold.net{img_url}"
                    product_data['image_url'] = img_url

                    # 이미지 다운로드
                    img_path = await self.download_image(img_url, product.get('pIdx', 'unknown'))
                    product_data['image_path'] = img_path
            except:
                product_data['image_url'] = 'N/A'
                product_data['image_path'] = None

            # 테이블 데이터 추출
            try:
                tables = await page.query_selector_all('table')
                table_data = {}

                for table in tables:
                    rows = await table.query_selector_all('tr')
                    for row in rows:
                        cells = await row.query_selector_all('th, td')
                        if len(cells) >= 2:
                            key_elem = cells[0]
                            value_elem = cells[1]
                            key = await key_elem.text_content()
                            value = await value_elem.text_content()
                            table_data[key.strip()] = value.strip()

                product_data['specifications'] = table_data
            except:
                product_data['specifications'] = {}

            # 가격 정보
            try:
                price_elem = await page.query_selector('.price, .product-price, [class*="price"]')
                if price_elem:
                    product_data['price'] = await price_elem.text_content()
            except:
                product_data['price'] = 'N/A'

            return product_data

        except Exception as e:
            raise Exception(f"Crawl failed: {str(e)}")

    async def crawl_with_retries(self, browser: Browser, product: Dict) -> Optional[Dict]:
        """재시도 로직으로 크롤링"""
        for attempt in range(self.max_retries):
            proxy = self.get_next_proxy()

            if not proxy:
                print(f"  ❌ No more working proxies available!")
                return None

            try:
                print(f"  🔄 Attempt {attempt + 1}/{self.max_retries} with proxy: {proxy}")

                # 새 컨텍스트와 페이지 생성
                context = await browser.new_context(
                    proxy={"server": proxy},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                # 크롤링
                result = await self.crawl_product_page(page, product, proxy)

                # 성공
                await page.close()
                await context.close()

                print(f"  ✅ Success with proxy: {proxy}")
                return result

            except Exception as e:
                print(f"  ⚠️ Failed with proxy {proxy}: {e}")
                self.mark_proxy_failed(proxy)

                try:
                    await page.close()
                    await context.close()
                except:
                    pass

                # 다음 시도 전 짧은 대기
                await asyncio.sleep(2)

        return None

    async def crawl_product_list(
        self,
        product_list_file: str,
        start_index: int = 0,
        max_products: Optional[int] = None
    ):
        """제품 리스트 크롤링"""
        # 제품 리스트 로드
        with open(product_list_file) as f:
            all_products = json.load(f)

        # 슬라이스
        if max_products:
            products = all_products[start_index:start_index + max_products]
        else:
            products = all_products[start_index:]

        self.stats['total'] = len(products)

        print("=" * 60)
        print("🤖 Freemold Free Proxy Crawler")
        print("=" * 60)
        print(f"\n📦 Total products to crawl: {len(products)} (from index {start_index})")
        print(f"⏱️  Estimated time: {len(products) * 10 / 3600:.1f} hours")
        print(f"🛡️  Anti-block: {self.delay_min}-{self.delay_max}s delay")
        print(f"🔄 Available proxies: {len(self.proxies)}\n")

        # Playwright 시작
        async with async_playwright() as p:
            # Chrome CDP 연결 시도
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Connected to Chrome via CDP")
            except Exception as e:
                print(f"⚠️ CDP connection failed ({e}), launching new browser...")
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )

            # 각 제품 크롤링
            for idx, product in enumerate(products):
                pIdx = product.get('pIdx', 'unknown')
                print(f"\n[{idx + 1}/{len(products)}] Product #{pIdx}")

                # 크롤링
                result = await self.crawl_with_retries(browser, product)

                if result:
                    # 성공
                    self.stats['success'] += 1

                    # 저장
                    output_file = self.output_dir / f"product_{pIdx}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

                    print(f"  💾 Saved to: {output_file}")
                else:
                    # 실패
                    self.stats['failed'] += 1
                    print(f"  ❌ Failed after {self.max_retries} attempts")

                # 통계
                print(f"  📊 Progress: {self.stats['success']} success, {self.stats['failed']} failed")

                # 안전한 지연
                if idx < len(products) - 1:
                    delay = random.uniform(self.delay_min, self.delay_max)
                    print(f"  ⏳ Waiting {delay:.1f}s before next...")
                    await self.random_delay()

            await browser.close()

        # 최종 통계
        self.print_final_stats()

    def print_final_stats(self):
        """최종 통계 출력"""
        print("\n" + "=" * 60)
        print("📊 Final Statistics")
        print("=" * 60)
        print(f"Total products: {self.stats['total']}")
        print(f"✅ Success: {self.stats['success']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"🔄 Proxy failures: {self.stats['proxy_failures']}")
        print(f"📉 Failed proxies: {len(self.failed_proxies)}/{len(self.proxies)}")

        if self.stats['total'] > 0:
            success_rate = self.stats['success'] / self.stats['total'] * 100
            print(f"✨ Success rate: {success_rate:.1f}%")

        print("=" * 60)


async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 crawl_freemold_free_proxy.py <product_list_json> [start_index] [max_products]")
        print("\nExample:")
        print("  python3 crawl_freemold_free_proxy.py data/freemold/crawled_products/B004/B004_products.json 0 10")
        sys.exit(1)

    product_list_file = sys.argv[1]
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    max_products = int(sys.argv[3]) if len(sys.argv) > 3 else None

    crawler = FreeProxyCrawler(
        delay_min=5.0,
        delay_max=15.0,
        max_retries=5
    )

    await crawler.crawl_product_list(product_list_file, start_index, max_products)


if __name__ == "__main__":
    asyncio.run(main())
