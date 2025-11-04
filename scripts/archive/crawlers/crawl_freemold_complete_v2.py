#!/usr/bin/env python3
"""
Freemold.net 완전 크롤러 - 모든 정보 추출
- 제품명, 규격, 카테고리, 재질, MOQ, 원산지, 제조사, 담당자, 이미지
- 로그인 세션 유지 (10분마다 확인)
- 진행 상황 저장 및 이어하기
- 5-7초 안전 지연
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
import aiohttp
import re


class FreemoldCrawlerComplete:
    """Freemold 완전 크롤러"""

    def __init__(self, delay_min=5.0, delay_max=7.0, output_dir="data/freemold/crawled_v2"):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        
        self.progress_file = self.output_dir / "crawl_progress.json"
        self.progress = self.load_progress()
        
        self.last_login_check = datetime.now()
        self.login_check_interval = timedelta(minutes=10)
        
        self.stats = {
            'products_crawled': 0,
            'images_downloaded': 0,
            'errors': 0,
            'login_checks': 0,
            'start_time': datetime.now().isoformat()
        }

    def load_progress(self):
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    print(f"📂 Progress loaded: {len(progress.get('completed', []))} products done")
                    return progress
            except Exception as e:
                print(f"⚠️ Progress load failed: {e}")
        return {'completed': [], 'last_updated': None}

    def save_progress(self):
        self.progress['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Progress save failed: {e}")

    def is_completed(self, pIdx):
        return pIdx in self.progress.get('completed', [])

    def mark_completed(self, pIdx):
        if pIdx not in self.progress['completed']:
            self.progress['completed'].append(pIdx)
            self.save_progress()

    async def random_delay(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)

    async def check_login(self, page):
        now = datetime.now()
        if now - self.last_login_check < self.login_check_interval:
            return True
        
        print(f"\n🔐 Login check... ({(now - self.last_login_check).seconds // 60}min ago)")
        try:
            if 'login' in page.url.lower():
                print("❌ Session expired! Re-login needed.")
                input("Press Enter after re-login...")
                self.last_login_check = datetime.now()
                return True
            
            user_elem = await page.query_selector("a[href*='logout'], .member-info")
            if user_elem:
                print("✅ Session active")
                self.last_login_check = now
                self.stats['login_checks'] += 1
                return True
            else:
                print("⚠️ Cannot verify - continuing")
                self.last_login_check = now
                return True
        except:
            return True

    async def download_image(self, img_url, pIdx):
        if not img_url:
            return None
        try:
            if not img_url.startswith('http'):
                img_url = f"https://www.freemold.net{img_url}"

            # SSL 인증서 검증 우회 (프리몰드 사이트 인증서 이슈)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        img_data = await resp.read()
                        ext = img_url.split('.')[-1].split('?')[0][:4]
                        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            ext = 'jpg'
                        img_path = self.images_dir / f"{pIdx}.{ext}"
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        self.stats['images_downloaded'] += 1
                        return str(img_path)
        except Exception as e:
            print(f"  ⚠️ Image download failed: {e}")
        return None

    async def extract_product_info(self, page, product):
        """테이블 구조에서 모든 정보 추출"""
        pIdx = product['pIdx']
        
        if self.is_completed(pIdx):
            print(f"  ✓ Already done: pIdx={pIdx}")
            return None
        
        url = product['product_url']
        print(f"  URL: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            await self.check_login(page)
            
            result = {
                'pIdx': pIdx,
                'mIdx': product.get('mIdx'),
                'category_code': product.get('category_code'),
                'category_name': product.get('category_name'),
                'url': url,
                'crawled_at': datetime.now().isoformat()
            }
            
            # 테이블 찾기 (제품 정보가 있는 메인 테이블)
            tables = await page.query_selector_all("table")
            
            for table in tables:
                rows = await table.query_selector_all("tr")
                
                for row in rows:
                    try:
                        # 각 행에서 레이블:값 패턴 찾기
                        cells = await row.query_selector_all("td")
                        if len(cells) >= 2:
                            label_elem = cells[0]
                            value_elem = cells[1]
                            
                            label = await label_elem.text_content()
                            value = await value_elem.text_content()
                            
                            label = label.strip()
                            value = value.strip()
                            
                            # 제품명
                            if '제품명' in label:
                                result['product_name'] = value
                            
                            # 제품규격
                            elif '제품규격' in label or '규격' in label:
                                result['specifications'] = value
                                # 용량 추출
                                capacity_match = re.search(r'용량\s*[:：]\s*([0-9.]+)\s*([㎖mlML]+)', value)
                                if capacity_match:
                                    result['capacity'] = f"{capacity_match.group(1)}{capacity_match.group(2)}"
                                # 사이즈 추출
                                size_match = re.search(r'사이즈\s*[:：]\s*([0-9x*×X.mm\s]+)', value)
                                if size_match:
                                    result['size'] = size_match.group(1).strip()
                            
                            # 재질
                            elif '재질' in label:
                                result['material'] = value
                            
                            # MOQ
                            elif 'MOQ' in label.upper():
                                result['moq'] = value
                            
                            # 원산지
                            elif '원산지' in label:
                                result['origin'] = value
                            
                            # 제조사
                            elif '제조사' in label and '제조사정보' not in label:
                                result['manufacturer'] = value
                            
                            # 제조사정보
                            elif '제조사정보' in label:
                                result['manufacturer_info'] = value
                                # 전화번호 추출
                                phone_match = re.search(r'전화\s*[:：]\s*([\d-]+)', value)
                                if phone_match:
                                    result['manufacturer_phone'] = phone_match.group(1)
                                # 이메일 추출
                                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value)
                                if email_match:
                                    result['manufacturer_email'] = email_match.group(1)
                            
                            # 담당자
                            elif '담당자' in label:
                                result['contact_person'] = value
                                # 담당자 전화
                                contact_phone_match = re.search(r'(01[0-9]-[0-9]{4}-[0-9]{4})', value)
                                if contact_phone_match:
                                    result['contact_phone'] = contact_phone_match.group(1)
                                # 담당자 이메일
                                contact_email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value)
                                if contact_email_match:
                                    result['contact_email'] = contact_email_match.group(1)
                            
                            # 제품코드
                            elif 'JYP' in label or 'YH' in label or 'SR-' in label:
                                result['product_code'] = label.strip()
                        
                        # 해시태그 찾기
                        text = await row.text_content()
                        if '#' in text:
                            hashtags = re.findall(r'#([가-힣a-zA-Z0-9\s]+)', text)
                            if hashtags:
                                result['hashtags'] = [tag.strip() for tag in hashtags]
                    
                    except Exception as e:
                        continue
            
            # 이미지 추출 (메인 + 갤러리 썸네일 → 원본 변환)
            try:
                # 1. 메인 이미지 먼저 확인
                main_img = await page.query_selector("img#imageMain")
                main_img_url = None
                if main_img:
                    main_img_url = await main_img.get_attribute("src")

                # 2. 썸네일 이미지들 (imgThumb) - 같은 제품의 다른 각도
                thumbs = await page.query_selector_all("img.imgThumb")

                image_urls = []
                image_paths = []

                # 메인 이미지 추가
                if main_img_url and '/data/Product/' in main_img_url:
                    image_urls.append(main_img_url)
                    img_path = await self.download_image(main_img_url, f"{pIdx}_0")
                    if img_path:
                        image_paths.append(img_path)

                # 썸네일 이미지들을 원본으로 변환하여 추가
                for thumb in thumbs:
                    thumb_url = await thumb.get_attribute("src")
                    if thumb_url and '/data/Product/' in thumb_url and '/thumb/' in thumb_url:
                        # 썸네일 → 원본 경로 변환
                        original_url = thumb_url.replace('/thumb/', '/')
                        if original_url not in image_urls:
                            image_urls.append(original_url)
                            img_path = await self.download_image(original_url, f"{pIdx}_{len(image_urls)-1}")
                            if img_path:
                                image_paths.append(img_path)

                if image_urls:
                    result['image_urls'] = image_urls  # 복수형
                    result['image_url'] = image_urls[0]  # 메인 이미지 (하위 호환)
                if image_paths:
                    result['image_paths'] = image_paths  # 복수형
                    result['image_path'] = image_paths[0]  # 메인 이미지 (하위 호환)
            except Exception as e:
                print(f"  ⚠️ Image extraction failed: {e}")
            
            self.stats['products_crawled'] += 1
            self.mark_completed(pIdx)
            
            return result
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats['errors'] += 1
            return None

    async def crawl_all(self, product_list_file):
        """제품 리스트 파일로부터 크롤링"""
        # 제품 리스트 로드
        with open(product_list_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print(f"\n🚀 Freemold Complete Crawler")
        print(f"="*60)
        print(f"Total products: {len(products)}")
        print(f"Already completed: {len(self.progress.get('completed', []))}")
        print(f"Remaining: {len(products) - len(self.progress.get('completed', []))}")
        print(f"="*60)
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222", timeout=60000)
                print("✅ Connected to CDP")
            except Exception as e:
                print(f"❌ CDP failed: {e}")
                return
            
            contexts = browser.contexts
            page = None
            if contexts and contexts[0].pages:
                page = contexts[0].pages[0]
            else:
                page = await browser.new_page()
            
            results = []
            
            for idx, product in enumerate(products):
                pIdx = product['pIdx']
                print(f"\n[{idx+1}/{len(products)}] pIdx={pIdx}")
                
                result = await self.extract_product_info(page, product)
                
                if result:
                    results.append(result)
                    print(f"  ✅ Extracted: {result.get('product_name', 'N/A')}")
                
                # 지연
                if idx < len(products) - 1:
                    await self.random_delay()
            
            # 결과 저장
            output_file = self.output_dir / f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n{'='*60}")
            print(f"✅ Crawling Complete!")
            print(f"{'='*60}")
            print(f"Crawled: {self.stats['products_crawled']}")
            print(f"Images: {self.stats['images_downloaded']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"Login checks: {self.stats['login_checks']}")
            print(f"Output: {output_file}")
            print(f"{'='*60}")


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 crawl_freemold_complete_v2.py <product_list_json>")
        print("Example: python3 crawl_freemold_complete_v2.py data/freemold/crawled_products/B001/B001_products.json")
        sys.exit(1)
    
    product_list = sys.argv[1]
    
    # 처음 5개만 테스트 (옵션)
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    crawler = FreemoldCrawlerComplete(delay_min=5.0, delay_max=7.0)
    await crawler.crawl_all(product_list)


if __name__ == "__main__":
    asyncio.run(main())
