"""
Integrated Router - MCP + Claude + Agent 통합 자동 라우팅

Purpose:
    사용자 질의를 분석하여:
    1. MCP 도구 필요 여부 판단 (Intent Router)
    2. Claude 모델 선택 (Claude Router: Haiku vs Sonnet)
    3. Agent 선택 (어떤 agent 활성화?)
    4. 최적의 조합으로 질의 처리

Workflow:
    User Query
        ↓
    Intent Detection (MCP 필요?)
        ↓
    Complexity Analysis (Haiku vs Sonnet?)
        ↓
    Agent Selection (어떤 agent?)
        ↓
    Combined Execution
        ↓
    Response with Transparency Message
"""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

from .intent_router import MCPRouter, IntentResult, Intent
from .llm_router import ClaudeRouter, ModelSelection, ClaudeModel

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """통합 라우팅 결정"""
    # MCP 관련
    requires_mcp: bool
    mcp_tool: Optional[str]
    mcp_intent: IntentResult

    # Claude 모델 관련
    claude_model: ClaudeModel
    model_name: str
    model_selection: ModelSelection

    # Agent 관련
    recommended_agents: List[str]

    # 실행 전략
    execution_strategy: str  # "mcp_only", "claude_only", "mcp_then_claude"
    cost_type: str  # "deposit" or "max"


