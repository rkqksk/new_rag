#!/usr/bin/env python3
"""
컨텍스트 인식 채팅 MVP 테스트 스크립트
"""

import time
from typing import Dict, List

import requests


class ChatTester:
    """채팅 시스템 테스트"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session_id = None

    def create_session(self) -> bool:
        """세션 생성"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/create_session", json={"user_id": "test_user"}
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            print(f"✅ 세션 생성 성공: {self.session_id}")
            return True
        except Exception as e:
            print(f"❌ 세션 생성 실패: {e}")
            return False

    def send_query(self, query: str) -> Dict:
        """쿼리 전송"""
        if not self.session_id:
            print("❌ 세션이 없습니다.")
            return {}

        try:
            response = requests.post(
                f"{self.base_url}/chat/query", json={"session_id": self.session_id, "query": query}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 쿼리 실패: {e}")
            return {}

    def test_scenario_1_basic_search(self):
        """시나리오 1: 기본 검색"""
        print("\n" + "=" * 60)
        print("📋 시나리오 1: 기본 검색")
        print("=" * 60)

        queries = ["100ml 에센스 용기 추천해줘", "PE 재질로 찾아줘", "투명한 것만 보여줘"]

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}] 👤 사용자: {query}")
            result = self.send_query(query)

            if result:
                print(f"    🤖 응답: {result.get('response', 'N/A')}")
                print(f"    📊 의도: {result.get('intent', {}).get('intent', 'N/A')}")
                print(f"    📦 제품 수: {result.get('total_count', 0)}")
            time.sleep(1)

    def test_scenario_2_reference_resolution(self):
        """시나리오 2: 참조 해결"""
        print("\n" + "=" * 60)
        print("📋 시나리오 2: 참조 해결")
        print("=" * 60)

        queries = [
            "100ml 용기 추천해줘",
            "첫 번째 제품 상세 정보",
            "그 용기에 맞는 펌프는?",
            "가격은 얼마야?",
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}] 👤 사용자: {query}")
            result = self.send_query(query)

            if result:
                print(f"    🤖 응답: {result.get('response', 'N/A')[:100]}...")
                print(f"    📊 의도: {result.get('intent', {}).get('intent', 'N/A')}")
                print(f"    🔗 참조 해결: {'✅' if result.get('reference_resolved') else '❌'}")
                if result.get("expanded_query"):
                    print(f"    📝 확장된 쿼리: {result['expanded_query'][:80]}...")
            time.sleep(1)

    def test_scenario_3_context_maintenance(self):
        """시나리오 3: 컨텍스트 유지"""
        print("\n" + "=" * 60)
        print("📋 시나리오 3: 컨텍스트 유지")
        print("=" * 60)

        queries = ["클렌징 오일 용기", "더 저렴한 옵션", "투명한 걸로", "100개 주문하면 총 얼마야?"]

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}] 👤 사용자: {query}")
            result = self.send_query(query)

            if result:
                print(f"    🤖 응답: {result.get('response', 'N/A')[:100]}...")
                print(f"    📊 의도: {result.get('intent', {}).get('intent', 'N/A')}")
                filters = result.get("filters_applied", {})
                if filters:
                    print(f"    🔍 적용된 필터: {filters}")
            time.sleep(1)

    def test_scenario_4_compatibility(self):
        """시나리오 4: 호환성 확인"""
        print("\n" + "=" * 60)
        print("📋 시나리오 4: 호환성 확인")
        print("=" * 60)

        queries = [
            "100ml PE 용기 추천",
            "첫 번째 제품 호환 펌프",
            "그 중에서 가장 저렴한 거",
            "전체 패키지 가격",
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}] 👤 사용자: {query}")
            result = self.send_query(query)

            if result:
                print(f"    🤖 응답: {result.get('response', 'N/A')[:100]}...")
                print(f"    📊 의도: {result.get('intent', {}).get('intent', 'N/A')}")
                print(f"    📦 제품 수: {result.get('total_count', 0)}")
            time.sleep(1)

    def run_all_tests(self):
        """전체 테스트 실행"""
        print("\n" + "=" * 60)
        print("🧪 컨텍스트 인식 채팅 MVP 테스트 시작")
        print("=" * 60)

        # 세션 생성
        if not self.create_session():
            return

        # 시나리오 실행
        self.test_scenario_1_basic_search()
        self.test_scenario_2_reference_resolution()

        # 새 세션으로 독립 테스트
        print("\n" + "=" * 60)
        print("🔄 새 세션 시작 (컨텍스트 초기화)")
        print("=" * 60)
        self.create_session()

        self.test_scenario_3_context_maintenance()
        self.test_scenario_4_compatibility()

        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)

    def test_health(self):
        """헬스 체크"""
        try:
            response = requests.get(f"{self.base_url}/chat/health")
            response.raise_for_status()
            data = response.json()

            print("\n🏥 시스템 상태:")
            print(f"  상태: {data.get('status', 'N/A')}")
            print(f"  Redis: {data.get('redis', 'N/A')}")

            services = data.get("services", {})
            print("  서비스:")
            for service, status in services.items():
                print(f"    - {service}: {status}")

            return data.get("status") == "healthy"
        except Exception as e:
            print(f"❌ 헬스 체크 실패: {e}")
            return False


def main():
    """메인 실행"""
    tester = ChatTester()

    # 1. 헬스 체크
    if not tester.test_health():
        print("\n⚠️  서버가 실행되지 않았습니다.")
        print("다음 명령어로 서버를 시작하세요:")
        print("  python run_chat_server.py")
        return

    # 2. 전체 테스트 실행
    tester.run_all_tests()

    # 3. 추가 정보
    print("\n💡 추가 테스트:")
    print("  - WebSocket 테스트: frontend/chat-demo.html 열기")
    print("  - API 문서: http://localhost:8001/docs")
    print("  - Redis 데이터: redis-cli KEYS chat_session:*")


if __name__ == "__main__":
    main()
