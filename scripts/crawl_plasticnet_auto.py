#!/usr/bin/env python3
"""
🚀 PLASTICNET AUTO CRAWLER (Non-Interactive)

Usage: python3 crawl_plasticnet_auto.py [category_number]

Examples:
  python3 crawl_plasticnet_auto.py 1    # Crawl PP Materials
  python3 crawl_plasticnet_auto.py 5    # Crawl Webzine #1
  python3 crawl_plasticnet_auto.py all  # Crawl all categories
"""

import json
import time
import logging
import sys
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

BASE_URL = "https://plasticnet.kr"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = OUTPUT_DIR / "plastic_technical_knowledge.jsonl"
INDEX_FILE = OUTPUT_DIR / "knowledge_index.json"
PROGRESS_FILE = OUTPUT_DIR / "crawl_progress.json"
CRAWLED_URLS_FILE = OUTPUT_DIR / "crawled_urls.json"

log_file = LOG_DIR / f"plasticnet_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PLASTICNET_CATEGORIES = {
    "1": {
        "name": "폴리프로필렌/PP 재료",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6075&ctitle=%B9%CC%B4%CF%B5%A5%C0%CC%C5%CD%B7%EB"
    },
    "2": {
        "name": "파이렉/PFA 재료",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6074&ctitle=%C6%E4%C0%CE%C6%AE/%C4%DA%C6%C3"
    },
    "3": {
        "name": "플라스틱 가이드",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6076&ctitle=%C7%C3%B6%F3%BD%BA%C6%BD%20%B0%A1%C0%CC%B5%E5"
    },
    "4": {
        "name": "폴리에틸렌 이더",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6077&ctitle=%C6%FA%B8%AE%B8%D3%B3%EB%C6%AE"
    },
    "5": {
        "name": "Webzine #1",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board.php?mart_id=mbwshop&bbs_no=3"
    },
    "6": {
        "name": "Webzine #2",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board2.php?mart_id=mbwshop&bbs_no=2"
    },
    "7": {
        "name": "Webzine #3",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board3.php?mart_id=mbwshop&bbs_no=1"
    },
    "8": {
        "name": "Webzine #4",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board10.php?mart_id=mbwshop&bbs_no=16"
    }
}

PLASTIC_MATERIALS = {
    'PET': ['polyethylene terephthalate', 'polyester', '폴리에스터', 'PET'],
    'HDPE': ['high density polyethylene', '고밀도폴리에틸렌', 'HDPE'],
    'LDPE': ['low density polyethylene', '저밀도폴리에틸렌', 'LDPE'],
    'PP': ['polypropylene', 'polyprop', '폴리프로필렌', 'PP'],
    'PVC': ['polyvinyl chloride', '염화폴리비닐', 'PVC'],
    'PS': ['polystyrene', '폴리스타이렌', 'PS'],
    'ABS': ['acrylonitrile butadiene styrene', 'ABS'],
    'PC': ['polycarbonate', '폴리카보네이트', 'PC'],
    'PA': ['polyamide', 'nylon', '나일론', 'PA'],
    'TPE': ['thermoplastic elastomer', '열가소성탄성체', 'TPE'],
    'EVA': ['ethylene vinyl acetate', 'EVA'],
}

TESTING_STANDARDS = {
    'ASTM': 'American Society for Testing and Materials',
    'ISO': 'International Organization for Standardization',
    'JIS': 'Japanese Industrial Standard',
    'DIN': 'Deutsches Institut für Normung',
    'BS': 'British Standard',
    'KS': 'Korean Standard',
}

MATERIAL_PROPERTIES = [
    'tensile strength', 'elongation', 'hardness', 'density', 'melting point',
    'impact strength', 'chemical resistance', 'uv resistance',
    '강도', '탄성', '경도', '밀도', '용융점', '내열성', '내화학성', '인장강도'
]