class IntegratedRouter:
    """MCP + Claude + Agent 통합 라우터"""

    def __init__(self):
        self.mcp_router = MCPRouter()
        self.claude_router = ClaudeRouter()

        # Agent 매핑 (복잡도/작업 유형별)
        self.agent_mapping = {
            "simple": [],  # Agent 불필요
            "backend": ["backend-architect"],
            "system": ["system-architect"],
            "performance": ["performance-engineer"],
            "security": ["security-engineer"],
            "ai": ["ai-integrator"],
            "research": ["deep-research-agent"],
            "python": ["python-expert"]
        }

    def route(self, query: str, context: Dict = None) -> RoutingDecision:
        """
        질의를 분석하여 최적의 실행 전략 결정

        Args:
            query: 사용자 질의
            context: 추가 컨텍스트 (파일 개수, 에러 여부 등)

        Returns:
            RoutingDecision: 통합 라우팅 결정
        """
        if context is None:
            context = {}

        # 1. MCP Intent Detection
        mcp_tool, mcp_intent = self.mcp_router.route(query)
        requires_mcp = mcp_intent.intent != Intent.UNKNOWN

        # 2. Claude Model Selection
        model_selection = self.claude_router.route(query, context)

        # 3. Agent Selection
        recommended_agents = self._select_agents(query, model_selection)

        # 4. Execution Strategy 결정
        execution_strategy = self._decide_execution_strategy(
            requires_mcp, mcp_intent.intent, model_selection
        )

        return RoutingDecision(
            requires_mcp=requires_mcp,
            mcp_tool=mcp_tool if requires_mcp else None,
            mcp_intent=mcp_intent,
            claude_model=model_selection.model,
            model_name=model_selection.model.value,
            model_selection=model_selection,
            recommended_agents=recommended_agents,
            execution_strategy=execution_strategy,
            cost_type=model_selection.cost_type
        )

    def _select_agents(self, query: str, model_selection: ModelSelection) -> List[str]:
        """
        질의 내용 기반 Agent 선택

        Args:
            query: 사용자 질의
            model_selection: 모델 선택 결과

        Returns:
            List[str]: 추천 Agent 목록
        """
        query_lower = query.lower()
        agents = []

        # 복잡도가 낮으면 Agent 불필요
        if model_selection.complexity_score.total <= 30:
            return []

        # 키워드 기반 Agent 매핑
        if any(kw in query_lower for kw in ["backend", "api", "fastapi", "라우터", "router"]):
            agents.extend(self.agent_mapping["backend"])

        if any(kw in query_lower for kw in ["시스템", "아키텍처", "architecture", "system", "설계"]):
            agents.extend(self.agent_mapping["system"])

        if any(kw in query_lower for kw in ["성능", "performance", "최적화", "optimize"]):
            agents.extend(self.agent_mapping["performance"])

        if any(kw in query_lower for kw in ["보안", "security", "인증", "auth"]):
            agents.extend(self.agent_mapping["security"])

        if any(kw in query_lower for kw in ["ai", "llm", "rag", "임베딩", "embedding"]):
            agents.extend(self.agent_mapping["ai"])

        if any(kw in query_lower for kw in ["검색", "조사", "research", "찾아"]):
            agents.extend(self.agent_mapping["research"])

        if any(kw in query_lower for kw in ["python", "파이썬"]):
            agents.extend(self.agent_mapping["python"])

        # 중복 제거
        return list(set(agents))

    def _decide_execution_strategy(
        self, requires_mcp: bool, mcp_intent: Intent, model_selection: ModelSelection
    ) -> str:
        """
        실행 전략 결정

        Strategies:
            - "mcp_only": MCP 도구만 실행
            - "claude_only": Claude만 실행
            - "mcp_then_claude": MCP 결과를 Claude에 전달
        """
        # MCP 불필요 → Claude만 사용
        if not requires_mcp:
            return "claude_only"

        # FILE_OPERATION이지만 단순 목록 조회 → MCP만
        if mcp_intent == Intent.FILE_OPERATION and model_selection.complexity_score.total <= 30:
            return "mcp_only"

        # VECTOR_SEARCH → MCP 검색 후 Claude로 정리
        if mcp_intent == Intent.VECTOR_SEARCH:
            return "mcp_then_claude"

        # 기본값: MCP 결과를 Claude에 전달
        return "mcp_then_claude"

    def explain_decision(self, decision: RoutingDecision) -> str:
        """
        라우팅 결정 설명 생성 (UI 투명성 메시지)

        Args:
            decision: 라우팅 결정

        Returns:
            str: 사용자에게 보여줄 투명성 메시지
        """
        lines = []

        # 헤더
        lines.append("=" * 70)
        lines.append("🎯 자동 라우팅 분석 결과")
        lines.append("=" * 70)

        # Claude 모델
        if decision.claude_model == ClaudeModel.HAIKU_4_5:
            lines.append("💡 [Claude Haiku 4.5] 일반 작업 (API deposit 사용)")
        else:
            lines.append("🧠 [Claude Sonnet 4.5] 복잡한 작업/검증/시스템 (Max 무제한)")

        lines.append(f"   사유: {decision.model_selection.reason}")

        # MCP 도구
        if decision.requires_mcp:
            lines.append(f"\n📂 [MCP Tool] {decision.mcp_tool}")
            lines.append(f"   의도: {decision.mcp_intent.intent.value}")
            lines.append(f"   신뢰도: {decision.mcp_intent.confidence:.2f}")

        # Agent
        if decision.recommended_agents:
            agent_list = ", ".join(decision.recommended_agents)
            lines.append(f"\n🤖 [Agent] {agent_list}")
        else:
            lines.append("\n🤖 [Agent] 불필요 (단순 작업)")

        # 실행 전략
        strategy_emoji = {
            "mcp_only": "📂",
            "claude_only": "💬",
            "mcp_then_claude": "📂 → 💬"
        }
        emoji = strategy_emoji.get(decision.execution_strategy, "⚙️")
        lines.append(f"\n{emoji} [실행 전략] {decision.execution_strategy}")

        # 복잡도 점수
        complexity = decision.model_selection.complexity_score
        lines.append(f"\n📊 [복잡도] {complexity.total}/100")
        lines.append(f"   - 길이: {complexity.length_score}/20")
        lines.append(f"   - 기술: {complexity.technical_score}/25")
        lines.append(f"   - 범위: {complexity.scope_score}/20")
        lines.append(f"   - 추론: {complexity.reasoning_score}/20")
        lines.append(f"   - 생성: {complexity.creativity_score}/15")

        # 비용
        cost_emoji = "💰" if decision.cost_type == "deposit" else "🎯"
        lines.append(f"\n{cost_emoji} [비용] {decision.cost_type.upper()}")

        lines.append("=" * 70)

        return "\n".join(lines)


# 전역 통합 라우터 인스턴스
integrated_router = IntegratedRouter()


if __name__ == "__main__":
    # 테스트
    test_queries = [
        ("Python 리스트 만드는 법?", {}),
        ("vault 폴더에 있는 파일들 개수는?", {}),
        ("FastAPI 인증 라우터 3개 만들어줘", {}),
        ("RAG 시스템 설계 문서 검색해줘", {}),
        ("전체 시스템 성능 최적화 및 검증", {"file_count": 30})
    ]

    router = IntegratedRouter()

    for query, context in test_queries:
        decision = router.route(query, context)
        explanation = router.explain_decision(decision)

        logger.info(f"\n질의: {query}")
        logger.info(explanation)
