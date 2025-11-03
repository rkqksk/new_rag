#!/usr/bin/env python3
"""
🔍 FREEMOLD.NET - API 분석 및 네트워크 요청 추출

목표: Chrome 개발자 도구 없이, 직접 HTTP 요청으로 인증된 데이터 추출
방식: requests 라이브러리 + 세션 유지
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "https://www.freemold.net"

# 테스트용 상품 ID (Phase 1에서 추출한 실제 ID)
TEST_PRODUCT_IDS = [87201, 87202, 87197, 87196, 87200]

def test_direct_api_access():
    """직접 API 요청으로 인증된 데이터 접근 가능한지 테스트"""

    print("\n" + "="*80)
    print("🔍 FREEMOLD API 테스트")
    print("="*80)

    session = requests.Session()
    session.verify = False  # SSL 검증 무시

    # requests 라이브러리 경고 무시
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 먼저 메인 페이지에 접속해서 세션 초기화
    print("\n1️⃣  메인 페이지 접속...")
    try:
        response = session.get(f"{BASE_URL}/", timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies: {len(session.cookies)}")
    except Exception as e:
        print(f"   ❌ 에러: {e}")
        return

    # 상품 상세 페이지 직접 접속 시도
    print("\n2️⃣  상품 상세 페이지 API 요청...")
    for product_id in TEST_PRODUCT_IDS[:2]:
        product_url = f"{BASE_URL}/Front/Product/?tp=vi&pIdx={product_id}"

        print(f"\n   상품 ID: {product_id}")
        print(f"   URL: {product_url}")

        try:
            response = session.get(product_url, timeout=10, verify=False)
            print(f"   Status: {response.status_code}")
            print(f"   Content-Length: {len(response.content)}")

            # 비회원 메시지 확인
            if '비회원은' in response.text:
                print(f"   ⚠️  비회원 에러 감지됨")
            elif 'product' in response.text.lower() or '제품' in response.text:
                print(f"   ✅ 상품 데이터 포함됨")
                # 처음 500자 출력
                print(f"\n   미리보기:\n{response.text[:500]}")
            else:
                print(f"   🤔 알 수 없는 응답")

        except Exception as e:
            print(f"   ❌ 에러: {e}")

        time.sleep(1)

    # 가능한 API 엔드포인트 테스트
    print("\n3️⃣  API 엔드포인트 탐색...")

    possible_endpoints = [
        "/api/product/detail",
        "/api/product/info",
        "/api/v1/product",
        "/Front/Product/Detail",
        "/Front/api/product",
    ]

    for endpoint in possible_endpoints:
        test_url = f"{BASE_URL}{endpoint}?pIdx={TEST_PRODUCT_IDS[0]}"
        try:
            response = session.get(test_url, timeout=5, verify=False)
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - 응답 있음")
                if response.text:
                    print(f"      Content: {response.text[:200]}")
        except:
            pass

    print("\n" + "="*80)

if __name__ == "__main__":
    test_direct_api_access()
