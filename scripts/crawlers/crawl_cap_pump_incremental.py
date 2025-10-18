#!/usr/bin/env python3
"""
Cap&Pump 카테고리 증분 업데이트 크롤러
기존 제품 SKIP, 새 제품만 크롤링

페이지네이션: 그룹형 (1-14 페이지, 3개 그룹)
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
        logging.FileHandler('crawl_cap_pump_incremental.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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
    """Cap&Pump 증분 크롤링"""

    logger.info(f"\n{'='*80}")
    logger.info("Cap&Pump 카테고리 증분 크롤링 시작")
    logger.info(f"{'='*80}")

    # 크롤러 초기화
    crawler = ChungjinCrawler(output_dir="data/crawled_products")

    # 1단계: 기존 제품 ID 로드
    logger.info("\n[Step 1] 기존 제품 확인 중...")
    existing_ids = await load_existing_product_ids(crawler.output_dir)
    logger.info(f"  → {len(existing_ids)}개 제품 이미 존재")

    # 2단계: 모든 페이지 URL 수집 (그룹 페이지네이션)
    logger.info("\n[Step 2] 제품 URL 수집 중...")
    category_url = "http://chungjinkorea.com/kr/product/list.php?part_idx=3"
    max_pages = 14

    all_urls = []
    for page in range(1, max_pages + 1):
        logger.info(f"  페이지 {page}/{max_pages} 수집 중...")
        page_urls = await crawler.get_product_urls_from_page(category_url, page)
        all_urls.extend(page_urls)
        await asyncio.sleep(2)

    # 중복 제거
    unique_urls = list(set(all_urls))
    logger.info(f"  → {len(unique_urls)}개 제품 URL 발견")

    # 3단계: 새 제품 필터링
    logger.info("\n[Step 3] 새 제품 필터링 중...")
    new_urls = []

    for url in unique_urls:
        idx = url.split('idx=')[1] if 'idx=' in url else None
        if idx and idx not in existing_ids:
            new_urls.append(url)

    logger.info(f"  → {len(new_urls)}개 새 제품 발견")
    logger.info(f"  → {len(unique_urls) - len(new_urls)}개 제품은 이미 존재 (SKIP)")

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

        if i < len(new_urls):
            await asyncio.sleep(2)

    # 5단계: 요약 저장
    summary = {
        'category': 'Cap&Pump',
        'category_url': category_url,
        'total_pages': max_pages,
        'total_urls_found': len(unique_urls),
        'existing_products': len(existing_ids),
        'new_products': len(new_urls),
        'success': success_count,
        'error': error_count,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }

    summary_path = crawler.output_dir / f"category_Cap_Pump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*80}")
    logger.info("✅ Cap&Pump 크롤링 완료!")
    logger.info(f"{'='*80}")
    logger.info(f"발견: {len(unique_urls)}개 제품")
    logger.info(f"기존: {len(existing_ids)}개 (SKIP)")
    logger.info(f"새 제품: {len(new_urls)}개")
    logger.info(f"성공: {success_count}개")
    logger.info(f"실패: {error_count}개")
    logger.info(f"요약: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
