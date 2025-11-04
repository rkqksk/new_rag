import json
import os
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import logging
import time
import random

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/onehago_details_merger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_product_details(product):
    """
    단일 제품의 상세 정보 추출
    """
    if not product.get('detail_url'):
        return product

    try:
        # User-Agent 랜덤화
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ])
        }

        # 요청 지연 (크롤링 예의)
        time.sleep(random.uniform(0.5, 1.5))

        response = requests.get(product['detail_url'], headers=headers, timeout=10)
        response.encoding = 'euc-kr'  # 한국어 인코딩
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

        # 이미지 URL 추출
        img_elem = soup.find('img', src=lambda x: x and 'productImages' in x)
        full_image_url = img_elem['src'] if img_elem else None

        # 제조사 정보 추출
        manufacturer_dt = soup.find('dt', string=lambda x: x and '제조사' in x)
        manufacturer = manufacturer_dt.find_next('dd').get_text(strip=True) if manufacturer_dt else None

        # 연락처 정보 추출
        phone_dt = soup.find('dt', string=lambda x: x and 'PHONE' in x)
        phone = phone_dt.find_next('dd').get_text(strip=True) if phone_dt else None

        email_dt = soup.find('dt', string=lambda x: x and 'MAIL' in x)
        email = email_dt.find_next('dd').get_text(strip=True) if email_dt else None

        # 제품 정보 업데이트
        product['specifications'] = specifications
        product['full_image_url'] = full_image_url
        product['manufacturer'] = manufacturer
        product['phone'] = phone
        product['email'] = email
        product['already_crawled'] = True

        logger.info(f"제품 ID {product['product_id']} 상세정보 추출 완료")
        return product

    except Exception as e:
        logger.error(f"제품 ID {product.get('product_id', 'N/A')} 처리 중 오류: {e}")
        return product

def merge_product_details(input_file, output_file, max_workers=10):
    """
    제품 상세정보 병합
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"총 {len(products)}개 제품 처리 시작")

    # 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        products = list(executor.map(extract_product_details, products))

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # 추출 통계
    detailed_products = [p for p in products if p.get('specifications')]
    logger.info(f"총 {len(detailed_products)}개 제품 상세정보 추출 완료")

def main():
    input_dir = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/'
    output_dir = '/Users/oypnus/Project/rag-enterprise/data/onehago/full_crawl_clean/'

    os.makedirs(output_dir, exist_ok=True)

    # 모든 카테고리 파일 처리
    for filename in os.listdir(input_dir):
        if filename.startswith('category_') and filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f'processed_{filename}')

            logger.info(f"파일 처리 시작: {filename}")
            merge_product_details(input_path, output_path)

if __name__ == '__main__':
    main()