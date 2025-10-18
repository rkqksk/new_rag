"""
카테고리 기반 자동 크롤링 Spider v1.0
Google DevTools MCP를 활용한 사이트 전체 탐색

기능:
- 카테고리 자동 탐색
- 제품 링크 자동 수집
- 중복 방지 및 진행상황 저장
- 재개 가능한 크롤링
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Optional
from urllib.parse import urljoin, urlparse

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.google_devtools.server import DevToolsAutomation
from mcp_servers.google_devtools.product_crawler import ProductPageCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CategorySpider:
    """카테고리 기반 자동 크롤링 Spider"""

    def __init__(
        self,
        base_url: str,
        output_dir: str = "data/spider_crawled",
        state_file: str = "data/spider_state.json"
    ):
        """
        Args:
            base_url: 사이트 베이스 URL
            output_dir: 크롤링 데이터 저장 디렉토리
            state_file: 진행상황 저장 파일
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.state_file = Path(state_file)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 크롤링 상태
        self.visited_urls: Set[str] = set()
        self.product_urls: List[str] = []
        self.failed_urls: List[str] = []

        # 컴포넌트
        self.automation = DevToolsAutomation()
        self.product_crawler = ProductPageCrawler(output_dir=str(self.output_dir))

        # 상태 로드
        self._load_state()

    def _load_state(self):
        """저장된 크롤링 상태 로드"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.visited_urls = set(state.get('visited_urls', []))
                self.product_urls = state.get('product_urls', [])
                self.failed_urls = state.get('failed_urls', [])
                logger.info(f"✓ 상태 로드: 방문 {len(self.visited_urls)}, 제품 {len(self.product_urls)}")

    def _save_state(self):
        """크롤링 상태 저장"""
        state = {
            'visited_urls': list(self.visited_urls),
            'product_urls': self.product_urls,
            'failed_urls': self.failed_urls,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    async def discover_categories(
        self,
        start_url: str,
        category_selector: str = "a[href*='list.php']"
    ) -> List[str]:
        """
        카테고리 페이지 자동 탐색

        Args:
            start_url: 시작 페이지 (보통 제품 메인)
            category_selector: 카테고리 링크 CSS 셀렉터

        Returns:
            카테고리 페이지 URL 목록
        """
        logger.info(f"🔍 카테고리 탐색 시작: {start_url}")

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")

            # 페이지 로드
            await self.automation.navigate(start_url)

            # 카테고리 링크 추출
            # JavaScript 문자열로 셀렉터 변환 (작은따옴표 이스케이프)
            js_selector = category_selector.replace("'", "\\'")

            js_code = f"""
            () => {{
                const links = Array.from(document.querySelectorAll("{js_selector}"));
                return links.map(a => ({{
                    href: a.href,
                    text: a.textContent.trim()
                }}));
            }}
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                categories = result.get('result', [])
                category_urls = [cat['href'] for cat in categories if cat['href']]

                # 중복 제거
                category_urls = list(dict.fromkeys(category_urls))

                logger.info(f"✓ {len(category_urls)}개 카테고리 발견")
                for i, cat in enumerate(categories[:len(category_urls)], 1):
                    logger.info(f"  {i}. {cat.get('text', 'N/A')}: {cat.get('href', 'N/A')}")

                await self.automation.close_browser()
                return category_urls
            else:
                raise Exception(f"카테고리 추출 실패: {result}")

        except Exception as e:
            logger.error(f"✗ 카테고리 탐색 실패: {e}")
            await self.automation.close_browser()
            return []

    async def extract_product_links_from_category(
        self,
        category_url: str,
        product_link_selector: str = "a[href*='view.php']",
        limit: Optional[int] = None
    ) -> List[str]:
        """
        카테고리 페이지에서 제품 링크 추출

        Args:
            category_url: 카테고리 페이지 URL
            product_link_selector: 제품 링크 CSS 셀렉터
            limit: 추출할 최대 개수 (None이면 전체)

        Returns:
            제품 페이지 URL 목록
        """
        logger.info(f"📦 제품 링크 추출: {category_url}")

        try:
            # 이미 방문한 URL이면 스킵
            if category_url in self.visited_urls:
                logger.info(f"⏭️  이미 방문한 카테고리, 스킵")
                return []

            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(category_url)

            # 제품 링크 추출
            js_selector = product_link_selector.replace("'", "\\'")

            js_code = f"""
            () => {{
                const links = Array.from(document.querySelectorAll("{js_selector}"));
                return links.map(a => a.href).filter((v, i, a) => a.indexOf(v) === i);
            }}
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                product_links = result.get('result', [])

                # limit 적용
                if limit:
                    product_links = product_links[:limit]

                logger.info(f"✓ {len(product_links)}개 제품 링크 발견")

                # 방문 완료 표시
                self.visited_urls.add(category_url)

                await self.automation.close_browser()
                return product_links
            else:
                raise Exception(f"제품 링크 추출 실패: {result}")

        except Exception as e:
            logger.error(f"✗ 제품 링크 추출 실패: {e}")
            self.failed_urls.append(category_url)
            await self.automation.close_browser()
            return []

    async def crawl_by_categories(
        self,
        start_url: str,
        limit_per_category: Optional[int] = None,
        category_selector: str = "a[href*='list.php']",
        product_selector: str = "a[href*='view.php']"
    ) -> Dict[str, Any]:
        """
        카테고리 기반 전체 크롤링

        Args:
            start_url: 시작 페이지
            limit_per_category: 카테고리당 최대 제품 수
            category_selector: 카테고리 링크 셀렉터
            product_selector: 제품 링크 셀렉터

        Returns:
            크롤링 요약
        """
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("🕷️  카테고리 기반 Spider 크롤링 시작")
        logger.info("="*60)

        # 1. 카테고리 탐색
        logger.info("\n[1/3] 카테고리 탐색 중...")
        categories = await self.discover_categories(start_url, category_selector)

        if not categories:
            logger.error("카테고리를 찾을 수 없습니다")
            return {"status": "error", "message": "No categories found"}

        # 2. 각 카테고리에서 제품 링크 수집
        logger.info(f"\n[2/3] {len(categories)}개 카테고리에서 제품 링크 수집 중...")

        all_product_urls = []

        for i, cat_url in enumerate(categories, 1):
            logger.info(f"\n  [{i}/{len(categories)}] {cat_url}")

            product_links = await self.extract_product_links_from_category(
                cat_url,
                product_link_selector=product_selector,
                limit=limit_per_category
            )

            all_product_urls.extend(product_links)

            # 진행상황 저장
            self.product_urls = all_product_urls
            self._save_state()

            # 다음 카테고리 전 대기
            if i < len(categories):
                await asyncio.sleep(1)

        # 중복 제거
        unique_products = list(dict.fromkeys(all_product_urls))
        logger.info(f"\n✓ 총 {len(unique_products)}개 제품 발견 (중복 제거 후)")

        # 3. 제품 크롤링
        logger.info(f"\n[3/3] {len(unique_products)}개 제품 크롤링 중...")

        crawl_results = []
        success_count = 0
        error_count = 0

        for i, product_url in enumerate(unique_products, 1):
            logger.info(f"\n  [{i}/{len(unique_products)}] {product_url}")

            try:
                result = await self.product_crawler.crawl_product_page(product_url)

                if result.get('status') == 'success':
                    success_count += 1
                    logger.info(f"    ✓ {result['product_data'].get('product_name', 'N/A')}")
                else:
                    error_count += 1
                    logger.warning(f"    ✗ 실패")

                crawl_results.append(result)

                # 진행상황 저장
                self._save_state()

                # 다음 제품 전 대기
                if i < len(unique_products):
                    await asyncio.sleep(2)

            except Exception as e:
                error_count += 1
                logger.error(f"    ✗ 에러: {e}")
                crawl_results.append({
                    "status": "error",
                    "url": product_url,
                    "message": str(e)
                })

        # 4. 최종 요약
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "status": "completed",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "categories_found": len(categories),
            "products_found": len(unique_products),
            "products_crawled": len(crawl_results),
            "success": success_count,
            "error": error_count,
            "results": crawl_results
        }

        # 요약 저장
        summary_path = self.output_dir / f"spider_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info("\n" + "="*60)
        logger.info("✅ Spider 크롤링 완료!")
        logger.info("="*60)
        logger.info(f"카테고리: {len(categories)}개")
        logger.info(f"제품 발견: {len(unique_products)}개")
        logger.info(f"크롤링 성공: {success_count}개")
        logger.info(f"크롤링 실패: {error_count}개")
        logger.info(f"소요 시간: {duration:.1f}초")
        logger.info(f"요약 저장: {summary_path}")

        return summary


async def main():
    """청진코리아 테스트 - 각 카테고리별 첫 번째 제품만 (품질 개선 테스트)"""

    # 청진코리아 설정
    chungjin_config = {
        "base_url": "http://chungjinkorea.com",
        "start_url": "http://chungjinkorea.com/kr/product/list.php",
        "category_selector": "a[href*='list.php']",
        "product_selector": "a[href*='view.php']"
    }

    spider = CategorySpider(
        base_url=chungjin_config["base_url"],
        output_dir="data/spider_quality_test",
        state_file="data/spider_quality_test_state.json"
    )

    # 카테고리별 첫 번째 제품만 크롤링 (품질 테스트)
    summary = await spider.crawl_by_categories(
        start_url=chungjin_config["start_url"],
        limit_per_category=1,  # 카테고리당 1개만! (품질 검증)
        category_selector=chungjin_config["category_selector"],
        product_selector=chungjin_config["product_selector"]
    )

    print("\n" + "="*60)
    print("품질 개선 테스트 결과")
    print("="*60)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
