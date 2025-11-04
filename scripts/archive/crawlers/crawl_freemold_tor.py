#!/usr/bin/env python3
"""
Freemold 크롤러 - Tor 네트워크 버전
- 무료 IP 로테이션 via Tor
- 10개 제품마다 Tor circuit 재시작 (새로운 IP)
- 긴 지연 시간 (30-120초) for 봇 탐지 회피
"""

import asyncio
import json
import random
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import hashlib

try:
    from playwright.async_api import async_playwright, Page
    import aiofiles
except ImportError:
    print("❌ Installing dependencies...")
    import subprocess as sp
    sp.run(["pip", "install", "playwright", "aiohttp", "aiofiles"], check=True)
    from playwright.async_api import async_playwright, Page
    import aiofiles


class TorCrawler:
    """Tor 네트워크 기반 크롤러"""

    def __init__(
        self,
        output_dir: str = "data/freemold/tor_crawl",
        image_dir: str = "data/freemold/tor_images",
        delay_min: float = 30.0,  # 30초
        delay_max: float = 120.0,  # 2분
        tor_renewal_interval: int = 10,  # 10개마다 IP 변경
        max_retries: int = 5
    ):
        self.output_dir = Path(output_dir)
        self.image_dir = Path(image_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        self.delay_min = delay_min
        self.delay_max = delay_max
        self.tor_renewal_interval = tor_renewal_interval
        self.max_retries = max_retries

        self.tor_proxy = "socks5://localhost:9050"

        self.progress_file = self.output_dir / "crawl_progress.json"
        self.error_log_file = self.output_dir / "error_log.json"
        self.ip_history_file = self.output_dir / "ip_history.json"

        self.progress = self._load_progress()
        self.errors = []
        self.ip_history = []
        self.stats = {
            "total_products": 0,
            "successful": 0,
            "failed": 0,
            "images_downloaded": 0,
            "tor_renewals": 0,
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

    def _save_ip_history(self):
        """IP 히스토리 저장"""
        with open(self.ip_history_file, 'w') as f:
            json.dump(self.ip_history, f, indent=2)

    async def random_delay(self):
        """랜덤 지연 (30-120초)"""
        delay = random.uniform(self.delay_min, self.delay_max)
        print(f"      ⏳ Waiting {delay:.1f}s...")
        await asyncio.sleep(delay)

    async def renew_tor_circuit(self) -> str:
        """Tor circuit 재시작하여 새 IP 획득"""
        print("\n      🔄 Renewing Tor circuit...")

        try:
            # Tor에 HUP 신호 보내기 (circuit 재시작)
            subprocess.run(["killall", "-HUP", "tor"], check=True)
            await asyncio.sleep(5)  # Tor가 새 circuit 생성할 시간

            # 새 IP 확인
            async with aiohttp.ClientSession() as session:
                proxy_url = "socks5://localhost:9050"
                async with session.get(
                    "https://check.torproject.org/api/ip",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        new_ip = data.get("IP", "Unknown")
                        self.ip_history.append({
                            "ip": new_ip,
                            "timestamp": datetime.now().isoformat(),
                            "products_crawled": self.stats["successful"]
                        })
                        self.stats["tor_renewals"] += 1
                        self._save_ip_history()
                        print(f"      ✅ New Tor IP: {new_ip}")
                        return new_ip

        except Exception as e:
            print(f"      ⚠️ Tor renewal failed: {e}")
            await asyncio.sleep(10)

        return "Unknown"

    async def download_image(self, image_url: str, product_id: str) -> Optional[str]:
        """이미지 다운로드 (Tor 경유)"""
        try:
            if not image_url.startswith('http'):
                image_url = f"https://www.freemold.net{image_url}"

            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
            ext = Path(image_url).suffix or '.jpg'
            filename = f"{product_id}_{url_hash}{ext}"
            filepath = self.image_dir / filename

            if filepath.exists():
                return str(filepath)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image_url,
                    proxy=self.tor_proxy,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        filepath.write_bytes(content)
                        self.stats["images_downloaded"] += 1
                        return str(filepath)

        except Exception as e:
            print(f"        ⚠️ Image download failed: {e}")
            return None

    async def extract_product_details(self, page: Page, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """제품 상세 정보 추출"""

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"        🔄 Retry {attempt}/{self.max_retries}...")
                    await asyncio.sleep(15)  # 재시도 시 15초 대기

                await page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                # 에러 체크
                error_text = await page.eval_on_selector_all(
                    "body",
                    "elements => elements.map(el => el.textContent)"
                )
                if any("error occurred" in text.lower() for text in error_text):
                    print(f"        ❌ Server error, retry...")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(30)  # 서버 에러 시 30초 대기
                    continue

                # 제품 정보 추출
                product_data = {
                    "product_id": product_id,
                    "product_url": product_url,
                    "crawled_at": datetime.now().isoformat()
                }

                # 제품명
                for selector in ["h1", "h2", ".product-title", ".prd-name", "title"]:
                    try:
                        el = await page.query_selector(selector)
                        if el:
                            name = (await el.text_content()).strip()
                            if name and len(name) > 2 and "freemold" not in name.lower():
                                product_data["product_name"] = name
                                break
                    except:
                        pass

                # 이미지
                images = []
                for selector in ["img[src*='product']", "img[src*='Product']", "img[src*='upload']", "img"]:
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

                product_data["images"] = images[:5]

                # 테이블 스펙
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
                                if key and value and len(key) < 50 and "error" not in value.lower():
                                    specifications[key] = value
                    except:
                        pass

                product_data["specifications"] = specifications

                # 본문에서 추가 정보 추출
                try:
                    body_text = await page.eval_on_selector("body", "el => el.innerText")
                    import re
                    product_data["capacities"] = list(set(re.findall(r'(\d+(?:\.\d+)?)\s*(ml|ML|L|g|cc)', body_text)[:5]))
                    product_data["materials"] = list(set(re.findall(r'\b(PET|PETG|PP|PE|HDPE|LDPE|PVC|ABS|AS|PC)\b', body_text)))
                    product_data["neck_sizes"] = list(set(re.findall(r'\b(\d+/\d+)\b', body_text)[:5]))
                except:
                    pass

                # 이미지 다운로드 (1개만)
                if images:
                    print(f"        📥 Downloading first image...")
                    local_path = await self.download_image(images[0], product_id)
                    product_data["downloaded_images"] = [local_path] if local_path else []
                else:
                    product_data["downloaded_images"] = []

                if product_data.get("product_name"):
                    return product_data
                else:
                    print(f"        ⚠️ No product name, retrying...")
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

        with open(product_list_file) as f:
            products = json.load(f)

        total = len(products)
        if max_products:
            products = products[start_index:start_index + max_products]
        else:
            products = products[start_index:]

        self.stats["total_products"] = len(products)
        self.stats["start_time"] = datetime.now().isoformat()

        # 예상 시간 계산
        avg_delay = (self.delay_min + self.delay_max) / 2
        estimated_hours = (len(products) * avg_delay) / 3600
        estimated_days = estimated_hours / 24

        print(f"\n📦 Total products to crawl: {len(products)} (from index {start_index})")
        print(f"⏱️  Estimated time: {estimated_hours:.1f} hours ({estimated_days:.1f} days)")
        print(f"🛡️  Anti-block: {self.delay_min}-{self.delay_max}s delay, Tor IP rotation every {self.tor_renewal_interval} products")
        print(f"🔄 Tor renewals needed: ~{len(products) // self.tor_renewal_interval}")

        # 초기 Tor IP 확인
        await self.renew_tor_circuit()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # headless 모드로 변경 (안정성 향상)
                proxy={"server": self.tor_proxy}
            )

            context = await browser.new_context()
            page = await context.new_page()

            detailed_products = []

            for idx, product in enumerate(products, start_index + 1):
                product_id = product.get("pIdx", f"unknown_{idx}")
                product_url = product.get("product_url")

                if product_id in self.progress["completed"]:
                    print(f"\n[{idx}/{total}] ⏭️  Skipping (done): {product_id}")
                    continue

                print(f"\n[{idx}/{total}] 🔍 Crawling: {product_id}")
                print(f"      URL: {product_url}")

                # Tor circuit 재시작 (10개마다)
                if (idx - start_index) % self.tor_renewal_interval == 0 and idx > start_index:
                    await self.renew_tor_circuit()

                # 상세 정보 추출
                details = await self.extract_product_details(page, product_url, product_id)

                if details:
                    product_complete = {**product, **details}
                    detailed_products.append(product_complete)
                    self.progress["completed"].append(product_id)
                    self.stats["successful"] += 1
                    print(f"      ✅ Success: {details.get('product_name', 'N/A')[:50]}")
                else:
                    self.progress["failed"].append(product_id)
                    self.stats["failed"] += 1
                    print(f"      ❌ Failed after {self.max_retries} retries")

                # 진행상황 저장 (5개마다)
                if (idx - start_index) % 5 == 0:
                    self._save_progress()
                    self._save_errors()

                    category_code = product.get("category_code", "unknown")
                    temp_output = self.output_dir / f"{category_code}_detailed_temp.json"
                    with open(temp_output, 'w', encoding='utf-8') as f:
                        json.dump(detailed_products, f, ensure_ascii=False, indent=2)

                    print(f"\n      💾 Progress: {len(self.progress['completed'])} ✅ | {len(self.progress['failed'])} ❌ | {self.stats['tor_renewals']} 🔄")

                # 긴 랜덤 지연
                await self.random_delay()

            await context.close()
            await browser.close()

            self.stats["end_time"] = datetime.now().isoformat()

            # 최종 저장
            category_code = products[0].get("category_code", "unknown")
            final_output = self.output_dir / f"{category_code}_detailed_complete.json"
            with open(final_output, 'w', encoding='utf-8') as f:
                json.dump(detailed_products, f, ensure_ascii=False, indent=2)

            self._save_progress()
            self._save_errors()

            stats_file = self.output_dir / "crawl_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)

            print("\n" + "="*60)
            print("✅ Crawling Complete!")
            print("="*60)
            print(f"Total: {self.stats['total_products']}")
            print(f"✅ Successful: {self.stats['successful']}")
            print(f"❌ Failed: {self.stats['failed']}")
            print(f"📸 Images: {self.stats['images_downloaded']}")
            print(f"🔄 Tor renewals: {self.stats['tor_renewals']}")
            print(f"📁 Output: {final_output}")
            print("="*60)


async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python crawl_freemold_tor.py <product_list.json> [start_index] [max_products]")
        print("\nExample:")
        print("  python crawl_freemold_tor.py data/freemold/crawled_products/B004/B004_products.json 0 10")
        sys.exit(1)

    product_list_file = Path(sys.argv[1])
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    max_products = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not product_list_file.exists():
        print(f"❌ File not found: {product_list_file}")
        sys.exit(1)

    # Tor 실행 확인
    import subprocess
    result = subprocess.run(["lsof", "-i", ":9050"], capture_output=True, text=True)
    if "LISTEN" not in result.stdout:
        print("❌ Tor is not running on port 9050!")
        print("Start Tor with: /opt/homebrew/opt/tor/bin/tor")
        sys.exit(1)

    print("=" * 60)
    print("🤖 Freemold Tor Crawler")
    print("=" * 60)

    crawler = TorCrawler(
        delay_min=30.0,  # 30초
        delay_max=120.0,  # 2분
        tor_renewal_interval=10,  # 10개마다 IP 변경
        max_retries=5
    )

    await crawler.crawl_product_list(product_list_file, start_index, max_products)


if __name__ == "__main__":
    asyncio.run(main())
