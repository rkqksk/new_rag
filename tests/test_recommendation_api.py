"""
스마트 추천 API 테스트
"""

import json

import requests

API_BASE = "http://localhost:8001"

print("=" * 60)
print("  스마트 추천 API 테스트")
print("=" * 60)

# 1. 제품군 프로필 목록 조회
print("\n1. 제품군 프로필 목록")
response = requests.get(f"{API_BASE}/recommend/profiles")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"총 프로필: {result['total_count']}개")
    print(f"\n제품군 목록:")
    for i, (name, profile) in enumerate(result["profiles"].items(), 1):
        keywords = ", ".join(profile["keywords"][:3])
        print(f"  {i:2d}. {name:12s} - {keywords}")

# 2. 스마트 추천 테스트 (클렌징오일)
print("\n" + "=" * 60)
print("2. 스마트 추천 - 클렌징오일")
response = requests.post(
    f"{API_BASE}/recommend/smart",
    json={
        "query": "클렌징오일 용기 추천해줘",
        "user_id": None,
        "limit": 5,
        "use_personalization": False,
    },
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"쿼리: {result['query']}")
    print(f"매칭된 프로필: {result.get('matched_profile', 'N/A')}")
    print(f"프로필 설명: {result.get('profile_description', 'N/A')}")
    print(f"추천 타입: {result['recommendation_type']}")
    print(f"추천 제품 수: {result['total_count']}개")

    if result["total_count"] > 0:
        print(f"\n📦 추천 제품 (상위 3개):")
        for i, product in enumerate(result["products"][:3], 1):
            name = product.get("product_name", "N/A")
            score = product.get("recommendation_score", 0)
            reason = product.get("recommendation_reason", "N/A")
            print(f"  {i}. {name}")
            print(f"     점수: {score:.2f}")
            print(f"     이유: {reason}")
    else:
        print("검색 결과가 없습니다.")
else:
    print(f"Error: {response.text}")

# 3. 스마트 추천 테스트 (토너)
print("\n" + "=" * 60)
print("3. 스마트 추천 - 토너")
response = requests.post(
    f"{API_BASE}/recommend/smart",
    json={"query": "토너 용기", "limit": 5, "use_personalization": False},
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"매칭된 프로필: {result.get('matched_profile', 'N/A')}")
    print(f"프로필 설명: {result.get('profile_description', 'N/A')}")
    print(f"추천 제품 수: {result['total_count']}개")
else:
    print(f"Error: {response.text}")

# 4. 인터랙션 추적 테스트
print("\n" + "=" * 60)
print("4. 사용자 인터랙션 추적")
response = requests.post(
    f"{API_BASE}/recommend/track",
    json={"user_id": "test_user_123", "product_idx": "823", "action": "click"},
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"성공: {result['success']}")
    print(f"메시지: {result['message']}")
    print(f"사용자: {result['user_id']}")
    print(f"제품: {result['product_idx']}")
    print(f"행동: {result['action']}")

# 5. 사용자 프로필 조회
print("\n5. 사용자 프로필 조회")
response = requests.get(f"{API_BASE}/recommend/profile/test_user_123")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"사용자 ID: {result['user_id']}")
    print(f"총 인터랙션: {result['total_interactions']}회")
    print(f"재질 선호도: {dict(result['material_preference'])}")
    print(f"용량 선호도: {dict(result['capacity_preference'])}")
    print(f"가격 민감도: {result['price_sensitivity']:.2f}")

print("\n" + "=" * 60)
print("  추천 API 테스트 완료!")
print("=" * 60)
