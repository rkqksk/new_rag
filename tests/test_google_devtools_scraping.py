#!/usr/bin/env python3
"""
Google DevTools MCP 웹 스크래핑 테스트
Playwright 기반 브라우저 자동화
"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def test_simple_scraping():
    """간단한 웹 스크래핑 테스트"""
    print("=" * 60)
    print("Google DevTools MCP - 웹 스크래핑 테스트")
    print("=" * 60)

    automation = DevToolsAutomation()

    try:
        # 1. 브라우저 시작 (macOS에서는 WebKit이 더 안정적)
        print("\n[1/5] 브라우저 시작 중 (WebKit/Safari 엔진)...")
        launch_result = await automation.launch_browser(headless=False, browser_type="webkit")
        print(f"✓ {launch_result.get('message')}")

        # 2. 청진코리아 제품 페이지 스크래핑
        print("\n[2/5] 청진코리아 제품 페이지 방문 중...")
        test_url = "http://chungjinkorea.com/kr/product/view.php?idx=777"

        nav_result = await automation.navigate(test_url)
        print(f"✓ 페이지 로드 완료")
        print(f"  - URL: {nav_result.get('url')}")
        print(f"  - 제목: {nav_result.get('title')}")
        print(f"  - 로드 시간: {nav_result.get('load_time', 0):.2f}초")

        # 3. 페이지 크롤링
        print("\n[3/5] 페이지 데이터 수집 중...")
        crawl_result = await automation.crawl_page()

        if crawl_result.get('status') == 'success':
            data = crawl_result.get('data', {})
            print(f"✓ 데이터 수집 완료")
            print(f"  - 제목: {data.get('title')}")
            print(f"  - URL: {data.get('url')}")
            print(f"  - 헤딩 수: {len(data.get('headings', []))}")
            print(f"  - 링크 수: {len(data.get('links', []))}")
            print(f"  - 이미지 수: {data.get('images', 0)}")
            print(f"  - 폼 수: {data.get('forms', 0)}")

            # 텍스트 미리보기
            text_content = data.get('text', '')[:200]
            print(f"\n  📄 텍스트 미리보기:")
            print(f"  {text_content}...")

        # 4. 성능 메트릭 수집
        print("\n[4/5] 성능 메트릭 수집 중...")
        metrics_result = await automation.get_performance_metrics()

        if metrics_result.get('status') == 'success':
            metrics = metrics_result.get('metrics', {})
            print(f"✓ 성능 메트릭 수집 완료")
            print(f"  - 페이지 로드 시간: {metrics.get('loadTime', 0)}ms")
            print(f"  - DOM 로드 시간: {metrics.get('domContentLoaded', 0)}ms")
            print(f"  - First Paint: {metrics.get('firstPaint', 0):.0f}ms")

            if metrics.get('memory'):
                memory = metrics['memory']
                print(f"  - 메모리 사용량: {memory.get('heapUsagePercent')}%")

        # 5. 스크린샷 저장
        print("\n[5/5] 스크린샷 캡처 중...")
        screenshot_result = await automation.take_screenshot("chungjinkorea_product.png")

        if screenshot_result.get('status') == 'success':
            print(f"✓ 스크린샷 저장됨: {screenshot_result.get('path')}")

        # 종료
        print("\n[완료] 브라우저 종료 중...")
        close_result = await automation.close_browser()
        print(f"✓ {close_result.get('message')}")

        print("\n" + "=" * 60)
        print("✅ 웹 스크래핑 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 브라우저가 열려있으면 종료
        try:
            await automation.close_browser()
        except Exception as e:
            logger.debug(f"Error closing browser: {e}")


async def test_advanced_scraping():
    """고급 스크래핑 - 여러 페이지"""
    print("\n" + "=" * 60)
    print("고급 테스트: 여러 페이지 스크래핑")
    print("=" * 60)

    automation = DevToolsAutomation()

    urls = [
        "https://example.com",
        "https://www.python.org",
        "https://github.com"
    ]

    try:
        print("\n브라우저 시작 중...")
        await automation.launch_browser(headless=True)

        results = []

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url} 스크래핑 중...")

            try:
                # 페이지 방문
                nav_result = await automation.navigate(url, timeout=15000)

                # 데이터 수집
                crawl_result = await automation.crawl_page()
                metrics_result = await automation.get_performance_metrics()

                result = {
                    "url": url,
                    "title": nav_result.get('title'),
                    "load_time": nav_result.get('load_time', 0),
                    "links_count": len(crawl_result.get('data', {}).get('links', [])),
                    "images_count": crawl_result.get('data', {}).get('images', 0),
                    "load_time_ms": metrics_result.get('metrics', {}).get('loadTime', 0)
                }

                results.append(result)

                print(f"  ✓ 제목: {result['title']}")
                print(f"  ✓ 링크: {result['links_count']}개")
                print(f"  ✓ 이미지: {result['images_count']}개")
                print(f"  ✓ 로드: {result['load_time']:.2f}초")

            except Exception as e:
                print(f"  ✗ 실패: {e}")
                results.append({"url": url, "error": str(e)})

        # 결과 요약
        print("\n" + "=" * 60)
        print("스크래핑 요약")
        print("=" * 60)
        print(f"총 시도: {len(urls)}개")
        print(f"성공: {sum(1 for r in results if 'error' not in r)}개")
        print(f"실패: {sum(1 for r in results if 'error' in r)}개")

        print("\n✅ 고급 스크래핑 테스트 완료!")

        # 브라우저 종료
        await automation.close_browser()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 실행"""
    print("🚀 Google DevTools MCP 웹 스크래핑 테스트 시작\n")

    # 테스트 1: 기본 스크래핑
    await test_simple_scraping()

    # 테스트 2: 고급 스크래핑 (여러 페이지)
    # await test_advanced_scraping()

    print("\n🎉 모든 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
