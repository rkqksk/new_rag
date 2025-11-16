"""
Manual Authentication Handler

사용자가 직접 브라우저에서 로그인하도록 하는 방식.
2FA, CAPTCHA 등 자동화가 어려운 경우 사용.

장점:
- 모든 인증 방식 지원 (2FA, CAPTCHA, biometric 등)
- 법적 문제 없음 (사용자가 직접 로그인)
- 복잡한 인증 플로우도 처리 가능

단점:
- 수동 작업 필요
- 자동화 불가
"""

import asyncio
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class ManualAuthHandler:
    """
    수동 인증 처리기

    브라우저를 띄워서 사용자가 직접 로그인하도록 함.
    로그인 후 쿠키를 저장해서 재사용 가능.

    Example:
        >>> handler = ManualAuthHandler()
        >>>
        >>> # 첫 로그인 - 브라우저가 뜨고 사용자가 직접 로그인
        >>> cookies = await handler.manual_login(
        ...     url='https://portal.com/login',
        ...     success_url='https://portal.com/dashboard'
        ... )
        >>>
        >>> # 쿠키 저장
        >>> handler.save_cookies('my-portal', cookies)
        >>>
        >>> # 나중에 쿠키 로드해서 재사용
        >>> saved_cookies = handler.load_cookies('my-portal')
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Args:
            storage_dir: 쿠키 저장 디렉토리
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".rag-enterprise" / "manual-auth"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Manual auth handler initialized (storage: {self.storage_dir})")

    async def manual_login(
        self,
        url: str,
        success_url: Optional[str] = None,
        wait_message: str = "로그인을 완료한 후 아무 키나 누르세요...",
        timeout: int = 300,  # 5분
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        브라우저를 띄워서 수동 로그인

        Args:
            url: 로그인 페이지 URL
            success_url: 로그인 성공 후 이동할 URL (확인용)
            wait_message: 사용자에게 표시할 메시지
            timeout: 최대 대기 시간 (초)
            headless: headless 모드 (False = 브라우저 보임)

        Returns:
            쿠키 딕셔너리
        """
        logger.info(f"Manual login started: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless, args=["--start-maximized"])

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            page = await context.new_page()

            try:
                # 로그인 페이지로 이동
                await page.goto(url)

                logger.info(f"\n{'='*60}")
                logger.info(f"브라우저가 열렸습니다: {url}")
                logger.info(f"수동으로 로그인을 진행해주세요.")
                logger.info(f"- 아이디/비밀번호 입력")
                logger.info(f"- 2FA 코드 입력")
                logger.info(f"- CAPTCHA 풀기")
                logger.info(f"- 기타 인증 단계 완료")
                logger.info(f"{wait_message}")
                logger.info(f"{'='*60}\n")

                # 사용자가 로그인 완료할 때까지 대기
                # 방법 1: 성공 URL로 이동 감지
                if success_url:
                    try:
                        await page.wait_for_url(success_url, timeout=timeout * 1000)
                        logger.info(f"✅ 로그인 성공 감지: {success_url}")
                    except:
                        logger.warning("Success URL로 자동 감지 실패. Enter 키를 눌러 계속하세요.")
                        input()
                else:
                    # 방법 2: 사용자가 Enter 누를 때까지 대기
                    await asyncio.get_event_loop().run_in_executor(
                        None, lambda: input(wait_message)
                    )

                # 쿠키 추출
                cookies = await context.cookies()

                logger.info(f"✅ 쿠키 추출 완료: {len(cookies)}개")

                return {
                    "cookies": cookies,
                    "url": page.url,
                    "storage_state": await context.storage_state(),
                }

            finally:
                await browser.close()

    def save_cookies(self, name: str, auth_data: Dict[str, Any]):
        """
        쿠키 저장

        Args:
            name: 저장할 이름
            auth_data: manual_login()에서 반환된 데이터
        """
        cookie_path = self.storage_dir / f"{name}.pkl"

        with open(cookie_path, "wb") as f:
            pickle.dump(auth_data, f)

        logger.info(f"✅ 쿠키 저장 완료: {name}")

    def load_cookies(self, name: str) -> Optional[Dict[str, Any]]:
        """
        저장된 쿠키 로드

        Args:
            name: 쿠키 이름

        Returns:
            쿠키 데이터 또는 None
        """
        cookie_path = self.storage_dir / f"{name}.pkl"

        if not cookie_path.exists():
            logger.warning(f"쿠키 파일 없음: {name}")
            return None

        with open(cookie_path, "rb") as f:
            auth_data = pickle.load(f)

        logger.info(f"✅ 쿠키 로드 완료: {name}")
        return auth_data

    async def login_with_saved_cookies(
        self, url: str, name: str, verify_url: Optional[str] = None
    ) -> bool:
        """
        저장된 쿠키로 로그인 시도

        Args:
            url: 접속할 URL
            name: 저장된 쿠키 이름
            verify_url: 로그인 확인 URL

        Returns:
            로그인 성공 여부
        """
        auth_data = self.load_cookies(name)

        if not auth_data:
            logger.error(f"저장된 쿠키 없음: {name}")
            return False

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # storage_state로 컨텍스트 생성 (쿠키 포함)
            context = await browser.new_context(storage_state=auth_data["storage_state"])

            page = await context.new_page()

            try:
                await page.goto(url)

                # 로그인 페이지로 리다이렉트되는지 확인
                if verify_url:
                    current_url = page.url
                    if "login" in current_url.lower():
                        logger.warning(f"❌ 로그인 페이지로 리다이렉트됨. 쿠키 만료 가능성 있음.")
                        return False

                    logger.info(f"✅ 쿠키로 로그인 성공: {current_url}")
                    return True
                else:
                    logger.info(f"✅ 쿠키 적용 완료")
                    return True

            except Exception as e:
                logger.error(f"쿠키 로그인 실패: {e}")
                return False

            finally:
                await browser.close()

    def delete_cookies(self, name: str):
        """쿠키 삭제"""
        cookie_path = self.storage_dir / f"{name}.pkl"

        if cookie_path.exists():
            cookie_path.unlink()
            logger.info(f"✅ 쿠키 삭제 완료: {name}")
        else:
            logger.warning(f"쿠키 파일 없음: {name}")

    def list_saved_cookies(self) -> list:
        """저장된 쿠키 목록"""
        cookies = []

        for cookie_file in self.storage_dir.glob("*.pkl"):
            cookies.append(cookie_file.stem)

        return cookies


# Convenience functions


async def manual_login_once(
    url: str, session_name: str, success_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    수동 로그인 후 쿠키 저장 (편의 함수)

    Example:
        >>> # 첫 로그인
        >>> await manual_login_once(
        ...     url='https://portal.com/login',
        ...     session_name='my-portal',
        ...     success_url='https://portal.com/dashboard'
        ... )
        >>>
        >>> # 이후 재사용
        >>> handler = ManualAuthHandler()
        >>> cookies = handler.load_cookies('my-portal')
    """
    handler = ManualAuthHandler()

    auth_data = await handler.manual_login(url=url, success_url=success_url)

    handler.save_cookies(session_name, auth_data)

    return auth_data


async def auto_or_manual_login(
    url: str, session_name: str, verify_url: Optional[str] = None, force_manual: bool = False
) -> Dict[str, Any]:
    """
    자동 또는 수동 로그인

    저장된 쿠키가 있으면 자동, 없으면 수동 로그인

    Example:
        >>> # 첫 실행: 수동 로그인
        >>> # 이후 실행: 자동 (저장된 쿠키 사용)
        >>> auth = await auto_or_manual_login(
        ...     url='https://portal.com/login',
        ...     session_name='my-portal',
        ...     verify_url='https://portal.com/dashboard'
        ... )
    """
    handler = ManualAuthHandler()

    # 강제 수동 로그인
    if force_manual:
        logger.info("🔄 강제 수동 로그인 모드")
        auth_data = await handler.manual_login(url=url)
        handler.save_cookies(session_name, auth_data)
        return auth_data

    # 저장된 쿠키 확인
    saved_cookies = handler.load_cookies(session_name)

    if saved_cookies:
        logger.info("🔄 저장된 쿠키로 로그인 시도...")

        # 쿠키 유효성 확인
        if verify_url:
            valid = await handler.login_with_saved_cookies(url=verify_url, name=session_name)

            if valid:
                logger.info("✅ 저장된 쿠키 사용")
                return saved_cookies
            else:
                logger.warning("⚠️ 쿠키 만료. 수동 로그인 필요")
        else:
            logger.info("✅ 저장된 쿠키 사용 (검증 스킵)")
            return saved_cookies

    # 수동 로그인 필요
    logger.info("🔄 수동 로그인 시작...")
    auth_data = await handler.manual_login(url=url)
    handler.save_cookies(session_name, auth_data)

    return auth_data
