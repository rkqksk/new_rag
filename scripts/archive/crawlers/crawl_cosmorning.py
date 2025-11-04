#!/usr/bin/env python3
"""
Cosmorning.com News Crawler
Crawls articles from https://cosmorning.com/news/article_list_all.html
Extracts: article_id, title, author, date, content, url, thumbnail
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import time

# Setup logging
log_file = Path('/Users/oypnus/Project/rag-enterprise/data/cosmorning/logs') / f'cosmorning_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/cosmorning')
OUTPUT_DIR = BASE_PATH / 'crawled'
PROGRESS_FILE = OUTPUT_DIR / 'progress.json'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
BASE_URL = "https://cosmorning.com/news/article_list_all.html"
ARTICLES_PER_PAGE = 10
WORKERS = 8  # Conservative for news site
REQUEST_DELAY = 1.0  # Seconds between requests (respect server)
CHECKPOINT_INTERVAL = 100  # Save progress every 100 articles

class CosmorningCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.articles = []
        self.failed_articles = []
        self.start_time = datetime.now()

    def get_article_list_page(self, page_num: int = 0) -> List[Dict[str, Any]]:
        """Fetch article list for a specific page"""
        try:
            url = f"{BASE_URL}?page={page_num}"
            logger.info(f"📥 Fetching page {page_num}: {url}")

            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            time.sleep(REQUEST_DELAY)  # Rate limiting

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all article items (li elements with links)
            articles = []
            article_items = soup.find_all('li')

            for item in article_items:
                link = item.find('a', href=re.compile(r'/news/article\.html\?no='))
                if not link:
                    continue

                try:
                    # Extract data
                    href = link.get('href')
                    article_id_match = re.search(r'no=(\d+)', href)
                    if not article_id_match:
                        continue

                    article_id = article_id_match.group(1)

                    # Title
                    title_tag = link.find('h3')
                    title = title_tag.get_text(strip=True) if title_tag else 'N/A'

                    # Author
                    author_span = link.find('span', class_='author')
                    author = author_span.get_text(strip=True) if author_span else 'Unknown'

                    # Date
                    date_span = link.find('span', class_='date')
                    date_str = date_span.get_text(strip=True) if date_span else 'N/A'

                    # Thumbnail
                    img = link.find('img')
                    thumbnail = img.get('src') if img else None
                    if thumbnail and not thumbnail.startswith('http'):
                        thumbnail = f"https://cosmorning.com{thumbnail}"

                    # Excerpt
                    excerpt_p = link.find('p')
                    excerpt = excerpt_p.get_text(strip=True) if excerpt_p else 'N/A'

                    article = {
                        'article_id': article_id,
                        'title': title,
                        'author': author,
                        'date': date_str,
                        'excerpt': excerpt,
                        'article_url': f"https://cosmorning.com/news/article.html?no={article_id}",
                        'thumbnail_url': thumbnail,
                        'page': page_num,
                        'discovered_at': datetime.now().isoformat()
                    }

                    articles.append(article)
                    logger.debug(f"✓ Extracted: [{article_id}] {title[:50]}")

                except Exception as e:
                    logger.warning(f"⚠️  Failed to extract article from item: {e}")
                    continue

            logger.info(f"✅ Page {page_num}: {len(articles)} articles extracted")
            return articles

        except Exception as e:
            logger.error(f"❌ Error fetching page {page_num}: {e}")
            return []

    def extract_article_content(self, article_id: str, article_url: str) -> Dict[str, Any]:
        """Extract full content from article detail page"""
        try:
            logger.debug(f"📄 Fetching article {article_id}...")

            response = self.session.get(article_url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            time.sleep(REQUEST_DELAY)  # Rate limiting

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find article body
            content_div = soup.find('div', class_='article_content')
            content = ""
            if content_div:
                content = content_div.get_text(strip=True)
                # Clean up content (remove extra whitespace)
                content = re.sub(r'\s+', ' ', content)

            return {
                'article_id': article_id,
                'full_content': content,
                'content_length': len(content),
                'fetched_at': datetime.now().isoformat(),
                'success': True
            }

        except Exception as e:
            logger.error(f"❌ Failed to extract content from {article_id}: {e}")
            return {
                'article_id': article_id,
                'full_content': '',
                'content_length': 0,
                'error': str(e),
                'success': False
            }

    def save_progress(self, articles: List[Dict]):
        """Save current progress"""
        progress = {
            'total_articles': len(articles),
            'failed_articles': len(self.failed_articles),
            'last_update': datetime.now().isoformat(),
            'elapsed_time': str(datetime.now() - self.start_time)
        }

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

        # Save articles to JSONL
        output_file = OUTPUT_DIR / 'articles.jsonl'
        with open(output_file, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')

        logger.info(f"💾 Progress saved: {len(articles)} articles")

def main():
    logger.info("="*80)
    logger.info("🚀 COSMORNING NEWS CRAWLER")
    logger.info("="*80)
    logger.info(f"📊 Configuration:")
    logger.info(f"  Base URL: {BASE_URL}")
    logger.info(f"  Articles per page: {ARTICLES_PER_PAGE}")
    logger.info(f"  Workers: {WORKERS}")
    logger.info(f"  Request delay: {REQUEST_DELAY}s")
    logger.info("="*80)

    crawler = CosmorningCrawler()

    # Step 1: Get article list pages
    logger.info("\n📋 PHASE 1: Collecting article URLs from all pages...")

    # First, determine total pages by fetching first page
    first_page = crawler.get_article_list_page(0)
    if not first_page:
        logger.error("❌ Failed to fetch first page. Aborting.")
        return False

    logger.info(f"✅ First page loaded: {len(first_page)} articles")

    # For now, we'll crawl pages 0-9 (typical range on news sites)
    # You can adjust MAX_PAGES based on actual site structure
    MAX_PAGES = 10
    all_articles = first_page.copy()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(crawler.get_article_list_page, page_num): page_num
            for page_num in range(1, MAX_PAGES)
        }

        for future in as_completed(futures):
            page_num = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"❌ Failed to process page {page_num}: {e}")

    logger.info(f"\n✅ PHASE 1 COMPLETE: {len(all_articles)} article URLs collected")

    # Step 2: Extract full content from each article
    logger.info(f"\n📄 PHASE 2: Extracting full article content...")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {}

        for article in all_articles:
            future = executor.submit(
                crawler.extract_article_content,
                article['article_id'],
                article['article_url']
            )
            futures[future] = article

        completed = 0
        for future in as_completed(futures):
            try:
                article_info = futures[future]
                content_data = future.result()

                # Merge content data with article metadata
                article_info.update(content_data)
                completed += 1

                if completed % CHECKPOINT_INTERVAL == 0:
                    crawler.save_progress(all_articles)
                    logger.info(f"📊 Progress: {completed}/{len(all_articles)} articles")

            except Exception as e:
                logger.error(f"❌ Error processing article: {e}")

    # Final save
    crawler.save_progress(all_articles)

    # Summary
    elapsed = datetime.now() - crawler.start_time
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ COSMORNING CRAWLER COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Total articles: {len(all_articles):,}")
    logger.info(f"  Time elapsed: {elapsed}")
    logger.info(f"  Average: {len(all_articles)/elapsed.total_seconds()*60:.1f} articles/min")
    logger.info(f"  Output file: {OUTPUT_DIR / 'articles.jsonl'}")
    logger.info(f"  Progress file: {PROGRESS_FILE}")
    logger.info(f"{'='*80}")

    return len(all_articles) > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
