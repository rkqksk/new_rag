#!/usr/bin/env python3
"""
Query Router - 질문 난이도 기반 자동 라우팅
Haiku 4.5 (빠른 처리) vs Sonnet 4.5 (정교한 처리) 자동 선택
Teacher-Student 구조로 토큰 효율화
"""

import asyncio
import json
import sys
import os
import logging
from typing import Any, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

import anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """질문 난이도"""
    SIMPLE = "simple"  # Haiku 처리
    MODERATE = "moderate"  # Haiku → Sonnet 검증
    COMPLEX = "complex"  # Sonnet 처리


class QueryAnalyzer:
    """질문 난이도 분석"""

    SIMPLE_KEYWORDS = {
        "what", "how", "when", "where", "which",
        "simple", "basic", "explain", "tell me",
        "list", "brief", "quick", "summary"
    }

    COMPLEX_KEYWORDS = {
        "design", "architect", "refactor", "optimize",
        "implement", "build", "create", "algorithm",
        "strategy", "security", "performance", "scalability",
        "trade-off", "analysis", "system", "infrastructure"
    }

    SIMPLE_PATTERNS = [
        r"^\d+\s*\+\s*\d+",  # 단순 계산
        r"^what is",  # 간단한 정의
        r"^how do i",  # 기본 사용법
        r"^list all",  # 단순 나열
    ]

    COMPLEX_PATTERNS = [
        r"refactor.*architecture",  # 아키텍처 리팩토링
        r"design.*system",  # 시스템 설계
        r"optimize.*performance",  # 성능 최적화
        r"implement.*algorithm",  # 알고리즘 구현
        r"security.*vulnerability",  # 보안 분석
    ]

    @staticmethod
    def analyze(query: str) -> Tuple[QueryComplexity, float]:
        """
        질문 난이도 분석

        Returns:
            (난이도, 신뢰도 0-1)
        """
        import re
        
        query_lower = query.lower()
        
        # 패턴 매칭 (높은 신뢰도)
        for pattern in QueryAnalyzer.COMPLEX_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.COMPLEX, 0.9
        
        for pattern in QueryAnalyzer.SIMPLE_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.SIMPLE, 0.9
        
        # 키워드 기반 분석
        complex_score = sum(1 for kw in QueryAnalyzer.COMPLEX_KEYWORDS if kw in query_lower)
        simple_score = sum(1 for kw in QueryAnalyzer.SIMPLE_KEYWORDS if kw in query_lower)

        # 길이 기반 분석 (길수록 복잡할 가능성)
        length_factor = min(len(query) / 500, 1.0)
        query_length = len(query)

        # 키워드 스코어 우선 판단
        if complex_score > 2:
            return QueryComplexity.COMPLEX, 0.7 + (complex_score * 0.05)
        elif simple_score > 2:
            return QueryComplexity.SIMPLE, 0.7 + (simple_score * 0.05)

        # 키워드가 명확하지 않으면 길이로 판단 (Moderate 제거)
        # 150자 기준: 짧으면 Simple(Haiku), 길면 Complex(Sonnet)
        elif query_length < 150:
            return QueryComplexity.SIMPLE, 0.55  # 비용 우선
        else:
            return QueryComplexity.COMPLEX, 0.55  # 품질 우선


