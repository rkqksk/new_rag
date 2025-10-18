#!/usr/bin/env python3
"""
크로스 플랫폼 브라우저 자동화 통합 레이어

지원하는 백엔드:
- Google DevTools MCP (기본)
- Playwright (대체)

브라우저 지원:
- webkit: macOS Safari 기반 (빠름)
- chromium: 크로스 플랫폼 Chrome 기반 (안정적)
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """통합 브라우저 자동화 인터페이스"""

    def __init__(self, backend: str = "devtools", browser_type: str = "webkit"):
        """
        Args:
            backend: "devtools" (Google DevTools MCP) 또는 "playwright"
            browser_type: "webkit" 또는 "chromium"
        """
        self.backend = backend
        self.browser_type = browser_type
        self.automation = None

        logger.info(f"브라우저 자동화 초기화: {backend} + {browser_type}")

        if backend == "devtools":
            from mcp_servers.google_devtools.server import DevToolsAutomation
            self.automation = DevToolsAutomation()
        elif backend == "playwright":
            self._init_playwright()
        else:
            raise ValueError(f"지원하지 않는 백엔드: {backend}")

    def _init_playwright(self):
        """Playwright 초기화"""
        try:
            # Playwright 통합 (추후 구현)
            logger.warning("Playwright 백엔드는 아직 구현되지 않았습니다. DevTools로 fallback합니다.")
            from mcp_servers.google_devtools.server import DevToolsAutomation
            self.automation = DevToolsAutomation()
        except ImportError:
            logger.error("Playwright가 설치되지 않았습니다. pip install playwright 실행 필요")
            raise

    async def launch_browser(self, headless: bool = True, **kwargs) -> Dict[str, Any]:
        """브라우저 실행"""
        # browser_type을 kwargs에서 제공하지 않으면 self.browser_type 사용
        if 'browser_type' not in kwargs:
            kwargs['browser_type'] = self.browser_type

        return await self.automation.launch_browser(headless=headless, **kwargs)

    async def navigate(self, url: str) -> Dict[str, Any]:
        """페이지 이동"""
        return await self.automation.navigate(url)

    async def evaluate_javascript(self, js_code: str) -> Dict[str, Any]:
        """JavaScript 실행"""
        return await self.automation.evaluate_javascript(js_code)

    async def close_browser(self):
        """브라우저 종료"""
        return await self.automation.close_browser()

    async def take_screenshot(self, output_path: str) -> Dict[str, Any]:
        """스크린샷 촬영 (Playwright 전용)"""
        if hasattr(self.automation, 'take_screenshot'):
            return await self.automation.take_screenshot(output_path)
        else:
            logger.warning(f"{self.backend} 백엔드는 스크린샷을 지원하지 않습니다")
            return {"status": "error", "message": "Not supported"}


# 편의 함수
def create_automation(
    backend: Optional[str] = None,
    browser_type: Optional[str] = None
) -> BrowserAutomation:
    """
    브라우저 자동화 인스턴스 생성

    Args:
        backend: "devtools" (기본) 또는 "playwright"
        browser_type: "webkit" (기본, macOS) 또는 "chromium" (크로스 플랫폼)

    Returns:
        BrowserAutomation 인스턴스

    Examples:
        # macOS 최적화 (기본)
        automation = create_automation()

        # 크로스 플랫폼 Chromium
        automation = create_automation(browser_type="chromium")

        # Playwright 사용
        automation = create_automation(backend="playwright", browser_type="chromium")
    """
    import platform

    # 기본값 결정
    if backend is None:
        backend = "devtools"

    if browser_type is None:
        # macOS면 webkit, 그 외는 chromium
        browser_type = "webkit" if platform.system() == "Darwin" else "chromium"

    return BrowserAutomation(backend=backend, browser_type=browser_type)
