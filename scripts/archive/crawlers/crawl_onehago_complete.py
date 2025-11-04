#!/usr/bin/env python3
"""
Onehago.com 완전 크롤러 (Selenium 버전 - 안정성 개선)
- 모든 카테고리 자동 크롤링
- 제품 리스트 수집
- 제품 상세 정보 추출
- 이미지 다운로드
- 진행 상황 저장 및 이어하기 (Resumable)
"""

import json
import random
import time
import requests
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# User-Agent 로테이션 (차단 회피)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
]


class OneHagoCrawler:
    """Onehago.com 크롤러 (Selenium - 진행 상황 저장)"""

    def __init__(
        self,
        delay_min: float = 3.0,
        delay_max: float = 8.0,
        output_dir: str = "data/onehago/crawled",
        headless: bool = True
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        self.headless = headless

        # 진행 상황 파일
        self.progress_file = self.output_dir / "crawl_progress.json"
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

        self.driver = None

    def load_progress(self) -> dict:
        """진행 상황 로드"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    print(f"📂 Loaded progress: {len(progress.get('completed_products', []))} products already crawled", flush=True)
                    return progress
            except Exception as e:
                print(f"⚠️ Failed to load progress: {e}", flush=True)

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

    def is_product_crawled(self, product_id: str) -> bool:
        """제품이 이미 크롤링되었는지 확인"""
        return product_id in self.progress.get('completed_products', [])

    def is_category_completed(self, category_id: str) -> bool:
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

    def random_delay(self):
        """랜덤 지연"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def setup_driver(self):
        """Selenium WebDriver 설정"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # Random User-Agent (차단 회피)
        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')

        self.driver = webdriver.Chrome(options=chrome_options)
        print(f"✅ Chrome driver initialized (headless={self.headless})", flush=True)
        print(f"🔐 User-Agent: {user_agent[:50]}...", flush=True)

    def download_image(self, img_url: str, product_id: str) -> str:
        """이미지 다운로드 (requests 사용)"""
        if not img_url:
            return None

        try:
            if not img_url.startswith('http'):
                img_url = f"https://onehago.com{img_url}"

            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                # 확장자 추출
                ext = img_url.split('.')[-1].split('?')[0][:4]
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    ext = 'jpg'

                img_path = self.images_dir / f"{product_id}.{ext}"
                with open(img_path, 'wb') as f:
                    f.write(response.content)

                self.stats['images_downloaded'] += 1
                return str(img_path)
        except Exception as e:
            print(f"  ⚠️ Image download failed: {e}")

        return None

    def get_total_pages(self, category_id: str) -> int:
        """카테고리의 총 페이지 수 확인"""
        try:
            url = f"https://onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE=1"
            self.driver.get(url)
            time.sleep(2)

            # 페이지네이션에서 마지막 페이지 번호 찾기
            try:
                # "맨끝" 버튼의 링크에서 페이지 수 추출
                last_page_link = self.driver.find_element(By.XPATH, "//a[contains(@href, 'CURRENT_PAGE=') and contains(text(), '맨끝')]")
                href = last_page_link.get_attribute("href")
                page_num = href.split("CURRENT_PAGE=")[1].split("&")[0]
                return int(page_num)
            except:
                # 맨끝 버튼이 없으면 페이지 번호 링크들에서 최대값 찾기
                page_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'CURRENT_PAGE=')]")
                max_page = 1
                for link in page_links:
                    href = link.get_attribute("href")
                    if "CURRENT_PAGE=" in href:
                        page_num = href.split("CURRENT_PAGE=")[1].split("&")[0]
                        try:
                            max_page = max(max_page, int(page_num))
                        except:
                            pass
                return max_page
        except Exception as e:
            print(f"  ⚠️ Failed to get total pages: {e}, defaulting to 1")
            return 1

    def crawl_category_page(self, category_id: str, category_name: str):
        """카테고리의 모든 페이지에서 제품 리스트 수집"""
        # 이미 완료된 카테고리는 건너뛰기
        if self.is_category_completed(category_id):
            print(f"\n✓ Category already completed: {category_name} (ID: {category_id})", flush=True)
            # 기존 데이터 로드
            output_file = self.output_dir / f"category_{category_id}_{category_name.replace('/', '_')}.json"
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []

        print(f"\n📦 Category: {category_name} (ID: {category_id})", flush=True)

        # 총 페이지 수 확인
        total_pages = self.get_total_pages(category_id)
        print(f"  📄 Total pages: {total_pages}", flush=True)

        all_products = []

        # 모든 페이지 크롤링
        for page_num in range(1, total_pages + 1):
            url = f"https://onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"
            print(f"  📄 Page {page_num}/{total_pages}: {url}", flush=True)

            try:
                self.driver.get(url)
                time.sleep(2)

                # 제품 카드 수집
                products = self.driver.find_elements(By.CSS_SELECTOR, ".product")
                print(f"    ✅ Found {len(products)} products on this page", flush=True)

                for idx, product in enumerate(products):
                    try:
                        html = product.get_attribute('innerHTML')

                        # 제품 ID 추출
                        product_id = None
                        if "prodWish('" in html:
                            start = html.find("prodWish('") + 10
                            end = html.find("')", start)
                            product_id = html[start:end]

                        if not product_id:
                            continue

                        # 링크에서 company_no 추출
                        company_no = None
                        links = product.find_elements(By.CSS_SELECTOR, "a[href*='cate_mode=view']")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and "&no=" in href:
                                no_start = href.find("&no=") + 4
                                no_end = href.find("&", no_start)
                                if no_end == -1:
                                    company_no = href[no_start:]
                                else:
                                    company_no = href[no_start:no_end]
                                break

                        # 제품명 추출 - 다중 방법 시도
                        # 주의: 목록페이지에는 실제 제품명이 없는 경우가 많음
                        product_name = None
                        text_lines = product.text.split('\n')  # 먼저 정의

                        # 방법 1: 이미지의 alt 또는 title 속성 (제품명이 종종 여기에 있음)
                        try:
                            img = product.find_element(By.TAG_NAME, "img")
                            img_alt = img.get_attribute("alt") or ""
                            img_title = img.get_attribute("title") or ""

                            # alt가 있고 "새창열기"가 아니면 사용
                            if img_alt and "새창열기" not in img_alt and len(img_alt) > 3:
                                product_name = img_alt.strip()
                            elif img_title and "새창열기" not in img_title and len(img_title) > 3:
                                product_name = img_title.strip()
                        except:
                            pass

                        # 방법 2: data-* 속성에서 제품명 찾기
                        if not product_name:
                            try:
                                # data-name, data-title, data-product 등 확인
                                for attr in ['data-name', 'data-title', 'data-product']:
                                    try:
                                        elem = product.find_element(By.XPATH, f".//*[@{attr}]")
                                        value = elem.get_attribute(attr)
                                        if value and len(value) > 3:
                                            product_name = value
                                            break
                                    except:
                                        pass
                            except:
                                pass

                        # 방법 3: 목록페이지 텍스트에서 추출 (마지막 수단)
                        if not product_name:
                            for line in text_lines:
                                if line and len(line) > 3 and len(line) < 200:
                                    # "새창열기"는 제외, MOQ/Item 라벨도 제외
                                    lower_line = line.lower()
                                    if (line.strip() != '새창열기' and
                                        ':' not in line and
                                        'moq' not in lower_line and
                                        'item' not in lower_line and
                                        '바로가기' not in lower_line):
                                        product_name = line.strip()
                                        break

                        # 방법 4: 이미지 파일명에서 제품명 추출 (마지막 폴백)
                        if not product_name:
                            try:
                                img = product.find_element(By.TAG_NAME, "img")
                                src = img.get_attribute("src") or ""
                                # URL 또는 파일명에서 의미있는 부분 추출
                                if src:
                                    # 예: /productImages/2025-02/thumb/1739726538_1.jpg → 1739726538
                                    filename = src.split('/')[-1].split('.')[0]
                                    if filename and filename != "default":
                                        product_name = f"제품ID_{filename}"
                            except:
                                pass

                        # MOQ
                        moq = None
                        for line in text_lines:
                            if 'moq' in line.lower() and ':' in line:
                                moq = line.split(':', 1)[1].strip()
                                break

                        # 이미지 URL (썸네일)
                        img_url = None
                        try:
                            img = product.find_element(By.CSS_SELECTOR, "img")
                            img_url = img.get_attribute("src")
                            if img_url and not img_url.startswith('http'):
                                # 썸네일을 고화질로 변환
                                img_url = img_url.replace('/thumb/', '/')
                        except:
                            pass

                        product_data = {
                            'product_id': product_id,
                            'company_no': company_no,
                            'category_id': category_id,
                            'category_name': category_name,
                            'product_name': product_name,
                            'moq': moq,
                            'image_url': img_url,
                            'detail_url': f"https://onehago.com/mall/?cate_mode=view&pid={product_id}&no={company_no}" if company_no else None,
                            'already_crawled': self.is_product_crawled(product_id)
                        }

                        all_products.append(product_data)
                        self.stats['products_found'] += 1

                    except Exception as e:
                        print(f"      ⚠️ Failed to parse product {idx + 1}: {e}", flush=True)

                # 페이지 간 지연
                if page_num < total_pages:
                    time.sleep(random.uniform(self.delay_min, self.delay_max))

            except Exception as e:
                print(f"    ❌ Failed to crawl page {page_num}: {e}", flush=True)
                self.stats['errors'] += 1

        # 카테고리 전체 제품 리스트 저장
        if all_products:
            output_file = self.output_dir / f"category_{category_id}_{category_name.replace('/', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)
            print(f"  💾 Saved {len(all_products)} total products to: {output_file.name}", flush=True)

        self.stats['categories_processed'] += 1
        return all_products

    def crawl_product_detail(self, product: dict):
        """제품 상세 페이지 크롤링"""
        product_id = product.get('product_id')

        # 이미 크롤링된 제품은 건너뛰기
        if product.get('already_crawled') or self.is_product_crawled(product_id):
            print(f"    ✓ Already crawled: {product.get('product_name', 'N/A')}")
            return product

        if not product.get('detail_url'):
            return product

        try:
            self.driver.get(product['detail_url'])
            time.sleep(2)

            # 제품명 (상세)
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h2")
                if name_elem:
                    product['detailed_name'] = name_elem.text.strip()
            except:
                pass

            # 고화질 이미지
            try:
                img_elem = self.driver.find_element(By.CSS_SELECTOR, "img[src*='productImages']")
                if img_elem:
                    full_img_url = img_elem.get_attribute("src")
                    if full_img_url:
                        product['full_image_url'] = full_img_url
                        # 이미지 다운로드
                        img_path = self.download_image(full_img_url, product['product_id'])
                        if img_path:
                            product['image_path'] = img_path
            except:
                pass

            # 제품 스펙 (dl/dt/dd 구조)
            try:
                spec_data = {}

                # dl 요소 찾기
                dl_elements = self.driver.find_elements(By.CSS_SELECTOR, "dl")

                for dl in dl_elements:
                    try:
                        dt_elem = dl.find_element(By.CSS_SELECTOR, "dt")
                        dd_elem = dl.find_element(By.CSS_SELECTOR, "dd")

                        if dt_elem and dd_elem:
                            key = dt_elem.text.strip()
                            value = dd_elem.text.strip()

                            if key and value and len(key) < 50:
                                spec_data[key] = value
                    except:
                        pass

                if spec_data:
                    product['specifications'] = spec_data

                # 제조사 정보 (특별 처리)
                try:
                    company_dt = self.driver.find_element(By.XPATH, "//dt[contains(text(), '제조사')]")
                    if company_dt:
                        # 다음 형제 요소 (dd) 찾기
                        company_dd = company_dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        if company_dd:
                            product['manufacturer'] = company_dd.text.strip().split('\n')[0].strip()
                except:
                    pass

                # 연락처 정보
                try:
                    phone_dt = self.driver.find_element(By.XPATH, "//dt[contains(text(), 'PHONE')]")
                    if phone_dt:
                        phone_dd = phone_dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        if phone_dd:
                            product['phone'] = phone_dd.text.strip()
                except:
                    pass

                try:
                    email_dt = self.driver.find_element(By.XPATH, "//dt[contains(text(), 'MAIL') or contains(text(), 'EMAIL')]")
                    if email_dt:
                        email_dd = email_dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        if email_dd:
                            product['email'] = email_dd.text.strip()
                except:
                    pass

            except:
                pass

            product['crawled_at'] = datetime.now().isoformat()
            self.stats['products_crawled'] += 1

            # 제품을 완료로 표시
            self.mark_product_completed(product_id)

        except Exception as e:
            print(f"    ⚠️ Detail crawl failed: {e}")
            self.stats['errors'] += 1

        return product

    def crawl_all_categories(self, categories: list, crawl_details: bool = True):
        """모든 카테고리 크롤링 (이어하기 지원)"""
        # Selenium WebDriver 설정
        self.setup_driver()

        try:
            print("\n" + "="*60, flush=True)
            print(f"🚀 Starting Onehago.com Crawler (Selenium - Resumable)", flush=True)
            print("="*60, flush=True)
            print(f"Categories to crawl: {len(categories)}", flush=True)
            print(f"Crawl details: {crawl_details}", flush=True)
            print(f"Already completed: {len(self.progress.get('completed_products', []))} products", flush=True)
            print("="*60, flush=True)

            all_products = []

            # 각 카테고리 크롤링
            for idx, category in enumerate(categories):
                category_id = category['id']
                category_name = category['name']

                print(f"\n[{idx + 1}/{len(categories)}]")

                # 카테고리 페이지 크롤링
                products = self.crawl_category_page(category_id, category_name)

                # 상세 페이지 크롤링 (옵션)
                if crawl_details and products:
                    # 크롤링할 제품 필터링 (이미 완료된 제품 제외)
                    products_to_crawl = [p for p in products if not p.get('already_crawled', False)]

                    if products_to_crawl:
                        print(f"  🔍 Crawling {len(products_to_crawl)} NEW product details (skipping {len(products) - len(products_to_crawl)} already done)...")

                        for pidx, product in enumerate(products_to_crawl):
                            print(f"    [{pidx + 1}/{len(products_to_crawl)}] {product.get('product_name', 'N/A')}")

                            detailed = self.crawl_product_detail(product)

                            # products 리스트에서 해당 제품 업데이트
                            for i, p in enumerate(products):
                                if p['product_id'] == detailed['product_id']:
                                    products[i] = detailed
                                    break

                            # 지연
                            if pidx < len(products_to_crawl) - 1:
                                self.random_delay()
                    else:
                        print(f"  ✓ All {len(products)} products in this category already crawled")

                all_products.extend(products)

                # 카테고리를 완료로 표시
                self.mark_category_completed(category_id)

                # 카테고리 간 지연
                if idx < len(categories) - 1:
                    self.random_delay()

            # 전체 제품 리스트 저장
            output_file = self.output_dir / "all_products.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print("\n" + "="*60)
            print("✅ Crawling Complete!")
            print("="*60)
            print(f"Categories processed: {self.stats['categories_processed']}")
            print(f"Products found: {self.stats['products_found']}")
            print(f"Products crawled: {self.stats['products_crawled']}")
            print(f"Images downloaded: {self.stats['images_downloaded']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"Total products saved: {len(all_products)}")
            print(f"Output file: {output_file}")
            print("="*60)

        finally:
            if self.driver:
                self.driver.quit()
                print("✅ Browser closed")


def main():
    import sys
    import json
    from pathlib import Path

    # Load all valid categories from JSON file
    valid_categories_file = Path("data/onehago/valid_categories.json")

    if valid_categories_file.exists():
        print("📂 Loading valid categories from file...")
        with open(valid_categories_file, 'r', encoding='utf-8') as f:
            all_categories = json.load(f)
        print(f"✅ Loaded {len(all_categories)} valid categories")
        print(f"📊 Estimated total products: {sum(c['products'] * c['pages'] for c in all_categories):,}")
    else:
        # Fallback to test categories if file doesn't exist
        print("⚠️ Valid categories file not found, using test categories")
        all_categories = [
            {'id': '2', 'name': 'PACKAGING'},
            {'id': '7', 'name': 'BOTTLE'},
            {'id': '21', 'name': 'CONTAINER'},
        ]

    crawler = OneHagoCrawler(
        delay_min=3.0,
        delay_max=8.0,
        headless=True
    )

    # 상세 크롤링 여부
    crawl_details = len(sys.argv) > 1 and sys.argv[1] == '--details'

    crawler.crawl_all_categories(all_categories, crawl_details=crawl_details)


if __name__ == "__main__":
    main()
