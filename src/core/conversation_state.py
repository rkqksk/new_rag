"""
대화 상태 머신 (Conversation State Machine)
영업사원 수준의 맥락 기반 대화를 위한 상태 관리
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class ConversationState(str, Enum):
    """대화 상태"""
    GREETING = "greeting"                    # 인사/시작
    SEARCHING = "searching"                  # 검색 중
    RESULTS_SHOWN = "results_shown"          # 결과 표시됨
    FILTERING = "filtering"                  # 필터링 중 (누적)
    FOCUSED = "focused"                      # 특정 제품 포커스
    COMPARING = "comparing"                  # 제품 비교 중
    COMPATIBILITY_CHECK = "compatibility_check"  # 호환성 확인 중
    DOCUMENT_REQUEST = "document_request"    # 문서 요청
    CLARIFICATION = "clarification"          # 명확화 필요
    IDLE = "idle"                           # 대기 중


@dataclass
class DialogueContext:
    """대화 컨텍스트 (확장된 버전)"""

    # 기본 정보
    session_id: str
    user_id: str
    created_at: str
    last_activity: str

    # 상태 정보
    current_state: ConversationState = ConversationState.GREETING
    previous_state: Optional[ConversationState] = None

    # 검색 결과 관리
    last_query: str = ""
    last_search_results: List[str] = field(default_factory=list)  # product idx list
    display_indices: Dict[int, str] = field(default_factory=dict)  # {1: "idx_123", 2: "idx_456"}

    # 필터 관리 (누적)
    active_filters: Dict[str, Any] = field(default_factory=dict)
    filter_history: List[Dict[str, Any]] = field(default_factory=list)

    # 포커스 제품
    focused_product: Optional[str] = None
    focused_product_name: Optional[str] = None

    # 비교 모드
    comparison_products: List[str] = field(default_factory=list)

    # 대화 히스토리
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)

    # 사용자 선호도
    user_preferences: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환 (Redis 저장용)"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "current_state": self.current_state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "last_query": self.last_query,
            "last_search_results": self.last_search_results,
            "display_indices": self.display_indices,
            "active_filters": self.active_filters,
            "filter_history": self.filter_history,
            "focused_product": self.focused_product,
            "focused_product_name": self.focused_product_name,
            "comparison_products": self.comparison_products,
            "conversation_history": self.conversation_history,
            "user_preferences": self.user_preferences
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DialogueContext":
        """딕셔너리에서 복원"""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            current_state=ConversationState(data.get("current_state", "greeting")),
            previous_state=ConversationState(data["previous_state"]) if data.get("previous_state") else None,
            last_query=data.get("last_query", ""),
            last_search_results=data.get("last_search_results", []),
            display_indices={int(k): v for k, v in data.get("display_indices", {}).items()},
            active_filters=data.get("active_filters", {}),
            filter_history=data.get("filter_history", []),
            focused_product=data.get("focused_product"),
            focused_product_name=data.get("focused_product_name"),
            comparison_products=data.get("comparison_products", []),
            conversation_history=data.get("conversation_history", []),
            user_preferences=data.get("user_preferences", {})
        )


class StateTransition:
    """상태 전환 규칙"""

    @staticmethod
    def can_transition(
        from_state: ConversationState,
        to_state: ConversationState,
        context: DialogueContext
    ) -> bool:
        """상태 전환 가능 여부 확인"""

        # 전환 규칙 매트릭스
        valid_transitions = {
            ConversationState.GREETING: [
                ConversationState.SEARCHING,
                ConversationState.IDLE
            ],
            ConversationState.SEARCHING: [
                ConversationState.RESULTS_SHOWN,
                ConversationState.FILTERING,        # "PET만" (검색 결과 필터링)
                ConversationState.FOCUSED,          # "3번" (검색 중 특정 제품 선택)
                ConversationState.SEARCHING,        # 새 검색 (연속 검색)
                ConversationState.CLARIFICATION,
                ConversationState.IDLE
            ],
            ConversationState.RESULTS_SHOWN: [
                ConversationState.FILTERING,        # "PET만"
                ConversationState.FOCUSED,          # "3번"
                ConversationState.COMPARING,        # "비교해줘"
                ConversationState.SEARCHING,        # 새 검색
                ConversationState.COMPATIBILITY_CHECK,  # "호환되는 캡"
                ConversationState.DOCUMENT_REQUEST, # "원산지 증명서"
                ConversationState.IDLE
            ],
            ConversationState.FILTERING: [
                ConversationState.RESULTS_SHOWN,    # 필터 적용 완료
                ConversationState.FILTERING,        # 추가 필터
                ConversationState.FOCUSED,
                ConversationState.SEARCHING,
                ConversationState.IDLE
            ],
            ConversationState.FOCUSED: [
                ConversationState.COMPATIBILITY_CHECK,
                ConversationState.DOCUMENT_REQUEST,
                ConversationState.COMPARING,
                ConversationState.RESULTS_SHOWN,    # 목록으로 돌아가기
                ConversationState.SEARCHING,
                ConversationState.IDLE
            ],
            ConversationState.COMPARING: [
                ConversationState.FOCUSED,
                ConversationState.RESULTS_SHOWN,
                ConversationState.SEARCHING,
                ConversationState.IDLE
            ],
            ConversationState.COMPATIBILITY_CHECK: [
                ConversationState.RESULTS_SHOWN,
                ConversationState.FOCUSED,
                ConversationState.SEARCHING,
                ConversationState.IDLE
            ],
            ConversationState.DOCUMENT_REQUEST: [
                ConversationState.FOCUSED,
                ConversationState.RESULTS_SHOWN,
                ConversationState.SEARCHING,
                ConversationState.IDLE
            ],
            ConversationState.CLARIFICATION: [
                ConversationState.SEARCHING,
                ConversationState.FILTERING,
                ConversationState.IDLE
            ],
            ConversationState.IDLE: [
                ConversationState.SEARCHING,
                ConversationState.GREETING
            ]
        }

        return to_state in valid_transitions.get(from_state, [])

    @staticmethod
    def transition(
        context: DialogueContext,
        to_state: ConversationState,
        reason: str = ""
    ) -> DialogueContext:
        """상태 전환 실행"""

        if not StateTransition.can_transition(context.current_state, to_state, context):
            raise ValueError(
                f"Invalid state transition: {context.current_state} -> {to_state}"
            )

        # 이전 상태 저장
        context.previous_state = context.current_state
        context.current_state = to_state
        context.last_activity = datetime.now().isoformat()

        # 상태 전환 이벤트 기록
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": "state_transition",
            "from": context.previous_state.value,
            "to": to_state.value,
            "reason": reason
        })

        return context

    @staticmethod
    def get_expected_intents(state: ConversationState) -> List[str]:
        """현재 상태에서 예상되는 의도들"""

        intent_map = {
            ConversationState.GREETING: ["search", "greeting"],
            ConversationState.SEARCHING: ["search"],
            ConversationState.RESULTS_SHOWN: [
                "filter", "reference", "compare", "compatibility",
                "document", "search", "detail"
            ],
            ConversationState.FILTERING: [
                "filter", "reference", "search"
            ],
            ConversationState.FOCUSED: [
                "compatibility", "document", "detail", "compare", "search"
            ],
            ConversationState.COMPARING: [
                "reference", "detail", "search"
            ],
            ConversationState.COMPATIBILITY_CHECK: [
                "reference", "filter", "search"
            ],
            ConversationState.DOCUMENT_REQUEST: [
                "reference", "search"
            ],
            ConversationState.CLARIFICATION: [
                "search", "filter"
            ],
            ConversationState.IDLE: ["search", "greeting"]
        }

        return intent_map.get(state, ["search"])
