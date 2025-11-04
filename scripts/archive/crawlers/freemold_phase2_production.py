#!/usr/bin/env python3
"""
🚀 FREEMOLD PHASE 2 - Production Extraction (80,000 products)

사용자의 로그인된 Chrome에서 쿠키를 직접 추출하여 사용합니다.
"""

import json
import time
import logging
import requests
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://www.freemold.net"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

URLS_FILE = OUTPUT_DIR / "product_urls.jsonl"
OUTPUT_FILE = OUTPUT_DIR / "products_text_complete.jsonl"
PROGRESS_FILE = OUTPUT_DIR / "freemold_phase2_progress.json"

log_file = LOG_DIR / f"freemold_phase2_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# CHROME COOKIE 추출
# ============================================

def extract_cookies_from_chrome():
    """macOS Chrome에서 쿠키 추출"""

    logger.info("\n" + "=" * 80)
    logger.info("🍪 Chrome 쿠키 추출 중...")
    logger.info("=" * 80)

    try:
        # macOS Chrome 쿠키 경로
        chrome_cookie_path = os.path.expanduser(
            "~/Library/Application Support/Google/Chrome/Default/Cookies"
        )

        if not os.path.exists(chrome_cookie_path):
            logger.warning(f"⚠️  Cookie 파일을 찾을 수 없습니다: {chrome_cookie_path}")
            return {}

        # 임시 파일에 복사 (Chrome이 파일을 사용 중이므로)
        import shutil
        temp_cookie_path = "/tmp/chrome_cookies.db"
        shutil.copy(chrome_cookie_path, temp_cookie_path)

        # SQLite에서 쿠키 읽기
        conn = sqlite3.connect(temp_cookie_path)
        cursor = conn.cursor()

        # freemold.net 쿠키 조회
        cursor.execute("""
            SELECT name, value FROM cookies
            WHERE host_key LIKE '%.freemold.net%'
        """)

        cookies = {}
        for name, value in cursor.fetchall():
            cookies[name] = value

        conn.close()
        os.remove(temp_cookie_path)

        if cookies:
            logger.info(f"✅ {len(cookies)}개 쿠키 추출됨")
            logger.info(f"   쿠키: {list(cookies.keys())[:5]}...")
        else:
            logger.warning("⚠️  freemold.net 쿠키를 찾을 수 없습니다")

        return cookies

    except Exception as e:
        logger.error(f"❌ 쿠키 추출 실패: {e}")
        return {}

# ============================================
# 진행 상황 추적
# ============================================

def load_progress():
    """진행 상황 로드"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'products_extracted': 0, 'start_time': datetime.now().isoformat()}

def save_progress(count):
    """진행 상황 저장"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'products_extracted': count, 'start_time': datetime.now().isoformat()}, f)

# ============================================
# 상품 데이터 추출
# ============================================

def extract_product_from_html(html, product_id, product_url, category, category_name):
    """HTML에서 상품 데이터 추출"""

    product_data = {
        'product_id': product_id,
        'url': product_url,
        'category': category,
        'category_name': category_name,
        'crawled_at': datetime.now().isoformat(),
        'name': None,
        'description': None,
        'specs': {},
        'manufacturer': None,
        'supplier': None,
        'contact': None,
        'tags': [],
        'images': [],
        'related_products': []
    }

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 제품명
        name_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'title' in x.lower() if x else False)
        if name_elem:
            product_data['name'] = name_elem.get_text(strip=True)[:500]

        # 설명
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'detail', 'body', 'main']) if x else False)
        if main_content:
            for p in main_content.find_all(['p', 'div', 'span'], limit=20):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    if not product_data['description']:
                        product_data['description'] = text[:2000]
                    elif len(product_data['description']) < 3000:
                        product_data['description'] += '\n' + text[:500]

        # 테이블 데이터
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if '제품명' in label or 'product name' in label:
                        product_data['name'] = value[:500]
                    elif '규격' in label or 'specification' in label:
                        product_data['specs']['specification'] = value
                    elif '용량' in label or 'capacity' in label or 'size' in label:
                        product_data['specs']['capacity'] = value
                    elif '재질' in label or 'material' in label:
                        product_data['specs']['material'] = value
                    elif '제조사' in label or 'manufacturer' in label:
                        product_data['manufacturer'] = value
                    elif '공급업체' in label or 'supplier' in label:
                        product_data['supplier'] = value
                    elif '연락처' in label or 'contact' in label or '전화' in label:
                        product_data['contact'] = value

        # 이미지
        images = soup.find_all('img', src=lambda x: x and any(k in x.lower() for k in ['product', 'image', 'pic']) if x else False)
        for img in images[:10]:
            img_url = img.get('src', '')
            if img_url and not img_url.startswith('data:'):
                if not img_url.startswith('http'):
                    img_url = urljoin(BASE_URL, img_url)
                product_data['images'].append(img_url)

    except Exception as e:
        logger.error(f"❌ 추출 에러 {product_id}: {str(e)[:100]}")

    return product_data

