#!/usr/bin/env python3
"""
idx=960 심층 이미지 검증 - 모든 가능한 이미지 소스 탐지
- img 태그
- CSS background-image
- data-* 속성의 이미지 URL
- picture/source 태그
- 동적 로드 이미지
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def deep_image_analysis():
    """모든 가능한 이미지 소스 탐지"""
    automation = DevToolsAutomation()

    try:
        await automation.launch_browser(headless=False, browser_type="webkit")
        await automation.navigate("http://chungjinkorea.com/kr/product/view.php?idx=960")

        # 충분한 대기 시간 (동적 콘텐츠 로드)
        await asyncio.sleep(8)

        # 모든 이미지 소스 탐지 JavaScript
        js_code = """
        () => {
            const result = {
                img_tags: [],
                background_images: [],
                data_src_images: [],
                picture_sources: [],
                lazy_load_images: []
            };

            // 1. 모든 img 태그
            const allImgs = Array.from(document.querySelectorAll('img'));
            result.img_tags = allImgs.map((img, i) => ({
                index: i + 1,
                src: img.src,
                data_src: img.getAttribute('data-src') || '',
                data_original: img.getAttribute('data-original') || '',
                alt: img.alt || '',
                width: img.width,
                height: img.height,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                className: img.className || '',
                parent_class: img.parentElement?.className || '',
                parent_tag: img.parentElement?.tagName || ''
            }));

            // 2. CSS background-image
            const allElements = Array.from(document.querySelectorAll('*'));
            allElements.forEach((elem, i) => {
                const style = window.getComputedStyle(elem);
                const bgImage = style.backgroundImage;

                if (bgImage && bgImage !== 'none' && bgImage.includes('url(')) {
                    // url("...") 형식에서 URL 추출
                    const urlMatch = bgImage.match(/url\(["']?([^"')]+)["']?\)/);
                    if (urlMatch && urlMatch[1]) {
                        result.background_images.push({
                            url: urlMatch[1],
                            element: elem.tagName,
                            className: elem.className || '',
                            id: elem.id || ''
                        });
                    }
                }
            });

            // 3. data-src, data-original 속성 (lazy loading)
            const lazyElements = Array.from(document.querySelectorAll('[data-src], [data-original], [data-lazy]'));
            lazyElements.forEach((elem, i) => {
                const dataSrc = elem.getAttribute('data-src') ||
                              elem.getAttribute('data-original') ||
                              elem.getAttribute('data-lazy');

                if (dataSrc) {
                    result.lazy_load_images.push({
                        data_src: dataSrc,
                        element: elem.tagName,
                        className: elem.className || '',
                        src: elem.src || ''
                    });
                }
            });

            // 4. picture/source 태그
            const pictures = Array.from(document.querySelectorAll('picture'));
            pictures.forEach((picture, i) => {
                const sources = Array.from(picture.querySelectorAll('source'));
                const img = picture.querySelector('img');

                result.picture_sources.push({
                    sources: sources.map(s => ({
                        srcset: s.srcset || '',
                        media: s.media || '',
                        type: s.type || ''
                    })),
                    img_src: img?.src || ''
                });
            });

            // 5. 갤러리/슬라이더 컨테이너 탐지
            const galleryPatterns = [
                '.gallery', '.slider', '.carousel', '.swiper',
                '.product-images', '.goods-images', '.image-list',
                '[class*="gallery"]', '[class*="slider"]', '[class*="image"]'
            ];

            result.gallery_containers = [];
            galleryPatterns.forEach(pattern => {
                const containers = document.querySelectorAll(pattern);
                containers.forEach((container, i) => {
                    const images = container.querySelectorAll('img');
                    if (images.length > 0) {
                        result.gallery_containers.push({
                            pattern: pattern,
                            className: container.className || '',
                            id: container.id || '',
                            image_count: images.length,
                            images: Array.from(images).map(img => ({
                                src: img.src,
                                alt: img.alt || '',
                                data_src: img.getAttribute('data-src') || ''
                            }))
                        });
                    }
                });
            });

            return result;
        }
        """

        result = await automation.evaluate_javascript(js_code)

        if result.get('status') == 'success':
            data = result.get('result', {})

            print("\n" + "="*80)
            print("idx=960 심층 이미지 분석")
            print("="*80 + "\n")

            # 1. img 태그
            print(f"[1] IMG 태그: {len(data['img_tags'])}개")
            for img in data['img_tags']:
                print(f"  [{img['index']}] {img['src']}")
                print(f"      alt: {img['alt']}")
                print(f"      크기: {img['width']}x{img['height']} (실제: {img['naturalWidth']}x{img['naturalHeight']})")
                if img['data_src']:
                    print(f"      data-src: {img['data_src']}")
                if img['data_original']:
                    print(f"      data-original: {img['data_original']}")
                print()

            # 2. Background images
            print(f"\n[2] CSS Background Images: {len(data['background_images'])}개")
            for bg in data['background_images']:
                print(f"  - {bg['url']}")
                print(f"    element: <{bg['element']} class='{bg['className']}'>")
                print()

            # 3. Lazy load images
            print(f"\n[3] Lazy Load Images: {len(data['lazy_load_images'])}개")
            for lazy in data['lazy_load_images']:
                print(f"  - data-src: {lazy['data_src']}")
                print(f"    element: <{lazy['element']} class='{lazy['className']}'>")
                print()

            # 4. Picture sources
            print(f"\n[4] Picture/Source Tags: {len(data['picture_sources'])}개")
            for pic in data['picture_sources']:
                print(f"  - img: {pic['img_src']}")
                print(f"    sources: {len(pic['sources'])}개")
                print()

            # 5. Gallery containers
            print(f"\n[5] Gallery/Slider Containers: {len(data['gallery_containers'])}개")
            for gallery in data['gallery_containers']:
                print(f"  [{gallery['pattern']}] {gallery['image_count']}개 이미지")
                print(f"    class: {gallery['className']}")
                for img in gallery['images']:
                    print(f"      - {img['src']}")
                    if img['data_src']:
                        print(f"        (data-src: {img['data_src']})")
                print()

            # 종합 분석
            print("\n" + "="*80)
            print("종합 분석")
            print("="*80)

            # 제품 이미지로 보이는 것들 필터링
            product_images = []

            # img 태그에서
            for img in data['img_tags']:
                if 'goods' in img['src'].lower() or 'product' in img['src'].lower():
                    if img['naturalWidth'] >= 200:
                        product_images.append(f"IMG: {img['src']}")

            # background에서
            for bg in data['background_images']:
                if 'goods' in bg['url'].lower() or 'product' in bg['url'].lower():
                    product_images.append(f"BG: {bg['url']}")

            print(f"\n발견된 제품 이미지: {len(product_images)}개")
            for img in product_images:
                print(f"  - {img}")

            if len(product_images) >= 4:
                print("\n✅ 4개 이상의 제품 이미지 발견!")
            else:
                print(f"\n⚠️  제품 이미지 {len(product_images)}개만 발견")
                print("추가 조사 필요:")
                print("  1. 페이지에 JavaScript 갤러리가 있는가?")
                print("  2. 클릭/호버 시 추가 이미지가 로드되는가?")
                print("  3. 모바일 버전과 다른 이미지 구조인가?")

        await automation.close_browser()

    except Exception as e:
        print(f"에러: {e}")
        await automation.close_browser()


if __name__ == "__main__":
    asyncio.run(deep_image_analysis())
