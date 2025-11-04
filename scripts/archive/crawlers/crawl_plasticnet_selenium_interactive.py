#!/usr/bin/env python3
"""
🚀 PLASTICNET SELENIUM-BASED INTERACTIVE CRAWLER

Extract comprehensive technical plastic material knowledge from plasticnet.kr
with full pagination support and individual article extraction.

Features:
✅ Browser automation with Selenium for dynamic content
✅ Full pagination discovery and crawling
✅ Individual article extraction with proper session handling
✅ Interactive mode - crawl one category at a time
✅ Resumable crawling with progress tracking
✅ Proper URL handling with /found/market/mbwshop/ path
"""

import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup
import re

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Install with: pip install selenium")

BASE_URL = "https://plasticnet.kr"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = OUTPUT_DIR / "plastic_technical_knowledge.jsonl"
INDEX_FILE = OUTPUT_DIR / "knowledge_index.json"
PROGRESS_FILE = OUTPUT_DIR / "crawl_progress.json"
CRAWLED_URLS_FILE = OUTPUT_DIR / "crawled_urls.json"
CATEGORIES_FILE = OUTPUT_DIR / "categories.json"

log_file = LOG_DIR / f"plasticnet_selenium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# PREDEFINED CATEGORIES (User can add more)
# ============================================

PLASTICNET_CATEGORIES = {
    "1": {
        "name": "폴리프로필렌/PP 재료",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6075&ctitle=%B9%CC%B4%CF%B5%A5%C0%CC%C5%CD%B7%EB"
    },
    "2": {
        "name": "파이렉/PFA 재료",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6074&ctitle=%C6%E4%C0%CE%C6%AE/%C4%DA%C6%C3"
    },
    "3": {
        "name": "플라스틱 가이드",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6076&ctitle=%C7%C3%B6%F3%BD%BA%C6%BD%20%B0%A1%C0%CC%B5%E5"
    },
    "4": {
        "name": "폴리에틸렌 이더",
        "url": "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6077&ctitle=%C6%FA%B8%AE%B8%D3%B3%EB%C6%AE"
    },
    "5": {
        "name": "Webzine #1",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board.php?mart_id=mbwshop&bbs_no=3"
    },
    "6": {
        "name": "Webzine #2",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board2.php?mart_id=mbwshop&bbs_no=2"
    },
    "7": {
        "name": "Webzine #3",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board3.php?mart_id=mbwshop&bbs_no=1"
    },
    "8": {
        "name": "Webzine #4",
        "url": "https://plasticnet.kr/found/market/mbwshop/webzine_board10.php?mart_id=mbwshop&bbs_no=16"
    }
}

# ============================================
# KNOWLEDGE EXTRACTION
# ============================================

PLASTIC_MATERIALS = {
    'PET': ['polyethylene terephthalate', 'polyester', '폴리에스터', 'PET'],
    'HDPE': ['high density polyethylene', '고밀도폴리에틸렌', 'HDPE'],
    'LDPE': ['low density polyethylene', '저밀도폴리에틸렌', 'LDPE'],
    'PP': ['polypropylene', 'polyprop', '폴리프로필렌', 'PP'],
    'PVC': ['polyvinyl chloride', '염화폴리비닐', 'PVC'],
    'PVDC': ['polyvinylidene chloride', 'saran', 'PVDC'],
    'PS': ['polystyrene', '폴리스타이렌', 'PS'],
    'ABS': ['acrylonitrile butadiene styrene', 'ABS'],
    'PC': ['polycarbonate', '폴리카보네이트', 'PC'],
    'PMMA': ['polymethyl methacrylate', 'acrylic', 'plexiglass', 'PMMA'],
    'PA': ['polyamide', 'nylon', '나일론', 'PA'],
    'TPE': ['thermoplastic elastomer', '열가소성탄성체', 'TPE'],
    'TPU': ['thermoplastic urethane', 'TPU'],
    'EVA': ['ethylene vinyl acetate', 'EVA'],
    'PFA': ['perfluoroalkoxy', 'PFA'],
    'ETFE': ['ethylene tetrafluoroethylene', 'ETFE'],
}

TESTING_STANDARDS = {
    'ASTM': 'American Society for Testing and Materials',
    'ISO': 'International Organization for Standardization',
    'JIS': 'Japanese Industrial Standard',
    'DIN': 'Deutsches Institut für Normung',
    'BS': 'British Standard',
    'KS': 'Korean Standard',
    'GB': 'Chinese National Standard',
}

