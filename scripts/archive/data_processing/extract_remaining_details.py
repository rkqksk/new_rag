#!/usr/bin/env python3
"""
나머지 제품의 상세정보만 빠르게 추출하는 스크립트
"""
import json
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/onehago_remaining_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_product_details(product):
    """단일 제품의 상세 정보 추출"""
    if not product.get('detail_url'):
        return product
    
    # 이미 상세정보가 있으면 건너뛰기
    if product.get('specifications'):
        return product

    try:
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ])
        }

        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(product['detail_url'], headers=headers, timeout=10)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 상세정보 추출 (dl 태그 기반)
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
            except Exception as e:
                logger.warning(f"상세정보 추출 중 오류: {e}")

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

            logger.info(f"✅ 제품 ID {product['product_id']} 상세정보 추출 완료")
        else:
            logger.warning(f"⚠️ 제품 ID {product['product_id']} - 상세정보 없음")

        return product

    except Exception as e:
        logger.error(f"❌ 제품 ID {product.get('product_id', 'N/A')} 처리 중 오류: {e}")
        return product

def main():
    input_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_merged_with_details.json'
    output_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_complete.json'

    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # 상세정보 없는 제품만 필터링
    products_to_extract = [p for p in products if not p.get('specifications')]
    
    logger.info(f"📊 총 제품: {len(products)}개")
    logger.info(f"🔍 추출 필요: {len(products_to_extract)}개")
    logger.info(f"✅ 이미 완료: {len(products) - len(products_to_extract)}개")
    print()

    if not products_to_extract:
        logger.info("✅ 모든 제품의 상세정보가 이미 존재합니다!")
        return

    # 병렬 처리
    logger.info(f"🚀 {len(products_to_extract)}개 제품 상세정보 추출 시작...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(extract_product_details, p): i for i, p in enumerate(products_to_extract)}
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                updated_product = future.result()
                # 원본 리스트에서 업데이트
                for i, p in enumerate(products):
                    if p['product_id'] == updated_product['product_id']:
                        products[i] = updated_product
                        break
                
                # 진행 상황 출력 (10개마다)
                if (idx + 1) % 10 == 0:
                    logger.info(f"진행: {idx + 1}/{len(products_to_extract)}")
                    
            except Exception as e:
                logger.error(f"처리 중 오류: {e}")

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # 최종 통계
    final_with_specs = sum(1 for p in products if p.get('specifications'))
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 추출 완료!")
    logger.info(f"{'='*60}")
    logger.info(f"총 제품: {len(products)}개")
    logger.info(f"상세정보 있음: {final_with_specs}개")
    logger.info(f"상세정보 없음: {len(products) - final_with_specs}개")
    logger.info(f"출력 파일: {output_file}")
    logger.info(f"{'='*60}")

if __name__ == '__main__':
    main()
