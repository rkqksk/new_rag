#!/usr/bin/env python3
"""
🚀 PLASTICS.KR UNIFIED CRAWLER
Modern news portal crawler with multi-page pagination support
Strategy: Single unified extraction (all categories identical structure)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL = "https://www.plastics.kr"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plastics_kr")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Category configuration
CATEGORIES = {
    "S1N1": {"name": "Latest News (최신기사)", "max_pages": 50, "priority": 1},
    "S1N2": {"name": "Business News (뉴스)", "max_pages": 2, "priority": 2},
    "S1N3": {"name": "Features (특집)", "max_pages": 2, "priority": 3},
    "S1N4": {"name": "Media (미디어)", "max_pages": 5, "priority": 4},
}

# Output files
ARTICLES_FILE = OUTPUT_DIR / "plastic_news_articles.jsonl"
CRAWLED_URLS_FILE = OUTPUT_DIR / "crawled_urls.json"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"
INDEX_FILE = OUTPUT_DIR / "index.json"
LOG_DIR = OUTPUT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"plastics_kr_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting (respectful crawling)
DELAY_PER_ARTICLE = 0.3  # seconds
DELAY_PER_PAGE = 0.5     # seconds

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def fetch_page(url, retries=3):
    """Fetch page with proper headers and error handling"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.encoding = 'utf-8'  # Standard encoding

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Status {response.status_code}: {url}")
                time.sleep(DELAY_PER_PAGE)
                continue

        except requests.RequestException as e:
            logger.error(f"Fetch error (attempt {attempt+1}/{retries}): {str(e)[:100]} - {url}")
            if attempt < retries - 1:
                time.sleep(DELAY_PER_PAGE)
            continue

    return None


def load_crawled_urls():
    """Load set of already crawled URLs to prevent duplicates"""
    if CRAWLED_URLS_FILE.exists():
        try:
            with open(CRAWLED_URLS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('urls', []))
        except:
            return set()
    return set()


def save_crawled_urls(urls):
    """Save crawled URLs to file"""
    with open(CRAWLED_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'urls': list(urls), 'timestamp': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)


def load_progress():
    """Load progress state for resumable crawling"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_progress(progress):
    """Save progress state"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def save_article(article):
    """Append article to JSONL file"""
    with open(ARTICLES_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(article, ensure_ascii=False) + '\n')


def update_index(category, pages_crawled, articles_found):
    """Update statistics index"""
    index = {}
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except:
            pass

    if category not in index:
        index[category] = {}

    index[category]['pages_crawled'] = pages_crawled
    index[category]['articles_found'] = articles_found
    index[category]['last_updated'] = datetime.now().isoformat()

    # Calculate totals (filter out 'categories' key if it exists)
    categories_data = index.get('categories', index)
    if isinstance(categories_data, dict):
        total_articles = sum(
            cat.get('articles_found', 0)
            for cat in categories_data.values()
            if isinstance(cat, dict)
        )
        total_pages = sum(
            cat.get('pages_crawled', 0)
            for cat in categories_data.values()
            if isinstance(cat, dict)
        )
    else:
        total_articles = index.get('total_articles', 0)
        total_pages = index.get('total_pages', 0)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'categories': index,
            'total_articles': total_articles,
            'total_pages': total_pages,
            'timestamp': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    return total_articles


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def extract_article_links(html, category_code, base_url):
    """Extract article links from listing page using DIV.item selector"""
    soup = BeautifulSoup(html, 'html.parser')
    article_links = []

    # Find all article items via class selector (modern DIV-based structure)
    # Each <div class="item"> contains 2 links:
    # 1. Category link (<a class="auto-section">)
    # 2. Article link (<a class="auto-titles"> with articleView.html)
    for item in soup.find_all('div', class_='item'):
        try:
            # Extract ONLY the article title link (auto-titles class)
            # NOT the category link (auto-section class)
            link_elem = item.find('a', class_='auto-titles', href=True)
            if link_elem:
                href = link_elem.get('href', '')
                text = link_elem.get_text(strip=True)

                # Verify it's an article detail page (articleView pattern)
                if 'articleView' not in href:
                    logger.debug(f"Skipping non-article link: {href}")
                    continue

                # Convert relative URLs to absolute
                if href:
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue

                    article_links.append({
                        'url': full_url,
                        'title': text[:200] if text else 'Untitled',
                        'pattern': 'news_article'
                    })
        except Exception as e:
            logger.debug(f"Error extracting link: {str(e)}")
            continue

    logger.info(f"  ├─ Found {len(article_links)} article links on page")
    return article_links