MATERIAL_PROPERTIES = [
    'tensile strength', 'elongation', 'hardness', 'modulus',
    'density', 'melting point', 'glass transition', 'flexural strength',
    'impact strength', 'heat deflection', 'tear strength',
    'tensibility', 'elasticity', 'ductility', 'brittleness',
    'chemical resistance', 'uv resistance', 'weathering', 'aging',
    '투광율', '강도', '탄성', '경도', '밀도', '용융점', '내열성', '내화학성',
    '인장강도', '신율', '충격강도', '굴곡강도',
]

def fetch_page_selenium(driver, url, wait_time=10):
    """Fetch page using Selenium for JavaScript rendering"""
    try:
        logger.info(f"🌐 Loading: {url[:80]}")
        driver.get(url)
        time.sleep(3)  # Wait for dynamic content
        return driver.page_source
    except Exception as e:
        logger.error(f"❌ Selenium fetch error: {str(e)[:100]}")
        return None

def fetch_page_requests(url, max_retries=3):
    """Fallback: Fetch URL with requests library"""
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept-Charset': 'utf-8,iso-8859-1;q=0.7,*;q=0.7',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            response = requests.get(url, timeout=10, headers=headers)

            # Handle Korean encoding
            if response.encoding is None or 'utf' not in response.encoding.lower():
                try:
                    response.encoding = 'euc-kr'
                    test_decode = response.text
                except:
                    try:
                        response.encoding = 'cp949'
                        test_decode = response.text
                    except:
                        response.encoding = 'utf-8'

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"⚠️  HTTP {response.status_code}: {url}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️  Fetch error (attempt {attempt+1}/{max_retries}): {str(e)[:100]}")
            time.sleep(2)

    return None

def extract_pagination_links(html, category_url):
    """Extract pagination links from category listing page"""
    pagination_links = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Find all pagination links
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Check if this looks like a page number link
            if 'page=' in href:
                full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
                if full_url not in pagination_links and full_url != category_url:
                    pagination_links.append(full_url)
            elif text.isdigit() and 2 <= int(text) <= 999:
                # Likely a page number
                if '?' in category_url:
                    page_url = f"{category_url}&page={text}"
                else:
                    page_url = f"{category_url}?page={text}"
                if page_url not in pagination_links:
                    pagination_links.append(page_url)

    except Exception as e:
        logger.warning(f"⚠️  Pagination extraction error: {str(e)[:100]}")

    return pagination_links

def extract_article_links(html):
    """Extract individual article links from category page"""
    article_links = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Look for links to article detail pages
        for link in soup.find_all('a'):
            href = link.get('href', '')

            # Match article detail page patterns
            if 'board_view_info1.php' in href or 'webzine_board_read.php' in href or 'view=' in href:
                # Ensure proper absolute URL with full path
                if not href.startswith('http'):
                    if '/found/market/mbwshop/' not in href:
                        # Add the proper path prefix
                        href = f'/found/market/mbwshop/{href.lstrip("/")}'
                    full_url = urljoin(BASE_URL, href)
                else:
                    full_url = href

                if full_url not in article_links:
                    article_links.append(full_url)

    except Exception as e:
        logger.warning(f"⚠️  Article extraction error: {str(e)[:100]}")

    return article_links

def extract_material_knowledge(html, url):
    """Extract plastic material knowledge from HTML"""

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Extract main content
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'body', 'main', 'article']) if x else False)
        if not main_content:
            main_content = soup.find('article') or soup.find('div', id=lambda x: x and 'content' in x.lower() if x else False)

        if not main_content:
            main_content = soup

        # Extract all text
        text_content = main_content.get_text(separator='\n', strip=True)

        # Skip if too short (likely not an article)
        if len(text_content) < 100:
            return None

        # Extract title
        title = soup.find('h1') or soup.find('h2') or soup.find('h3')
        article_title = title.get_text(strip=True) if title else "Unknown"

        # Detect plastic materials mentioned
        materials_found = {}
        for material_code, aliases in PLASTIC_MATERIALS.items():
            for alias in aliases:
                if alias.lower() in text_content.lower():
                    materials_found[material_code] = alias
                    break

        # Detect testing standards mentioned
        standards_found = {}
        for standard_code, standard_name in TESTING_STANDARDS.items():
            if standard_code in text_content:
                standards_found[standard_code] = standard_name

        # Extract properties mentioned
        properties_found = []
        for prop in MATERIAL_PROPERTIES:
            if prop.lower() in text_content.lower():
                if prop not in properties_found:
                    properties_found.append(prop)

        # Extract tables (specifications, properties)
        tables = soup.find_all('table')
        table_data = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_text = [cell.get_text(strip=True) for cell in cells]
                    if row_text:
                        table_data.append(row_text)

        # Extract lists
        list_items = []
        for ul in soup.find_all(['ul', 'ol']):
            for li in ul.find_all('li'):
                item_text = li.get_text(strip=True)
                if item_text and item_text not in list_items:
                    list_items.append(item_text)

        # Create knowledge entry
        knowledge_entry = {
            'article_title': article_title,
            'url': url,
            'crawled_at': datetime.now().isoformat(),
            'content_preview': text_content[:500],
            'materials_mentioned': list(materials_found.keys()),
            'material_aliases': materials_found,
            'testing_standards': standards_found,
            'properties': properties_found,
            'tables': table_data[:10],  # Limit to first 10 tables
            'lists': list_items[:20],   # Limit to first 20 items
            'word_count': len(text_content.split()),
        }

        logger.info(f"✅ Extracted: {article_title[:60]}")
        if materials_found:
            logger.info(f"   Materials: {list(materials_found.keys())}")
        if properties_found:
            logger.info(f"   Properties: {len(properties_found)}")

        return knowledge_entry

    except Exception as e:
        logger.error(f"❌ Knowledge extraction error: {str(e)[:100]}")
        return None