class TeacherStudentOrchestrator:
    """Teacher(Sonnet) - Student(Haiku) 오케스트레이션"""

    def __init__(self):
        """초기화"""
        self.haiku_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.sonnet_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        self.haiku_model = "claude-haiku-4-5-20251001"
        self.sonnet_model = "claude-3-5-sonnet-20241022"
        
        self.stats = {
            "haiku_calls": 0,
            "sonnet_calls": 0,
            "haiku_tokens": 0,
            "sonnet_tokens": 0,
            "teacher_reviews": 0,
            "corrections": 0
        }

    async def route_and_process(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        질문 분석 후 자동 라우팅 및 처리

        Returns:
            {
                "query": 원본 질문,
                "complexity": 난이도,
                "response": 최종 응답,
                "model_used": 사용된 모델,
                "review_passed": 검증 통과 여부,
                "tokens": 토큰 사용량,
                "thinking": 처리 과정
            }
        """
        # 1. 질문 난이도 분석
        complexity, confidence = QueryAnalyzer.analyze(query)
        logger.info(f"🔍 Query complexity: {complexity.value} (confidence: {confidence:.2f})")

        thinking = [f"Query analysis: {complexity.value} (confidence: {confidence:.2f})"]

        # 2. 경로 선택
        if complexity == QueryComplexity.SIMPLE:
            # Haiku 직접 처리
            logger.info("→ Routing to Haiku (simple query)")
            thinking.append("Route: Haiku (fast path)")
            
            result = await self._haiku_only(query, system_prompt, max_tokens)
            result["thinking"] = thinking
            return result

        elif complexity == QueryComplexity.MODERATE:
            # Haiku 처리 + Sonnet 검증
            logger.info("→ Routing to Haiku with Sonnet review")
            thinking.append("Route: Haiku (student) → Sonnet (teacher review)")
            
            result = await self._haiku_with_review(query, system_prompt, max_tokens)
            result["thinking"] = thinking
            return result

        else:  # COMPLEX
            # Sonnet 직접 처리
            logger.info("→ Routing to Sonnet (complex query)")
            thinking.append("Route: Sonnet (teacher direct)")
            
            result = await self._sonnet_only(query, system_prompt, max_tokens)
            result["thinking"] = thinking
            return result

    async def _haiku_only(
        self,
        query: str,
        system_prompt: Optional[str],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Haiku 직접 처리"""
        try:
            response = self.haiku_client.messages.create(
                model=self.haiku_model,
                max_tokens=max_tokens,
                system=system_prompt if system_prompt else "You are a helpful AI assistant.",
                messages=[{"role": "user", "content": query}]
            )

            self.stats["haiku_calls"] += 1
            self.stats["haiku_tokens"] += response.usage.input_tokens + response.usage.output_tokens

            return {
                "query": query,
                "complexity": "simple",
                "response": response.content[0].text,
                "model_used": self.haiku_model,
                "review_passed": True,
                "tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Haiku processing error: {e}")
            return {
                "error": str(e),
                "model_used": self.haiku_model,
                "tokens": {"total": 0}
            }

    async def _haiku_with_review(
        self,
        query: str,
        system_prompt: Optional[str],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Haiku 처리 + Sonnet 검증"""
        try:
            # 1. Haiku이 먼저 응답 생성
            haiku_response = self.haiku_client.messages.create(
                model=self.haiku_model,
                max_tokens=max_tokens,
                system=system_prompt if system_prompt else "You are a helpful AI assistant.",
                messages=[{"role": "user", "content": query}]
            )

            haiku_text = haiku_response.content[0].text
            self.stats["haiku_calls"] += 1
            haiku_tokens = haiku_response.usage.input_tokens + haiku_response.usage.output_tokens
            self.stats["haiku_tokens"] += haiku_tokens

            logger.info("✓ Haiku generated response, sending to Sonnet for review...")

            # 2. Sonnet이 품질 검증
            review_response = self.sonnet_client.messages.create(
                model=self.sonnet_model,
                max_tokens=1000,
                system="You are a code/content quality reviewer. Analyze the response and provide brief feedback. Format: VERDICT: PASS/NEEDS_IMPROVEMENT\nFEEDBACK: ...",
                messages=[
                    {"role": "user", "content": f"Original question: {query}\n\nResponse to review:\n{haiku_text}\n\nProvide a brief quality assessment."}
                ]
            )

            review_text = review_response.content[0].text
            self.stats["teacher_reviews"] += 1
            review_tokens = review_response.usage.input_tokens + review_response.usage.output_tokens
            self.stats["sonnet_tokens"] += review_tokens

            # 3. 검증 결과 분석
            verdict = "PASS" in review_text.upper()

            if not verdict:
                logger.warning("⚠️ Sonnet review: needs improvement, regenerating with Sonnet...")
                self.stats["corrections"] += 1

                # Sonnet이 개선된 응답 생성
                improved_response = self.sonnet_client.messages.create(
                    model=self.sonnet_model,
                    max_tokens=max_tokens,
                    system=system_prompt if system_prompt else "You are a helpful AI assistant.",
                    messages=[
                        {"role": "user", "content": f"Improve the following response to: {query}\n\nOriginal response:\n{haiku_text}"}
                    ]
                )

                final_text = improved_response.content[0].text
                improved_tokens = improved_response.usage.input_tokens + improved_response.usage.output_tokens
                self.stats["sonnet_tokens"] += improved_tokens

                return {
                    "query": query,
                    "complexity": "moderate",
                    "response": final_text,
                    "model_used": f"{self.haiku_model} → {self.sonnet_model} (improved)",
                    "review_passed": True,
                    "review_feedback": review_text,
                    "tokens": {
                        "haiku": haiku_tokens,
                        "sonnet_review": review_tokens,
                        "sonnet_improvement": improved_tokens,
                        "total": haiku_tokens + review_tokens + improved_tokens
                    }
                }
            else:
                logger.info("✓ Sonnet review: PASS")
                return {
                    "query": query,
                    "complexity": "moderate",
                    "response": haiku_text,
                    "model_used": f"{self.haiku_model} (validated by {self.sonnet_model})",
                    "review_passed": True,
                    "review_feedback": review_text,
                    "tokens": {
                        "haiku": haiku_tokens,
                        "sonnet_review": review_tokens,
                        "total": haiku_tokens + review_tokens
                    }
                }

        except Exception as e:
            logger.error(f"Haiku-Sonnet orchestration error: {e}")
            return {
                "error": str(e),
                "model_used": f"{self.haiku_model} + {self.sonnet_model}",
                "tokens": {"total": 0}
            }

    async def _sonnet_only(
        self,
        query: str,
        system_prompt: Optional[str],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Sonnet 직접 처리"""
        try:
            response = self.sonnet_client.messages.create(
                model=self.sonnet_model,
                max_tokens=max_tokens,
                system=system_prompt if system_prompt else "You are an expert AI assistant.",
                messages=[{"role": "user", "content": query}]
            )

            self.stats["sonnet_calls"] += 1
            self.stats["sonnet_tokens"] += response.usage.input_tokens + response.usage.output_tokens

            return {
                "query": query,
                "complexity": "complex",
                "response": response.content[0].text,
                "model_used": self.sonnet_model,
                "review_passed": True,
                "tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Sonnet processing error: {e}")
            return {
                "error": str(e),
                "model_used": self.sonnet_model,
                "tokens": {"total": 0}
            }

    def get_stats(self) -> Dict[str, Any]:
        """사용 통계 반환"""
        total_haiku = self.stats["haiku_tokens"]
        total_sonnet = self.stats["sonnet_tokens"]
        total_tokens = total_haiku + total_sonnet

        haiku_percentage = (total_haiku / total_tokens * 100) if total_tokens > 0 else 0
        sonnet_percentage = (total_sonnet / total_tokens * 100) if total_tokens > 0 else 0

        return {
            "summary": {
                "total_calls": self.stats["haiku_calls"] + self.stats["sonnet_calls"],
                "teacher_reviews": self.stats["teacher_reviews"],
                "corrections_made": self.stats["corrections"],
                "efficiency": f"{haiku_percentage:.1f}% Haiku / {sonnet_percentage:.1f}% Sonnet"
            },
            "haiku": {
                "calls": self.stats["haiku_calls"],
                "tokens": total_haiku,
                "percentage": haiku_percentage
            },
            "sonnet": {
                "calls": self.stats["sonnet_calls"],
                "tokens": total_sonnet,
                "percentage": sonnet_percentage
            },
            "optimization": {
                "total_tokens": total_tokens,
                "teacher_reviews": self.stats["teacher_reviews"],
                "corrections": self.stats["corrections"]
            }
        }


async def main():
    """CLI 테스트"""
    orchestrator = TeacherStudentOrchestrator()

    test_queries = [
        ("What is Python?", "simple"),
        ("How do I reverse a list in Python?", "simple"),
        ("Design a caching system with TTL and LRU eviction", "complex"),
        ("Implement a REST API that integrates with PostgreSQL and Redis", "complex"),
        ("Create a function that validates email addresses with regex", "moderate"),
    ]

    logger.info("🚀 Starting Query Router Tests\n")

    for query, expected in test_queries:
        logger.info(f"Query: {query}")
        logger.info(f"Expected complexity: {expected}")

        result = await orchestrator.route_and_process(query)

        logger.info(f"Result complexity: {result.get('complexity', 'N/A')}")
        logger.info(f"Model used: {result.get('model_used', 'N/A')}")
        logger.info(f"Tokens used: {result.get('tokens', {}).get('total', 0)}")
        logger.info(f"Response preview: {result.get('response', 'N/A')[:100]}...\n")

    # 최종 통계
    logger.info("📊 Final Statistics:")
    logger.info(json.dumps(orchestrator.get_stats(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
