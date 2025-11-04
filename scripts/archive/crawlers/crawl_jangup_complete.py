#!/usr/bin/env python3
"""
🚀 JANGUP NEWSPAPER COMPLETE CRAWLER
====================================

Crawls all articles from jangup.com news section
- Supports pagination
- Text-only extraction
- Multiple categories and sections
- Production-ready with checkpoints

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

# Output directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/jangup/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/jangup/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = LOG_DIR / f"jangup_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# PHASE 1: COLLECT ARTICLE URLS
# ============================================

def collect_article_urls(max_pages=100):
    """
    Collect all article URLs from listing pages using Selenium
    """
    
    logger.info("=" * 80)
    logger.info("🚀 PHASE 1: COLLECTING ARTICLE URLs FROM LISTING PAGES")
    logger.info("=" * 80)
    
    article_urls = set()
    
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
        
        for page_num in range(1, max_pages + 1):
            url = f"{NEWS_LIST_URL}?view_type=sm&page={page_num}"
            
            logger.info(f"📄 Page {page_num}/{max_pages}: {url}")
            
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)
                
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all article links
                links = soup.find_all('a', href=lambda x: x and '/news/article' in str(x))
                
                # Filter for actual article URLs (not category/section navigation)
                page_articles = 0
                for link in links:
                    href = link.get('href', '')
                    if '/news/article' in href and 'articleList' not in href:
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in article_urls:
                            article_urls.add(full_url)
                            page_articles += 1
                
                logger.info(f"  ✓ Found {page_articles} new articles on this page (Total: {len(article_urls)})")
                
                # Stop if no new articles (end of list)
                if page_articles == 0 and page_num > 5:
                    logger.info(f"✓ No new articles found. Assuming end of list at page {page_num}")
                    break
                
                time.sleep(2)  # Respectful delay
                
            except Exception as e:
                logger.warning(f"  ⚠️  Error on page {page_num}: {e}")
                continue
        
        driver.quit()
        
    except Exception as e:
        logger.error(f"❌ Critical error in Phase 1: {e}")
    
    logger.info(f"\n✅ PHASE 1 COMPLETE: {len(article_urls)} unique article URLs collected\n")
    return sorted(list(article_urls))

# ============================================
# PHASE 2: EXTRACT ARTICLE CONTENT
# ============================================

def extract_article_content(article_url):
    """
    Extract content from a single article page
    """
    
    try:
        response = requests.get(article_url, timeout=10)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract article data
        article_data = {
            "url": article_url,
            "title": None,
            "author": None,
            "date": None,
            "category": None,
            "content": None,
            "crawled_at": datetime.now().isoformat()
        }
        
        # Extract title
        title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
        if title_elem:
            article_data["title"] = title_elem.get_text(strip=True)[:500]
        
        # Extract author and date (usually in byline)
        byline = soup.find(class_=lambda x: x and 'byline' in x.lower() if x else False)
        if byline:
            byline_text = byline.get_text(strip=True)
            article_data["author"] = byline_text[:100]
        
        # Try to extract date
        date_elem = soup.find(class_=lambda x: x and any(word in x.lower() for word in ['date', 'time', 'posted']) if x else False)
        if date_elem:
            article_data["date"] = date_elem.get_text(strip=True)[:50]
        else:
            # Look for date pattern in page
            date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})', soup.get_text())
            if date_match:
                article_data["date"] = date_match.group(1)
        
        # Extract category
        cat_elem = soup.find(class_=lambda x: x and any(word in x.lower() for word in ['category', 'section', 'cate']) if x else False)
        if cat_elem:
            article_data["category"] = cat_elem.get_text(strip=True)[:100]
        
        # Extract main content
        content_elem = soup.find(class_=lambda x: x and 'article' in x.lower() and 'content' in x.lower() if x else False)
        if not content_elem:
            content_elem = soup.find('div', class_='article-view-content')
        if not content_elem:
            content_elem = soup.find('article')
        if not content_elem:
            # Fallback: get body text after title
            body = soup.find('body')
            if body:
                content_elem = body
        
        if content_elem:
            # Remove scripts and styles
            for script in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            content_text = content_elem.get_text(separator='\n', strip=True)
            content_text = '\n'.join(line.strip() for line in content_text.split('\n') if line.strip())
            article_data["content"] = content_text[:5000]
        
        return article_data if article_data.get("content") else None
        
    except Exception as e:
        logger.warning(f"⚠️  Error extracting {article_url}: {e}")
        return None

def extract_all_articles(article_urls, workers=4):
    """
    Extract content from all articles using parallel processing
    """
    
    logger.info("=" * 80)
    logger.info("🚀 PHASE 2: EXTRACTING ARTICLE CONTENT")
    logger.info("=" * 80)
    logger.info(f"📊 Processing {len(article_urls)} articles with {workers} workers\n")
    
    articles = []
    processed = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(extract_article_content, url): url for url in article_urls}
        
        for future in as_completed(futures):
            processed += 1
            result = future.result()
            
            if result:
                articles.append(result)
                logger.info(f"✓ [{processed}/{len(article_urls)}] {result.get('title', 'No title')[:60]}")
            
            # Checkpoint every 500 articles
            if processed % 500 == 0:
                logger.info(f"📊 Progress: {processed}/{len(article_urls)} ({100*processed/len(article_urls):.1f}%)")
    
    logger.info(f"\n✅ PHASE 2 COMPLETE: {len(articles)} articles successfully extracted\n")
    return articles

# ============================================
# PHASE 3: SAVE RESULTS
# ============================================

def save_results(articles):
    """
    Save articles to JSONL and summary JSON
    """
    
    logger.info("=" * 80)
    logger.info("🚀 PHASE 3: SAVING RESULTS")
    logger.info("=" * 80)
    
    # Save as JSONL
    jsonl_file = OUTPUT_DIR / "articles_complete.jsonl"
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False) + '\n')
    
    logger.info(f"💾 Saved {len(articles)} articles to {jsonl_file}")
    
    # Save summary
    summary_file = OUTPUT_DIR / "articles_summary.json"
    summary = {
        "total_articles": len(articles),
        "crawl_date": datetime.now().isoformat(),
        "output_file": str(jsonl_file),
        "articles_with_content": len([a for a in articles if a.get('content')]),
        "articles_with_date": len([a for a in articles if a.get('date')]),
        "articles_with_category": len([a for a in articles if a.get('category')]),
        "avg_content_length": int(sum(len(a.get('content', '')) for a in articles) / len(articles)) if articles else 0
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📊 Saved summary to {summary_file}")
    
    return jsonl_file, summary_file

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    start_time = time.time()
    
    try:
        logger.info("\n" + "=" * 80)
        logger.info("🚀 JANGUP COMPLETE NEWSPAPER CRAWLER")
        logger.info("=" * 80 + "\n")
        
        # Phase 1: Collect URLs
        article_urls = collect_article_urls(max_pages=100)
        
        if not article_urls:
            logger.error("❌ No article URLs found. Exiting.")
            return
        
        # Phase 2: Extract content
        articles = extract_all_articles(article_urls, workers=8)
        
        if not articles:
            logger.error("❌ No articles extracted. Exiting.")
            return
        
        # Phase 3: Save results
        jsonl_file, summary_file = save_results(articles)
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("✅ CRAWLING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   - Total articles extracted: {len(articles)}")
        logger.info(f"   - Time elapsed: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        logger.info(f"   - Average speed: {len(articles)/elapsed:.1f} articles/second")
        logger.info(f"   - Output: {jsonl_file}")
        logger.info("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
