#!/usr/bin/env python3
"""
🔍 PLASTICNET STRUCTURAL ANALYSIS
Analyze HTML/TABLE structure across categories to understand:
1. TABLE-based layout patterns
2. Content type variations (text-only, photo+text, photo-only)
3. Pagination structure
4. Category-specific differences
"""

import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from collections import defaultdict

BASE_URL = "https://plasticnet.kr"

PLASTICNET_CATEGORIES = {
    "1": {
        "name": "폴리프로필렌/PP 재료",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6075&ctitle=%B9%CC%B4%CF%B5%A5%C0%CC%C5%CD%B7%EB"
    },
    "5": {
        "name": "Webzine #1",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board.php?mart_id=mbwshop&bbs_no=3"
    }
}

def fetch_page_requests(url):
    """Fetch URL with proper encoding"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Charset': 'utf-8,iso-8859-1;q=0.7,*;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url, timeout=10, headers=headers)

        if response.encoding is None or 'utf' not in response.encoding.lower():
            try:
                response.encoding = 'euc-kr'
                test = response.text
            except:
                try:
                    response.encoding = 'cp949'
                    test = response.text
                except:
                    response.encoding = 'utf-8'

        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"⚠️ Fetch error: {str(e)[:100]}")
        return None

def analyze_table_structure(html):
    """Deep analyze TABLE structure"""
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all('table')
    print(f"  📊 Total tables: {len(tables)}")

    analysis = {
        'total_tables': len(tables),
        'table_structures': [],
        'content_patterns': defaultdict(int)
    }

    for idx, table in enumerate(tables[:3]):  # Analyze first 3 tables only
        rows = table.find_all('tr')
        cells_per_row = [len(row.find_all(['td', 'th'])) for row in rows[:5]]

        # Check for images, links, text in table
        images = table.find_all('img')
        links = table.find_all('a')
        has_text = bool(table.get_text(strip=True))

        table_info = {
            'table_index': idx,
            'rows_sampled': len(rows[:5]),
            'cells_per_row': cells_per_row,
            'images_count': len(images),
            'links_count': len(links),
            'has_text': has_text,
            'first_row_sample': cells_per_row[0] if cells_per_row else 0
        }

        analysis['table_structures'].append(table_info)

        # Classify content type
        if len(images) > 0 and has_text:
            analysis['content_patterns']['photo+text'] += 1
        elif len(images) > 0 and not has_text:
            analysis['content_patterns']['photo_only'] += 1
        elif len(images) == 0 and has_text:
            analysis['content_patterns']['text_only'] += 1

    return analysis

def analyze_content_links(html):
    """Analyze article/product links and their patterns"""
    soup = BeautifulSoup(html, 'html.parser')

    # Find all links that point to articles/products
    links = soup.find_all('a')
    content_links = []

    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for article/product links
        if 'webzine_board_read.php' in href or 'board_view_info1.php' in href:
            if not href.startswith('http'):
                href = urljoin(BASE_URL, href)

            content_links.append({
                'url': href,
                'text': text[:50],  # First 50 chars
                'type': 'webzine' if 'webzine_board_read.php' in href else 'product'
            })

    return content_links

def analyze_pagination(html):
    """Analyze pagination structure"""
    soup = BeautifulSoup(html, 'html.parser')

    # Look for page links
    page_links = []
    links = soup.find_all('a')

    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # Look for page= parameter
        if 'page=' in href or text.isdigit() or text in ['다음', '이전', 'Next', 'Prev']:
            page_links.append({
                'url': href,
                'text': text,
                'is_page_number': text.isdigit()
            })

    # Deduplicate
    unique_pages = []
    seen = set()
    for link in page_links:
        key = (link['url'], link['text'])
        if key not in seen:
            seen.add(key)
            unique_pages.append(link)

    return unique_pages

def analyze_category(category_key):
    """Full structural analysis of a category"""
    if category_key not in PLASTICNET_CATEGORIES:
        print(f"❌ Invalid category: {category_key}")
        return None

    category = PLASTICNET_CATEGORIES[category_key]
    print(f"\n{'='*80}")
    print(f"📂 ANALYZING: {category['name']}")
    print(f"{'='*80}\n")

    # Fetch category page
    html = fetch_page_requests(category['url'])
    if not html:
        print(f"❌ Failed to fetch: {category['url']}")
        return None

    # Analysis 1: TABLE structure
    print("🔍 TABLE STRUCTURE ANALYSIS:")
    table_analysis = analyze_table_structure(html)
    for table_info in table_analysis['table_structures']:
        print(f"  └─ Table {table_info['table_index']}: {table_info['rows_sampled']} rows, {table_info['images_count']} images, {table_info['links_count']} links")
    print(f"  📊 Content patterns: {dict(table_analysis['content_patterns'])}")

    # Analysis 2: Content links
    print("\n🔗 CONTENT LINKS ANALYSIS:")
    content_links = analyze_content_links(html)
    print(f"  Total content links found: {len(content_links)}")
    if content_links:
        print(f"  Sample links:")
        for link in content_links[:3]:
            print(f"    • {link['text'][:30]} ({link['type']})")

    # Analysis 3: Pagination
    print("\n📄 PAGINATION ANALYSIS:")
    pagination = analyze_pagination(html)
    print(f"  Total pagination links: {len(pagination)}")
    page_numbers = [p for p in pagination if p['is_page_number']]
    if page_numbers:
        print(f"  Page numbers found: {len(page_numbers)}")
        print(f"  Sample: {[p['text'] for p in page_numbers[:5]]}")

    return {
        'category': category['name'],
        'category_key': category_key,
        'table_analysis': table_analysis,
        'content_links_count': len(content_links),
        'pagination_links_count': len(pagination),
        'sample_links': content_links[:3],
        'sample_pagination': pagination[:3]
    }

def main():
    """Run structural analysis on sample categories"""
    print("\n" + "="*80)
    print("🔍 PLASTICNET STRUCTURAL DEEP-DIVE ANALYSIS")
    print("="*80)
    print("\nAnalyzing HTML TABLE structures, content patterns, and pagination...")

    results = {}

    # Analyze each category
    for category_key in ["1", "5"]:
        result = analyze_category(category_key)
        if result:
            results[category_key] = result

    # Save analysis results
    output_file = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet/structure_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Analysis saved to: {output_file}")

    # Summary
    print("\n" + "="*80)
    print("📊 ANALYSIS SUMMARY")
    print("="*80)
    for cat_key, result in results.items():
        print(f"\n{result['category']}:")
        print(f"  • Content links: {result['content_links_count']}")
        print(f"  • Pagination links: {result['pagination_links_count']}")
        print(f"  • TABLE structures: {result['table_analysis']['total_tables']}")

if __name__ == "__main__":
    main()
