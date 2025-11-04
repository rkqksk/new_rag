#!/usr/bin/env python3
"""
Freemold 상세 정보 크롤러 (완전 수동 로그인)
- 자동 로그인 없음 - 창 뜨면 직접 로그인
- WebDriverWait로 JavaScript 테이블 로딩 대기
"""
import time
import json
import random
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class FreemoldDetailCrawler:
    def __init__(self, delay_min=5.0, delay_max=7.0):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.output_dir = Path('data/freemold/crawled_v2')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress_manual.json'
        self.progress = self.load_progress()

        self.stats = {
            'crawled': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat(),
            'session_refreshes': 0
        }

    def load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'completed': []}

    def save_progress(self):
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def is_completed(self, pIdx):
        return pIdx in self.progress['completed']

    def mark_completed(self, pIdx):
        if pIdx not in self.progress['completed']:
            self.progress['completed'].append(pIdx)
            self.save_progress()

    def random_delay(self):
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def setup_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(options=options)
        return driver

    def check_session(self, driver):
        """세션 확인 - 로그아웃되었는지 체크"""
        try:
            page_source = driver.page_source
            if "로그인" in page_source and "로그아웃" not in page_source:
                return False
            if "비회원" in page_source:
                return False
            return True
        except:
            return True

    def refresh_session(self, driver):
        """세션 갱신 - 수동 로그인"""
        print(f"\n⚠️  세션 만료 감지!")
        print(f"🔄 브라우저에서 다시 로그인해주세요...")
        self.stats['session_refreshes'] += 1

        driver.get("https://www.freemold.net")
        input("로그인 완료 후 ENTER를 눌러주세요... ")

        print(f"✅ 세션 갱신 완료 (총 갱신 횟수: {self.stats['session_refreshes']})")
        return True

    def transform_to_standard(self, raw_product):
        """원시 데이터를 Onehago 표준 구조로 즉시 변환"""
        # specifications dict 생성
        specs_dict = {}

        # 기본 필드들을 specifications dict에 추가
        if raw_product.get('specifications'):
            specs_dict['사이즈'] = raw_product['specifications']
        if raw_product.get('material'):
            specs_dict['재질'] = raw_product['material']
        if raw_product.get('moq'):
            specs_dict['MOQ'] = raw_product['moq']
        if raw_product.get('origin'):
            specs_dict['원산지'] = raw_product['origin']
        if raw_product.get('manufacturer'):
            specs_dict['제조사'] = raw_product['manufacturer']

        # 표준 구조로 변환
        return {
            'product_id': raw_product.get('pIdx', ''),
            'company_no': raw_product.get('mIdx', ''),
            'category_id': raw_product.get('category_code', ''),
            'category_name': raw_product.get('category_name', ''),
            'product_name': raw_product.get('product_name', ''),
            'detailed_name': raw_product.get('product_name', ''),
            'moq': raw_product.get('moq', ''),
            'detail_url': raw_product.get('url', ''),
            'image_url': raw_product.get('main_image', ''),
            'full_image_url': raw_product.get('main_image', ''),
            'image_path': '',
            'images': raw_product.get('images', []),
            'specifications': specs_dict,
            'manufacturer': specs_dict.get('제조사', ''),
            'phone': '',
            'fax': '',
            'email': '',
            'contact': '',
            'crawled_at': raw_product.get('crawled_at', datetime.now().isoformat())
        }

    def extract_detail(self, driver, product):
        pIdx = product['pIdx']

        if self.is_completed(pIdx):
            print(f"  ✓ Already done: {pIdx}")
            return None

        url = product['product_url']

        try:
            driver.get(url)

            # WebDriverWait로 JavaScript 테이블 로딩 대기
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'table'))
                )
                time.sleep(1)  # 추가 버퍼
            except:
                print(f"  ⚠️  테이블 로딩 10초 대기 후에도 없음")

            result = {
                'pIdx': pIdx,
                'mIdx': product.get('mIdx'),
                'category_code': product.get('category_code'),
                'category_name': product.get('category_name'),
                'url': url,
                'crawled_at': datetime.now().isoformat()
            }

            # 이미지 URL 추출 (제품 상세 이미지들)
            try:
                # 주요 이미지: .product-image, .detail-image, img 태그 등
                images = []

                # 메인 제품 이미지
                main_imgs = driver.find_elements(By.CSS_SELECTOR, '.product-image img, .main-image img, .detail_img img')
                for img in main_imgs:
                    src = img.get_attribute('src')
                    if src and src.startswith('http'):
                        images.append(src)

                # 추가 상세 이미지
                detail_imgs = driver.find_elements(By.CSS_SELECTOR, '#product_detail img, .product_detail img')
                for img in detail_imgs:
                    src = img.get_attribute('src')
                    if src and src.startswith('http') and src not in images:
                        images.append(src)

                if images:
                    result['images'] = images
                    result['main_image'] = images[0] if images else None
            except Exception as e:
                print(f"  ⚠️  이미지 추출 실패: {e}")

            # 테이블에서 데이터 추출
            tables = driver.find_elements(By.TAG_NAME, 'table')

            for table in tables:
                rows = table.find_elements(By.TAG_NAME, 'tr')

                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) >= 2:
                            label = cells[0].text.strip()
                            value = cells[1].text.strip()

                            if '제품명' in label:
                                result['product_name'] = value
                            elif '제품규격' in label or '규격' in label:
                                result['specifications'] = value
                            elif '재질' in label:
                                result['material'] = value
                            elif 'MOQ' in label.upper():
                                result['moq'] = value
                            elif '원산지' in label:
                                result['origin'] = value
                            elif '제조사' in label or '회사명' in label:
                                result['manufacturer'] = value
                    except:
                        pass

            self.stats['crawled'] += 1
            self.mark_completed(pIdx)

            # 즉시 표준 구조로 변환하여 반환
            return self.transform_to_standard(result)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats['errors'] += 1
            return None

    def crawl_all(self, products):
        driver = self.setup_driver()

        try:
            # 수동 로그인
            print("\n" + "=" * 70)
            print("🔐 수동 로그인")
            print("=" * 70)
            driver.get("https://www.freemold.net")

            print("\n⏸️  브라우저에서 직접 로그인해주세요...")
            input("로그인 완료 후 ENTER를 눌러주세요... ")

            print("\n✅ 로그인 확인! 크롤링 시작...")
            print(f"📊 총 제품 수: {len(products)}")
            print(f"⏱️  예상 시간: {len(products) * 6 / 3600:.1f} 시간\n")

            # 크롤링 시작
            results = []

            for idx, product in enumerate(products, 1):
                # 100개마다 세션 체크
                if idx % 100 == 0:
                    print(f"\n🔍 세션 확인 중 ({idx}개 제품 완료)...")
                    if not self.check_session(driver):
                        if not self.refresh_session(driver):
                            print(f"❌ 세션 갱신 실패")
                            break
                    else:
                        print(f"✅ 세션 유지 중")

                print(f"[{idx}/{len(products)}] pIdx={product['pIdx']}")

                result = self.extract_detail(driver, product)
                if result:
                    results.append(result)

                # 50개마다 저장
                if len(results) % 50 == 0 and results:
                    output_file = self.output_dir / f"products_batch_{len(results)}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results[-50:], f, ensure_ascii=False, indent=2)
                    print(f"  💾 배치 저장: {output_file.name}")

                self.random_delay()

            # 최종 저장
            final_file = self.output_dir / 'all_products_detailed.json'
            with open(final_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print("\n" + "=" * 70)
            print("✅ 크롤링 완료")
            print("=" * 70)
            print(f"수집: {self.stats['crawled']}")
            print(f"에러: {self.stats['errors']}")
            print(f"세션 갱신: {self.stats['session_refreshes']}")
            print(f"출력: {final_file}")

        finally:
            driver.quit()

def main():
    universal_file = Path('data/freemold/universal/A001_products.json')

    print("=" * 70)
    print("🏭 FREEMOLD 상세 크롤러 (수동 로그인)")
    print("=" * 70)
    print(f"\n📂 로딩: {universal_file}")

    with open(universal_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"✅ {len(products)}개 제품 로드 완료\n")

    crawler = FreemoldDetailCrawler(delay_min=5.0, delay_max=7.0)
    crawler.crawl_all(products)

if __name__ == "__main__":
    main()