def fetch_page_requests(url):
    """Fetch URL with proper encoding"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Charset': 'utf-8,iso-8859-1;q=0.7,*;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url, timeout=10, headers=headers)

        if response.encoding is None or 'utf' not in response.encoding.lower():
            try:
                response.encoding = 'euc-kr'
                test = response.text
            except:
                try:
                    response.encoding = 'cp949'
                    test = response.text
                except:
                    response.encoding = 'utf-8'

        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        logger.warning(f"⚠️  Fetch error: {str(e)[:100]}")
        return None

def extract_pagination_links(html, category_url):
    """Extract pagination links"""
    pagination_links = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'page=' in href:
                full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
                if full_url not in pagination_links and full_url != category_url:
                    pagination_links.append(full_url)
    except Exception as e:
        logger.warning(f"Pagination error: {str(e)[:100]}")
    return pagination_links

def extract_article_links(html):
    """Extract article links"""
    article_links = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'board_view_info1.php' in href or 'webzine_board_read.php' in href or 'view=' in href:
                if not href.startswith('http'):
                    if '/found/market/mbwshop/' not in href:
                        href = f'/found/market/mbwshop/{href.lstrip("/")}'
                    full_url = urljoin(BASE_URL, href)
                else:
                    full_url = href
                if full_url not in article_links:
                    article_links.append(full_url)
    except Exception as e:
        logger.warning(f"Article extraction error: {str(e)[:100]}")
    return article_links

def extract_material_knowledge(html, url):
    """Extract knowledge from article (title + main content only, excluding unnecessary info)"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unnecessary elements
        for tag in soup.find_all(['script', 'style', 'noscript']):
            tag.decompose()

        # Remove contact/footer info
        for selector in ['footer', 'aside', '.contact', '.footer', '.tel', '.email', '.address',
                        '[class*="contact"]', '[class*="footer"]', '[class*="info"]']:
            for element in soup.select(selector):
                element.decompose()

        # Get title
        title = soup.find('h1') or soup.find('h2')
        article_title = title.get_text(strip=True) if title else "Unknown"

        # Find main content area
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'body', 'main', 'article']) if x else False)
        if not main_content:
            main_content = soup.find('article') or soup

        # Extract text with title first
        text_content = f"{article_title}\n\n"
        text_content += main_content.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        text_content = '\n'.join(line.strip() for line in text_content.split('\n') if line.strip())

        if len(text_content) < 100:
            return None

        materials_found = {}
        for material_code, aliases in PLASTIC_MATERIALS.items():
            for alias in aliases:
                if alias.lower() in text_content.lower():
                    materials_found[material_code] = alias
                    break

        standards_found = {}
        for standard_code in TESTING_STANDARDS.keys():
            if standard_code in text_content:
                standards_found[standard_code] = TESTING_STANDARDS[standard_code]

        properties_found = []
        for prop in MATERIAL_PROPERTIES:
            if prop.lower() in text_content.lower() and prop not in properties_found:
                properties_found.append(prop)

        knowledge_entry = {
            'article_title': article_title,
            'url': url,
            'crawled_at': datetime.now().isoformat(),
            'content_preview': text_content[:500],
            'full_content': text_content,  # Include full content for RAG
            'materials_mentioned': list(materials_found.keys()),
            'testing_standards': standards_found,
            'properties': properties_found,
            'word_count': len(text_content.split()),
        }

        logger.info(f"✅ Extracted: {article_title[:60]}")
        return knowledge_entry

    except Exception as e:
        logger.error(f"Extraction error: {str(e)[:100]}")
        return None

