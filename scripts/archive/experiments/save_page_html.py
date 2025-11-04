#!/usr/bin/env python3
"""
Save actual page HTML for deep analysis
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pathlib import Path

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
    return webdriver.Chrome(options=chrome_options)

def save_category_page(driver, category_id=22, page=1):
    """Save category page HTML"""
    url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page}"
    print(f"Loading: {url}")

    driver.get(url)
    time.sleep(3)  # Wait for JavaScript

    # Save full HTML
    html = driver.page_source
    output_file = Path(f"/tmp/onehago_category_{category_id}_page_{page}.html")
    output_file.write_text(html, encoding='utf-8')
    print(f"✅ Saved: {output_file} ({len(html):,} chars)")

    # Find first .product element and save its HTML
    products = driver.find_elements(By.CSS_SELECTOR, ".product")
    if products:
        first_product_html = products[0].get_attribute('outerHTML')
        product_file = Path(f"/tmp/onehago_product_element.html")
        product_file.write_text(first_product_html, encoding='utf-8')
        print(f"✅ Saved first product element: {product_file}")
        print(f"\nFirst 500 chars of product HTML:")
        print(first_product_html[:500])

def save_detail_page(driver, product_id="46893"):
    """Save product detail page HTML"""
    url = f"https://www.onehago.com/mall/?mode=view&prod_cd={product_id}"
    print(f"\nLoading: {url}")

    driver.get(url)
    time.sleep(3)

    html = driver.page_source
    output_file = Path(f"/tmp/onehago_detail_{product_id}.html")
    output_file.write_text(html, encoding='utf-8')
    print(f"✅ Saved: {output_file} ({len(html):,} chars)")

def main():
    driver = setup_driver()
    try:
        save_category_page(driver, category_id=22, page=1)
        save_detail_page(driver, product_id="46893")

        print(f"\n📁 Files saved to /tmp/")
        print(f"   - onehago_category_22_page_1.html")
        print(f"   - onehago_product_element.html")
        print(f"   - onehago_detail_46893.html")
        print(f"\n🔍 Analyze these files to find the correct extraction pattern")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
