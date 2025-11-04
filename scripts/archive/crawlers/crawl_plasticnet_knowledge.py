#!/usr/bin/env python3
"""
🚀 PLASTICNET KNOWLEDGE BASE CRAWLER

Extract technical plastic material information from plasticnet.kr
to enhance RAG knowledge base for product recommendations.

Features:
✅ Crawl multiple webzine/technical article pages
✅ Extract material properties, testing standards, processing info
✅ Store structured knowledge for RAG augmentation
✅ Link to product data (PET, HDPE, PP, ABS, PVC, etc.)
"""

import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

BASE_URL = "https://plasticnet.kr"

OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/plasticnet/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = OUTPUT_DIR / "plastic_technical_knowledge.jsonl"
INDEX_FILE = OUTPUT_DIR / "knowledge_index.json"
PROGRESS_FILE = OUTPUT_DIR / "crawl_progress.json"

log_file = LOG_DIR / f"plasticnet_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# KNOWLEDGE EXTRACTION
# ============================================

PLASTIC_MATERIALS = {
    'PET': ['polyethylene terephthalate', 'polyester', '폴리에스터'],
    'HDPE': ['high density polyethylene', '고밀도폴리에틸렌'],
    'LDPE': ['low density polyethylene', '저밀도폴리에틸렌'],
    'PP': ['polypropylene', ' polyprop', '폴리프로필렌'],
    'PVC': ['polyvinyl chloride', '염화폴리비닐'],
    'PVDC': ['polyvinylidene chloride', 'saran'],
    'PS': ['polystyrene', '폴리스타이렌'],
    'ABS': ['acrylonitrile butadiene styrene'],
    'PC': ['polycarbonate', '폴리카보네이트'],
    'PMMA': ['polymethyl methacrylate', 'acrylic', 'plexiglass'],
    'PA': ['polyamide', 'nylon', '나일론'],
    'TPE': ['thermoplastic elastomer', '열가소성탄성체'],
    'TPU': ['thermoplastic urethane'],
    'EVA': ['ethylene vinyl acetate'],
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
    '透光率', '강도', '탄성', '경도', '밀도', '용융점', '내열성',
]

def extract_material_knowledge(html, url):
    """Extract plastic material knowledge from HTML"""

    knowledge_items = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Extract main content
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'body', 'main']) if x else False)
        if not main_content:
            main_content = soup.find('article') or soup.find('div', id=lambda x: x and 'content' in x.lower() if x else False)

        if not main_content:
            main_content = soup

        # Extract all text
        text_content = main_content.get_text(separator='\n', strip=True)

        # Extract title/article name
        title = soup.find('h1') or soup.find('h2')
        article_title = title.get_text(strip=True) if title else "Unknown"

        # Detect plastic materials mentioned
        materials_found = {}
        for material_code, aliases in PLASTIC_MATERIALS.items():
            for alias in aliases:
                if alias.lower() in text_content.lower():
                    materials_found[material_code] = alias

        # Detect testing standards mentioned
        standards_found = {}
        for standard_code, standard_name in TESTING_STANDARDS.items():
            if standard_code in text_content:
                standards_found[standard_code] = standard_name

        # Extract properties mentioned
        properties_found = []
        for prop in MATERIAL_PROPERTIES:
            if prop.lower() in text_content.lower():
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
                    table_data.append(row_text)

        # Extract lists
        list_items = []
        for ul in soup.find_all(['ul', 'ol']):
            for li in ul.find_all('li'):
                list_items.append(li.get_text(strip=True))

        # Create knowledge entry
        knowledge_entry = {
            'article_title': article_title,
            'url': url,
            'crawled_at': datetime.now().isoformat(),
            'content_preview': text_content[:1000],  # First 1000 chars
            'full_content': text_content,
            'materials_mentioned': list(materials_found.keys()),
            'material_aliases': materials_found,
            'testing_standards': standards_found,
            'properties': properties_found,
            'tables': table_data,
            'lists': list_items,
            'word_count': len(text_content.split()),
        }

        knowledge_items.append(knowledge_entry)

        logger.info(f"✅ Extracted knowledge from: {article_title}")
        if materials_found:
            logger.info(f"   Materials: {list(materials_found.keys())}")
        if standards_found:
            logger.info(f"   Standards: {list(standards_found.keys())}")
        if properties_found:
            logger.info(f"   Properties: {len(properties_found)} found")

    except Exception as e:
        logger.error(f"❌ Extraction error: {str(e)[:100]}")

    return knowledge_items

