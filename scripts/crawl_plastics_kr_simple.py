#!/usr/bin/env python3
"""
Minimal Plastics.kr News Crawler
Based on PLASTICS_KR_SIMPLE_PLAN.md
Purpose: Extract all text articles from 4 categories
Target: ~700-1000 articles across 59 pages
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
from pathlib import Path

# Configuration
BASE = "https://www.plastics.kr"
CODES = ["S1N1", "S1N2", "S1N3", "S1N4"]
MAX_PAGES = {"S1N1": 50, "S1N2": 2, "S1N3": 2, "S1N4": 5}
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plastics_kr")
OUTPUT_FILE = OUTPUT_DIR / "articles.jsonl"
RATE_LIMIT = 1  # seconds between requests

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Main data structures
articles = []
seen_urls = set()  # Changed from seen_ids to seen_urls to properly track duplicates
category_stats = {}

def fetch_page(url, timeout=10):
    """Fetch page with error handling"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return None

def extract_article_links(html, category, base_url):
    """Extract article links from list page"""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Find all items with class 'item' (actual structure on plastics.kr)
        items = soup.select("div.item")

        links = []
        for item in items:
            # Find all article links with articleView in href
            article_links = item.find_all("a", href=lambda x: x and "articleView" in x and "idxno=" in x)

            for link_elem in article_links:
                href = link_elem.get("href", "")

                # Construct full detail URL first
                if href.startswith("/"):
                    detail_url = base_url + href
                else:
                    detail_url = href

                # Skip if URL already seen (proper deduplication)
                if detail_url in seen_urls:
                    continue

                seen_urls.add(detail_url)

                # Extract article ID (optional, for logging)
                try:
                    article_id = href.split("idxno=")[1].split("&")[0]
                except (IndexError, ValueError):
                    article_id = "unknown"

                # Get article title
                title = link_elem.text.strip() if link_elem else ""

                # Try to find date (look in item or parent)
                date_elem = item.select_one("span.date") or item.select_one("span.publish-date")
                date = date_elem.text.strip() if date_elem else ""

                # Construct full detail URL
                if href.startswith("/"):
                    detail_url = base_url + href
                else:
                    detail_url = href

                links.append({
                    "article_id": article_id,
                    "title": title,
                    "date": date,
                    "url": detail_url
                })

        return links

    except Exception as e:
        print(f"  ✗ Error parsing list page: {e}")
        return []

def extract_article_content(html, article_url):
    """Extract article content from detail page"""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Extract title (try multiple selectors)
        title_elem = soup.select_one("div.article-title") or soup.select_one("h1.title") or soup.select_one("h1")
        title = title_elem.text.strip() if title_elem else ""

        # Extract date (try multiple selectors)
        date_elem = soup.select_one("div.article-date") or soup.select_one("span.date") or soup.select_one("span.publish-date")
        date = date_elem.text.strip() if date_elem else ""

        # Extract body content
        body_elem = soup.select_one("div.article-body") or soup.select_one("div.content") or soup.select_one("div#article-content")
        body = body_elem.text.strip() if body_elem else ""

        # Extract author (optional)
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
        print(f"  ✗ Error parsing detail page: {e}")
        return None

def crawl_category(category_code):
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
        # Build list page URL
        list_url = f"{BASE}/news/articleList.html?sc_section_code={category_code}&view_type=sm&page={page}"

        print(f"  Page {page}/{max_pages}...", end=" ", flush=True)

        # Fetch list page
        html = fetch_page(list_url)
        if not html:
            print("⚠️  Skipped")
            continue

        # Extract article links from list page
        article_links = extract_article_links(html, category_code, BASE)

        if not article_links:
            print("(0 articles)")
            continue

        # Process each article
        for link_info in article_links:
            # Fetch detail page
            detail_html = fetch_page(link_info["url"])
            if not detail_html:
                continue

            # Extract content
            content = extract_article_content(detail_html, link_info["url"])
            if not content:
                continue

            # Create article record
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

            # Respectful rate limiting
            time.sleep(RATE_LIMIT)

        print(f"✓ ({len(article_links)} items)")

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
    print("📊 CRAWL SUMMARY")
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

def validate_output():
    """Validate output data quality"""
    if not articles:
        print("⚠️  No articles extracted!")
        return False

    print("\n🔍 Validating output...")
    print("-" * 60)

    # Check for required fields
    required_fields = ["title", "date", "body", "url", "category"]

    empty_count = {field: 0 for field in required_fields}

    for article in articles:
        for field in required_fields:
            if not article.get(field):
                empty_count[field] += 1

    print("Field completeness:")
    for field, count in empty_count.items():
        percentage = 100 * (len(articles) - count) / len(articles)
        status = "✓" if percentage > 90 else "⚠️"
        print(f"  {status} {field}: {percentage:.1f}% complete")

    # Show sample
    if articles:
        print("\n📋 Sample article (first):")
        print("-" * 60)
        sample = articles[0]
        print(f"Title: {sample['title'][:60]}...")
        print(f"Date: {sample['date']}")
        print(f"Body length: {len(sample['body'])} chars")
        print(f"Category: {sample['category']}")
        print(f"URL: {sample['url']}")

    print("-" * 60)
    return True

def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print("🚀 PLASTICS.KR MINIMAL CRAWLER")
    print("=" * 60)
    print(f"Target: {BASE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Rate limit: {RATE_LIMIT}s between requests")

    try:
        # Crawl each category
        for code in CODES:
            crawl_category(code)

        # Save results
        if articles:
            save_articles()
            validate_output()
            print_summary()
            print("\n✨ Crawl complete!")
            return 0
        else:
            print("\n⚠️  No articles extracted. Check selectors on actual website.")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print(f"Partial results ({len(articles)} articles) saved to {OUTPUT_FILE}")
        if articles:
            save_articles()
        return 130

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
