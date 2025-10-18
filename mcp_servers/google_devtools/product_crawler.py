"""
제품 페이지 전문 크롤러 v1.0
Google DevTools MCP를 활용한 구조화된 데이터 추출

기능:
- 제품 이미지 다운로드
- 인쇄영역 파일 다운로드
- 제품 정보 추출 (제품명, 코드, 재질, 사양)
- JSON 형식으로 저장
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.google_devtools.server import DevToolsAutomation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductPageCrawler:
    """제품 페이지 전문 크롤러"""

    def __init__(self, output_dir: str = "data/crawled_products"):
        """
        Args:
            output_dir: 크롤링 데이터 저장 디렉토리
        """
        self.automation = DevToolsAutomation()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 이미지 및 파일 저장 디렉토리
        self.images_dir = self.output_dir / "images"
        self.files_dir = self.output_dir / "files"
        self.images_dir.mkdir(exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)

    async def crawl_product_page(
        self,
        url: str,
        site_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        제품 페이지 크롤링 및 데이터 추출

        Args:
            url: 제품 페이지 URL
            site_config: 사이트별 CSS 셀렉터 설정

        Returns:
            구조화된 제품 데이터
        """
        logger.info(f"🔍 제품 페이지 크롤링 시작: {url}")

        try:
            # 1. 브라우저 시작
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            logger.info("✓ 브라우저 시작됨")

            # 2. 페이지 이동
            nav_result = await self.automation.navigate(url)
            if nav_result.get("status") != "success":
                raise Exception(f"페이지 로드 실패: {nav_result}")

            page_title = nav_result.get("title", "")
            logger.info(f"✓ 페이지 로드: {page_title}")

            # 3. 사이트 설정 적용 (기본값: 청진코리아)
            if not site_config:
                site_config = self._get_chungjin_config()

            # 4. 데이터 추출
            product_data = await self._extract_product_data(url, site_config)

            # 5. 제품 이미지 다운로드 (복수 이미지 지원)
            product_data["local_images"] = []

            if product_data.get("product_images"):
                for idx, img_info in enumerate(product_data["product_images"]):
                    try:
                        image_url = img_info.get("url")
                        img_type = img_info.get("type", "unknown")

                        # 파일명 prefix: main_1, thumbnail_2, etc.
                        prefix = f"{img_type}_{idx+1}_"

                        image_path = await self._download_file(
                            image_url,
                            self.images_dir,
                            prefix=prefix
                        )

                        product_data["local_images"].append({
                            "url": image_url,
                            "local_path": str(image_path),
                            "type": img_type,
                            "alt": img_info.get("alt", "")
                        })

                        logger.info(f"  ✓ {img_type} 이미지 다운로드: {image_path.name}")
                    except Exception as e:
                        logger.warning(f"  ✗ 이미지 다운로드 실패 ({image_url}): {e}")

            # 하위 호환성: 첫 번째 이미지를 local_image_path로 유지
            if product_data["local_images"]:
                product_data["local_image_path"] = product_data["local_images"][0]["local_path"]

            # 6. 인쇄영역 파일 다운로드
            if product_data.get("print_area_url"):
                file_path = await self._download_file(
                    product_data["print_area_url"],
                    self.files_dir,
                    prefix="printarea_"
                )
                product_data["local_printarea_path"] = str(file_path)
                logger.info(f"✓ 인쇄영역 파일 다운로드: {file_path}")

            # 7. 메타데이터 추가
            product_data["crawled_at"] = datetime.now().isoformat()
            product_data["source_url"] = url
            product_data["page_title"] = page_title

            # 8. JSON 저장
            json_path = await self._save_product_json(product_data)
            logger.info(f"✓ 제품 데이터 저장: {json_path}")

            # 9. 브라우저 종료
            await self.automation.close_browser()
            logger.info("✓ 브라우저 종료")

            return {
                "status": "success",
                "product_data": product_data,
                "json_path": str(json_path)
            }

        except Exception as e:
            logger.error(f"✗ 크롤링 실패: {e}")
            await self.automation.close_browser()
            return {
                "status": "error",
                "message": str(e),
                "url": url
            }

    async def _extract_product_data(
        self,
        url: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """JavaScript를 사용하여 제품 데이터 추출 (개선된 버전)"""

        selectors = config.get("selectors", {})

        # JavaScript 코드: DOM에서 데이터 추출
        js_code = """
        () => {
            const data = {};

            // 1. 제품 이미지 URL 추출 (복수 이미지 지원)
            // 패턴: img[src*='goodsImages'] + a[style*='goodsImages']
            data.product_images = [];

            // 메인 이미지 (img 태그)
            const mainImg = document.querySelector("img[src*='goodsImages']");
            if (mainImg && mainImg.src) {
                data.product_images.push({
                    url: mainImg.src,
                    alt: mainImg.alt || '',
                    type: 'main'
                });
            }

            // 추가 이미지 (background-image in style)
            const thumbnails = document.querySelectorAll("a[style*='goodsImages']");
            thumbnails.forEach(thumb => {
                const styleAttr = thumb.getAttribute('style');
                const urlMatch = styleAttr.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/);
                if (urlMatch && urlMatch[1]) {
                    const imageUrl = urlMatch[1];
                    // 중복 제거 (이미 추가된 URL은 스킵)
                    const isDuplicate = data.product_images.some(img => img.url === imageUrl);
                    if (!isDuplicate) {
                        data.product_images.push({
                            url: imageUrl,
                            alt: '',
                            type: 'thumbnail'
                        });
                    }
                }
            });

            // 메인 이미지 정보 (하위 호환성)
            if (data.product_images.length > 0) {
                data.image_url = data.product_images[0].url;
                data.image_alt = data.product_images[0].alt;
            }

            // 2. 인쇄영역 다운로드 URL (개선된 패턴)
            // 패턴 1: a[download] + textContent에 '인쇄영역' 포함
            const downloadLinks = document.querySelectorAll("a[download]");
            for (const link of downloadLinks) {
                if (link.textContent.includes('인쇄영역')) {
                    data.print_area_url = link.href;
                    break;
                }
            }

            // 패턴 2 (fallback): a[href*='goods_download.php']
            if (!data.print_area_url) {
                const phpDownload = document.querySelector("a[href*='goods_download.php']");
                if (phpDownload) {
                    data.print_area_url = phpDownload.href;
                }
            }

            // 3. 제품 정보 (feature list) - 현재 잘 작동하는 부분
            const featureElements = document.querySelectorAll(".feature-list li");

            data.specifications = {};
            featureElements.forEach(li => {
                const titleEl = li.querySelector('h5.tit');
                const textEl = li.querySelector('p.txt');

                if (titleEl && textEl) {
                    const key = titleEl.textContent.trim();
                    const value = textEl.textContent.trim();
                    data.specifications[key] = value;
                }
            });

            // 4. 제품명 추출 (specifications에서 우선, 없으면 h5.tit 첫번째)
            if (data.specifications['제품명']) {
                data.product_name = data.specifications['제품명'];
            } else {
                const productNameElement = document.querySelector("h5.tit");
                if (productNameElement) {
                    data.product_name = productNameElement.textContent.trim();
                } else if (data.image_alt) {
                    data.product_name = data.image_alt;
                }
            }

            return data;
        }
        """

        result = await self.automation.evaluate_javascript(js_code)

        if result.get("status") == "success":
            extracted_data = result.get("result", {})

            # 로깅 개선: 이미지 개수, 인쇄영역 여부 표시
            image_count = len(extracted_data.get("product_images", []))
            has_printarea = bool(extracted_data.get("print_area_url"))
            logger.info(f"✓ 데이터 추출: 이미지 {image_count}개, 인쇄영역 {'✓' if has_printarea else '✗'}, 사양 {len(extracted_data.get('specifications', {}))}개")

            return extracted_data
        else:
            raise Exception(f"데이터 추출 실패: {result}")

    async def _download_file(
        self,
        url: str,
        output_dir: Path,
        prefix: str = ""
    ) -> Path:
        """파일 다운로드 (이미지, PDF 등)"""

        # URL에서 파일명 추출
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        if not filename or filename == "goods_download.php":
            # 파일명이 없거나 PHP 스크립트인 경우 타임스탬프 사용
            ext = ".pdf" if "download" in url else ".jpg"
            filename = f"{prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        else:
            filename = f"{prefix}{filename}"

        output_path = output_dir / filename

        # 파일 다운로드
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    output_path.write_bytes(content)
                    logger.debug(f"파일 다운로드: {url} -> {output_path}")
                else:
                    raise Exception(f"다운로드 실패 (HTTP {response.status}): {url}")

        return output_path

    async def _save_product_json(self, product_data: Dict[str, Any]) -> Path:
        """제품 데이터를 JSON 파일로 저장"""

        # 파일명: 제품코드 또는 타임스탬프
        product_code = product_data.get("specifications", {}).get("제품 코드", "")
        if product_code:
            filename = f"{product_code}.json"
        else:
            filename = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        json_path = self.output_dir / filename

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

        return json_path

    def _get_chungjin_config(self) -> Dict[str, Any]:
        """청진코리아 사이트 설정"""
        return {
            "name": "청진코리아",
            "selectors": {
                "image": "img[alt]",  # 제품 이미지
                "download": "a[download]",  # 인쇄영역 다운로드
                "features": ".feature-list li",  # 제품 정보 리스트
                "product_name": "h5.tit"  # 제품명
            }
        }

    async def crawl_multiple_products(
        self,
        urls: List[str],
        site_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """여러 제품 페이지 일괄 크롤링"""

        logger.info(f"🚀 일괄 크롤링 시작: {len(urls)}개 제품")

        results = []
        success_count = 0
        error_count = 0

        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] {url}")

            result = await self.crawl_product_page(url, site_config)

            if result.get("status") == "success":
                success_count += 1
            else:
                error_count += 1

            results.append(result)

            # 다음 요청 전 대기 (서버 부하 방지)
            if i < len(urls):
                await asyncio.sleep(2)

        summary = {
            "status": "completed",
            "total": len(urls),
            "success": success_count,
            "error": error_count,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

        # 요약 JSON 저장
        summary_path = self.output_dir / f"crawl_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ 크롤링 완료: 성공 {success_count}, 실패 {error_count}")
        logger.info(f"요약 저장: {summary_path}")

        return summary


async def main():
    """CLI 테스트"""

    # 청진코리아 제품 페이지 예시
    test_urls = [
        "http://chungjinkorea.com/kr/product/view.php?idx=224",  # 400ml 브로우용기
        # "http://chungjinkorea.com/kr/product/view.php?idx=777",  # 450g 크림사출용기
        # 추가 URL...
    ]

    crawler = ProductPageCrawler(output_dir="data/crawled_products")

    # 단일 제품 크롤링
    result = await crawler.crawl_product_page(test_urls[0])

    print("\n" + "=" * 60)
    print("크롤링 결과")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 여러 제품 크롤링 (주석 해제 시 사용)
    # summary = await crawler.crawl_multiple_products(test_urls)


if __name__ == "__main__":
    asyncio.run(main())