def fetch_and_extract(url):
    """Fetch URL and extract knowledge"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Charset': 'utf-8,iso-8859-1;q=0.7,*;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url, timeout=10, headers=headers)

        # Try to detect and use proper encoding
        if response.encoding is None or 'utf' not in response.encoding.lower():
            # plasticnet.kr uses EUC-KR or CP949 encoding
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
            return extract_material_knowledge(response.text, url)
        else:
            logger.warning(f"⚠️  HTTP {response.status_code}: {url}")
            return []
    except Exception as e:
        logger.error(f"❌ Fetch error {url}: {str(e)[:100]}")
        return []

def load_progress():
    """Load crawl progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'urls_crawled': 0, 'knowledge_items': 0, 'start_time': datetime.now().isoformat()}

def save_progress(stats):
    """Save crawl progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ============================================
# MAIN
# ============================================

def main():
    logger.info("=" * 80)
    logger.info("🚀 PLASTICNET KNOWLEDGE BASE CRAWLER")
    logger.info("=" * 80)

    # Target URLs - webzine, technical articles, standards info
    target_urls = [
        # Technical material info pages - Original 4
        "https://plasticnet.kr/found/market/mbwshop/webzine_board.php?mart_id=mbwshop&bbs_no=3",
        "https://plasticnet.kr/found/market/mbwshop/webzine_board2.php?mart_id=mbwshop&bbs_no=2",
        "https://plasticnet.kr/found/market/mbwshop/webzine_board3.php?mart_id=mbwshop&bbs_no=1",
        "https://plasticnet.kr/found/market/mbwshop/webzine_board10.php?mart_id=mbwshop&bbs_no=16",

        # Additional 4 material specification pages
        "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6075&ctitle=%B9%CC%B4%CF%B5%A5%C0%CC%C5%CD%B7%EB",
        "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6074&ctitle=%C6%E4%C0%CE%C6%AE/%C4%DA%C6%C3",
        "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6076&ctitle=%C7%C3%B6%F3%BD%BA%C6%BD%20%B0%A1%C0%CC%B5%E5",
        "https://plasticnet.kr/found/market/mbwshop/board_list_info1.php?mart_id=mbwshop&con_category_no=6074&sub_category_no=6074&sub_category_no2=6077&ctitle=%C6%FA%B8%AE%B8%D3%B3%EB%C6%AE",
    ]

    progress = load_progress()
    total_knowledge_items = 0
    total_urls = len(target_urls)

    logger.info(f"\n📊 Starting crawl of {total_urls} knowledge pages\n")

    # Open output file for streaming writes
    with open(KNOWLEDGE_FILE, 'a') as out_f:
        for i, url in enumerate(target_urls, 1):
            logger.info(f"📖 [{i}/{total_urls}] Crawling: {url}")

            # Fetch and extract
            knowledge_items = fetch_and_extract(url)

            # Save to JSONL
            for item in knowledge_items:
                out_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                out_f.flush()
                total_knowledge_items += 1

            # Brief pause
            time.sleep(1)

    # Create index for quick search
    logger.info("\n🗂️  Building knowledge index...")

    index = {
        'total_articles': total_urls,
        'total_knowledge_items': total_knowledge_items,
        'materials': {},
        'standards': {},
        'properties': {},
        'crawled_at': datetime.now().isoformat(),
    }

    # Read knowledge file and build index
    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, 'r') as f:
            for line in f:
                item = json.loads(line)

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

    # Save index
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Update progress
    progress['urls_crawled'] = total_urls
    progress['knowledge_items'] = total_knowledge_items
    progress['last_crawl'] = datetime.now().isoformat()
    save_progress(progress)

    logger.info(f"\n✅ CRAWL COMPLETE:")
    logger.info(f"   📚 Knowledge items extracted: {total_knowledge_items}")
    logger.info(f"   🔗 URLs crawled: {total_urls}")
    logger.info(f"   📊 Materials indexed: {len(index['materials'])}")
    logger.info(f"   📋 Standards indexed: {len(index['standards'])}")
    logger.info(f"   🏷️  Properties indexed: {len(index['properties'])}")
    logger.info(f"\n📁 Output:")
    logger.info(f"   Knowledge base: {KNOWLEDGE_FILE}")
    logger.info(f"   Index: {INDEX_FILE}")
    logger.info(f"   Logs: {log_file}")

if __name__ == "__main__":
    main()
