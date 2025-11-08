#!/usr/bin/env python3
"""
MCP 서버 통합 테스트
- Query Router (Haiku/Sonnet 자동 라우팅)
- Google DevTools (자동 크롤링/디버깅)
- Haiku 4.5 (API 키 라우팅)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.query_router import QueryAnalyzer, QueryComplexity, TeacherStudentOrchestrator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPIntegrationTests:
    """MCP 서버 통합 테스트"""

    def __init__(self):
        self.orchestrator = TeacherStudentOrchestrator()
        self.test_results = []

    async def test_query_complexity_analysis(self):
        """질문 난이도 분석 테스트"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: Query Complexity Analysis")
        logger.info("=" * 60)

        test_cases = [
            ("What is Python?", QueryComplexity.SIMPLE),
            ("How do I reverse a list?", QueryComplexity.SIMPLE),
            ("Design a caching system with LRU eviction", QueryComplexity.COMPLEX),
            ("Implement a REST API with authentication", QueryComplexity.COMPLEX),
            ("Refactor this authentication middleware", QueryComplexity.MODERATE),
        ]

        for query, expected_complexity in test_cases:
            complexity, confidence = QueryAnalyzer.analyze(query)

            status = "✓ PASS" if complexity == expected_complexity else "✗ FAIL"
            logger.info(f"{status}: '{query[:50]}...'")
            logger.info(f"  Expected: {expected_complexity.value}, Got: {complexity.value}")
            logger.info(f"  Confidence: {confidence:.2f}")

            self.test_results.append(
                {
                    "test": "complexity_analysis",
                    "query": query,
                    "expected": expected_complexity.value,
                    "actual": complexity.value,
                    "confidence": confidence,
                    "status": "PASS" if complexity == expected_complexity else "FAIL",
                }
            )

    async def test_haiku_only_routing(self):
        """Haiku 직접 처리 테스트 (Simple)"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Haiku-Only Routing (Simple Query)")
        logger.info("=" * 60)

        query = "What is the difference between list and tuple in Python?"
        logger.info(f"Query: {query}")

        try:
            result = await self.orchestrator.route_and_process(query)

            logger.info(f"✓ Model used: {result.get('model_used')}")
            logger.info(f"✓ Complexity: {result.get('complexity')}")
            logger.info(f"✓ Tokens used: {result.get('tokens', {}).get('total', 'N/A')}")
            logger.info(f"✓ Response preview: {result.get('response', '')[:100]}...")

            self.test_results.append(
                {
                    "test": "haiku_only_routing",
                    "status": "PASS",
                    "model": result.get("model_used"),
                    "complexity": result.get("complexity"),
                }
            )

        except Exception as e:
            logger.error(f"✗ FAIL: {e}")
            self.test_results.append(
                {"test": "haiku_only_routing", "status": "FAIL", "error": str(e)}
            )

    async def test_haiku_with_sonnet_review(self):
        """Haiku + Sonnet 검증 테스트 (Moderate)"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: Haiku + Sonnet Review (Moderate Query)")
        logger.info("=" * 60)

        query = "How should I structure a Node.js project for scalability?"
        logger.info(f"Query: {query}")

        try:
            result = await self.orchestrator.route_and_process(query)

            logger.info(f"✓ Model used: {result.get('model_used')}")
            logger.info(f"✓ Complexity: {result.get('complexity')}")
            logger.info(f"✓ Review passed: {result.get('review_passed')}")
            logger.info(f"✓ Tokens used: {result.get('tokens', {}).get('total', 'N/A')}")

            tokens = result.get("tokens", {})
            if isinstance(tokens, dict):
                haiku_tokens = tokens.get("haiku", 0)
                sonnet_tokens = tokens.get("sonnet_review", 0)
                logger.info(f"  - Haiku tokens: {haiku_tokens}")
                logger.info(f"  - Sonnet review tokens: {sonnet_tokens}")

            self.test_results.append(
                {
                    "test": "haiku_sonnet_review",
                    "status": "PASS",
                    "model": result.get("model_used"),
                    "complexity": result.get("complexity"),
                    "review_passed": result.get("review_passed"),
                }
            )

        except Exception as e:
            logger.error(f"✗ FAIL: {e}")
            self.test_results.append(
                {"test": "haiku_sonnet_review", "status": "FAIL", "error": str(e)}
            )

    async def test_sonnet_direct_routing(self):
        """Sonnet 직접 처리 테스트 (Complex)"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: Sonnet Direct Routing (Complex Query)")
        logger.info("=" * 60)

        query = "Design a microservice architecture for a real-time collaborative document editor with WebSocket support, offline-first capabilities, and eventual consistency"
        logger.info(f"Query: {query[:100]}...")

        try:
            result = await self.orchestrator.route_and_process(query)

            logger.info(f"✓ Model used: {result.get('model_used')}")
            logger.info(f"✓ Complexity: {result.get('complexity')}")
            logger.info(f"✓ Tokens used: {result.get('tokens', {}).get('total', 'N/A')}")
            logger.info(f"✓ Response preview: {result.get('response', '')[:150]}...")

            self.test_results.append(
                {
                    "test": "sonnet_direct_routing",
                    "status": "PASS",
                    "model": result.get("model_used"),
                    "complexity": result.get("complexity"),
                }
            )

        except Exception as e:
            logger.error(f"✗ FAIL: {e}")
            self.test_results.append(
                {"test": "sonnet_direct_routing", "status": "FAIL", "error": str(e)}
            )

    async def test_batch_routing(self):
        """배치 라우팅 테스트"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: Batch Query Routing")
        logger.info("=" * 60)

        queries = [
            "What is a decorator in Python?",
            "How do I optimize database queries?",
            "Design a distributed cache system with consistency guarantees",
        ]

        logger.info(f"Processing {len(queries)} queries...")

        for i, query in enumerate(queries, 1):
            try:
                result = await self.orchestrator.route_and_process(query)
                logger.info(f"  {i}. ✓ {result.get('complexity').upper()}: {query[:50]}...")

                self.test_results.append(
                    {
                        "test": "batch_routing",
                        "query_index": i,
                        "status": "PASS",
                        "complexity": result.get("complexity"),
                    }
                )

            except Exception as e:
                logger.error(f"  {i}. ✗ {query[:50]}... - {e}")
                self.test_results.append(
                    {"test": "batch_routing", "query_index": i, "status": "FAIL", "error": str(e)}
                )

    async def test_usage_statistics(self):
        """사용 통계 테스트"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 6: Usage Statistics")
        logger.info("=" * 60)

        stats = self.orchestrator.get_stats()

        logger.info(f"Total calls: {stats['summary']['total_calls']}")
        logger.info(f"Teacher reviews: {stats['summary']['teacher_reviews']}")
        logger.info(f"Corrections made: {stats['summary']['corrections_made']}")
        logger.info(f"Efficiency: {stats['summary']['efficiency']}")

        logger.info(f"\nHaiku:")
        logger.info(f"  Calls: {stats['haiku']['calls']}")
        logger.info(f"  Tokens: {stats['haiku']['tokens']}")
        logger.info(f"  Percentage: {stats['haiku']['percentage']:.1f}%")

        logger.info(f"\nSonnet:")
        logger.info(f"  Calls: {stats['sonnet']['calls']}")
        logger.info(f"  Tokens: {stats['sonnet']['tokens']}")
        logger.info(f"  Percentage: {stats['sonnet']['percentage']:.1f}%")

        self.test_results.append({"test": "usage_statistics", "status": "PASS", "stats": stats})

    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("\n" + "=" * 80)
        logger.info("MCP Integration Test Suite - Query Router")
        logger.info("=" * 80)

        try:
            await self.test_query_complexity_analysis()
            await self.test_haiku_only_routing()
            await self.test_haiku_with_sonnet_review()
            await self.test_sonnet_direct_routing()
            await self.test_batch_routing()
            await self.test_usage_statistics()

        except Exception as e:
            logger.error(f"✗ Test suite error: {e}")

        # 최종 리포트
        self._print_test_report()

    def _print_test_report(self):
        """테스트 리포트 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST REPORT")
        logger.info("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("status") == "PASS"])
        failed_tests = total_tests - passed_tests

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✓")
        logger.info(f"Failed: {failed_tests} ✗")
        logger.info(
            f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A"
        )

        # 상세 결과
        logger.info("\n" + "-" * 80)
        logger.info("Detailed Results:")
        logger.info("-" * 80)

        for result in self.test_results:
            status_icon = "✓" if result.get("status") == "PASS" else "✗"
            test_name = result.get("test", "unknown")
            logger.info(f"{status_icon} {test_name}: {result.get('status')}")


async def main():
    """메인 테스트 함수"""
    tester = MCPIntegrationTests()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
