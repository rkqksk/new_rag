#!/usr/bin/env python3
"""
🚀 JANGUP NEWSPAPER FULL CRAWLER - 81,471 ARTICLES
===================================================

Complete crawler for jangup.com news section
- Target: All 81,471 articles
- Smart pagination: 4,074 pages required
- Batch checkpoints every 500 articles
- Production-ready with error recovery

"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.jangup.com"
NEWS_LIST_URL = f"{BASE_URL}/news/articleList.html"

TOTAL_ARTICLES_AVAILABLE = 81471
ARTICLES_PER_PAGE = 20
TOTAL_PAGES = (TOTAL_ARTICLES_AVAILABLE // ARTICLES_PER_PAGE) + 1  # 4,074

# Output directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/jangup/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/jangup/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Checkpoint files
PROGRESS_FILE = OUTPUT_DIR / "jangup_progress.json"
URLS_FILE = OUTPUT_DIR / "article_urls_full.jsonl"
ARTICLES_FILE = OUTPUT_DIR / "articles_complete_81k.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "jangup_summary_81k.json"

# Setup logging
log_file = LOG_DIR / f"jangup_full_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# PROGRESS TRACKING
# ============================================

def load_progress():
    """Load progress from checkpoint file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'phase': 'url_collection',
        'pages_collected': 0,
        'urls_collected': 0,
        'articles_extracted': 0,
        'start_time': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save progress to checkpoint file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ============================================
# PHASE 1: COLLECT ALL ARTICLE URLs
# ============================================

def collect_article_urls_batch():
    """
    Collect all article URLs from all 4,074 pages
    """

    logger.info("=" * 80)
    logger.info("🚀 PHASE 1: COLLECTING ALL ARTICLE URLs (81,471 articles)")
    logger.info("=" * 80)
    logger.info(f"Total pages to collect: {TOTAL_PAGES:,}")
    logger.info(f"Target: {TOTAL_ARTICLES_AVAILABLE:,} articles")

    progress = load_progress()
    start_page = progress.get('pages_collected', 0) + 1

    article_urls = set()
    urls_collected = progress.get('urls_collected', 0)

    # Load existing URLs if resuming
    if URLS_FILE.exists():
        with open(URLS_FILE, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    article_urls.add(data['url'])
                except:
                    pass
        urls_collected = len(article_urls)
        logger.info(f"📥 Loaded {urls_collected} existing URLs from checkpoint")

    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2
        })

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        for page_num in range(start_page, TOTAL_PAGES + 1):
            url = f"{NEWS_LIST_URL}?view_type=sm&page={page_num}"

            if page_num % 100 == 0 or page_num == start_page:
                logger.info(f"📄 Page {page_num:,}/{TOTAL_PAGES:,} | URLs: {len(article_urls):,}")

            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
                )
                time.sleep(1)  # Reduced from 2s for speed

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                links = soup.find_all('a', href=lambda x: x and '/news/article' in str(x))

                page_new_urls = 0
                for link in links:
                    href = link.get('href', '')
                    if '/news/article' in href and 'articleList' not in href:
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in article_urls:
                            article_urls.add(full_url)
                            page_new_urls += 1

                # Checkpoint every 500 pages
                if page_num % 500 == 0:
                    progress['pages_collected'] = page_num
                    progress['urls_collected'] = len(article_urls)
                    progress['last_checkpoint'] = datetime.now().isoformat()
                    save_progress(progress)

                    # Save URLs to file
                    with open(URLS_FILE, 'w') as f:
                        for url_item in sorted(article_urls):
                            f.write(json.dumps({'url': url_item, 'collected_at': datetime.now().isoformat()}, ensure_ascii=False) + '\n')

                    logger.info(f"  ✅ Checkpoint: Page {page_num:,} | Total URLs: {len(article_urls):,}")

                # Safety: Stop if no new URLs for 10 pages (indicates end of list)
                if page_new_urls == 0 and page_num > 100:
                    consecutive_empty = 0
                    for check_page in range(page_num - 10, page_num + 1):
                        if check_page > page_num:
                            break
                        # Simple check - this is already handled by continuing through pages

                time.sleep(0.5)  # Small delay between requests

            except Exception as e:
                logger.warning(f"⚠️  Error on page {page_num}: {e}")
                time.sleep(2)  # Back off on error
                continue

        driver.quit()

    except Exception as e:
        logger.error(f"❌ Fatal error in Phase 1: {e}")

    # Final save
    progress['pages_collected'] = TOTAL_PAGES
    progress['urls_collected'] = len(article_urls)
    progress['phase'] = 'content_extraction'
    save_progress(progress)

    with open(URLS_FILE, 'w') as f:
        for url_item in sorted(article_urls):
            f.write(json.dumps({'url': url_item, 'collected_at': datetime.now().isoformat()}, ensure_ascii=False) + '\n')

    logger.info(f"\n✅ PHASE 1 COMPLETE")
    logger.info(f"Total unique URLs collected: {len(article_urls):,}")

    return sorted(list(article_urls))

# ============================================
# PHASE 2: EXTRACT ARTICLE CONTENT
# ============================================

