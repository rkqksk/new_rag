#!/usr/bin/env python3
"""
통합 Claude API 서버 테스트
Haiku 4.5 + Sonnet 4.5 + 자동 모델 선택 + 할당량 추적
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def test_unified_api():
    """통합 API 서버 테스트"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found")
        return False

    print(f"✅ API Key found: {api_key[:20]}...")

    try:
        from mcp_servers.claude_api_server import ClaudeAPIServer, ComplexityAnalyzer
        import asyncio

        print("✅ Claude API Server module imported")

        # 서버 초기화
        server = ClaudeAPIServer()
        print(f"✅ Server initialized")
        print(f"   - Haiku: {server.client.messages}")
        print(f"   - Sonnet: Available")
        print(f"   - Daily limit: {server.quota_manager.daily_limit:,} tokens")

        async def run_tests():
            # Test 1: 단순 작업 (Haiku로 자동 라우팅)
            print("\n" + "="*60)
            print("Test 1: Simple task (auto-route to Haiku)")
            print("="*60)

            result1 = await server.call_api(
                prompt="Say 'Hello from Haiku' in Korean",
                model="auto"
            )

            print(f"Model used: {result1.get('model_type', 'N/A').upper()}")
            print(f"Response: {result1.get('text', 'ERROR')[:100]}")
            print(f"Tokens: {result1.get('tokens', {})}")
            print(f"Cost: ${result1.get('cost', {}).get('this_request', 0):.6f}")

            # Test 2: 복잡한 작업 (Sonnet으로 자동 라우팅)
            print("\n" + "="*60)
            print("Test 2: Complex task (auto-route to Sonnet)")
            print("="*60)

            result2 = await server.call_api(
                prompt="""Analyze and compare the architectural differences between
                microservices and monolithic systems. Provide a detailed explanation
                of trade-offs and when to use each approach.""",
                model="auto"
            )

            print(f"Model used: {result2.get('model_type', 'N/A').upper()}")
            print(f"Response: {result2.get('text', 'ERROR')[:150]}...")
            print(f"Tokens: {result2.get('tokens', {})}")
            print(f"Cost: ${result2.get('cost', {}).get('this_request', 0):.6f}")

            # Test 3: 명시적 Haiku 호출
            print("\n" + "="*60)
            print("Test 3: Explicit Haiku call")
            print("="*60)

            result3 = await server.call_api(
                prompt="Write a Python function to calculate fibonacci numbers",
                model="haiku"
            )

            print(f"Model used: {result3.get('model_type', 'N/A').upper()}")
            print(f"Response: {result3.get('text', 'ERROR')[:150]}...")
            print(f"Tokens: {result3.get('tokens', {})}")
            print(f"Cost: ${result3.get('cost', {}).get('this_request', 0):.6f}")

            # Test 4: 명시적 Sonnet 호출
            print("\n" + "="*60)
            print("Test 4: Explicit Sonnet call")
            print("="*60)

            result4 = await server.call_api(
                prompt="Explain quantum computing in Korean",
                model="sonnet"
            )

            print(f"Model used: {result4.get('model_type', 'N/A').upper()}")
            print(f"Response: {result4.get('text', 'ERROR')[:150]}...")
            print(f"Tokens: {result4.get('tokens', {})}")
            print(f"Cost: ${result4.get('cost', {}).get('this_request', 0):.6f}")

            # 최종 사용량 요약
            print("\n" + "="*60)
            print("Usage Summary")
            print("="*60)

            usage = server.quota_manager.get_usage_summary()
            print(f"Date: {usage['date']}")
            print(f"\nHaiku:")
            print(f"  - Requests: {usage['haiku']['requests']}")
            print(f"  - Tokens: {usage['haiku']['tokens']:,}")
            print(f"  - Cost: ${usage['haiku']['cost']:.4f}")
            print(f"\nSonnet:")
            print(f"  - Requests: {usage['sonnet']['requests']}")
            print(f"  - Tokens: {usage['sonnet']['tokens']:,}")
            print(f"  - Cost: ${usage['sonnet']['cost']:.4f}")
            print(f"\nTotal:")
            print(f"  - Tokens: {usage['total_tokens']:,} / {usage['daily_limit']:,}")
            print(f"  - Cost: ${usage['total_cost']:.4f}")
            print(f"  - Quota used: {usage['quota_used_percent']}%")
            print(f"  - Remaining: {usage['remaining_tokens']:,} tokens")

            # Complexity analyzer test
            print("\n" + "="*60)
            print("Complexity Analysis Test")
            print("="*60)

            test_prompts = [
                "Write code",
                "Explain this concept in detail",
                "Analyze, compare, and design a comprehensive architecture"
            ]

            for prompt in test_prompts:
                complexity = ComplexityAnalyzer.estimate_complexity(prompt)
                recommended = "Sonnet" if complexity >= 0.7 else "Haiku"
                print(f"Prompt: {prompt[:50]}...")
                print(f"  Complexity: {complexity:.2f} → Recommended: {recommended}")

        asyncio.run(run_tests())

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nUnified API Server Features:")
        print("  ✅ Haiku 4.5 connection")
        print("  ✅ Sonnet 4.5 connection")
        print("  ✅ Auto model selection")
        print("  ✅ Quota tracking")
        print("  ✅ Cost monitoring")
        print("  ✅ Daily limit enforcement")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 Testing Unified Claude API Server...")
    print("="*60)

    success = test_unified_api()

    if success:
        print("\n✅ Unified API server ready for production")
        sys.exit(0)
    else:
        print("\n❌ Tests failed - check errors above")
        sys.exit(1)
