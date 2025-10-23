"""
대화 컨텍스트 관리 시스템
Redis 기반 세션 관리 및 대화 이력 추적
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis
from redis import Redis


class ConversationManager:
    """대화 세션 및 컨텍스트 관리"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Args:
            redis_url: Redis 연결 URL
        """
        self.redis_client: Redis = redis.from_url(
            redis_url,
            decode_responses=True
        )
        self.session_ttl = 3600  # 1시간 (초 단위)
        self.max_history_length = 10  # 최대 대화 이력 개수

    def create_session(self, user_id: str = None) -> str:
        """
        새 대화 세션 생성

        Args:
            user_id: 사용자 ID (선택사항)

        Returns:
            session_id: 생성된 세션 ID
        """
        session_id = f"chat_session:{uuid.uuid4()}"

        session_data = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "context": {
                "search_history": [],
                "current_focus": None,  # 현재 포커스 제품 idx
                "previous_products": [],  # 이전 검색 결과 제품들
                "filters": {},  # 활성 필터
                "preferences": {},  # 사용자 선호도
                "conversation_state": "initial"  # 대화 상태
            }
        }

        # Redis에 저장 (TTL 설정)
        self.redis_client.setex(
            session_id,
            self.session_ttl,
            json.dumps(session_data, ensure_ascii=False)
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        세션 데이터 조회

        Args:
            session_id: 세션 ID

        Returns:
            세션 데이터 또는 None
        """
        data = self.redis_client.get(session_id)
        if data:
            return json.loads(data)
        return None

    def update_session(self, session_id: str, session_data: Dict) -> bool:
        """
        세션 데이터 업데이트

        Args:
            session_id: 세션 ID
            session_data: 업데이트할 세션 데이터

        Returns:
            성공 여부
        """
        try:
            # 마지막 활동 시간 갱신
            session_data["last_activity"] = datetime.now().isoformat()

            # Redis에 저장 (TTL 갱신)
            self.redis_client.setex(
                session_id,
                self.session_ttl,
                json.dumps(session_data, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"세션 업데이트 실패: {e}")
            return False

    def add_to_history(
        self,
        session_id: str,
        query: str,
        intent: str,
        results: List[Dict],
        response: str = None
    ) -> bool:
        """
        대화 이력에 새로운 턴 추가

        Args:
            session_id: 세션 ID
            query: 사용자 쿼리
            intent: 감지된 의도
            results: 검색 결과
            response: 시스템 응답

        Returns:
            성공 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 새 이력 항목 생성
        history_item = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "intent": intent,
            "result_count": len(results),
            "result_idxs": [r.get("idx") for r in results[:5]],
            "response": response
        }

        # 검색 이력에 추가
        session["context"]["search_history"].append(history_item)

        # 최대 길이 제한
        if len(session["context"]["search_history"]) > self.max_history_length:
            session["context"]["search_history"] = \
                session["context"]["search_history"][-self.max_history_length:]

        # 세션 업데이트
        return self.update_session(session_id, session)

    def update_focus(
        self,
        session_id: str,
        product_idx: str,
        product_list: List[str] = None
    ) -> bool:
        """
        현재 포커스 제품 업데이트

        Args:
            session_id: 세션 ID
            product_idx: 포커스할 제품 idx
            product_list: 이전 검색 결과 제품 목록

        Returns:
            성공 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 현재 포커스 업데이트
        session["context"]["current_focus"] = product_idx

        # 이전 제품 목록 업데이트
        if product_list:
            # 중복 제거하면서 추가
            existing = set(session["context"]["previous_products"])
            new_products = [p for p in product_list if p not in existing]
            session["context"]["previous_products"].extend(new_products)

            # 최대 50개까지만 유지
            if len(session["context"]["previous_products"]) > 50:
                session["context"]["previous_products"] = \
                    session["context"]["previous_products"][-50:]

        return self.update_session(session_id, session)

    def update_filters(
        self,
        session_id: str,
        filters: Dict[str, Any]
    ) -> bool:
        """
        활성 필터 업데이트

        Args:
            session_id: 세션 ID
            filters: 새 필터 딕셔너리

        Returns:
            성공 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 필터 병합 (새 값이 기존 값 덮어씀)
        session["context"]["filters"].update(filters)

        # None 값 제거 (필터 해제)
        session["context"]["filters"] = {
            k: v for k, v in session["context"]["filters"].items()
            if v is not None
        }

        return self.update_session(session_id, session)

    def get_context(self, session_id: str) -> Optional[Dict]:
        """
        컨텍스트 정보 조회

        Args:
            session_id: 세션 ID

        Returns:
            컨텍스트 딕셔너리 또는 None
        """
        session = self.get_session(session_id)
        if session:
            return session.get("context", {})
        return None

    def get_recent_history(
        self,
        session_id: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        최근 대화 이력 조회

        Args:
            session_id: 세션 ID
            limit: 최대 개수

        Returns:
            최근 이력 리스트
        """
        context = self.get_context(session_id)
        if context and "search_history" in context:
            return context["search_history"][-limit:]
        return []

    def clear_focus(self, session_id: str) -> bool:
        """
        현재 포커스 제품 초기화

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["context"]["current_focus"] = None
        return self.update_session(session_id, session)

    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        try:
            self.redis_client.delete(session_id)
            return True
        except Exception as e:
            print(f"세션 삭제 실패: {e}")
            return False

    def extend_session_ttl(self, session_id: str) -> bool:
        """
        세션 TTL 연장

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        try:
            self.redis_client.expire(session_id, self.session_ttl)
            return True
        except Exception as e:
            print(f"TTL 연장 실패: {e}")
            return False

    def get_all_sessions(self, user_id: str = None) -> List[str]:
        """
        모든 활성 세션 ID 조회

        Args:
            user_id: 특정 사용자의 세션만 조회 (선택사항)

        Returns:
            세션 ID 리스트
        """
        pattern = "chat_session:*"
        session_keys = self.redis_client.keys(pattern)

        if user_id:
            # 특정 사용자 필터링
            filtered = []
            for key in session_keys:
                session = self.get_session(key)
                if session and session.get("user_id") == user_id:
                    filtered.append(key)
            return filtered

        return session_keys

    def get_session_stats(self, session_id: str) -> Dict:
        """
        세션 통계 정보

        Args:
            session_id: 세션 ID

        Returns:
            통계 정보 딕셔너리
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        context = session.get("context", {})

        created = datetime.fromisoformat(session["created_at"])
        last_activity = datetime.fromisoformat(session["last_activity"])
        duration = (last_activity - created).total_seconds()

        return {
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "duration_seconds": duration,
            "total_queries": len(context.get("search_history", [])),
            "unique_products_viewed": len(set(context.get("previous_products", []))),
            "active_filters": len(context.get("filters", {})),
            "created_at": session["created_at"],
            "last_activity": session["last_activity"]
        }
