"""
Dynamic Crawler with Playwright

Handles JavaScript-heavy websites (React, Vue, Angular, SPA)
with anti-detection and lazy-loading support.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


@dataclass
class PlaywrightConfig:
    """Playwright browser configuration"""

    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    timeout: int = 30000  # 30 seconds
    wait_until: str = "networkidle"  # load, domcontentloaded, networkidle
    stealth_mode: bool = True  # Enable anti-detection
    javascript_enabled: bool = True
    images_enabled: bool = True
    proxy: Optional[Dict[str, str]] = None
    extra_http_headers: Optional[Dict[str, str]] = None
    browser_args: List[str] = field(default_factory=lambda: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
    ])


class DynamicCrawler:
    """
    Advanced dynamic web crawler using Playwright

    Features:
    - JavaScript rendering (React, Vue, Angular, etc.)
    - Lazy-loading content detection
    - Infinite scroll handling
    - Anti-bot detection (stealth mode)
    - Screenshot capture
    - Wait for specific elements
    - Custom JavaScript execution

    Example:
        >>> config = PlaywrightConfig(stealth_mode=True)
        >>> crawler = DynamicCrawler(config)
        >>> content = await crawler.crawl('https://react-app.com')
        >>> # With custom wait
        >>> content = await crawler.crawl(
        ...     'https://vue-app.com',
        ...     wait_for_selector='div.product-list'
        ... )
    """

    def __init__(self, config: Optional[PlaywrightConfig] = None):
        self.config = config or PlaywrightConfig()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def _get_browser(self) -> Browser:
        """Get or create browser instance"""
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=self.config.headless,
                args=self.config.browser_args
            )
        return self._browser

    async def _get_context(self) -> BrowserContext:
        """Get or create browser context with anti-detection"""
        if self._context is None:
            browser = await self._get_browser()

            context_options = {
                'viewport': {
                    'width': self.config.viewport_width,
                    'height': self.config.viewport_height
                },
                'java_script_enabled': self.config.javascript_enabled,
            }

            # User agent
            if self.config.user_agent:
                context_options['user_agent'] = self.config.user_agent
            else:
                # Default to realistic user agent
                context_options['user_agent'] = (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )

            # Proxy
            if self.config.proxy:
                context_options['proxy'] = self.config.proxy

            # Extra headers
            if self.config.extra_http_headers:
                context_options['extra_http_headers'] = self.config.extra_http_headers

            self._context = await browser.new_context(**context_options)

        return self._context

    async def _apply_stealth(self, page: Page):
        """Apply anti-detection scripts"""
        if not self.config.stealth_mode:
            return

        # Remove webdriver detection
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Override chrome property
            window.chrome = {
                runtime: {}
            };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    async def crawl(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_for_timeout: Optional[int] = None,
        scroll_to_bottom: bool = False,
        execute_script: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        custom_wait: Optional[Callable[[Page], Any]] = None
    ) -> Dict[str, Any]:
        """
        Crawl a dynamic website

        Args:
            url: Target URL
            wait_for_selector: CSS selector to wait for (optional)
            wait_for_timeout: Additional timeout after page load (ms)
            scroll_to_bottom: Auto-scroll to load lazy content
            execute_script: Custom JavaScript to execute
            screenshot_path: Path to save screenshot (optional)
            custom_wait: Custom async function to wait for specific condition

        Returns:
            Dict with:
                - url: Final URL (after redirects)
                - content: HTML content
                - title: Page title
                - metadata: Additional metadata
        """
        try:
            context = await self._get_context()
            page = await context.new_page()

            # Apply anti-detection
            await self._apply_stealth(page)

            logger.info(f"Crawling dynamic site: {url}")

            # Navigate to URL
            response = await page.goto(
                url,
                wait_until=self.config.wait_until,
                timeout=self.config.timeout
            )

            # Wait for specific selector
            if wait_for_selector:
                try:
                    await page.wait_for_selector(
                        wait_for_selector,
                        timeout=self.config.timeout
                    )
                    logger.debug(f"Found selector: {wait_for_selector}")
                except PlaywrightTimeout:
                    logger.warning(f"Timeout waiting for selector: {wait_for_selector}")

            # Additional timeout
            if wait_for_timeout:
                await asyncio.sleep(wait_for_timeout / 1000)

            # Scroll to bottom for lazy-loaded content
            if scroll_to_bottom:
                await self._scroll_to_bottom(page)

            # Execute custom JavaScript
            if execute_script:
                await page.evaluate(execute_script)

            # Custom wait function
            if custom_wait:
                await custom_wait(page)

            # Get page content and metadata
            content = await page.content()
            title = await page.title()
            final_url = page.url

            # Take screenshot if requested
            screenshot_data = None
            if screenshot_path:
                await page.screenshot(path=screenshot_path, full_page=True)
                screenshot_data = screenshot_path

            result = {
                'url': final_url,
                'original_url': url,
                'content': content,
                'title': title,
                'status_code': response.status if response else None,
                'screenshot': screenshot_data,
                'metadata': {
                    'viewport': {
                        'width': self.config.viewport_width,
                        'height': self.config.viewport_height
                    },
                    'user_agent': self.config.user_agent,
                    'stealth_mode': self.config.stealth_mode
                }
            }

            await page.close()

            logger.info(f"Successfully crawled: {url} (length: {len(content)} chars)")
            return result

        except PlaywrightTimeout as e:
            logger.error(f"Timeout crawling {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            raise

    async def _scroll_to_bottom(self, page: Page, scroll_delay: float = 0.5):
        """
        Scroll to bottom of page to trigger lazy loading

        Args:
            page: Playwright page
            scroll_delay: Delay between scroll steps (seconds)
        """
        logger.debug("Scrolling to bottom to load lazy content")

        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)

        # Wait for any lazy-loaded content
        await asyncio.sleep(scroll_delay)

    async def crawl_multiple(
        self,
        urls: List[str],
        concurrent_limit: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs concurrently

        Args:
            urls: List of URLs to crawl
            concurrent_limit: Maximum concurrent requests
            **kwargs: Additional arguments passed to crawl()

        Returns:
            List of crawl results
        """
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def crawl_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.crawl(url, **kwargs)
                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    return {
                        'url': url,
                        'error': str(e),
                        'content': None
                    }

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return results

    async def extract_links(self, url: str, selector: str = "a[href]") -> List[str]:
        """
        Extract links from a page

        Args:
            url: Target URL
            selector: CSS selector for links

        Returns:
            List of absolute URLs
        """
        result = await self.crawl(url)
        context = await self._get_context()
        page = await context.new_page()

        try:
            await page.set_content(result['content'])

            links = await page.evaluate(f"""
                (selector) => {{
                    const elements = document.querySelectorAll(selector);
                    return Array.from(elements).map(a => a.href);
                }}
            """, selector)

            await page.close()
            return links

        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            await page.close()
            return []

    async def wait_for_navigation(
        self,
        page: Page,
        trigger_func: Callable,
        wait_until: str = "networkidle"
    ) -> None:
        """
        Wait for navigation after triggering an action

        Args:
            page: Playwright page
            trigger_func: Async function that triggers navigation
            wait_until: Wait until this state
        """
        async with page.expect_navigation(wait_until=wait_until):
            await trigger_func()

    async def close(self):
        """Close browser and cleanup"""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        logger.info("Dynamic crawler closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Convenience function for one-off crawls
async def crawl_dynamic_site(
    url: str,
    headless: bool = True,
    stealth: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for one-off dynamic crawls

    Args:
        url: Target URL
        headless: Run browser in headless mode
        stealth: Enable anti-detection
        **kwargs: Additional arguments passed to DynamicCrawler.crawl()

    Returns:
        Crawl result dictionary

    Example:
        >>> result = await crawl_dynamic_site('https://react-app.com')
        >>> print(result['title'])
    """
    config = PlaywrightConfig(headless=headless, stealth_mode=stealth)

    async with DynamicCrawler(config) as crawler:
        return await crawler.crawl(url, **kwargs)
