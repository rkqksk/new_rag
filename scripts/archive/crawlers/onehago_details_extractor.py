import json
import requests
from bs4 import BeautifulSoup
import os
import time
import random
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def normalize_text(text):
    """Clean and normalize text by removing extra whitespaces and special characters."""
    return re.sub(r'\s+', ' ', text).strip() if text else ''

def extract_product_specifications_playwright(detail_url):
    """
    Extract product specifications using Playwright for JavaScript rendering

    Args:
        detail_url (str): Product detail page URL

    Returns:
        dict: Extracted specifications or None if extraction fails
    """
    with sync_playwright() as p:
        try:
            # Launch browser with random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
            ]

            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=random.choice(user_agents))

            # Add randomization to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))

            # Navigate and wait for content
            page.goto(detail_url, timeout=15000)
            page.wait_for_load_state('networkidle')

            # Try multiple strategies to find specifications
            strategies = [
                # Strategy 1: Find detail info table
                lambda: page.evaluate_handle('''
                    Array.from(document.querySelectorAll('table.detail_info_table tr, div.detail_info'))
                        .map(row => {
                            const key = row.querySelector('th, .label');
                            const value = row.querySelector('td, .value');
                            return key && value ? {
                                key: key.textContent.trim(),
                                value: value.textContent.trim()
                            } : null;
                        })
                        .filter(item => item !== null)
                '''),

                # Strategy 2: Find all text-based detail info
                lambda: page.evaluate_handle('''
                    Array.from(document.querySelectorAll('*'))
                        .filter(el => {
                            const text = el.textContent.trim();
                            return text.includes(':') && text.length < 200;
                        })
                        .map(el => {
                            const parts = el.textContent.split(':');
                            return parts.length === 2 ? {
                                key: parts[0].trim(),
                                value: parts[1].trim()
                            } : null;
                        })
                        .filter(item => item !== null)
                ''')
            ]

            specifications = {}
            for strategy in strategies:
                try:
                    details = strategy()
                    rows = details.jsonValue()

                    for row in rows:
                        if row:
                            key = normalize_text(row.get('key', ''))
                            value = normalize_text(row.get('value', ''))

                            if key and value:
                                specifications[key] = value

                    if specifications:  # Stop if we found something
                        break

                except Exception as strategy_error:
                    logger.warning(f"Strategy failed: {strategy_error}")

            browser.close()
            return specifications if specifications else None

        except Exception as e:
            logger.error(f"Playwright error for {detail_url}: {e}")
            return None

def extract_product_specifications_requests(detail_url):
    """
    Fallback to requests method if Playwright fails

    Args:
        detail_url (str): Product detail page URL

    Returns:
        dict: Extracted specifications or None if extraction fails
    """
    try:
        time.sleep(random.uniform(0.5, 1.5))
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }

        response = requests.get(detail_url, headers=headers, timeout=10)
        response.encoding = 'euc-kr'  # Explicitly set encoding
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Advanced extraction strategies
        specifications = {}

        # Strategy 1: Find detailed info tables/divs
        tables = [
            soup.select('table.detail_info_table tr'),
            soup.select('div.detail_info tr'),
            soup.find_all(['tr', 'div'], class_=['detail_row', 'row'])
        ]

        for table in tables:
            for row in table:
                try:
                    key_el = row.find(['th', 'span'], class_='label')
                    value_el = row.find(['td', 'span'], class_='value')

                    if key_el and value_el:
                        key = normalize_text(key_el.get_text())
                        value = normalize_text(value_el.get_text())

                        if key and value:
                            specifications[key] = value
                except Exception as e:
                    logger.warning(f"Row parsing error: {e}")

        # Strategy 2: Find text with colons
        if not specifications:
            text_elements = soup.find_all(text=re.compile(r'\s*:\s*'))
            for el in text_elements:
                parts = el.split(':')
                if len(parts) == 2:
                    key = normalize_text(parts[0])
                    value = normalize_text(parts[1])
                    if key and value:
                        specifications[key] = value

        return specifications if specifications else None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {detail_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {detail_url}: {e}")
        return None

def extract_product_specifications(detail_url):
    """
    Main function to extract specifications with fallback strategies

    Args:
        detail_url (str): Product detail page URL

    Returns:
        dict: Extracted specifications or None if extraction fails
    """
    try:
        # First try Playwright (modern method)
        specs = extract_product_specifications_playwright(detail_url)

        if not specs:
            # Fallback to requests method
            specs = extract_product_specifications_requests(detail_url)

        return specs

    except Exception as e:
        logger.error(f"Specification extraction failed for {detail_url}: {e}")
        return None

def process_product_list(input_file, output_file, max_workers=10):
    """
    Process a list of products, extract their specifications

    Args:
        input_file (str): Path to input JSON file with products
        output_file (str): Path to output JSON file with added specifications
        max_workers (int): Number of concurrent threads for processing
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"Processing {len(products)} products...")

    # Ensure thread safety with a copy
    products_copy = products.copy()

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map futures to their product indices
        future_to_index = {
            executor.submit(extract_product_specifications, product['detail_url']): index
            for index, product in enumerate(products_copy)
            if product.get('detail_url')
        }

        # Process results as they complete
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                specs = future.result()
                if specs:
                    products_copy[index]['specifications'] = specs
                    products_copy[index]['already_crawled'] = True

                    # Optional: log progress
                    if index % 100 == 0:
                        logger.info(f"Processed {index} products...")
            except Exception as e:
                logger.error(f"Error processing product at index {index}: {e}")

    # Save updated products
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products_copy, f, ensure_ascii=False, indent=2)

    logger.info(f"Completed processing. Results saved to {output_file}")

def main():
    input_dir = '/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/'
    output_dir = '/Users/oypnus/Project/rag-enterprise/data/onehago/full_crawl_clean/'

    os.makedirs(output_dir, exist_ok=True)

    # Process each category file
    for filename in os.listdir(input_dir):
        if filename.startswith('category_') and filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f'processed_{filename}')

            logger.info(f"Processing {filename}...")
            process_product_list(input_path, output_path)

if __name__ == '__main__':
    main()