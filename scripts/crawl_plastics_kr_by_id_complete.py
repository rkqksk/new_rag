#!/usr/bin/env python3
"""
Comprehensive Plastics.kr Crawler - ID-based Discovery
Crawls all articles by systematically testing ID ranges
"""

import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

BASE = "https://www.plastics.kr"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plastics_kr")
OUTPUT_FILE = OUTPUT_DIR / "articles_complete_all_ids.jsonl"
WAIT_TIMEOUT = 10

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

articles = []
processed_ids = set()

print("\n" + "="*70)
print("🚀 PLASTICS.KR COMPLETE CRAWLER - ID-BASED DISCOVERY")
print("="*70)

def setup_driver():
    """Initialize Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver initialized")
        return driver
    except Exception as e:
        print(f"✗ Failed to initialize driver: {e}")
        return None

def extract_article_from_direct_url(driver, article_id, url):
    """Extract article content from direct article URL"""
    try:
        driver.get(url)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract article content
        title_elem = soup.select_one("h1") or soup.select_one("h2")
        title = title_elem.text.strip() if title_elem else ""

        date_elem = soup.select_one(".date") or soup.select_one("span.date")
        date = date_elem.text.strip() if date_elem else ""

        body_elem = soup.select_one("div.content") or soup.select_one("article") or soup.select_one("div[class*='body']")
        body = body_elem.text.strip() if body_elem else ""

        # If no body found with selectors, try broader search
        if not body:
            # Get all text and clean it up
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            body = soup.get_text(separator='\n').strip()
            body = '\n'.join([line.strip() for line in body.split('\n') if line.strip()])

        author_elem = soup.select_one(".author") or soup.select_one("span.writer")
        author = author_elem.text.strip() if author_elem else ""

        # Only save if we got meaningful content
        if body and len(body) > 100:
            article = {
                "title": title,
                "date": date,
                "body": body[:5000],  # Limit body length
                "author": author,
                "url": url,
                "article_id": article_id,
                "type": "news_article"
            }
            return article
        else:
            return None

    except TimeoutException:
        return None
    except Exception as e:
        return None

def save_articles(articles_list):
    """Save all articles to JSONL file"""
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for article in articles_list:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")
        print(f"\n✅ Saved {len(articles_list)} articles to {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"✗ Error saving: {e}")
        return False

def main():
    """Main execution"""
    driver = setup_driver()
    if not driver:
        return 1

    try:
        print("\n📊 PHASE 1: DISCOVERING ARTICLE ID RANGE")
        print("-" * 70)

        # First, test to find the range of valid IDs
        print("Testing ID ranges to find valid articles...")

        # Based on previous test, we know 1400-1605 have content
        # Let's search broader: 1300-1700
        test_ranges = [
            (1100, 1200),
            (1200, 1300),
            (1300, 1400),
            (1400, 1500),
            (1500, 1600),
            (1600, 1700),
        ]

        valid_ids = set()

        for start, end in test_ranges:
            print(f"\nTesting range {start}-{end}...", end=" ", flush=True)
            range_valid = 0

            for article_id in range(start, end + 1, 10):  # Test every 10th ID
                url = f"{BASE}/news/articleView.html?idxno={article_id}"
                article = extract_article_from_direct_url(driver, article_id, url)
                if article:
                    valid_ids.add(article_id)
                    range_valid += 1

            print(f"({range_valid} valid IDs found)")

        print(f"\n✅ Found {len(valid_ids)} potentially valid IDs")

        # Now fetch ALL articles in the valid range
        print("\n📊 PHASE 2: FULL ARTICLE EXTRACTION")
        print("-" * 70)

        if valid_ids:
            min_id = min(valid_ids)
            max_id = max(valid_ids)

            print(f"Crawling articles from ID {min_id} to {max_id}...")
            print(f"(This may take a while...)\n")

            articles_extracted = 0
            for article_id in range(min_id - 100, max_id + 100):
                url = f"{BASE}/news/articleView.html?idxno={article_id}"

                if article_id % 50 == 0:
                    print(f"  Progress: ID {article_id}...", end=" ", flush=True)

                article = extract_article_from_direct_url(driver, article_id, url)
                if article and article_id not in processed_ids:
                    articles.append(article)
                    processed_ids.add(article_id)
                    articles_extracted += 1

                    if article_id % 50 == 0:
                        print(f"({articles_extracted} extracted)", flush=True)

                time.sleep(0.2)  # Rate limiting

            print(f"\n✅ Extracted {articles_extracted} articles")

            # Save results
            if save_articles(articles):
                print(f"\n📊 FINAL STATISTICS")
                print("-" * 70)
                print(f"Total articles extracted: {len(articles)}")
                print(f"File: {OUTPUT_FILE}")

                if OUTPUT_FILE.exists():
                    file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)
                    print(f"File size: {file_size:.2f} MB")

                print("=" * 70)
                print("✨ Crawl complete!")
                return 0
        else:
            print("❌ No valid articles found")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        if articles:
            save_articles(articles)
        return 130

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        if articles:
            save_articles(articles)
        return 1

    finally:
        driver.quit()
        print("\n🛑 Browser closed")

if __name__ == "__main__":
    import sys
    sys.exit(main())
