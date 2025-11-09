"""
Conversation State Machine for Context-Aware Product Search
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ConversationState(str, Enum):
    """Conversation states for the state machine"""

    IDLE = "idle"  # 초기 상태, 대화 시작
    SEARCHING = "searching"  # 검색 실행 중
    BROWSING = "browsing"  # 검색 결과 탐색 중
    FILTERING = "filtering"  # 결과 필터링 중
    COMPARING = "comparing"  # 제품 비교 중
    DETAILED = "detailed"  # 특정 제품 상세 조회
    CHECKOUT = "checkout"  # 견적/주문 준비


class IntentType(str, Enum):
    """User intent types detected by LLM"""

    NEW_SEARCH = "new_search"  # 새로운 검색 시작
    FILTER_PREVIOUS = "filter_previous"  # 이전 결과 필터링
    REFINE_SEARCH = "refine_search"  # 검색 조건 수정
    COMPARE_PRODUCTS = "compare_products"  # 제품 비교
    VIEW_DETAILS = "view_details"  # 상세 정보 조회
    REQUEST_QUOTE = "request_quote"  # 견적 요청
    ASK_QUESTION = "ask_question"  # 일반 질문
    RESET_CONTEXT = "reset_context"  # 맥락 초기화
    RECOMMEND_ACCESSORY = "recommend_accessory"  # 호환 가능한 펌프/캡 추천


class SearchCriteria(BaseModel):
    """Extracted search criteria from user query"""

    capacity: Optional[float] = None  # 용량 (ml)
    capacity_unit: Optional[str] = None  # ml, g
    material: Optional[str] = None  # PET, PETG, PE, PP
    product_code: Optional[str] = None  # 제품 코드
    product_type: Optional[str] = None  # BOTTLE, JAR, CAP, PUMP
    neck_size: Optional[str] = None  # 네크사이즈 (예: 20파이, 24파이, Ø20, Ø24)
    dosage: Optional[float] = None  # 펌프 토출량 (cc)
    moq: Optional[str] = None  # MOQ
    price_range: Optional[Dict[str, float]] = None  # 가격 범위
    has_coating: Optional[bool] = None  # 코팅 가능 여부
    keywords: List[str] = []  # 추가 키워드


class ConversationContext(BaseModel):
    """Current conversation context"""

    session_id: str
    user_id: Optional[str] = None
    state: ConversationState = ConversationState.IDLE

    # 대화 히스토리
    queries: List[str] = []  # 쿼리 기록
    intents: List[IntentType] = []  # 의도 기록

    # 현재 검색 컨텍스트
    current_query: Optional[str] = None
    current_criteria: Optional[SearchCriteria] = None
    current_results: List[Dict[str, Any]] = []

    # 이전 검색 컨텍스트 (for filtering)
    previous_query: Optional[str] = None
    previous_results: List[Dict[str, Any]] = []

    # 선택된 제품들 (비교용)
    selected_products: List[str] = []

    # 메타데이터
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    turn_count: int = 0

    class Config:
        arbitrary_types_allowed = True


class StateTransition(BaseModel):
    """State transition definition"""

    from_state: ConversationState
    to_state: ConversationState
    trigger_intent: IntentType
    condition: Optional[str] = None  # 추가 조건


# 상태 전이 규칙
STATE_TRANSITIONS: List[StateTransition] = [
    # IDLE → SEARCHING
    StateTransition(
        from_state=ConversationState.IDLE,
        to_state=ConversationState.SEARCHING,
        trigger_intent=IntentType.NEW_SEARCH,
    ),
    # SEARCHING → BROWSING
    StateTransition(
        from_state=ConversationState.SEARCHING,
        to_state=ConversationState.BROWSING,
        trigger_intent=IntentType.NEW_SEARCH,
        condition="results_found",
    ),
    # BROWSING → FILTERING
    StateTransition(
        from_state=ConversationState.BROWSING,
        to_state=ConversationState.FILTERING,
        trigger_intent=IntentType.FILTER_PREVIOUS,
    ),
    # FILTERING → BROWSING
    StateTransition(
        from_state=ConversationState.FILTERING,
        to_state=ConversationState.BROWSING,
        trigger_intent=IntentType.FILTER_PREVIOUS,
        condition="filter_applied",
    ),
    # BROWSING → COMPARING
    StateTransition(
        from_state=ConversationState.BROWSING,
        to_state=ConversationState.COMPARING,
        trigger_intent=IntentType.COMPARE_PRODUCTS,
    ),
    # BROWSING → DETAILED
    StateTransition(
        from_state=ConversationState.BROWSING,
        to_state=ConversationState.DETAILED,
        trigger_intent=IntentType.VIEW_DETAILS,
    ),
    # DETAILED → CHECKOUT
    StateTransition(
        from_state=ConversationState.DETAILED,
        to_state=ConversationState.CHECKOUT,
        trigger_intent=IntentType.REQUEST_QUOTE,
    ),
    # Any state → IDLE (reset)
    StateTransition(
        from_state=ConversationState.BROWSING,
        to_state=ConversationState.IDLE,
        trigger_intent=IntentType.RESET_CONTEXT,
    ),
    StateTransition(
        from_state=ConversationState.FILTERING,
        to_state=ConversationState.IDLE,
        trigger_intent=IntentType.RESET_CONTEXT,
    ),
    StateTransition(
        from_state=ConversationState.COMPARING,
        to_state=ConversationState.IDLE,
        trigger_intent=IntentType.RESET_CONTEXT,
    ),
    # BROWSING/COMPARING → NEW_SEARCH
    StateTransition(
        from_state=ConversationState.BROWSING,
        to_state=ConversationState.SEARCHING,
        trigger_intent=IntentType.NEW_SEARCH,
    ),
    StateTransition(
        from_state=ConversationState.COMPARING,
        to_state=ConversationState.SEARCHING,
        trigger_intent=IntentType.NEW_SEARCH,
    ),
    # BROWSING/FILTERING → BROWSING (accessory recommendation)
    StateTransition(
        from_state=ConversationState.BROWSING,
        to_state=ConversationState.BROWSING,
        trigger_intent=IntentType.RECOMMEND_ACCESSORY,
    ),
    StateTransition(
        from_state=ConversationState.FILTERING,
        to_state=ConversationState.BROWSING,
        trigger_intent=IntentType.RECOMMEND_ACCESSORY,
    ),
]


def get_next_state(
    current_state: ConversationState, intent: IntentType, condition: Optional[str] = None
) -> Optional[ConversationState]:
    """Get next state based on current state and intent

    Args:
        current_state: Current conversation state
        intent: Detected user intent
        condition: Optional condition for transition

    Returns:
        Next state or None if no valid transition
    """
    for transition in STATE_TRANSITIONS:
        if transition.from_state == current_state and transition.trigger_intent == intent:

            # Check condition if specified
            if transition.condition:
                if transition.condition == condition:
                    return transition.to_state
            else:
                return transition.to_state

    # No valid transition found
    return None
