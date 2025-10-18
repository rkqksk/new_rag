#!/usr/bin/env python3
"""
Ollama MCP Server
MCP 프로토콜을 통해 로컬 Ollama LLM을 사용할 수 있게 해주는 서버
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

try:
    import aiohttp
except ImportError:
    print("Error: aiohttp not installed. Run: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

# 환경 변수 로드
load_dotenv()


class OllamaServer:
    """Ollama Local LLM MCP Server"""

    def __init__(self):
        """서버 초기화"""
        # Ollama 설정 (환경변수 또는 기본값)
        self.host = os.getenv("OLLAMA_HOST", "172.28.0.6")
        self.port = int(os.getenv("OLLAMA_PORT", "11434"))
        self.default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b-instruct-q4_K_M")
        self.base_url = f"http://{self.host}:{self.port}"
        self.timeout = aiohttp.ClientTimeout(total=120)  # 2분 타임아웃

    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model.get("name") for model in data.get("models", [])]
                        return {
                            "status": "healthy",
                            "host": self.host,
                            "port": self.port,
                            "default_model": self.default_model,
                            "available_models": models,
                            "models_count": len(models)
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def list_models(self) -> Dict[str, Any]:
        """사용 가능한 모델 목록 조회"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model in data.get("models", []):
                            models.append({
                                "name": model.get("name"),
                                "size": model.get("size"),
                                "modified_at": model.get("modified_at")
                            })
                        return {
                            "success": True,
                            "models": models,
                            "count": len(models)
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름 (None이면 default_model 사용)
            system: 시스템 프롬프트
            temperature: 온도 (0-1)
            max_tokens: 최대 토큰 수
            stream: 스트리밍 여부
        """
        try:
            model_name = model or self.default_model

            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            if system:
                payload["system"] = system

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        if stream:
                            # 스트리밍 모드 (현재는 전체 응답 반환)
                            full_response = ""
                            async for line in response.content:
                                if line:
                                    try:
                                        chunk = json.loads(line.decode('utf-8'))
                                        if chunk.get("response"):
                                            full_response += chunk.get("response", "")
                                        if chunk.get("done"):
                                            break
                                    except json.JSONDecodeError:
                                        continue

                            return {
                                "success": True,
                                "text": full_response,
                                "model": model_name
                            }
                        else:
                            # 비스트리밍 모드
                            data = await response.json()
                            return {
                                "success": True,
                                "text": data.get("response", ""),
                                "model": model_name,
                                "total_duration": data.get("total_duration"),
                                "load_duration": data.get("load_duration"),
                                "prompt_eval_count": data.get("prompt_eval_count"),
                                "eval_count": data.get("eval_count")
                            }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Request timeout (exceeded 120 seconds)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        채팅 완료 (대화 형식)

        Args:
            messages: 메시지 리스트 [{"role": "user", "content": "..."}]
            model: 모델 이름
            temperature: 온도
            max_tokens: 최대 토큰 수
        """
        try:
            model_name = model or self.default_model

            payload = {
                "model": model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = data.get("message", {})
                        return {
                            "success": True,
                            "role": message.get("role", "assistant"),
                            "content": message.get("content", ""),
                            "model": model_name,
                            "total_duration": data.get("total_duration"),
                            "prompt_eval_count": data.get("prompt_eval_count"),
                            "eval_count": data.get("eval_count")
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Request timeout (exceeded 120 seconds)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        모델 다운로드

        Args:
            model_name: 다운로드할 모델 이름
        """
        try:
            payload = {
                "name": model_name,
                "stream": False
            }

            # 모델 다운로드는 시간이 오래 걸릴 수 있으므로 타임아웃 연장
            long_timeout = aiohttp.ClientTimeout(total=1800)  # 30분

            async with aiohttp.ClientSession(timeout=long_timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "model": model_name,
                            "message": "Model pulled successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_model(self, model_name: str) -> Dict[str, Any]:
        """
        모델 삭제

        Args:
            model_name: 삭제할 모델 이름
        """
        try:
            payload = {
                "name": model_name
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(
                    f"{self.base_url}/api/delete",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "model": model_name,
                            "message": "Model deleted successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def embeddings(
        self,
        text: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트
            model: 모델 이름
        """
        try:
            model_name = model or self.default_model

            payload = {
                "model": model_name,
                "prompt": text
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "embedding": data.get("embedding", []),
                            "model": model_name
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 요청 처리

        Args:
            request: MCP 요청 JSON

        Returns:
            MCP 응답 JSON
        """
        method = request.get("method")
        params = request.get("params", {})

        try:
            # MCP 프로토콜 초기화
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "ollama-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }

            # Health check
            elif method == "health":
                result = await self.health_check()

            # 모델 목록
            elif method == "list_models":
                result = await self.list_models()

            # 텍스트 생성
            elif method == "generate":
                result = await self.generate(
                    prompt=params.get("prompt"),
                    model=params.get("model"),
                    system=params.get("system"),
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 2048),
                    stream=params.get("stream", False)
                )

            # 채팅
            elif method == "chat":
                result = await self.chat(
                    messages=params.get("messages", []),
                    model=params.get("model"),
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 2048)
                )

            # 모델 다운로드
            elif method == "pull_model":
                result = await self.pull_model(
                    model_name=params.get("model_name")
                )

            # 모델 삭제
            elif method == "delete_model":
                result = await self.delete_model(
                    model_name=params.get("model_name")
                )

            # 임베딩
            elif method == "embeddings":
                result = await self.embeddings(
                    text=params.get("text"),
                    model=params.get("model")
                )

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def run(self):
        """서버 실행 (stdin/stdout 통신)"""
        while True:
            try:
                # stdin에서 요청 읽기
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line.strip())

                # 요청 처리
                response = await self.handle_request(request)

                # stdout으로 응답 전송
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


async def main():
    """메인 함수"""
    server = OllamaServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
