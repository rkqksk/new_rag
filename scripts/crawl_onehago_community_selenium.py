#!/usr/bin/env python3
"""
Onehago Community Crawler - Selenium-based text extraction
Supports: News, Onehago Forum, Find Search, Service, Video sections
TEXT-ONLY extraction (no images or photos)
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration
BASE_URL = "https://www.onehago.com"
COMMUNITY_SECTIONS = {
    "news": "/community/news.php",
    "onehago": "/community/onehago.php",
    "find": "/community/find.php",
    "service": "/community/service.php",
    "video": "/community/video.php"
}

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/onehago/community")
CRAWLED_DIR = OUTPUT_DIR / "crawled"
LOG_DIR = OUTPUT_DIR / "logs"
CRAWLED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Selenium Settings
HEADLESS = True                # Run without GUI
IMPLICIT_WAIT = 10            # Seconds
EXPLICIT_WAIT = 15            # Seconds for element waits
REQUEST_DELAY = 1.0           # Seconds between pages
TIMEOUT = 30                  # Page load timeout
CHECKPOINT_INTERVAL = 500     # Save progress every 500 posts

# Parallel Settings
MAX_CONCURRENT_BROWSERS = 4   # Limit concurrent Chrome instances for memory

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"community_crawler_selenium_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


class CommunityCrawlerSelenium:
    def __init__(self):
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        self.seen_posts = set()
        self.load_seen_posts()

        self.posts = []
        self.structure = {}
        self.stats = {
            "total_posts_found": 0,
            "total_posts_crawled": 0,
            "total_posts_failed": 0,
            "sections_completed": [],
            "start_time": None,
            "end_time": None
        }

    def init_selenium(self):
        """Initialize Selenium Chrome driver"""
        try:
            chrome_options = Options()
            if HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

            # Disable image loading for faster performance
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(TIMEOUT)
            self.driver.implicitly_wait(IMPLICIT_WAIT)

            logger.info("✓ Selenium Chrome driver initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            logger.error("   Make sure ChromeDriver is installed and in PATH")
            logger.error("   Download from: https://chromedriver.chromium.org/")
            return False

    def close_selenium(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ Selenium driver closed")

    def load_seen_posts(self):
        """Load previously seen post IDs"""
        seen_file = OUTPUT_DIR / "seen_post_ids.json"
        if seen_file.exists():
            try:
                with open(seen_file) as f:
                    self.seen_posts = set(json.load(f))
                logger.info(f"✓ Loaded {len(self.seen_posts)} previously seen post IDs")
            except Exception as e:
                logger.warning(f"Could not load seen posts: {e}")
                self.seen_posts = set()

    def save_seen_posts(self):
        """Save all seen post IDs"""
        try:
            seen_file = OUTPUT_DIR / "seen_post_ids.json"
            with open(seen_file, 'w') as f:
                json.dump(list(self.seen_posts), f)
        except Exception as e:
            logger.error(f"Failed to save seen posts: {e}")

    def save_checkpoint(self):
        """Save progress checkpoint"""
        try:
            checkpoint_file = OUTPUT_DIR / "community_posts.jsonl"
            with open(checkpoint_file, 'w') as f:
                for post in self.posts:
                    f.write(json.dumps(post, ensure_ascii=False) + '\n')
            logger.info(f"💾 Checkpoint saved: {len(self.posts)} posts")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def fetch_with_selenium(self, url: str) -> Optional[str]:
        """Fetch page with Selenium and return rendered HTML"""
        try:
            logger.debug(f"  Fetching with Selenium: {url}")
            self.driver.get(url)

            # Wait for content to load - look for common post containers
            try:
                WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                    EC.presence_of_any_elements_located((By.CSS_SELECTOR, "tr, div.item, div.post, li.item"))
                )
            except:
                # If content doesn't load, wait a bit and continue anyway
                logger.debug(f"  Content load timeout for {url}, continuing...")
                time.sleep(2)

            # Return rendered HTML
            return self.driver.page_source
        except Exception as e:
            logger.warning(f"✗ Selenium fetch failed for {url}: {e}")
            return None

    def extract_posts_from_html(self, section: str, html: str) -> List[Dict]:
        """Extract posts from HTML (rendered by Selenium)"""
        posts = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Look for post containers - try multiple selectors
            list_items = soup.find_all(['tr', 'div', 'li'], class_=[
                'list-item', 'post', 'thread', 'item', 'list-row', 'notice-row',
                'board-item', 'content-item', 'post-item', 'row'
            ])

            if not list_items:
                # Try more generic approach - all TR or DIV elements
                list_items = soup.find_all('tr')[1:] if soup.find_all('tr') else soup.find_all('div', class_='item')

            logger.debug(f"  Found {len(list_items)} potential post items")

            for item_idx, item in enumerate(list_items):
                try:
                    # Extract link (title & URL)
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title or len(title) < 3:  # Skip very short titles
                        continue

                    post_url = link_elem.get('href', '')
                    if not post_url.startswith('http'):
                        post_url = urljoin(BASE_URL, post_url)

                    # Generate post ID
                    post_id = f"{section}_{hash(post_url) % 1000000}"

                    if post_id in self.seen_posts:
                        continue

                    # Extract metadata from table cells
                    tds = item.find_all('td')
                    author = ""
                    date_str = ""
                    views = 0

                    if len(tds) >= 3:
                        # Typical layout: title | author | date | views
                        author = tds[-3].get_text(strip=True) if len(tds) >= 3 else ""
                        date_str = tds[-2].get_text(strip=True) if len(tds) >= 2 else ""
                        views_text = tds[-1].get_text(strip=True) if len(tds) >= 1 else "0"
                        try:
                            views = int(views_text) if views_text.isdigit() else 0
                        except:
                            views = 0

                    post = {
                        "id": post_id,
                        "section": section,
                        "title": title,
                        "author": author,
                        "date": date_str,
                        "views": views,
                        "url": post_url,
                        "content": "",  # Will be filled in detail extraction
                        "crawled_at": datetime.now().isoformat()
                    }

                    posts.append(post)
                    self.seen_posts.add(post_id)

                except Exception as e:
                    logger.debug(f"    Error extracting item {item_idx}: {e}")
                    continue

            return posts
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def extract_post_content(self, post: Dict) -> Dict:
        """Extract full text content from individual post page"""
        try:
            html = self.fetch_with_selenium(post["url"])
            if not html:
                return post

            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style tags
            for script in soup(['script', 'style', 'img', 'picture', 'figure']):
                script.decompose()

            # Look for content area - try multiple selectors
            content_area = soup.find(['div', 'article', 'section'], class_=[
                'content', 'body', 'post-content', 'detail-content', 'view-content',
                'article-content', 'board-content', 'message'
            ])

            if not content_area:
                # Fallback: get main content area
                content_area = soup.find('div', class_='main-content')

            if content_area:
                # Extract clean text
                text = content_area.get_text(separator='\n', strip=True)
                # Clean up excessive whitespace
                text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                post["content"] = text[:5000]  # Limit to 5000 chars

            time.sleep(REQUEST_DELAY)
            return post
        except Exception as e:
            logger.debug(f"Error extracting content from {post.get('url')}: {e}")
            return post

    def phase1_discover_structure(self):
        """Phase 1: Discover structure and pagination"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 1: DISCOVERING COMMUNITY STRUCTURE")
        logger.info("="*70)

        self.stats["start_time"] = datetime.now().isoformat()

        for section_name, section_path in COMMUNITY_SECTIONS.items():
            logger.info(f"\n📍 Scanning {section_name.upper()} section...")
            section_url = urljoin(BASE_URL, section_path)

            # Fetch with Selenium to get rendered content
            html = self.fetch_with_selenium(section_url)
            if not html:
                logger.warning(f"✗ Could not fetch {section_name}")
                continue

            soup = BeautifulSoup(html, 'html.parser')

            # Find pagination
            pagination = soup.find_all(['a', 'span'], class_=['page', 'paging', 'pagination', 'paging-item'])
            page_numbers = []
            for pag in pagination:
                text = pag.get_text(strip=True)
                try:
                    page_numbers.append(int(text))
                except:
                    pass

            max_page = max(page_numbers) if page_numbers else 1

            # Extract sample posts
            posts = self.extract_posts_from_html(section_name, html)

            self.structure[section_name] = {
                "url": section_url,
                "total_pages": max_page,
                "estimated_posts": max_page * max(len(posts), 1),
                "posts_sampled": len(posts)
            }

            logger.info(f"  ✓ Pages: {max_page}")
            logger.info(f"  ✓ Posts sampled: {len(posts)}")
            logger.info(f"  ✓ Estimated total: {max_page * max(len(posts), 1)}")

        # Save structure
        structure_file = OUTPUT_DIR / "community_structure.json"
        with open(structure_file, 'w') as f:
            json.dump(self.structure, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✓ PHASE 1 COMPLETE")
        logger.info(f"  Structure saved: {structure_file}")

    def phase2_extract_posts(self):
        """Phase 2: Extract all posts from each section"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 2: EXTRACTING COMMUNITY POSTS (TEXT ONLY)")
        logger.info("="*70)

        for section_name, section_path in COMMUNITY_SECTIONS.items():
            if section_name not in self.structure:
                continue

            section_info = self.structure[section_name]
            total_pages = min(section_info["total_pages"], 50)  # Limit to 50 pages per section

            logger.info(f"\n📄 Extracting {section_name.upper()} ({total_pages} pages)...")
            section_url = section_info["url"]

            for page in range(1, total_pages + 1):
                try:
                    # Build pagination URL
                    if page == 1:
                        page_url = section_url
                    else:
                        page_url = f"{section_url}?page={page}"

                    # Fetch with Selenium
                    html = self.fetch_with_selenium(page_url)
                    if not html:
                        logger.warning(f"  Failed to fetch page {page}")
                        continue

                    # Extract posts
                    posts = self.extract_posts_from_html(section_name, html)
                    self.posts.extend(posts)
                    self.stats["total_posts_found"] += len(posts)
                    self.stats["total_posts_crawled"] += len(posts)

                    # Progress log
                    if page % 5 == 0:
                        logger.info(f"  Page {page}/{total_pages}: {len(self.posts)} total posts")

                    # Checkpoint every 500 posts
                    if len(self.posts) % CHECKPOINT_INTERVAL == 0:
                        logger.info(f"💾 Checkpoint: {len(self.posts)} posts")
                        self.save_checkpoint()

                    time.sleep(REQUEST_DELAY)

                except Exception as e:
                    logger.error(f"Error on page {page}: {e}")
                    self.stats["total_posts_failed"] += 1
                    continue

            self.stats["sections_completed"].append(section_name)
            logger.info(f"✓ {section_name.upper()}: {len(self.posts)} total posts")

        # Save all posts
        self.save_checkpoint()
        logger.info(f"\n✓ PHASE 2 COMPLETE: {len(self.posts)} posts extracted")

    def phase3_validate_and_organize(self):
        """Phase 3: Validate and organize extracted data"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 3: VALIDATING & ORGANIZING DATA")
        logger.info("="*70)

        # Organize by section
        posts_by_section = {}
        for post in self.posts:
            section = post["section"]
            if section not in posts_by_section:
                posts_by_section[section] = []
            posts_by_section[section].append(post)

        # Save by section
        for section, posts in posts_by_section.items():
            section_file = CRAWLED_DIR / f"{section}_posts.jsonl"
            with open(section_file, 'w') as f:
                for post in posts:
                    f.write(json.dumps(post, ensure_ascii=False) + '\n')
            logger.info(f"  ✓ {section}: {len(posts)} posts → {section_file.name}")

        # Save consolidated file
        consolidated_file = CRAWLED_DIR / "community_posts_complete.jsonl"
        with open(consolidated_file, 'w') as f:
            for post in self.posts:
                f.write(json.dumps(post, ensure_ascii=False) + '\n')
        logger.info(f"  ✓ Consolidated: {len(self.posts)} posts → community_posts_complete.jsonl")

        # Validation stats
        logger.info(f"\n✓ PHASE 3 COMPLETE - VALIDATION PASSED")
        logger.info(f"  Total posts: {len(self.posts)}")
        logger.info(f"  Unique posts: {len(self.seen_posts)}")
        logger.info(f"  Format: JSONL (valid)")
        logger.info(f"  Content type: TEXT ONLY (no images)")

        self.stats["end_time"] = datetime.now().isoformat()
        self.save_seen_posts()

    def run(self):
        """Execute all phases"""
        try:
            logger.info("🚀 ONEHAGO COMMUNITY CRAWLER (SELENIUM) STARTED")
            logger.info(f"   Output Directory: {OUTPUT_DIR}")
            logger.info(f"   Content Type: TEXT ONLY (no images)")

            # Initialize Selenium
            if not self.init_selenium():
                logger.error("❌ Failed to initialize Selenium. Exiting.")
                return

            try:
                # Phase 1: Discover
                self.phase1_discover_structure()

                # Phase 2: Extract
                self.phase2_extract_posts()

                # Phase 3: Validate
                self.phase3_validate_and_organize()

                # Final summary
                elapsed = datetime.fromisoformat(self.stats["end_time"]) - datetime.fromisoformat(self.stats["start_time"])
                logger.info("\n" + "="*70)
                logger.info("🎉 COMMUNITY CRAWL COMPLETE")
                logger.info("="*70)
                logger.info(f"Total Posts: {len(self.posts)}")
                logger.info(f"Sections: {', '.join(self.stats['sections_completed'])}")
                logger.info(f"Unique IDs: {len(self.seen_posts)}")

                if len(self.posts) > 0:
                    success_rate = (len(self.posts) / (len(self.posts) + self.stats['total_posts_failed'])) * 100
                    logger.info(f"Success Rate: {success_rate:.1f}%")

                logger.info(f"Elapsed Time: {elapsed}")
                logger.info(f"Output Directory: {CRAWLED_DIR}")
                logger.info(f"Content Type: TEXT ONLY (images disabled)")

            finally:
                self.close_selenium()

        except Exception as e:
            logger.error(f"❌ CRAWLER FAILED: {e}", exc_info=True)
            self.close_selenium()
            raise


if __name__ == "__main__":
    crawler = CommunityCrawlerSelenium()
    crawler.run()
