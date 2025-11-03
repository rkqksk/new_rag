#!/usr/bin/env python3
"""
🌐 FREEMOLD.NET - MANUAL BROWSER LOGIN
======================================

Simply opens Chrome browser and waits for user to manually log in.
No automation, no detection - just a simple browser for you to use.

You handle the login, then tell me what to do next.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

BASE_URL = "https://www.freemold.net"

print("=" * 80)
print("🌐 FREEMOLD.NET - MANUAL LOGIN")
print("=" * 80)
print("\n📱 Opening Chrome browser...\n")

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# NOT headless - visible window

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# Navigate to Freemold
driver.get(BASE_URL)

print("✅ Chrome browser is now open with Freemold.net")
print("\n📌 Please log in manually to your account")
print("📌 Once logged in, close this terminal message and tell me the next steps")
print("\n⏳ Browser will stay open. Take your time...\n")

# Keep browser open - don't close it
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n✅ Closing browser")
    driver.quit()