def load_crawled_urls():
    if CRAWLED_URLS_FILE.exists():
        with open(CRAWLED_URLS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_crawled_urls(crawled_set):
    with open(CRAWLED_URLS_FILE, 'w') as f:
        json.dump(list(crawled_set), f, ensure_ascii=False, indent=2)

def update_index():
    """Rebuild index from JSONL"""
    index = {
        'total_knowledge_items': 0,
        'materials': {},
        'standards': {},
        'properties': {},
        'crawled_at': datetime.now().isoformat(),
    }

    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        index['total_knowledge_items'] += 1
                        for material in item.get('materials_mentioned', []):
                            index['materials'][material] = index['materials'].get(material, 0) + 1
                        for standard in item.get('testing_standards', {}).keys():
                            index['standards'][standard] = index['standards'].get(standard, 0) + 1
                        for prop in item.get('properties', []):
                            index['properties'][prop] = index['properties'].get(prop, 0) + 1
                    except:
                        continue

    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index

def crawl_category(category_key):
    """Crawl a single category"""
    if category_key not in PLASTICNET_CATEGORIES:
        logger.error(f"Invalid category: {category_key}")
        return

    category = PLASTICNET_CATEGORIES[category_key]
    category_url = category['url']
    category_name = category['name']

    logger.info(f"\n{'='*80}")
    logger.info(f"📂 CRAWLING: {category_name}")
    logger.info(f"{'='*80}\n")

    crawled_urls = load_crawled_urls()
    total_knowledge_items = 0
    articles_processed = 0

    # Fetch category page
    html = fetch_page_requests(category_url)
    if not html:
        logger.error(f"Failed to fetch: {category_url}")
        return

    # Extract pagination
    pagination_links = extract_pagination_links(html, category_url)
    all_urls = [category_url] + pagination_links
    logger.info(f"📄 Found {len(all_urls)} pages to crawl\n")

    # Crawl all pages
    with open(KNOWLEDGE_FILE, 'a') as out_f:
        for page_idx, page_url in enumerate(all_urls, 1):
            if page_url in crawled_urls:
                logger.info(f"⏭️  Page {page_idx} already crawled")
                continue

            logger.info(f"📄 [Page {page_idx}/{len(all_urls)}] Fetching...")
            page_html = fetch_page_requests(page_url)
            if not page_html:
                continue

            # Extract articles
            article_links = extract_article_links(page_html)
            logger.info(f"   Found {len(article_links)} articles")

            # Crawl articles
            for article_url in article_links:
                if article_url in crawled_urls:
                    continue

                article_html = fetch_page_requests(article_url)
                if not article_html:
                    continue

                knowledge = extract_material_knowledge(article_html, article_url)
                if knowledge:
                    out_f.write(json.dumps(knowledge, ensure_ascii=False) + '\n')
                    out_f.flush()
                    total_knowledge_items += 1
                    articles_processed += 1

                crawled_urls.add(article_url)
                time.sleep(0.5)

            crawled_urls.add(page_url)
            time.sleep(1)

    save_crawled_urls(crawled_urls)
    index = update_index()

    logger.info(f"\n✅ COMPLETE:")
    logger.info(f"   📚 Items extracted: {total_knowledge_items}")
    logger.info(f"   📄 Articles processed: {articles_processed}")
    logger.info(f"   📊 Total materials: {len(index['materials'])}")
    logger.info(f"   📋 Total standards: {len(index['standards'])}")
    logger.info(f"   🏷️  Total properties: {len(index['properties'])}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 crawl_plasticnet_auto.py [category_number|all]")
        print("\nCategories:")
        for key, cat in PLASTICNET_CATEGORIES.items():
            print(f"  {key}: {cat['name']}")
        print("\nExamples:")
        print("  python3 crawl_plasticnet_auto.py 1    # Crawl PP Materials")
        print("  python3 crawl_plasticnet_auto.py 5    # Crawl Webzine #1")
        print("  python3 crawl_plasticnet_auto.py all  # Crawl all")
        sys.exit(1)

    choice = sys.argv[1].lower()

    if choice == "all":
        for cat_key in sorted(PLASTICNET_CATEGORIES.keys()):
            crawl_category(cat_key)
    elif choice in PLASTICNET_CATEGORIES:
        crawl_category(choice)
    else:
        print(f"Invalid category: {choice}")
        sys.exit(1)

if __name__ == "__main__":
    main()
