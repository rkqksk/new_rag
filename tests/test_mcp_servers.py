#!/usr/bin/env python3
"""
MCP 서버 통합 테스트 도구
모든 MCP 서버의 health check 및 기본 기능 검증
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


# 색상 출력용
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class MCPServerTester:
    """MCP 서버 테스트 클래스"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.mcp_servers_dir = self.project_root / "mcp_servers"
        self.results: List[Dict[str, Any]] = []

    def print_header(self, text: str):
        """헤더 출력"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    def print_success(self, text: str):
        """성공 메시지"""
        print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

    def print_error(self, text: str):
        """에러 메시지"""
        print(f"{Colors.RED}❌ {text}{Colors.RESET}")

    def print_warning(self, text: str):
        """경고 메시지"""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

    def print_info(self, text: str):
        """정보 메시지"""
        print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

    async def test_mcp_server(
        self, server_name: str, server_path: Path, test_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        개별 MCP 서버 테스트

        Args:
            server_name: 서버 이름
            server_path: 서버 파일 경로
            test_request: 테스트 요청 JSON

        Returns:
            테스트 결과
        """
        self.print_info(f"Testing {server_name}...")

        try:
            # MCP 서버 실행
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 요청 전송
            request_json = json.dumps(test_request) + "\n"
            stdout, stderr = await asyncio.wait_for(
                process.communicate(request_json.encode()), timeout=10.0
            )

            # 응답 파싱
            if stdout:
                response = json.loads(stdout.decode().strip())

                # 에러 체크
                if "error" in response:
                    self.print_error(f"{server_name}: {response['error']['message']}")
                    return {
                        "server": server_name,
                        "status": "failed",
                        "error": response["error"]["message"],
                    }

                # 성공
                result = response.get("result", {})
                self.print_success(f"{server_name}: {result.get('status', 'OK')}")

                return {"server": server_name, "status": "passed", "result": result}
            else:
                # stderr 확인
                error_msg = stderr.decode().strip() if stderr else "No response"
                self.print_error(f"{server_name}: {error_msg}")
                return {"server": server_name, "status": "failed", "error": error_msg}

        except asyncio.TimeoutError:
            self.print_error(f"{server_name}: Timeout (>10s)")
            return {"server": server_name, "status": "timeout", "error": "Request timeout"}

        except FileNotFoundError:
            self.print_error(f"{server_name}: Server file not found")
            return {"server": server_name, "status": "not_found", "error": "Server file not found"}

        except Exception as e:
            self.print_error(f"{server_name}: {str(e)}")
            return {"server": server_name, "status": "error", "error": str(e)}

    async def test_claude_haiku_server(self) -> Dict[str, Any]:
        """Claude Haiku MCP 서버 테스트"""
        server_path = self.mcp_servers_dir / "claude_haiku_server.py"

        test_request = {"jsonrpc": "2.0", "id": 1, "method": "health", "params": {}}

        return await self.test_mcp_server("Claude Haiku Server", server_path, test_request)

    async def test_qdrant_server(self) -> Dict[str, Any]:
        """Qdrant MCP 서버 테스트"""
        server_path = self.mcp_servers_dir / "qdrant_server.py"

        test_request = {"jsonrpc": "2.0", "id": 2, "method": "health", "params": {}}

        return await self.test_mcp_server("Qdrant Server", server_path, test_request)

    async def test_ollama_server(self) -> Dict[str, Any]:
        """Ollama MCP 서버 테스트"""
        server_path = self.mcp_servers_dir / "ollama_server.py"

        test_request = {"jsonrpc": "2.0", "id": 3, "method": "health", "params": {}}

        return await self.test_mcp_server("Ollama Server", server_path, test_request)

    async def run_all_tests(self):
        """모든 MCP 서버 테스트 실행"""
        self.print_header("🧪 MCP 서버 통합 테스트")

        # 환경 확인
        self.print_info("Checking environment...")
        print(f"  Project Root: {self.project_root}")
        print(f"  MCP Servers Dir: {self.mcp_servers_dir}")
        print(f"  Python: {sys.executable}")
        print()

        # 서버 파일 존재 확인
        self.print_info("Checking MCP server files...")
        servers = [
            ("claude_haiku_server.py", "Claude Haiku Server"),
            ("qdrant_server.py", "Qdrant Server"),
            ("ollama_server.py", "Ollama Server"),
        ]

        for filename, name in servers:
            server_path = self.mcp_servers_dir / filename
            if server_path.exists():
                self.print_success(f"{name}: Found")
            else:
                self.print_error(f"{name}: Not Found")

        print()

        # 각 서버 테스트
        self.print_header("🔍 Health Check Tests")

        # Claude Haiku 테스트
        result1 = await self.test_claude_haiku_server()
        self.results.append(result1)

        # Qdrant 테스트
        result2 = await self.test_qdrant_server()
        self.results.append(result2)

        # Ollama 테스트
        result3 = await self.test_ollama_server()
        self.results.append(result3)

        # 결과 요약
        self.print_summary()

    def print_summary(self):
        """테스트 결과 요약 출력"""
        self.print_header("📊 Test Summary")

        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(
            1 for r in self.results if r["status"] in ["failed", "error", "timeout", "not_found"]
        )
        total = len(self.results)

        print(f"Total Tests: {total}")
        print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
        print()

        # 상세 결과
        for result in self.results:
            server = result["server"]
            status = result["status"]

            if status == "passed":
                self.print_success(f"{server}: PASSED")
                if "result" in result:
                    print(f"    {json.dumps(result['result'], indent=4)}")
            else:
                self.print_error(f"{server}: {status.upper()}")
                if "error" in result:
                    print(f"    Error: {result['error']}")

        print()

        # 최종 판정
        if failed == 0:
            self.print_header("✅ All MCP Servers Healthy!")
        else:
            self.print_header(f"⚠️  {failed}/{total} MCP Servers Failed")

            # 실패 원인 안내
            print("\n💡 Troubleshooting Tips:")
            print("1. Check if Docker services are running:")
            print("   docker-compose ps")
            print()
            print("2. Check environment variables:")
            print("   cat .env")
            print()
            print("3. Check MCP server dependencies:")
            print("   pip install anthropic qdrant-client aiohttp python-dotenv")
            print()
            print("4. Check Docker network connectivity:")
            print("   docker network inspect rag-enterprise_rag_network")
            print()


async def main():
    """메인 함수"""
    tester = MCPServerTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
