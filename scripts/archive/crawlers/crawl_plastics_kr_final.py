#!/usr/bin/env python3
"""
Final Plastics.kr Crawler - Correct Implementation
Purpose: Extract ALL articles from plastics.kr with proper pagination handling
Key Insight: Website displays the same article pool across all categories/views
"""

import time
import json
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# Configuration
BASE = "https://www.plastics.kr"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plastics_kr")
OUTPUT_FILE = OUTPUT_DIR / "articles_complete.jsonl"
WAIT_TIMEOUT = 15

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

articles = []
seen_urls = set()

print("\n" + "=" * 70)
print("🚀 PLASTICS.KR FINAL CRAWLER - SELENIUM WITH PAGINATION")
print("=" * 70)

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

def extract_all_articles_with_scrolling(driver):
    """
    Extract all articles by scrolling through paginated content.
    The website shows 19 articles per page initially, need to scroll/paginate for more.
    """
    articles_found = 0

    # Start on page 1
    page = 1
    max_pages = 50  # Safety limit

    while page <= max_pages:
        list_url = f"{BASE}/news/articleList.html?sc_section_code=S1N1&view_type=sm&page={page}"
        print(f"\nPage {page}: {list_url}")

        try:
            driver.get(list_url)
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.item"))
            )

            time.sleep(2)  # Wait for JS to fully render

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            items = soup.select("div.item")

            print(f"  Found {len(items)} item containers")

            # Extract all article links from this page
            page_article_links = []
            for item in items:
                # Look for all links with articleView
                article_links = item.find_all("a", href=lambda x: x and "articleView" in x and "idxno=" in x)

                for link_elem in article_links:
                    href = link_elem.get("href", "")

                    # Construct full URL
                    if href.startswith("/"):
                        detail_url = BASE + href
                    elif not href.startswith("http"):
                        detail_url = BASE + href if href.startswith("/") else BASE + "/" + href
                    else:
                        detail_url = href

                    # Skip if already seen
                    if detail_url in seen_urls:
                        print(f"    ⊘ Skipped duplicate: {detail_url[-40:]}")
                        continue

                    seen_urls.add(detail_url)

                    title = link_elem.text.strip()[:60]
                    page_article_links.append({"title": title, "url": detail_url})

            if not page_article_links:
                print(f"  ⚠️  No new articles on this page. Stopping pagination.")
                break

            print(f"  ✓ Found {len(page_article_links)} unique articles on this page")

            # Extract content from each article
            for i, link_info in enumerate(page_article_links):
                print(f"    [{i+1}/{len(page_article_links)}] Extracting: {link_info['url'][-50:]}", end=" ")

                content = extract_article_content(driver, link_info["url"])
                if not content or not content.get("body"):
                    print("(extraction failed)")
                    continue

                article = {
                    "title": content["title"] or link_info["title"],
                    "date": content["date"],
                    "body": content["body"],
                    "author": content["author"],
                    "url": link_info["url"],
                    "category": "S1N1",
                    "type": "news_article"
                }

                articles.append(article)
                articles_found += 1
                print(f"(✓ {len(content['body'])} chars)")

                time.sleep(0.5)  # Respectful rate limiting

            page += 1

        except TimeoutException:
            print(f"  ⚠️  Timeout on page {page}")
            break
        except Exception as e:
            print(f"  ✗ Error on page {page}: {e}")
            break

    return articles_found

def extract_article_content(driver, article_url):
    """Extract full article content"""
    try:
        driver.get(article_url)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.article-body"))
        )

        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract fields with fallback selectors
        title_elem = soup.select_one("div.article-title") or soup.select_one("h1.title") or soup.select_one("h1")
        title = title_elem.text.strip() if title_elem else ""

        date_elem = soup.select_one("div.article-date") or soup.select_one("span.date")
        date = date_elem.text.strip() if date_elem else ""

        body_elem = soup.select_one("div.article-body") or soup.select_one("div.content")
        body = body_elem.text.strip() if body_elem else ""

        author_elem = soup.select_one("span.writer") or soup.select_one("span.author")
        author = author_elem.text.strip() if author_elem else ""

        return {
            "title": title,
            "date": date,
            "body": body,
            "author": author,
            "url": article_url
        }

    except Exception as e:
        print(f"        ✗ Extraction error: {e}")
        return None

def save_articles():
    """Save all articles to JSONL file"""
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")

        print(f"\n✅ Saved {len(articles)} articles to {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"✗ Error saving: {e}")
        return False

def print_summary():
    """Print summary statistics"""
    print("\n" + "=" * 70)
    print("📊 FINAL CRAWL SUMMARY")
    print("=" * 70)
    print(f"Total unique articles extracted: {len(articles)}")
    print(f"Total article URLs crawled: {len(seen_urls)}")

    if OUTPUT_FILE.exists():
        file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        print(f"File size: {file_size:.2f} MB")

    if articles:
        print(f"\nSample article:")
        sample = articles[0]
        print(f"  Title: {sample['title'][:60]}...")
        print(f"  URL: {sample['url']}")
        print(f"  Body length: {len(sample['body'])} characters")

    print("=" * 70)

def main():
    """Main execution"""
    print(f"Target: {BASE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"JavaScript rendering: ENABLED")
    print(f"Pagination strategy: Automated page navigation")

    driver = setup_driver()
    if not driver:
        print("✗ Failed to initialize driver")
        return 1

    try:
        total_articles = extract_all_articles_with_scrolling(driver)

        if articles:
            save_articles()
            print_summary()
            print("\n✨ Crawl complete!")
            return 0
        else:
            print("\n⚠️  No articles extracted")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        if articles:
            save_articles()
        return 130

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        driver.quit()
        print("\n🛑 Browser closed")

if __name__ == "__main__":
    sys.exit(main())
