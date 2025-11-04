#!/usr/bin/env python3
"""
🔍 PLASTICS.KR STRUCTURAL ANALYSIS
Analyze URL patterns and page structure to develop crawling strategies
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import json
from collections import defaultdict

BASE_URL = "https://www.plastics.kr"

# Target categories with page ranges
CATEGORIES = {
    "S1N1": {
        "name": "News - S1N1",
        "url_template": "https://www.plastics.kr/news/articleList.html?sc_section_code=S1N1&view_type=sm",
        "estimated_pages": "1-50",
        "description": "Main news category (largest)"
    },
    "S1N2": {
        "name": "News - S1N2",
        "url_template": "https://www.plastics.kr/news/articleList.html?sc_section_code=S1N2&view_type=sm",
        "estimated_pages": "1-2",
        "description": "Sub-category 2"
    },
    "S1N3": {
        "name": "News - S1N3",
        "url_template": "https://www.plastics.kr/news/articleList.html?sc_section_code=S1N3&view_type=sm",
        "estimated_pages": "1-2",
        "description": "Sub-category 3"
    },
    "S1N4": {
        "name": "News - S1N4",
        "url_template": "https://www.plastics.kr/news/articleList.html?sc_section_code=S1N4&view_type=sm",
        "estimated_pages": "1-5",
        "description": "Sub-category 4"
    }
}

def fetch_page(url):
    """Fetch page with proper headers"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url, timeout=10, headers=headers)

        # Handle encoding
        if response.encoding is None or 'utf' not in response.encoding.lower():
            try:
                response.encoding = 'utf-8'
            except:
                pass

        if response.status_code == 200:
            return response.text
        print(f"⚠️ Status {response.status_code}: {url}")
        return None
    except Exception as e:
        print(f"❌ Fetch error: {str(e)[:100]}")
        return None

def analyze_listing_page(html, category_key):
    """Analyze article listing page structure"""
    soup = BeautifulSoup(html, 'html.parser')

    print(f"\n{'='*80}")
    print(f"📄 ANALYZING: {CATEGORIES[category_key]['name']}")
    print(f"{'='*80}\n")

    # 1. Find article links
    print("🔗 ARTICLE LINKS DETECTION:")
    article_links = []

    # Look for common patterns
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for article patterns
        if 'article' in href.lower() or 'view' in href.lower() or 'detail' in href.lower():
            if text and len(text) > 3:  # Has meaningful text
                article_links.append({
                    'url': href,
                    'text': text[:60],
                    'pattern': 'article_link'
                })

    print(f"  • Total potential article links: {len(article_links)}")
    if article_links:
        print(f"  Sample links:")
        for link in article_links[:3]:
            print(f"    - {link['text'][:50]}")
            print(f"      URL: {link['url'][:80]}")

    # 2. Analyze HTML structure
    print("\n📊 HTML STRUCTURE ANALYSIS:")

    # Check for div-based layout
    divs = soup.find_all('div')
    print(f"  • Total DIVs: {len(divs)}")

    # Check for list elements
    lists = soup.find_all(['ul', 'ol'])
    print(f"  • List elements (ul/ol): {len(lists)}")

    # Check for table elements
    tables = soup.find_all('table')
    print(f"  • Tables: {len(tables)}")

    # Check for article-like elements
    articles = soup.find_all('article')
    print(f"  • Article tags: {len(articles)}")

    # Check for specific class patterns
    print("\n🎯 CLASS/ID PATTERNS:")
    class_pattern = defaultdict(int)
    for elem in soup.find_all(class_=True):
        classes = elem.get('class', [])
        for cls in classes:
            if 'article' in cls.lower() or 'item' in cls.lower() or 'post' in cls.lower():
                class_pattern[cls] += 1

    if class_pattern:
        print(f"  Relevant class patterns:")
        for cls, count in sorted(class_pattern.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    • {cls}: {count}")
    else:
        print(f"  (No obvious article/item class patterns found)")

    # 3. Pagination detection
    print("\n📄 PAGINATION DETECTION:")
    page_links = []

    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for page parameters
        if 'page' in href.lower():
            page_links.append({
                'url': href,
                'text': text,
                'param': 'page'
            })

    print(f"  • Page links found: {len(page_links)}")
    if page_links:
        print(f"  Sample pagination links:")
        for link in page_links[:3]:
            print(f"    - {link['text']}: {link['url'][:80]}")

    # 4. Content indicators
    print("\n📝 CONTENT TYPE INDICATORS:")
    print(f"  • Total paragraphs: {len(soup.find_all('p'))}")
    print(f"  • Total headings (h1-h6): {len(soup.find_all(['h1','h2','h3','h4','h5','h6']))}")
    print(f"  • Total images: {len(soup.find_all('img'))}")
    print(f"  • Total spans: {len(soup.find_all('span'))}")

    return {
        'category': category_key,
        'article_links': len(article_links),
        'divs': len(divs),
        'lists': len(lists),
        'tables': len(tables),
        'articles': len(articles),
        'pages': len(page_links),
        'sample_articles': article_links[:3]
    }

def main():
    print("\n" + "="*80)
    print("🔍 PLASTICS.KR STRUCTURAL ANALYSIS & STRATEGY DEVELOPMENT")
    print("="*80)
    print("\nTarget: https://www.plastics.kr/news/")
    print("Categories: 4 (S1N1, S1N2, S1N3, S1N4)")
    print("Estimated articles: 1000+ (S1N1: ~50 pages)")

    results = {}

    # Analyze each category (test first page only)
    for category_key, category_info in CATEGORIES.items():
        print(f"\n\n🌐 Fetching {category_info['name']}...")
        html = fetch_page(category_info['url_template'])

        if html:
            result = analyze_listing_page(html, category_key)
            results[category_key] = result
        else:
            print(f"❌ Failed to fetch {category_key}")

    # Save analysis
    output_file = "/Users/oypnus/Project/rag-enterprise/data/plastics_kr_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\n{'='*80}")
    print("✅ ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to: {output_file}")

    # Summary
    print("\n📊 SUMMARY:")
    for cat_key, result in results.items():
        print(f"\n{CATEGORIES[cat_key]['name']}:")
        print(f"  • Article links found: {result['article_links']}")
        print(f"  • Pagination links: {result['pages']}")

if __name__ == "__main__":
    main()
