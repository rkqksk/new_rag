#!/usr/bin/env python3
"""
idx=960 제품 이미지 정밀 검증
사용자가 4장이라고 확인했으므로 모든 이미지를 상세히 분석
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def verify_images():
    """idx=960의 모든 이미지 상세 분석"""
    automation = DevToolsAutomation()

    try:
        await automation.launch_browser(headless=False, browser_type="webkit")  # 헤드리스 OFF로 확인
        await automation.navigate("http://chungjinkorea.com/kr/product/view.php?idx=960")
        await asyncio.sleep(5)  # 충분한 로딩 시간

        # 모든 이미지 상세 분석 (필터링 없이)
        js_code = """
        () => {
            const allImages = Array.from(document.querySelectorAll('img'));

            return {
                total_count: allImages.length,
                all_images: allImages.map((img, index) => ({
                    index: index + 1,
                    src: img.src,
                    alt: img.alt || '',
                    width: img.width,
                    height: img.height,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    className: img.className || '',
                    id: img.id || '',
                    // 경로 분석
                    is_data_path: img.src.includes('/data/'),
                    is_goods: img.src.includes('goods') || img.src.includes('GOODS'),
                    is_logo: img.src.includes('logo') || img.src.includes('Logo'),
                    is_icon: img.src.includes('icon') || img.src.includes('Icon'),
                    // 부모 구조
                    parent: {
                        tag: img.parentElement?.tagName,
                        class: img.parentElement?.className || '',
                        id: img.parentElement?.id || ''
                    },
                    // HTML 스니펫
                    html: img.outerHTML.substring(0, 200)
                }))
            };
        }
        """

        result = await automation.evaluate_javascript(js_code)

        if result.get('status') == 'success':
            data = result.get('result', {})

            print(f"\n{'='*80}")
            print(f"idx=960 전체 이미지 분석")
            print(f"{'='*80}\n")
            print(f"총 이미지 수: {data['total_count']}개\n")

            # 제품 이미지로 보이는 것들 필터링
            product_images = []
            ui_images = []

            for img in data['all_images']:
                print(f"[이미지 {img['index']}]")
                print(f"  src: {img['src']}")
                print(f"  alt: {img['alt']}")
                print(f"  크기: {img['width']}x{img['height']} (실제: {img['naturalWidth']}x{img['naturalHeight']})")
                print(f"  class: {img['className']}")
                print(f"  parent: <{img['parent']['tag']} class='{img['parent']['class']}'>")

                # 분류
                is_product = False
                if img['is_data_path'] and not img['is_logo'] and not img['is_icon']:
                    if img['naturalWidth'] >= 200:  # 충분히 큰 이미지
                        is_product = True
                        product_images.append(img)
                        print(f"  >>> 제품 이미지로 판단")
                    else:
                        ui_images.append(img)
                        print(f"  >>> UI 요소로 판단")
                else:
                    ui_images.append(img)
                    print(f"  >>> 로고/아이콘으로 판단")

                print()

            print(f"{'='*80}")
            print(f"분류 결과:")
            print(f"  제품 이미지: {len(product_images)}개")
            print(f"  UI/로고: {len(ui_images)}개")
            print(f"{'='*80}\n")

            if len(product_images) >= 4:
                print("✅ 4개 이상의 제품 이미지 발견!")
                print("\n제품 이미지 목록:")
                for img in product_images:
                    print(f"  - {img['src']}")
                    print(f"    alt: {img['alt']}")
            else:
                print(f"⚠️  제품 이미지 {len(product_images)}개만 발견")
                print("필터링 조건을 재검토해야 함")

        await automation.close_browser()

    except Exception as e:
        print(f"에러: {e}")
        await automation.close_browser()


if __name__ == "__main__":
    asyncio.run(verify_images())
