#!/usr/bin/env python3
"""
Phase 1 Targeted Analysis: 사용자 선택 페이지 집중 분석
목표:
- 각 카테고리별 사용자가 선택한 제품 페이지 상세 분석
- 모든 이미지 패턴 파악 (단수/복수)
- 제품 정보 구조 파악 (테이블/리스트/div)
- 인쇄영역 및 특수 요소 탐지
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TargetedAnalyzer:
    """선택된 제품 페이지 상세 분석기"""

    def __init__(self, output_dir: str = "dev/phase1_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.automation = DevToolsAutomation()
        self.results = []

    async def analyze_product_detailed(
        self,
        url: str,
        category: str
    ) -> Dict[str, Any]:
        """제품 페이지 초상세 분석"""
        idx = url.split('idx=')[1] if 'idx=' in url else 'unknown'

        logger.info("=" * 80)
        logger.info(f"분석 시작: [{category}] idx={idx}")
        logger.info(f"URL: {url}")
        logger.info("=" * 80)

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(url)
            await asyncio.sleep(3)  # 충분한 렌더링 시간

            # 초상세 분석 JavaScript
            js_code = """
            () => {
                const result = {
                    url: window.location.href,
                    page_title: document.title
                };

                // ============================================================
                // 1. 제품명 추출 (다양한 방법 시도)
                // ============================================================
                const productNameSelectors = [
                    'h1', 'h2', 'h3',
                    '.product_name', '.goods_name', '.product-name',
                    '.product-view-name', '.view-name',
                    'div.name', 'div.title'
                ];

                result.product_names = {};
                productNameSelectors.forEach(selector => {
                    const elem = document.querySelector(selector);
                    if (elem) {
                        result.product_names[selector] = elem.textContent.trim();
                    }
                });

                // 이미지 alt 텍스트에서도 추출
                const mainImg = document.querySelector('img[src*="goodsImages"]');
                if (mainImg && mainImg.alt) {
                    result.product_names['img_alt'] = mainImg.alt;
                }

                // ============================================================
                // 2. 모든 이미지 분석 (img 태그 + CSS background)
                // ============================================================
                const allProductImages = [];

                // 2-1. img 태그에서 제품 이미지 추출
                const allImgTags = Array.from(document.querySelectorAll('img'));
                const imgProductImages = allImgTags.filter(img =>
                    img.src.includes('goodsImages') || img.src.includes('GOODS')
                );

                imgProductImages.forEach((img, index) => {
                    const filename = img.src.split('/').pop();
                    let imageType = 'unknown';
                    if (filename.includes('GOODS1_')) imageType = 'main';
                    else if (filename.includes('ADD_GOODS1_')) imageType = 'additional_1';
                    else if (filename.includes('ADD_GOODS2_')) imageType = 'additional_2';
                    else if (filename.includes('ADD_GOODS3_')) imageType = 'additional_3';
                    else if (filename.includes('GOODS2_')) imageType = 'sub';

                    allProductImages.push({
                        source: 'img_tag',
                        src: img.src,
                        filename: filename,
                        alt: img.alt || '',
                        type_guess: imageType,
                        width: img.width,
                        height: img.height,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        className: img.className || '',
                        id: img.id || '',
                        parent: {
                            tag: img.parentElement?.tagName || '',
                            class: img.parentElement?.className || '',
                            id: img.parentElement?.id || ''
                        }
                    });
                });

                // 2-2. CSS background-image에서 제품 이미지 추출
                const allElements = Array.from(document.querySelectorAll('*'));
                allElements.forEach(elem => {
                    const style = window.getComputedStyle(elem);
                    const bgImage = style.backgroundImage;

                    if (bgImage && bgImage !== 'none' && bgImage.includes('url(')) {
                        const urlMatch = bgImage.match(/url\(["']?([^"')]+)["']?\)/);
                        if (urlMatch && urlMatch[1]) {
                            const url = urlMatch[1];

                            // goodsImages 경로만 추출
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
                                    src: url,
                                    filename: filename,
                                    type_guess: imageType,
                                    element: elem.tagName,
                                    className: elem.className || '',
                                    id: elem.id || ''
                                });
                            }
                        }
                    }
                });

                // 2-3. URL 기준 중복 제거 (같은 이미지는 한 번만)
                const uniqueImages = [];
                const seenUrls = new Set();

                allProductImages.forEach(img => {
                    if (!seenUrls.has(img.src)) {
                        seenUrls.add(img.src);
                        uniqueImages.push(img);
                    }
                });

                // 파일명 기준 정렬 (GOODS1 → ADD_GOODS1 → ADD_GOODS2 → ADD_GOODS3)
                uniqueImages.sort((a, b) => {
                    const order = { 'main': 0, 'additional_1': 1, 'additional_2': 2, 'additional_3': 3, 'sub': 4, 'unknown': 5 };
                    return (order[a.type_guess] || 99) - (order[b.type_guess] || 99);
                });

                result.images = {
                    total_img_tags: allImgTags.length,
                    product_images_count: uniqueImages.length,
                    all_product_images: uniqueImages.map((img, index) => ({
                        index: index + 1,
                        ...img
                    }))
                };

                // ============================================================
                // 3. 이미지 컨테이너 상세 분석
                // ============================================================
                const containerPatterns = [
                    'div.goods_img', 'ul.goods_img', 'div.product_img',
                    'div.view_img', 'div.image-gallery', 'ul.image-list',
                    'div[class*="image"]', 'div[class*="photo"]',
                    'div[class*="picture"]', 'div[class*="gallery"]',
                    'li', 'ul li'
                ];

                result.image_containers = [];
                containerPatterns.forEach(pattern => {
                    const elements = document.querySelectorAll(pattern);
                    elements.forEach((elem, elemIndex) => {
                        const imgs = Array.from(elem.querySelectorAll('img')).filter(img =>
                            img.src.includes('goodsImages')
                        );

                        if (imgs.length > 0) {
                            result.image_containers.push({
                                pattern: pattern,
                                element_index: elemIndex + 1,
                                tag: elem.tagName,
                                className: elem.className || '',
                                id: elem.id || '',
                                image_count: imgs.length,
                                image_srcs: imgs.map(img => img.src),
                                html_snippet: elem.outerHTML.substring(0, 200)
                            });
                        }
                    });
                });

                // ============================================================
                // 4. 제품 정보 추출 (다양한 구조)
                // ============================================================
                result.product_info = {
                    tables: [],
                    definition_lists: [],
                    divs: []
                };

                // 테이블
                const tables = Array.from(document.querySelectorAll('table'));
                tables.forEach((table, index) => {
                    const rows = Array.from(table.querySelectorAll('tr'));
                    const data = {};

                    rows.forEach(row => {
                        const cells = Array.from(row.querySelectorAll('th, td'));
                        if (cells.length >= 2) {
                            const key = cells[0].textContent.trim();
                            const value = cells[1].textContent.trim();
                            if (key) data[key] = value;
                        }
                    });

                    if (Object.keys(data).length > 0) {
                        result.product_info.tables.push({
                            index: index + 1,
                            className: table.className || '',
                            id: table.id || '',
                            data: data
                        });
                    }
                });

                // Definition List (dl/dt/dd)
                const dls = Array.from(document.querySelectorAll('dl'));
                dls.forEach((dl, index) => {
                    const dts = Array.from(dl.querySelectorAll('dt'));
                    const dds = Array.from(dl.querySelectorAll('dd'));
                    const data = {};

                    dts.forEach((dt, i) => {
                        if (dds[i]) {
                            data[dt.textContent.trim()] = dds[i].textContent.trim();
                        }
                    });

                    if (Object.keys(data).length > 0) {
                        result.product_info.definition_lists.push({
                            index: index + 1,
                            className: dl.className || '',
                            id: dl.id || '',
                            data: data
                        });
                    }
                });

                // Div 기반 정보
                const infoDivPatterns = [
                    'div[class*="info"]', 'div[class*="spec"]',
                    'div[class*="detail"]', 'div[class*="product"]'
                ];

                infoDivPatterns.forEach(pattern => {
                    const divs = document.querySelectorAll(pattern);
                    divs.forEach((div, index) => {
                        const text = div.textContent.trim();
                        // 제품 관련 키워드 체크
                        if (text.includes('제품') || text.includes('코드') ||
                            text.includes('재질') || text.includes('사양')) {
                            result.product_info.divs.push({
                                pattern: pattern,
                                index: index + 1,
                                className: div.className || '',
                                id: div.id || '',
                                text_preview: text.substring(0, 300),
                                html_snippet: div.outerHTML.substring(0, 300)
                            });
                        }
                    });
                });

                // ============================================================
                // 5. 인쇄영역 및 특수 영역 탐지
                // ============================================================
                const specialAreaPatterns = [
                    { name: 'print_area', patterns: ['div[id*="print"]', 'div[class*="print"]', 'section[class*="print"]'] },
                    { name: 'spec_area', patterns: ['div[id*="spec"]', 'div[class*="spec"]'] },
                    { name: 'detail_area', patterns: ['div[id*="detail"]', 'div[class*="detail"]'] }
                ];

                result.special_areas = {};
                specialAreaPatterns.forEach(({ name, patterns }) => {
                    for (const pattern of patterns) {
                        const elem = document.querySelector(pattern);
                        if (elem) {
                            result.special_areas[name] = {
                                pattern: pattern,
                                tag: elem.tagName,
                                className: elem.className || '',
                                id: elem.id || '',
                                has_images: elem.querySelectorAll('img').length,
                                has_table: elem.querySelectorAll('table').length > 0,
                                text_length: elem.textContent.trim().length,
                                html_snippet: elem.outerHTML.substring(0, 500)
                            };
                            break;
                        }
                    }
                });

                // ============================================================
                // 6. DOM 구조 통계
                // ============================================================
                result.dom_stats = {
                    total_elements: document.querySelectorAll('*').length,
                    total_divs: document.querySelectorAll('div').length,
                    total_tables: document.querySelectorAll('table').length,
                    total_lists: document.querySelectorAll('ul, ol, dl').length
                };

                return result;
            }
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                data = result.get('result', {})

                # 결과 로깅
                logger.info(f"\n제품명 후보:")
                for selector, name in data.get('product_names', {}).items():
                    if name and name != 'Menu':
                        logger.info(f"  {selector}: {name}")

                logger.info(f"\n이미지:")
                logger.info(f"  제품 이미지: {data['images']['product_images_count']}개")
                for img in data['images']['all_product_images']:
                    logger.info(f"    [{img['type_guess']}] {img['filename']} (source: {img.get('source', 'unknown')})")
                    if img.get('alt'):
                        logger.info(f"      alt: {img['alt']}")

                logger.info(f"\n컨테이너 패턴: {len(data.get('image_containers', []))}개")
                for cont in data.get('image_containers', [])[:3]:
                    logger.info(f"  {cont['pattern']}: {cont['image_count']}개 이미지")

                logger.info(f"\n제품 정보:")
                logger.info(f"  테이블: {len(data['product_info']['tables'])}개")
                logger.info(f"  Definition Lists: {len(data['product_info']['definition_lists'])}개")
                logger.info(f"  Info Divs: {len(data['product_info']['divs'])}개")

                logger.info(f"\n특수 영역:")
                for area_name, area_data in data.get('special_areas', {}).items():
                    logger.info(f"  {area_name}: {area_data['pattern']}")

                analysis_result = {
                    "category": category,
                    "url": url,
                    "idx": idx,
                    "analysis": data,
                    "timestamp": datetime.now().isoformat()
                }

                await self.automation.close_browser()
                return analysis_result
            else:
                raise Exception(f"분석 실패: {result}")

        except Exception as e:
            logger.error(f"✗ 에러: {e}")
            await self.automation.close_browser()
            return {
                "category": category,
                "url": url,
                "idx": idx,
                "error": str(e)
            }

    async def run_targeted_analysis(self, product_urls: Dict[str, List[str]]):
        """선택된 제품들 분석 실행"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1 Targeted Analysis: 선택 제품 상세 분석")
        logger.info("=" * 80)

        for category, urls in product_urls.items():
            logger.info(f"\n[{category}] {len(urls)}개 제품 분석")

            for url in urls:
                result = await self.analyze_product_detailed(url, category)
                self.results.append(result)
                await asyncio.sleep(2)  # 서버 부하 방지

        # 패턴 분석
        self._analyze_patterns()

        # 결과 저장
        self._save_results()

        logger.info("\n" + "=" * 80)
        logger.info("✅ 분석 완료!")
        logger.info("=" * 80)
        logger.info(f"분석된 제품: {len(self.results)}개")

    def _analyze_patterns(self):
        """패턴 분석"""
        logger.info("\n" + "=" * 80)
        logger.info("패턴 분석")
        logger.info("=" * 80)

        # 이미지 수 분포
        image_counts = []
        for r in self.results:
            if 'analysis' in r:
                count = r['analysis']['images']['product_images_count']
                image_counts.append({
                    'idx': r['idx'],
                    'category': r['category'],
                    'count': count
                })

        logger.info("\n이미지 수 분포:")
        for item in image_counts:
            logger.info(f"  [{item['category']}] idx={item['idx']}: {item['count']}개")

        # 제품명 추출 성공률
        logger.info("\n제품명 추출:")
        for r in self.results:
            if 'analysis' in r:
                names = r['analysis'].get('product_names', {})
                valid_names = {k: v for k, v in names.items() if v and v != 'Menu'}
                logger.info(f"  idx={r['idx']}: {len(valid_names)}개 후보")

        # 제품 정보 구조
        logger.info("\n제품 정보 구조:")
        for r in self.results:
            if 'analysis' in r:
                info = r['analysis']['product_info']
                logger.info(f"  idx={r['idx']}: 테이블 {len(info['tables'])}, DL {len(info['definition_lists'])}, Div {len(info['divs'])}")

    def _save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSON 저장
        result_file = self.output_dir / f"targeted_analysis_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_analyzed': len(self.results),
                'results': self.results
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"\n결과 저장: {result_file}")


async def main():
    """메인 실행"""
    # 사용자가 선택한 제품 URL
    product_urls = {
        "Bottle": [
            "http://chungjinkorea.com/kr/product/view.php?idx=960",
            "http://chungjinkorea.com/kr/product/view.php?idx=969",
            "http://chungjinkorea.com/kr/product/view.php?idx=967",
            "http://chungjinkorea.com/kr/product/view.php?idx=912"
        ],
        "Jar": [
            "http://chungjinkorea.com/kr/product/view.php?idx=928",
            "http://chungjinkorea.com/kr/product/view.php?idx=937"
        ],
        "Cap&Pump": [
            "http://chungjinkorea.com/kr/product/view.php?idx=946",
            "http://chungjinkorea.com/kr/product/view.php?idx=934"
        ]
    }

    analyzer = TargetedAnalyzer(output_dir="dev/phase1_results")
    await analyzer.run_targeted_analysis(product_urls)


if __name__ == "__main__":
    asyncio.run(main())
