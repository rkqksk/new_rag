#!/usr/bin/env python3
"""
🚀 ONEHAGO COMMUNITY FINDER - FINAL PRODUCTION CRAWLER
=======================================================

Strategy:
- Extract posts from find.php listing pages (content is visible in preview)
- Handle pagination to get all available posts
- Text-only extraction (no images)
- Production-ready with full error handling
"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, parse_qs
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

BASE_URL = "https://www.onehago.com"
FIND_PAGE_URL = f"{BASE_URL}/community/find.php"

# Output directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/community/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/community/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = LOG_DIR / f"community_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# EXTRACT POSTS FROM LISTING PAGE
# ============================================

def extract_posts_from_page(page_url):
    """
    Extract all posts from a listing page.
    Posts show their full content in the preview on find.php
    """
    
    posts = []
    
    try:
        # Setup Selenium
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        # Disable images
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2
        })
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        logger.info(f"📥 Fetching: {page_url}")
        driver.get(page_url)
        
        # Wait for page content to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='BoardMode=view']"))
        )
        
        time.sleep(2)  # Extra wait for JavaScript rendering
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all post links
        post_links = soup.find_all('a', href=lambda x: x and 'BoardMode=view' in x)
        
        logger.info(f"✅ Found {len(post_links)} posts on page")
        
        # Extract each post
        for link in post_links:
            try:
                href = link.get('href')
                if not href or 'BoardMode=view' not in href:
                    continue
                
                # Parse UID from URL
                full_url = urljoin(BASE_URL, href)
                match = re.search(r'UID=(\d+)', href)
                uid = match.group(1) if match else None
                
                if not uid:
                    continue
                
                # Extract post content from the link text
                # The full post content is displayed in the listing
                post_text = link.get_text(strip=True)
                
                if not post_text or len(post_text) < 10:
                    continue
                
                # Clean up text
                post_text = '\n'.join(line.strip() for line in post_text.split('\n') if line.strip())
                
                # Try to extract title (first line or before first newline of substantial content)
                lines = post_text.split('\n')
                title = lines[0][:200] if lines else "No title"
                
                # Get full content
                content = post_text[:5000]  # Limit to 5000 chars
                
                # Try to extract metadata from visible text
                author = None
                date = None
                
                # Look for author patterns (often mentions "원하고" or company names)
                author_match = re.search(r'([\w가-힣]+\s+\w+\s+\d{3}-\d{4}-\d{4})', post_text)
                if author_match:
                    author = author_match.group(1)[:100]
                
                # Look for dates
                date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2})', post_text)
                if date_match:
                    date = date_match.group(1)
                
                post_data = {
                    "id": f"find_{uid}",
                    "uid": uid,
                    "url": full_url,
                    "title": title,
                    "author": author,
                    "date": date,
                    "content": content,
                    "crawled_at": datetime.now().isoformat(),
                    "source": "onehago_community_find"
                }
                
                posts.append(post_data)
                logger.info(f"  ✅ Post {uid}: {title[:50]}...")
                
            except Exception as e:
                logger.warning(f"  ⚠️  Error processing post: {e}")
                continue
        
        driver.quit()
        
    except Exception as e:
        logger.error(f"❌ Error fetching page {page_url}: {e}")
    
    return posts

# ============================================
# PAGINATE THROUGH ALL POSTS
# ============================================

def crawl_all_posts(max_pages=100):
    """
    Crawl all posts by iterating through find.php pages.
    """
    
    logger.info("=" * 80)
    logger.info("🚀 ONEHAGO COMMUNITY FINDER CRAWLER - PRODUCTION MODE")
    logger.info("=" * 80)
    
    all_posts = []
    seen_uids = set()
    
    # Try different pagination methods
    for page_num in range(max_pages):
        
        # Method 1: Traditional pagination parameter
        page_url = f"{FIND_PAGE_URL}?CURRENT_PAGE={page_num + 1}"
        
        logger.info(f"\n📄 Page {page_num + 1}/{max_pages}")
        
        posts = extract_posts_from_page(page_url)
        
        if not posts:
            logger.info(f"ℹ️  No more posts found. Stopping at page {page_num + 1}")
            break
        
        # Add posts, skipping duplicates
        for post in posts:
            uid = post['uid']
            if uid not in seen_uids:
                all_posts.append(post)
                seen_uids.add(uid)
        
        logger.info(f"📊 Total posts collected: {len(all_posts)}")
        
        # Be respectful - add delay between requests
        time.sleep(3)
    
    return all_posts

# ============================================
# SAVE RESULTS
# ============================================

def save_results(posts):
    """Save posts to JSONL and summary JSON"""
    
    # Save as JSONL
    jsonl_file = OUTPUT_DIR / "community_find_posts.jsonl"
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    logger.info(f"💾 Saved {len(posts)} posts to {jsonl_file}")
    
    # Save summary
    summary_file = OUTPUT_DIR / "community_find_summary.json"
    summary = {
        "total_posts": len(posts),
        "unique_posts": len(set(p['uid'] for p in posts)),
        "crawl_date": datetime.now().isoformat(),
        "output_file": str(jsonl_file),
        "posts": posts[:100]  # Include first 100 for preview
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
        # Crawl all posts
        all_posts = crawl_all_posts(max_pages=20)  # Start with 20 pages
        
        if not all_posts:
            logger.error("❌ No posts were extracted")
            return
        
        logger.info(f"\n✅ CRAWLING COMPLETE - Total posts: {len(all_posts)}")
        
        # Save results
        jsonl_file, summary_file = save_results(all_posts)
        
        elapsed = time.time() - start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"  - Total posts extracted: {len(all_posts)}")
        logger.info(f"  - Unique UIDs: {len(set(p['uid'] for p in all_posts))}")
        logger.info(f"  - Time elapsed: {elapsed:.1f} seconds")
        logger.info(f"  - Average: {len(all_posts)/elapsed:.1f} posts/second")
        logger.info(f"  - Output: {jsonl_file}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
