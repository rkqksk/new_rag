#!/usr/bin/env python3
"""
🚀 PLASTICNET MULTI-STRATEGY CRAWLER
Complete refactoring to handle:
1. TABLE-based HTML structure (not divs)
2. Multiple pages with pagination
3. Different content types per category
4. Category-specific extraction strategies

Strategy Selection:
- Category 1,2,3,4: Product materials (title+table specs approach)
- Category 5,6,7,8: Webzine articles (title+full content approach)
"""

import json
import time
import logging
import sys
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup
from collections import defaultdict

BASE_URL = "https://plasticnet.kr"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Multi-strategy output files
KNOWLEDGE_FILE = OUTPUT_DIR / "plastic_knowledge_multistrategy.jsonl"
INDEX_FILE = OUTPUT_DIR / "multistrategy_index.json"
CRAWLED_URLS_FILE = OUTPUT_DIR / "multistrategy_crawled_urls.json"
PROGRESS_FILE = OUTPUT_DIR / "multistrategy_progress.json"

log_file = LOG_DIR / f"plasticnet_multistrategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6075",
        "type": "product",
        "strategy": "material_specs"
    },
    "2": {
        "name": "파이렉/PFA 재료",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6074",
        "type": "product",
        "strategy": "material_specs"
    },
    "3": {
        "name": "플라스틱 가이드",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6076",
        "type": "product",
        "strategy": "material_specs"
    },
    "4": {
        "name": "폴리에틸렌 이더",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6077",
        "type": "product",
        "strategy": "material_specs"
    },
    "5": {
        "name": "Webzine #1",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board.php?mart_id=mbwshop&bbs_no=3",
        "type": "article",
        "strategy": "webzine_article"
    },
    "6": {
        "name": "Webzine #2",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board2.php?mart_id=mbwshop&bbs_no=2",
        "type": "article",
        "strategy": "webzine_article"
    },
    "7": {
        "name": "Webzine #3",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board3.php?mart_id=mbwshop&bbs_no=1",
        "type": "article",
        "strategy": "webzine_article"
    },
    "8": {
        "name": "Webzine #4",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board10.php?mart_id=mbwshop&bbs_no=16",
        "type": "article",
        "strategy": "webzine_article"
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
        logger.warning(f"⚠️ Fetch error: {str(e)[:100]}")
        return None

def extract_pagination_urls(html, base_url, current_page=1):
    """Extract next page URLs from pagination"""
    soup = BeautifulSoup(html, 'html.parser')
    page_urls = []

    # Find all links
    for link in soup.find_all('a'):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for page numbers
        if text.isdigit():
            page_num = int(text)
            if page_num > current_page:
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                page_urls.append({
                    'url': href,
                    'page': page_num
                })

    # Return sorted by page number, limit to next 5 pages
    page_urls = sorted(page_urls, key=lambda x: x['page'])
    return [p['url'] for p in page_urls[:5]]

def extract_article_links_from_tables(html, base_url):
    """Extract article/product links from TABLE structure"""
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    # Find all tables
    for table in soup.find_all('table'):
        for cell in table.find_all(['td', 'th']):
            for link in cell.find_all('a'):
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Look for article links
                if ('webzine_board_read.php' in href or 'board_view_info1.php' in href) and text:
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)

                    links.append({
                        'url': href,
                        'title': text
                    })

    # Deduplicate
    unique_links = []
    seen_urls = set()
    for link in links:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_links.append(link)

    return unique_links

def extract_material_specs(html):
    """Extract material specifications from product page (strategy: material_specs)"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unnecessary elements
        for tag in soup.find_all(['script', 'style', 'noscript']):
            tag.decompose()

        # Extract title - usually first significant text or from h1/h2
        title = None
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            title_text = heading.get_text(strip=True)
            if len(title_text) > 3:
                title = title_text
                break

        # If no heading found, get from first table cell
        if not title:
            for table in soup.find_all('table'):
                first_cell = table.find('td') or table.find('th')
                if first_cell:
                    title = first_cell.get_text(strip=True)
                    if len(title) > 3:
                        break

        if not title or len(title.strip()) < 2:
            return None

        # Extract content - find main content area or all tables
        content_parts = []

        # Get text from all tables (contains specs)
        for table in soup.find_all('table'):
            table_text = table.get_text(separator='\n', strip=True)
            if table_text and len(table_text) > 50:
                content_parts.append(table_text)

        # Get remaining text (after tables)
        all_text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]

        # Remove footer/contact info
        final_lines = []
        for line in lines:
            if any(marker in line for marker in ['회사소개', '이용약관', '사업자번호', '통신판매', 'Copyright']):
                break
            final_lines.append(line)

        content = '\n'.join(final_lines[-200:])  # Last 200 lines of content

        if len(content.strip()) < 50:
            return None

        return {
            'title': title,
            'content': content,
            'type': 'material_specs'
        }

    except Exception as e:
        logger.error(f"Material specs extraction error: {str(e)[:100]}")
        return None

def extract_webzine_article(html):
    """Extract webzine article content (strategy: webzine_article)"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unnecessary elements
        for tag in soup.find_all(['script', 'style', 'noscript']):
            tag.decompose()

        # Remove navigation/footer
        for selector in ['footer', 'aside', 'nav', '[class*=\"contact\"]', '[class*=\"footer\"]', '[class*=\"nav\"]']:
            for element in soup.select(selector):
                element.decompose()

        # Extract title
        title = None
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            title_text = heading.get_text(strip=True)
            if len(title_text) > 3 and len(title_text) < 100:
                title = title_text
                break

        # If no heading, search in all text
        if not title:
            all_text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            for line in lines[:20]:  # First 20 lines
                if len(line) > 5 and len(line) < 100 and not any(skip in line for skip in ['HOME', '플라스틱', 'TM']):
                    title = line
                    break

        if not title or len(title.strip()) < 2:
            return None

        # Extract content - get all text
        all_text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 2]

        # Remove title from lines if present
        content_lines = []
        skip_until_content = True
        for line in lines:
            if skip_until_content and (title in line or title.split()[0] in line):
                skip_until_content = False
                continue

            # Stop at footer markers
            if any(marker in line for marker in ['회사소개', '이용약관', '사업자번호', '통신판매', 'Copyright', '상단']):
                break

            if not skip_until_content:
                content_lines.append(line)

        content = '\n'.join(content_lines)

        if len(content.strip()) < 30:
            return None

        return {
            'title': title,
            'content': content,
            'type': 'webzine_article'
        }

    except Exception as e:
        logger.error(f"Webzine extraction error: {str(e)[:100]}")
        return None

