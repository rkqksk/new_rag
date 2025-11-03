#!/usr/bin/env python3
"""
Selenium-based Plastics.kr Crawler
Purpose: Discover actual pagination and content availability via browser automation
"""

import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configuration
BASE = "https://www.plastics.kr"
CODES = ["S1N1", "S1N2", "S1N3", "S1N4"]
MAX_PAGES = {"S1N1": 5, "S1N2": 2, "S1N3": 2, "S1N4": 5}  # Test with smaller sample first
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plastics_kr")
OUTPUT_FILE = OUTPUT_DIR / "articles_selenium.jsonl"
WAIT_TIMEOUT = 15

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

articles = []
seen_urls = set()
category_stats = {}

def setup_driver():
    """Setup Selenium WebDriver with Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Uncomment for headless mode
    # options.add_argument("--headless")

    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver initialized")
        return driver
    except Exception as e:
        print(f"✗ Failed to initialize Chrome driver: {e}")
        return None

def extract_article_links_selenium(driver, category, page, base_url):
    """Extract article links using Selenium"""
    list_url = f"{base_url}/news/articleList.html?sc_section_code={category}&view_type=sm&page={page}"

    try:
        driver.get(list_url)
        print(f"    Navigating to: {list_url}")

        # Wait for content to load
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.item"))
        )

        time.sleep(2)  # Extra wait for JS to fully render

        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        items = soup.select("div.item")
        print(f"    Found {len(items)} items")

        links = []
        for item in items:
            article_links = item.find_all("a", href=lambda x: x and "articleView" in x and "idxno=" in x)

            for link_elem in article_links:
                href = link_elem.get("href", "")

                # Construct full URL
                if href.startswith("/"):
                    detail_url = base_url + href
                else:
                    detail_url = href

                # Skip if already seen
                if detail_url in seen_urls:
                    continue

                seen_urls.add(detail_url)

                title = link_elem.text.strip() if link_elem else ""
                date_elem = item.select_one("span.date")
                date = date_elem.text.strip() if date_elem else ""

                links.append({
                    "title": title,
                    "date": date,
                    "url": detail_url
                })

        print(f"    Extracted {len(links)} unique article links")
        return links

    except TimeoutException:
        print(f"    ⚠️ Timeout waiting for content to load")
        return []
    except Exception as e:
        print(f"    ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_article_content(driver, article_url):
    """Extract article content using Selenium"""
    try:
        driver.get(article_url)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.article-body"))
        )

        time.sleep(1)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Extract fields
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
        print(f"      ✗ Error parsing: {e}")
        return None

def crawl_category(driver, category_code):
    """Crawl all pages for a category"""
    category_name = {
        "S1N1": "뉴스 (Latest News)",
        "S1N2": "인사이트 (Insights)",
        "S1N3": "오피니언 (Opinion)",
        "S1N4": "TECH"
    }.get(category_code, category_code)

    max_pages = MAX_PAGES[category_code]
    articles_count = 0

    print(f"\n📄 {category_code} - {category_name} ({max_pages} pages)")
    print("=" * 60)

    for page in range(1, max_pages + 1):
        print(f"  Page {page}/{max_pages}...", end=" ", flush=True)

        article_links = extract_article_links_selenium(driver, category_code, page, BASE)

        if not article_links:
            print("(0 articles)")
            continue

        print(f"Processing {len(article_links)} articles...")

        for i, link_info in enumerate(article_links):
            print(f"    Article {i+1}/{len(article_links)}: {link_info['url'][-50:]}", end=" ")

            content = extract_article_content(driver, link_info["url"])
            if not content or not content.get("body"):
                print("(extraction failed)")
                continue

            article = {
                "title": content["title"] or link_info["title"],
                "date": content["date"] or link_info["date"],
                "body": content["body"],
                "author": content["author"],
                "url": link_info["url"],
                "category": category_code,
                "type": "news_article"
            }

            articles.append(article)
            articles_count += 1
            print(f"(✓ {len(content['body'])} chars)")

            time.sleep(1)  # Respectful rate limiting

        print(f"  ✓ Page {page}: {len(article_links)} items processed")

    category_stats[category_code] = articles_count
    print(f"  📊 {category_name}: {articles_count} articles extracted")

    return articles_count

def save_articles():
    """Save articles to JSONL file"""
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")

        print(f"\n✅ Saved {len(articles)} articles to {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"✗ Error saving articles: {e}")
        return False

def print_summary():
    """Print execution summary"""
    total_pages = sum(MAX_PAGES.values())

    print("\n" + "=" * 60)
    print("📊 SELENIUM CRAWL SUMMARY")
    print("=" * 60)
    print(f"Total articles extracted: {len(articles)}")
    print(f"Total pages processed: {total_pages}")
    print(f"Categories covered: {len(category_stats)}")

    if OUTPUT_FILE.exists():
        file_size = OUTPUT_FILE.stat().st_size
        size_mb = file_size / (1024 * 1024)
        print(f"File size: {size_mb:.2f} MB")

    print("\nCategory breakdown:")
    for code in CODES:
        count = category_stats.get(code, 0)
        max_p = MAX_PAGES[code]
        print(f"  {code}: {count} articles ({max_p} pages)")

    print("=" * 60)

def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print("🚀 PLASTICS.KR SELENIUM CRAWLER")
    print("=" * 60)
    print(f"Target: {BASE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"JavaScript rendering: ENABLED")

    driver = setup_driver()
    if not driver:
        print("✗ Failed to initialize driver. Exiting.")
        return 1

    try:
        # Crawl each category
        for code in CODES:
            crawl_category(driver, code)

        # Save results
        if articles:
            save_articles()
            print_summary()
            print("\n✨ Crawl complete!")
            return 0
        else:
            print("\n⚠️  No articles extracted.")
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
    import sys
    sys.exit(main())
