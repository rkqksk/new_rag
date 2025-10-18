#!/usr/bin/env python3
"""
Bottle 카테고리 적응형 크롤러
동적 페이지 탐색으로 실제 존재하는 페이지만 크롤링

전략:
1. 현재 보이는 페이지 버튼 탐색
2. 각 페이지에서 제품 URL 수집
3. paging-next 버튼으로 다음 그룹 이동
4. 더 이상 그룹이 없을 때까지 반복
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from chungjin_crawler import ChungjinCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawl_bottle_adaptive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def get_all_bottle_urls_adaptive(crawler: ChungjinCrawler, category_url: str) -> list:
    """
    동적으로 모든 Bottle 페이지 탐색 및 URL 수집

    Returns:
        list: 모든 제품 URL 목록
    """
    all_urls = []
    visited_pages = set()

    try:
        await crawler.automation.launch_browser(headless=True, browser_type="webkit")
        await crawler.automation.navigate(category_url)
        await asyncio.sleep(3)

        group_number = 1
        max_groups = 20  # 안전장치: 최대 20개 그룹

        while group_number <= max_groups:
            logger.info(f"\n{'='*80}")
            logger.info(f"그룹 {group_number} 탐색 중...")
            logger.info(f"{'='*80}")

            # 현재 보이는 페이지 번호 확인
            check_pages_js = """
            () => {
                const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
                const pageNumbers = pageLinks
                    .map(a => a.textContent.trim())
                    .filter(text => /^\d{1,3}$/.test(text))
                    .map(Number);

                const nextButton = document.querySelector('.paging-next');
                const hasNext = nextButton && !nextButton.classList.contains('disabled');

                return {
                    visible_pages: pageNumbers,
                    has_next: hasNext
                };
            }
            """

            result = await crawler.automation.evaluate_javascript(check_pages_js)

            if result.get('status') != 'success':
                logger.error("페이지 정보 추출 실패")
                break

            data = result.get('result', {})
            visible_pages = data.get('visible_pages', [])
            has_next = data.get('has_next', False)

            if not visible_pages:
                logger.warning("더 이상 페이지가 없습니다")
                break

            logger.info(f"발견된 페이지: {visible_pages}")

            # 각 페이지에서 제품 URL 수집
            for page in visible_pages:
                if page in visited_pages:
                    logger.debug(f"페이지 {page} 이미 방문함 - SKIP")
                    continue

                logger.info(f"\n[페이지 {page}] URL 수집 중...")

                # 페이지 클릭
                click_js = f"""
                () => {{
                    const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
                    const targetLink = pageLinks.find(a => a.textContent.trim() === '{page}');

                    if (targetLink) {{
                        targetLink.click();
                        return {{ clicked: true }};
                    }}
                    return {{ clicked: false }};
                }}
                """

                click_result = await crawler.automation.evaluate_javascript(click_js)

                if click_result.get('status') == 'success' and click_result.get('result', {}).get('clicked'):
                    await asyncio.sleep(5)  # AJAX 로딩 대기

                    # 제품 URL 추출
                    extract_js = """
                    () => {
                        const productLinks = Array.from(document.querySelectorAll('a[href*="view.php"]'));
                        const uniqueUrls = new Set();

                        productLinks.forEach(a => {
                            if (a.href.includes('idx=')) {
                                uniqueUrls.add(a.href);
                            }
                        });

                        return Array.from(uniqueUrls);
                    }
                    """

                    extract_result = await crawler.automation.evaluate_javascript(extract_js)

                    if extract_result.get('status') == 'success':
                        page_urls = extract_result.get('result', [])
                        logger.info(f"  → {len(page_urls)}개 제품 URL 발견")
                        all_urls.extend(page_urls)
                        visited_pages.add(page)
                    else:
                        logger.warning(f"페이지 {page} URL 추출 실패")
                else:
                    logger.warning(f"페이지 {page} 클릭 실패")

            # 다음 그룹으로 이동
            if has_next:
                logger.info(f"\n→ 다음 그룹으로 이동 (paging-next 클릭)")

                next_js = """
                () => {
                    const nextButton = document.querySelector('.paging-next');
                    if (nextButton && !nextButton.classList.contains('disabled')) {
                        nextButton.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
                """

                next_result = await crawler.automation.evaluate_javascript(next_js)

                if next_result.get('status') == 'success' and next_result.get('result', {}).get('clicked'):
                    await asyncio.sleep(5)  # AJAX 로딩 대기
                    group_number += 1
                else:
                    logger.warning("paging-next 버튼 클릭 실패 - 종료")
                    break
            else:
                logger.info("\n✓ 마지막 그룹입니다 - 탐색 완료")
                break

        await crawler.automation.close_browser()

        # 중복 제거
        unique_urls = list(set(all_urls))

        logger.info(f"\n{'='*80}")
        logger.info(f"URL 수집 완료!")
        logger.info(f"{'='*80}")
        logger.info(f"방문한 페이지: {sorted(visited_pages)}")
        logger.info(f"수집: {len(all_urls)}개 URL")
        logger.info(f"중복 제거 후: {len(unique_urls)}개 URL")

        return unique_urls

    except Exception as e:
        logger.error(f"URL 수집 에러: {e}")
        await crawler.automation.close_browser()
        return []


async def load_existing_product_ids(output_dir: Path) -> set:
    """기존 크롤링 데이터에서 제품 ID 목록 추출"""
    existing_ids = set()

    json_files = list(output_dir.glob('idx_*.json'))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                idx = data.get('idx')
                if idx:
                    existing_ids.add(idx)
        except Exception as e:
            logger.warning(f"파일 읽기 실패 {json_file.name}: {e}")

    return existing_ids


async def main():
    """적응형 Bottle 크롤링 메인"""

    logger.info(f"\n{'='*80}")
    logger.info("Bottle 카테고리 적응형 크롤링 시작")
    logger.info(f"{'='*80}")

    # 크롤러 초기화
    crawler = ChungjinCrawler(output_dir="data/crawled_products")

    # 1단계: 기존 제품 ID 로드
    logger.info("\n[Step 1] 기존 제품 확인 중...")
    existing_ids = await load_existing_product_ids(crawler.output_dir)
    logger.info(f"  → {len(existing_ids)}개 제품 이미 존재")

    # 2단계: 동적 URL 수집
    logger.info("\n[Step 2] 제품 URL 동적 수집 중...")
    category_url = "http://chungjinkorea.com/kr/product/list.php?part_idx=1"
    all_urls = await get_all_bottle_urls_adaptive(crawler, category_url)

    if not all_urls:
        logger.error("제품 URL을 찾을 수 없습니다")
        return

    # 3단계: 새 제품 필터링
    logger.info("\n[Step 3] 새 제품 필터링 중...")
    new_urls = []

    for url in all_urls:
        idx = url.split('idx=')[1] if 'idx=' in url else None
        if idx and idx not in existing_ids:
            new_urls.append(url)

    logger.info(f"  → {len(new_urls)}개 새 제품 발견")
    logger.info(f"  → {len(all_urls) - len(new_urls)}개 제품은 이미 존재 (SKIP)")

    if not new_urls:
        logger.info("\n✓ 모든 제품이 이미 수집되어 있습니다!")
        return

    # 4단계: 새 제품만 크롤링
    logger.info(f"\n[Step 4] {len(new_urls)}개 새 제품 크롤링 시작...")

    results = []
    success_count = 0
    error_count = 0

    for i, url in enumerate(new_urls, 1):
        logger.info(f"\n[{i}/{len(new_urls)}] 크롤링 중...")

        result = await crawler.crawl_product(url)

        if result['status'] == 'success':
            success_count += 1
        else:
            error_count += 1

        results.append(result)

        # 서버 부하 방지
        if i < len(new_urls):
            await asyncio.sleep(2)

    # 5단계: 요약 저장
    summary = {
        'category': 'Bottle',
        'category_url': category_url,
        'total_urls_found': len(all_urls),
        'existing_products': len(existing_ids),
        'new_products': len(new_urls),
        'success': success_count,
        'error': error_count,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }

    summary_path = crawler.output_dir / f"category_Bottle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*80}")
    logger.info("✅ Bottle 크롤링 완료!")
    logger.info(f"{'='*80}")
    logger.info(f"발견: {len(all_urls)}개 제품")
    logger.info(f"기존: {len(existing_ids)}개 (SKIP)")
    logger.info(f"새 제품: {len(new_urls)}개")
    logger.info(f"성공: {success_count}개")
    logger.info(f"실패: {error_count}개")
    logger.info(f"요약: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
