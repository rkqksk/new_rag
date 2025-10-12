import os
import requests
import time
import json
import random
import re
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 8.0; SM-G950F)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0)",
    "Googlebot/2.1 (+http://www.google.com/bot.html)"
]

def safe_write(path, content, mode="w", encoding="utf-8"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding=encoding if "b" not in mode else None) as f:
        f.write(content)

def robust_get(session, url, headers, max_retry=3):
    for attempt in range(max_retry):
        try:
            h = dict(headers or {})
            if 'User-Agent' not in h:
                h['User-Agent'] = random.choice(USER_AGENTS)
            h['Referer'] = h.get('Referer', url)
            resp = session.get(url, headers=h, timeout=20)
            if resp.status_code == 200:
                return resp
        except Exception as e:
            print(f"[요청 실패 {attempt+1}/{max_retry}]: {url} — {e}")
        time.sleep(2)
    return None

def get_detail_urls(start_url, domain_keyword, detail_url_pattern, headers, sleep_sec=0.5, max_depth=4):
    session = requests.Session()
    visited, collected = set(), set()
    to_crawl = [(start_url, 0)]
    while to_crawl:
        url, depth = to_crawl.pop()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)
        resp = robust_get(session, url, headers)
        if not resp: continue
        soup = BeautifulSoup(resp.content, "html.parser")
        # 패턴 기반 상세 url 수집
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = requests.compat.urljoin(url, href)
            if domain_keyword not in full_url or full_url in visited: continue
            if detail_url_pattern in full_url:
                collected.add(full_url)
            # 추가로 탐색 확장
            if full_url.startswith("http") and full_url not in visited:
                to_crawl.append((full_url, depth+1))
        time.sleep(sleep_sec)
    return list(collected)

def scrape_product_detail(url, site):
    session = requests.Session()
    headers = dict(site.get("headers", {}))
    if "User-Agent" not in headers:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    resp = robust_get(session, url, headers)
    if not resp:
        return None
    soup = BeautifulSoup(resp.content, "html.parser")
    page_text = soup.get_text()
    # 키워드 필터: product_keywords 포함 없으면 배제
    product_keywords = site.get("product_keywords", [])
    if product_keywords and not any(k in page_text for k in product_keywords):
        return None
    # 이미지 추출 (공통: /upload/ 등)
    images = [requests.compat.urljoin(url, img['src'])
              for img in soup.find_all('img') if img.get('src') and '/upload/' in img['src']]
    # 설명 추출: description_selectors 사용
    description = {}
    for sel in site.get("description_selectors", []):
        for block in soup.select(sel):
            txt = block.get_text(strip=True)
            if ":" in txt:
                k, v = txt.split(":", 1)
                description[k.strip()] = v.strip()
            else:
                # 일괄 패턴 추출(제품명/코드/치수 등)
                for field in ["제품명", "제품 코드", "재질", "사양"]:
                    if field in txt:
                        description[field] = re.sub(field, "", txt).strip()
    # 다운로드/첨부
    download_link = None
    for a in soup.find_all('a', href=True):
        if any(word in a.get_text() for word in ["인쇄", "스펙", "치수", "pdf", "도면"]):
            download_link = requests.compat.urljoin(url, a['href'])
            break
    return {
        "url": url,
        "images": images,
        "description": description,
        "download_link": download_link
    }

def run_crawler_from_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    assert "sites" in config, "'sites' 키가 필요합니다."
    for site in config["sites"]:
        print(f"\n=== {site['site_name']} 크롤링 시작 ===")
        output = []
        output_folder = site["output_folder"]
        os.makedirs(output_folder, exist_ok=True)
        detail_urls = get_detail_urls(
            start_url = site["base_url"],
            domain_keyword = site["domain_keyword"],
            detail_url_pattern = site.get("detail_url_pattern", "/product/view"),
            headers = site.get("headers", {}),
            sleep_sec = site.get("sleep_sec", 1),
            max_depth = site.get("max_depth", 4),
        )
        print(f"총 {len(detail_urls)}개 상세페이지 수집됨")
        for url in detail_urls:
            data = scrape_product_detail(url, site)
            if data: output.append(data)
            time.sleep(site.get("sleep_sec", 1))
        safe_write(os.path.join(output_folder, "products.json"),
                   json.dumps(output, ensure_ascii=False, indent=2))
        print(f"=== {site['site_name']} 크롤링 완료 ({len(output)}건 저장) ===")

if __name__ == "__main__":
    config_fn = input("config 파일명(예: agents/agent_config.json): ").strip()
    run_crawler_from_config(config_fn)
