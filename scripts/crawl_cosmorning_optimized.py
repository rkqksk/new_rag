#!/usr/bin/env python3
"""
Cosmorning.com News Crawler - OPTIMIZED
Extracts: title, date, contents (text only)
No images, no author, no unnecessary data
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
log_file = Path('/Users/oypnus/Project/rag-enterprise/data/cosmorning/logs') / f'cosmorning_optimized_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
PROGRESS_FILE = OUTPUT_DIR / 'progress_optimized.json'
OUTPUT_FILE = OUTPUT_DIR / 'articles_optimized.jsonl'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
BASE_URL = "https://cosmorning.com/news/article_list_all.html"
WORKERS = 12  # More workers since we're just extracting text
REQUEST_DELAY = 0.5  # Slightly faster since no images
CHECKPOINT_INTERVAL = 50  # Progress checkpoint every 50 articles

class CosmorningOptimizedCrawler:
    def __init__(self):
        # Configure session with connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=2
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
        self.start_time = datetime.now()

    def get_article_list_page(self, page_num: int = 0) -> List[Dict[str, Any]]:
        """Fetch article list page and extract title + date"""
        try:
            url = f"{BASE_URL}?page={page_num}"
            logger.debug(f"📥 Fetching page {page_num}")

            response = self.session.get(url, timeout=10)
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

                    # Extract title and date from link text
                    # Text structure: [title, excerpt, author, date]
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
                    logger.debug(f"✓ Article {article_id}: {title[:50]}...")

                except Exception as e:
                    logger.warning(f"⚠️  Failed to extract article: {e}")
                    continue

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
            logger.debug(f"📄 Fetching content: {article_id}")

            response = self.session.get(article_url, timeout=10)
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
            'last_update': datetime.now().isoformat(),
            'elapsed_time': str(datetime.now() - self.start_time)
        }

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

        # Save articles to JSONL
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')

        logger.info(f"💾 Saved: {len(articles)} articles")

def main():
    logger.info("="*80)
    logger.info("🚀 COSMORNING NEWS CRAWLER - OPTIMIZED (Title + Date + Content)")
    logger.info("="*80)
    logger.info(f"📊 Configuration:")
    logger.info(f"  Base URL: {BASE_URL}")
    logger.info(f"  Workers: {WORKERS}")
    logger.info(f"  Request delay: {REQUEST_DELAY}s")
    logger.info(f"  Extraction: Title, Date, Content (text only)")
    logger.info("="*80)

    crawler = CosmorningOptimizedCrawler()

    # Step 1: Get article list
    logger.info("\n📋 PHASE 1: Collecting article metadata (title + date)...")

    # Determine number of pages to crawl
    MAX_PAGES = 10  # Adjust as needed
    all_articles = []

    # Fetch all pages in parallel
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(crawler.get_article_list_page, page_num): page_num
            for page_num in range(MAX_PAGES)
        }

        for future in as_completed(futures):
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"❌ Error in parallel fetch: {e}")

    logger.info(f"\n✅ PHASE 1 COMPLETE: {len(all_articles)} articles collected")

    # Step 2: Extract content from each article
    logger.info(f"\n📄 PHASE 2: Extracting article content...")

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
                    logger.info(f"📊 Progress: {completed}/{len(all_articles)} articles")

            except Exception as e:
                logger.error(f"❌ Error processing article: {e}")

    # Final save
    crawler.save_progress(enriched_articles)

    # Summary
    elapsed = datetime.now() - crawler.start_time
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ COSMORNING CRAWLER COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Total articles: {len(enriched_articles):,}")
    logger.info(f"  Success: {crawler.articles_success:,}")
    logger.info(f"  Failed: {crawler.articles_failed:,}")
    logger.info(f"  Time elapsed: {elapsed}")
    logger.info(f"  Average speed: {len(enriched_articles)/elapsed.total_seconds()*60:.1f} articles/min")
    logger.info(f"  Output file: {OUTPUT_FILE}")
    logger.info(f"  Progress file: {PROGRESS_FILE}")
    logger.info(f"{'='*80}")

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
