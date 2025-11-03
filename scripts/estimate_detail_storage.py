#!/usr/bin/env python3
"""
Estimate storage requirements for detailed product page crawling

Analyzes sample product detail pages to estimate:
- Number of images per product
- Average image sizes
- Text/specification data size
- Total storage for 21,201 products
"""

import os
import json
import time
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

class DetailStorageEstimator:
    def __init__(self):
        self.driver = None
        self.storage_data = {
            'products_analyzed': 0,
            'total_images': 0,
            'total_image_bytes': 0,
            'total_text_bytes': 0,
            'products': []
        }

    def setup_driver(self):
        """Initialize Chrome driver - EXACT copy from working crawler"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        self.driver = webdriver.Chrome(options=chrome_options)
        print(f"✅ Chrome driver initialized")

    def login(self):
        """Login to freemold.net - EXACT copy from working crawler"""
        print("Logging in...")

        try:
            self.driver.get('https://www.freemold.net')
            time.sleep(3)

            # Remove overlay that blocks clicks
            self.driver.execute_script("""
                var mask = document.getElementById('divMask');
                if (mask) mask.style.display = 'none';
            """)

            # Click login button using JavaScript
            self.driver.execute_script("""
                var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (loginBtn) {
                    loginBtn.click();
                } else if (typeof loginLayer === 'function') {
                    loginLayer();
                }
            """)

            time.sleep(2)

            # Enter credentials
            wait = WebDriverWait(self.driver, 10)
            username_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            username_input.clear()
            username_input.send_keys(USERNAME)
            password_input.clear()
            password_input.send_keys(PASSWORD)

            # Submit login
            password_input.submit()
            time.sleep(5)

            # Verify login success
            if "로그아웃" in self.driver.page_source or "Logout" in self.driver.page_source:
                print("✅ Login successful - session established")
                return True
            else:
                print("❌ Login failed - could not verify session")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def get_image_size(self, img_url):
        """Get size of an image via HTTP HEAD request"""
        try:
            # Make URL absolute
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = 'https://www.freemold.net' + img_url

            response = requests.head(img_url, timeout=10, allow_redirects=True)
            content_length = response.headers.get('Content-Length')

            if content_length:
                return int(content_length)
            else:
                # Fallback to GET if HEAD doesn't provide size
                response = requests.get(img_url, timeout=10, stream=True)
                return int(response.headers.get('Content-Length', 0))
        except:
            # Estimate if can't fetch
            return 100 * 1024  # Assume 100KB if fetch fails

    def analyze_product_page(self, product_url, pIdx):
        """Analyze a single product detail page"""
        print(f"\nAnalyzing: {product_url}")

        try:
            # Navigate to product page
            self.driver.get(product_url)
            time.sleep(3)

            # Handle alert if present (shouldn't happen if session is maintained)
            try:
                alert = self.driver.switch_to.alert
                print(f"  ⚠️  Alert detected: {alert.text[:50]}...")
                alert.accept()
                print(f"  ❌ Session lost - skipping")
                return None
            except:
                pass  # No alert, good!

            # Extract images
            images = self.driver.find_elements(By.TAG_NAME, 'img')
            product_images = []

            for img in images:
                src = img.get_attribute('src')
                # Filter out icons, logos, UI elements
                if src and any(keyword in src.lower() for keyword in ['product', 'upload', 'board', 'attach']):
                    if not any(skip in src.lower() for skip in ['logo', 'icon', 'button', 'banner']):
                        product_images.append(src)

            # Get image sizes
            image_sizes = []
            for img_url in product_images[:5]:  # Sample first 5 images
                size = self.get_image_size(img_url)
                image_sizes.append(size)
                print(f"  Image: {size / 1024:.1f} KB")

            # Extract text content (specifications, description)
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            text_size = len(body_text.encode('utf-8'))

            # Get HTML for detailed specs
            html_content = self.driver.page_source
            html_size = len(html_content.encode('utf-8'))

            product_data = {
                'pIdx': pIdx,
                'url': product_url,
                'image_count': len(product_images),
                'image_sizes': image_sizes,
                'avg_image_size': sum(image_sizes) / len(image_sizes) if image_sizes else 0,
                'total_image_bytes': sum(image_sizes),
                'text_bytes': text_size,
                'html_bytes': html_size
            }

            self.storage_data['products'].append(product_data)
            self.storage_data['products_analyzed'] += 1
            self.storage_data['total_images'] += len(product_images)
            self.storage_data['total_image_bytes'] += sum(image_sizes)
            self.storage_data['total_text_bytes'] += text_size

            print(f"  Images: {len(product_images)} (avg {product_data['avg_image_size'] / 1024:.1f} KB)")
            print(f"  Text: {text_size / 1024:.1f} KB")
            print(f"  HTML: {html_size / 1024:.1f} KB")

            return product_data

        except Exception as e:
            print(f"  Error: {e}")
            return None

    def estimate_total_storage(self, total_products=21201):
        """Calculate total storage estimate"""
        if self.storage_data['products_analyzed'] == 0:
            return None

        # Calculate averages
        avg_images = self.storage_data['total_images'] / self.storage_data['products_analyzed']
        avg_image_bytes = self.storage_data['total_image_bytes'] / self.storage_data['products_analyzed']
        avg_text_bytes = self.storage_data['total_text_bytes'] / self.storage_data['products_analyzed']

        # Estimate total
        total_image_bytes = avg_image_bytes * total_products
        total_text_bytes = avg_text_bytes * total_products
        total_bytes = total_image_bytes + total_text_bytes

        return {
            'products_sampled': self.storage_data['products_analyzed'],
            'total_products': total_products,
            'avg_images_per_product': avg_images,
            'avg_image_storage_per_product_mb': avg_image_bytes / (1024 * 1024),
            'avg_text_storage_per_product_kb': avg_text_bytes / 1024,
            'total_image_storage_gb': total_image_bytes / (1024 * 1024 * 1024),
            'total_text_storage_mb': total_text_bytes / (1024 * 1024),
            'total_storage_gb': total_bytes / (1024 * 1024 * 1024)
        }

    def run(self, sample_file='data/freemold/sample_products_for_detail_crawl.json'):
        """Run storage estimation"""
        try:
            # Load sample products
            with open(sample_file, 'r') as f:
                products = json.load(f)

            print(f"Analyzing {len(products)} sample products...")

            self.setup_driver()
            self.login()

            # Analyze each product
            for product in products:
                self.analyze_product_page(
                    product['product_url'],
                    product['pIdx']
                )
                time.sleep(1)  # Be polite

            # Calculate estimates
            estimate = self.estimate_total_storage()

            print("\n" + "=" * 70)
            print("STORAGE ESTIMATION RESULTS")
            print("=" * 70)
            print(f"\nProducts Sampled: {estimate['products_sampled']}")
            print(f"Total Products: {estimate['total_products']:,}")
            print(f"\nAverage per Product:")
            print(f"  - Images: {estimate['avg_images_per_product']:.1f}")
            print(f"  - Image Storage: {estimate['avg_image_storage_per_product_mb']:.2f} MB")
            print(f"  - Text/Specs: {estimate['avg_text_storage_per_product_kb']:.1f} KB")
            print(f"\nTotal Storage Estimate:")
            print(f"  - Images: {estimate['total_image_storage_gb']:.2f} GB")
            print(f"  - Text/Specs: {estimate['total_text_storage_mb']:.1f} MB")
            print(f"  - TOTAL: {estimate['total_storage_gb']:.2f} GB")
            print("=" * 70)

            # Save results
            output_file = Path('data/freemold/storage_estimate_detail.json')
            with open(output_file, 'w') as f:
                json.dump({
                    'raw_data': self.storage_data,
                    'estimate': estimate
                }, f, indent=2)

            print(f"\nDetailed results saved to: {output_file}")

            return estimate

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == '__main__':
    estimator = DetailStorageEstimator()
    estimator.run()
