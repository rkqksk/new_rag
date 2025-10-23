#!/usr/bin/env python3
"""
Search and Crawl Missing Products
Uses Playwright to search for product codes on website and crawl them
"""

import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from chungjin_crawler import ChungjinCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search_missing_products.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductSearchCrawler:
    """Search for missing products and crawl them"""

    def __init__(self):
        self.base_url = "http://chungjinkorea.com"
        self.search_url = f"{self.base_url}/goods/goods_search.php"
        self.found_products = []
        self.not_found = []

    async def search_product(self, page, product_code: str) -> dict:
        """
        Search for a product code and return its URL if found

        Returns:
            {"code": str, "idx": int, "url": str} or None if not found
        """
        logger.info(f"\n🔍 Searching for: {product_code}")

        try:
            # Navigate to search page
            await page.goto(f"{self.search_url}?keyword={product_code}")
            await asyncio.sleep(2)

            # Check if product found in results
            # Look for product links in search results
            product_links = await page.query_selector_all('a[href*="goods_view.php?goodsIdx="]')

            if not product_links:
                logger.warning(f"❌ Not found: {product_code}")
                return None

            # Get first result
            first_link = product_links[0]
            href = await first_link.get_attribute('href')

            if not href:
                return None

            # Extract idx from URL
            if 'goodsIdx=' in href:
                idx = href.split('goodsIdx=')[1].split('&')[0]
                full_url = f"{self.base_url}/goods/goods_view.php?goodsIdx={idx}"

                logger.info(f"✅ Found: {product_code} → idx={idx}")

                return {
                    "code": product_code,
                    "idx": int(idx),
                    "url": full_url
                }

        except Exception as e:
            logger.error(f"Error searching {product_code}: {e}")
            return None

    async def search_all_missing_products(self, product_codes: list) -> dict:
        """Search for all missing product codes"""

        async with async_playwright() as p:
            browser = await p.webkit.launch(headless=True)
            page = await browser.new_page()

            results = {
                "found": [],
                "not_found": []
            }

            for code in product_codes:
                result = await self.search_product(page, code)

                if result:
                    results["found"].append(result)
                else:
                    results["not_found"].append(code)

                # Delay between searches
                await asyncio.sleep(1)

            await browser.close()

            return results

    async def crawl_found_products(self, found_products: list):
        """Crawl products that were found"""

        crawler = ChungjinCrawler(
            output_dir="data/crawled_products_final/temp_missing",
            browser_type="webkit",
            use_playwright=True
        )

        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Starting crawl for {len(found_products)} missing products")
        logger.info(f"{'='*80}\n")

        crawled = []
        failed = []

        for product in found_products:
            try:
                logger.info(f"Crawling: {product['code']} (idx={product['idx']})")
                data = await crawler.crawl_product(product['url'])

                # Save JSON
                output_file = f"idx_{product['idx']}.json"
                output_path = crawler.output_dir / output_file

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                logger.info(f"✅ Saved: {output_file}")
                crawled.append(product)

                # Delay between crawls
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ Failed to crawl {product['code']}: {e}")
                failed.append(product)

        logger.info(f"\n{'='*80}")
        logger.info(f"📊 Crawl Summary:")
        logger.info(f"   Successfully crawled: {len(crawled)}")
        logger.info(f"   Failed: {len(failed)}")
        logger.info(f"{'='*80}\n")

        return {
            "crawled": crawled,
            "failed": failed
        }


async def main():
    """Main execution"""

    # Load missing product codes
    codes_file = Path("data/excel_uploads/processed/missing_product_codes.txt")

    if not codes_file.exists():
        logger.error(f"Missing codes file not found: {codes_file}")
        logger.error("Run: python scripts/analyze_missing_products.py first")
        return

    with open(codes_file, 'r', encoding='utf-8') as f:
        product_codes = [line.strip() for line in f if line.strip()]

    logger.info(f"📋 Loaded {len(product_codes)} missing product codes")

    # Step 1: Search for products
    searcher = ProductSearchCrawler()
    search_results = await searcher.search_all_missing_products(product_codes)

    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 Search Results:")
    logger.info(f"   Found: {len(search_results['found'])}")
    logger.info(f"   Not found: {len(search_results['not_found'])}")
    logger.info(f"{'='*80}\n")

    # Save search results
    results_file = Path("data/excel_uploads/processed/search_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(search_results, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 Search results saved: {results_file}")

    # Step 2: Crawl found products
    if search_results['found']:
        crawl_results = await searcher.crawl_found_products(search_results['found'])

        # Save crawl results
        crawl_file = Path("data/excel_uploads/processed/crawl_results.json")
        with open(crawl_file, 'w', encoding='utf-8') as f:
            json.dump(crawl_results, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Crawl results saved: {crawl_file}")

    logger.info("\n✅ Process complete!")


if __name__ == "__main__":
    asyncio.run(main())
