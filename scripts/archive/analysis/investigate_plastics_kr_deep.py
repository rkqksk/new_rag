#!/usr/bin/env python3
"""
Deep investigation of plastics.kr structure to find all ~1000 articles
Purpose: Discover the actual crawling strategy needed
"""

import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

BASE = "https://www.plastics.kr"
WAIT_TIMEOUT = 15

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

def investigate_home_page(driver):
    """Investigate the main page to find all categories and sections"""
    print("\n" + "="*70)
    print("🔍 INVESTIGATING HOMEPAGE STRUCTURE")
    print("="*70)

    driver.get(BASE)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find all navigation links
    print("\n📍 Navigation Links Found:")
    nav_links = soup.find_all("a", href=lambda x: x and "articleList" in x)
    unique_categories = set()

    for link in nav_links:
        href = link.get("href", "")
        text = link.text.strip()
        if "sc_section_code=" in href:
            # Extract category code
            code = href.split("sc_section_code=")[1].split("&")[0]
            unique_categories.add(code)
            print(f"  - {text}: {code}")

    print(f"\n✅ Total Unique Categories Found: {len(unique_categories)}")
    print(f"   Categories: {sorted(unique_categories)}")

    return sorted(unique_categories)

def investigate_pagination_limits(driver, category_code):
    """Test pagination to find actual article limits"""
    print(f"\n📖 TESTING CATEGORY: {category_code}")
    print("-" * 70)

    all_articles_found = set()
    page = 1
    consecutive_empty_pages = 0
    max_consecutive_empty = 3

    while consecutive_empty_pages < max_consecutive_empty and page <= 200:
        list_url = f"{BASE}/news/articleList.html?sc_section_code={category_code}&view_type=sm&page={page}"

        print(f"  Page {page}...", end=" ", flush=True)

        try:
            driver.get(list_url)
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.item"))
            )
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.select("div.item")

            # Extract articles
            page_articles = []
            for item in items:
                article_links = item.find_all("a", href=lambda x: x and "articleView" in x and "idxno=" in x)
                for link in article_links:
                    href = link.get("href", "")
                    if href.startswith("/"):
                        detail_url = BASE + href
                    else:
                        detail_url = href

                    # Extract ID
                    try:
                        article_id = href.split("idxno=")[1].split("&")[0]
                        page_articles.append((article_id, detail_url))
                        all_articles_found.add(article_id)
                    except:
                        pass

            if len(page_articles) == 0:
                consecutive_empty_pages += 1
                print(f"(empty, consecutive: {consecutive_empty_pages})")
            else:
                consecutive_empty_pages = 0
                print(f"({len(page_articles)} articles, total: {len(all_articles_found)})")

            page += 1

        except TimeoutException:
            print("(timeout)")
            break
        except Exception as e:
            print(f"(error: {e})")
            break

    print(f"\n  ✅ Category {category_code}: {len(all_articles_found)} unique articles found")
    return all_articles_found

def investigate_alternative_urls(driver):
    """Test alternative URL patterns that might have more articles"""
    print("\n" + "="*70)
    print("🔎 TESTING ALTERNATIVE URL PATTERNS")
    print("="*70)

    patterns = [
        # Different view types
        "{}/news/articleList.html?sc_section_code=S1N1&view_type=sm&page=1",
        "{}/news/articleList.html?sc_section_code=S1N1&view_type=list&page=1",

        # Different sorting
        "{}/news/articleList.html?sc_section_code=S1N1&sort=date&page=1",
        "{}/news/articleList.html?sc_section_code=S1N1&sort=popular&page=1",

        # Different parameters
        "{}/news/articleList.html?sc_section_code=&page=1",
        "{}/news/articleList.html?page=1",

        # Different base paths
        "{}/news/?page=1",
        "{}/news/list.html?page=1",
    ]

    for pattern in patterns:
        url = pattern.format(BASE)
        print(f"\n🔗 Testing: {url}")

        try:
            driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.select("div.item")

            if items:
                print(f"   ✅ Found {len(items)} items")
                # Get first 3 article links
                links = soup.find_all("a", href=lambda x: x and "articleView" in x)[:3]
                for i, link in enumerate(links, 1):
                    print(f"      {i}. {link.text.strip()[:60]}")
            else:
                print(f"   ⚠️  No items found")

        except Exception as e:
            print(f"   ✗ Error: {e}")

def investigate_search_functionality(driver):
    """Check if there's a search function that might reveal total article count"""
    print("\n" + "="*70)
    print("🔍 CHECKING SEARCH FUNCTIONALITY")
    print("="*70)

    # Look for search endpoints
    driver.get(BASE)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find search forms
    search_forms = soup.find_all("form")
    print(f"\n📝 Found {len(search_forms)} forms")

    for i, form in enumerate(search_forms, 1):
        print(f"\nForm {i}:")
        print(f"  Action: {form.get('action', 'N/A')}")
        print(f"  Method: {form.get('method', 'N/A')}")

        inputs = form.find_all("input")
        for inp in inputs:
            print(f"  - {inp.get('name', 'unnamed')}: {inp.get('type', 'unknown')}")

def main():
    """Main investigation"""
    print("\n" + "="*70)
    print("🚀 PLASTICS.KR DEEP INVESTIGATION - FINDING ALL ~1000 ARTICLES")
    print("="*70)

    driver = setup_driver()
    if not driver:
        return 1

    try:
        # Phase 1: Discover all categories
        categories = investigate_home_page(driver)

        # Phase 2: Test pagination for each category
        print("\n" + "="*70)
        print("📊 PAGINATION TESTING")
        print("="*70)

        all_articles_across_categories = {}
        total_unique_articles = set()

        for category in categories:
            articles = investigate_pagination_limits(driver, category)
            all_articles_across_categories[category] = articles
            total_unique_articles.update(articles)
            time.sleep(1)  # Rate limiting

        # Phase 3: Test alternative URLs
        investigate_alternative_urls(driver)

        # Phase 4: Check search functionality
        investigate_search_functionality(driver)

        # Summary
        print("\n" + "="*70)
        print("📊 INVESTIGATION SUMMARY")
        print("="*70)

        print(f"\n✅ Categories Tested: {len(categories)}")
        for category in sorted(categories):
            count = len(all_articles_across_categories[category])
            print(f"   {category}: {count} articles")

        print(f"\n✅ Total Unique Articles Across All Categories: {len(total_unique_articles)}")

        if len(total_unique_articles) < 100:
            print("\n⚠️  WARNING: Only found <100 articles")
            print("   This suggests the crawling strategy is still incorrect")
            print("   Possible reasons:")
            print("   - CSS selectors are not capturing all articles")
            print("   - Articles are loaded dynamically via JavaScript")
            print("   - There are additional pages or sections not tested")
            print("   - The pagination limit is higher than expected")
        elif len(total_unique_articles) >= 900:
            print("\n✅ SUCCESS: Found ~1000 articles as expected!")
        else:
            print(f"\n🔄 PARTIAL: Found {len(total_unique_articles)} articles")
            print("   Need to investigate further to find remaining articles")

        print("\n" + "="*70)

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
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
