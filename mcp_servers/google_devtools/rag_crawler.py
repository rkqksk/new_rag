"""
RAG 대시보드 자동 크롤러 v2.0
웹 인터페이스 테스트, 데이터 수집 자동화, 성능 모니터링
"""

from typing import Dict, List, Any
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CrawlReport:
    """크롤 리포트"""
    timestamp: str
    total_pages: int
    total_links: int
    average_load_time: float
    errors: List[Dict[str, Any]]
    performance_summary: Dict[str, Any]


class RAGSiteCrawler:
    """RAG Enterprise 웹 사이트 크롤러 v2.0"""

    def __init__(self, browser_automation):
        self.automation = browser_automation
        self.base_url = "http://localhost:8000"
        self.crawl_results = []
        self.errors = []

    async def crawl_dashboard_comprehensive(self) -> Dict[str, Any]:
        """대시보드 전체 크롤링 (심층 분석)"""
        logger.info("🔍 Starting comprehensive dashboard crawl...")
        
        try:
            # 1. 대시보드 페이지 접근
            nav_result = await self.automation.navigate(f"{self.base_url}/dashboard")
            if nav_result.get("status") != "success":
                self.errors.append({"step": "dashboard_navigation", "error": nav_result})
                return {"status": "error", "message": "Failed to navigate to dashboard"}

            # 2. 초기 페이지 분석
            page_data = await self.automation.crawl_page()
            metrics = await self.automation.get_performance_metrics()
            
            initial_result = {
                "page": "dashboard",
                "page_data": page_data.get("data"),
                "metrics": metrics.get("metrics"),
                "timestamp": datetime.now().isoformat()
            }
            
            self.crawl_results.append(initial_result)

            # 3. 모든 탭 순회 및 데이터 수집
            tabs_data = await self._crawl_all_tabs()

            # 4. API 엔드포인트 테스트
            api_results = await self._test_api_endpoints()

            # 5. 폼 제출 테스트
            form_results = await self._test_form_submissions()

            # 6. 스크린샷 캡처
            screenshot_result = await self.automation.take_screenshot("dashboard_full.png")

            report = {
                "status": "success",
                "workflow": "comprehensive_crawl",
                "base_url": self.base_url,
                "initial_result": initial_result,
                "tabs": tabs_data,
                "api_tests": api_results,
                "form_tests": form_results,
                "screenshot": screenshot_result,
                "total_pages_crawled": len(self.crawl_results),
                "errors": self.errors,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"✓ Comprehensive crawl completed: {len(self.crawl_results)} pages")
            return report

        except Exception as e:
            logger.error(f"✗ Comprehensive crawl failed: {e}")
            self.errors.append({"step": "comprehensive_crawl", "error": str(e)})
            return {"status": "error", "message": str(e), "errors": self.errors}

    async def _crawl_all_tabs(self) -> Dict[str, Any]:
        """모든 대시보드 탭 크롤링"""
        logger.info("📑 Crawling dashboard tabs...")
        
        tabs = {}
        tab_config = {
            "documents": {
                "selector": 'button[data-tab="documents"], a:has-text("Documents")',
                "wait_time": 1000
            },
            "search": {
                "selector": 'button[data-tab="search"], a:has-text("Search")',
                "wait_time": 1000
            },
            "crawlers": {
                "selector": 'button[data-tab="crawlers"], a:has-text("Crawlers")',
                "wait_time": 1000
            },
            "performance": {
                "selector": 'button[data-tab="performance"], a:has-text("Performance")',
                "wait_time": 1000
            },
            "settings": {
                "selector": 'button[data-tab="settings"], a:has-text("Settings")',
                "wait_time": 1000
            }
        }

        for tab_name, config in tab_config.items():
            try:
                logger.info(f"  → Crawling tab: {tab_name}")
                
                # 탭 클릭
                await self.automation.click_element(config["selector"])

                # 로드 대기
                await self.automation.page.wait_for_timeout(config["wait_time"])

                # 데이터 추출
                tab_page_data = await self.automation.crawl_page()
                tab_metrics = await self.automation.get_performance_metrics()
                
                tabs[tab_name] = {
                    "page_data": tab_page_data.get("data"),
                    "metrics": tab_metrics.get("metrics"),
                    "timestamp": datetime.now().isoformat()
                }

                self.crawl_results.append(tabs[tab_name])
                logger.info(f"  ✓ Tab {tab_name} crawled successfully")

            except Exception as e:
                logger.warning(f"  ✗ Failed to crawl tab {tab_name}: {e}")
                self.errors.append({"tab": tab_name, "error": str(e)})
                tabs[tab_name] = {"status": "error", "message": str(e)}

        return tabs

    async def _test_api_endpoints(self) -> Dict[str, Any]:
        """API 엔드포인트 테스트"""
        logger.info("🔗 Testing API endpoints...")
        
        endpoints = [
            ("Health", f"{self.base_url}/health"),
            ("Dashboard Stats", f"{self.base_url}/api/v1/dashboard/stats"),
            ("Documents", f"{self.base_url}/api/v1/dashboard/documents"),
            ("Search", f"{self.base_url}/api/v1/search?query=test"),
            ("Crawlers", f"{self.base_url}/api/v1/dashboard/crawlers"),
            ("Stats", f"{self.base_url}/api/v1/stats")
        ]

        results = {}

        for endpoint_name, url in endpoints:
            try:
                logger.info(f"  → Testing: {endpoint_name}")
                
                await self.automation.navigate(url)
                content = await self.automation.get_page_content()
                
                # JSON 파싱 시도
                try:
                    json_data = json.loads(content.get("content", "{}"))
                    results[endpoint_name.lower()] = {
                        "status": "success",
                        "url": url,
                        "data": json_data
                    }
                except:
                    results[endpoint_name.lower()] = {
                        "status": "success",
                        "url": url,
                        "content_length": content.get("length")
                    }

                logger.info(f"  ✓ {endpoint_name} tested")

            except Exception as e:
                logger.warning(f"  ✗ {endpoint_name} test failed: {e}")
                self.errors.append({"endpoint": endpoint_name, "error": str(e)})
                results[endpoint_name.lower()] = {"status": "error", "message": str(e)}

        return results

    async def _test_form_submissions(self) -> Dict[str, Any]:
        """폼 제출 테스트"""
        logger.info("📝 Testing form submissions...")
        
        try:
            # 대시보드로 돌아가기
            await self.automation.navigate(f"{self.base_url}/dashboard")

            # 검색 폼 테스트
            search_results = {}
            test_queries = ["test", "product", "defect"]

            for query in test_queries:
                try:
                    logger.info(f"  → Testing search query: {query}")
                    
                    # 검색 탭 클릭
                    await self.automation.click_element('button[data-tab="search"], a:has-text("Search")')
                    await self.automation.page.wait_for_timeout(500)

                    # 검색 입력
                    search_input = await self.automation.evaluate_javascript("""
                        () => {
                            const input = document.querySelector('#search-query, [placeholder*="search" i]');
                            return input ? input.getAttribute('class') : null;
                        }
                    """)

                    if search_input.get("result"):
                        # 폼 채우기
                        await self.automation.fill_form({
                            "#search-query, [placeholder*='search' i]": query
                        })

                        # 검색 버튼 클릭
                        await self.automation.click_element('button:has-text("Search"), button[type="submit"]')
                        await self.automation.page.wait_for_timeout(1000)

                        # 결과 페이지 크롤링
                        result_data = await self.automation.crawl_page()
                        
                        search_results[query] = {
                            "status": "success",
                            "query": query,
                            "results_count": len(result_data.get("data", {}).get("text", "")) 
                        }

                        logger.info(f"  ✓ Search query '{query}' tested")

                except Exception as e:
                    logger.warning(f"  ✗ Search query '{query}' failed: {e}")
                    self.errors.append({"search_query": query, "error": str(e)})
                    search_results[query] = {"status": "error", "message": str(e)}

            return {"search_tests": search_results}

        except Exception as e:
            logger.error(f"✗ Form submission tests failed: {e}")
            self.errors.append({"step": "form_submission_tests", "error": str(e)})
            return {"status": "error", "message": str(e)}

    async def monitor_performance_detailed(self) -> Dict[str, Any]:
        """상세 성능 모니터링"""
        logger.info("📊 Starting detailed performance monitoring...")
        
        performance_data = {}
        pages = [
            ("dashboard", f"{self.base_url}/dashboard"),
            ("api_docs", f"{self.base_url}/docs"),
            ("health", f"{self.base_url}/health"),
        ]

        samples_per_page = 3

        for page_name, url in pages:
            try:
                logger.info(f"  → Monitoring: {page_name}")
                
                metrics_samples = []

                for i in range(samples_per_page):
                    try:
                        await self.automation.navigate(url)
                        metrics = await self.automation.get_performance_metrics()
                        metrics_samples.append(metrics.get("metrics", {}))
                    except Exception as e:
                        logger.warning(f"    Sample {i + 1} failed: {e}")

                # 평균 계산
                if metrics_samples:
                    avg_metrics = self._calculate_average_metrics(metrics_samples)
                    performance_data[page_name] = {
                        "url": url,
                        "samples": len(metrics_samples),
                        "average_metrics": avg_metrics,
                        "all_samples": metrics_samples
                    }
                    logger.info(f"  ✓ {page_name} monitoring completed ({len(metrics_samples)} samples)")

            except Exception as e:
                logger.error(f"  ✗ Monitoring failed for {page_name}: {e}")
                self.errors.append({"monitoring": page_name, "error": str(e)})
                performance_data[page_name] = {"error": str(e)}

        return {
            "status": "success",
            "workflow": "performance_monitoring",
            "performance_data": performance_data,
            "timestamp": datetime.now().isoformat()
        }

    async def take_full_report(self) -> Dict[str, Any]:
        """전체 리포트 생성"""
        logger.info("📋 Generating full report...")
        
        try:
            report = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "sections": {
                    "dashboard_crawl": await self.crawl_dashboard_comprehensive(),
                    "performance_monitoring": await self.monitor_performance_detailed(),
                }
            }

            logger.info("✓ Full report generated")
            return report

        except Exception as e:
            logger.error(f"✗ Report generation failed: {e}")
            return {"status": "error", "message": str(e), "errors": self.errors}

    @staticmethod
    def _calculate_average_metrics(metrics_list: List[Dict]) -> Dict[str, float]:
        """메트릭 평균 계산"""
        if not metrics_list:
            return {}

        # 첫 번째 메트릭에서 키 추출
        first_metrics = metrics_list[0]
        if not first_metrics:
            return {}

        averages = {}

        for key in first_metrics.keys():
            values = []
            for m in metrics_list:
                val = m.get(key)
                if isinstance(val, (int, float)):
                    values.append(val)

            if values:
                averages[key] = sum(values) / len(values)

        return averages


class RegressionTester:
    """회귀 테스트"""

    def __init__(self, crawler: RAGSiteCrawler):
        self.crawler = crawler
        self.baseline = None
        self.current = None

    async def run_regression_tests(self) -> Dict[str, Any]:
        """회귀 테스트 실행"""
        logger.info("🧪 Running regression tests...")
        
        try:
            self.current = await self.crawler.crawl_dashboard_comprehensive()

            if not self.baseline:
                logger.info("⚠️ No baseline available, using current as baseline")
                self.baseline = self.current
                return {
                    "status": "baseline_created",
                    "message": "Baseline created from current run"
                }

            # 비교 분석
            comparison = self._compare_results(self.baseline, self.current)

            return {
                "status": "success",
                "workflow": "regression_tests",
                "comparison": comparison,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"✗ Regression tests failed: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _compare_results(baseline: Dict, current: Dict) -> Dict[str, Any]:
        """결과 비교"""
        comparison = {
            "differences": [],
            "performance_changes": {}
        }

        # 기본 비교 (구조 검증)
        if baseline.get("status") != current.get("status"):
            comparison["differences"].append({
                "field": "status",
                "baseline": baseline.get("status"),
                "current": current.get("status")
            })

        return comparison