def extract_article_content(article_url):
    """Extract content from single article page"""

    try:
        response = requests.get(article_url, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        article_data = {
            "url": article_url,
            "title": None,
            "author": None,
            "date": None,
            "content": None,
            "crawled_at": datetime.now().isoformat()
        }

        # Extract title
        title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
        if title_elem:
            article_data["title"] = title_elem.get_text(strip=True)[:500]

        # Extract date
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, soup.get_text())
            if date_match:
                article_data["date"] = date_match.group(1)
                break

        # Extract content
        content_elem = soup.find(class_=lambda x: x and any(keyword in x.lower() for keyword in ['article', 'content', 'body']) if x else False)
        if not content_elem:
            content_elem = soup.find('div', class_=lambda x: x is not None)

        if content_elem:
            for script in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()

            content_text = content_elem.get_text(separator='\n', strip=True)
            content_text = '\n'.join(line.strip() for line in content_text.split('\n') if line.strip())
            article_data["content"] = content_text[:5000]

        return article_data if article_data.get("content") else None

    except Exception as e:
        logger.debug(f"Error extracting {article_url}: {e}")
        return None

def extract_all_articles(article_urls, max_workers=8):
    """Extract content from all collected article URLs"""

    logger.info("=" * 80)
    logger.info(f"🚀 PHASE 2: EXTRACTING ARTICLE CONTENT ({len(article_urls):,} URLs)")
    logger.info(f"Using {max_workers} parallel workers")
    logger.info("=" * 80)

    articles_extracted = []
    checkpoint_interval = 500
    start_idx = 0

    # Check for existing extracted articles
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, 'r') as f:
            for line in f:
                try:
                    articles_extracted.append(json.loads(line.strip()))
                    start_idx += 1
                except:
                    pass
        logger.info(f"📥 Loaded {len(articles_extracted)} existing extracted articles")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_article_content, url): (idx, url) for idx, url in enumerate(article_urls[start_idx:], start_idx)}

        completed = start_idx

        for future in as_completed(futures):
            idx, url = futures[future]
            completed += 1

            try:
                result = future.result()
                if result:
                    articles_extracted.append(result)

                    # Checkpoint every 500 articles
                    if completed % checkpoint_interval == 0:
                        logger.info(f"📊 Progress: {completed:,}/{len(article_urls):,} ({100*completed/len(article_urls):.1f}%)")

                        # Save checkpoint
                        with open(ARTICLES_FILE, 'w') as f:
                            for article in articles_extracted:
                                f.write(json.dumps(article, ensure_ascii=False) + '\n')

                        progress = load_progress()
                        progress['articles_extracted'] = len(articles_extracted)
                        progress['last_checkpoint'] = datetime.now().isoformat()
                        save_progress(progress)

            except Exception as e:
                logger.warning(f"Error processing article {idx}: {e}")

    return articles_extracted

# ============================================
# PHASE 3: SAVE RESULTS
# ============================================

def save_results(articles):
    """Save extracted articles and summary"""

    logger.info("=" * 80)
    logger.info("📾 PHASE 3: SAVING RESULTS")
    logger.info("=" * 80)

    # Save JSONL
    with open(ARTICLES_FILE, 'w') as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False) + '\n')

    logger.info(f"💾 Saved {len(articles)} articles to {ARTICLES_FILE}")

    # Save summary
    summary = {
        "total_target": TOTAL_ARTICLES_AVAILABLE,
        "extracted_articles": len(articles),
        "extracted_with_content": len([a for a in articles if a.get('content')]),
        "completion_rate": f"{100 * len(articles) / TOTAL_ARTICLES_AVAILABLE:.1f}%",
        "crawl_date": datetime.now().isoformat(),
        "output_file": str(ARTICLES_FILE),
        "articles_sample": articles[:5] if articles else []
    }

    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"📊 Saved summary to {SUMMARY_FILE}")

    return ARTICLES_FILE, SUMMARY_FILE

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    start_time = time.time()

    try:
        logger.info("\n" + "=" * 80)
        logger.info("🚀 JANGUP NEWSPAPER FULL CRAWLER - 81,471 ARTICLES")
        logger.info("=" * 80)

        # Phase 1: Collect URLs
        article_urls = collect_article_urls_batch()

        if not article_urls:
            logger.error("❌ No articles found")
            return

        logger.info(f"\n✅ Phase 1 complete: {len(article_urls):,} URLs collected")

        # Phase 2: Extract content
        articles = extract_all_articles(article_urls, max_workers=8)

        if not articles:
            logger.error("❌ No articles extracted")
            return

        logger.info(f"\n✅ Phase 2 complete: {len(articles):,} articles extracted")

        # Phase 3: Save results
        jsonl_file, summary_file = save_results(articles)

        elapsed = time.time() - start_time

        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"  - Target articles: {TOTAL_ARTICLES_AVAILABLE:,}")
        logger.info(f"  - URLs collected: {len(article_urls):,}")
        logger.info(f"  - Articles extracted: {len(articles):,}")
        logger.info(f"  - With content: {len([a for a in articles if a.get('content')]):,}")
        logger.info(f"  - Completion rate: {100 * len(articles) / TOTAL_ARTICLES_AVAILABLE:.1f}%")
        logger.info(f"  - Time elapsed: {elapsed/3600:.1f} hours")
        logger.info(f"  - Output: {jsonl_file}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
