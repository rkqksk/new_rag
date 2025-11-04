from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def setup_driver():
    """Selenium WebDriver 설정"""
    chrome_options = Options()

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--headless')  # 헤드리스 모드

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    chrome_options.add_argument(f'user-agent={user_agents[0]}')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def debug_detail_page(url):
    """상세 페이지 디버깅"""
    driver = setup_driver()

    try:
        # 페이지 로드 및 대기
        driver.get(url)
        time.sleep(3)  # 초기 로드 대기

        print("🌐 Page Title:", driver.title)
        print("📍 Current URL:", driver.current_url)

        # 동적 콘텐츠 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 페이지 소스 분석 (JavaScript 렌더링 후)
        page_source = driver.page_source

        # 상세정보 추출 시도
        specs_data = {}

        # 전략 1: dl/dt/dd 구조
        try:
            dl_elements = driver.find_elements(By.CSS_SELECTOR, "dl")
            print(f"\n🔍 Found {len(dl_elements)} definition lists")

            for dl in dl_elements:
                try:
                    dt_elem = dl.find_element(By.CSS_SELECTOR, "dt")
                    dd_elem = dl.find_element(By.CSS_SELECTOR, "dd")

                    key = dt_elem.text.strip()
                    value = dd_elem.text.strip()

                    if key and value:
                        specs_data[key] = value
                        print(f"  ✅ {key}: {value}")
                except Exception as e:
                    print(f"  ❌ DL parsing error: {e}")
        except Exception as e:
            print(f"❌ DL parsing failed: {e}")

        # 전략 2: 텍스트 기반 키:값 추출
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            text_lines = [line.strip() for line in body_text.split('\n') if ':' in line]

            print(f"\n📝 Found {len(text_lines)} text lines with ':'")
            for line in text_lines[:10]:  # 최초 10개 라인만 출력
                print(f"  - {line}")
        except Exception as e:
            print(f"❌ Text parsing failed: {e}")

        # 이미지 및 기타 정보
        try:
            images = driver.find_elements(By.TAG_NAME, "img")
            print(f"\n🖼️ Found {len(images)} images")
            for img in images[:5]:  # 첫 5개 이미지만 분석
                print(f"  - {img.get_attribute('src')}")
        except Exception as e:
            print(f"❌ Image parsing failed: {e}")

        # JSON 형식으로 저장
        with open('/tmp/onehago_debug_details.json', 'w', encoding='utf-8') as f:
            json.dump({
                'title': driver.title,
                'url': driver.current_url,
                'specifications': specs_data,
                'page_source_length': len(page_source)
            }, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ Fatal Error: {e}")

    finally:
        driver.quit()

def main():
    # 제공된 상세 페이지 URL
    url = "https://onehago.com/mall/?cate_mode=view&pid=57908&no=144"
    debug_detail_page(url)

if __name__ == "__main__":
    main()