#!/usr/bin/env python3
"""
Freemold.net 완전 크롤러 (진행 상황 저장 기능 + 로그인 세션 유지)
- 로그인 세션 유지 확인 (10분마다)
- 모든 카테고리 자동 크롤링
- 제품 리스트 수집
- 제품 상세 정보 추출
- 이미지 다운로드
- 진행 상황 저장 및 이어하기 (Resumable)
- 긴 지연 시간 (5초) for safety
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
import aiohttp


class FreemoldCrawler:
    """Freemold.net 크롤러 (진행 상황 저장 + 세션 유지)"""

    def __init__(
        self,
        delay_min: float = 5.0,
        delay_max: float = 7.0,
        output_dir: str = "data/freemold/crawled"
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)

        # 진행 상황 파일
        self.progress_file = self.output_dir / "crawl_progress.json"
        self.progress = self.load_progress()

        # 로그인 세션 체크
        self.last_login_check = datetime.now()
        self.login_check_interval = timedelta(minutes=10)

        # 통계
        self.stats = {
            'categories_processed': 0,
            'products_found': 0,
            'products_crawled': 0,
            'images_downloaded': 0,
            'errors': 0,
            'login_checks': 0,
            'start_time': datetime.now().isoformat()
        }

    def load_progress(self):
        """진행 상황 로드"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    print(f"📂 Loaded progress: {len(progress.get('completed_products', []))} products already crawled")
                    return progress
            except Exception as e:
                print(f"⚠️ Failed to load progress: {e}")

        return {
            'completed_products': [],
            'completed_categories': [],
            'last_category': None,
            'last_product': None,
            'last_updated': None
        }

    def save_progress(self):
        """진행 상황 저장"""
        self.progress['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save progress: {e}")

    def is_product_crawled(self, product_id: str):
        """제품이 이미 크롤링되었는지 확인"""
        return product_id in self.progress.get('completed_products', [])

    def is_category_completed(self, category_id: str):
        """카테고리가 완료되었는지 확인"""
        return category_id in self.progress.get('completed_categories', [])

    def mark_product_completed(self, product_id: str):
        """제품을 완료로 표시"""
        if product_id not in self.progress['completed_products']:
            self.progress['completed_products'].append(product_id)
            self.progress['last_product'] = product_id
            self.save_progress()

    def mark_category_completed(self, category_id: str):
        """카테고리를 완료로 표시"""
        if category_id not in self.progress['completed_categories']:
            self.progress['completed_categories'].append(category_id)
            self.progress['last_category'] = category_id
            self.save_progress()

    async def random_delay(self):
        """랜덤 지연 (5-7초)"""
        delay = random.uniform(self.delay_min, self.delay_max)
        print(f"  ⏳ Waiting {delay:.1f}s...")
        await asyncio.sleep(delay)

    async def check_login_status(self, page):
        """로그인 상태 확인 (10분마다)"""
        now = datetime.now()
        if now - self.last_login_check < self.login_check_interval:
            return True

        print(f"\n🔐 Checking login status... (last check: {(now - self.last_login_check).seconds // 60} min ago)")

        try:
            current_url = page.url

            if 'login' in current_url.lower() or 'signin' in current_url.lower():
                print("❌ Login session expired! Please re-login manually.")
                input("Press Enter after re-login...")
                self.last_login_check = datetime.now()
                return True

            user_menu = await page.query_selector("a[href*='logout'], .user-menu, .member-info, .my-page")
            if user_menu:
                print("✅ Login session is active")
                self.last_login_check = now
                self.stats['login_checks'] += 1
                return True
            else:
                print("⚠️ Could not verify login status - continuing anyway")
                self.last_login_check = now
                return True

        except Exception as e:
            print(f"⚠️ Login check failed: {e}")
            return True

    async def download_image(self, img_url: str, product_id: str):
        """이미지 다운로드"""
        if not img_url:
            return None

        try:
            if not img_url.startswith('http'):
                img_url = f"https://www.freemold.net{img_url}"

            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        img_data = await response.read()
                        ext = img_url.split('.')[-1].split('?')[0][:4]
                        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            ext = 'jpg'
                        img_path = self.images_dir / f"{product_id}.{ext}"
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        self.stats['images_downloaded'] += 1
                        return str(img_path)
        except Exception as e:
            print(f"  ⚠️ Image download failed: {e}")
        return None

    async def discover_categories(self, page):
        """카테고리 자동 탐색"""
        print("\n🔍 Discovering categories from freemold.net...")
        categories = []

        try:
            await page.goto("https://www.freemold.net", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # 여러 선택자 시도
            selectors = [
                "nav a",
                ".category a",
                ".menu a",
                "#menu a",
                ".gnb a"
            ]

            for selector in selectors:
                links = await page.query_selector_all(selector)
                if len(links) > 0:
                    print(f"  Found {len(links)} links with selector: {selector}")
                    break

            for link in links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    if href and text:
                        text = text.strip()
                        if len(text) > 0 and len(text) < 50:
                            categories.append({
                                'name': text,
                                'url': href if href.startswith('http') else f"https://www.freemold.net{href}",
                                'id': href.split('/')[-1] if '/' in href else text.replace(' ', '_')
                            })
                except:
                    continue

            print(f"✅ Found {len(categories)} categories")
            return categories[:10]  # 처음 10개만 테스트

        except Exception as e:
            print(f"❌ Failed to discover categories: {e}")
            return []

    async def crawl_category_page(self, page, category: dict):
        """카테고리 페이지에서 제품 리스트 수집"""
        category_id = category['id']
        category_name = category['name']

        if self.is_category_completed(category_id):
            print(f"\n✓ Category already completed: {category_name}")
            output_file = self.output_dir / f"category_{category_id}.json"
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []

        print(f"\n📦 Category: {category_name}")
        print(f"  URL: {category['url']}")

        try:
            await page.goto(category['url'], wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            await self.check_login_status(page)

            # 여러 선택자 시도
            selectors = [
                ".product-item",
                ".item",
                ".goods-item",
                ".list-item",
                ".product",
                "article"
            ]

            products_elements = []
            for selector in selectors:
                products_elements = await page.query_selector_all(selector)
                if len(products_elements) > 0:
                    print(f"  ✅ Found {len(products_elements)} products with selector: {selector}")
                    break

            product_list = []

            for idx, product in enumerate(products_elements[:20]):  # 처음 20개만
                try:
                    link_elem = await product.query_selector("a")
                    if not link_elem:
                        continue

                    detail_url = await link_elem.get_attribute("href")
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = f"https://www.freemold.net{detail_url}"

                    product_id = detail_url.split('/')[-1] if detail_url else f"{category_id}_{idx}"

                    product_name = None
                    name_elem = await product.query_selector("h3, h4, .product-name, .title, strong")
                    if name_elem:
                        product_name = await name_elem.text_content()
                        product_name = product_name.strip() if product_name else None

                    img_url = None
                    img = await product.query_selector("img")
                    if img:
                        img_url = await img.get_attribute("src")

                    product_data = {
                        'product_id': product_id,
                        'category_id': category_id,
                        'category_name': category_name,
                        'product_name': product_name,
                        'image_url': img_url,
                        'detail_url': detail_url,
                        'already_crawled': self.is_product_crawled(product_id)
                    }

                    product_list.append(product_data)
                    self.stats['products_found'] += 1

                except Exception as e:
                    print(f"    ⚠️ Failed to parse product {idx + 1}: {e}")

            if product_list:
                output_file = self.output_dir / f"category_{category_id}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(product_list, f, ensure_ascii=False, indent=2)
                print(f"  💾 Saved {len(product_list)} products")

            self.stats['categories_processed'] += 1
            return product_list

        except Exception as e:
            print(f"  ❌ Failed to crawl category: {e}")
            self.stats['errors'] += 1
            return []

    async def crawl_product_detail(self, page, product: dict):
        """제품 상세 페이지 크롤링"""
        product_id = product.get('product_id')

        if product.get('already_crawled') or self.is_product_crawled(product_id):
            print(f"    ✓ Already crawled: {product.get('product_name', 'N/A')}")
            return product

        if not product.get('detail_url'):
            return product

        try:
            await page.goto(product['detail_url'], wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            await self.check_login_status(page)

            # 상세 정보 추출
            try:
                name_elem = await page.query_selector("h1, h2, .product-title, .detail-title")
                if name_elem:
                    detailed_name = await name_elem.text_content()
                    product['detailed_name'] = detailed_name.strip()
            except:
                pass

            try:
                desc_elem = await page.query_selector(".description, .product-desc, .detail-content")
                if desc_elem:
                    description = await desc_elem.text_content()
                    product['description'] = description.strip()[:500]  # 처음 500자만
            except:
                pass

            try:
                img_elem = await page.query_selector(".product-image img, .detail-image img, .main-image")
                if img_elem:
                    full_img_url = await img_elem.get_attribute("src")
                    if full_img_url:
                        product['full_image_url'] = full_img_url
                        img_path = await self.download_image(full_img_url, product['product_id'])
                        if img_path:
                            product['image_path'] = img_path
            except:
                pass

            product['crawled_at'] = datetime.now().isoformat()
            self.stats['products_crawled'] += 1
            self.mark_product_completed(product_id)

        except Exception as e:
            print(f"    ⚠️ Detail crawl failed: {e}")
            self.stats['errors'] += 1

        return product

    async def crawl_all(self, categories=None, crawl_details=True):
        """모든 카테고리 크롤링"""
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Connected to Chrome via CDP (logged in session)")
            except Exception as e:
                print(f"❌ CDP connection failed: {e}")
                return

            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                page = pages[0] if pages else await context.new_page()
            else:
                page = await browser.new_page()

            print("\n" + "="*60)
            print(f"🚀 Freemold.net Crawler (Resumable + Session Maintained)")
            print("="*60)
            print(f"Delay: {self.delay_min}-{self.delay_max}s | Login check: every 10min")
            print(f"Already completed: {len(self.progress.get('completed_products', []))} products")
            print("="*60)

            if not categories:
                categories = await self.discover_categories(page)
                if not categories:
                    print("❌ No categories found!")
                    return

            print(f"Categories to crawl: {len(categories)}")
            all_products = []

            for idx, category in enumerate(categories):
                print(f"\n[{idx + 1}/{len(categories)}]")
                products = await self.crawl_category_page(page, category)

                if crawl_details and products:
                    products_to_crawl = [p for p in products if not p.get('already_crawled', False)]

                    if products_to_crawl:
                        print(f"  🔍 Crawling {len(products_to_crawl)} NEW products...")

                        for pidx, product in enumerate(products_to_crawl):
                            print(f"    [{pidx + 1}/{len(products_to_crawl)}] {product.get('product_name', 'N/A')}")
                            detailed = await self.crawl_product_detail(page, product)
                            for i, p in enumerate(products):
                                if p['product_id'] == detailed['product_id']:
                                    products[i] = detailed
                                    break
                            if pidx < len(products_to_crawl) - 1:
                                await self.random_delay()
                    else:
                        print(f"  ✓ All products already crawled")

                all_products.extend(products)
                self.mark_category_completed(category['id'])

                if idx < len(categories) - 1:
                    await self.random_delay()

            output_file = self.output_dir / "all_products.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print("\n" + "="*60)
            print("✅ Crawling Complete!")
            print("="*60)
            print(f"Categories: {self.stats['categories_processed']}")
            print(f"Products found: {self.stats['products_found']}")
            print(f"Products crawled: {self.stats['products_crawled']}")
            print(f"Images: {self.stats['images_downloaded']}")
            print(f"Login checks: {self.stats['login_checks']}")
            print(f"Errors: {self.stats['errors']}")
            print("="*60)


async def main():
    import sys
    crawler = FreemoldCrawler(delay_min=5.0, delay_max=7.0)
    crawl_details = len(sys.argv) > 1 and sys.argv[1] == '--details'
    await crawler.crawl_all(categories=None, crawl_details=crawl_details)


if __name__ == "__main__":
    asyncio.run(main())