def load_crawled_urls():
    """Load set of already crawled URLs"""
    if CRAWLED_URLS_FILE.exists():
        with open(CRAWLED_URLS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_crawled_urls(crawled_set):
    """Save set of crawled URLs"""
    with open(CRAWLED_URLS_FILE, 'w') as f:
        json.dump(list(crawled_set), f, ensure_ascii=False, indent=2)

def load_progress():
    """Load crawl progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'articles_crawled': 0, 'knowledge_items': 0, 'start_time': datetime.now().isoformat()}

def save_progress(stats):
    """Save crawl progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def update_index():
    """Rebuild knowledge index from JSONL file"""
    index = {
        'total_knowledge_items': 0,
        'materials': {},
        'standards': {},
        'properties': {},
        'crawled_at': datetime.now().isoformat(),
    }

    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)

                        index['total_knowledge_items'] += 1

                        # Index materials
                        for material in item.get('materials_mentioned', []):
                            if material not in index['materials']:
                                index['materials'][material] = 0
                            index['materials'][material] += 1

                        # Index standards
                        for standard in item.get('testing_standards', {}).keys():
                            if standard not in index['standards']:
                                index['standards'][standard] = 0
                            index['standards'][standard] += 1

                        # Index properties
                        for prop in item.get('properties', []):
                            if prop not in index['properties']:
                                index['properties'][prop] = 0
                            index['properties'][prop] += 1
                    except json.JSONDecodeError:
                        continue

    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return index

# ============================================
# INTERACTIVE MODE
# ============================================

def show_menu():
    """Show category selection menu"""
    print("\n" + "="*80)
    print("🚀 PLASTICNET INTERACTIVE CRAWLER")
    print("="*80)
    print("\n📚 Available Categories to Crawl:\n")

    for key, cat in PLASTICNET_CATEGORIES.items():
        status = "✅ (Already crawled)" if CRAWLED_URLS_FILE.exists() else ""
        print(f"  [{key}] {cat['name']} {status}")

    print(f"\n  [a] Crawl All Categories")
    print(f"  [s] Show Stats")
    print(f"  [q] Quit\n")

