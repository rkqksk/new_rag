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
            'start_time': datetime.now().isoformat()
        }

        self.logged_in = False
    
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
        """Smart login: .env auto → manual fallback"""
        print("\n" + "="*70)
        print("🔐 LOGGING IN TO FREEMOLD.NET")
        print("="*70)

        # Try automatic login first if credentials available
        if USERNAME and PASSWORD:
            print("🔄 Attempting automatic login with .env credentials...")
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

                # Enter credentials (use ID to find correct fields)
                wait = WebDriverWait(driver, 10)
                username_input = wait.until(
                    EC.presence_of_element_located((By.ID, "loginId"))
                )
                password_input = driver.find_element(By.ID, "loginPw")

                username_input.clear()
                username_input.send_keys(USERNAME)
                password_input.clear()
                password_input.send_keys(PASSWORD)

                # Submit
                password_input.submit()
                time.sleep(5)

                # Verify
                if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
                    print("✅ Automatic login successful")
                    self.logged_in = True

                    # Test product page access
                    print("🧪 Testing product detail page access...")
                    test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=89037"
                    driver.get(test_url)
                    time.sleep(2)

                    # Check for alert
                    try:
                        alert = driver.switch_to.alert
                        print(f"⚠️  Alert after login: {alert.text}")
                        alert.accept()
                        print("❌ Automatic login failed - session not maintained")
                        raise Exception("Session not maintained")
                    except:
                        print("✅ Product pages accessible")
                        driver.get(LOGIN_URL)
                        time.sleep(1)
                        return True
                else:
                    raise Exception("Login verification failed")

            except Exception as e:
                print(f"⚠️  Automatic login failed: {e}")
                print("🔄 Switching to manual login...")

        else:
            print("⚠️  No credentials in .env - using manual login")

        # Manual login fallback
        print("\n" + "="*70)
        print("👤 MANUAL LOGIN REQUIRED")
        print("="*70)
        print("Please login in the browser window that will open...")
        print("Press Ctrl+C to cancel")

        # Switch to non-headless if needed
        if self.headless:
            print("⚠️  Restarting browser in visible mode for manual login...")
            driver.quit()
            driver = self.setup_driver_manual()

        driver.get(LOGIN_URL)
        input("\n✋ Press ENTER after you finish logging in... ")

        # Verify manual login
        if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
            print("✅ Manual login successful")
            self.logged_in = True
            return True
        else:
            print("❌ Manual login verification failed")
            return False

    def setup_driver_manual(self):
        """Setup driver for manual login (non-headless)"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)
        print(f"✅ Chrome driver restarted (headless=False for manual login)")
        return driver
    
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

    # Use headless=True for background execution (auto-login with .env)
    crawler = FreemoldDetailCrawler(delay_min=5.0, delay_max=7.0, headless=True)
    crawler.crawl_all(products)

if __name__ == "__main__":
    main()
