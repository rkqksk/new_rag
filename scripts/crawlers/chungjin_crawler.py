#!/usr/bin/env python3
"""
청진코리아 전용 프로덕션 크롤러 v2.0
Phase 1/2 분석 결과를 완벽하게 반영한 최종 크롤러

주요 기능:
- img 태그 + CSS background-image 모두 추출
- Definition Lists (dl/dt/dd) 스펙 정보 추출
- 인쇄영역 PDF 다운로드
- 제품명 100% 추출 (img alt)
- 파일명 기준 이미지 정렬
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from browser_automation import BrowserAutomation, create_automation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChungjinCrawler:
    """청진코리아 전용 프로덕션 크롤러

    브라우저 지원:
    - webkit: macOS 최적화 (기본값)
    - chromium: 크로스 플랫폼 호환성
    """

    def __init__(
        self,
        output_dir: str = "data/crawled_products",
        browser_type: str = "webkit",
        use_playwright: bool = False
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 서브 디렉토리
        self.images_dir = self.output_dir / "images"
        self.print_area_dir = self.output_dir / "print_area"

        self.images_dir.mkdir(exist_ok=True)
        self.print_area_dir.mkdir(exist_ok=True)

        # 브라우저 설정
        self.browser_type = browser_type
        self.use_playwright = use_playwright

        # 브라우저 자동화 도구 초기화
        backend = "playwright" if use_playwright else "devtools"
        self.automation = create_automation(backend=backend, browser_type=browser_type)

    async def crawl_product(self, url: str) -> Dict[str, Any]:
        """
        제품 페이지 완벽 크롤링
        Phase 1/2 발견사항 100% 적용
        """
        idx = url.split('idx=')[1] if 'idx=' in url else 'unknown'

        logger.info(f"\n{'='*80}")
        logger.info(f"제품 크롤링: idx={idx}")
        logger.info(f"URL: {url}")
        logger.info(f"{'='*80}")

        try:
            await self.automation.launch_browser(headless=True, browser_type=self.browser_type)
            await self.automation.navigate(url)
            await asyncio.sleep(3)  # CSS background 렌더링 대기

            # 데이터 추출
            js_code = """
            () => {
                const result = {};

                // ========================================
                // 1. 제품명 (img alt에서 100% 추출)
                // ========================================
                const mainImg = document.querySelector('img[src*="goodsImages"]');
                result.product_name = mainImg?.alt || 'Unknown Product';

                // ========================================
                // 2. 모든 이미지 추출 (img + CSS background)
                // ========================================
                const allProductImages = [];

                // 2-1. img 태그
                const imgTags = Array.from(document.querySelectorAll('img'));
                const productImgTags = imgTags.filter(img =>
                    img.src.includes('goodsImages') || img.src.includes('GOODS')
                );

                productImgTags.forEach(img => {
                    const filename = img.src.split('/').pop();
                    let imageType = 'unknown';

                    if (filename.includes('GOODS1_')) imageType = 'main';
                    else if (filename.includes('ADD_GOODS1_')) imageType = 'additional_1';
                    else if (filename.includes('ADD_GOODS2_')) imageType = 'additional_2';
                    else if (filename.includes('ADD_GOODS3_')) imageType = 'additional_3';
                    else if (filename.includes('GOODS2_')) imageType = 'sub';

                    allProductImages.push({
                        source: 'img_tag',
                        url: img.src,
                        filename: filename,
                        alt: img.alt || '',
                        type: imageType,
                        width: img.naturalWidth,
                        height: img.naturalHeight
                    });
                });

                // 2-2. CSS background-image
                const allElements = Array.from(document.querySelectorAll('*'));
                allElements.forEach(elem => {
                    const style = window.getComputedStyle(elem);
                    const bgImage = style.backgroundImage;

                    if (bgImage && bgImage !== 'none' && bgImage.includes('url(')) {
                        const urlMatch = bgImage.match(/url\\(["']?([^"')]+)["']?\\)/);
                        if (urlMatch && urlMatch[1]) {
                            const url = urlMatch[1];

                            if (url.includes('goodsImages') || url.includes('GOODS')) {
                                const filename = url.split('/').pop();
                                let imageType = 'unknown';

                                if (filename.includes('GOODS1_')) imageType = 'main';
                                else if (filename.includes('ADD_GOODS1_')) imageType = 'additional_1';
                                else if (filename.includes('ADD_GOODS2_')) imageType = 'additional_2';
                                else if (filename.includes('ADD_GOODS3_')) imageType = 'additional_3';
                                else if (filename.includes('GOODS2_')) imageType = 'sub';

                                allProductImages.push({
                                    source: 'css_background',
                                    url: url,
                                    filename: filename,
                                    type: imageType
                                });
                            }
                        }
                    }
                });

                // 2-3. 중복 제거 (URL 기준)
                const uniqueImages = [];
                const seenUrls = new Set();

                allProductImages.forEach(img => {
                    if (!seenUrls.has(img.url)) {
                        seenUrls.add(img.url);
                        uniqueImages.push(img);
                    }
                });

                // 2-4. 정렬 (GOODS1 → ADD_GOODS1 → ADD_GOODS2 → ADD_GOODS3)
                const typeOrder = {
                    'main': 0,
                    'additional_1': 1,
                    'additional_2': 2,
                    'additional_3': 3,
                    'sub': 4,
                    'unknown': 99
                };

                uniqueImages.sort((a, b) => {
                    return (typeOrder[a.type] || 99) - (typeOrder[b.type] || 99);
                });

                result.images = uniqueImages;

                // ========================================
                // 3. 스펙 정보 (Definition Lists)
                // ========================================
                result.specifications = {};

                // 방법 1: DL 요소 기반 추출
                let specContainer = document.querySelector('div.product-view-bottom-item');
                if (!specContainer) {
                    specContainer = document.querySelector('div.product-view-bottom');
                }

                if (specContainer) {
                    // 컨테이너 내의 모든 DL 요소 추출
                    const dls = specContainer.querySelectorAll('dl');
                    dls.forEach(dl => {
                        const dts = dl.querySelectorAll('dt');
                        const dds = dl.querySelectorAll('dd');

                        dts.forEach((dt, i) => {
                            if (dds[i]) {
                                const key = dt.textContent.trim();
                                const value = dds[i].textContent.trim();
                                if (key && key !== 'Description') {
                                    result.specifications[key] = value;
                                }
                            }
                        });
                    });
                }

                // 방법 2: innerText 기반 파싱 (DL이 없는 경우의 폴백)
                if (Object.keys(result.specifications).length === 0 && specContainer) {
                    const text = specContainer.innerText;
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l);

                    for (let i = 0; i < lines.length - 1; i++) {
                        const key = lines[i];
                        const value = lines[i + 1];

                        // 제품 스펙 키워드인지 확인
                        if (key && (
                            key.includes('제품명') ||
                            key.includes('코드') ||
                            key.includes('재질') ||
                            key.includes('사양') ||
                            key.includes('Product') ||
                            key.includes('Material') ||
                            key.includes('Specification')
                        )) {
                            if (value && value !== 'Description' && !value.includes('List')) {
                                result.specifications[key] = value;
                                i++; // 다음 줄 스킵
                            }
                        }
                    }
                }

                // 방법 3: 페이지 전체에서 DL 요소 추출 (최후의 폴백)
                if (Object.keys(result.specifications).length === 0) {
                    const dls = document.querySelectorAll('dl');
                    dls.forEach(dl => {
                        const dts = dl.querySelectorAll('dt');
                        const dds = dl.querySelectorAll('dd');

                        dts.forEach((dt, i) => {
                            if (dds[i]) {
                                const key = dt.textContent.trim();
                                const value = dds[i].textContent.trim();
                                if (key && !['Phone', 'Fax', 'Email', 'Description'].includes(key)) {
                                    result.specifications[key] = value;
                                }
                            }
                        });
                    });
                }

                // ========================================
                // 4. 인쇄영역 다운로드 링크
                // ========================================
                const links = Array.from(document.querySelectorAll('a'));
                const printLink = links.find(link =>
                    link.textContent.includes('인쇄영역') &&
                    link.textContent.includes('다운로드')
                );

                result.print_area_url = printLink ? printLink.href : null;

                return result;
            }
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                data = result.get('result', {})

                logger.info(f"✓ 제품명: {data.get('product_name')}")
                logger.info(f"✓ 이미지: {len(data.get('images', []))}개")
                logger.info(f"✓ 스펙: {len(data.get('specifications', {}))}개 항목")
                logger.info(f"✓ 인쇄영역: {'있음' if data.get('print_area_url') else '없음'}")

                # 이미지 다운로드
                downloaded_images = []
                for i, img in enumerate(data.get('images', []), 1):
                    try:
                        local_path = await self._download_image(
                            img['url'],
                            idx,
                            img['type'],
                            i
                        )
                        downloaded_images.append({
                            **img,
                            'local_path': str(local_path)
                        })
                        logger.info(f"  ✓ 이미지 {i}: {img['type']} - {local_path.name}")
                    except Exception as e:
                        logger.warning(f"  ✗ 이미지 {i} 다운로드 실패: {e}")

                data['downloaded_images'] = downloaded_images

                # 인쇄영역 다운로드
                if data.get('print_area_url'):
                    try:
                        print_path = await self._download_print_area(
                            data['print_area_url'],
                            idx
                        )
                        data['print_area_local_path'] = str(print_path)
                        logger.info(f"  ✓ 인쇄영역: {print_path.name}")
                    except Exception as e:
                        logger.warning(f"  ✗ 인쇄영역 다운로드 실패: {e}")

                # 메타데이터 추가
                data['idx'] = idx
                data['url'] = url
                data['crawled_at'] = datetime.now().isoformat()

                # JSON 저장
                json_path = await self._save_json(data, idx)
                logger.info(f"✓ JSON 저장: {json_path.name}")

                await self.automation.close_browser()

                return {
                    'status': 'success',
                    'idx': idx,
                    'data': data,
                    'json_path': str(json_path)
                }

            else:
                raise Exception(f"데이터 추출 실패: {result}")

        except Exception as e:
            logger.error(f"✗ 크롤링 실패: {e}")
            await self.automation.close_browser()

            return {
                'status': 'error',
                'idx': idx,
                'url': url,
                'error': str(e)
            }

    async def _download_image(
        self,
        url: str,
        idx: str,
        img_type: str,
        img_num: int
    ) -> Path:
        """이미지 다운로드"""
        filename = f"idx_{idx}_{img_type}_{img_num}.jpg"
        output_path = self.images_dir / filename

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    output_path.write_bytes(content)
                else:
                    raise Exception(f"HTTP {response.status}")

        return output_path

    async def _download_print_area(self, url: str, idx: str) -> Path:
        """인쇄영역 PDF 다운로드"""
        filename = f"idx_{idx}_print_area.pdf"
        output_path = self.print_area_dir / filename

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    output_path.write_bytes(content)
                else:
                    raise Exception(f"HTTP {response.status}")

        return output_path

    async def _save_json(self, data: Dict[str, Any], idx: str) -> Path:
        """제품 데이터 JSON 저장"""
        filename = f"idx_{idx}.json"
        json_path = self.output_dir / filename

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return json_path

    async def crawl_multiple(
        self,
        urls: List[str],
        delay: int = 2
    ) -> Dict[str, Any]:
        """여러 제품 일괄 크롤링"""
        logger.info(f"\n{'='*80}")
        logger.info(f"청진코리아 크롤러 v2.0 - {len(urls)}개 제품 크롤링 시작")
        logger.info(f"{'='*80}")

        results = []
        success_count = 0
        error_count = 0

        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] 크롤링 중...")

            result = await self.crawl_product(url)

            if result['status'] == 'success':
                success_count += 1
            else:
                error_count += 1

            results.append(result)

            # 서버 부하 방지
            if i < len(urls):
                await asyncio.sleep(delay)

        # 요약
        summary = {
            'total': len(urls),
            'success': success_count,
            'error': error_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        # 요약 저장
        summary_path = self.output_dir / f"crawl_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 크롤링 완료!")
        logger.info(f"{'='*80}")
        logger.info(f"성공: {success_count}개")
        logger.info(f"실패: {error_count}개")
        logger.info(f"요약: {summary_path}")

        return summary

    async def get_product_urls_from_page(
        self,
        category_url: str,
        page: int = 1
    ) -> List[str]:
        """
        카테고리 페이지에서 제품 URL 추출 (그룹 페이지네이션 지원)

        로직:
        1. 메인 페이지 로드
        2. 목표 페이지가 현재 그룹에 있는지 확인
        3. 없으면 paging-next로 다음 그룹 이동
        4. 목표 페이지 클릭 (AJAX)
        5. 제품 URL 추출

        그룹 페이지네이션:
        - Jar: 페이지 1-4 (단일 그룹)
        - Cap&Pump: 그룹 1 (1-5), 그룹 2 (6-10), 그룹 3 (11-14)
        - Bottle: 그룹 1 (1-5), 그룹 2 (6-10), ... (예상)
        """
        try:
            await self.automation.launch_browser(headless=True, browser_type=self.browser_type)
            await self.automation.navigate(category_url)
            await asyncio.sleep(3)  # 초기 로딩

            if page > 1:
                # 그룹 페이지네이션: 목표 페이지까지 네비게이션
                max_attempts = 20  # 최대 그룹 이동 횟수 (무한 루프 방지)

                for attempt in range(max_attempts):
                    # 현재 보이는 페이지 번호 확인
                    check_pages_js = """
                    () => {
                        const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
                        const pageNumbers = pageLinks
                            .map(a => a.textContent.trim())
                            .filter(text => /^\d{1,3}$/.test(text))
                            .map(Number);

                        return {
                            visible_pages: pageNumbers,
                            min_page: Math.min(...pageNumbers),
                            max_page: Math.max(...pageNumbers)
                        };
                    }
                    """

                    pages_result = await self.automation.evaluate_javascript(check_pages_js)

                    if pages_result.get('status') == 'success':
                        pages_data = pages_result.get('result', {})
                        visible_pages = pages_data.get('visible_pages', [])
                        min_page = pages_data.get('min_page', 1)
                        max_page = pages_data.get('max_page', 1)

                        logger.debug(f"현재 그룹: {min_page}-{max_page} 페이지")

                        # 목표 페이지가 현재 그룹에 있는지 확인
                        if page in visible_pages:
                            logger.debug(f"페이지 {page}가 현재 그룹에 있음")
                            break

                        # 목표 페이지가 현재 그룹보다 뒤에 있으면 paging-next 클릭
                        if page > max_page:
                            logger.debug(f"페이지 {page}가 다음 그룹에 있음. paging-next 클릭...")

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

                            next_result = await self.automation.evaluate_javascript(next_js)

                            if next_result.get('status') == 'success':
                                if next_result.get('result', {}).get('clicked'):
                                    await asyncio.sleep(5)  # AJAX 로딩 대기
                                else:
                                    logger.warning(f"paging-next 버튼 없음 또는 비활성화")
                                    await self.automation.close_browser()
                                    return []
                        elif page < min_page:
                            # 목표 페이지가 현재 그룹보다 앞에 있음 (AJAX 로딩 지연 가능성)
                            logger.debug(f"페이지 {page}가 현재 그룹({min_page}-{max_page})보다 앞에 있음. AJAX 로딩 대기 중...")
                            await asyncio.sleep(2)  # 추가 대기
                            # 계속 시도 (return하지 않음)

                # 목표 페이지 버튼 클릭
                click_page_js = f"""
                () => {{
                    const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
                    const targetLink = pageLinks.find(a => {{
                        const text = a.textContent.trim();
                        return text === '{page}';
                    }});

                    if (targetLink) {{
                        targetLink.click();
                        return {{ clicked: true }};
                    }} else {{
                        const availablePages = pageLinks
                            .map(a => a.textContent.trim())
                            .filter(text => /^\d{{1,3}}$/.test(text));
                        return {{ clicked: false, available_pages: availablePages }};
                    }}
                }}
                """

                click_result = await self.automation.evaluate_javascript(click_page_js)

                if click_result.get('status') == 'success':
                    data = click_result.get('result', {})
                    if data.get('clicked'):
                        logger.info(f"페이지 {page} 버튼 클릭 성공")
                        await asyncio.sleep(5)  # AJAX 로딩 대기
                    else:
                        logger.warning(f"페이지 {page} 버튼 찾기 실패. 사용 가능: {data.get('available_pages')}")
                        await self.automation.close_browser()
                        return []

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

            result = await self.automation.evaluate_javascript(extract_js)
            await self.automation.close_browser()

            if result.get('status') == 'success':
                urls = result.get('result', [])
                logger.info(f"페이지 {page}: {len(urls)}개 제품 URL 발견")
                return urls
            else:
                logger.error(f"페이지 {page}: URL 추출 실패")
                return []

        except Exception as e:
            logger.error(f"페이지 {page} 처리 에러: {e}")
            await self.automation.close_browser()
            return []

    async def crawl_category(
        self,
        category_name: str,
        category_url: str,
        max_pages: int,
        delay: int = 2
    ) -> Dict[str, Any]:
        """카테고리 전체 크롤링 (페이지네이션 포함)"""
        logger.info(f"\n{'='*80}")
        logger.info(f"카테고리 크롤링 시작: {category_name}")
        logger.info(f"URL: {category_url}")
        logger.info(f"페이지: {max_pages}개")
        logger.info(f"{'='*80}")

        all_product_urls = []

        # 1단계: 모든 페이지에서 제품 URL 수집
        for page in range(1, max_pages + 1):
            logger.info(f"\n[페이지 {page}/{max_pages}] URL 수집 중...")
            page_urls = await self.get_product_urls_from_page(category_url, page)
            all_product_urls.extend(page_urls)

            if page < max_pages:
                await asyncio.sleep(delay)

        # 중복 제거 (페이지 간 중복 방지)
        unique_urls = list(set(all_product_urls))
        logger.info(f"\n수집: {len(all_product_urls)}개 URL")
        logger.info(f"중복 제거 후: {len(unique_urls)}개 URL")

        all_product_urls = unique_urls

        # 2단계: 수집된 URL로 제품 크롤링
        results = []
        success_count = 0
        error_count = 0

        for i, url in enumerate(all_product_urls, 1):
            logger.info(f"\n[{i}/{len(all_product_urls)}] 제품 크롤링 중...")

            result = await self.crawl_product(url)

            if result['status'] == 'success':
                success_count += 1
            else:
                error_count += 1

            results.append(result)

            if i < len(all_product_urls):
                await asyncio.sleep(delay)

        # 요약
        summary = {
            'category': category_name,
            'category_url': category_url,
            'total_pages': max_pages,
            'total_products': len(all_product_urls),
            'success': success_count,
            'error': error_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        # 카테고리별 요약 저장
        summary_path = self.output_dir / f"category_{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ {category_name} 크롤링 완료!")
        logger.info(f"{'='*80}")
        logger.info(f"총 제품: {len(all_product_urls)}개")
        logger.info(f"성공: {success_count}개")
        logger.info(f"실패: {error_count}개")
        logger.info(f"요약: {summary_path}")

        return summary

    async def crawl_all_categories(self, delay: int = 2) -> Dict[str, Any]:
        """전체 카테고리 크롤링"""
        categories = {
            "Bottle": {
                "url": "http://chungjinkorea.com/kr/product/list.php?part_idx=1",
                "pages": 68
            },
            "Jar": {
                "url": "http://chungjinkorea.com/kr/product/list.php?part_idx=2",
                "pages": 4
            },
            "Cap&Pump": {
                "url": "http://chungjinkorea.com/kr/product/list.php?part_idx=3",
                "pages": 14
            }
        }

        logger.info(f"\n{'='*80}")
        logger.info("청진코리아 전체 사이트 크롤링 시작")
        logger.info(f"총 카테고리: {len(categories)}개")
        logger.info(f"예상 페이지: {sum(cat['pages'] for cat in categories.values())}개")
        logger.info(f"{'='*80}")

        all_summaries = []

        for category_name, info in categories.items():
            summary = await self.crawl_category(
                category_name,
                info['url'],
                info['pages'],
                delay
            )
            all_summaries.append(summary)

        # 전체 요약
        total_products = sum(s['total_products'] for s in all_summaries)
        total_success = sum(s['success'] for s in all_summaries)
        total_error = sum(s['error'] for s in all_summaries)

        final_summary = {
            'categories': all_summaries,
            'total_products': total_products,
            'total_success': total_success,
            'total_error': total_error,
            'timestamp': datetime.now().isoformat()
        }

        # 전체 요약 저장
        final_path = self.output_dir / f"full_site_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(final_summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\n{'='*80}")
        logger.info("✅ 전체 사이트 크롤링 완료!")
        logger.info(f"{'='*80}")
        logger.info(f"총 제품: {total_products}개")
        logger.info(f"성공: {total_success}개")
        logger.info(f"실패: {total_error}개")
        logger.info(f"전체 요약: {final_path}")

        return final_summary


async def main():
    """테스트: Phase 1/2에서 분석한 8개 제품"""

    test_urls = [
        "http://chungjinkorea.com/kr/product/view.php?idx=960",
        "http://chungjinkorea.com/kr/product/view.php?idx=969",
        "http://chungjinkorea.com/kr/product/view.php?idx=967",
        "http://chungjinkorea.com/kr/product/view.php?idx=912",
        "http://chungjinkorea.com/kr/product/view.php?idx=928",
        "http://chungjinkorea.com/kr/product/view.php?idx=937",
        "http://chungjinkorea.com/kr/product/view.php?idx=946",
        "http://chungjinkorea.com/kr/product/view.php?idx=934"
    ]

    crawler = ChungjinCrawler(output_dir="data/chungjin_final_crawl")
    summary = await crawler.crawl_multiple(test_urls)

    print("\n" + "="*80)
    print("크롤링 요약")
    print("="*80)
    print(f"총 {summary['total']}개 중 {summary['success']}개 성공, {summary['error']}개 실패")


if __name__ == "__main__":
    asyncio.run(main())