def crawl_category(category_key, use_selenium=True):
    """Crawl a single category with pagination and articles"""

    if category_key not in PLASTICNET_CATEGORIES:
        logger.error(f"❌ Invalid category: {category_key}")
        return

    category = PLASTICNET_CATEGORIES[category_key]
    category_url = category['url']
    category_name = category['name']

    logger.info(f"\n{'='*80}")
    logger.info(f"📂 CRAWLING CATEGORY: {category_name}")
    logger.info(f"{'='*80}\n")

    crawled_urls = load_crawled_urls()
    progress = load_progress()

    # Initialize Selenium if available
    driver = None
    if use_selenium and SELENIUM_AVAILABLE:
        try:
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            driver = webdriver.Chrome(options=options)
            logger.info("✅ Selenium WebDriver initialized")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize Selenium: {e}. Using requests library instead.")
            driver = None

    total_knowledge_items = 0
    articles_processed = 0

    # Fetch category page
    if driver:
        html = fetch_page_selenium(driver, category_url)
    else:
        html = fetch_page_requests(category_url)

    if not html:
        logger.error(f"❌ Failed to fetch category: {category_url}")
        if driver:
            driver.quit()
        return

    # Extract pagination links
    pagination_links = extract_pagination_links(html, category_url)
    all_category_urls = [category_url] + pagination_links

    logger.info(f"📄 Found {len(pagination_links)} additional pagination pages (total: {len(all_category_urls)})\n")

    # Open output file for streaming writes
    with open(KNOWLEDGE_FILE, 'a') as out_f:
        # Process each pagination page
        for page_idx, page_url in enumerate(all_category_urls, 1):
            if page_url in crawled_urls:
                logger.info(f"⏭️  Page {page_idx}/{len(all_category_urls)} already crawled")
                continue

            logger.info(f"📄 [Page {page_idx}/{len(all_category_urls)}] Fetching articles...")

            if driver:
                page_html = fetch_page_selenium(driver, page_url)
            else:
                page_html = fetch_page_requests(page_url)

            if not page_html:
                logger.warning(f"⚠️  Failed to fetch page: {page_url}")
                continue

            # Extract article links
            article_links = extract_article_links(page_html)
            logger.info(f"   Found {len(article_links)} articles on this page\n")

            # Process each article
            for article_idx, article_url in enumerate(article_links, 1):
                if article_url in crawled_urls:
                    continue

                if driver:
                    article_html = fetch_page_selenium(driver, article_url)
                else:
                    article_html = fetch_page_requests(article_url)

                if not article_html:
                    continue

                # Extract knowledge
                knowledge = extract_material_knowledge(article_html, article_url)
                if knowledge:
                    # Save to JSONL
                    out_f.write(json.dumps(knowledge, ensure_ascii=False) + '\n')
                    out_f.flush()
                    total_knowledge_items += 1
                    articles_processed += 1

                crawled_urls.add(article_url)
                time.sleep(0.5)  # Rate limiting

            crawled_urls.add(page_url)
            time.sleep(1)

    # Clean up
    if driver:
        driver.quit()

    # Update progress and index
    save_crawled_urls(crawled_urls)
    progress['articles_crawled'] = progress.get('articles_crawled', 0) + articles_processed
    progress['knowledge_items'] = progress.get('knowledge_items', 0) + total_knowledge_items
    progress['last_crawl'] = datetime.now().isoformat()
    save_progress(progress)

    # Rebuild index
    index = update_index()

    logger.info(f"\n✅ CATEGORY CRAWL COMPLETE:")
    logger.info(f"   📚 Knowledge items extracted: {total_knowledge_items}")
    logger.info(f"   📄 Articles crawled: {articles_processed}")
    logger.info(f"   📊 Total materials indexed: {len(index['materials'])}")
    logger.info(f"   📋 Total standards indexed: {len(index['standards'])}")
    logger.info(f"   🏷️  Total properties indexed: {len(index['properties'])}")
    logger.info(f"\n📁 Output:")
    logger.info(f"   Knowledge base: {KNOWLEDGE_FILE}")
    logger.info(f"   Index: {INDEX_FILE}")

def show_stats():
    """Show crawling statistics"""
    progress = load_progress()

    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r') as f:
            index = json.load(f)
    else:
        index = {'total_knowledge_items': 0, 'materials': {}, 'standards': {}, 'properties': {}}

    print(f"\n{'='*80}")
    print("📊 CRAWLING STATISTICS")
    print(f"{'='*80}\n")
    print(f"📚 Total Knowledge Items: {index['total_knowledge_items']}")
    print(f"📄 Total Articles Crawled: {progress.get('articles_crawled', 0)}")
    print(f"📊 Materials Indexed: {len(index['materials'])}")
    print(f"   {list(index['materials'].keys())[:10]}")
    print(f"📋 Standards Indexed: {len(index['standards'])}")
    print(f"   {list(index['standards'].keys())}")
    print(f"🏷️  Properties Indexed: {len(index['properties'])}")
    print(f"   {list(index['properties'].keys())[:10]}\n")

def main():
    if not SELENIUM_AVAILABLE:
        print("⚠️  Selenium not available. Install with: pip install selenium")
        print("   For Selenium WebDriver, also install ChromeDriver:\n")
        print("   Mac: brew install chromedriver")
        print("   Or download from: https://chromedriver.chromium.org/\n")

    while True:
        show_menu()
        choice = input("👉 Select category (or command): ").strip()

        if choice.lower() == 'q':
            print("\n👋 Goodbye!")
            break
        elif choice.lower() == 's':
            show_stats()
        elif choice.lower() == 'a':
            print("\n🔄 Crawling all categories...")
            for cat_key in PLASTICNET_CATEGORIES.keys():
                crawl_category(cat_key, use_selenium=SELENIUM_AVAILABLE)
                input("👉 Press Enter to continue to next category...")
        elif choice in PLASTICNET_CATEGORIES:
            crawl_category(choice, use_selenium=SELENIUM_AVAILABLE)
            input("👉 Press Enter to return to menu...")
        else:
            print(f"❌ Invalid choice: {choice}\n")

if __name__ == "__main__":
    main()
