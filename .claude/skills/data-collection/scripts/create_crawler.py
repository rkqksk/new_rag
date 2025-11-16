#!/usr/bin/env python3
"""
Generate web crawler for manufacturing sites
"""
import argparse
from pathlib import Path

CRAWLER_TEMPLATE = """#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
import json
from typing import List, Dict

class {class_name}Crawler:
    def __init__(self):
        self.base_url = "{base_url}"
        self.session = requests.Session()
        self.session.headers.update({{
            'User-Agent': 'Mozilla/5.0 (compatible; PETER-Bot/1.0)'
        }})

    def crawl_products(self, max_pages: int = 10) -> List[Dict]:
        \"\"\"Crawl product listings\"\"\"
        products = []

        for page in range(1, max_pages + 1):
            print(f"Crawling page {{page}}/{{max_pages}}...")

            try:
                response = self.session.get(
                    f"{{self.base_url}}/products?page={{page}}",
                    timeout=30
                )
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract products (customize selectors)
                product_items = soup.select('.product-item')  # Adjust selector

                for item in product_items:
                    product = self.extract_product(item)
                    if product:
                        products.append(product)

                # Rate limiting
                time.sleep(2)

            except Exception as e:
                print(f"Error on page {{page}}: {{e}}")
                continue

        return products

    def extract_product(self, item) -> Dict:
        \"\"\"Extract product details from HTML element\"\"\"
        try:
            return {{
                'name': item.select_one('.product-name').text.strip(),
                'code': item.select_one('.product-code').text.strip(),
                'price': item.select_one('.price').text.strip(),
                'url': item.select_one('a')['href'],
                'image': item.select_one('img')['src'],
                'description': item.select_one('.description').text.strip() if item.select_one('.description') else None
            }}
        except Exception as e:
            print(f"Error extracting product: {{e}}")
            return None

    def save_results(self, products: List[Dict], output_file: str):
        \"\"\"Save results to JSON\"\"\"
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        print(f"Saved {{len(products)}} products to {{output_file}}")

if __name__ == '__main__':
    crawler = {class_name}Crawler()
    products = crawler.crawl_products(max_pages={max_pages})
    crawler.save_results(products, 'data/crawled/{site_name}_products.json')
"""

def create_crawler(site_name: str, base_url: str, max_pages: int = 10):
    """
    Generate crawler script for a site
    """
    class_name = ''.join(word.capitalize() for word in site_name.split('_'))

    output_dir = Path(f"scripts/crawlers")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{site_name}_crawler.py"

    code = CRAWLER_TEMPLATE.format(
        class_name=class_name,
        base_url=base_url,
        max_pages=max_pages,
        site_name=site_name
    )

    output_file.write_text(code)
    output_file.chmod(0o755)

    print(f"✅ Created crawler: {output_file}")
    print(f"Run with: python {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate web crawler")
    parser.add_argument('--site', required=True, help='Site name (e.g., onehago)')
    parser.add_argument('--url', required=True, help='Base URL')
    parser.add_argument('--pages', type=int, default=10, help='Max pages to crawl')

    args = parser.parse_args()

    create_crawler(args.site, args.url, args.pages)
