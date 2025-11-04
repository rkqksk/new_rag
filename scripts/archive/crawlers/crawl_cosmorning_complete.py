#!/usr/bin/env python3
"""
Cosmorning.com Complete News Crawler
Crawls ALL articles from https://cosmorning.com/news/article_list_all.html
Extracts: title, date, contents (text only)
Supports: resume capability, checkpoint saving, parallel processing
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import time

# Setup logging
log_dir = Path('/Users/oypnus/Project/rag-enterprise/data/cosmorning/logs')
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f'cosmorning_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

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
PROGRESS_FILE = OUTPUT_DIR / 'progress_complete.json'
ARTICLES_FILE = OUTPUT_DIR / 'articles_complete.jsonl'
SEEN_IDS_FILE = OUTPUT_DIR / 'seen_article_ids.json'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
BASE_URL = "https://cosmorning.com/news/article_list_all.html"
MAX_PAGES = 5000  # All pages (0-4999)
WORKERS = 16  # Higher parallelism for large-scale crawl
REQUEST_DELAY = 0.3  # Balance between speed and respect
CHECKPOINT_INTERVAL = 500  # Save progress every 500 articles

class CosmorningCompleteCrawler:
    def __init__(self):
        # Configure session with connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=30,
            pool_maxsize=30,
            max_retries=3
        )
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        self.articles_processed = 0
        self.articles_success = 0
        self.articles_failed = 0
        self.duplicate_ids = 0
        self.start_time = datetime.now()

        # Load seen article IDs to prevent duplicates
        self.seen_ids: Set[str] = set()
        if SEEN_IDS_FILE.exists():
            try:
                with open(SEEN_IDS_FILE, 'r') as f:
                    self.seen_ids = set(json.load(f))
                logger.info(f"📋 Loaded {len(self.seen_ids)} previously seen article IDs")
            except Exception as e:
                logger.warning(f"⚠️  Could not load seen IDs: {e}")

    def get_article_list_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Fetch article list page and extract title + date"""
        try:
            url = f"{BASE_URL}?page={page_num}"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            time.sleep(REQUEST_DELAY)

            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []
            # Find article links directly (they have href with /news/article.html?no=)
            article_links = soup.find_all('a', href=re.compile(r'/news/article\.html\?no='))

            for link in article_links:
                try:
                    # Extract article ID from href
                    href = link.get('href')
                    article_id_match = re.search(r'no=(\d+)', href)
                    if not article_id_match:
                        continue

                    article_id = article_id_match.group(1)

                    # Skip if already processed
                    if article_id in self.seen_ids:
                        self.duplicate_ids += 1
                        continue

                    # Extract title and date from link text
                    all_text = link.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                    # Title is first line
                    title = lines[0] if lines else 'N/A'

                    # Excerpt is second line (preview text)
                    excerpt = lines[1] if len(lines) > 1 else ''

                    # Date matches YYYY-MM-DD HH:MM pattern (usually last)
                    date_str = 'N/A'
                    for line in lines:
                        if re.match(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}', line):
                            date_str = line
                            break

                    article = {
                        'article_id': article_id,
                        'title': title,
                        'date': date_str,
                        'excerpt': excerpt,
                        'article_url': f"https://cosmorning.com/news/article.html?no={article_id}",
                        'page': page_num,
                        'discovered_at': datetime.now().isoformat()
                    }

                    articles.append(article)
                    self.seen_ids.add(article_id)

                except Exception as e:
                    logger.debug(f"⚠️  Failed to extract article: {e}")
                    continue

            if page_num % 100 == 0:
                logger.info(f"✅ Page {page_num}: {len(articles)} articles")

            return articles

        except Exception as e:
            logger.error(f"❌ Error fetching page {page_num}: {e}")
            return []

    def extract_article_content(self, article: Dict) -> Dict[str, Any]:
        """Extract full text content from article detail page"""
        article_id = article['article_id']
        article_url = article['article_url']

        try:
            response = self.session.get(article_url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            time.sleep(REQUEST_DELAY)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find article content - correct container is news_body_area
            content = ""

            # Primary: news_body_area div (verified correct selector)
            content_div = soup.find('div', class_='news_body_area')
            if content_div:
                # Get all text, clean up whitespace
                content = content_div.get_text(separator='\n', strip=True)
                # Remove excessive newlines
                content = re.sub(r'\n\s*\n', '\n', content)
            else:
                # Fallback: try article_content if news_body_area not found
                content_div = soup.find('div', class_='article_content')
                if content_div:
                    content = content_div.get_text(separator='\n', strip=True)
                    content = re.sub(r'\n\s*\n', '\n', content)

            # Merge with article metadata
            article['content'] = content
            article['content_length'] = len(content)
            article['fetched_at'] = datetime.now().isoformat()
            article['success'] = True

            self.articles_success += 1
            return article

        except Exception as e:
            logger.error(f"❌ Failed to extract content from {article_id}: {e}")
            article['content'] = ''
            article['content_length'] = 0
            article['error'] = str(e)
            article['success'] = False
            self.articles_failed += 1
            return article

    def save_progress(self, articles: List[Dict]):
        """Save articles and progress"""
        progress = {
            'total_articles': len(articles),
            'articles_success': self.articles_success,
            'articles_failed': self.articles_failed,
            'duplicate_ids': self.duplicate_ids,
            'unique_ids_seen': len(self.seen_ids),
            'last_update': datetime.now().isoformat(),
            'elapsed_time': str(datetime.now() - self.start_time)
        }

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

        # Save articles to JSONL
        with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')

        # Save seen IDs
        with open(SEEN_IDS_FILE, 'w') as f:
            json.dump(list(self.seen_ids), f)

        logger.info(f"💾 Progress saved: {len(articles)} articles, {len(self.seen_ids)} unique IDs")

def main():
    logger.info("="*100)
    logger.info("🚀 COSMORNING COMPLETE NEWS CRAWLER (ALL ARTICLES)")
    logger.info("="*100)
    logger.info(f"📊 Configuration:")
    logger.info(f"  Base URL: {BASE_URL}")
    logger.info(f"  Max Pages: {MAX_PAGES} (pages 0-{MAX_PAGES-1})")
    logger.info(f"  Expected articles: ~{MAX_PAGES * 22:,}")
    logger.info(f"  Workers: {WORKERS}")
    logger.info(f"  Request delay: {REQUEST_DELAY}s")
    logger.info(f"  Extraction: Title, Date, Content (text only)")
    logger.info("="*100)

    crawler = CosmorningCompleteCrawler()

    # Step 1: Get article list from all pages
    logger.info(f"\n📋 PHASE 1: Collecting article metadata from {MAX_PAGES} pages...")
    logger.info(f"   Starting at: {datetime.now().isoformat()}")

    all_articles = []
    page_count = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(crawler.get_article_list_page, page_num): page_num
            for page_num in range(MAX_PAGES)
        }

        for future in as_completed(futures):
            try:
                articles = future.result()
                all_articles.extend(articles)
                page_count += 1

                if page_count % 100 == 0:
                    logger.info(f"   📈 {page_count}/{MAX_PAGES} pages fetched, {len(all_articles)} articles collected")
            except Exception as e:
                logger.error(f"❌ Error in parallel fetch: {e}")

    logger.info(f"\n✅ PHASE 1 COMPLETE: {len(all_articles)} articles collected from {page_count} pages")

    # Step 2: Extract content from each article
    logger.info(f"\n📄 PHASE 2: Extracting article content from {len(all_articles)} articles...")
    logger.info(f"   Starting at: {datetime.now().isoformat()}")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(crawler.extract_article_content, article): article['article_id']
            for article in all_articles
        }

        completed = 0
        enriched_articles = []

        for future in as_completed(futures):
            try:
                article = future.result()
                enriched_articles.append(article)
                completed += 1

                if completed % CHECKPOINT_INTERVAL == 0:
                    crawler.save_progress(enriched_articles)
                    elapsed = datetime.now() - crawler.start_time
                    speed = completed / elapsed.total_seconds() * 60
                    eta_remaining = (len(all_articles) - completed) / speed
                    logger.info(f"   📊 Progress: {completed}/{len(all_articles)} | Speed: {speed:.0f} articles/min | ETA: {eta_remaining:.0f} min")

            except Exception as e:
                logger.error(f"❌ Error processing article: {e}")

    # Final save
    crawler.save_progress(enriched_articles)

    # Summary
    elapsed = datetime.now() - crawler.start_time
    logger.info(f"\n{'='*100}")
    logger.info(f"✅ COSMORNING COMPLETE CRAWLER FINISHED")
    logger.info(f"{'='*100}")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Total articles collected: {len(all_articles):,}")
    logger.info(f"  Articles with content: {crawler.articles_success:,}")
    logger.info(f"  Failed extractions: {crawler.articles_failed:,}")
    logger.info(f"  Duplicate IDs skipped: {crawler.duplicate_ids:,}")
    logger.info(f"  Unique article IDs: {len(crawler.seen_ids):,}")
    logger.info(f"  Time elapsed: {elapsed}")
    logger.info(f"  Average speed: {len(enriched_articles)/elapsed.total_seconds()*60:.1f} articles/min")
    logger.info(f"  Output file: {ARTICLES_FILE}")
    logger.info(f"  Progress file: {PROGRESS_FILE}")
    logger.info(f"{'='*100}")

    return len(enriched_articles) > 0

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
