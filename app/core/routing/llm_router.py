"""
LLM Router - Claude Haiku 4.5 vs Sonnet 4.5 자동 선택

Purpose:
    질문의 복잡도를 분석하여 최적의 Claude 모델 선택
    - Haiku 4.5: 일반 작업 (API deposit 차감)
    - Sonnet 4.5: 복잡한 작업/검증/시스템 구축 (Max 무제한)

Strategy:
    간단/중간 작업 → Haiku 4.5 (deposit 절약)
    복잡/시스템 작업 → Sonnet 4.5 (Max 무제한 활용)
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict

logger = logging.getLogger(__name__)


class ClaudeModel(Enum):
    """Claude 모델 분류"""

    HAIKU_4_5 = "claude-haiku-4-5"  # 일반 작업 (deposit)
    SONNET_4_5 = "claude-sonnet-4-5"  # 복잡/검증/시스템 (Max)


@dataclass
class ComplexityScore:
    """복잡도 점수"""

    length_score: int  # 0-20
    technical_score: int  # 0-25
    scope_score: int  # 0-20
    reasoning_score: int  # 0-20
    creativity_score: int  # 0-15
    total: int  # 0-100


@dataclass
class ModelSelection:
    """모델 선택 결과"""

    model: ClaudeModel
    complexity_score: ComplexityScore
    reason: str
    cost_type: str  # "deposit" or "max"


class ComplexityAnalyzer:
    """질의 복잡도 분석기"""

    def __init__(self):
        self.complexity_keywords = {
            "simple": ["what is", "무엇", "간단히", "짧게", "요약", "뭐야"],
            "moderate": ["how to", "어떻게", "만들어", "작성", "구현", "추가"],
            "complex": ["분석", "설계", "아키텍처", "최적화", "리팩토링", "전체", "검증"],
            "advanced": ["시스템", "전략", "마이그레이션", "성능", "보안", "대규모"],
        }

        self.scope_keywords = {
            "single": ["this file", "이 함수", "이 변수", "하나만", "단일"],
            "multiple": ["여러", "multiple", "all", "몇 개", "3개", "5개"],
            "project": ["프로젝트", "project", "system", "시스템", "전체", "모든"],
        }

        self.reasoning_keywords = {
            "shallow": ["is", "인가", "뭐야", "show", "보여"],
            "moderate": ["explain", "설명", "왜", "how", "어떻게"],
            "deep": ["분석", "analyze", "debug", "왜 안되는지", "원인"],
            "strategic": ["설계", "design", "strategy", "plan", "접근법", "아키텍처"],
        }

    def analyze(self, query: str) -> ComplexityScore:
        """
        질의 복잡도 분석

        Args:
            query: 사용자 질의

        Returns:
            ComplexityScore: 복잡도 점수
        """
        query_lower = query.lower()

        length_score = self._score_length(query)
        technical_score = self._score_technical_complexity(query_lower)
        scope_score = self._score_scope(query_lower)
        reasoning_score = self._score_reasoning_depth(query_lower)
        creativity_score = self._score_creativity(query_lower)

        total = sum([length_score, technical_score, scope_score, reasoning_score, creativity_score])

        return ComplexityScore(
            length_score=length_score,
            technical_score=technical_score,
            scope_score=scope_score,
            reasoning_score=reasoning_score,
            creativity_score=creativity_score,
            total=min(total, 100),
        )

    def _score_length(self, query: str) -> int:
        """질의 길이 점수 (0-20)"""
        word_count = len(query.split())

        if word_count <= 10:
            return 5  # 단순 질문
        elif word_count <= 30:
            return 10  # 중간 질문
        elif word_count <= 100:
            return 15  # 복잡한 질문
        else:
            return 20  # 매우 복잡한 질문

    def _score_technical_complexity(self, query: str) -> int:
        """기술적 복잡도 점수 (0-25)"""
        if any(kw in query for kw in self.complexity_keywords["advanced"]):
            return 25
        elif any(kw in query for kw in self.complexity_keywords["complex"]):
            return 18
        elif any(kw in query for kw in self.complexity_keywords["moderate"]):
            return 10
        else:
            return 5

    def _score_scope(self, query: str) -> int:
        """작업 범위 점수 (0-20)"""
        if any(kw in query for kw in self.scope_keywords["project"]):
            return 20  # 프로젝트 전체
        elif any(kw in query for kw in self.scope_keywords["multiple"]):
            return 12  # 여러 파일/모듈
        else:
            return 5  # 단일 파일/함수

    def _score_reasoning_depth(self, query: str) -> int:
        """추론 깊이 점수 (0-20)"""
        if any(kw in query for kw in self.reasoning_keywords["strategic"]):
            return 20
        elif any(kw in query for kw in self.reasoning_keywords["deep"]):
            return 15
        elif any(kw in query for kw in self.reasoning_keywords["moderate"]):
            return 10
        else:
            return 5

    def _score_creativity(self, query: str) -> int:
        """창의성/생성 요구 점수 (0-15)"""
        creative_keywords = ["create", "generate", "만들어", "작성", "디자인", "구축"]

        if any(kw in query for kw in creative_keywords):
            if "simple" in query or "간단" in query:
                return 5
            else:
                return 12
        return 0


class ClaudeRouter:
    """Claude 모델 자동 선택 라우터"""

    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()

        # Haiku vs Sonnet 임계값 (0-100)
        self.haiku_threshold = 50  # 50점 이하 → Haiku
        self.sonnet_threshold = 51  # 51점 이상 → Sonnet

    def route(self, query: str, context: Dict = None) -> ModelSelection:
        """
        질의를 분석하여 Claude Haiku 4.5 vs Sonnet 4.5 선택

        Args:
            query: 사용자 질의
            context: 추가 컨텍스트 (파일 개수, 에러 여부 등)

        Returns:
            ModelSelection: 선택된 모델 정보
        """
        if context is None:
            context = {}

        # 1. 복잡도 분석
        complexity_score = self.complexity_analyzer.analyze(query)

        # 2. Sonnet 필수 상황 감지 (시스템/검증/대규모 작업)
        if self._requires_sonnet(query, context):
            return ModelSelection(
                model=ClaudeModel.SONNET_4_5,
                complexity_score=complexity_score,
                reason="시스템 구축/검증/대규모 작업 - Sonnet 필수",
                cost_type="max",
            )

        # 3. 점수 기반 모델 선택
        if complexity_score.total <= self.haiku_threshold:
            # 간단/중간 작업 → Haiku (deposit 절약)
            return ModelSelection(
                model=ClaudeModel.HAIKU_4_5,
                complexity_score=complexity_score,
                reason=f"일반 작업 (복잡도: {complexity_score.total}/100)",
                cost_type="deposit",
            )
        else:
            # 복잡한 작업 → Sonnet (Max 무제한)
            return ModelSelection(
                model=ClaudeModel.SONNET_4_5,
                complexity_score=complexity_score,
                reason=f"복잡한 작업 (복잡도: {complexity_score.total}/100)",
                cost_type="max",
            )

    def _requires_sonnet(self, query: str, context: Dict) -> bool:
        """
        Sonnet 필수 상황 감지

        Examples:
            - "전체 시스템 아키텍처 설계"
            - "10개 파일 리팩토링"
            - "성능 최적화 검증"
        """
        query_lower = query.lower()

        # Multi-file operations (10+ 파일)
        if context.get("file_count", 0) >= 10:
            return True

        # 검증 키워드
        verification_keywords = ["검증", "verify", "validation", "확인", "테스트"]
        if any(kw in query_lower for kw in verification_keywords):
            return True

        # Architecture/System keywords
        system_keywords = [
            "아키텍처",
            "architecture",
            "설계",
            "design system",
            "전체 시스템",
            "entire system",
            "마이그레이션",
            "migration",
        ]
        if any(kw in query_lower for kw in system_keywords):
            return True

        # Performance optimization
        if "성능" in query_lower or "performance" in query_lower:
            if "최적화" in query_lower or "optimize" in query_lower:
                return True

        # Large-scale refactoring
        large_scale_keywords = ["대규모", "전체", "리팩토링", "refactor all", "모든"]
        if any(kw in query_lower for kw in large_scale_keywords):
            return True

        return False


# 전역 라우터 인스턴스
claude_router = ClaudeRouter()


if __name__ == "__main__":
    # 테스트
    test_queries = [
        ("Python 리스트 만드는 법?", {}),
        ("FastAPI 인증 라우터 1개 만들어줘", {}),
        ("FastAPI 라우터 3개 만들어줘 - 인증, 사용자, 문서", {}),
        ("전체 RAG 시스템 아키텍처 설계 및 검증", {}),
        ("50개 파일 리팩토링", {"file_count": 50}),
        ("성능 최적화 검증해줘", {}),
    ]

    router = ClaudeRouter()

    logger.info("=" * 70)
    logger.info("Claude Model Router Test - Haiku 4.5 vs Sonnet 4.5")
    logger.info("=" * 70)

    for query, context in test_queries:
        result = router.route(query, context)

        cost_emoji = "💰" if result.cost_type == "deposit" else "🎯"
        model_emoji = "💡" if result.model == ClaudeModel.HAIKU_4_5 else "🧠"

        logger.info(f"\n질의: {query}")
        logger.info(f"{model_emoji} {result.model.value}")
        logger.info(f"{cost_emoji} Cost: {result.cost_type.upper()}")
        logger.info(f"📊 복잡도: {result.complexity_score.total}/100")
        logger.info(f"💬 사유: {result.reason}")
