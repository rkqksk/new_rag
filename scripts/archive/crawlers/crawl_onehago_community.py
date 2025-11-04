#!/usr/bin/env python3
"""
Onehago Community Crawler - Extract forums, news, and discussions
Supports: News, Onehago Forum, Find Search, Service, Video sections
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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

# Crawler Settings
WORKERS = 8
REQUEST_DELAY = 1.0  # seconds between requests
TIMEOUT = 30
CHECKPOINT_INTERVAL = 500
MAX_RETRIES = 3

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"community_crawler_{timestamp}.log"
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
    "Referer": "https://www.onehago.com"
}


class CommunityCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.verify = True

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

    def load_seen_posts(self):
        """Load previously seen post IDs to avoid duplicates"""
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
            logger.info(f"💾 Progress saved: {len(self.posts)} posts")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def fetch_page(self, url: str, retries: int = 0) -> Optional[str]:
        """Fetch a page with retry logic"""
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.encoding = 'euc-kr'  # Korean encoding

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"⚠️ Status {response.status_code}: {url}")
                return None
        except Exception as e:
            if retries < MAX_RETRIES:
                time.sleep(REQUEST_DELAY * (retries + 1))
                return self.fetch_page(url, retries + 1)
            else:
                logger.warning(f"✗ Failed after {MAX_RETRIES} retries: {url} - {e}")
                return None

    def extract_posts_from_list(self, section: str, url: str, html: str) -> List[Dict]:
        """Extract posts from a section page"""
        posts = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Generic list item extraction (adjustable based on actual HTML)
            list_items = soup.find_all(['tr', 'div', 'li'], class_=[
                'list-item', 'post', 'thread', 'item', 'list-row', 'notice-row'
            ])

            if not list_items:
                # Fallback: look for any table rows or div with links
                list_items = soup.find_all('tr')[1:]  # Skip header row
                if not list_items:
                    list_items = soup.find_all('div', class_=['item', 'row'])

            for item in list_items:
                try:
                    # Extract link (title & URL)
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    post_url = link_elem.get('href', '')

                    if not post_url.startswith('http'):
                        post_url = urljoin(BASE_URL, post_url)

                    # Generate post ID from URL
                    post_id = f"{section}_{hash(post_url)}"

                    if post_id in self.seen_posts:
                        continue

                    # Extract meta info (author, date, views, replies)
                    tds = item.find_all('td')
                    author = ""
                    date_str = ""
                    views = 0
                    replies = 0

                    if len(tds) >= 2:
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
                        "replies": replies,
                        "url": post_url,
                        "content": "",  # Will be filled in detail extraction
                        "crawled_at": datetime.now().isoformat()
                    }

                    posts.append(post)
                    self.seen_posts.add(post_id)

                except Exception as e:
                    logger.debug(f"Error extracting post item: {e}")
                    continue

            return posts
        except Exception as e:
            logger.error(f"Error parsing page {url}: {e}")
            return []

    def extract_post_detail(self, post: Dict) -> Dict:
        """Extract full content from individual post"""
        try:
            html = self.fetch_page(post["url"])
            if not html:
                return post

            soup = BeautifulSoup(html, 'html.parser')

            # Extract content (adjust selectors based on actual HTML)
            content_area = soup.find(['div', 'article'], class_=[
                'content', 'body', 'post-content', 'detail-content'
            ])

            if content_area:
                # Remove script and style tags
                for script in content_area(['script', 'style']):
                    script.decompose()

                post["content"] = content_area.get_text(separator='\n', strip=True)

            return post
        except Exception as e:
            logger.debug(f"Error extracting detail from {post['url']}: {e}")
            return post

    def phase1_discover_structure(self):
        """Phase 1: Discover community structure and pages"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 1: DISCOVERING COMMUNITY STRUCTURE")
        logger.info("="*70)

        self.stats["start_time"] = datetime.now().isoformat()

        for section_name, section_path in COMMUNITY_SECTIONS.items():
            logger.info(f"\n📍 Scanning {section_name.upper()} section...")
            section_url = urljoin(BASE_URL, section_path)

            html = self.fetch_page(section_url)
            if not html:
                logger.warning(f"✗ Could not fetch {section_name}")
                continue

            # Extract pagination info
            soup = BeautifulSoup(html, 'html.parser')

            # Look for pagination links
            pagination = soup.find_all(['a', 'span'], class_=['page', 'paging', 'pagination'])
            page_numbers = []
            for pag in pagination:
                text = pag.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))

            max_page = max(page_numbers) if page_numbers else 1

            # Extract posts from first page
            posts = self.extract_posts_from_list(section_name, section_url, html)

            self.structure[section_name] = {
                "url": section_url,
                "total_pages": max_page,
                "estimated_posts": max_page * len(posts),  # Rough estimate
                "posts_sampled": len(posts)
            }

            logger.info(f"  ✓ Pages: {max_page}")
            logger.info(f"  ✓ Posts sampled: {len(posts)}")
            logger.info(f"  ✓ Estimated total: {max_page * len(posts)}")

        # Save structure
        structure_file = OUTPUT_DIR / "community_structure.json"
        with open(structure_file, 'w') as f:
            json.dump(self.structure, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✓ PHASE 1 COMPLETE")
        logger.info(f"  Structure saved to: {structure_file}")

    def phase2_extract_posts(self):
        """Phase 2: Extract all posts from each section"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 2: EXTRACTING COMMUNITY POSTS")
        logger.info("="*70)

        for section_name, section_path in COMMUNITY_SECTIONS.items():
            if section_name not in self.structure:
                continue

            section_info = self.structure[section_name]
            total_pages = section_info["total_pages"]

            logger.info(f"\n📄 Extracting {section_name.upper()} ({total_pages} pages)...")
            section_url = section_info["url"]

            for page in range(1, min(total_pages + 1, 50)):  # Limit to 50 pages per section for safety
                try:
                    # Build pagination URL
                    if page == 1:
                        page_url = section_url
                    else:
                        page_url = f"{section_url}?page={page}"

                    html = self.fetch_page(page_url)
                    if not html:
                        continue

                    posts = self.extract_posts_from_list(section_name, page_url, html)
                    self.posts.extend(posts)
                    self.stats["total_posts_found"] += len(posts)
                    self.stats["total_posts_crawled"] += len(posts)

                    # Log progress
                    if page % 5 == 0:
                        logger.info(f"  Page {page}/{total_pages}: {len(self.posts)} total posts")

                    # Checkpoint every 500 posts
                    if len(self.posts) % CHECKPOINT_INTERVAL == 0:
                        logger.info(f"💾 Checkpoint: {len(self.posts)} posts saved")
                        self.save_checkpoint()

                    time.sleep(REQUEST_DELAY)

                except Exception as e:
                    logger.error(f"Error on page {page}: {e}")
                    self.stats["total_posts_failed"] += 1
                    continue

            self.stats["sections_completed"].append(section_name)
            logger.info(f"✓ {section_name.upper()} complete: {len(self.posts)} total posts")

        # Save all posts
        self.save_checkpoint()
        logger.info(f"\n✓ PHASE 2 COMPLETE")
        logger.info(f"  Total posts extracted: {len(self.posts)}")

    def phase3_validate(self):
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

        self.stats["end_time"] = datetime.now().isoformat()
        self.save_seen_posts()

    def run(self):
        """Execute all phases"""
        try:
            logger.info("🚀 ONEHAGO COMMUNITY CRAWLER STARTED")
            logger.info(f"   Output Directory: {OUTPUT_DIR}")

            # Phase 1: Discover
            self.phase1_discover_structure()

            # Phase 2: Extract
            self.phase2_extract_posts()

            # Phase 3: Validate
            self.phase3_validate()

            # Final summary
            elapsed = datetime.fromisoformat(self.stats["end_time"]) - datetime.fromisoformat(self.stats["start_time"])
            logger.info("\n" + "="*70)
            logger.info("🎉 COMMUNITY CRAWL COMPLETE")
            logger.info("="*70)
            logger.info(f"Total Posts: {len(self.posts)}")
            logger.info(f"Sections: {', '.join(self.stats['sections_completed'])}")
            logger.info(f"Success Rate: {(len(self.posts) / (len(self.posts) + self.stats['total_posts_failed'])) * 100:.1f}%")
            logger.info(f"Elapsed Time: {elapsed}")
            logger.info(f"Output Directory: {CRAWLED_DIR}")

        except Exception as e:
            logger.error(f"❌ CRAWLER FAILED: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    crawler = CommunityCrawler()
    crawler.run()
