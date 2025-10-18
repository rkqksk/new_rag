#!/usr/bin/env python3
"""
Phase 1: 카테고리 구조 및 샘플링 분석
목표:
- 카테고리 구조 파악
- 페이지네이션 분석
- 각 카테고리에서 랜덤 2-3개 샘플링
- 상세 HTML 구조 분석 (이미지, 인쇄영역)
- 패턴 분석 리포트 생성
"""

import asyncio
import json
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase1Analyzer:
    """Phase 1: 카테고리 및 샘플링 분석기"""

    def __init__(self, base_url: str, output_dir: str = "dev/phase1_results"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.automation = DevToolsAutomation()
        self.analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "categories": [],
            "samples": [],
            "patterns": {},
            "recommendations": []
        }

    async def analyze_category_structure(
        self,
        start_url: str,
        category_selector: str = "a[href*='list.php']"
    ) -> List[Dict[str, Any]]:
        """카테고리 구조 분석"""
        logger.info("=" * 80)
        logger.info("Phase 1-1: 카테고리 구조 분석")
        logger.info("=" * 80)

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(start_url)
            await asyncio.sleep(2)

            # 카테고리 링크 및 메타데이터 추출
            # f-string 안에서 백슬래시 사용 불가로 임시 변수 사용
            escaped_selector = category_selector.replace('"', '\\"')
            js_code = f"""
            () => {{
                const selector = "{escaped_selector}";
                const links = Array.from(document.querySelectorAll(selector));

                return links.map((a, index) => {{
                    // URL에서 idx 추출
                    const url = a.href;
                    const urlParams = new URLSearchParams(url.split('?')[1]);
                    const idx = urlParams.get('idx');

                    return {{
                        index: index + 1,
                        text: a.textContent.trim(),
                        href: url,
                        idx: idx,
                        parent_class: a.parentElement?.className || '',
                        parent_tag: a.parentElement?.tagName || ''
                    }};
                }});
            }}
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                categories = result.get('result', [])

                # 중복 제거
                unique_categories = []
                seen_hrefs = set()

                for cat in categories:
                    if cat['href'] not in seen_hrefs:
                        unique_categories.append(cat)
                        seen_hrefs.add(cat['href'])

                logger.info(f"\n✓ 발견된 카테고리: {len(unique_categories)}개")
                for cat in unique_categories:
                    logger.info(f"  {cat['index']}. {cat['text']} (idx={cat['idx']})")

                self.analysis_results['categories'] = unique_categories

                await self.automation.close_browser()
                return unique_categories
            else:
                raise Exception(f"카테고리 추출 실패: {result}")

        except Exception as e:
            logger.error(f"✗ 카테고리 분석 실패: {e}")
            await self.automation.close_browser()
            return []

    async def analyze_category_pagination(
        self,
        category_url: str,
        category_name: str
    ) -> Dict[str, Any]:
        """카테고리 페이지네이션 및 제품 수 분석"""
        logger.info(f"\n카테고리 분석: {category_name}")
        logger.info("-" * 80)

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(category_url)
            await asyncio.sleep(2)

            # 페이지네이션 및 제품 정보 추출
            js_code = """
            () => {
                // 페이지네이션 분석
                const paginationLinks = Array.from(document.querySelectorAll('a[href*="page="], a.page, .pagination a'));
                const pageNumbers = paginationLinks.map(a => {
                    const match = a.href.match(/page=(\\d+)/);
                    return match ? parseInt(match[1]) : null;
                }).filter(n => n !== null);

                const maxPage = pageNumbers.length > 0 ? Math.max(...pageNumbers) : 1;

                // 제품 링크 추출
                const productLinks = Array.from(document.querySelectorAll("a[href*='view.php']"));
                const productUrls = productLinks.map(a => a.href);

                // 제품 idx 추출
                const productIds = productUrls.map(url => {
                    const match = url.match(/idx=(\\d+)/);
                    return match ? parseInt(match[1]) : null;
                }).filter(id => id !== null);

                return {
                    total_pages: maxPage,
                    products_on_page: productIds.length,
                    product_ids: productIds,
                    pagination_found: paginationLinks.length > 0
                };
            }
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                data = result.get('result', {})

                logger.info(f"  페이지네이션: {data['total_pages']}페이지")
                logger.info(f"  현재 페이지 제품 수: {data['products_on_page']}개")
                logger.info(f"  제품 ID 범위: {min(data['product_ids']) if data['product_ids'] else 'N/A'} ~ {max(data['product_ids']) if data['product_ids'] else 'N/A'}")

                await self.automation.close_browser()
                return {
                    "category_name": category_name,
                    "category_url": category_url,
                    "pagination": data
                }
            else:
                raise Exception(f"페이지네이션 분석 실패: {result}")

        except Exception as e:
            logger.error(f"  ✗ 분석 실패: {e}")
            await self.automation.close_browser()
            return {
                "category_name": category_name,
                "category_url": category_url,
                "error": str(e)
            }

    async def sample_products_from_category(
        self,
        category_url: str,
        category_name: str,
        sample_size: int = 3
    ) -> List[str]:
        """카테고리에서 랜덤으로 제품 샘플링"""
        logger.info(f"\n랜덤 샘플링: {category_name} (목표: {sample_size}개)")

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(category_url)
            await asyncio.sleep(2)

            # 모든 제품 링크 추출
            js_code = """
            () => {
                const productLinks = Array.from(document.querySelectorAll("a[href*='view.php']"));
                return [...new Set(productLinks.map(a => a.href))];
            }
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                product_urls = result.get('result', [])

                # 랜덤 샘플링
                sample_urls = random.sample(
                    product_urls,
                    min(sample_size, len(product_urls))
                )

                logger.info(f"  ✓ {len(sample_urls)}개 제품 선택됨")
                for url in sample_urls:
                    idx = url.split('idx=')[1] if 'idx=' in url else 'N/A'
                    logger.info(f"    - idx={idx}")

                await self.automation.close_browser()
                return sample_urls
            else:
                raise Exception(f"제품 추출 실패: {result}")

        except Exception as e:
            logger.error(f"  ✗ 샘플링 실패: {e}")
            await self.automation.close_browser()
            return []

    async def analyze_product_html_structure(
        self,
        product_url: str,
        category_name: str
    ) -> Dict[str, Any]:
        """제품 페이지 상세 HTML 구조 분석"""
        idx = product_url.split('idx=')[1] if 'idx=' in product_url else 'unknown'
        logger.info(f"\n  제품 분석: idx={idx}")

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(product_url)
            await asyncio.sleep(3)  # JavaScript 렌더링 대기

            # 상세 HTML 구조 분석
            js_code = """
            () => {
                // 1. 모든 이미지 분석
                const allImages = Array.from(document.querySelectorAll('img'));
                const productImages = allImages.filter(img =>
                    img.src.includes('goodsImages') || img.src.includes('GOODS')
                ).map((img, index) => ({
                    index: index + 1,
                    src: img.src,
                    alt: img.alt || '',
                    width: img.width,
                    height: img.height,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    className: img.className || '',
                    id: img.id || '',
                    parent_tag: img.parentElement?.tagName || '',
                    parent_class: img.parentElement?.className || '',
                    parent_id: img.parentElement?.id || ''
                }));

                // 2. 이미지 컨테이너 패턴 분석
                const containerPatterns = [
                    'div.goods_img', 'div.product_img', 'div.view_img',
                    'ul.goods_img', 'li img', 'div[id*="goods"]',
                    'div[class*="product"]', 'div[class*="detail"]'
                ];

                const foundContainers = [];
                containerPatterns.forEach(pattern => {
                    const elements = document.querySelectorAll(pattern);
                    if (elements.length > 0) {
                        elements.forEach(elem => {
                            const imgs = elem.querySelectorAll('img');
                            const prodImgs = Array.from(imgs).filter(img =>
                                img.src.includes('goodsImages')
                            );
                            if (prodImgs.length > 0) {
                                foundContainers.push({
                                    pattern: pattern,
                                    tag: elem.tagName,
                                    className: elem.className || '',
                                    id: elem.id || '',
                                    image_count: prodImgs.length,
                                    image_urls: prodImgs.map(img => img.src)
                                });
                            }
                        });
                    }
                });

                // 3. 제품 정보 테이블 분석
                const tables = Array.from(document.querySelectorAll('table'));
                const productTables = tables.map((table, index) => {
                    const rows = Array.from(table.querySelectorAll('tr'));
                    const data = rows.map(row => {
                        const cells = Array.from(row.querySelectorAll('th, td'));
                        return cells.map(cell => cell.textContent.trim());
                    });

                    return {
                        index: index + 1,
                        rows: data.length,
                        className: table.className || '',
                        id: table.id || '',
                        has_product_info: data.some(row =>
                            row.some(cell =>
                                cell.includes('제품') ||
                                cell.includes('코드') ||
                                cell.includes('재질') ||
                                cell.includes('사양')
                            )
                        ),
                        sample_data: data.slice(0, 3)
                    };
                });

                // 4. 인쇄영역 탐지
                const printAreaPatterns = [
                    'div[id*="print"]', 'div[class*="print"]',
                    'section[id*="print"]', 'section[class*="print"]',
                    'div[id*="spec"]', 'div[class*="spec"]'
                ];

                let printArea = null;
                for (const pattern of printAreaPatterns) {
                    const elem = document.querySelector(pattern);
                    if (elem) {
                        printArea = {
                            pattern: pattern,
                            tag: elem.tagName,
                            className: elem.className || '',
                            id: elem.id || '',
                            has_images: elem.querySelectorAll('img').length > 0,
                            text_length: elem.textContent.trim().length
                        };
                        break;
                    }
                }

                // 5. 제품명 추출
                const titleSelectors = ['h1', 'h2', '.product_name', '.goods_name', 'title'];
                let productName = '';
                for (const selector of titleSelectors) {
                    const elem = document.querySelector(selector);
                    if (elem && elem.textContent.trim()) {
                        productName = elem.textContent.trim();
                        break;
                    }
                }

                return {
                    url: window.location.href,
                    title: document.title,
                    product_name: productName,
                    images: {
                        total_images: allImages.length,
                        product_images_count: productImages.length,
                        details: productImages
                    },
                    containers: foundContainers,
                    tables: productTables.filter(t => t.has_product_info),
                    print_area: printArea,
                    dom_stats: {
                        total_elements: document.querySelectorAll('*').length,
                        total_divs: document.querySelectorAll('div').length,
                        total_tables: tables.length
                    }
                };
            }
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                data = result.get('result', {})

                # 분석 결과 로깅
                logger.info(f"    제품명: {data.get('product_name', 'N/A')}")
                logger.info(f"    이미지: {data['images']['product_images_count']}개")
                logger.info(f"    컨테이너 패턴: {len(data['containers'])}개")
                logger.info(f"    제품 정보 테이블: {len(data['tables'])}개")
                logger.info(f"    인쇄영역: {'있음' if data['print_area'] else '없음'}")

                analysis = {
                    "category": category_name,
                    "url": product_url,
                    "idx": idx,
                    "analysis": data,
                    "timestamp": datetime.now().isoformat()
                }

                await self.automation.close_browser()
                return analysis
            else:
                raise Exception(f"HTML 분석 실패: {result}")

        except Exception as e:
            logger.error(f"    ✗ 분석 실패: {e}")
            await self.automation.close_browser()
            return {
                "category": category_name,
                "url": product_url,
                "idx": idx,
                "error": str(e)
            }

    async def run_full_analysis(
        self,
        start_url: str,
        samples_per_category: int = 3
    ):
        """전체 Phase 1 분석 실행"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1: 카테고리 구조 및 샘플링 분석 시작")
        logger.info("=" * 80)

        # 1. 카테고리 구조 분석
        categories = await self.analyze_category_structure(start_url)

        if not categories:
            logger.error("카테고리를 찾을 수 없습니다.")
            return

        # 2. 각 카테고리 분석 및 샘플링
        logger.info("\n" + "=" * 80)
        logger.info(f"Phase 1-2: 카테고리별 샘플링 ({samples_per_category}개씩)")
        logger.info("=" * 80)

        for cat in categories[:]:  # 모든 카테고리 분석
            # 페이지네이션 분석
            pagination_info = await self.analyze_category_pagination(
                cat['href'],
                cat['text']
            )

            # 랜덤 샘플링
            sample_urls = await self.sample_products_from_category(
                cat['href'],
                cat['text'],
                sample_size=samples_per_category
            )

            # 샘플 제품 상세 분석
            for product_url in sample_urls:
                sample_analysis = await self.analyze_product_html_structure(
                    product_url,
                    cat['text']
                )
                self.analysis_results['samples'].append(sample_analysis)
                await asyncio.sleep(1)  # 서버 부하 방지

        # 3. 패턴 분석
        self._analyze_patterns()

        # 4. 권장사항 생성
        self._generate_recommendations()

        # 5. 결과 저장
        self._save_results()

        logger.info("\n" + "=" * 80)
        logger.info("✅ Phase 1 분석 완료!")
        logger.info("=" * 80)
        logger.info(f"분석된 카테고리: {len(categories)}개")
        logger.info(f"분석된 샘플: {len(self.analysis_results['samples'])}개")

    def _analyze_patterns(self):
        """수집된 데이터에서 패턴 분석"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1-3: 패턴 분석")
        logger.info("=" * 80)

        samples = self.analysis_results['samples']

        # 이미지 수 분포
        image_counts = [s['analysis']['images']['product_images_count']
                       for s in samples if 'analysis' in s]

        # 컨테이너 패턴 빈도
        all_patterns = []
        for s in samples:
            if 'analysis' in s and 'containers' in s['analysis']:
                all_patterns.extend([c['pattern'] for c in s['analysis']['containers']])

        pattern_freq = {}
        for p in all_patterns:
            pattern_freq[p] = pattern_freq.get(p, 0) + 1

        # 인쇄영역 유무
        print_area_count = sum(1 for s in samples
                              if 'analysis' in s and s['analysis'].get('print_area'))

        patterns = {
            "image_distribution": {
                "min": min(image_counts) if image_counts else 0,
                "max": max(image_counts) if image_counts else 0,
                "avg": sum(image_counts) / len(image_counts) if image_counts else 0,
                "counts": image_counts
            },
            "container_patterns": pattern_freq,
            "print_area": {
                "with_print_area": print_area_count,
                "without_print_area": len(samples) - print_area_count,
                "percentage": (print_area_count / len(samples) * 100) if samples else 0
            }
        }

        self.analysis_results['patterns'] = patterns

        logger.info(f"\n이미지 수 분포:")
        logger.info(f"  최소: {patterns['image_distribution']['min']}개")
        logger.info(f"  최대: {patterns['image_distribution']['max']}개")
        logger.info(f"  평균: {patterns['image_distribution']['avg']:.1f}개")

        logger.info(f"\n가장 많이 발견된 컨테이너 패턴:")
        for pattern, count in sorted(pattern_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"  {pattern}: {count}번")

        logger.info(f"\n인쇄영역:")
        logger.info(f"  있음: {print_area_count}개 ({patterns['print_area']['percentage']:.1f}%)")
        logger.info(f"  없음: {patterns['print_area']['without_print_area']}개")

    def _generate_recommendations(self):
        """분석 결과 기반 권장사항 생성"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1-4: 권장사항 생성")
        logger.info("=" * 80)

        patterns = self.analysis_results['patterns']
        recommendations = []

        # 이미지 처리 전략
        max_images = patterns['image_distribution']['max']
        if max_images <= 1:
            recommendations.append({
                "category": "이미지 처리",
                "finding": "대부분 제품이 단일 이미지",
                "action": "단순 이미지 추출 로직으로 충분"
            })
        elif max_images <= 3:
            recommendations.append({
                "category": "이미지 처리",
                "finding": "제품당 1-3개 이미지",
                "action": "메인 이미지 + 추가 이미지 분리 처리 필요"
            })
        else:
            recommendations.append({
                "category": "이미지 처리",
                "finding": f"최대 {max_images}개 이미지",
                "action": "복수 이미지 처리 로직 필수, 우선순위 지정 필요"
            })

        # 컨테이너 패턴
        if patterns['container_patterns']:
            most_common = max(patterns['container_patterns'].items(), key=lambda x: x[1])
            recommendations.append({
                "category": "컨테이너 패턴",
                "finding": f"가장 많은 패턴: {most_common[0]}",
                "action": f"우선적으로 {most_common[0]} 패턴 사용, fallback 패턴 준비"
            })

        # 인쇄영역
        print_pct = patterns['print_area']['percentage']
        if print_pct < 50:
            recommendations.append({
                "category": "인쇄영역",
                "finding": f"{print_pct:.1f}% 제품만 인쇄영역 보유",
                "action": "인쇄영역이 없는 경우 대체 전략 필수 (제품 정보 테이블 활용)"
            })
        else:
            recommendations.append({
                "category": "인쇄영역",
                "finding": f"{print_pct:.1f}% 제품이 인쇄영역 보유",
                "action": "인쇄영역 우선 추출, 없으면 fallback"
            })

        self.analysis_results['recommendations'] = recommendations

        logger.info("\n권장사항:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"\n{i}. [{rec['category']}]")
            logger.info(f"   발견: {rec['finding']}")
            logger.info(f"   조치: {rec['action']}")

    def _save_results(self):
        """분석 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 전체 결과 JSON
        result_file = self.output_dir / f"phase1_analysis_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)

        # 읽기 쉬운 리포트
        report_file = self.output_dir / f"phase1_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Phase 1: 카테고리 구조 및 샘플링 분석 리포트\n\n")
            f.write(f"**분석 일시:** {self.analysis_results['timestamp']}\n\n")

            f.write("## 1. 카테고리 목록\n\n")
            for cat in self.analysis_results['categories']:
                f.write(f"- {cat['text']} (idx={cat['idx']})\n")

            f.write(f"\n## 2. 샘플 분석 결과\n\n")
            f.write(f"총 {len(self.analysis_results['samples'])}개 제품 분석\n\n")

            f.write("### 2.1 이미지 분포\n\n")
            patterns = self.analysis_results['patterns']
            f.write(f"- 최소: {patterns['image_distribution']['min']}개\n")
            f.write(f"- 최대: {patterns['image_distribution']['max']}개\n")
            f.write(f"- 평균: {patterns['image_distribution']['avg']:.1f}개\n\n")

            f.write("### 2.2 컨테이너 패턴\n\n")
            for pattern, count in sorted(patterns['container_patterns'].items(),
                                        key=lambda x: x[1], reverse=True):
                f.write(f"- `{pattern}`: {count}번\n")

            f.write("\n### 2.3 인쇄영역\n\n")
            f.write(f"- 있음: {patterns['print_area']['with_print_area']}개 ")
            f.write(f"({patterns['print_area']['percentage']:.1f}%)\n")
            f.write(f"- 없음: {patterns['print_area']['without_print_area']}개\n\n")

            f.write("## 3. 권장사항\n\n")
            for i, rec in enumerate(self.analysis_results['recommendations'], 1):
                f.write(f"### 3.{i} {rec['category']}\n\n")
                f.write(f"**발견사항:** {rec['finding']}\n\n")
                f.write(f"**권장 조치:** {rec['action']}\n\n")

        logger.info(f"\n결과 저장:")
        logger.info(f"  JSON: {result_file}")
        logger.info(f"  리포트: {report_file}")


async def main():
    """Phase 1 실행"""
    analyzer = Phase1Analyzer(
        base_url="http://chungjinkorea.com",
        output_dir="dev/phase1_results"
    )

    await analyzer.run_full_analysis(
        start_url="http://chungjinkorea.com/kr/product/list.php",
        samples_per_category=3  # 카테고리당 3개 샘플링
    )


if __name__ == "__main__":
    asyncio.run(main())
