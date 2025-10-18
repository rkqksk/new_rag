"""
Google DevTools MCP Server v2.0
크롤링 자동화, 디버깅, 성능 모니터링 강화 버전
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import sys
import os
from datetime import datetime
from dataclasses import asdict, dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.types as types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Initialize MCP Server
server = Server("google-devtools-mcp")


@dataclass
class CrawlMetrics:
    """크롤링 메트릭"""
    url: str
    status_code: int
    load_time: float
    total_elements: int
    total_links: int
    total_images: int
    total_forms: int
    memory_usage: int
    timestamp: str


class AutomationWorkflow:
    """자동화 워크플로우 관리"""

    def __init__(self):
        self.workflows = {}
        self.results = {}

    async def execute_workflow(
        self,
        workflow_type: str,
        config: Dict[str, Any],
        automation: 'DevToolsAutomation'
    ) -> Dict[str, Any]:
        """워크플로우 실행"""
        if workflow_type == "crawl":
            return await self._crawl_workflow(config, automation)
        elif workflow_type == "debug":
            return await self._debug_workflow(config, automation)
        elif workflow_type == "performance_monitor":
            return await self._performance_workflow(config, automation)
        else:
            return {"error": f"Unknown workflow: {workflow_type}"}

    async def _crawl_workflow(
        self,
        config: Dict[str, Any],
        automation: 'DevToolsAutomation'
    ) -> Dict[str, Any]:
        """크롤링 워크플로우"""
        url = config.get("url")
        depth = config.get("depth", 1)
        max_pages = config.get("max_pages", 10)
        extract_data = config.get("extract_data", True)

        visited = set()
        results = []

        async def crawl_recursive(current_url: str, current_depth: int):
            if current_depth > depth or len(visited) >= max_pages:
                return

            if current_url in visited:
                return

            visited.add(current_url)
            logger.info(f"Crawling: {current_url} (depth: {current_depth})")

            try:
                await automation.navigate(current_url)
                page_data = await automation.crawl_page()
                metrics = await automation.get_performance_metrics()

                result = {
                    "url": current_url,
                    "depth": current_depth,
                    "page_data": page_data.get("data"),
                    "metrics": metrics.get("metrics"),
                    "timestamp": datetime.now().isoformat()
                }

                if extract_data:
                    result["extracted_content"] = await automation.get_page_content()

                results.append(result)

                # 다음 깊이 크롤링
                if current_depth < depth:
                    links = page_data.get("data", {}).get("links", [])
                    for link in links[:5]:  # 최대 5개 링크만
                        next_url = link.get("href")
                        if next_url and not next_url.startswith("#"):
                            try:
                                await crawl_recursive(next_url, current_depth + 1)
                            except Exception as e:
                                logger.warning(f"Failed to crawl link {next_url}: {e}")

            except Exception as e:
                logger.error(f"Crawl error for {current_url}: {e}")

        await crawl_recursive(url, 0)

        return {
            "status": "success",
            "workflow": "crawl",
            "pages_crawled": len(visited),
            "results": results
        }

    async def _debug_workflow(
        self,
        config: Dict[str, Any],
        automation: 'DevToolsAutomation'
    ) -> Dict[str, Any]:
        """디버깅 워크플로우"""
        url = config.get("url")
        check_js_errors = config.get("check_js_errors", True)
        check_console = config.get("check_console", True)
        take_screenshot = config.get("take_screenshot", True)

        debug_info = {}

        try:
            await automation.navigate(url)

            # JS 에러 확인
            if check_js_errors:
                js_errors = await automation.evaluate_javascript("""
                    () => {
                        return window.__jsErrors || [];
                    }
                """)
                debug_info["js_errors"] = js_errors

            # 콘솔 메시지 확인
            if check_console:
                console_logs = await automation.evaluate_javascript("""
                    () => {
                        return window.__consoleLogs || [];
                    }
                """)
                debug_info["console_logs"] = console_logs

            # 성능 메트릭
            metrics = await automation.get_performance_metrics()
            debug_info["performance"] = metrics.get("metrics")

            # 스크린샷
            if take_screenshot:
                screenshot_result = await automation.take_screenshot("debug_screenshot.png")
                debug_info["screenshot"] = screenshot_result

            # DOM 분석
            dom_analysis = await automation.evaluate_javascript("""
                () => ({
                    totalNodes: document.querySelectorAll('*').length,
                    totalStylesheets: document.styleSheets.length,
                    totalScripts: document.querySelectorAll('script').length,
                    totalFonts: document.fonts.size,
                    unusedCss: 'detection not implemented yet'
                })
            """)
            debug_info["dom_analysis"] = dom_analysis

            return {
                "status": "success",
                "workflow": "debug",
                "url": url,
                "debug_info": debug_info,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Debug workflow error: {e}")
            return {"status": "error", "message": str(e)}

    async def _performance_workflow(
        self,
        config: Dict[str, Any],
        automation: 'DevToolsAutomation'
    ) -> Dict[str, Any]:
        """성능 모니터링 워크플로우"""
        urls = config.get("urls", [])
        sample_count = config.get("sample_count", 5)

        performance_results = []

        for url in urls:
            try:
                metrics_samples = []

                for i in range(sample_count):
                    await automation.navigate(url)
                    metrics = await automation.get_performance_metrics()
                    metrics_samples.append(metrics.get("metrics"))

                # 평균 계산
                avg_metrics = self._calculate_average_metrics(metrics_samples)

                performance_results.append({
                    "url": url,
                    "samples": sample_count,
                    "average_metrics": avg_metrics,
                    "samples": metrics_samples
                })

            except Exception as e:
                logger.error(f"Performance monitoring error for {url}: {e}")
                performance_results.append({
                    "url": url,
                    "error": str(e)
                })

        return {
            "status": "success",
            "workflow": "performance_monitor",
            "results": performance_results,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def _calculate_average_metrics(metrics_list: List[Dict]) -> Dict[str, float]:
        """메트릭 평균 계산"""
        if not metrics_list:
            return {}

        keys = metrics_list[0].keys()
        averages = {}

        for key in keys:
            values = [m.get(key, 0) for m in metrics_list if isinstance(m.get(key), (int, float))]
            if values:
                averages[key] = sum(values) / len(values)

        return averages


class DevToolsAutomation:
    """Google DevTools 기반 브라우저 자동화"""

    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.workflow_manager = AutomationWorkflow()
        self.retry_attempts = 3

    async def launch_browser(self, headless: bool = True, viewport: Optional[Dict] = None, browser_type: str = "webkit") -> Dict[str, Any]:
        """브라우저 시작 - macOS에서는 WebKit 권장"""
        try:
            from playwright.async_api import async_playwright
            import platform

            playwright = await async_playwright().start()

            # macOS에서는 WebKit (Safari 엔진)이 더 안정적
            if browser_type == "webkit":
                logger.info("Using WebKit (Safari engine) - best for macOS")
                self.browser = await playwright.webkit.launch(headless=headless)
            elif browser_type == "firefox":
                logger.info("Using Firefox engine")
                self.browser = await playwright.firefox.launch(headless=headless)
            else:  # chromium
                logger.info("Using Chromium engine")
                # macOS 호환성을 위한 launch args 추가
                launch_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
                self.browser = await playwright.chromium.launch(
                    headless=headless,
                    args=launch_args
                )

            context_options = {}
            if viewport:
                context_options["viewport"] = viewport

            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()

            # 콘솔 및 에러 리스닝 설정
            self.page.on("console", lambda msg: logger.info(f"Console: {msg.text}"))
            self.page.on("pageerror", lambda err: logger.error(f"Page error: {err}"))

            logger.info("✓ Browser launched successfully")
            return {"status": "success", "message": "Browser launched"}

        except Exception as e:
            logger.error(f"✗ Failed to launch browser: {e}")
            return {"status": "error", "message": str(e)}

    async def navigate(self, url: str, wait_until: str = "networkidle", timeout: int = 30000) -> Dict[str, Any]:
        """URL로 이동"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            start_time = asyncio.get_event_loop().time()
            
            for attempt in range(self.retry_attempts):
                try:
                    await self.page.goto(url, wait_until=wait_until, timeout=timeout)
                    load_time = asyncio.get_event_loop().time() - start_time
                    title = await self.page.title()

                    logger.info(f"✓ Navigated to {url} in {load_time:.2f}s")
                    return {
                        "status": "success",
                        "url": url,
                        "title": title,
                        "load_time": load_time
                    }
                except Exception as e:
                    if attempt < self.retry_attempts - 1:
                        logger.warning(f"Navigation attempt {attempt + 1} failed, retrying: {e}")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise

        except Exception as e:
            logger.error(f"✗ Navigation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def take_screenshot(self, filename: str = "screenshot.png") -> Dict[str, Any]:
        """스크린샷 캡처"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            path = f"/tmp/{filename}"
            await self.page.screenshot(path=path)

            logger.info(f"✓ Screenshot saved to {path}")
            return {
                "status": "success",
                "path": path,
                "filename": filename
            }

        except Exception as e:
            logger.error(f"✗ Screenshot failed: {e}")
            return {"status": "error", "message": str(e)}

    async def evaluate_javascript(self, code: str) -> Dict[str, Any]:
        """JavaScript 실행"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            result = await self.page.evaluate(code)

            logger.debug(f"✓ JS evaluation successful")
            return {
                "status": "success",
                "result": result,
                "type": type(result).__name__
            }

        except Exception as e:
            logger.error(f"✗ JS evaluation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_page_content(self) -> Dict[str, Any]:
        """페이지 HTML 콘텐츠 추출"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            content = await self.page.content()

            logger.debug(f"✓ Page content extracted ({len(content)} bytes)")
            return {
                "status": "success",
                "length": len(content),
                "content": content
            }

        except Exception as e:
            logger.error(f"✗ Failed to get page content: {e}")
            return {"status": "error", "message": str(e)}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 수집"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            metrics = await self.page.evaluate("""
                () => ({
                    navigationStart: performance.timing.navigationStart,
                    loadEventEnd: performance.timing.loadEventEnd,
                    loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                    domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
                    firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
                    largestContentfulPaint: performance.getEntriesByName('largest-contentful-paint')[0]?.startTime || 0,
                    memory: performance.memory ? {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                        heapUsagePercent: (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit * 100).toFixed(2)
                    } : null
                })
            """)

            logger.debug(f"✓ Performance metrics collected")
            return {
                "status": "success",
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"✗ Failed to get metrics: {e}")
            return {"status": "error", "message": str(e)}

    async def crawl_page(self) -> Dict[str, Any]:
        """페이지의 모든 링크와 데이터 크롤링"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            page_data = await self.page.evaluate("""
                () => ({
                    url: window.location.href,
                    title: document.title,
                    headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent.trim()),
                    links: Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href
                    })),
                    tables: Array.from(document.querySelectorAll('table')).length,
                    forms: Array.from(document.querySelectorAll('form')).length,
                    images: Array.from(document.querySelectorAll('img')).length,
                    text: document.body.innerText.substring(0, 5000)
                })
            """)

            logger.debug(f"✓ Page crawled successfully")
            return {
                "status": "success",
                "data": page_data
            }

        except Exception as e:
            logger.error(f"✗ Crawl failed: {e}")
            return {"status": "error", "message": str(e)}

    async def click_element(self, selector: str) -> Dict[str, Any]:
        """요소 클릭"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            await self.page.click(selector)
            await self.page.wait_for_load_state("networkidle", timeout=10000)

            logger.info(f"✓ Clicked {selector}")
            return {"status": "success", "message": f"Clicked {selector}"}

        except Exception as e:
            logger.error(f"✗ Click failed: {e}")
            return {"status": "error", "message": str(e)}

    async def fill_form(self, data: Dict[str, str]) -> Dict[str, Any]:
        """폼 채우기"""
        try:
            if not self.page:
                return {"status": "error", "message": "Browser not launched"}

            for selector, value in data.items():
                await self.page.fill(selector, value)

            logger.info(f"✓ Form filled with {len(data)} fields")
            return {"status": "success", "message": f"Form filled with {len(data)} fields"}

        except Exception as e:
            logger.error(f"✗ Form fill failed: {e}")
            return {"status": "error", "message": str(e)}

    async def close_browser(self) -> Dict[str, Any]:
        """브라우저 종료"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()

            logger.info("✓ Browser closed")
            return {"status": "success", "message": "Browser closed"}

        except Exception as e:
            logger.error(f"✗ Close failed: {e}")
            return {"status": "error", "message": str(e)}


# Global automation instance
automation = DevToolsAutomation()


# ============================================================
# MCP Tools Definition
# ============================================================

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """사용 가능한 도구 목록"""
    return [
        types.Tool(
            name="launch_browser",
            description="브라우저 시작 (Chrome/Chromium)",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {
                        "type": "boolean",
                        "description": "헤드리스 모드 (기본값: true)"
                    },
                    "viewport": {
                        "type": "object",
                        "description": "뷰포트 설정 (width, height)"
                    }
                }
            }
        ),
        types.Tool(
            name="navigate",
            description="URL로 이동",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "방문할 URL"
                    },
                    "wait_until": {
                        "type": "string",
                        "description": "대기 조건 (load, domcontentloaded, networkidle)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "타임아웃 (밀리초)"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="screenshot",
            description="현재 페이지의 스크린샷 캡처",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "저장할 파일명"
                    }
                }
            }
        ),
        types.Tool(
            name="evaluate_js",
            description="JavaScript 코드 실행",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "실행할 JavaScript 코드"
                    }
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="get_page_content",
            description="페이지의 HTML 콘텐츠 추출",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_metrics",
            description="페이지 성능 메트릭 수집",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="crawl_page",
            description="페이지의 모든 링크와 데이터 크롤링",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="execute_workflow",
            description="자동화 워크플로우 실행 (crawl, debug, performance_monitor)",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_type": {
                        "type": "string",
                        "description": "워크플로우 타입: crawl, debug, performance_monitor"
                    },
                    "config": {
                        "type": "object",
                        "description": "워크플로우 설정"
                    }
                },
                "required": ["workflow_type", "config"]
            }
        ),
        types.Tool(
            name="click_element",
            description="CSS 셀렉터로 요소 클릭",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 셀렉터"
                    }
                },
                "required": ["selector"]
            }
        ),
        types.Tool(
            name="fill_form",
            description="폼 필드 채우기",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "셀렉터: 값 매핑"
                    }
                },
                "required": ["data"]
            }
        ),
        types.Tool(
            name="close_browser",
            description="브라우저 종료",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """도구 실행"""
    logger.info(f"Tool called: {name}")

    try:
        if name == "launch_browser":
            result = await automation.launch_browser(
                headless=arguments.get("headless", True),
                viewport=arguments.get("viewport")
            )
        elif name == "navigate":
            result = await automation.navigate(
                arguments["url"],
                wait_until=arguments.get("wait_until", "networkidle"),
                timeout=arguments.get("timeout", 30000)
            )
        elif name == "screenshot":
            result = await automation.take_screenshot(
                arguments.get("filename", "screenshot.png")
            )
        elif name == "evaluate_js":
            result = await automation.evaluate_javascript(arguments["code"])
        elif name == "get_page_content":
            result = await automation.get_page_content()
        elif name == "get_metrics":
            result = await automation.get_performance_metrics()
        elif name == "crawl_page":
            result = await automation.crawl_page()
        elif name == "execute_workflow":
            result = await automation.workflow_manager.execute_workflow(
                arguments["workflow_type"],
                arguments["config"],
                automation
            )
        elif name == "click_element":
            result = await automation.click_element(arguments["selector"])
        elif name == "fill_form":
            result = await automation.fill_form(arguments["data"])
        elif name == "close_browser":
            result = await automation.close_browser()
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)})
            )
        ]


async def main():
    """MCP 서버 실행"""
    async with server:
        logger.info("✓ Google DevTools MCP Server started")
        await server.wait_for_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
