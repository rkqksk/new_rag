"""
웹 크롤링 및 스케줄링 서비스
- 제조업 관련 웹사이트 자동 크롤링
- 정기적 업데이트 스케줄링
- MSDS, 제품 정보, 업체 정보 수집
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from uuid import uuid4

import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class WebSource:
    """웹 소스 설정"""

    def __init__(
        self,
        url: str,
        selectors: Dict[str, str],
        name: str,
        category: str = "general",
        depth: int = 1,
    ):
        self.url = url
        self.selectors = selectors  # CSS 선택자 매핑
        self.name = name
        self.category = category  # product, supplier, msds, etc.
        self.depth = depth  # 크롤링 깊이
        self.last_crawled = None
        self.enabled = True


class WebCrawlerService:
    """
    웹 크롤링 및 데이터 수집 서비스
    """

    def __init__(self, document_ingestion_service=None):
        self.document_ingestion_service = document_ingestion_service
        self.sources: Dict[str, WebSource] = {}
        self.crawl_history: List[Dict[str, Any]] = []

        # 기본 크롤링 소스 설정
        self._setup_default_sources()

    def _setup_default_sources(self):
        """기본 크롤링 소스 설정"""

        # 예시 1: 제품 카탈로그 사이트
        self.sources["product_catalog"] = WebSource(
            url="https://example-product-site.com",
            selectors={
                "product_name": ".product-title",
                "description": ".product-description",
                "price": ".product-price",
                "specs": ".product-specs",
            },
            name="Product Catalog",
            category="product",
            depth=2,
        )

        # 예시 2: MSDS 데이터베이스
        self.sources["msds_db"] = WebSource(
            url="https://pubchem.ncbi.nlm.nih.gov",
            selectors={"chemical_name": ".compound-title", "properties": ".section-content"},
            name="PubChem MSDS",
            category="msds",
            depth=1,
        )

        # 예시 3: 공급업체 정보
        self.sources["supplier_info"] = WebSource(
            url="https://example-supplier-site.com",
            selectors={
                "company_name": ".company-name",
                "contact": ".contact-info",
                "products": ".product-list",
            },
            name="Supplier Directory",
            category="supplier",
            depth=1,
        )

    def add_source(self, source_id: str, web_source: WebSource):
        """크롤링 소스 추가"""
        self.sources[source_id] = web_source
        logger.info(f"Added crawling source: {source_id} ({web_source.name})")

    async def crawl_source(self, source_id: str, use_selenium: bool = False) -> Dict[str, Any]:
        """
        특정 소스 크롤링

        Args:
            source_id: 소스 ID
            use_selenium: JavaScript 렌더링이 필요한 경우 True

        Returns:
            크롤링 결과
        """
        if source_id not in self.sources:
            raise ValueError(f"Unknown source: {source_id}")

        source = self.sources[source_id]

        try:
            logger.info(f"Crawling source: {source.name} ({source.url})")

            if use_selenium or self._requires_javascript(source.url):
                data = await self._crawl_with_selenium(source)
            else:
                data = await self._crawl_with_http(source)

            # 크롤링 히스토리 기록
            crawl_record = {
                "source_id": source_id,
                "source_name": source.name,
                "crawled_at": datetime.utcnow().isoformat(),
                "items_count": len(data.get("items", [])),
                "status": "success",
            }
            self.crawl_history.append(crawl_record)
            source.last_crawled = datetime.utcnow()

            return {
                "source_id": source_id,
                "source_name": source.name,
                "category": source.category,
                "url": source.url,
                "items_count": len(data.get("items", [])),
                "items": data.get("items", []),
                "crawled_at": datetime.utcnow().isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error crawling source {source_id}: {e}")
            crawl_record = {
                "source_id": source_id,
                "source_name": source.name,
                "crawled_at": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e),
            }
            self.crawl_history.append(crawl_record)
            raise

    async def _crawl_with_http(self, source: WebSource) -> Dict[str, Any]:
        """HTTP 요청을 사용한 크롤링"""
        items = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    source.url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        items = self._parse_html(html, source)
                    else:
                        logger.warning(f"HTTP {resp.status} from {source.url}")

        except asyncio.TimeoutError:
            logger.error(f"Timeout crawling {source.url}")
        except Exception as e:
            logger.error(f"Error in HTTP crawl: {e}")

        return {"items": items}

    async def _crawl_with_selenium(self, source: WebSource) -> Dict[str, Any]:
        """Selenium을 사용한 크롤링 (JavaScript 렌더링)"""
        items = []

        try:
            # Chrome 옵션 설정
            options = Options()
            options.add_argument("--headless")  # 백그라운드 실행
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)

            try:
                driver.get(source.url)

                # 페이지 로드 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "body"))
                )

                # 페이지 렌더링 대기
                await asyncio.sleep(2)

                # HTML 파싱
                html = driver.page_source
                items = self._parse_html(html, source)

            finally:
                driver.quit()

        except Exception as e:
            logger.error(f"Error in Selenium crawl: {e}")

        return {"items": items}

    def _parse_html(self, html: str, source: WebSource) -> List[Dict[str, Any]]:
        """
        HTML 파싱 및 데이터 추출

        Args:
            html: HTML 콘텐츠
            source: 웹 소스 설정

        Returns:
            추출된 항목 리스트
        """
        items = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            # 소스별 파싱 로직
            if source.category == "product":
                items = self._parse_products(soup, source)
            elif source.category == "msds":
                items = self._parse_msds(soup, source)
            elif source.category == "supplier":
                items = self._parse_suppliers(soup, source)
            else:
                items = self._parse_generic(soup, source)

        except Exception as e:
            logger.error(f"Error parsing HTML for {source.name}: {e}")

        return items

    def _parse_products(self, soup: BeautifulSoup, source: WebSource) -> List[Dict[str, Any]]:
        """제품 정보 파싱"""
        items = []

        try:
            # 일반적인 제품 리스트 선택자
            product_elements = soup.select(".product, [data-product], .item")

            for elem in product_elements[:20]:  # 최대 20개 항목
                item = {
                    "id": str(uuid4()),
                    "source": source.name,
                    "category": "product",
                    "title": None,
                    "description": None,
                    "price": None,
                    "url": None,
                    "metadata": {},
                }

                # 커스텀 선택자 적용
                if "product_name" in source.selectors:
                    title_elem = elem.select_one(source.selectors["product_name"])
                    if title_elem:
                        item["title"] = title_elem.get_text(strip=True)

                if "description" in source.selectors:
                    desc_elem = elem.select_one(source.selectors["description"])
                    if desc_elem:
                        item["description"] = desc_elem.get_text(strip=True)

                if "price" in source.selectors:
                    price_elem = elem.select_one(source.selectors["price"])
                    if price_elem:
                        item["price"] = price_elem.get_text(strip=True)

                # URL 추출
                link = elem.find("a", href=True)
                if link:
                    item["url"] = urljoin(source.url, link["href"])

                if item["title"]:  # 제목이 있을 때만 추가
                    items.append(item)

        except Exception as e:
            logger.error(f"Error parsing products: {e}")

        return items

    def _parse_msds(self, soup: BeautifulSoup, source: WebSource) -> List[Dict[str, Any]]:
        """MSDS 정보 파싱"""
        items = []

        try:
            # PubChem 스타일 파싱
            chemical_sections = soup.select(".compound, [data-compound], .chemical")

            for section in chemical_sections[:10]:
                item = {
                    "id": str(uuid4()),
                    "source": source.name,
                    "category": "msds",
                    "chemical_name": None,
                    "properties": {},
                    "url": None,
                    "metadata": {},
                }

                # 화학물질명 추출
                name_elem = section.select_one(source.selectors.get("chemical_name", ".name"))
                if name_elem:
                    item["chemical_name"] = name_elem.get_text(strip=True)

                # 프로퍼티 추출
                prop_elem = section.select_one(source.selectors.get("properties", ".properties"))
                if prop_elem:
                    properties_text = prop_elem.get_text(strip=True)
                    item["properties"]["raw"] = properties_text

                # URL 추출
                link = section.find("a", href=True)
                if link:
                    item["url"] = urljoin(source.url, link["href"])

                if item["chemical_name"]:
                    items.append(item)

        except Exception as e:
            logger.error(f"Error parsing MSDS: {e}")

        return items

    def _parse_suppliers(self, soup: BeautifulSoup, source: WebSource) -> List[Dict[str, Any]]:
        """공급업체 정보 파싱"""
        items = []

        try:
            company_elements = soup.select(".company, [data-company], .supplier")

            for elem in company_elements[:15]:
                item = {
                    "id": str(uuid4()),
                    "source": source.name,
                    "category": "supplier",
                    "company_name": None,
                    "contact": {},
                    "products": [],
                    "url": None,
                    "metadata": {},
                }

                # 회사명 추출
                name_elem = elem.select_one(source.selectors.get("company_name", ".name"))
                if name_elem:
                    item["company_name"] = name_elem.get_text(strip=True)

                # 연락처 추출
                contact_elem = elem.select_one(source.selectors.get("contact", ".contact"))
                if contact_elem:
                    contact_text = contact_elem.get_text(strip=True)
                    item["contact"]["raw"] = contact_text

                # URL 추출
                link = elem.find("a", href=True)
                if link:
                    item["url"] = urljoin(source.url, link["href"])

                if item["company_name"]:
                    items.append(item)

        except Exception as e:
            logger.error(f"Error parsing suppliers: {e}")

        return items

    def _parse_generic(self, soup: BeautifulSoup, source: WebSource) -> List[Dict[str, Any]]:
        """일반 콘텐츠 파싱"""
        items = []

        try:
            # 모든 선택자를 시도
            for selector_name, selector in source.selectors.items():
                elements = soup.select(selector)

                for elem in elements[:10]:
                    item = {
                        "id": str(uuid4()),
                        "source": source.name,
                        "category": "generic",
                        "content": elem.get_text(strip=True)[:500],  # 처음 500자
                        "selector": selector_name,
                        "metadata": {},
                    }
                    items.append(item)

        except Exception as e:
            logger.error(f"Error parsing generic content: {e}")

        return items

    def _requires_javascript(self, url: str) -> bool:
        """URL이 JavaScript 렌더링이 필요한지 판단"""
        # 간단한 휴리스틱
        js_frameworks = ["angular", "react", "vue"]
        return any(framework in url.lower() for framework in js_frameworks)

    async def crawl_all_sources(self) -> List[Dict[str, Any]]:
        """모든 활성화된 소스 크롤링"""
        results = []

        for source_id, source in self.sources.items():
            if not source.enabled:
                continue

            try:
                result = await self.crawl_source(source_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to crawl {source_id}: {e}")

        return results

    def get_crawl_history(self, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """크롤링 히스토리 조회"""
        if source_id:
            return [record for record in self.crawl_history if record["source_id"] == source_id]
        return self.crawl_history

    def get_sources_status(self) -> List[Dict[str, Any]]:
        """모든 소스의 상태 조회"""
        status = []

        for source_id, source in self.sources.items():
            status.append(
                {
                    "source_id": source_id,
                    "name": source.name,
                    "url": source.url,
                    "category": source.category,
                    "enabled": source.enabled,
                    "last_crawled": (
                        source.last_crawled.isoformat() if source.last_crawled else None
                    ),
                    "depth": source.depth,
                }
            )

        return status
