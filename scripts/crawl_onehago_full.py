#!/usr/bin/env python3
"""
Onehago.com 전체 크롤링
- 217개 모든 카테고리
- 모든 제품 상세 정보
- 이미지 다운로드
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import aiohttp


class OneHagoFullCrawler:
    """Onehago.com 전체 크롤러"""

    def __init__(
        self,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        output_dir: str = "data/onehago/full_crawl"
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)

        # 진행 상황 저장
        self.progress_file = self.output_dir / "progress.json"
        self.progress = self.load_progress()

        # 통계
        self.stats = {
            'categories_processed': 0,
            'products_found': 0,
            'products_crawled': 0,
            'images_downloaded': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }

    def load_progress(self):
        """진행 상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        return {
            'last_category_index': -1,
            'processed_categories': [],
            'failed_categories': []
        }

    def save_progress(self):
        """진행 상황 저장"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    async def random_delay(self):
        """랜덤 지연"""
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)

    async def download_image(self, img_url: str, product_id: str) -> str:
        """이미지 다운로드"""
        if not img_url:
            return None

        try:
            if not img_url.startswith('http'):
                img_url = f"https://onehago.com{img_url}"

            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
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

    async def crawl_category_page(self, page, category_id: str, category_name: str):
        """카테고리 페이지에서 제품 리스트 수집"""
        url = f"https://onehago.com/mall/?cate={category_id}"

        print(f"\n📦 Category: {category_name} (ID: {category_id})")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            products = await page.query_selector_all(".product")
            print(f"  ✅ Found {len(products)} products")

            product_list = []

            for product in products:
                try:
                    html = await product.inner_html()

                    # 제품 ID
                    product_id = None
                    if "prodWish('" in html:
                        start = html.find("prodWish('") + 10
                        end = html.find("')", start)
                        product_id = html[start:end]

                    if not product_id:
                        continue

                    # Company No
                    company_no = None
                    links = await product.query_selector_all("a[href*='cate_mode=view']")
                    for link in links:
                        href = await link.get_attribute("href")
                        if href and "&no=" in href:
                            no_start = href.find("&no=") + 4
                            no_end = href.find("&", no_start)
                            if no_end == -1:
                                company_no = href[no_start:]
                            else:
                                company_no = href[no_start:no_end]
                            break

                    # 제품명
                    product_name = None
                    text_lines = (await product.text_content()).split('\n')
                    for line in text_lines:
                        if 'item' in line.lower() and ':' in line:
                            product_name = line.split(':', 1)[1].strip()
                            break

                    # MOQ
                    moq = None
                    for line in text_lines:
                        if 'moq' in line.lower() and ':' in line:
                            moq = line.split(':', 1)[1].strip()
                            break

                    # 이미지
                    img_url = None
                    img = await product.query_selector("img")
                    if img:
                        img_url = await img.get_attribute("src")
                        if img_url and not img_url.startswith('http'):
                            img_url = img_url.replace('/thumb/', '/')

                    product_data = {
                        'product_id': product_id,
                        'company_no': company_no,
                        'category_id': category_id,
                        'category_name': category_name,
                        'product_name': product_name,
                        'moq': moq,
                        'image_url': img_url,
                        'detail_url': f"https://onehago.com/mall/?cate_mode=view&pid={product_id}&no={company_no}" if company_no else None
                    }

                    product_list.append(product_data)
                    self.stats['products_found'] += 1

                except Exception as e:
                    print(f"    ⚠️ Failed to parse product: {e}")

            # 카테고리 제품 저장
            if product_list:
                safe_name = category_name.replace('/', '_').replace('\\', '_')
                output_file = self.output_dir / f"category_{category_id}_{safe_name}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(product_list, f, ensure_ascii=False, indent=2)

            self.stats['categories_processed'] += 1
            return product_list

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            self.stats['errors'] += 1
            return []

    async def crawl_product_detail(self, page, product: dict):
        """제품 상세 정보 크롤링"""
        if not product.get('detail_url'):
            return product

        try:
            await page.goto(product['detail_url'], wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # 제품명 (상세)
            try:
                name_elem = await page.query_selector("h2")
                if name_elem:
                    product['detailed_name'] = (await name_elem.text_content()).strip()
            except:
                pass

            # 고화질 이미지
            try:
                img_elem = await page.query_selector("img[src*='productImages']")
                if img_elem:
                    full_img_url = await img_elem.get_attribute("src")
                    if full_img_url:
                        product['full_image_url'] = full_img_url
                        img_path = await self.download_image(full_img_url, product['product_id'])
                        if img_path:
                            product['image_path'] = img_path
            except:
                pass

            # 제품 스펙 (dl/dt/dd)
            try:
                spec_data = {}
                dl_elements = await page.query_selector_all("dl")

                for dl in dl_elements:
                    try:
                        dt_elem = await dl.query_selector("dt")
                        dd_elem = await dl.query_selector("dd")

                        if dt_elem and dd_elem:
                            key = (await dt_elem.text_content()).strip()
                            value = (await dd_elem.text_content()).strip()

                            if key and value and len(key) < 50:
                                spec_data[key] = value
                    except:
                        pass

                if spec_data:
                    product['specifications'] = spec_data

                # 제조사
                try:
                    company_dt = await page.query_selector("dt:has-text('제조사')")
                    if company_dt:
                        company_dd = await company_dt.evaluate_handle("el => el.nextElementSibling")
                        if company_dd:
                            company_text = await company_dd.text_content()
                            product['manufacturer'] = company_text.strip().split('\n')[0].strip()
                except:
                    pass

                # 연락처
                try:
                    phone_dt = await page.query_selector("dt:has-text('PHONE')")
                    if phone_dt:
                        phone_dd = await phone_dt.evaluate_handle("el => el.nextElementSibling")
                        if phone_dd:
                            product['phone'] = (await phone_dd.text_content()).strip()
                except:
                    pass

                try:
                    email_dt = await page.query_selector("dt:has-text('E MAIL'), dt:has-text('EMAIL')")
                    if email_dt:
                        email_dd = await email_dt.evaluate_handle("el => el.nextElementSibling")
                        if email_dd:
                            product['email'] = (await email_dd.text_content()).strip()
                except:
                    pass

            except:
                pass

            product['crawled_at'] = datetime.now().isoformat()
            self.stats['products_crawled'] += 1

        except Exception as e:
            print(f"    ⚠️ Detail failed: {e}")
            self.stats['errors'] += 1

        return product

    async def crawl_all(self, categories: list):
        """전체 크롤링"""
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Connected to Chrome via CDP")
            except Exception as e:
                print(f"❌ CDP connection failed: {e}")
                return

            page = await browser.new_page()

            print("\n" + "="*60)
            print(f"🚀 FULL Onehago.com Crawler")
            print("="*60)
            print(f"Total categories: {len(categories)}")
            print(f"Resume from: Category #{self.progress['last_category_index'] + 1}")
            print("="*60)

            all_products = []
            start_index = self.progress['last_category_index'] + 1

            for idx in range(start_index, len(categories)):
                category = categories[idx]

                print(f"\n[{idx + 1}/{len(categories)}]")

                # 카테고리 크롤링
                products = await self.crawl_category_page(
                    page,
                    category['id'],
                    category['name']
                )

                # 상세 크롤링 (모든 제품)
                if products:
                    print(f"  🔍 Crawling {len(products)} details...")

                    for pidx, product in enumerate(products):
                        if (pidx + 1) % 10 == 0:
                            print(f"    [{pidx + 1}/{len(products)}]")

                        detailed = await self.crawl_product_detail(page, product)
                        products[pidx] = detailed

                        # 제품간 지연
                        if pidx < len(products) - 1:
                            await self.random_delay()

                all_products.extend(products)

                # 진행 상황 저장
                self.progress['last_category_index'] = idx
                self.progress['processed_categories'].append(category['id'])
                self.save_progress()

                # 카테고리간 지연
                if idx < len(categories) - 1:
                    await self.random_delay()

                # 주기적 통계 출력
                if (idx + 1) % 10 == 0:
                    print(f"\n📊 Progress: {idx + 1}/{len(categories)} categories")
                    print(f"   Products: {self.stats['products_found']} found, {self.stats['products_crawled']} detailed")
                    print(f"   Images: {self.stats['images_downloaded']}")
                    print(f"   Errors: {self.stats['errors']}")

            # 전체 저장
            output_file = self.output_dir / "all_products_full.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            # 최종 통계
            print("\n" + "="*60)
            print("✅ FULL CRAWL COMPLETE!")
            print("="*60)
            print(f"Categories: {self.stats['categories_processed']}")
            print(f"Products found: {self.stats['products_found']}")
            print(f"Products detailed: {self.stats['products_crawled']}")
            print(f"Images downloaded: {self.stats['images_downloaded']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"Output: {output_file}")
            print("="*60)

            await page.close()


async def main():
    # 전체 카테고리 로드
    with open("data/onehago/analysis/analysis_result.json") as f:
        data = json.load(f)

    # cate= 파라미터가 있는 카테고리만
    categories = []
    for cat in data['categories']:
        href = cat.get('href', '')
        if 'cate=' in href:
            cate_id = href.split('cate=')[1].split('&')[0]
            categories.append({
                'id': cate_id,
                'name': cat['text'].strip()
            })

    print(f"📋 Loaded {len(categories)} categories")

    crawler = OneHagoFullCrawler(
        delay_min=2.0,
        delay_max=5.0
    )

    await crawler.crawl_all(categories)


if __name__ == "__main__":
    asyncio.run(main())