# ============================================
# 메인
# ============================================

def main():
    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2 - Production Extraction (80,000 products)")
    logger.info("=" * 80)

    # Chrome에서 쿠키 추출
    cookies = extract_cookies_from_chrome()

    if not cookies:
        logger.error("❌ 쿠키를 추출할 수 없습니다")
        logger.info("\n✅ 대신 requests session을 사용합니다")

    # Session 생성
    session = requests.Session()
    session.verify = False  # SSL 검증 무시

    # 쿠키 추가
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='www.freemold.net')

    # HTTP 경고 무시
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        # 진행 상황 로드
        progress = load_progress()
        start_index = progress['products_extracted']

        logger.info(f"\n📊 시작 위치: {start_index}")

        # 상품 URL 로드
        products = []
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r') as f:
                for i, line in enumerate(f):
                    if i >= start_index:
                        data = json.loads(line)
                        products.append(data)
        else:
            logger.error(f"❌ {URLS_FILE} 찾을 수 없음")
            return

        logger.info(f"📦 추출할 상품: {len(products)}개\n")

        # 상품 추출
        with open(OUTPUT_FILE, 'a') as out_f:
            extracted_count = 0
            failed_count = 0

            for i, product in enumerate(products):
                product_url = product['url']
                product_id = product['product_id']

                try:
                    # 페이지 요청
                    response = session.get(product_url, timeout=10, verify=False)

                    if response.status_code == 200:
                        html = response.text

                        # 비회원 에러 확인
                        if '비회원은' in html:
                            logger.warning(f"⚠️  [{extracted_count + 1}] {product_id}: 비회원 에러")
                            failed_count += 1
                        else:
                            # 데이터 추출
                            result = extract_product_from_html(
                                html,
                                product_id,
                                product_url,
                                product['category'],
                                product['category_name']
                            )

                            # 결과 저장
                            out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                            out_f.flush()

                            extracted_count += 1

                            # 보고
                            if result['name']:
                                logger.info(f"✅ [{extracted_count}] {product_id}: {result['name'][:40]}")
                            else:
                                logger.warning(f"⚠️  [{extracted_count}] {product_id}: 데이터 없음")

                            # 체크포인트
                            if extracted_count % 100 == 0:
                                save_progress(start_index + extracted_count)
                                pct = 100 * extracted_count // len(products) if products else 0
                                logger.info(f"\n📊 진행률: {extracted_count}/{len(products)} ({pct}%)")
                                logger.info(f"✅ 체크포인트 저장 ({failed_count} 실패)\n")
                    else:
                        logger.warning(f"❌ HTTP {response.status_code} - {product_id}")
                        failed_count += 1

                except Exception as e:
                    logger.error(f"❌ {product_id} 추출 실패: {str(e)[:100]}")
                    failed_count += 1

                # 짧은 대기
                if extracted_count > 0 and extracted_count % 10 == 0:
                    time.sleep(0.5)

        logger.info(f"\n✅ 추출 완료:")
        logger.info(f"   ✅ 성공: {extracted_count}개")
        logger.info(f"   ❌ 실패: {failed_count}개")
        logger.info(f"   📦 총합: {extracted_count + failed_count}개")

    except KeyboardInterrupt:
        logger.info("\n⚠️  사용자에 의해 중단됨")

    finally:
        logger.info("🔒 세션 종료")

if __name__ == "__main__":
    main()
