#!/usr/bin/env python3
"""Haiku MCP 서버 테스트 스크립트"""

import asyncio
import json
import sys
import os

# 환경변수 확인
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"✅ API Key loaded: {api_key[:30]}..." if api_key else "❌ API Key NOT FOUND")

# MCP 서버 임포트 테스트
try:
    from mcp_servers.claude_haiku_server import ClaudeHaikuServer
    print("✅ MCP 서버 모듈 임포트 성공")
except Exception as e:
    print(f"❌ MCP 서버 임포트 실패: {e}")
    sys.exit(1)

async def test_haiku_server():
    """Haiku 서버 기능 테스트"""
    try:
        # 서버 초기화
        server = ClaudeHaikuServer()
        print("✅ Haiku 서버 초기화 성공")

        # Health check
        health_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "health"
        }
        health_response = await server.handle_request(health_request)
        print(f"✅ Health Check: {json.dumps(health_response, indent=2)}")

        # 간단한 생성 테스트
        generate_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "generate",
            "params": {
                "prompt": "2+2는?",
                "max_tokens": 100,
                "temperature": 0.1
            }
        }
        generate_response = await server.handle_request(generate_request)
        print(f"✅ Generate Test: {json.dumps(generate_response, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🧪 Haiku MCP 서버 테스트 시작...\n")
    asyncio.run(test_haiku_server())
    print("\n✅ 모든 테스트 통과!")
