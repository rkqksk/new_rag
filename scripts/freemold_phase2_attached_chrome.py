#!/usr/bin/env python3
"""
🚀 FREEMOLD PHASE 2 - 사용자의 로그인된 Chrome에 연결

이 스크립트는 사용자가 다음 명령어로 시작한 Chrome에 연결합니다:
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome \
  --remote-debugging-port=9222 \
  https://www.freemold.net

특징:
✅ 새로운 Chrome을 생성하지 않습니다
✅ 사용자의 로그인 세션을 그대로 사용합니다
✅ WebSocket을 통해 Chrome DevTools Protocol로 직접 통신합니다
"""

import json
import time
import logging
import asyncio
import websockets
import requests
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

log_file = LOG_DIR / f"freemold_phase2_attached_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# CHROME DEVTOOLS PROTOCOL 연결
# ============================================

class ChromeConnection:
    def __init__(self, host='127.0.0.1', port=9222):
        self.host = host
        self.port = port
        self.ws = None
        self.msg_id = 0

    async def connect(self):
        """Chrome DevTools Protocol에 연결"""
        try:
            # Chrome 인스턴스 목록 조회
            url = f"http://{self.host}:{self.port}/json"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            targets = response.json()

            # 탭이 없으면 생성
            if not targets:
                logger.info("📝 Chrome 탭 생성 중...")
                create_response = requests.put(
                    f"http://{self.host}:{self.port}/json/new",
                    json={'url': BASE_URL},
                    timeout=10
                )
                if create_response.status_code != 200:
                    logger.error("❌ Chrome 탭을 생성할 수 없습니다")
                    return False

                target = create_response.json()
                logger.info(f"✅ Chrome 탭 생성됨: {BASE_URL}")

                # 페이지 로딩 대기
                import asyncio
                await asyncio.sleep(3)
            else:
                # 첫 번째 탭 사용
                target = targets[0]
                logger.info(f"✅ 기존 Chrome 탭 발견: {target.get('title', 'Unknown')[:50]}")

            # WebSocket URL 가져오기
            ws_url = target.get('webSocketDebuggerUrl')
            if not ws_url:
                logger.error("❌ WebSocket 디버거 URL을 찾을 수 없습니다")
                return False

            # WebSocket 연결
            self.ws = await websockets.connect(ws_url)
            logger.info("✅ Chrome DevTools Protocol에 연결됨")
            return True

        except Exception as e:
            logger.error(f"❌ 연결 실패: {e}")
            logger.error("\n⚠️  Chrome이 다음과 같이 실행되어야 합니다:")
            logger.error("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome \\")
            logger.error("  --user-data-dir=/tmp/chrome_remote_debug \\")
            logger.error("  --remote-debugging-port=9222 \\")
            logger.error("  https://www.freemold.net")
            return False

    async def send_command(self, method, params=None):
        """Chrome DevTools 명령 전송"""
        if not self.ws:
            return None

        self.msg_id += 1
        command = {
            'id': self.msg_id,
            'method': method,
            'params': params or {}
        }

        await self.ws.send(json.dumps(command))

        # 응답 기다리기
        while True:
            response = await self.ws.recv()
            data = json.loads(response)
            if data.get('id') == self.msg_id:
                return data

    async def navigate_to(self, url):
        """URL로 이동"""
        result = await self.send_command('Page.navigate', {'url': url})
        await asyncio.sleep(2)  # 페이지 로딩 대기
        return result

    async def get_page_source(self):
        """페이지 소스 코드 가져오기"""
        # DOM 가져오기
        dom_result = await self.send_command('DOM.getDocument')

        if dom_result.get('result'):
            node_id = dom_result['result'].get('root', {}).get('nodeId')
            if node_id:
                outer_html = await self.send_command(
                    'DOM.getOuterHTML',
                    {'nodeId': node_id}
                )
                return outer_html.get('result', {}).get('outerHTML', '')

        return None

    async def close(self):
        """연결 종료"""
        if self.ws:
            await self.ws.close()

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

async def main():
    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2 - 로그인된 Chrome에 연결")
    logger.info("=" * 80)

    # Chrome에 연결
    chrome = ChromeConnection()
    if not await chrome.connect():
        logger.error("❌ Chrome에 연결할 수 없습니다")
        return

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

            for i, product in enumerate(products):
                product_url = product['url']
                product_id = product['product_id']

                try:
                    # 페이지 이동
                    await chrome.navigate_to(product_url)

                    # 페이지 소스 가져오기
                    html = await chrome.get_page_source()

                    if html:
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
                            logger.info(f"✅ 체크포인트 저장\n")

                except Exception as e:
                    logger.error(f"❌ {product_id} 추출 실패: {str(e)[:100]}")

                # 짧은 대기
                await asyncio.sleep(0.5)

        logger.info(f"\n✅ 추출 완료: {extracted_count}개 상품")

    except KeyboardInterrupt:
        logger.info("\n⚠️  사용자에 의해 중단됨")

    finally:
        await chrome.close()
        logger.info("🔒 Chrome 연결 종료")

if __name__ == "__main__":
    asyncio.run(main())