def extract_pagination_url(html, category_code, current_page, max_pages):
    """Extract next page URL via pagination links"""
    if current_page >= max_pages:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    next_page = current_page + 1

    # Look for pagination links with page parameter
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Match page=X pattern
        if f'page={next_page}' in href and f'sc_section_code={category_code}' in href:
            logger.debug(f"  ├─ Next page found: page={next_page}")
            return href if next_page <= max_pages else None

    logger.debug(f"  ├─ No next page link found (checked for page={next_page})")
    return None


def extract_article_content(html, article_url):
    """Extract article content from detail page"""
    soup = BeautifulSoup(html, 'html.parser')

    # Extract title (multiple fallback patterns)
    title = None
    if soup.find('h1', class_='title'):
        title = soup.find('h1', class_='title').get_text(strip=True)
    elif soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)
    elif soup.find('h2'):
        title = soup.find('h2').get_text(strip=True)

    # Extract content from article/content div
    content_div = soup.find('div', class_='content')
    if not content_div:
        content_div = soup.find('article')
    if not content_div:
        # Fallback: get main content area
        for div in soup.find_all('div', class_=['article-content', 'body', 'text', 'post-content']):
            content_div = div
            break

    content = ''
    if content_div:
        # Get text while preserving paragraph structure
        content = content_div.get_text(separator='\n', strip=True)

    # Extract metadata
    date_elem = soup.find('span', class_='date')
    author_elem = soup.find('span', class_='author')

    date_text = date_elem.get_text(strip=True) if date_elem else None
    author_text = author_elem.get_text(strip=True) if author_elem else None

    result = {
        'title': title or 'Untitled',
        'content': content or '[Content not extractable]',
        'date': date_text,
        'author': author_text,
        'url': article_url,
        'type': 'news_article'
    }

    return result


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CRAWLING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def crawl_category(category_code, max_pages=None, resume=False):
    """
    Main crawling loop for a category
    Handles pagination, URL deduplication, and progress tracking
    """
    category_info = CATEGORIES.get(category_code)
    if not category_code in CATEGORIES:
        logger.error(f"Unknown category: {category_code}")
        return 0

    if max_pages is None:
        max_pages = category_info['max_pages']

    logger.info(f"\n{'='*80}")
    logger.info(f"📰 Crawling: {category_info['name']} ({category_code})")
    logger.info(f"{'='*80}")
    logger.info(f"Max pages: {max_pages}, Delay per article: {DELAY_PER_ARTICLE}s")

    # Load state
    crawled_urls = load_crawled_urls()
    progress = load_progress()
    category_progress = progress.get(category_code, {'pages_crawled': 0, 'articles_count': 0})

    # Determine starting page
    start_page = 1
    if resume and category_progress.get('last_page'):
        start_page = category_progress['last_page'] + 1
        logger.info(f"📍 Resuming from page {start_page}")

    # Build initial URL
    current_url = f"{BASE_URL}/news/articleList.html?sc_section_code={category_code}&view_type=sm&page={start_page}"
    pages_crawled = start_page - 1
    articles_count = category_progress.get('articles_count', 0)

    # Pagination loop
    while pages_crawled < max_pages:
        logger.info(f"\n📄 Page {pages_crawled + 1}/{max_pages}")
        logger.info(f"  ├─ URL: {current_url[:100]}...")

        # Fetch listing page
        time.sleep(DELAY_PER_PAGE)
        html = fetch_page(current_url)

        if not html:
            logger.warning(f"  └─ Failed to fetch page {pages_crawled + 1}")
            break

        # Extract article links
        article_links = extract_article_links(html, category_code, BASE_URL)

        if not article_links:
            logger.info(f"  ├─ No article links found, stopping")
            break

        # Process each article
        for idx, article_link in enumerate(article_links, 1):
            article_url = article_link['url']

            # Skip if already crawled
            if article_url in crawled_urls:
                logger.debug(f"  │  └─ [{idx}/{len(article_links)}] ⏭️ Skipped (already crawled)")
                continue

            logger.debug(f"  │  └─ [{idx}/{len(article_links)}] Processing: {article_link['title'][:60]}...")

            # Fetch article
            time.sleep(DELAY_PER_ARTICLE)
            article_html = fetch_page(article_url)

            if article_html:
                # Extract content
                article_content = extract_article_content(article_html, article_url)
                article_content['category'] = category_code

                # Save to JSONL
                save_article(article_content)
                crawled_urls.add(article_url)
                articles_count += 1
                logger.debug(f"  │    ✅ Saved")
            else:
                logger.debug(f"  │    ❌ Failed to fetch")

        # Save progress
        pages_crawled += 1
        progress[category_code] = {
            'pages_crawled': pages_crawled,
            'articles_count': articles_count,
            'last_page': pages_crawled,
            'last_updated': datetime.now().isoformat()
        }
        save_progress(progress)
        save_crawled_urls(crawled_urls)

        # Find next page
        next_url = extract_pagination_url(html, category_code, pages_crawled, max_pages)
        if next_url:
            current_url = next_url if next_url.startswith('http') else urljoin(BASE_URL, next_url)
        else:
            logger.info(f"  └─ No next page link found, stopping")
            break

    # Update index
    total_articles = update_index(category_code, pages_crawled, articles_count)

    logger.info(f"\n✅ Category complete: {pages_crawled} pages, {articles_count} articles")
    logger.info(f"📊 Total articles extracted so far: {total_articles}")

    return articles_count


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main orchestration function"""
    logger.info("\n" + "="*80)
    logger.info("🚀 PLASTICS.KR UNIFIED CRAWLER - STARTING")
    logger.info("="*80)
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Start time: {datetime.now().isoformat()}")

    # Parse arguments
    resume = '--resume' in sys.argv
    specific_categories = [arg for arg in sys.argv[1:] if arg.startswith('S1N')]

    if not specific_categories:
        if 'all' in sys.argv or len(sys.argv) == 1:
            # Crawl all categories in priority order
            specific_categories = sorted(CATEGORIES.keys(), key=lambda x: CATEGORIES[x]['priority'])
        else:
            logger.error("Usage: python crawl_plastics_kr.py [S1N1|S1N2|S1N3|S1N4|all] [--resume]")
            sys.exit(1)

    logger.info(f"Categories to crawl: {', '.join(specific_categories)}")
    logger.info(f"Resume mode: {resume}")

    # Crawl categories
    total_articles = 0
    for category_code in specific_categories:
        if category_code in CATEGORIES:
            count = crawl_category(category_code, resume=resume)
            total_articles += count
        else:
            logger.warning(f"Unknown category: {category_code}")

    # Final summary
    logger.info("\n" + "="*80)
    logger.info("📊 CRAWLING COMPLETE - SUMMARY")
    logger.info("="*80)
    logger.info(f"Total articles extracted: {total_articles}")
    logger.info(f"Output file: {ARTICLES_FILE}")
    logger.info(f"File size: {ARTICLES_FILE.stat().st_size / 1024 / 1024:.2f} MB" if ARTICLES_FILE.exists() else "No file")

    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        logger.info(f"Lines in file: {line_count}")

    logger.info(f"End time: {datetime.now().isoformat()}")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