def load_crawled_urls():
    if CRAWLED_URLS_FILE.exists():
        with open(CRAWLED_URLS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_crawled_urls(crawled_set):
    with open(CRAWLED_URLS_FILE, 'w') as f:
        json.dump(list(crawled_set), f, ensure_ascii=False, indent=2)

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def update_index():
    """Build index from JSONL"""
    index = {
        'total_articles': 0,
        'by_strategy': defaultdict(int),
        'crawled_at': datetime.now().isoformat(),
        'categories': {}
    }

    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        index['total_articles'] += 1
                        strategy = item.get('type', 'unknown')
                        index['by_strategy'][strategy] += 1
                    except:
                        continue

    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index

def crawl_category_multipage(category_key, max_pages=3):
    """Crawl category with pagination support"""
    if category_key not in PLASTICNET_CATEGORIES:
        logger.error(f"Invalid category: {category_key}")
        return

    category = PLASTICNET_CATEGORIES[category_key]
    category_url = category['url']
    category_name = category['name']
    strategy = category['strategy']

    logger.info(f"\n{'='*80}")
    logger.info(f"📂 CRAWLING: {category_name} (Strategy: {strategy})")
    logger.info(f"{'='*80}\n")

    crawled_urls = load_crawled_urls()
    progress = load_progress()
    total_new_articles = 0

    # Crawl multiple pages
    current_url = category_url
    pages_crawled = 0

    with open(KNOWLEDGE_FILE, 'a') as out_f:
        while pages_crawled < max_pages and current_url:
            logger.info(f"📄 Page {pages_crawled + 1}/{max_pages}: Fetching...")
            html = fetch_page_requests(current_url)
            if not html:
                logger.error(f"Failed to fetch page {pages_crawled + 1}")
                break

            # Extract article links from this page
            article_links = extract_article_links_from_tables(html, current_url)
            logger.info(f"   Found {len(article_links)} articles on this page")

            # Crawl articles
            for idx, link_info in enumerate(article_links, 1):
                article_url = link_info['url']
                article_title = link_info['title']

                if article_url in crawled_urls:
                    logger.info(f"   ⏭️ [{idx}/{len(article_links)}] Already crawled: {article_title[:40]}")
                    continue

                logger.info(f"   📄 [{idx}/{len(article_links)}] Extracting: {article_title[:40]}")
                article_html = fetch_page_requests(article_url)
                if not article_html:
                    logger.warning(f"      Failed to fetch article")
                    continue

                # Use appropriate extraction strategy
                if strategy == 'material_specs':
                    result = extract_material_specs(article_html)
                elif strategy == 'webzine_article':
                    result = extract_webzine_article(article_html)
                else:
                    result = None

                if result:
                    out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    out_f.flush()
                    total_new_articles += 1
                    logger.info(f"      ✅ Saved: {result['title'][:50]}")

                crawled_urls.add(article_url)
                time.sleep(0.5)  # Rate limiting

            # Save progress
            save_crawled_urls(crawled_urls)
            pages_crawled += 1

            # Get next page URL
            next_pages = extract_pagination_urls(html, current_url, pages_crawled)
            if next_pages:
                current_url = next_pages[0]
            else:
                break

    # Update progress and index
    progress[category_key] = {
        'name': category_name,
        'articles': total_new_articles,
        'completed_at': datetime.now().isoformat()
    }
    save_progress(progress)
    index = update_index()

    logger.info(f"\n✅ COMPLETE:")
    logger.info(f"   📚 New articles: {total_new_articles}")
    logger.info(f"   📊 Total in database: {index['total_articles']}")
    logger.info(f"   🎯 By strategy: {dict(index['by_strategy'])}\n")

def main():
    """Run multi-strategy crawler"""
    if len(sys.argv) < 2:
        print("Usage: python3 crawl_plasticnet_multistrategy.py [category_number|all] [max_pages]")
        print("\nCategories:")
        for key, cat in PLASTICNET_CATEGORIES.items():
            print(f"  {key}: {cat['name']} ({cat['strategy']})")
        print("\nExamples:")
        print("  python3 crawl_plasticnet_multistrategy.py 1 2    # Category 1, up to 2 pages")
        print("  python3 crawl_plasticnet_multistrategy.py all 3  # All categories, up to 3 pages each")
        sys.exit(1)

    choice = sys.argv[1].lower()
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    logger.info(f"\n🚀 PLASTICNET MULTI-STRATEGY CRAWLER")
    logger.info(f"Max pages per category: {max_pages}\n")

    if choice == "all":
        for cat_key in sorted(PLASTICNET_CATEGORIES.keys()):
            crawl_category_multipage(cat_key, max_pages)
    elif choice in PLASTICNET_CATEGORIES:
        crawl_category_multipage(choice, max_pages)
    else:
        print(f"Invalid category: {choice}")
        sys.exit(1)

if __name__ == "__main__":
    main()
