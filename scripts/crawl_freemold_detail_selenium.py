#!/usr/bin/env python3
"""
Freemold 상세 정보 크롤러 (Selenium)
- .env 자동 로그인
- 모든 상세 정보 추출
"""
import time
import json
import random
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load .env
load_dotenv()

# Get credentials
USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')
LOGIN_URL = 'https://www.freemold.net'

class FreemoldDetailCrawler:
    def __init__(self, delay_min=5.0, delay_max=7.0, headless=True):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headless = headless
        self.output_dir = Path('data/freemold/crawled_v2')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress_selenium.json'
        self.progress = self.load_progress()

        self.stats = {
            'crawled': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat(),
            'session_refreshes': 0
        }

        self.logged_in = False
        self.last_session_check = 0  # Track when we last checked session
    
    def load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'completed': []}
    
    def save_progress(self):
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def is_completed(self, pIdx):
        return pIdx in self.progress['completed']
    
    def mark_completed(self, pIdx):
        if pIdx not in self.progress['completed']:
            self.progress['completed'].append(pIdx)
            self.save_progress()
    
    def random_delay(self):
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def check_session(self, driver):
        """Check if still logged in, refresh session if needed"""
        try:
            # Check page source for logout indicators
            page_source = driver.page_source
            if "로그인" in page_source and "로그아웃" not in page_source:
                print(f"\n⚠️  Session expired detected!")
                return False

            # Check for login-related text in page
            if "비회원" in page_source:
                print(f"\n⚠️  Non-member access detected!")
                return False

            return True
        except:
            return True  # If check fails, assume still logged in

    def refresh_session(self, driver):
        """Re-login to maintain session"""
        print(f"\n🔄 Refreshing session...")
        self.stats['session_refreshes'] += 1

        if self.login(driver):
            print(f"✅ Session refreshed successfully (Total refreshes: {self.stats['session_refreshes']})")
            return True
        else:
            print(f"❌ Session refresh failed!")
            return False
    
    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)
        print(f"✅ Chrome driver initialized (headless={self.headless})")
        return driver

    def login(self, driver):
        """Automatic login using .env credentials"""
        print("\n" + "="*70)
        print("🔐 LOGGING IN TO FREEMOLD.NET")
        print("="*70)

        try:
            driver.get(LOGIN_URL)
            time.sleep(3)

            # Remove overlay
            driver.execute_script("""
                var mask = document.getElementById('divMask');
                if (mask) mask.style.display = 'none';
            """)

            # Click login button
            driver.execute_script("""
                var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (loginBtn) {
                    loginBtn.click();
                } else if (typeof loginLayer === 'function') {
                    loginLayer();
                }
            """)

            time.sleep(2)

            # Enter credentials
            wait = WebDriverWait(driver, 10)
            username_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            username_input.clear()
            username_input.send_keys(USERNAME)
            password_input.clear()
            password_input.send_keys(PASSWORD)

            # Submit
            password_input.submit()
            time.sleep(5)

            # Verify
            if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
                print("✅ Login successful")
                self.logged_in = True

                # Save cookies for session persistence
                self.cookies = driver.get_cookies()

                # Test if we can access a product detail page
                print("🧪 Testing product detail page access...")
                test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=89037"
                driver.get(test_url)
                time.sleep(2)

                # Check for alert
                try:
                    alert = driver.switch_to.alert
                    print(f"❌ Alert detected after login: {alert.text}")
                    alert.accept()
                    print("⚠️  Cannot access product pages - login session not maintained")
                    return False
                except:
                    print("✅ Product detail page accessible")
                    # Go back to homepage
                    driver.get(LOGIN_URL)
                    time.sleep(1)

                return True
            else:
                print("❌ Login failed")
                self.logged_in = False
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            self.logged_in = False
            return False
    
    def extract_detail(self, driver, product):
        pIdx = product['pIdx']

        if self.is_completed(pIdx):
            print(f"  ✓ Already done: {pIdx}")
            return None

        url = product['product_url']

        try:
            driver.get(url)
            time.sleep(2)

            # Handle alert popup if present
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                if "비회원" in alert_text or "로그인" in alert_text:
                    print(f"  ⚠️  Login alert detected, re-logging in...")
                    alert.accept()
                    # Re-login
                    if not self.login(driver):
                        print(f"  ❌ Re-login failed for pIdx={pIdx}")
                        return None
                    # Try accessing the page again
                    driver.get(url)
                    time.sleep(2)
            except:
                pass  # No alert

            result = {
                'pIdx': pIdx,
                'mIdx': product.get('mIdx'),
                'category_code': product.get('category_code'),
                'category_name': product.get('category_name'),
                'url': url,
                'crawled_at': datetime.now().isoformat()
            }

            # Wait for table to load (JavaScript rendering)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'table'))
                )
                time.sleep(1)  # Additional buffer for full content load
            except:
                print(f"  ⚠️  No table found after 10s wait")

            # Extract from table
            tables = driver.find_elements(By.TAG_NAME, 'table')
            
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) >= 2:
                            label = cells[0].text.strip()
                            value = cells[1].text.strip()
                            
                            if '제품명' in label:
                                result['product_name'] = value
                            elif '제품규격' in label or '규격' in label:
                                result['specifications'] = value
                            elif '재질' in label:
                                result['material'] = value
                            elif 'MOQ' in label.upper():
                                result['moq'] = value
                            elif '원산지' in label:
                                result['origin'] = value
                            elif '제조사' in label or '회사명' in label:
                                result['manufacturer'] = value
                    except:
                        pass
            
            self.stats['crawled'] += 1
            self.mark_completed(pIdx)
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats['errors'] += 1
            return None
    
    def crawl_all(self, products):
        driver = self.setup_driver()

        try:
            # Automatic login
            if not self.login(driver):
                print("❌ Login failed, cannot proceed")
                return

            print("\n✅ Login confirmed! Starting crawler...")
            print(f"📊 Total products: {len(products)}")
            print(f"⏱️  Estimated time: {len(products) * 6 / 3600:.1f} hours\n")

            # Start crawling
            results = []

            for idx, product in enumerate(products, 1):
                # Periodic session check every 100 products
                if idx % 100 == 0:
                    print(f"\n🔍 Checking session status (after {idx} products)...")
                    if not self.check_session(driver):
                        print(f"⚠️  Session expired! Attempting to refresh...")
                        if not self.refresh_session(driver):
                            print(f"❌ Cannot continue without valid session")
                            break
                    else:
                        print(f"✅ Session still active")

                print(f"[{idx}/{len(products)}] pIdx={product['pIdx']}")

                result = self.extract_detail(driver, product)
                if result:
                    results.append(result)

                # Save every 50 products
                if len(results) % 50 == 0 and results:
                    output_file = self.output_dir / f"products_batch_{len(results)}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results[-50:], f, ensure_ascii=False, indent=2)
                    print(f"  💾 Saved batch: {output_file.name}")

                self.random_delay()
            
            # Final save
            final_file = self.output_dir / 'all_products_detailed.json'
            with open(final_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print("\n" + "=" * 70)
            print("✅ CRAWLING COMPLETE")
            print("=" * 70)
            print(f"Crawled: {self.stats['crawled']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"Session Refreshes: {self.stats['session_refreshes']}")
            print(f"Output: {final_file}")
            
        finally:
            driver.quit()

def main():
    # Load universal products
    universal_file = Path('data/freemold/universal/A001_products.json')

    print("=" * 70)
    print("🏭 FREEMOLD DETAIL CRAWLER (Selenium - Auto Login)")
    print("=" * 70)
    print(f"\n📂 Loading: {universal_file}")

    with open(universal_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"✅ Loaded {len(products)} products\n")

    # Use headless=False to debug login issues
    crawler = FreemoldDetailCrawler(delay_min=5.0, delay_max=7.0, headless=False)
    crawler.crawl_all(products)

if __name__ == "__main__":
    main()
