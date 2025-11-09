"""
robots.txt Handler

robots.txt 확인 및 우회 옵션

Options:
1. RESPECT: robots.txt 준수 (기본)
2. IGNORE: robots.txt 무시 (자기 책임)
3. BYPASS: User-Agent 변경으로 우회
"""

import logging
from enum import Enum
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)


class RobotsPolicy(Enum):
    """robots.txt 정책"""

    RESPECT = "respect"  # 준수
    IGNORE = "ignore"  # 무시
    BYPASS = "bypass"  # 우회 (User-Agent 변경)


class RobotsHandler:
    """
    robots.txt 처리

    Example:
        >>> # 준수 모드 (기본)
        >>> handler = RobotsHandler(policy=RobotsPolicy.RESPECT)
        >>> can_fetch = await handler.can_fetch('https://example.com/api/data')
        >>> if not can_fetch:
        >>>     print("robots.txt에서 차단됨")
        >>>
        >>> # 무시 모드
        >>> handler = RobotsHandler(policy=RobotsPolicy.IGNORE)
        >>> can_fetch = await handler.can_fetch('https://example.com/api/data')
        >>> # 항상 True 반환
    """

    def __init__(self, policy: RobotsPolicy = RobotsPolicy.RESPECT, user_agent: str = "*"):
        """
        Args:
            policy: robots.txt 정책
            user_agent: User-Agent 문자열
        """
        self.policy = policy
        self.user_agent = user_agent

        # robots.txt 캐시
        self._cache: dict = {}

        logger.info(f"Robots handler initialized (policy: {policy.value})")

    async def can_fetch(self, url: str, user_agent: Optional[str] = None) -> bool:
        """
        URL을 크롤링해도 되는지 확인

        Args:
            url: 확인할 URL
            user_agent: User-Agent (None이면 기본값 사용)

        Returns:
            크롤링 가능 여부
        """
        # IGNORE 모드: 항상 허용
        if self.policy == RobotsPolicy.IGNORE:
            logger.debug(f"✅ robots.txt 무시 모드: {url}")
            return True

        # BYPASS 모드: Googlebot으로 위장
        if self.policy == RobotsPolicy.BYPASS:
            user_agent = "Googlebot"
            logger.debug(f"🔄 robots.txt 우회 모드 (Googlebot): {url}")

        # RESPECT 모드: robots.txt 확인
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 캐시 확인
        if base_url not in self._cache:
            await self._fetch_robots(base_url)

        parser = self._cache.get(base_url)

        if parser is None:
            # robots.txt 없음 = 허용
            logger.debug(f"✅ robots.txt 없음: {url}")
            return True

        # robots.txt 확인
        ua = user_agent or self.user_agent
        allowed = parser.can_fetch(ua, url)

        if allowed:
            logger.debug(f"✅ robots.txt 허용: {url}")
        else:
            logger.warning(f"❌ robots.txt 차단: {url}")

        return allowed

    async def _fetch_robots(self, base_url: str):
        """
        robots.txt 다운로드 및 파싱

        Args:
            base_url: 베이스 URL (https://example.com)
        """
        robots_url = f"{base_url}/robots.txt"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(robots_url)

                if response.status_code == 200:
                    parser = RobotFileParser()
                    parser.parse(response.text.splitlines())
                    self._cache[base_url] = parser

                    logger.debug(f"📄 robots.txt 로드 완료: {base_url}")
                else:
                    # robots.txt 없음
                    self._cache[base_url] = None
                    logger.debug(f"📄 robots.txt 없음 ({response.status_code}): {base_url}")

        except Exception as e:
            logger.warning(f"robots.txt 로드 실패: {base_url} - {e}")
            self._cache[base_url] = None

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Crawl-delay 값 가져오기

        Args:
            url: URL

        Returns:
            Crawl-delay (초) 또는 None
        """
        if self.policy == RobotsPolicy.IGNORE:
            return None

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        parser = self._cache.get(base_url)

        if parser:
            delay = parser.crawl_delay(self.user_agent)
            if delay:
                logger.debug(f"⏱️ Crawl-delay: {delay}초")
                return delay

        return None

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.debug("🗑️ robots.txt 캐시 초기화")


# Convenience functions


async def check_robots(url: str, respect: bool = True) -> bool:
    """
    robots.txt 확인 (간편 함수)

    Args:
        url: 확인할 URL
        respect: True = 준수, False = 무시

    Returns:
        크롤링 가능 여부

    Example:
        >>> # 준수
        >>> allowed = await check_robots('https://example.com/api')
        >>>
        >>> # 무시
        >>> allowed = await check_robots('https://example.com/api', respect=False)
        >>> # 항상 True
    """
    policy = RobotsPolicy.RESPECT if respect else RobotsPolicy.IGNORE
    handler = RobotsHandler(policy=policy)

    return await handler.can_fetch(url)


async def bypass_robots(url: str) -> bool:
    """
    robots.txt 우회 (Googlebot으로 위장)

    Args:
        url: 확인할 URL

    Returns:
        크롤링 가능 여부

    Example:
        >>> allowed = await bypass_robots('https://example.com/api')
    """
    handler = RobotsHandler(policy=RobotsPolicy.BYPASS)
    return await handler.can_fetch(url)


# Integration with crawlers


def add_robots_check_to_crawler(crawler, policy: RobotsPolicy = RobotsPolicy.RESPECT):
    """
    크롤러에 robots.txt 체크 추가

    Args:
        crawler: 크롤러 인스턴스
        policy: robots.txt 정책
    """
    handler = RobotsHandler(policy=policy)

    # 원래 crawl 함수 저장
    original_crawl = crawler.crawl

    async def crawl_with_robots_check(url: str, *args, **kwargs):
        """robots.txt 체크 후 크롤링"""

        # robots.txt 확인
        can_fetch = await handler.can_fetch(url)

        if not can_fetch and policy == RobotsPolicy.RESPECT:
            raise Exception(f"robots.txt에서 차단됨: {url}")

        # 크롤링 실행
        return await original_crawl(url, *args, **kwargs)

    # crawl 함수 교체
    crawler.crawl = crawl_with_robots_check

    logger.info(f"✅ robots.txt 체크 추가 (policy: {policy.value})")
