#!/usr/bin/env python3
"""
실시간 저장 + 빠른 스킵 로직을 가진 Onehago 크롤러
- 제품별 즉시 저장
- 이미 크롤링된 제품은 즉시 스킵
- 병렬 처리로 속도 최적화
"""
import json
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/onehago_realtime_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OnehagoRealtimeCrawler:
    """실시간 저장 크롤러"""

    def __init__(self, output_file: str):
        self.output_file = Path(output_file)
        self.completed_ids = set()
        self.data_lock = None  # ThreadPoolExecutor는 GIL 보호

        # 기존 데이터 로드
        self.load_existing_data()

    def load_existing_data(self):
        """기존 크롤링 데이터 로드"""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    products = json.load(f)

                # 이미 상세정보가 있는 제품 ID 수집
                for p in products:
                    if p.get('specifications'):
                        self.completed_ids.add(p['product_id'])

                logger.info(f"✅ 기존 데이터 로드: {len(products)}개 제품")
                logger.info(f"✅ 이미 완료된 제품: {len(self.completed_ids)}개")

                self.products = products
            except Exception as e:
                logger.error(f"기존 데이터 로드 실패: {e}")
                self.products = []
        else:
            self.products = []
            logger.info("새로운 크롤링 시작")

    def is_completed(self, product_id: str) -> bool:
        """제품이 이미 크롤링 완료되었는지 확인 (즉시 스킵)"""
        return product_id in self.completed_ids

    def save_realtime(self):
        """실시간 저장 (매번 호출)"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"저장 실패: {e}")

    def extract_product_details(self, product: dict) -> dict:
        """단일 제품 상세정보 추출"""
        product_id = product['product_id']

        # ⚡ 빠른 스킵: 이미 완료된 제품
        if self.is_completed(product_id):
            logger.debug(f"⏭️ 스킵: {product_id} (이미 완료)")
            return product

        if not product.get('detail_url'):
            return product

        try:
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ])
            }

            time.sleep(random.uniform(0.3, 0.8))  # 더 빠른 지연
            response = requests.get(product['detail_url'], headers=headers, timeout=10)
            response.encoding = 'euc-kr'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 상세정보 추출
            specifications = {}
            dl_elements = soup.find_all('dl')
            for dl in dl_elements:
                try:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd:
                        key = dt.get_text(strip=True)
                        value = dd.get_text(strip=True)
                        if key and value and len(key) < 50:
                            specifications[key] = value
                except:
                    pass

            # 이미지, 제조사, 연락처 추출
            img_elem = soup.find('img', src=lambda x: x and 'productImages' in x)
            full_image_url = img_elem['src'] if img_elem else None

            manufacturer_dt = soup.find('dt', string=lambda x: x and '제조사' in x)
            manufacturer = manufacturer_dt.find_next('dd').get_text(strip=True).split('\n')[0].strip() if manufacturer_dt else None

            phone_dt = soup.find('dt', string=lambda x: x and 'PHONE' in x)
            phone = phone_dt.find_next('dd').get_text(strip=True) if phone_dt else None

            fax_dt = soup.find('dt', string=lambda x: x and 'FAX' in x)
            fax = fax_dt.find_next('dd').get_text(strip=True) if fax_dt else None

            email_dt = soup.find('dt', string=lambda x: x and 'MAIL' in x)
            email = email_dt.find_next('dd').get_text(strip=True) if email_dt else None

            contact_dt = soup.find('dt', string=lambda x: x and '담당' in x)
            contact = contact_dt.find_next('dd').get_text(strip=True) if contact_dt else None

            # 제품 정보 업데이트
            if specifications:
                product['specifications'] = specifications
                product['full_image_url'] = full_image_url
                product['manufacturer'] = manufacturer
                product['phone'] = phone
                product['fax'] = fax
                product['email'] = email
                product['contact'] = contact
                product['already_crawled'] = True
                product['crawled_at'] = datetime.now().isoformat()

                # ✅ 완료 목록에 추가
                self.completed_ids.add(product_id)

                logger.info(f"✅ {product_id} 완료")

                return product
            else:
                logger.warning(f"⚠️ {product_id} - 상세정보 없음")
                return product

        except Exception as e:
            logger.error(f"❌ {product_id} 오류: {e}")
            return product

    def crawl_batch(self, products_to_crawl: list, max_workers: int = 15):
        """배치 크롤링 + 실시간 저장"""
        logger.info(f"🚀 {len(products_to_crawl)}개 제품 크롤링 시작...")

        completed_count = 0
        save_interval = 10  # 10개마다 저장

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.extract_product_details, p): i for i, p in enumerate(products_to_crawl)}

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    updated_product = future.result()

                    # 원본 리스트 업데이트
                    for i, p in enumerate(self.products):
                        if p['product_id'] == updated_product['product_id']:
                            self.products[i] = updated_product
                            break

                    completed_count += 1

                    # 💾 실시간 저장 (10개마다)
                    if completed_count % save_interval == 0:
                        self.save_realtime()
                        logger.info(f"💾 저장 완료: {completed_count}/{len(products_to_crawl)}")

                except Exception as e:
                    logger.error(f"처리 중 오류: {e}")

        # 최종 저장
        self.save_realtime()
        logger.info(f"✅ 최종 저장 완료: {completed_count}개 제품")

def main():
    """메인 실행 함수"""
    # 입력 파일 (기본 정보)
    input_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_merged.json'

    # 출력 파일 (실시간 업데이트) - 올바른 작업 폴더
    output_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/full_crawl_clean/all_products_clean.json'

    # 크롤러 초기화
    crawler = OnehagoRealtimeCrawler(output_file)

    # 입력 데이터가 없으면 로드
    if not crawler.products:
        with open(input_file, 'r', encoding='utf-8') as f:
            crawler.products = json.load(f)

    # 크롤링 필요한 제품 필터링
    products_to_crawl = [p for p in crawler.products if not crawler.is_completed(p['product_id'])]

    logger.info(f"📊 총 제품: {len(crawler.products)}개")
    logger.info(f"✅ 이미 완료: {len(crawler.completed_ids)}개")
    logger.info(f"🔍 크롤링 필요: {len(products_to_crawl)}개")

    if not products_to_crawl:
        logger.info("✅ 모든 제품 크롤링 완료!")
        return

    # 배치 크롤링 시작
    crawler.crawl_batch(products_to_crawl, max_workers=15)

    # 최종 통계
    final_completed = sum(1 for p in crawler.products if p.get('specifications'))
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 크롤링 완료!")
    logger.info(f"{'='*60}")
    logger.info(f"총 제품: {len(crawler.products)}개")
    logger.info(f"상세정보 완료: {final_completed}개")
    logger.info(f"출력 파일: {output_file}")
    logger.info(f"{'='*60}")

if __name__ == '__main__':
    main()
