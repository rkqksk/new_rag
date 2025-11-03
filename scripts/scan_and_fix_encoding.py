#!/usr/bin/env python3
"""
인코딩 깨진 제품 데이터 스캔 및 수정
- 크롤링 완료 후 실행
- 깨진 데이터 검출 및 재크롤링
"""
import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/encoding_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def is_corrupted_text(text):
    """텍스트가 깨졌는지 확인"""
    if not isinstance(text, str):
        return False

    # 한글이 깨지면 나타나는 패턴들
    corruption_patterns = [
        r'[�]{2,}',  # ��� 같은 패턴
        r'[\x80-\xff]{3,}',  # 비정상적인 바이트 시퀀스
        r'[酉곗궗]',  # 깨진 한글 특정 패턴
    ]

    for pattern in corruption_patterns:
        if re.search(pattern, text):
            return True

    # 한글이 전혀 없고 이상한 문자만 있는 경우
    if not re.search(r'[가-힣]', text) and re.search(r'[^\x00-\x7F]{5,}', text):
        return True

    return False


def scan_product_encoding(product):
    """제품 데이터의 인코딩 상태 검사"""
    product_id = product.get('product_id')
    issues = []

    # 제품명 검사
    if is_corrupted_text(product.get('product_name', '')):
        issues.append('product_name')

    # specifications 검사
    specs = product.get('specifications', {})
    if isinstance(specs, dict):
        for key, value in specs.items():
            if is_corrupted_text(key):
                issues.append(f'spec_key: {key[:20]}...')
            if is_corrupted_text(str(value)):
                issues.append(f'spec_value: {key}')

    # 기타 필드 검사
    text_fields = ['manufacturer', 'phone', 'contact', 'email']
    for field in text_fields:
        if is_corrupted_text(product.get(field, '')):
            issues.append(field)

    return {
        'product_id': product_id,
        'detail_url': product.get('detail_url'),
        'corrupted': len(issues) > 0,
        'issues': issues
    }


def recrawl_product_detail(product_info):
    """깨진 제품 재크롤링"""
    product_id = product_info['product_id']
    detail_url = product_info['detail_url']

    if not detail_url:
        logger.warning(f"❌ {product_id}: detail_url 없음")
        return None

    try:
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            ])
        }

        time.sleep(random.uniform(0.5, 1.5))

        # EUC-KR로 명시적으로 요청
        response = requests.get(detail_url, headers=headers, timeout=10)
        response.encoding = 'euc-kr'

        soup = BeautifulSoup(response.text, 'html.parser')

        # 상세정보 추출 (dl/dt/dd)
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
                logger.warning(f"dl 파싱 오류: {e}")

        # 제조사, 연락처 등
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

        fixed_data = {
            'specifications': specifications,
            'manufacturer': manufacturer,
            'phone': phone,
            'fax': fax,
            'email': email,
            'contact': contact,
        }

        logger.info(f"✅ {product_id} 재크롤링 완료")
        return fixed_data

    except Exception as e:
        logger.error(f"❌ {product_id} 재크롤링 실패: {e}")
        return None


def main():
    """메인 실행 함수"""
    input_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products.json'
    output_file = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_fixed.json'

    logger.info("=" * 60)
    logger.info("🔍 인코딩 검수 및 수정 시작")
    logger.info("=" * 60)
    logger.info(f"입력: {input_file}")
    logger.info(f"출력: {output_file}")
    logger.info("")

    # 1단계: 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"📊 총 {len(products):,}개 제품 로드 완료")
    logger.info("")

    # 2단계: 인코딩 스캔
    logger.info("🔍 1단계: 인코딩 문제 스캔 중...")
    corrupted_products = []

    for i, product in enumerate(products):
        scan_result = scan_product_encoding(product)
        if scan_result['corrupted']:
            corrupted_products.append(scan_result)

        if (i + 1) % 1000 == 0:
            logger.info(f"   진행: {i + 1}/{len(products)} ({len(corrupted_products)} 문제 발견)")

    logger.info("")
    logger.info(f"✅ 스캔 완료: {len(corrupted_products):,}개 제품에서 인코딩 문제 발견")
    logger.info("")

    # 3단계: 깨진 제품 재크롤링
    if corrupted_products:
        logger.info(f"🔧 2단계: {len(corrupted_products)}개 제품 재크롤링 시작...")
        logger.info(f"   병렬 처리: 10개 워커")
        logger.info("")

        fixed_count = 0
        product_map = {p['product_id']: p for p in products}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(recrawl_product_detail, cp): cp for cp in corrupted_products}

            for future in as_completed(futures):
                corrupt_product = futures[future]
                try:
                    fixed_data = future.result()

                    if fixed_data:
                        # 원본 제품 데이터 업데이트
                        product_id = corrupt_product['product_id']
                        if product_id in product_map:
                            product_map[product_id].update(fixed_data)
                            fixed_count += 1

                    if fixed_count % 10 == 0:
                        logger.info(f"   진행: {fixed_count}/{len(corrupted_products)}")

                except Exception as e:
                    logger.error(f"처리 중 오류: {e}")

        logger.info("")
        logger.info(f"✅ 재크롤링 완료: {fixed_count}/{len(corrupted_products)}개 수정")
        logger.info("")

    # 4단계: 결과 저장
    logger.info("💾 3단계: 수정된 데이터 저장 중...")
    fixed_products = list(product_map.values())

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_products, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 저장 완료: {output_file}")
    logger.info("")

    # 5단계: 최종 검증
    logger.info("🔍 4단계: 최종 검증 중...")
    remaining_issues = sum(1 for p in fixed_products if scan_product_encoding(p)['corrupted'])

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ 인코딩 검수 및 수정 완료!")
    logger.info("=" * 60)
    logger.info(f"총 제품: {len(fixed_products):,}개")
    logger.info(f"발견된 문제: {len(corrupted_products):,}개")
    logger.info(f"수정 완료: {fixed_count:,}개")
    logger.info(f"남은 문제: {remaining_issues:,}개")
    logger.info(f"출력 파일: {output_file}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
