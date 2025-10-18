#!/usr/bin/env python3
"""
Claude Haiku MCP Server 테스트
"""

import json
import subprocess
import sys
import os

def test_haiku_mcp_direct():
    """직접 API 호출 테스트"""
    print("=" * 60)
    print("테스트 1: 직접 Haiku API 호출")
    print("=" * 60)

    # 환경 변수 체크
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False

    try:
        import anthropic
        from dotenv import load_dotenv

        load_dotenv()

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": "2+2는?"}]
        )

        result = response.content[0].text
        print(f"✅ Haiku 응답: {result}")
        return True

    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        return False

def test_haiku_mcp_server():
    """MCP 서버 통신 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: MCP 서버 통신")
    print("=" * 60)

    try:
        # MCP 서버 실행
        proc = subprocess.Popen(
            ["python", "-m", "mcp_servers.claude_haiku_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Health check 요청
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "health",
            "params": {}
        }

        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()

        # 응답 읽기
        response_line = proc.stdout.readline()
        response = json.loads(response_line)

        if response.get("result", {}).get("status") == "healthy":
            print(f"✅ Health check 성공: {response}")
        else:
            print(f"❌ Health check 실패: {response}")
            return False

        # 텍스트 생성 요청
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "generate",
            "params": {
                "prompt": "Python에서 리스트 만드는 법을 한 줄로 설명해줘",
                "max_tokens": 100
            }
        }

        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()

        # 응답 읽기
        response_line = proc.stdout.readline()
        response = json.loads(response_line)

        if "result" in response:
            print(f"✅ 생성 성공: {response['result']['text'][:100]}...")
        else:
            print(f"❌ 생성 실패: {response}")
            return False

        proc.terminate()
        return True

    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🧪 Claude Haiku MCP Server 테스트 시작\n")

    test1_pass = test_haiku_mcp_direct()
    test2_pass = test_haiku_mcp_server()

    print("\n" + "=" * 60)
    print("테스트 결과")
    print("=" * 60)
    print(f"직접 API 호출: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"MCP 서버 통신: {'✅ PASS' if test2_pass else '❌ FAIL'}")

    if test1_pass and test2_pass:
        print("\n🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n❌ 일부 테스트 실패")
        sys.exit(1)
