#!/usr/bin/env python3
"""
🔍 ONEHAGO COMMUNITY POSTS CRAWLER - IMPROVED STRATEGY
====================================================

This crawler:
1. Finds post URLs from find.php pagination
2. Extracts individual post content (title, author, date, content)
3. Handles dynamic JavaScript content with Selenium
4. Text-only extraction (no images)
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
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

CHROME_OPTIONS = {
    "headless": True,
    "no_sandbox": True,
    "disable_dev_shm_usage": True,
    "disable_gpu": True,
    "window_size": "1920,1080",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/community/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/community/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = LOG_DIR / f"community_posts_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# PHASE 1: DISCOVER POST URLS
# ============================================

def discover_post_urls(max_pages=10):
    """
    Find all post URLs from find.php listing pages.
    
    The find.php page uses AJAX/JavaScript to load content.
    We'll use Selenium to render the page and extract post links.
    """
    
    logger.info("=" * 80)
    logger.info("PHASE 1: DISCOVERING POST URLs FROM LISTING PAGES")
    logger.info("=" * 80)
    
    post_urls = set()
    
    try:
        # Setup Selenium
        chrome_options = webdriver.ChromeOptions()
        for key, value in CHROME_OPTIONS.items():
            if key == "window_size":
                chrome_options.add_argument(f"--{key}={value}")
            elif key == "user_agent":
                chrome_options.add_argument(f"user-agent={value}")
            else:
                chrome_options.add_argument(f"--{key}")
        
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2  # Disable images
        })
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        logger.info(f"📥 Fetching find.php listing page...")
        driver.get(FIND_PAGE_URL)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='BoardMode=view']"))
        )
        
        time.sleep(2)  # Extra wait for dynamic content
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all post links
        post_links = soup.find_all('a', href=lambda x: x and 'BoardMode=view' in x)
        
        logger.info(f"✅ Found {len(post_links)} post links on find.php")
        
        for link in post_links:
            href = link.get('href')
            if href and 'BoardMode=view' in href:
                full_url = urljoin(BASE_URL, href)
                post_urls.add(full_url)
        
        driver.quit()
        
    except Exception as e:
        logger.error(f"❌ Error discovering post URLs: {e}")
    
    logger.info(f"📊 Total unique post URLs found: {len(post_urls)}")
    return sorted(list(post_urls))

# ============================================
# PHASE 2: EXTRACT POST CONTENT
# ============================================

def extract_post_content(post_url):
    """
    Extract content from a single post URL.
    """
    
    try:
        # Setup Selenium for this post
        chrome_options = webdriver.ChromeOptions()
        for key, value in CHROME_OPTIONS.items():
            if key == "window_size":
                chrome_options.add_argument(f"--{key}={value}")
            elif key == "user_agent":
                chrome_options.add_argument(f"user-agent={value}")
            else:
                chrome_options.add_argument(f"--{key}")
        
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2
        })
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        driver.get(post_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "body"))
        )
        
        time.sleep(1)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract data
        post_data = {
            "url": post_url,
            "crawled_at": datetime.now().isoformat(),
            "title": None,
            "author": None,
            "date": None,
            "content": None
        }
        
        # Try to find title (common patterns)
        title_elem = soup.find('h1', class_='post-title') or soup.find('h2', class_='post-title')
        if not title_elem:
            title_elem = soup.find('h1') or soup.find('h2')
        if title_elem:
            post_data["title"] = title_elem.get_text(strip=True)[:500]
        
        # Extract author
        author_elem = soup.find(class_='author') or soup.find(class_='writer')
        if author_elem:
            post_data["author"] = author_elem.get_text(strip=True)
        
        # Extract date
        date_elem = soup.find(class_='date') or soup.find(class_='time') or soup.find(class_='date-time')
        if date_elem:
            post_data["date"] = date_elem.get_text(strip=True)
        
        # Extract main content
        content_elem = soup.find(class_='post-content') or soup.find(class_='content') or soup.find(class_='article-body')
        if content_elem:
            # Remove scripts and styles
            for script in content_elem(['script', 'style']):
                script.decompose()
            
            content_text = content_elem.get_text(separator='\n', strip=True)
            # Clean up whitespace
            content_text = '\n'.join(line.strip() for line in content_text.split('\n') if line.strip())
            post_data["content"] = content_text[:5000]  # Limit to 5000 chars
        
        driver.quit()
        
        return post_data if post_data["content"] else None
        
    except Exception as e:
        logger.warning(f"⚠️  Error extracting {post_url}: {e}")
        return None

# ============================================
# PHASE 3: SAVE RESULTS
# ============================================

def save_results(posts):
    """Save extracted posts to JSONL file."""
    
    output_file = OUTPUT_DIR / "community_posts_extracted.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for post in posts:
            if post:
                f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    logger.info(f"💾 Saved {len([p for p in posts if p])} posts to {output_file}")
    return output_file

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    logger.info("\n" + "=" * 80)
    logger.info("🚀 ONEHAGO COMMUNITY POSTS CRAWLER - IMPROVED VERSION")
    logger.info("=" * 80)
    
    # Phase 1: Discover post URLs
    post_urls = discover_post_urls()
    
    if not post_urls:
        logger.error("❌ No post URLs found. Check if find.php has accessible content.")
        return
    
    logger.info(f"\n✅ Found {len(post_urls)} post URLs to extract")
    
    # Phase 2: Extract content from posts
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: EXTRACTING POST CONTENT")
    logger.info("=" * 80)
    
    posts = []
    
    # Use ThreadPoolExecutor for parallel extraction
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(extract_post_content, url): url for url in post_urls[:10]}  # Start with 10
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                posts.append(result)
                logger.info(f"✅ Extracted: {result.get('title', 'No title')[:50]}")
            
            if completed % 5 == 0:
                logger.info(f"📊 Progress: {completed}/{len(post_urls)}")
    
    # Phase 3: Save results
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: SAVING RESULTS")
    logger.info("=" * 80)
    
    output_file = save_results(posts)
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ CRAWLER COMPLETE")
    logger.info("=" * 80)
    logger.info(f"📊 Statistics:")
    logger.info(f"  - Total post URLs found: {len(post_urls)}")
    logger.info(f"  - Posts successfully extracted: {len([p for p in posts if p])}")
    logger.info(f"  - Output file: {output_file}")

if __name__ == "__main__":
    main()
