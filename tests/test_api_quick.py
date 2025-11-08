"""
빠른 API 테스트
"""

import json

import requests

API_BASE = "http://localhost:8001"

print("=" * 60)
print("  제품 비교 API 테스트")
print("=" * 60)

# 1. 헬스 체크
print("\n1. 헬스 체크")
response = requests.get(f"{API_BASE}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 2. 비교 메트릭 조회
print("\n2. 비교 메트릭 조회")
response = requests.get(f"{API_BASE}/compare/metrics")
print(f"Status: {response.status_code}")
result = response.json()
print(f"총 메트릭: {result['total_count']}개")
print(f"메트릭 목록: {list(result['metrics'].keys())}")

# 3. 제품 비교 (2개)
print("\n3. 제품 비교 (2개 제품)")
response = requests.post(
    f"{API_BASE}/compare/products",
    json={"product_idxs": ["823", "209"], "metrics": ["재질", "용량", "가격", "호환성"]},
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"비교 제품 수: {result['product_count']}개")

    # 제품 이름
    print("\n📦 비교 제품:")
    for i, product in enumerate(result["products"], 1):
        print(f"  {i}. {product.get('product_name', 'N/A')}")

    # 비교 매트릭스
    print("\n📊 비교 매트릭스:")
    for row in result["comparison_matrix"]:
        metric = row["metric"]
        values = " | ".join([v["display"] for v in row["values"]])
        print(f"  {metric}: {values}")

    # 추천
    print(f"\n💡 추천:")
    print(f"  {result['recommendation']}")
else:
    print(f"Error: {response.text}")

# 4. 제품 비교 (5개)
print("\n" + "=" * 60)
print("4. 제품 비교 (5개 제품 - 전체 메트릭)")
response = requests.post(
    f"{API_BASE}/compare/products",
    json={"product_idxs": ["823", "209", "248", "835", "321"], "metrics": None},  # 전체 메트릭
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"비교 제품 수: {result['product_count']}개")
    print(f"비교 메트릭: {', '.join(result['metrics'])}")

    # 하이라이트 개수
    highlights = 0
    for row in result["comparison_matrix"]:
        for value in row["values"]:
            if value.get("highlight") == "best":
                highlights += 1
    print(f"하이라이트: {highlights}개 ★")

    # 추천
    print(f"\n💡 추천:")
    for line in result["recommendation"].split("\n"):
        if line.strip():
            print(f"  {line}")
else:
    print(f"Error: {response.text}")

print("\n" + "=" * 60)
print("  테스트 완료!")
print("=" * 60)
print("\n🌐 프론트엔드 데모:")
print("  frontend/comparison-demo.html 브라우저에서 열기")
print("  (서버가 http://localhost:8001 에서 실행 중)")
