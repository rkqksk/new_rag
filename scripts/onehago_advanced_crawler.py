import json
import requests
import logging
from bs4 import BeautifulSoup
import random
import time
import re
import concurrent.futures

# 고급 세션 및 보안 우회 기능을 포함한 고급 크롤러
class OnehavoAdvancedCrawler:
    def __init__(self, proxy_list=None):
        self.logger = self._setup_logger()
        self.session = self._create_session()
        self.proxy_list = proxy_list or []

    def _setup_logger(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('/tmp/onehago_crawler.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _create_session(self):
        """보안 및 성능 최적화된 세션 생성"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self._random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://onehago.com/mall/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session

    def _random_user_agent(self):
        """랜덤 User-Agent 선택"""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        ]
        return random.choice(agents)

    def _rotate_proxy(self):
        """프록시 로테이션 (선택적)"""
        if self.proxy_list:
            return random.choice(self.proxy_list)
        return None

    def fetch_page(self, url, max_retries=3):
        """
        고급 페이지 가져오기 메서드
        반복적인 접근과 다양한 에러 처리
        """
        for attempt in range(max_retries):
            try:
                proxy = self._rotate_proxy()
                proxies = {'http': proxy, 'https': proxy} if proxy else None

                # 지수적 백오프를 사용한 대기
                time.sleep(2 ** attempt + random.random())

                response = self.session.get(
                    url,
                    proxies=proxies,
                    timeout=(10, 20),  # 연결 및 읽기 타임아웃
                    allow_redirects=True
                )

                # EUC-KR 인코딩 처리
                response.encoding = 'euc-kr'

                # 상태 코드 확인
                if response.status_code == 200:
                    return response.text

                self.logger.warning(f"Attempt {attempt + 1}: Status code {response.status_code}")

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error (Attempt {attempt + 1}): {e}")

        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    def extract_specifications(self, html_content):
        """
        HTML에서 사양 정보 추출
        다중 전략 사용
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        specifications = {}

        # 전략 1: 테이블 및 정의 목록 찾기
        tables = soup.find_all(['table', 'dl'], class_=['detail_info', 'specifications'])
        for table in tables:
            rows = table.find_all(['tr', 'dt', 'dd'])
            for row in rows:
                try:
                    key_el = row.find(['th', 'dt'])
                    value_el = row.find(['td', 'dd'])

                    if key_el and value_el:
                        key = key_el.get_text(strip=True)
                        value = value_el.get_text(strip=True)
                        specifications[key] = value
                except Exception as e:
                    self.logger.warning(f"Row parsing error: {e}")

        # 전략 2: 텍스트 기반 사양 추출
        if not specifications:
            text_elements = soup.find_all(text=re.compile(r'\s*:.+'))
            for el in text_elements:
                parts = el.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value and len(value) < 100:  # 너무 긴 값은 제외
                        specifications[key] = value

        return specifications

    def process_product_list(self, input_file, output_file, max_workers=10):
        """
        제품 목록 처리 및 상세 정보 크롤링
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        self.logger.info(f"Processing {len(products)} products...")

        products_copy = products.copy()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.fetch_and_process_product, product): index
                for index, product in enumerate(products_copy)
                if product.get('detail_url')
            }

            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    specs = future.result()
                    if specs:
                        products_copy[index]['specifications'] = specs
                        products_copy[index]['already_crawled'] = True

                        if index % 100 == 0:
                            self.logger.info(f"Processed {index} products...")
                except Exception as e:
                    self.logger.error(f"Error processing product at index {index}: {e}")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products_copy, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Completed processing. Results saved to {output_file}")

    def fetch_and_process_product(self, product):
        """
        개별 제품의 상세 페이지 가져오기 및 처리
        """
        detail_url = product.get('detail_url')
        if not detail_url:
            return None

        html_content = self.fetch_page(detail_url)
        if not html_content:
            return None

        specifications = self.extract_specifications(html_content)
        return specifications

    def main(self):
        input_dir = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/'
        output_dir = '/Users/oypnus/Project/rag-enterprise/data/onehago/full_crawl_clean/'

        import os
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(input_dir):
            if filename.startswith('category_') and filename.endswith('.json'):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, f'processed_{filename}')

                self.logger.info(f"Processing {filename}...")
                self.process_product_list(input_path, output_path)

if __name__ == '__main__':
    crawler = OnehavoAdvancedCrawler()
    crawler.main()