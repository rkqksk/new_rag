#!/usr/bin/env python3
"""
🚀 PLASTICNET SIMPLE CRAWLER (User's Requested Format)

Extract: Simple titles + detailed contents
Format: {'title': '피마자유', 'content': '비식용 작물인 피마자(아주까리)의 종자로부터...'}

Usage: python3 crawl_plasticnet_simple.py [category_number]

Examples:
  python3 crawl_plasticnet_simple.py 1    # Crawl PP Materials
  python3 crawl_plasticnet_simple.py 5    # Crawl Webzine #1
  python3 crawl_plasticnet_simple.py all  # Crawl all categories
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

BASE_URL = "https://plasticnet.kr"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Simplified output format
SIMPLE_KNOWLEDGE_FILE = OUTPUT_DIR / "plastic_simple_knowledge.jsonl"
SIMPLE_INDEX_FILE = OUTPUT_DIR / "simple_index.json"
CRAWLED_URLS_FILE = OUTPUT_DIR / "simple_crawled_urls.json"

log_file = LOG_DIR / f"plasticnet_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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


def extract_article_links(html, base_url):
    """Extract article links from listing page"""
    article_links = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Look for webzine_board_read or board_view links
            if 'webzine_board_read.php' in href or 'board_view_info1.php' in href:
                # Handle relative URLs
                if not href.startswith('http'):
                    # For webzine links that are relative (like "webzine_board_read.php?...")
                    if href.startswith('webzine_board_read.php') or href.startswith('board_view_info1.php'):
                        # These are relative to the directory containing the current page
                        full_url = urljoin(base_url, href)
                    else:
                        full_url = urljoin(BASE_URL, href)
                else:
                    full_url = href

                if full_url not in article_links:
                    article_links.append(full_url)
    except Exception as e:
        logger.warning(f"Article extraction error: {str(e)[:100]}")
    return article_links


def extract_title_and_content(html):
    """Extract simple title and detailed content"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unnecessary elements
        for tag in soup.find_all(['script', 'style', 'noscript']):
            tag.decompose()

        # Remove contact/footer info and navigation
        for selector in ['footer', 'aside', '.contact', '.footer', '.tel', '.email', '.address',
                        '[class*="contact"]', '[class*="footer"]', '[class*="info"]', '[class*="nav"]']:
            for element in soup.select(selector):
                element.decompose()

        # Get all text lines from the page
        all_text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]

        # Find "글제목" (article title label) and extract the next line as title
        article_title = None
        content_start_idx = -1

        for i, line in enumerate(lines):
            if '글제목' in line or 'title' in line.lower():
                # Title should be in next non-empty line
                if i + 1 < len(lines):
                    article_title = lines[i + 1]
                    content_start_idx = i + 2
                break

        # If no title found with labels, try to find it from first significant text
        if not article_title:
            # Skip common header elements
            for i, line in enumerate(lines):
                if len(line) > 3 and not any(skip in line for skip in ['플라스틱', '용어', 'HOME', '기술자료']):
                    article_title = line
                    content_start_idx = i + 1
                    break

        if not article_title or len(article_title.strip()) < 2:
            return None

        # Extract content from content_start_idx onwards, until we hit footer markers
        content_lines = []
        for i in range(content_start_idx, len(lines)):
            line = lines[i]
            # Stop at footer markers
            if any(marker in line for marker in ['회사소개', '이용약관', '사업자번호', '통신판매', 'Copyright', 'Tel', 'Email']):
                break
            if line.strip():
                content_lines.append(line)

        text_content = '\n'.join(content_lines)

        if len(text_content.strip()) < 50:
            return None

        # Return simple format: title + content
        return {
            'title': article_title,
            'content': text_content
        }

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


def update_simple_index():
    """Build simple index from JSONL"""
    index = {
        'total_articles': 0,
        'crawled_at': datetime.now().isoformat(),
        'categories': {}
    }

    if SIMPLE_KNOWLEDGE_FILE.exists():
        with open(SIMPLE_KNOWLEDGE_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        index['total_articles'] += 1
                    except:
                        continue

    with open(SIMPLE_INDEX_FILE, 'w') as f:
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
    total_articles = 0

    # Fetch category page
    html = fetch_page_requests(category_url)
    if not html:
        logger.error(f"Failed to fetch: {category_url}")
        return

    # Extract articles from first page
    article_links = extract_article_links(html, category_url)
    logger.info(f"📄 Found {len(article_links)} articles on first page\n")

    # Crawl articles
    with open(SIMPLE_KNOWLEDGE_FILE, 'a') as out_f:
        for idx, article_url in enumerate(article_links, 1):
            if article_url in crawled_urls:
                logger.info(f"⏭️  [{idx}/{len(article_links)}] Already crawled")
                continue

            logger.info(f"📄 [{idx}/{len(article_links)}] Fetching...")
            article_html = fetch_page_requests(article_url)
            if not article_html:
                continue

            result = extract_title_and_content(article_html)
            if result:
                # Write in simple format: title + content
                out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                out_f.flush()
                total_articles += 1
                logger.info(f"   ✅ Extracted: {result['title'][:50]}")

            crawled_urls.add(article_url)
            time.sleep(0.5)

    save_crawled_urls(crawled_urls)
    index = update_simple_index()

    logger.info(f"\n✅ COMPLETE:")
    logger.info(f"   📚 Articles extracted: {total_articles}")
    logger.info(f"   📊 Total in database: {index['total_articles']}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 crawl_plasticnet_simple.py [category_number|all]")
        print("\nCategories:")
        for key, cat in PLASTICNET_CATEGORIES.items():
            print(f"  {key}: {cat['name']}")
        print("\nExamples:")
        print("  python3 crawl_plasticnet_simple.py 1    # Crawl PP Materials")
        print("  python3 crawl_plasticnet_simple.py 5    # Crawl Webzine #1")
        print("  python3 crawl_plasticnet_simple.py all  # Crawl all")
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
