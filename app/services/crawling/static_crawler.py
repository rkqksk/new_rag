"""
Static Crawler with requests + BeautifulSoup

Fast crawling for static HTML websites (no JavaScript).
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import random

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class StaticCrawlerConfig:
    """Static crawler configuration"""

    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    user_agent: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None


class StaticCrawler:
    """
    Fast static web crawler using httpx + BeautifulSoup

    Best for:
    - Static HTML websites
    - News articles, blogs
    - Product catalogs (static)
    - Simple content pages

    Not suitable for:
    - JavaScript-heavy sites (use DynamicCrawler)
    - SPAs (React, Vue, Angular)
    - Lazy-loaded content

    Example:
        >>> config = StaticCrawlerConfig(timeout=10)
        >>> crawler = StaticCrawler(config)
        >>> result = await crawler.crawl('https://example.com')
        >>> soup = BeautifulSoup(result['content'], 'html.parser')
    """

    DEFAULT_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]

    def __init__(self, config: Optional[StaticCrawlerConfig] = None):
        self.config = config or StaticCrawlerConfig()

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {}

        # User agent
        if self.config.user_agent:
            headers['User-Agent'] = self.config.user_agent
        else:
            # Random user agent for anti-detection
            headers['User-Agent'] = random.choice(self.DEFAULT_USER_AGENTS)

        # Common headers to appear more human
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Extra headers
        if self.config.extra_headers:
            headers.update(self.config.extra_headers)

        return headers

    async def crawl(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        parse_html: bool = True
    ) -> Dict[str, Any]:
        """
        Crawl a static website

        Args:
            url: Target URL
            method: HTTP method (GET, POST)
            data: POST data (if method=POST)
            parse_html: Parse HTML with BeautifulSoup

        Returns:
            Dict with:
                - url: Final URL (after redirects)
                - content: Raw HTML or parsed BeautifulSoup
                - status_code: HTTP status code
                - headers: Response headers
                - text: Response text
        """
        headers = self._get_headers()

        client_kwargs = {
            'timeout': self.config.timeout,
            'follow_redirects': self.config.follow_redirects,
            'verify': self.config.verify_ssl,
        }

        if self.config.proxy:
            client_kwargs['proxies'] = self.config.proxy

        async with httpx.AsyncClient(**client_kwargs) as client:
            for attempt in range(self.config.max_retries):
                try:
                    logger.info(f"Crawling static site: {url} (attempt {attempt + 1}/{self.config.max_retries})")

                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=headers, data=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    response.raise_for_status()

                    # Parse HTML if requested
                    content = response.text
                    if parse_html:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup

                    result = {
                        'url': str(response.url),
                        'original_url': url,
                        'content': content,
                        'text': response.text,
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'encoding': response.encoding,
                        'metadata': {
                            'method': method,
                            'attempts': attempt + 1,
                        }
                    }

                    logger.info(f"Successfully crawled: {url} (status: {response.status_code}, length: {len(response.text)} chars)")
                    return result

                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

                except httpx.TimeoutException as e:
                    logger.error(f"Timeout crawling {url}: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise Exception(f"Failed to crawl {url} after {self.config.max_retries} attempts")

    async def crawl_multiple(
        self,
        urls: List[str],
        concurrent_limit: int = 5,
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
        import asyncio

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

    async def extract_links(
        self,
        url: str,
        selector: str = "a[href]",
        absolute: bool = True
    ) -> List[str]:
        """
        Extract links from a page

        Args:
            url: Target URL
            selector: CSS selector for links
            absolute: Convert to absolute URLs

        Returns:
            List of URLs
        """
        result = await self.crawl(url, parse_html=True)
        soup = result['content']

        links = []
        for link in soup.select(selector):
            href = link.get('href')
            if href:
                if absolute:
                    href = urljoin(url, href)
                links.append(href)

        return links

    async def extract_text(self, url: str, selector: Optional[str] = None) -> str:
        """
        Extract text content from a page

        Args:
            url: Target URL
            selector: CSS selector to extract (optional, default: whole page)

        Returns:
            Extracted text
        """
        result = await self.crawl(url, parse_html=True)
        soup = result['content']

        if selector:
            elements = soup.select(selector)
            return '\n\n'.join(elem.get_text(strip=True) for elem in elements)
        else:
            return soup.get_text(strip=True)

    async def download_file(self, url: str, output_path: str) -> Dict[str, Any]:
        """
        Download a file from URL

        Args:
            url: File URL
            output_path: Local path to save file

        Returns:
            Download metadata
        """
        headers = self._get_headers()

        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            follow_redirects=self.config.follow_redirects
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response.content)

            return {
                'url': url,
                'output_path': output_path,
                'size': len(response.content),
                'content_type': response.headers.get('content-type'),
                'status_code': response.status_code
            }


# Convenience function for one-off crawls
async def crawl_static_site(url: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function for one-off static crawls

    Args:
        url: Target URL
        **kwargs: Additional arguments passed to StaticCrawler.crawl()

    Returns:
        Crawl result dictionary

    Example:
        >>> result = await crawl_static_site('https://example.com')
        >>> soup = result['content']
        >>> title = soup.find('title').text
    """
    crawler = StaticCrawler()
    return await crawler.crawl(url, **kwargs)


# Add missing import
import asyncio
