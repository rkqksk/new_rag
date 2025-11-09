#!/usr/bin/env python3
"""
Haiku MCP 사용량 테스트 - 짧은 단문 생성
API 사용량 체크용
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.claude_haiku_server import ClaudeHaikuServer


async def test_short_responses():
    """짧은 단문 생성 테스트"""
    print("=" * 60)
    print("Haiku MCP 사용량 테스트 - 짧은 단문 생성")
    print("=" * 60)

    server = ClaudeHaikuServer()

    # 짧은 질문 5개
    test_prompts = [
        "Python이란?",
        "머신러닝을 한 문장으로 설명해줘",
        "REST API란 무엇인가?",
        "Docker를 간단히 설명해줘",
        "Git이란?",
    ]

    total_tokens = 0
    results = []

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[질문 {i}] {prompt}")

        result = await server.call_haiku(
            prompt=prompt, max_tokens=100, temperature=0.3, use_cache=False  # 짧게 제한
        )

        tokens_used = result.get("tokens", {}).get("total", 0)
        response_text = result.get("text", "N/A")

        print(f"✓ 응답: {response_text}")
        print(f"✓ 토큰: {tokens_used}")

        total_tokens += tokens_used
        results.append({"question": prompt, "response": response_text, "tokens": tokens_used})

    # 최종 통계
    print("\n" + "=" * 60)
    print("사용량 통계")
    print("=" * 60)
    print(f"총 질문 수: {len(test_prompts)}")
    print(f"총 토큰 사용: {total_tokens}")
    print(f"평균 토큰/질문: {total_tokens / len(test_prompts):.1f}")

    # API 키 사용량 (서버 내부 추적)
    usage_stats = server.api_router.get_usage_stats()
    print(f"\nAPI 키 사용량 추적:")
    for key, stats in usage_stats.get("key_usage", {}).items():
        print(f"  키: ...{key[-10:]}")
        print(f"  총 요청: {stats['request_count']}")
        print(f"  성공: {stats['success_count']}")
        print(f"  토큰: {stats['total_tokens']}")

    print("\n✅ 테스트 완료! Anthropic Console에서 사용량을 확인하세요.")
    print("https://console.anthropic.com/settings/usage")


if __name__ == "__main__":
    asyncio.run(test_short_responses())
